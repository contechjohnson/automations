# Claims Storage Schema

This document specifies the Supabase tables for storing claims, merged claims, and context packs in the v2 pipeline.

---

## Overview

The claims storage system consists of four interconnected tables:

1. **`v2_claims`** - Raw claims extracted from each research step
2. **`v2_merged_claims`** - Deduplicated claims after merge (step 07B)
3. **`v2_context_packs`** - Compact summaries for downstream efficiency
4. **`v2_claim_assignments`** - Routing of claims to dossier sections

---

## Table: `v2_claims`

Stores individual claims extracted from research steps BEFORE the merge.

```sql
CREATE TABLE v2_claims (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_run_id UUID NOT NULL REFERENCES v2_pipeline_runs(id) ON DELETE CASCADE,
    step_run_id UUID REFERENCES v2_step_runs(id) ON DELETE SET NULL,

    -- Claim identification
    claim_id TEXT NOT NULL,           -- Prefixed ID: "entity_001", "search_003", etc.
    claim_type TEXT NOT NULL,         -- SIGNAL | CONTACT | ENTITY | RELATIONSHIP | OPPORTUNITY | METRIC | ATTRIBUTE | NOTE

    -- Content
    statement TEXT NOT NULL,          -- One atomic fact, max 500 chars
    entities TEXT[] DEFAULT '{}',     -- Entity names mentioned in claim
    date_in_claim DATE,               -- Date referenced in claim (YYYY-MM-DD)

    -- Source attribution
    source_url TEXT,                  -- URL where fact was found
    source_name TEXT,                 -- Human-readable source name
    source_tier TEXT NOT NULL,        -- GOV | PRIMARY | NEWS | OTHER
    confidence TEXT NOT NULL,         -- HIGH | MEDIUM | LOW
    source_step TEXT NOT NULL,        -- Step that produced this claim

    -- Merge tracking
    is_merged BOOLEAN DEFAULT false,  -- True if merged into another claim
    merged_into TEXT,                 -- claim_id of merged result (e.g., "MERGED_001")

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT now(),

    -- Constraints
    CONSTRAINT claim_type_check CHECK (claim_type IN ('SIGNAL', 'CONTACT', 'ENTITY', 'RELATIONSHIP', 'OPPORTUNITY', 'METRIC', 'ATTRIBUTE', 'NOTE')),
    CONSTRAINT source_tier_check CHECK (source_tier IN ('GOV', 'PRIMARY', 'NEWS', 'OTHER')),
    CONSTRAINT confidence_check CHECK (confidence IN ('HIGH', 'MEDIUM', 'LOW'))
);

-- Indexes
CREATE INDEX idx_claims_pipeline_run ON v2_claims(pipeline_run_id);
CREATE INDEX idx_claims_step_run ON v2_claims(step_run_id);
CREATE INDEX idx_claims_type ON v2_claims(claim_type);
CREATE INDEX idx_claims_source_step ON v2_claims(source_step);
CREATE INDEX idx_claims_merged ON v2_claims(is_merged) WHERE is_merged = false;
```

### Claim ID Prefixes

| Prefix | Source Step | Example |
|--------|-------------|---------|
| `search_` | Search & Signal Discovery | `search_001` |
| `entity_` | Entity Research | `entity_001` |
| `contact_` | Contact Discovery | `contact_001` |
| `lead_` | Enrich Lead | `lead_001` |
| `opp_` | Enrich Opportunity | `opp_001` |
| `client_` | Client Specific | `client_001` |

---

## Table: `v2_merged_claims`

Stores the output of the claims merge process (step 07B Insight).

```sql
CREATE TABLE v2_merged_claims (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_run_id UUID NOT NULL REFERENCES v2_pipeline_runs(id) ON DELETE CASCADE,
    insight_step_run_id UUID REFERENCES v2_step_runs(id) ON DELETE SET NULL,

    -- Merged claim identification
    merged_claim_id TEXT NOT NULL,    -- "MERGED_001", "MERGED_002", etc.
    claim_type TEXT NOT NULL,

    -- Content (canonical version)
    statement TEXT NOT NULL,
    entities TEXT[] DEFAULT '{}',
    date_in_claim DATE,

    -- Source aggregation
    original_claim_ids TEXT[] NOT NULL,  -- ["entity_003", "lead_001"] - claims that were merged
    sources JSONB NOT NULL DEFAULT '[]', -- [{url, name, tier}, ...] - all sources
    confidence TEXT NOT NULL,             -- Aggregated confidence

    -- Reconciliation metadata
    reconciliation_type TEXT,            -- DUPLICATE | CONFLICT | TIMELINE | PASS_THROUGH
    conflicts_resolved JSONB,            -- If there were conflicts, how they were resolved
    supersedes JSONB,                    -- If this supersedes other timeline events

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT now(),

    -- Constraints
    CONSTRAINT merged_claim_type_check CHECK (claim_type IN ('SIGNAL', 'CONTACT', 'ENTITY', 'RELATIONSHIP', 'OPPORTUNITY', 'METRIC', 'ATTRIBUTE', 'NOTE')),
    CONSTRAINT merged_confidence_check CHECK (confidence IN ('HIGH', 'MEDIUM', 'LOW')),
    CONSTRAINT merged_recon_type_check CHECK (reconciliation_type IN ('DUPLICATE', 'CONFLICT', 'TIMELINE', 'PASS_THROUGH', NULL))
);

-- Indexes
CREATE INDEX idx_merged_claims_pipeline ON v2_merged_claims(pipeline_run_id);
CREATE INDEX idx_merged_claims_type ON v2_merged_claims(claim_type);
CREATE INDEX idx_merged_claims_insight_step ON v2_merged_claims(insight_step_run_id);
```

### Sources JSONB Structure

```json
[
  {
    "url": "https://gov.ontario.ca/...",
    "name": "Environmental Registry of Ontario",
    "tier": "GOV",
    "original_claim_id": "entity_003"
  },
  {
    "url": "https://company.com/press/...",
    "name": "Wyloo Metals Press Release",
    "tier": "PRIMARY",
    "original_claim_id": "lead_001"
  }
]
```

---

## Table: `v2_resolved_objects`

Stores resolved contacts, timelines, and conflicts from the merge process.

```sql
CREATE TABLE v2_resolved_objects (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_run_id UUID NOT NULL REFERENCES v2_pipeline_runs(id) ON DELETE CASCADE,

    -- Object type and identification
    object_type TEXT NOT NULL,        -- CONTACT | TIMELINE | CONFLICT | AMBIGUOUS
    object_id TEXT NOT NULL,          -- "contact_001", "timeline_001", etc.

    -- Resolution data (structure varies by type)
    data JSONB NOT NULL,

    -- Evidence
    evidence_claim_ids TEXT[] NOT NULL, -- Claims that support this resolution
    confidence TEXT NOT NULL,
    resolution TEXT,                   -- SAME_PERSON | DIFFERENT_PERSON | UNSURE | etc.

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT now(),

    -- Constraints
    CONSTRAINT object_type_check CHECK (object_type IN ('CONTACT', 'TIMELINE', 'CONFLICT', 'AMBIGUOUS'))
);

-- Indexes
CREATE INDEX idx_resolved_objects_pipeline ON v2_resolved_objects(pipeline_run_id);
CREATE INDEX idx_resolved_objects_type ON v2_resolved_objects(object_type);
```

### Object Data Structures

**CONTACT Resolution:**
```json
{
  "name": "Sylvain Goyette",
  "current_role": "VP Projects",
  "organization": "Wyloo Metals",
  "why_they_matter": "Owns project execution for Eagle's Nest",
  "bio_summary": "15+ years mining experience...",
  "notes": "Title varies: VP Projects, VP Operations"
}
```

**TIMELINE Resolution:**
```json
{
  "subject": "Construction start",
  "current_status": "Started September 2025",
  "current_date": "2025-09-01",
  "history": [
    {"date_reported": "2024-12", "status": "ANNOUNCED", "value": "June 2025"},
    {"date_reported": "2025-03", "status": "REVISED", "value": "September 2025"}
  ]
}
```

**CONFLICT:**
```json
{
  "description": "HQ location conflict",
  "values": {
    "entity_012": "Perth",
    "lead_045": "Sydney"
  },
  "recommendation": "Prefer entity_012 (GOV source)",
  "resolution_logic": "GOV > PRIMARY > NEWS"
}
```

---

## Table: `v2_context_packs`

Stores context packs built at strategic points in the pipeline.

```sql
CREATE TABLE v2_context_packs (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_run_id UUID NOT NULL REFERENCES v2_pipeline_runs(id) ON DELETE CASCADE,
    step_run_id UUID REFERENCES v2_step_runs(id) ON DELETE SET NULL,

    -- Pack type and content
    pack_type TEXT NOT NULL,          -- signal_to_entity | entity_to_contacts | contacts_to_enrichment
    pack_data JSONB NOT NULL,         -- Full context pack JSON

    -- Lineage
    anchor_claim_ids TEXT[] DEFAULT '{}',  -- Claims this pack summarizes

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT now(),

    -- Constraints
    CONSTRAINT pack_type_check CHECK (pack_type IN ('signal_to_entity', 'entity_to_contacts', 'contacts_to_enrichment'))
);

-- Indexes
CREATE INDEX idx_context_packs_pipeline ON v2_context_packs(pipeline_run_id);
CREATE INDEX idx_context_packs_type ON v2_context_packs(pack_type);
```

### Context Pack Types

| Pack Type | Built After | Purpose |
|-----------|-------------|---------|
| `signal_to_entity` | Signal Discovery | Prepare for Entity Research |
| `entity_to_contacts` | Entity Research | Establish canonical identity, prepare for Contact Discovery |
| `contacts_to_enrichment` | Insight (07B) | Prepare for parallel enrichment and section writers |

---

## Table: `v2_claim_assignments`

Routes claims to dossier sections via the Dossier Plan (step 09).

```sql
CREATE TABLE v2_claim_assignments (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_run_id UUID NOT NULL REFERENCES v2_pipeline_runs(id) ON DELETE CASCADE,
    dossier_plan_step_id UUID REFERENCES v2_step_runs(id) ON DELETE SET NULL,

    -- Assignment
    section_key TEXT NOT NULL,        -- INTRO | SCORE | SIGNALS | CONTACTS | LEAD_INTELLIGENCE | STRATEGY | OPPORTUNITY | CLIENT_SPECIFIC
    merged_claim_id TEXT NOT NULL,    -- Reference to v2_merged_claims.merged_claim_id

    -- Routing metadata
    priority INTEGER DEFAULT 0,       -- Higher = more important for this section
    coverage_notes TEXT,              -- Notes about what this claim covers

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT now(),

    -- Constraints
    CONSTRAINT section_key_check CHECK (section_key IN ('INTRO', 'SCORE', 'SIGNALS', 'CONTACTS', 'LEAD_INTELLIGENCE', 'STRATEGY', 'OPPORTUNITY', 'CLIENT_SPECIFIC'))
);

-- Indexes
CREATE INDEX idx_claim_assignments_pipeline ON v2_claim_assignments(pipeline_run_id);
CREATE INDEX idx_claim_assignments_section ON v2_claim_assignments(section_key);
CREATE INDEX idx_claim_assignments_claim ON v2_claim_assignments(merged_claim_id);

-- A claim can be assigned to multiple sections
CREATE UNIQUE INDEX idx_claim_assignments_unique ON v2_claim_assignments(pipeline_run_id, section_key, merged_claim_id);
```

---

## Merge Statistics Table

Tracks the merge process statistics for observability.

```sql
CREATE TABLE v2_merge_stats (
    -- Identity
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_run_id UUID NOT NULL REFERENCES v2_pipeline_runs(id) ON DELETE CASCADE,
    insight_step_run_id UUID REFERENCES v2_step_runs(id) ON DELETE SET NULL,

    -- Counts
    input_claims_count INTEGER NOT NULL,
    output_claims_count INTEGER NOT NULL,
    duplicates_merged INTEGER DEFAULT 0,
    conflicts_resolved INTEGER DEFAULT 0,
    timelines_resolved INTEGER DEFAULT 0,
    contacts_resolved INTEGER DEFAULT 0,
    ambiguous_items INTEGER DEFAULT 0,
    passed_through INTEGER DEFAULT 0,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Index
CREATE INDEX idx_merge_stats_pipeline ON v2_merge_stats(pipeline_run_id);
```

---

## Views

### Claims Summary View

```sql
CREATE VIEW v2_claims_summary AS
SELECT
    pipeline_run_id,
    claim_type,
    COUNT(*) as total_claims,
    COUNT(*) FILTER (WHERE is_merged = false) as active_claims,
    COUNT(*) FILTER (WHERE is_merged = true) as merged_claims,
    COUNT(*) FILTER (WHERE confidence = 'HIGH') as high_confidence,
    COUNT(*) FILTER (WHERE confidence = 'MEDIUM') as medium_confidence,
    COUNT(*) FILTER (WHERE confidence = 'LOW') as low_confidence
FROM v2_claims
GROUP BY pipeline_run_id, claim_type;
```

### Section Claims View

```sql
CREATE VIEW v2_section_claims AS
SELECT
    ca.pipeline_run_id,
    ca.section_key,
    mc.merged_claim_id,
    mc.claim_type,
    mc.statement,
    mc.confidence,
    mc.sources,
    ca.priority,
    ca.coverage_notes
FROM v2_claim_assignments ca
JOIN v2_merged_claims mc ON mc.pipeline_run_id = ca.pipeline_run_id
    AND mc.merged_claim_id = ca.merged_claim_id
ORDER BY ca.section_key, ca.priority DESC;
```

---

## Data Flow

```
Pipeline Start
      │
      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     CLAIMS EXTRACTION                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   Search/Signal → v2_claims (search_xxx)                            │
│   Entity Research → v2_claims (entity_xxx)                          │
│       └─ v2_context_packs (signal_to_entity)                        │
│   Contact Discovery → v2_claims (contact_xxx)                        │
│       └─ v2_context_packs (entity_to_contacts)                      │
│   Enrich Lead → v2_claims (lead_xxx)                                │
│   Enrich Opportunity → v2_claims (opp_xxx)                          │
│   Client Specific → v2_claims (client_xxx)                          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     CLAIMS MERGE (07B Insight)                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   1. Load all v2_claims for pipeline_run_id                         │
│   2. Run CLAIMS_MERGE prompt                                        │
│   3. Write to v2_merged_claims                                      │
│   4. Write to v2_resolved_objects (contacts, timelines, conflicts)  │
│   5. Write to v2_merge_stats                                        │
│   6. Update v2_claims.is_merged = true for merged claims            │
│   7. Build contacts_to_enrichment context pack                      │
│   8. Write to v2_context_packs                                      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     DOSSIER PLAN (Step 09)                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   1. Load v2_merged_claims for pipeline_run_id                      │
│   2. Run DOSSIER_PLAN prompt                                        │
│   3. Write routing to v2_claim_assignments                          │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     SECTION WRITERS                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   Each writer receives:                                              │
│   1. v2_section_claims view (filtered by section_key)               │
│   2. v2_resolved_objects (contacts, timelines)                      │
│   3. v2_context_packs (contacts_to_enrichment)                      │
│                                                                      │
│   Sources auto-populated from claim source_url fields               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Query Examples

### Get all claims for a pipeline run

```sql
SELECT
    claim_id,
    claim_type,
    statement,
    source_tier,
    confidence,
    source_step,
    is_merged
FROM v2_claims
WHERE pipeline_run_id = 'uuid-here'
ORDER BY source_step, claim_id;
```

### Get merged claims with all sources

```sql
SELECT
    merged_claim_id,
    claim_type,
    statement,
    confidence,
    array_length(original_claim_ids, 1) as source_count,
    sources
FROM v2_merged_claims
WHERE pipeline_run_id = 'uuid-here'
ORDER BY claim_type, merged_claim_id;
```

### Get claims routed to a specific section

```sql
SELECT
    mc.merged_claim_id,
    mc.claim_type,
    mc.statement,
    mc.confidence,
    ca.priority,
    ca.coverage_notes
FROM v2_claim_assignments ca
JOIN v2_merged_claims mc ON mc.pipeline_run_id = ca.pipeline_run_id
    AND mc.merged_claim_id = ca.merged_claim_id
WHERE ca.pipeline_run_id = 'uuid-here'
    AND ca.section_key = 'SIGNALS'
ORDER BY ca.priority DESC;
```

### Get resolved contacts

```sql
SELECT
    object_id,
    data->>'name' as name,
    data->>'current_role' as role,
    data->>'organization' as org,
    confidence,
    resolution,
    evidence_claim_ids
FROM v2_resolved_objects
WHERE pipeline_run_id = 'uuid-here'
    AND object_type = 'CONTACT'
ORDER BY confidence DESC;
```

### Merge statistics

```sql
SELECT
    pr.id as run_id,
    pr.created_at,
    ms.input_claims_count,
    ms.output_claims_count,
    ms.duplicates_merged,
    ms.conflicts_resolved,
    ms.contacts_resolved
FROM v2_pipeline_runs pr
JOIN v2_merge_stats ms ON ms.pipeline_run_id = pr.id
ORDER BY pr.created_at DESC
LIMIT 10;
```

---

## Migration SQL

Complete SQL to create all claims-related tables:

```sql
-- Run this in Supabase SQL editor

-- Claims table
CREATE TABLE IF NOT EXISTS v2_claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_run_id UUID NOT NULL REFERENCES v2_pipeline_runs(id) ON DELETE CASCADE,
    step_run_id UUID REFERENCES v2_step_runs(id) ON DELETE SET NULL,
    claim_id TEXT NOT NULL,
    claim_type TEXT NOT NULL CHECK (claim_type IN ('SIGNAL', 'CONTACT', 'ENTITY', 'RELATIONSHIP', 'OPPORTUNITY', 'METRIC', 'ATTRIBUTE', 'NOTE')),
    statement TEXT NOT NULL,
    entities TEXT[] DEFAULT '{}',
    date_in_claim DATE,
    source_url TEXT,
    source_name TEXT,
    source_tier TEXT NOT NULL CHECK (source_tier IN ('GOV', 'PRIMARY', 'NEWS', 'OTHER')),
    confidence TEXT NOT NULL CHECK (confidence IN ('HIGH', 'MEDIUM', 'LOW')),
    source_step TEXT NOT NULL,
    is_merged BOOLEAN DEFAULT false,
    merged_into TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_claims_pipeline_run ON v2_claims(pipeline_run_id);
CREATE INDEX IF NOT EXISTS idx_claims_step_run ON v2_claims(step_run_id);
CREATE INDEX IF NOT EXISTS idx_claims_type ON v2_claims(claim_type);
CREATE INDEX IF NOT EXISTS idx_claims_source_step ON v2_claims(source_step);
CREATE INDEX IF NOT EXISTS idx_claims_merged ON v2_claims(is_merged) WHERE is_merged = false;

-- Merged claims table
CREATE TABLE IF NOT EXISTS v2_merged_claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_run_id UUID NOT NULL REFERENCES v2_pipeline_runs(id) ON DELETE CASCADE,
    insight_step_run_id UUID REFERENCES v2_step_runs(id) ON DELETE SET NULL,
    merged_claim_id TEXT NOT NULL,
    claim_type TEXT NOT NULL CHECK (claim_type IN ('SIGNAL', 'CONTACT', 'ENTITY', 'RELATIONSHIP', 'OPPORTUNITY', 'METRIC', 'ATTRIBUTE', 'NOTE')),
    statement TEXT NOT NULL,
    entities TEXT[] DEFAULT '{}',
    date_in_claim DATE,
    original_claim_ids TEXT[] NOT NULL,
    sources JSONB NOT NULL DEFAULT '[]',
    confidence TEXT NOT NULL CHECK (confidence IN ('HIGH', 'MEDIUM', 'LOW')),
    reconciliation_type TEXT CHECK (reconciliation_type IN ('DUPLICATE', 'CONFLICT', 'TIMELINE', 'PASS_THROUGH', NULL)),
    conflicts_resolved JSONB,
    supersedes JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_merged_claims_pipeline ON v2_merged_claims(pipeline_run_id);
CREATE INDEX IF NOT EXISTS idx_merged_claims_type ON v2_merged_claims(claim_type);
CREATE INDEX IF NOT EXISTS idx_merged_claims_insight_step ON v2_merged_claims(insight_step_run_id);

-- Resolved objects table
CREATE TABLE IF NOT EXISTS v2_resolved_objects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_run_id UUID NOT NULL REFERENCES v2_pipeline_runs(id) ON DELETE CASCADE,
    object_type TEXT NOT NULL CHECK (object_type IN ('CONTACT', 'TIMELINE', 'CONFLICT', 'AMBIGUOUS')),
    object_id TEXT NOT NULL,
    data JSONB NOT NULL,
    evidence_claim_ids TEXT[] NOT NULL,
    confidence TEXT NOT NULL,
    resolution TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_resolved_objects_pipeline ON v2_resolved_objects(pipeline_run_id);
CREATE INDEX IF NOT EXISTS idx_resolved_objects_type ON v2_resolved_objects(object_type);

-- Context packs table
CREATE TABLE IF NOT EXISTS v2_context_packs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_run_id UUID NOT NULL REFERENCES v2_pipeline_runs(id) ON DELETE CASCADE,
    step_run_id UUID REFERENCES v2_step_runs(id) ON DELETE SET NULL,
    pack_type TEXT NOT NULL CHECK (pack_type IN ('signal_to_entity', 'entity_to_contacts', 'contacts_to_enrichment')),
    pack_data JSONB NOT NULL,
    anchor_claim_ids TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_context_packs_pipeline ON v2_context_packs(pipeline_run_id);
CREATE INDEX IF NOT EXISTS idx_context_packs_type ON v2_context_packs(pack_type);

-- Claim assignments table
CREATE TABLE IF NOT EXISTS v2_claim_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_run_id UUID NOT NULL REFERENCES v2_pipeline_runs(id) ON DELETE CASCADE,
    dossier_plan_step_id UUID REFERENCES v2_step_runs(id) ON DELETE SET NULL,
    section_key TEXT NOT NULL CHECK (section_key IN ('INTRO', 'SCORE', 'SIGNALS', 'CONTACTS', 'LEAD_INTELLIGENCE', 'STRATEGY', 'OPPORTUNITY', 'CLIENT_SPECIFIC')),
    merged_claim_id TEXT NOT NULL,
    priority INTEGER DEFAULT 0,
    coverage_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_claim_assignments_pipeline ON v2_claim_assignments(pipeline_run_id);
CREATE INDEX IF NOT EXISTS idx_claim_assignments_section ON v2_claim_assignments(section_key);
CREATE INDEX IF NOT EXISTS idx_claim_assignments_claim ON v2_claim_assignments(merged_claim_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_claim_assignments_unique ON v2_claim_assignments(pipeline_run_id, section_key, merged_claim_id);

-- Merge stats table
CREATE TABLE IF NOT EXISTS v2_merge_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_run_id UUID NOT NULL REFERENCES v2_pipeline_runs(id) ON DELETE CASCADE,
    insight_step_run_id UUID REFERENCES v2_step_runs(id) ON DELETE SET NULL,
    input_claims_count INTEGER NOT NULL,
    output_claims_count INTEGER NOT NULL,
    duplicates_merged INTEGER DEFAULT 0,
    conflicts_resolved INTEGER DEFAULT 0,
    timelines_resolved INTEGER DEFAULT 0,
    contacts_resolved INTEGER DEFAULT 0,
    ambiguous_items INTEGER DEFAULT 0,
    passed_through INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_merge_stats_pipeline ON v2_merge_stats(pipeline_run_id);

-- Views
CREATE OR REPLACE VIEW v2_claims_summary AS
SELECT
    pipeline_run_id,
    claim_type,
    COUNT(*) as total_claims,
    COUNT(*) FILTER (WHERE is_merged = false) as active_claims,
    COUNT(*) FILTER (WHERE is_merged = true) as merged_claims,
    COUNT(*) FILTER (WHERE confidence = 'HIGH') as high_confidence,
    COUNT(*) FILTER (WHERE confidence = 'MEDIUM') as medium_confidence,
    COUNT(*) FILTER (WHERE confidence = 'LOW') as low_confidence
FROM v2_claims
GROUP BY pipeline_run_id, claim_type;

CREATE OR REPLACE VIEW v2_section_claims AS
SELECT
    ca.pipeline_run_id,
    ca.section_key,
    mc.merged_claim_id,
    mc.claim_type,
    mc.statement,
    mc.confidence,
    mc.sources,
    ca.priority,
    ca.coverage_notes
FROM v2_claim_assignments ca
JOIN v2_merged_claims mc ON mc.pipeline_run_id = ca.pipeline_run_id
    AND mc.merged_claim_id = ca.merged_claim_id
ORDER BY ca.section_key, ca.priority DESC;
```
