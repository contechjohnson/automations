# Comprehensive Migration Plan: Make.com to Production Pipeline

## Executive Summary

This document provides a complete technical specification for migrating the Columnline dossier generation pipeline from Make.com visual workflows to a production Python codebase on the DigitalOcean automations droplet.

**Current State:**
- 19 Make.com blueprints with 231 modules
- 10 CSV files serving as testing harness (prompts, inputs, outputs)
- Google Sheets as runtime state machine
- 60-90 minute execution time per dossier

**Target State:**
- Python-based pipeline on DO droplet (`64.225.120.95`)
- Prompts stored in Supabase (editable via dashboard)
- Full I/O capture for every step
- Claims-based fact accumulation system
- Step isolation for rapid iteration

---

## Part 1: Make.com Blueprint Architecture

### 1.1 Blueprint Inventory (19 files)

| File | Purpose | Modules | LLM Calls |
|------|---------|---------|-----------|
| `_0A_CLIENT_ONBOARDING.blueprint.json` | Client setup | 18 | 4 |
| `_0B_PREP_INPUTS.blueprint.json` | Input preprocessing | 31 | 6 |
| `_0C_BATCH_COMPOSER.blueprint.json` | Batch strategy | 12 | 2 |
| `01AND02_SEARCH_AND_SIGNAL.blueprint.json` | Discovery | 24 | 4 |
| `03_AND_04_SEQUENTIAL_DEEP_RESEARCH_STEPS.blueprint.json` | Deep research | 35 | 8 |
| `05A_ENRICH_LEAD.blueprint.json` | Lead enrichment | 15 | 3 |
| `05B_ENRICH_OPPORTUNITY.blueprint.json` | Opportunity research | 15 | 3 |
| `05C_CLIENT_SPECIFIC.blueprint.json` | Custom research | 15 | 3 |
| `06_ENRICH_CONTACTS.blueprint.json` | Bulk contact lookup | 18 | 2 |
| `06.2_ENRICH_CONTACT.blueprint.json` | Individual contact | 14 | 2 |
| `07B_INSIGHT.blueprint.json` | Strategic analysis | 22 | 5 |
| `08_MEDIA.blueprint.json` | Logo/images | 12 | 1 |
| `09_DOSSIER_PLAN.blueprint.json` | Section routing | 16 | 2 |
| `MAIN_DOSSIER_PIPELINE.json` | Orchestrator | 28 | 0 |
| `WRITER_INTRO.blueprint.json` | Intro section | 8 | 1 |
| `WRITER_SIGNALS.blueprint.json` | Signals section | 8 | 1 |
| `WRITER_LEAD_INTELLIGENCE.blueprint.json` | Lead intel section | 8 | 1 |
| `WRITER_OPPORTUNITY_DETAILS.blueprint.json` | Opportunity section | 8 | 1 |
| `WRITER_STRATEGY.blueprint.json` | Strategy section | 8 | 1 |
| `WRITER_CLIENT_SPECIFIC.blueprint.json` | Client section | 8 | 1 |

**Total: 231 modules, 66 LLM calls, 64 Google Sheets operations**

### 1.2 Execution Architecture

```
MAIN_DOSSIER_PIPELINE
    │
    ├── Sync Stage 1: 01AND02_SEARCH_AND_SIGNAL
    │   └── search_builder → signal_discovery
    │
    ├── Async Batch 1 (parallel):
    │   ├── 03_AND_04_DEEP_RESEARCH → entity_research → contact_discovery
    │   └── 05A_ENRICH_LEAD
    │
    ├── Async Batch 2 (parallel):
    │   ├── 05B_ENRICH_OPPORTUNITY
    │   ├── 05C_CLIENT_SPECIFIC
    │   └── 06_ENRICH_CONTACTS → 06.2_ENRICH_CONTACT (per contact)
    │
    ├── Async Batch 3 (parallel):
    │   ├── 07B_INSIGHT (claims merge + context packs)
    │   └── 08_MEDIA
    │
    └── Final Stage: 09_DOSSIER_PLAN + 6 WRITER scenarios (parallel)
```

### 1.3 Polling Pattern

All async scenarios use a 30-second wait loop:
```
1. Trigger sub-scenario
2. Loop every 30s:
   - Check completion status via HTTP
   - If done, break loop
   - If timeout (usually 20 minutes), fail
3. Continue to next stage
```

### 1.4 Google Sheets Cell Mappings

**Inputs Sheet:**
| Cell | Variable | Description |
|------|----------|-------------|
| B2 | ICP_CONFIG | Ideal Customer Profile JSON |
| B3 | INDUSTRY_RESEARCH | Industry context JSON |
| B4 | RESEARCH_CONTEXT | Client positioning JSON |
| B5 | SEED_DATA | Optional seed input |
| B6 | CLAIMS_MERGE | Merge prompt |
| B7 | CONTEXT_PACK | Context pack prompt |
| B8 | CLAIMS_EXTRACTION | Extraction prompt |

**Prompts Sheet:**
| Row | Step | Cell C (Prompt) | Cell D (Input) | Cell E (Output) |
|-----|------|-----------------|----------------|-----------------|
| 2 | SEARCH_BUILDER | Prompt text | Last input | Last output |
| 3 | SIGNAL_DISCOVERY | Prompt text | Last input | Last output |
| 4 | ENTITY_RESEARCH | Prompt text | Last input | Last output |
| 5 | CONTACT_DISCOVERY | Prompt text | Last input | Last output |
| 6 | ENRICH_LEAD | Prompt text | Last input | Last output |
| 7 | ENRICH_OPPORTUNITY | Prompt text | Last input | Last output |
| 8 | CLIENT_SPECIFIC | Prompt text | Last input | Last output |
| 9 | ENRICH_CONTACTS | Prompt text | Last input | Last output |
| 10 | ENRICH_CONTACT | Prompt text | Last input | Last output |
| 11 | COPY | Prompt text | Last input | Last output |
| 12 | COPY_CLIENT | Prompt text | Last input | Last output |
| 13 | INSIGHT | Prompt text | Last input | Last output |
| 14 | MEDIA | Prompt text | Last input | Last output |
| 15 | DOSSIER_PLAN | Prompt text | Last input | Last output |

---

## Part 2: CSV Testing Harness Structure

### 2.1 Prompts.csv (2,804 lines)

**Columns:**
1. `STAGE` - Pipeline stage (FIND LEAD, ENRICH LEAD, ENRICH CONTACTS, COPY, INSIGHT, MEDIA, DOSSIER PLAN, BATCH COMPOSER)
2. `STEP` - Step ID (1 SEARCH_BUILDER, 2 SIGNAL_DISCOVERY, etc.)
3. `PROMPT` - Full LLM prompt with Handlebars templates
4. `INPUT` - JSON input structure
5. `OUTPUT` - Expected JSON output structure
6. `PRODUCE CLAIMS?` - YES/NO
7. `CLAIMS MERGED?` - YES/NO
8. `CONTEXT PACK PRODUCED?` - YES/NO
9. `CLAIMS` - Reference
10. `MERGED CLAIMS` - Reference
11. `CONTEXT PACKS` - Reference

**Pipeline Steps Defined:**

| Step | Produces Claims | Merges Claims | Produces Context Pack |
|------|-----------------|---------------|----------------------|
| 1 SEARCH_BUILDER | NO | NO | NO |
| 2 SIGNAL_DISCOVERY | NO | NO | NO |
| 3 ENTITY_RESEARCH | YES | NO | NO |
| 4 CONTACT_DISCOVERY | YES | NO | NO |
| 5a ENRICH_LEAD | YES | NO | NO |
| 5b ENRICH_OPPORTUNITY | YES | NO | NO |
| 5c CLIENT_SPECIFIC | YES | NO | NO |
| 6 ENRICH_CONTACTS | NO | NO | NO |
| 6.2 ENRICH_CONTACT | NO | NO | NO |
| 7a COPY | NO | NO | NO |
| 7.2 COPY_CLIENT | NO | NO | NO |
| 7b INSIGHT | YES | YES | YES |
| 8 MEDIA | NO | NO | NO |
| 9 DOSSIER_PLAN | NO | NO | NO |

### 2.2 DOSSIER SECTIONS.csv (542 lines)

Defines the 7 final dossier sections:

1. **INTRO** → `title`, `one_liner`, `the_angle`, `lead_score`, `score_explanation`, `timing_urgency`
2. **SIGNALS** → `why_theyll_buy_now[]` with signal_type, headline, status, date, source_url
3. **CONTACTS** → `verified_contacts[]` with name, title, email, linkedin, bio, tier
4. **LEAD INTELLIGENCE** → `company_intel`, `entity_brief`, `network_intelligence[]`, `quick_reference[]`
5. **STRATEGY** → `deal_strategy{}`, `common_objections[]`, `competitive_positioning{}`
6. **OPPORTUNITY** → `opportunity_details{}` with project_name, location, timeline, key_players
7. **CLIENT REQUEST** → `client_specific[]` question-answer pairs

### 2.3 Inputs.csv

**Key Input Structures:**

```json
// ICP_CONFIG
{
  "signals": [{"name": "...", "tier": "hot|warm|passive", "weight": 0-25}],
  "disqualifiers": ["..."],
  "target_titles": ["..."],
  "excluded_titles": ["CEO", "President", "Founder"],
  "scoring_weights": {},
  "geography": {"tier_1": [], "tier_2": [], "tier_3": []}
}

// INDUSTRY_RESEARCH
{
  "buying_signals": [{"name": "...", "weight": 0-25, "source": "..."}],
  "personas": [{"title": "...", "triggers": []}],
  "industries": [{"name": "...", "priority": 0-100}],
  "timing_constraints": [],
  "sources_to_check": []
}

// RESEARCH_CONTEXT
{
  "client": {"name": "...", "domain": "...", "tagline": "..."},
  "differentiators": [],
  "notable_projects": [],
  "competitors": [],
  "goals": {},
  "brand_voice": {"tone": "...", "phrases": [], "avoid": []}
}
```

---

## Part 3: Claims System Architecture

The claims system is the backbone of the pipeline. It transforms unstructured research narratives into atomic, verifiable facts that accumulate without redundancy and route intelligently to section writers.

### 3.1 What is a Claim?

A **claim** is an atomic, verifiable fact extracted from research output. Each claim is:
- **Additive** - Contributes unique information (duplicates are merged)
- **Verifiable** - Has source URL, source tier, confidence level
- **Typed** - Categorized for routing to appropriate dossier sections
- **Traceable** - Tagged with the step that produced it

**Claim Structure:**
```json
{
  "claim_id": "er_001",                    // Step prefix + sequence number
  "claim_type": "SIGNAL|CONTACT|ENTITY|RELATIONSHIP|OPPORTUNITY|METRIC|ATTRIBUTE|NOTE",
  "statement": "Acme Corp filed a $50M data center permit in Loudoun County",
  "entities": ["Acme Corp", "Loudoun County"],
  "date_in_claim": "2025-12-15",
  "source_url": "https://loudoun.gov/permits/2025/acme-dc",
  "source_name": "Loudoun County Permits Database",
  "source_tier": "GOV|PRIMARY|NEWS|OTHER",
  "confidence": "HIGH|MEDIUM|LOW",
  "source_step": "entity_research"
}
```

**Claim ID Prefixes by Step:**
| Prefix | Step | Example |
|--------|------|---------|
| `sd_` | Signal Discovery | sd_001, sd_002 |
| `er_` | Entity Research | er_001, er_002 |
| `cd_` | Contact Discovery | cd_001, cd_002 |
| `el_` | Enrich Lead | el_001, el_002 |
| `eo_` | Enrich Opportunity | eo_001, eo_002 |
| `cs_` | Client Specific | cs_001, cs_002 |

### 3.2 Claims Production (Which Steps Produce Claims)

**NOT all steps produce claims.** Only research steps that discover new facts produce claims:

| Step | Produces Claims | Why |
|------|-----------------|-----|
| Search Builder | ❌ NO | Planning step - no research |
| Signal Discovery | ✅ YES | Discovers signals via web search |
| Entity Research | ✅ YES | Deep research on company |
| Contact Discovery | ✅ YES | Discovers decision-makers |
| Enrich Lead | ✅ YES | Deep lead qualification research |
| Enrich Opportunity | ✅ YES | Opportunity sizing research |
| Client Specific | ✅ YES | Custom client questions |
| Enrich Contacts | ❌ NO | API calls only (Apollo, LinkedIn) |
| Copy | ❌ NO | Consumes claims, doesn't produce |
| Insight | ❌ NO | **MERGES claims, doesn't produce new ones** |
| Media | ❌ NO | API calls only (logo.dev) |
| Dossier Plan | ❌ NO | Routing step |
| Section Writers | ❌ NO | Consume claims to write sections |

**Critical Distinction:** The Insight step (7b) is the **merge point**, not a producer. It takes all claims from prior steps and consolidates them - it does not generate new claims.

### 3.3 Claims Flow Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLAIMS PRODUCTION                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  Stage 2: FIND LEAD                                                           │
│  ┌──────────────────┐    ┌──────────────────┐                                │
│  │ Signal Discovery │───►│ Claims [sd_001]  │──┐                             │
│  └──────────────────┘    └──────────────────┘  │                             │
│           │                                      │                             │
│           ▼                                      │                             │
│  ┌──────────────────┐    ┌──────────────────┐  │                             │
│  │ Entity Research  │───►│ Claims [er_001]  │──┤                             │
│  └──────────────────┘    └──────────────────┘  │                             │
│           │                                      │                             │
│           ▼                                      ▼                             │
│  ┌──────────────────┐    ┌──────────────────┐  ┌─────────────────────────┐  │
│  │Contact Discovery │───►│ Claims [cd_001]  │──►│  Context Pack #1        │  │
│  └──────────────────┘    └──────────────────┘  │  (after deep research)   │  │
│                                                  └─────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  Stage 3: ENRICH (Parallel)                                                   │
│  ┌──────────────────┐    ┌──────────────────┐                                │
│  │   Enrich Lead    │───►│ Claims [el_001]  │──┐                             │
│  └──────────────────┘    └──────────────────┘  │                             │
│                                                  │                             │
│  ┌──────────────────┐    ┌──────────────────┐  │                             │
│  │  Enrich Oppty    │───►│ Claims [eo_001]  │──┼────────────────────────────►│
│  └──────────────────┘    └──────────────────┘  │                             │
│                                                  │                             │
│  ┌──────────────────┐    ┌──────────────────┐  │                             │
│  │ Client Specific  │───►│ Claims [cs_001]  │──┘                             │
│  └──────────────────┘    └──────────────────┘                                │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLAIMS MERGE (Step 7b: Insight)                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ALL claims from steps 2-5c flow into Insight:                               │
│  • sd_001, sd_002, ... (Signal Discovery)                                    │
│  • er_001, er_002, ... (Entity Research)                                     │
│  • cd_001, cd_002, ... (Contact Discovery)                                   │
│  • el_001, el_002, ... (Enrich Lead)                                         │
│  • eo_001, eo_002, ... (Enrich Opportunity)                                  │
│  • cs_001, cs_002, ... (Client Specific)                                     │
│                                                                               │
│  MERGE_CLAIMS Prompt Does:                                                    │
│  1. Identify duplicates (same fact, different sources)                       │
│  2. Reconcile conflicts (contradictory claims)                               │
│  3. Assign confidence scores                                                  │
│  4. Group by claim type                                                       │
│  5. Create merged_claims array                                               │
│                                                                               │
│  Output: merged_claims[] - deduplicated, reconciled facts                    │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ ALSO produces: Context Pack #2 (after insight)                          ││
│  │ Compact summary optimized for section writers                            ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLAIMS CONSUMPTION (Writers)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  Each section writer receives THREE inputs:                                   │
│                                                                               │
│  1. ALL merged_claims[] ─────────────────────────────────────────────────────│
│     • Full set of deduplicated facts                                         │
│     • Writer extracts relevant claims by type                                │
│                                                                               │
│  2. Dossier Plan (routing map) ──────────────────────────────────────────────│
│     • Tells each writer what to emphasize                                    │
│     • Section-specific focus areas                                           │
│     • Priority ordering                                                       │
│                                                                               │
│  3. Context Pack #2 ─────────────────────────────────────────────────────────│
│     • Compact briefing from insight step                                     │
│     • Efficiency optimization (avoids re-reading all claims)                 │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │ Writers run in PARALLEL (6 concurrent):                                  ││
│  │                                                                           ││
│  │  WRITER_INTRO ─────────┐                                                  ││
│  │  WRITER_SIGNALS ───────┤                                                  ││
│  │  WRITER_LEAD_INTEL ────┼───► Final Dossier Sections                      ││
│  │  WRITER_STRATEGY ──────┤                                                  ││
│  │  WRITER_OPPORTUNITY ───┤                                                  ││
│  │  WRITER_CLIENT_SPEC ───┘                                                  ││
│  │                                                                           ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.4 Context Packs vs Merged Claims

**These are SEPARATE concepts.** Many people conflate them - don't.

| Concept | Purpose | When Built | Contents |
|---------|---------|------------|----------|
| **Claims** | Atomic facts | After each research step | Individual verifiable statements |
| **Merged Claims** | Deduplicated facts | At Step 7b (Insight) only | All claims, duplicates removed |
| **Context Pack** | Efficiency tool | At strategic points | Compact summary for downstream |

**Context Packs are built at TWO strategic points:**

1. **After Deep Research (Step 3-4):**
   - Entity Research produces claims → PRODUCE_CLAIMS prompt
   - Same step also produces → CONTEXT_PACK prompt
   - This context pack feeds into enrichment steps (5a, 5b, 5c)

2. **After Insight (Step 7b):**
   - Insight merges all claims → MERGE_CLAIMS prompt
   - Then builds → CONTEXT_PACK prompt
   - This context pack feeds into section writers

**Context Pack Structure:**
```json
{
  "context_pack": {
    "company": {
      "name": "Acme Corp",
      "domain": "acme.com",
      "key_facts": ["...", "..."]
    },
    "signals": [
      {"type": "permit", "headline": "$50M data center", "urgency": "HIGH"}
    ],
    "contacts": [
      {"name": "John Smith", "title": "VP Infrastructure", "relevance": "decision maker"}
    ],
    "merged_claims_count": 47,
    "client_context": {
      "what_we_do": "...",
      "why_we_win": "..."
    }
  }
}
```

**Why Context Packs Exist:**
- Token efficiency - Don't pass 47 full claims when a summary suffices
- Focus - Writers need relevant subset, not everything
- Speed - Smaller prompts = faster responses

### 3.5 How Section Writers Use Claims

Writers receive the FULL merged_claims array, not pre-filtered subsets. Each writer:

1. **Receives:** All merged claims + Dossier Plan + Context Pack
2. **Extracts:** Claims relevant to its section by type
3. **Writes:** Section content citing those claims
4. **Outputs:** Section content + sources[]

**Claim Type → Section Routing:**
| Claim Type | Primary Section | Also Used By |
|------------|-----------------|--------------|
| SIGNAL | Signals | Intro, Strategy |
| CONTACT | Contacts | Lead Intelligence |
| ENTITY | Lead Intelligence | Intro |
| RELATIONSHIP | Network Intelligence | Strategy |
| OPPORTUNITY | Opportunity Details | Intro |
| METRIC | Opportunity Details | The Math |
| ATTRIBUTE | Lead Intelligence | All |
| NOTE | Client Specific | Depends |

**Source Attribution:**
When a writer cites a claim, the claim's `source_url` and `source_name` automatically flow into the section's `sources[]` array. This is why dossiers have comprehensive source lists without manual curation.

### 3.6 Contacts Are NOT Claims

**Important distinction:** Contacts discovered via enrichment (Apollo, LinkedIn APIs) are stored in a **separate `contacts` table**, not as claims.

| Data | Storage | Why |
|------|---------|-----|
| Contact existence (name, title) | May be a claim | Discovered via research |
| Contact email, LinkedIn, phone | `contacts` table | Verified via API |
| Contact bio, tenure | `contacts` table | Enriched data |
| Per-contact copy | `copy` section | Generated from contact + claims |

**Contact Data Structure:**
```typescript
interface Contact {
  id: string;
  dossier_id: string;
  first_name: string;
  last_name: string;
  email: string | null;        // From Apollo/email verification
  phone: string | null;
  title: string;
  linkedin_url: string | null;
  bio: string | null;           // Researched/enriched
  tenure: string | null;
  is_primary: boolean;          // Exactly 1 per dossier
  source: 'apollo'|'linkedin'|'manual';
  // Client override fields
  contact_override: string | null;  // Custom instructions
  copy_enabled: boolean;            // Include in outreach
}
```

### 3.7 Claims Merge Logic (Step 7b)

The MERGE_CLAIMS prompt in Step 7b performs:

1. **Duplicate Detection:**
   - Same fact from different sources → Keep one, note multiple sources
   - Similar facts → Combine into strongest version

2. **Conflict Resolution:**
   - Contradictory claims → Flag for review, pick higher-confidence
   - Date conflicts → Prefer more recent source

3. **Timeline Resolution:**
   - Supersession detection (newer event makes older irrelevant)
   - Date normalization

4. **Confidence Assignment:**
   - Multiple sources → Higher confidence
   - Government source → Higher confidence
   - Recency → Higher confidence

**Merge Output:**
```json
{
  "merged_claims": [
    {
      "claim_id": "MERGED_001",
      "original_ids": ["er_003", "el_001"],  // Two sources merged
      "claim_type": "SIGNAL",
      "statement": "Acme Corp expanding into APAC market",
      "sources": [
        {"url": "...", "name": "Press Release"},
        {"url": "...", "name": "LinkedIn Post"}
      ],
      "confidence": "HIGH",  // Boosted by multiple sources
      "conflicts_resolved": []
    }
  ],
  "merge_stats": {
    "input_count": 47,
    "output_count": 31,
    "duplicates_merged": 12,
    "conflicts_resolved": 4
  }
}
```

### 3.8 Implementation Requirements for v2

**Claims Tables:**
```sql
-- Individual claims (before merge)
CREATE TABLE v2_claims (
    id UUID PRIMARY KEY,
    pipeline_run_id UUID REFERENCES v2_pipeline_runs(id),
    step_run_id UUID REFERENCES v2_step_runs(id),
    claim_id TEXT NOT NULL,           -- "er_001"
    claim_type TEXT NOT NULL,
    statement TEXT NOT NULL,
    entities TEXT[],
    date_in_claim DATE,
    source_url TEXT,
    source_name TEXT,
    source_tier TEXT,
    confidence TEXT,
    source_step TEXT,
    is_merged BOOLEAN DEFAULT false,
    merged_into TEXT,                 -- If merged, which MERGED_xxx
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Merged claims (after Step 7b)
CREATE TABLE v2_merged_claims (
    id UUID PRIMARY KEY,
    pipeline_run_id UUID REFERENCES v2_pipeline_runs(id),
    merged_claim_id TEXT NOT NULL,    -- "MERGED_001"
    original_claim_ids TEXT[],        -- ["er_003", "el_001"]
    claim_type TEXT NOT NULL,
    statement TEXT NOT NULL,
    sources JSONB NOT NULL,           -- [{url, name, tier}]
    confidence TEXT,
    conflicts_resolved JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Context packs
CREATE TABLE v2_context_packs (
    id UUID PRIMARY KEY,
    pipeline_run_id UUID REFERENCES v2_pipeline_runs(id),
    step_run_id UUID REFERENCES v2_step_runs(id),
    pack_type TEXT NOT NULL,          -- "post_deep_research" | "post_insight"
    pack_data JSONB NOT NULL,
    anchor_claim_ids TEXT[],          -- Claims this pack summarizes
    created_at TIMESTAMPTZ DEFAULT now()
);
```

**Processing Flow:**
```python
# After each research step
claims = await extract_claims(step_output, step_name)
await save_claims(pipeline_run_id, step_run_id, claims)

if step_name in ['entity_research', 'contact_discovery']:
    context_pack = await build_context_pack(claims, "post_deep_research")
    await save_context_pack(pipeline_run_id, step_run_id, context_pack)

# At Step 7b (Insight)
all_claims = await get_all_claims(pipeline_run_id)
merged_claims = await merge_claims(all_claims)
await save_merged_claims(pipeline_run_id, merged_claims)

context_pack = await build_context_pack(merged_claims, "post_insight")
await save_context_pack(pipeline_run_id, insight_step_run_id, context_pack)

# Pass to writers
for writer in SECTION_WRITERS:
    await run_writer(writer, {
        'merged_claims': merged_claims,
        'dossier_plan': dossier_plan,
        'context_pack': context_pack
    })
```

---

## Part 4: Current App Rendering Requirements

### 4.1 Database Schema (Must Match)

**Table: `dossiers`**
```typescript
interface Dossier {
  id: string;
  client_id: string;
  company_name: string;
  company_domain: string;
  lead_score: number;          // 0-100
  timing_urgency: string;      // 'HIGH'|'MEDIUM'|'LOW'
  primary_signal: string;
  status: string;              // 'skeleton'|'enriching'|'ready'|'archived'
  agents_completed: string[];  // ['find-lead', 'enrich-contacts', ...]

  // JSON sections (6 total)
  find_leads: FindLeadsSection;
  enrich_lead: EnrichLeadSection;
  copy: CopySection;
  insight: InsightSection;
  media: MediaSection;
  enrich_contacts: any;        // Legacy field
}
```

**Table: `contacts`**
```typescript
interface Contact {
  id: string;
  dossier_id: string;
  first_name: string;
  last_name: string;
  email: string | null;
  phone: string | null;
  title: string;
  linkedin_url: string | null;
  bio: string | null;
  tenure: string | null;
  is_primary: boolean;         // Only 1 per dossier
  source: 'apollo'|'linkedin'|'manual';
}
```

### 4.2 Section Schemas (Required Output Format)

**FindLeadsSection:**
```typescript
{
  company_name: string;
  company_snapshot: {
    domain: string;           // MUST be real domain like "acme.com"
    industry: string;
    location: string;
    size_estimate: string;
  };
  timing_urgency: 'HIGH'|'MEDIUM'|'LOW';
  lead_score: number;         // 0-100
  score_explanation: string;
  one_liner: string;          // Max 80 chars
  the_angle: string;          // 2-3 sentences
  primary_buying_signal: {
    signal_type: string;
    headline: string;
    description: string;
    date: string;
    source_url: string;
  };
  additional_signals: Signal[];
  sources: Source[];
}
```

**EnrichLeadSection:**
```typescript
{
  company_deep_dive: {
    revenue_estimate: string;
    employee_count: number;
    founded_year: number;
    full_address: string;
    coordinates: { lat: number; lng: number };
  };
  project_sites: {
    name: string;
    city: string;
    state: string;
    status: string;
    coordinates: { lat: number; lng: number };
  }[];
  additional_signals: Signal[];
  network_intelligence: {
    warm_paths: {
      name: string;
      title: string;
      linkedin_url: string;
      approach: string;
    }[];
    upcoming_opportunities: string[];
  };
  competitive_context: string;
  sources: Source[];
}
```

**CopySection:**
```typescript
{
  outreach: {
    contact_id: string;       // MUST match actual contact ID
    target_name: string;
    target_title: string;
    email_subject: string;    // <50 chars
    email_body: string;       // 60-75 words
    linkedin_message: string; // <250 chars
  }[];
  objections: { objection: string; response: string }[];
  conversation_starters: string[];
}
```

**InsightSection:**
```typescript
{
  the_math: {
    their_reality: string;
    the_opportunity: string;
    translation: string;
    bottom_line: string;
  };
  competitive_positioning: {
    insights_they_dont_know: string[];
    landmines_to_avoid: string[];
  };
  deal_strategy: {
    how_they_buy: string;
    unique_value_props: string[];
  };
  sources: Source[];
}
```

**MediaSection:**
```typescript
{
  logo_url: string;
  project_images: { url: string; caption: string }[];
}
```

---

## Part 5: Target Architecture

### 5.1 Folder Structure

```
/opt/automations/
├── api/
│   ├── main.py                    # Existing FastAPI
│   └── v2/
│       ├── __init__.py
│       ├── routes.py              # /v2/* endpoints
│       └── models.py              # Pydantic models
│
├── columnline_app/
│   ├── api_migration/             # This folder (specs)
│   │   ├── make_scenarios_and_csvs/
│   │   └── MIGRATION_PLAN.md      # This document
│   │
│   └── v2/                        # NEW PIPELINE
│       ├── __init__.py
│       │
│       ├── pipeline/
│       │   ├── __init__.py
│       │   ├── runner.py          # Main orchestrator
│       │   ├── step_executor.py   # Execute step with I/O capture
│       │   ├── variable_resolver.py
│       │   └── claims.py          # Claims extraction/merge
│       │
│       ├── prompts/
│       │   ├── __init__.py
│       │   ├── loader.py          # Load from Supabase
│       │   ├── interpolator.py    # {{variable}} substitution
│       │   └── migrator.py        # Import from CSV
│       │
│       ├── steps/
│       │   ├── __init__.py
│       │   ├── base.py            # BaseStep class
│       │   ├── search_builder.py
│       │   ├── signal_discovery.py
│       │   ├── entity_research.py
│       │   ├── contact_discovery.py
│       │   ├── enrich_lead.py
│       │   ├── enrich_opportunity.py
│       │   ├── client_specific.py
│       │   ├── enrich_contacts.py
│       │   ├── copy.py
│       │   ├── insight.py
│       │   ├── media.py
│       │   ├── dossier_plan.py
│       │   └── section_writers/
│       │       ├── intro.py
│       │       ├── signals.py
│       │       ├── lead_intelligence.py
│       │       ├── strategy.py
│       │       ├── opportunity.py
│       │       └── client_specific.py
│       │
│       ├── db/
│       │   ├── __init__.py
│       │   ├── models.py          # Pydantic models
│       │   └── repository.py      # CRUD operations
│       │
│       └── cli.py                 # CLI entry points
│
├── admin/                         # Streamlit dashboard
│   ├── app.py
│   └── pages/
│       ├── 1_prompts.py
│       ├── 2_runs.py
│       ├── 3_step_detail.py
│       └── 4_claims.py
│
└── workers/
    ├── ai.py                      # Existing
    └── v2_pipeline.py             # RQ worker
```

### 5.2 Database Schema (New v2 Tables)

```sql
-- Prompt Registry (replaces Google Sheets "Prompts" tab)
CREATE TABLE v2_prompts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_id TEXT UNIQUE NOT NULL,       -- "find-lead.search-builder"
    step TEXT NOT NULL,                    -- "find-lead"
    name TEXT NOT NULL,                    -- "Search Builder"
    stage TEXT NOT NULL,                   -- "FIND LEAD"
    produces_claims BOOLEAN DEFAULT false,
    merges_claims BOOLEAN DEFAULT false,
    produces_context_pack BOOLEAN DEFAULT false,
    current_version INTEGER DEFAULT 1,
    model TEXT DEFAULT 'gpt-4.1',
    temperature NUMERIC(3,2) DEFAULT 0.7,
    max_tokens INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Prompt Versions (full history)
CREATE TABLE v2_prompt_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_id TEXT NOT NULL REFERENCES v2_prompts(prompt_id),
    version_number INTEGER NOT NULL,
    content TEXT NOT NULL,                 -- Full prompt with {{variables}}
    change_notes TEXT,
    created_by TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(prompt_id, version_number)
);

-- Pipeline Runs
CREATE TABLE v2_pipeline_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id),
    dossier_id UUID,                       -- FK to dossiers table when created
    seed JSONB,
    status TEXT DEFAULT 'pending',
    current_step TEXT,
    steps_completed TEXT[] DEFAULT '{}',
    config JSONB DEFAULT '{}',
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Step Runs (I/O capture)
CREATE TABLE v2_step_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_run_id UUID NOT NULL REFERENCES v2_pipeline_runs(id),
    step TEXT NOT NULL,
    prompt_id TEXT,
    prompt_version INTEGER,
    status TEXT DEFAULT 'pending',
    input_variables JSONB DEFAULT '{}',
    interpolated_prompt TEXT,
    raw_output TEXT,
    parsed_output JSONB,
    model TEXT,
    tokens_in INTEGER,
    tokens_out INTEGER,
    duration_ms INTEGER,
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Claims
CREATE TABLE v2_claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_run_id UUID NOT NULL REFERENCES v2_pipeline_runs(id),
    step_run_id UUID REFERENCES v2_step_runs(id),
    claim_id TEXT NOT NULL,               -- "er_001"
    claim_type TEXT NOT NULL,             -- "SIGNAL|CONTACT|ENTITY|..."
    statement TEXT NOT NULL,
    entities TEXT[],
    date_in_claim DATE,
    source_url TEXT,
    source_name TEXT,
    source_tier TEXT,                     -- "GOV|PRIMARY|NEWS|OTHER"
    confidence TEXT,                      -- "HIGH|MEDIUM|LOW"
    source_step TEXT,
    is_merged BOOLEAN DEFAULT false,
    merged_into TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Context Packs
CREATE TABLE v2_context_packs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_run_id UUID NOT NULL REFERENCES v2_pipeline_runs(id),
    step_run_id UUID REFERENCES v2_step_runs(id),
    pack_type TEXT NOT NULL,              -- "signal_to_entity|entity_to_contacts|..."
    pack_data JSONB NOT NULL,
    anchor_claim_ids TEXT[],
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Variable Lineage
CREATE TABLE v2_variable_lineage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    step_run_id UUID NOT NULL REFERENCES v2_step_runs(id),
    variable_name TEXT NOT NULL,
    source_type TEXT NOT NULL,            -- "client_config|previous_step|seed|static"
    source_step TEXT,
    source_step_run_id UUID REFERENCES v2_step_runs(id),
    value_preview TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Last Run View (for dashboard)
CREATE VIEW v2_prompt_last_runs AS
SELECT DISTINCT ON (sr.prompt_id, pr.client_id)
    sr.prompt_id,
    pr.client_id,
    sr.id AS step_run_id,
    sr.status,
    sr.input_variables,
    sr.parsed_output AS output,
    sr.interpolated_prompt,
    sr.started_at,
    sr.duration_ms,
    sr.tokens_in,
    sr.tokens_out,
    sr.error_message
FROM v2_step_runs sr
JOIN v2_pipeline_runs pr ON sr.pipeline_run_id = pr.id
WHERE sr.status IN ('completed', 'failed')
ORDER BY sr.prompt_id, pr.client_id, sr.started_at DESC;
```

---

## Part 6: API Endpoints

### 6.1 Prompt Management

```
GET  /v2/prompts                     # List all prompts
GET  /v2/prompts/{prompt_id}         # Get prompt with current version
PUT  /v2/prompts/{prompt_id}         # Update (creates new version)
GET  /v2/prompts/{prompt_id}/versions
GET  /v2/prompts/{prompt_id}/last-run
POST /v2/prompts/{prompt_id}/test    # Test with custom variables
```

### 6.2 Pipeline Execution

```
POST /v2/runs                        # Start pipeline
GET  /v2/runs                        # List runs
GET  /v2/runs/{run_id}               # Get run with steps
POST /v2/runs/{run_id}/cancel        # Cancel running
```

### 6.3 Step Operations

```
GET  /v2/runs/{run_id}/steps/{step_run_id}  # Get step detail
POST /v2/runs/{run_id}/steps/{step}/rerun   # Re-run step
POST /v2/steps/{step}/run                    # Run step isolated (uses last state)
```

### 6.4 Claims

```
GET  /v2/runs/{run_id}/claims        # List claims for run
GET  /v2/claims/{claim_id}           # Get claim detail
```

---

## Part 7: Implementation Phases

### Phase 1: Database Setup (Day 1)

1. Create all v2_* tables in Supabase
2. Create indexes
3. Create views
4. Test with manual inserts

### Phase 2: Prompt Migration (Day 1-2)

1. Parse `Prompts.csv`
2. Extract all prompts with metadata
3. Insert into `v2_prompts` + `v2_prompt_versions`
4. Verify all 15+ prompts migrated

### Phase 3: Core Step Executor (Day 2-3)

```python
# columnline_app/v2/pipeline/step_executor.py

async def execute_step(
    pipeline_run_id: str,
    step: str,
    variables: dict,
    use_last_state: bool = False
) -> StepResult:
    """Execute a step with full I/O capture."""

    # 1. Get prompt from registry
    prompt = await get_prompt(step)

    # 2. If use_last_state, load variables from last run
    if use_last_state:
        variables = await get_last_input_variables(step)

    # 3. Create step_run record
    step_run_id = await create_step_run(pipeline_run_id, step, variables)

    # 4. Record variable lineage
    for var_name, value in variables.items():
        await record_lineage(step_run_id, var_name, value)

    # 5. Interpolate prompt
    interpolated = interpolate(prompt.content, variables)

    # 6. Call LLM
    result = await call_llm(interpolated, prompt.model, prompt.temperature)

    # 7. Update step_run with output
    await update_step_run(step_run_id, {
        'interpolated_prompt': interpolated,
        'raw_output': result.raw,
        'parsed_output': result.parsed,
        'tokens_in': result.tokens_in,
        'tokens_out': result.tokens_out,
        'duration_ms': result.duration,
        'status': 'completed'
    })

    # 8. Extract claims if step produces them
    if prompt.produces_claims:
        claims = await extract_claims(result.parsed, step, step_run_id)
        await save_claims(pipeline_run_id, step_run_id, claims)

    return result
```

### Phase 4: Individual Steps (Day 3-5)

Implement each step as a Python class:

```python
# columnline_app/v2/steps/search_builder.py

class SearchBuilderStep(BaseStep):
    step_id = "search_builder"
    prompt_id = "find-lead.search-builder"

    async def prepare_input(self, state: PipelineState) -> dict:
        return {
            'current_date': datetime.now().strftime('%Y-%m-%d'),
            'icp_config': state.icp_config,
            'industry_research': state.industry_research,
            'research_context': state.research_context,
            'seed': state.seed_data,
            'attempt_log': state.attempt_log,
            'exclude_domains': state.exclude_domains,
        }

    async def process_output(self, output: dict, state: PipelineState):
        state.step_outputs['search_builder'] = output
        state.search_plan = output
```

### Phase 5: Claims System (Day 5-6)

```python
# columnline_app/v2/pipeline/claims.py

async def extract_claims(output: dict, step: str, step_run_id: str) -> List[Claim]:
    """Extract atomic claims from step output."""
    # Call claims extraction prompt
    result = await call_llm(
        CLAIMS_EXTRACTION_PROMPT.format(narrative=json.dumps(output)),
        model='gpt-4.1'
    )

    claims = []
    for i, raw_claim in enumerate(result['claims']):
        claims.append(Claim(
            claim_id=f"{step[:2]}_{i+1:03d}",
            claim_type=raw_claim['type'],
            statement=raw_claim['statement'],
            entities=raw_claim['entities'],
            date_in_claim=raw_claim.get('date'),
            source_url=raw_claim['source_url'],
            source_tier=raw_claim['source_tier'],
            confidence=raw_claim['confidence'],
            source_step=step,
        ))

    return claims

async def merge_claims(claims: List[Claim]) -> List[Claim]:
    """Merge/deduplicate claims."""
    result = await call_llm(
        CLAIMS_MERGE_PROMPT.format(claims=json.dumps([c.dict() for c in claims])),
        model='gpt-4.1'
    )

    # Mark merged claims
    merged_ids = result['merged_into']
    for claim in claims:
        if claim.claim_id in merged_ids:
            claim.is_merged = True
            claim.merged_into = merged_ids[claim.claim_id]

    return [c for c in claims if not c.is_merged]
```

### Phase 6: Streamlit Dashboard (Day 6-7)

```python
# admin/pages/1_prompts.py

import streamlit as st
from columnline_app.v2.db import repository

st.title("Prompt Engineering Workbench")

# Sidebar: prompt list
prompts = repository.list_prompts()
selected = st.sidebar.selectbox("Select Prompt", [p.prompt_id for p in prompts])

if selected:
    prompt = repository.get_prompt(selected)
    last_run = repository.get_prompt_last_run(selected)

    # Main area: prompt editor
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader(f"Prompt: {prompt.name}")
        new_content = st.text_area("Prompt Content", prompt.content, height=400)

        if st.button("Save New Version"):
            repository.create_prompt_version(selected, new_content)
            st.success("Saved!")

    with col2:
        st.subheader("Config")
        model = st.selectbox("Model", ["gpt-4.1", "gpt-5.2", "o4-mini"])
        temp = st.slider("Temperature", 0.0, 1.0, prompt.temperature)

    # Last run display
    st.divider()
    st.subheader("Last Run")

    if last_run:
        st.text(f"Ran: {last_run.started_at} ({last_run.duration_ms}ms)")

        lcol, rcol = st.columns(2)
        with lcol:
            st.text("INPUT VARIABLES")
            st.json(last_run.input_variables)
        with rcol:
            st.text("OUTPUT")
            st.json(last_run.output)

    # Run button
    if st.button("Run Step (Use Last Input)"):
        result = execute_step_isolated(selected)
        st.json(result)
```

### Phase 7: Integration Testing (Day 7-8)

1. Run full pipeline for one client
2. Compare outputs to Make.com results
3. Verify claims extraction/merge works
4. Test step isolation (run single step with last state)
5. Validate dashboard functionality

---

## Part 8: Step Dependency Map

```
STAGE 1: PREP (load from client config)
    load_icp_config → load_industry_research → load_research_context → load_seed

STAGE 2: FIND LEAD
    search_builder (uses: icp, industry, research, seed)
        → signal_discovery (uses: search_plan, icp, industry)
            → entity_research (uses: signal, icp) [PRODUCES CLAIMS]
                → contact_discovery (uses: entity, icp) [PRODUCES CLAIMS]

STAGE 3: ENRICH (parallel)
    enrich_lead [PRODUCES CLAIMS]
    enrich_opportunity [PRODUCES CLAIMS]
    client_specific [PRODUCES CLAIMS]
    enrich_contacts (API calls, no LLM)

STAGE 4: INSIGHT
    insight [PRODUCES CLAIMS, MERGES CLAIMS, PRODUCES CONTEXT PACK]

STAGE 5: MEDIA
    media (API calls)

STAGE 6: DOSSIER PLAN + WRITERS (parallel)
    dossier_plan → routes claims to writers
        → writer_intro
        → writer_signals
        → writer_lead_intelligence
        → writer_strategy
        → writer_opportunity
        → writer_client_specific

STAGE 7: COPY (per contact)
    copy (uses: contact, claims, client_context)
    copy_client (uses: copy_output, client_overrides)
```

---

## Part 9: Key Files Reference

### From Current App (Must Match Output)

| File | Purpose |
|------|---------|
| `web/lib/types/database.ts` | TypeScript interfaces for dossier sections |
| `execution/dossier/lib/schemas/dossier.ts` | Zod validation schemas |
| `web/components/DossierView.tsx` | Main rendering component |
| `execution/dossier/lib/utils/supabase.ts` | `updateDossierSection()` function |

### From Make.com (Source)

| File | Purpose |
|------|---------|
| `MAIN_DOSSIER_PIPELINE.json` | Orchestration logic |
| `DOSSIER_FLOW_TEST - Prompts.csv` | All prompts with I/O |
| `DOSSIER_FLOW_TEST - DOSSIER SECTIONS.csv` | Section writers |
| `DOSSIER_FLOW_TEST - Inputs.csv` | Input configurations |

---

## Part 10: Success Criteria

1. **Prompt Editing** - Can edit any prompt in dashboard, save versions
2. **I/O Transparency** - Every step shows exact input → prompt → output
3. **Claims System** - Facts extracted, merged, routed to sections
4. **Step Isolation** - Can run any step using last state
5. **Lineage Tracing** - Can trace any variable back to source
6. **Output Parity** - New pipeline produces valid dossiers matching current schema
7. **Performance** - Similar or better than Make.com (60-90 min)
8. **Non-Breaking** - Existing Vercel app renders v2 dossiers correctly

---

## Appendix A: Full Prompt List

| prompt_id | Stage | Step | Produces Claims |
|-----------|-------|------|-----------------|
| find-lead.search-builder | FIND LEAD | 1 | NO |
| find-lead.signal-discovery | FIND LEAD | 2 | NO |
| find-lead.entity-research | FIND LEAD | 3 | YES |
| find-lead.contact-discovery | FIND LEAD | 4 | YES |
| enrich-lead.enrichment | ENRICH | 5a | YES |
| enrich-opportunity.research | ENRICH | 5b | YES |
| client-specific.research | ENRICH | 5c | YES |
| enrich-contacts.lookup | ENRICH | 6 | NO |
| enrich-contact.deep | ENRICH | 6.2 | NO |
| copy.outreach | COPY | 7a | NO |
| copy.client-override | COPY | 7.2 | NO |
| insight.analysis | INSIGHT | 7b | YES + MERGE |
| media.fetch | MEDIA | 8 | NO |
| dossier-plan.route | DOSSIER | 9 | NO |
| writer.intro | SECTION | intro | NO |
| writer.signals | SECTION | signals | NO |
| writer.lead-intelligence | SECTION | lead | NO |
| writer.strategy | SECTION | strategy | NO |
| writer.opportunity | SECTION | opportunity | NO |
| writer.client-specific | SECTION | client | NO |
| claims.extraction | UTILITY | - | - |
| claims.merge | UTILITY | - | - |
| context-pack.build | UTILITY | - | - |

---

## Appendix B: Variable Reference

| Variable | Source | Used By |
|----------|--------|---------|
| `{{current_date}}` | System | All steps |
| `{{icp_config}}` | Client config | Steps 1-7b |
| `{{industry_research}}` | Client config | Steps 1-4 |
| `{{research_context}}` | Client config | Steps 1-4, 7a |
| `{{seed}}` | Pipeline input | Step 1 |
| `{{search_plan}}` | Step 1 output | Step 2 |
| `{{signal}}` | Step 2 output | Steps 3-5 |
| `{{entity}}` | Step 3 output | Steps 4-6 |
| `{{contacts}}` | Step 4 output | Steps 6, 7a |
| `{{claims}}` | Accumulated | Step 7b |
| `{{merged_claims}}` | Step 7b | Section writers |
| `{{context_pack}}` | Step 7b | Section writers |
| `{{routed_claims}}` | Dossier plan | Each writer |

---

---

## Part 11: Current Columnline App Analysis

### 11.1 API Layer Architecture

**Pipeline-to-Database Communication:**
The TypeScript pipeline (`execution/dossier/`) writes to Supabase via a centralized utility layer:

| Helper Function | Purpose |
|-----------------|---------|
| `createDossier()` | Insert skeleton with status='skeleton' |
| `updateDossierSection(section, data, agent)` | Update JSON section + track agents_completed |
| `addContacts(dossierId, contacts[])` | Insert Contact rows |
| `addSourcesToDossier(dossierId, sources[], agent)` | Append deduplicated sources |
| `markSeedUsed(seedId, batchId, dossierId)` | Track seed pool consumption |

**Key File:** `/execution/dossier/lib/utils/supabase.ts` (1,977 lines)

**Pattern:** Service client with SERVICE_ROLE_KEY (bypasses RLS)

### 11.2 Next.js Portal API Routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/dossiers` | GET | List with filters, pagination, multi-list joins |
| `/api/dossiers/[id]` | GET/PATCH/DELETE | Single dossier CRUD |
| `/api/dossiers/bulk` | POST | Bulk archive, list assignment, delete |
| `/api/dossiers/[id]/release` | POST | Admin: release scheduled dossier |
| `/api/dossiers/[id]/rerun` | POST | Trigger GitHub Actions to re-run from step |
| `/api/contacts/dossier` | GET | Enriched contacts for a dossier |
| `/api/new-lead` | POST/GET | Client portal lead request (2/day quota) |
| `/api/lists` | CRUD | Dossier organization lists |
| `/api/cron/generate` | POST | Scheduled drip batch generation |
| `/api/cron/release` | POST | Release queued dossiers at configured time |

### 11.3 Dossier Rendering Flow

```
Database (Supabase)
    │
    ├─ dossiers table (6 JSONB sections)
    ├─ contacts table (1:N join)
    └─ dossier_lists + lists (junction)
    │
    ▼
API Routes (/api/dossiers)
    ├─ RLS filters by client_id
    ├─ Visibility filter (released_at)
    ├─ Joins: contacts, lists, batch info
    │
    ▼
Transform Layer (transformDossier)
    ├─ Flattens JSONB sections
    ├─ Maps enums (timing_urgency → UrgencyLevel)
    ├─ Normalizes nested objects
    ├─ Sanitizes URLs (LLM outputs literal "null")
    │
    ▼
DossierView Component (12+ sections)
    ├─ Header (logo, score, release date)
    ├─ Why Now (signals with sources)
    ├─ Company Intel (revenue, employees, phones)
    ├─ Verified Contacts (primary first)
    ├─ Enriched Contacts (fetched separately)
    ├─ Project Sites (coordinates, status)
    ├─ The Math (structured 4-part)
    ├─ Strategic Insights
    ├─ Decision-Making Process
    ├─ Deal Strategy
    ├─ Network Intelligence
    ├─ Outreach Copy (per contact)
    ├─ Objections & Responses
    └─ Sources (deduplicated)
```

### 11.4 Critical Data Contracts

**Dossier Status Lifecycle:**
```
skeleton → enriching → ready → archived
                    └─→ superseded (by newer dossier)
```

**Agent Completion Tracking:**
```typescript
agents_completed: ['find-lead', 'enrich-contacts', 'enrich-lead',
                   'write-copy', 'insight', 'enrich-media']
// When all 6 complete → status = 'ready'
```

**Multi-List Support:**
- Junction table: `dossier_lists` (dossier_id, list_id)
- Backward compatible with legacy `list_id` field

### 11.5 Release & Scheduling

**Drip Automation:**
- Client fields: `drip_enabled`, `drip_frequency`, `drip_day`, `drip_next_run`
- Dossier fields: `release_date` (DATE), `released_at` (TIMESTAMP)
- Visibility: `released_at IS NULL OR released_at <= now()`

**Timezone Handling:**
- Client timezone stored, converted to UTC for release calculations
- `calculateReleaseTime(timezone, releaseHour)` in cron route

---

## Part 12: Migration Risks & Safeguards

### 12.1 Critical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Schema mismatch** | Dossiers won't render | v2 must output exact same JSONB structure as v1 |
| **Agent name drift** | Status never reaches 'ready' | v2 uses same agent names: 'find-lead', 'enrich-contacts', etc. |
| **Missing transform handling** | UI crashes on null values | transformDossier() has extensive fallback chains - test all edge cases |
| **Contact ID mismatch** | Copy section references wrong contacts | contact_id in CopySection.outreach[] must match contacts table |
| **Source deduplication** | Duplicate sources in UI | addSourcesToDossier() dedupes by URL - v2 must do same |
| **Supersede logic** | Duplicate dossiers | v2 must check for existing domain before deep research |
| **Seed pool state** | Seeds never marked used | markSeedUsed() must be called after successful dossier creation |

### 12.2 Non-Breaking Patterns

**v2 must continue to:**
1. Write to same `dossiers` table (not separate v2_dossiers)
2. Use same section names: `find_leads`, `enrich_lead`, `copy`, `insight`, `media`
3. Track `agents_completed` with same agent names
4. Set status='ready' only when all 6 agents complete
5. Insert contacts with proper `dossier_id` foreign key
6. Support `is_primary` flag on contacts (exactly 1 per dossier)

**v2 tables are additive:**
- `v2_prompts` - New prompt registry
- `v2_pipeline_runs` - Execution tracking (links to dossiers.id)
- `v2_step_runs` - I/O capture
- `v2_claims` - Claims system (new feature)
- `v2_context_packs` - Context routing (new feature)

### 12.3 Integration Points

**GitHub Actions Triggers:**
- `/api/new-lead` → `process-new-lead.yml`
- `/api/dossiers/[id]/rerun` → `rerun-dossier.yml`
- v2 can use same triggers OR run directly on automations droplet

**Supabase RLS:**
- Portal uses anon/user key with RLS filtering
- Pipeline uses SERVICE_ROLE_KEY (bypasses RLS)
- v2 must also use SERVICE_ROLE_KEY for writes

### 12.4 Testing Checklist

Before any v2 dossier goes to production:

- [ ] All 6 JSONB sections present and valid
- [ ] `agents_completed` has all 6 entries
- [ ] `status` = 'ready'
- [ ] Contacts inserted with correct foreign key
- [ ] One contact marked `is_primary = true`
- [ ] Sources deduplicated
- [ ] `lead_score` extracted to root level
- [ ] `timing_urgency` extracted to root level
- [ ] `primary_signal` extracted to root level
- [ ] DossierView renders without errors
- [ ] transformDossier() produces valid UiDossier
- [ ] EnrichedContactsList loads contacts

---

## Part 13: Recommended Migration Path

### 13.1 Phase 1: Shadow Mode (Week 1-2)

Run v2 pipeline in parallel with existing pipeline:
1. Same client, same seed
2. v2 writes to separate dossier (different batch_id)
3. Compare outputs section-by-section
4. Fix discrepancies

### 13.2 Phase 2: Canary Mode (Week 3)

Run v2 for 10% of new batches:
1. Route specific clients to v2
2. Monitor for rendering errors
3. Collect quality feedback

### 13.3 Phase 3: Full Migration (Week 4+)

1. v2 becomes default
2. v1 remains as fallback
3. Gradually deprecate Make.com scenarios

---

*Generated: January 2026*
*Version: 1.1 - Added current app analysis (Parts 11-13)*
