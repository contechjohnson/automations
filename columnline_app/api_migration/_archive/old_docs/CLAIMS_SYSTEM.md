# Claims System Architecture

This document describes the claims extraction, merging, and context pack system used in the dossier pipeline.

---

## Overview

The claims system is a **fact management framework** that:
1. Extracts atomic, verifiable facts from research steps
2. Accumulates claims across the pipeline
3. Merges and reconciles claims at a single synchronization point
4. Builds focused context packs for downstream efficiency
5. Routes claims to section writers via a dossier plan

---

## What is a Claim?

A **claim** is an atomic, verifiable fact with evidence. It follows the principle: **one fact per claim**.

### Claim Structure

```json
{
  "claim_id": "entity_001",
  "claim_type": "SIGNAL",
  "statement": "Ontario removed the EA requirement for Eagle's Nest project under Bill 5",
  "entities": ["Wyloo Metals", "Eagle's Nest", "Ontario"],
  "date_in_claim": "2025-07-04",
  "source_url": "https://ero.ontario.ca/...",
  "source_name": "Environmental Registry of Ontario",
  "source_tier": "GOV",
  "confidence": "HIGH"
}
```

### Claim ID Convention

Each claim ID is prefixed by the step that produced it:
- `search_001` - Search & Signal step
- `entity_001` - Entity Research step
- `contact_001` - Contact Discovery step
- `lead_001` - Enrich Lead step
- `opp_001` - Enrich Opportunity step
- `client_001` - Client Specific step

### Claim Types

| Type | Description | Example |
|------|-------------|---------|
| **SIGNAL** | Trigger event indicating buying intent | "Ontario removed EA requirement in July 2025" |
| **CONTACT** | Information about a person | "Sylvain Goyette is VP Projects at Wyloo" |
| **ENTITY** | Information about a company | "Wyloo is a subsidiary of Tattarang Pty Ltd" |
| **RELATIONSHIP** | How entities connect | "Hatch Ltd is the EPCM partner for Eagle's Nest" |
| **OPPORTUNITY** | Project/deal information | "Eagle's Nest is a 3,000 tpd underground nickel mine" |
| **METRIC** | Quantified information | "Project capital cost estimated at $1.2 billion" |
| **ATTRIBUTE** | Simple data points | "Wyloo Canada phone: (807) 285-4808" |
| **NOTE** | Catch-all for other information | "Local community support is strong" |

### Source Tiers

| Tier | Description | Trust Level |
|------|-------------|-------------|
| **GOV** | Government, regulator, official registry | Highest |
| **PRIMARY** | Company website, official announcement | High |
| **NEWS** | Reputable news, trade publication | Medium |
| **OTHER** | Blog, forum, directory | Low |

### Confidence Levels

| Level | Criteria |
|-------|----------|
| **HIGH** | GOV or PRIMARY source, specific and verifiable |
| **MEDIUM** | NEWS source, or PRIMARY but vague |
| **LOW** | OTHER source, or conflicting info exists |

---

## When Claims Are Extracted

Claims are extracted from **every research step** using the `CLAIMS_EXTRACTION` prompt.

### Steps That Produce Claims

| Step | Row in Prompts.csv | Claims Column |
|------|-------------------|---------------|
| 1. Search & Signal | Row 2-3 | I2, I3 |
| 3. Entity Research | Row 4 | I4 |
| 4. Contact Discovery | Row 5 | I5 |
| 5a. Enrich Lead | Row 6 | I6 |
| 5b. Enrich Opportunity | Row 7 | I7 |
| 5c. Client Specific | Row 8 | I8 |

### What Does NOT Produce Claims

- **07B Insight** - Merges claims but doesn't produce new ones (consumes only)
- **08 Media** - Produces media assets, not claims
- **09 Dossier Plan** - Routes claims, doesn't produce them
- **Section Writers** - Consume claims, don't produce them

### Claims Extraction Rules

From the `CLAIMS_EXTRACTION` prompt:

1. **Extract EVERYTHING** - 50-200 claims from deep research
2. **One fact per claim** - Split compound sentences
3. **Preserve sources** - Include `source_url` when mentioned
4. **Dates as YYYY-MM-DD** - First of month if only month known
5. **Contact claims include org** - Add their company to entities
6. **When unclear, use NOTE** - With LOW confidence

---

## Claims Accumulation (Before Merge)

As the pipeline runs, claims accumulate in column I of the Prompts sheet:

```
Pipeline Flow:
                                           ┌── I6: Lead claims ────┐
Search → Entity → Contacts → Parallel ─────┼── I7: Opportunity ────┼──→ 07B Insight
   I3      I4        I5                    └── I8: Client claims ──┘

Each step APPENDS claims. Nothing is merged yet.
```

**Key point:** Before step 07B, claims exist separately. They may duplicate, contradict, or overlap - that's fine. The merge step resolves this.

---

## Claims Merge (Step 07B)

The **single merge point** is step 07B (Insight). This is the only place claims are reconciled.

### What Merge Does

1. **Contact Resolution** - Groups claims about the same person
2. **Timeline Resolution** - Sequences events, handles supersession
3. **Conflict Detection** - Flags contradictory claims
4. **Ambiguity Flagging** - Marks items needing human review
5. **Pass-Through** - Claims that need no reconciliation

### Contact Resolution

The merge identifies when multiple claims refer to the same person:

```json
{
  "contact_id": "contact_001",
  "name": "Sylvain Goyette",
  "current_role": "VP Projects",
  "organization": "Wyloo Metals",
  "evidence_claims": ["entity_012", "contact_003", "lead_007"],
  "resolution": "SAME_PERSON",
  "confidence": "HIGH"
}
```

**Decision framework:**
- Same name + same company + similar time = SAME_PERSON
- Same name + different companies = DIFFERENT_PERSON
- Same name + same company + different titles = SAME_PERSON (title varies)
- Ambiguous = UNSURE (keep both, flag)

### Timeline Resolution

Events are sequenced with status progression:

| Status | Meaning |
|--------|---------|
| ANNOUNCED | Initial projection |
| REVISED | Updated projection (supersedes ANNOUNCED) |
| ACTUAL | Confirmed happened (supersedes all) |
| SUPERSEDED | No longer relevant |

```json
{
  "timeline_id": "timeline_001",
  "subject": "Construction start",
  "current_status": "Started September 2025",
  "current_date": "2025-09-01",
  "history": [
    {"date_reported": "2024-12", "status": "ANNOUNCED", "value": "June 2025", "claim_id": "entity_012"},
    {"date_reported": "2025-03", "status": "REVISED", "value": "September 2025", "claim_id": "lead_003"}
  ]
}
```

### Conflict Detection

Contradictory claims are flagged:

```json
{
  "conflict_id": "conflict_001",
  "type": "ATTRIBUTE",
  "description": "HQ location conflict",
  "claims_involved": ["entity_012", "lead_045"],
  "values": {
    "entity_012": "Perth",
    "lead_045": "Sydney"
  },
  "recommendation": "Prefer entity_012 (GOV source)",
  "resolution_logic": "GOV > PRIMARY > NEWS"
}
```

### Merge Output Structure

```json
{
  "reconciliation_timestamp": "2025-01-11T12:00:00Z",
  "target_entity": "Wyloo Metals",
  "summary": {
    "total_claims": 150,
    "contacts_resolved": 8,
    "timelines_resolved": 3,
    "conflicts_found": 1,
    "ambiguous_items": 2,
    "passed_through": 120
  },
  "contacts_resolved": [...],
  "timelines_resolved": [...],
  "conflicts": [...],
  "ambiguous": [...],
  "pass_through": ["claim_003", "claim_007", ...]
}
```

---

## Context Packs

A **context pack** is NOT the same as merged claims. It's an **efficiency tool** - a focused, compact summary that passes forward only what the next step needs.

### Why Context Packs?

1. **Token efficiency** - Don't pass all 150+ claims to every step
2. **Focus** - Give each step exactly what it needs
3. **Prevent redundancy** - Explicit "do not repeat" sections
4. **Establish ground truth** - Canonical identity locked in

### When Context Packs Are Built

| After Step | Context Pack Type | Purpose |
|------------|------------------|---------|
| 3. Entity Research | `signal_to_entity` | Before Contact Discovery |
| 4. Contact Discovery | `entity_to_contacts` | Before Parallel Enrichment |
| 7b. Insight | `contacts_to_enrichment` | Before Section Writers |

### Context Pack Types

#### Type 1: SIGNAL_TO_ENTITY (Before Entity Research)

Built after Signal Discovery. Maps the discovered signal to a candidate company.

```json
{
  "context_type": "signal_to_entity",
  "signal_summary": {
    "signal_type": "REGULATORY",
    "description": "Ontario removed EA requirement for mining project",
    "date": "2025-07-04"
  },
  "candidate_entity": {
    "name": "Wyloo Metals",
    "confidence": "HIGH",
    "why": "Named in the regulatory filing"
  },
  "known_facts": ["...facts already established..."],
  "key_questions": ["What Entity Research should answer"],
  "search_hints": ["Suggested queries/sources"]
}
```

#### Type 2: ENTITY_TO_CONTACTS (Before Contact Discovery)

Built after Entity Research. Establishes **canonical identity** - this is CRITICAL.

```json
{
  "context_type": "entity_to_contacts",
  "canonical_target": {
    "name": "Wyloo Metals",
    "entity_type": "Subsidiary",
    "domains": ["wyloocanada.com", "wyloometals.com"],
    "hq_location": "West Perth, Australia"
  },
  "corporate_structure": {
    "parent": "Tattarang Pty Ltd",
    "subsidiaries": ["Wyloo Canada"],
    "notes": "Andrew Forrest's investment vehicle"
  },
  "key_project": {
    "name": "Eagle's Nest",
    "location": "Ontario, Canada",
    "stage": "Pre-construction"
  },
  "partner_organizations": [
    {
      "name": "Hatch Ltd",
      "role": "EPCM partner",
      "domains": ["hatch.com"],
      "notes": "Contacts may be here"
    }
  ],
  "anchor_claims": ["entity_001", "entity_012", "..."],
  "key_questions": ["Who selects contractors?"],
  "do_not_repeat": ["Entity identity - resolved", "Domain discovery - complete"]
}
```

#### Type 3: CONTACTS_TO_ENRICHMENT (Before Parallel Block)

Built after Contact Discovery. Sets up the parallel enrichment phase.

```json
{
  "context_type": "contacts_to_enrichment",
  "canonical_target": {
    "name": "Wyloo Metals",
    "domains": ["wyloometals.com"]
  },
  "key_project": {
    "name": "Eagle's Nest",
    "stage": "Pre-construction",
    "timeline": "Q2 2027 target"
  },
  "confirmed_contacts": [
    {
      "name": "Sylvain Goyette",
      "title": "VP Projects",
      "domain_for_email": "wyloocanada.com",
      "why_they_matter": "Owns project execution",
      "priority": "HIGH"
    }
  ],
  "enrichment_questions": {
    "enrich_lead": ["Network questions"],
    "enrich_opportunity": ["Sizing questions"],
    "client_specific": ["Client questions"],
    "enrich_contacts": ["Email verification"]
  },
  "do_not_repeat": ["Entity resolution", "Contact identification"]
}
```

### Context Pack Rules

1. **Be selective** - Include what next step NEEDS
2. **Establish ground truth** - `canonical_target` and `anchor_claims` are FACTS
3. **Include domains** - Critical for email lookup
4. **Surface partner orgs** - Contacts may be there
5. **Specific questions** - "Who signs POs?" not "Learn about procurement"
6. **Explicit do_not_repeat** - Prevent duplicate work
7. **Token limit** - Aim for 2,000-4,000 tokens

---

## Flow to Section Writers

Section writers receive THREE things:

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│   ALL MERGED CLAIMS ─────────────────────────────────────────┐   │
│   (full access to everything)                                │   │
│                                                              │   │
│   DOSSIER PLAN ──────────────────────────────────────────────┼──→│ SECTION WRITER
│   (routing map: which claims → which section)                │   │
│                                                              │   │
│   CONTEXT PACK ──────────────────────────────────────────────┘   │
│   (efficient summary for orientation)                            │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Dossier Plan Role

The Dossier Plan (step 9) creates a **routing map** that tells each writer which claims are relevant to its section:

```json
{
  "section_routing": {
    "INTRO": {
      "claim_ids": ["entity_001", "entity_007", "signal_003"],
      "resolved_object_ids": [],
      "coverage_notes": "Has entity name, type, parent. Missing: founding year."
    },
    "SCORE": {
      "claim_ids": ["signal_001", "signal_002", "signal_005"],
      "resolved_object_ids": ["timeline_001"],
      "coverage_notes": "3 signals, clear timing."
    }
  },
  "unmapped_claims": {
    "claim_ids": ["note_099"],
    "reasons": {
      "note_099": "Low relevance - general industry note"
    }
  }
}
```

### What Writers Receive

Each section writer gets:

1. **Routed Claims** - The claims assigned to that section by the dossier plan
2. **Resolved Objects** - Contacts, signals, timelines from the merge
3. **Client Context** - ICP, services, differentiators

Example writer input:

```
## Routed Claims
{{claims}}           ← Claims assigned to this section

## Resolved Objects
{{resolved_contacts}}
{{resolved_signals}}

## Client Context
Client: {{clientName}}
Services: {{clientServices}}
```

### Claims Can Appear in Multiple Sections

The same claim can be routed to multiple writers:
- A SIGNAL claim might go to both SCORE and WHY_THEYLL_BUY_NOW
- A CONTACT claim might go to both VERIFIED_CONTACTS and DEAL_STRATEGY

### Source Auto-Population

Sources are automatically collected from claims used by writers:

```javascript
// Pseudocode from DOSSIER SECTIONS CSV
const sources = [];
for (const section of sections) {
  for (const claimId of section.claim_ids) {
    const claim = claims.find(c => c.claim_id === claimId);
    if (claim.source_url && !seenUrls.has(claim.source_url)) {
      sources.push({
        url: claim.source_url,
        name: claim.source_name,
        used_in: [section.name]
      });
    }
  }
}
```

---

## Contacts: A Special Case

Contacts have their own enrichment path and storage:

### Per-Contact Data

Each contact has:
- **Bio** - Background summary
- **Relation to Signal** - Why they matter
- **Outreach Copy** - Email + LinkedIn messages
- **Client Override Settings** - Client-specific customization

### Contact Enrichment Flow

```
Contact Discovery (step 4)
        │
        ▼
Enrich Contacts (step 6)
        │
        ├── For each contact:
        │   └── 6.2 ENRICH_CONTACT_TEMPLATE
        │       ├── LinkedIn research
        │       ├── Web research
        │       ├── Email verification
        │       └── Copy generation
        │
        ▼
Contacts stored separately (not just in claims)
```

### Contact Copy Fields

| Field | Description |
|-------|-------------|
| EMAIL_COPY | Generic outreach email |
| LINKEDIN_COPY | Generic LinkedIn message (<250 char) |
| CLIENT_EMAIL_COPY | Personalized with client context |
| CLIENT_LINKEDIN_COPY | Personalized LinkedIn message |

---

## Summary: Claims vs Context Packs

| Aspect | Claims | Context Packs |
|--------|--------|---------------|
| **What** | Atomic facts with evidence | Focused summaries for next step |
| **When produced** | Every research step | Strategic points (after Entity, Contacts, Insight) |
| **Purpose** | Evidence trail | Token efficiency |
| **Size** | 50-200+ per dossier | 2,000-4,000 tokens each |
| **Contains** | Individual facts | Curated subset + ground truth |
| **Merge** | Once at 07B Insight | Never merged |
| **Used by** | Section writers (via routing) | Next step in pipeline |

---

## Pipeline Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  SEARCH & SIGNAL ──────────────────────────────────────────────────────────│
│       │                                                                     │
│       ├─ Extract claims → I3                                               │
│       │                                                                     │
│       ▼                                                                     │
│  ENTITY RESEARCH ──────────────────────────────────────────────────────────│
│       │                                                                     │
│       ├─ Extract claims → I4                                               │
│       ├─ Build context pack (signal_to_entity) → K4                        │
│       │                                                                     │
│       ▼                                                                     │
│  CONTACT DISCOVERY ────────────────────────────────────────────────────────│
│       │                                                                     │
│       ├─ Extract claims → I5                                               │
│       ├─ Build context pack (entity_to_contacts) → K5                      │
│       │                                                                     │
│       ▼                                                                     │
│  PARALLEL ENRICHMENT ──────────────────────────────────────────────────────│
│       │                                                                     │
│       ├─ Enrich Lead → claims I6                                           │
│       ├─ Enrich Opportunity → claims I7                                    │
│       ├─ Client Specific → claims I8                                       │
│       ├─ Enrich Contacts → per-contact data                                │
│       │                                                                     │
│       ▼                                                                     │
│  07B INSIGHT (SYNC POINT) ─────────────────────────────────────────────────│
│       │                                                                     │
│       ├─ MERGE all claims (I3-I8)                                          │
│       ├─ Resolve contacts, timelines, conflicts                            │
│       ├─ Generate strategic insights                                        │
│       ├─ Build context pack (contacts_to_enrichment) → K12                 │
│       │                                                                     │
│       ▼                                                                     │
│  DOSSIER PLAN ─────────────────────────────────────────────────────────────│
│       │                                                                     │
│       ├─ Route claims → sections                                           │
│       ├─ Identify gaps                                                      │
│       │                                                                     │
│       ▼                                                                     │
│  SECTION WRITERS (PARALLEL) ───────────────────────────────────────────────│
│       │                                                                     │
│       ├─ Each receives: routed claims + resolved objects + context pack    │
│       ├─ Each writes: its assigned section fields                          │
│       │                                                                     │
│       ▼                                                                     │
│  DOSSIER ASSEMBLY ─────────────────────────────────────────────────────────│
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```
