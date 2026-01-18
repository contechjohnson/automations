# Columnline App Migration Directive

## Overview

This document captures the analysis of Make.com workflow scenarios and Google Sheet test harness for migration to production code on the automations droplet.

**Current State:** Make.com visual workflows + Google Sheet "thinking surface"
**Target State:** Python workers on automations droplet + admin dashboard

---

## Make.com Blueprint Analysis

### Source Files Location
```
columnline_app/api_migration/make_scenarios_and_csvs/
```

### Discovered Blueprint Files (10 Core + 6 Writers + 3 Setup)

| File | Purpose | Execution Mode |
|------|---------|----------------|
| `MAIN_DOSSIER_PIPELINE.json` | Main orchestration (40 modules) | Sequential + Polling |
| `01AND02_SEARCH_AND_SIGNAL.blueprint.json` | Signal discovery | Sync subscenario |
| `03_AND_04_SEQUENTIAL_DEEP_RESEARCH_STEPS.blueprint.json` | Entity + Contact research | Async (polled) |
| `05A_ENRICH_LEAD.blueprint.json` | Lead enrichment | Async parallel |
| `05B_ENRICH_OPPORTUNITY.blueprint.json` | Opportunity sizing | Async parallel |
| `05C_CLIENT_SPECIFIC.blueprint.json` | Client-specific research | Async parallel |
| `06_ENRICH_CONTACTS.blueprint.json` | Batch contact enrichment | Async (polled) |
| `06.2_ENRICH_CONTACT.blueprint.json` | Single contact enrichment | Iterator child |
| `07B_INSIGHT.blueprint.json` | Agent insights | Sync |
| `08_MEDIA.blueprint.json` | Media/news enrichment | Async parallel |
| `09_DOSSIER_PLAN.blueprint.json` | Dossier structure planning | Async (polled) |
| `WRITER_*.blueprint.json` (6 files) | Section writers | Async parallel |
| `_0A_CLIENT_ONBOARDING.blueprint.json` | Client setup | Manual trigger |
| `_0B_PREP_INPUTS.blueprint.json` | Input preparation | Manual trigger |
| `_0C_BATCH_COMPOSER.blueprint.json` | Batch processing | Manual trigger |

---

## Main Pipeline Flow Analysis

From `MAIN_DOSSIER_PIPELINE.json` (40 modules):

### Phase 1: Load Inputs (Modules 1-8)
```
1. Manual trigger (ENTRY_POINT)
2. Google Sheets: Get ICP_CONFIG (Inputs!B2)
3. Google Sheets: Get INDUSTRY_RESEARCH (Inputs!B3)
4. Google Sheets: Get RESEARCH_CONTEXT (Inputs!B4)
5. Google Sheets: Get SEED_DATA (Inputs!B5)
6. Google Sheets: Get CLAIMS_PROMPT (Inputs!B8)
7. Google Sheets: Get CLAIMS_MERGE_PROMPT (Inputs!B9)
8. Google Sheets: Get CONTEXT_PACK_PROMPT (Inputs!B10)
```

### Phase 2: Signal Discovery (Modules 9-11)
```
9. SET_SCENARIO_IDS (variable setup)
10. RUN_SYNC_SEARCH_AND_SIGNAL (subscenario call - BLOCKING)
    - Model: gpt-4.1
    - Tools: web_search_preview
    - Prompts from: Prompts!C2 (SEARCH_BUILDER_PROMPT)
11. Process results
```

### Phase 3: Deep Research with Polling (Modules 12-21)
```
12. START_ASYNC_DEEP_ENTITY_AND_CONTACTS (subscenario call - NON-BLOCKING)
    - Model: o4-mini-deep-research (gpt-5.2 in some)
    - Tools: web_search_preview
    - background: true
    - max_output_tokens: 200000
13. SET "entity_contacts_done" = FALSE
14. BasicRepeater (max: 100 iterations)
15. Sleep 30 seconds
16. HTTP GET status check
17. Break if done
```

### Phase 4: Parallel Enrichment Batch 1 (Modules 22-30)
```
22. START_ASYNC_ENRICH_LEAD (background)
23. START_ASYNC_ENRICH_MEDIA (background)
24. START_ASYNC_ENRICH_OPPORTUNITY (background)
25. START_ASYNC_CLIENT_SPECIFIC (background)
26. SET "parallel_batch_1_done" = FALSE
27. BasicRepeater (polling loop)
28. Sleep 30 seconds
29. HTTP GET status check
30. Break if all done
```

### Phase 5: Sync Insight (Modules 31-32)
```
31. RUN_SYNC_AGENT_INSIGHT (blocking)
32. Process insight results
```

### Phase 6: Writers + Contact Enrichment (Modules 33-40)
```
33. START_ASYNC_DOSSIER_PLAN_AND_WRITERS
    - Triggers parallel writer subscenarios:
      - WRITER_INTRO
      - WRITER_LEAD_INTELLIGENCE
      - WRITER_OPPORTUNITY_DETAILS
      - WRITER_SIGNALS
      - WRITER_STRATEGY
      - WRITER_CLIENT_SPECIFIC
34. START_ASYNC_BATCH_ENRICH_CONTACTS
35. SET "final_batch_done" = FALSE
36. BasicRepeater (polling loop)
37. Sleep 30 seconds
38. HTTP GET status check
39. Break if done
40. Final assembly
```

---

## Polling Pattern Analysis

Make.com implements async operations with a polling loop:

```
Pattern:
1. Call subscenario (background: true)
2. Set done_flag = FALSE
3. Loop:
   a. Sleep 30 seconds
   b. HTTP check completion status
   c. If complete, BREAK
   d. If max iterations, timeout error
```

### Equivalent Python Implementation

```python
# Conceptual - NOT actual implementation
async def poll_async_step(response_id: str, timeout_seconds: int = 600):
    """Poll for async completion - mirrors Make.com BasicRepeater pattern."""
    start = time.time()
    while time.time() - start < timeout_seconds:
        status = await check_completion(response_id)
        if status["complete"]:
            return status["result"]
        await asyncio.sleep(30)
    raise TimeoutError(f"Step {response_id} did not complete in {timeout_seconds}s")
```

---

## Google Sheet Structure Analysis

### Sheet: Inputs
| Row | Cell B | Purpose |
|-----|--------|---------|
| 2 | ICP_CONFIG | Target signals, disqualifiers, titles, geography |
| 3 | INDUSTRY_RESEARCH | Buying signals, personas, timing constraints |
| 4 | RESEARCH_CONTEXT | Client info, differentiators, team |
| 5 | SEED_DATA | Discovery mode or specific seed |
| 8 | CLAIMS_PROMPT | Claims extraction template |
| 9 | CLAIMS_MERGE_PROMPT | Claims reconciliation template |
| 10 | CONTEXT_PACK_PROMPT | Context builder template |

### Sheet: Prompts
| Row | Col C (Prompt) | Col D (Live Input) |
|-----|----------------|-------------------|
| 2 | SEARCH_BUILDER_PROMPT | SEARCH_BUILDER_LIVE_INPUT |
| 4 | ENTITY_RESEARCH_PROMPT | ENTITY_RESEARCH_LIVE_INPUT |
| 6 | ENRICH_LEAD_PROMPT | ENRICH_LEAD_LIVE_INPUT |
| ... | ... | ... |

### Sheet: MASTER (Controls)
| Control | Purpose |
|---------|---------|
| PREP INPUT | YES/NO - Run input preparation |
| BATCH COMPOSER | YES/NO - Batch mode |
| NUMBER | Lead number (for batches) |
| CLIENT | Client ID |
| SEED | YES/NO - Use seed vs discovery |
| SCHEDULE | Scheduling flag |
| RELEASE AFTER _HRS | Delay before release |

---

## Model Usage Patterns

| Step | Model | Mode | Timeout |
|------|-------|------|---------|
| Search Builder | gpt-4.1 | sync | default |
| Entity Research | gpt-5.2 / o4-mini-deep-research | async (background=true) | 5min+ |
| Contact Discovery | o4-mini-deep-research | async | 5min+ |
| Enrich Lead | o4-mini-deep-research | async | 5min+ |
| Enrich Opportunity | o4-mini-deep-research | async | 5min+ |
| Client Specific | o4-mini-deep-research | async | 5min+ |
| Agent Insight | gpt-4.1 | sync | default |
| Writers | gpt-4.1 | async | 2min |

---

## Data Flow Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                       INPUTS (Google Sheets)                        │
│  ICP_CONFIG │ INDUSTRY_RESEARCH │ RESEARCH_CONTEXT │ SEED_DATA     │
└──────────────────────────────┬─────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 1: SIGNAL DISCOVERY (sync)                                   │
│  search_builder → signal_discovery                                  │
│  Output: candidate leads with signals                               │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 2: DEEP RESEARCH (async + poll)                              │
│  entity_research → contact_discovery                                │
│  Output: resolved entity, key contacts                              │
└─────────────────────────────────────────────────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  ENRICH_LEAD    │ │ ENRICH_OPP      │ │ CLIENT_SPECIFIC │
│  (async)        │ │ (async)         │ │ (async)         │
└─────────────────┘ └─────────────────┘ └─────────────────┘
              │                │                │
              └────────────────┼────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 3: INSIGHT SYNTHESIS (sync)                                  │
│  agent_insight                                                       │
│  Output: strategic analysis                                          │
└─────────────────────────────────────────────────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ WRITER_INTRO │ │ WRITER_LEAD  │ │ WRITER_...   │
│ (async)      │ │ (async)      │ │ (async)      │
└──────────────┘ └──────────────┘ └──────────────┘
              │                │                │
              └────────────────┼────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PHASE 4: ASSEMBLY                                                  │
│  Combine all sections → Final dossier                               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Proposed v2 Implementation

### Directory Structure (Conceptual)

```
automations/
├── workers/
│   └── pipeline/                    # NEW
│       ├── __init__.py
│       ├── runner.py               # Pipeline orchestration
│       ├── steps/
│       │   ├── signal_discovery.py
│       │   ├── entity_research.py
│       │   ├── contact_discovery.py
│       │   ├── enrich_lead.py
│       │   ├── enrich_opportunity.py
│       │   ├── client_specific.py
│       │   ├── agent_insight.py
│       │   └── writers/
│       │       ├── intro.py
│       │       ├── lead_intelligence.py
│       │       ├── opportunity_details.py
│       │       ├── signals.py
│       │       ├── strategy.py
│       │       └── client_specific.py
│       └── fixtures/               # Test data (from CSVs)
├── prompts/
│   └── dossier/                    # NEW prompt files
│       ├── search-builder.md
│       ├── entity-research.md
│       ├── contact-discovery.md
│       ├── enrich-lead.md
│       ├── claims-extract.md
│       ├── claims-merge.md
│       ├── context-pack.md
│       └── writers/
│           ├── intro.md
│           └── ...
└── admin/                          # NEW admin dashboard
    ├── templates/
    └── api.py
```

### Supabase v2 Tables (Conceptual)

```sql
-- Pipeline job tracking
CREATE TABLE pipeline_jobs_v2 (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  pipeline_version text DEFAULT 'v2',
  status text DEFAULT 'pending',  -- pending, running, completed, failed
  input jsonb NOT NULL,
  output jsonb,
  started_at timestamptz,
  completed_at timestamptz,
  error jsonb,
  created_at timestamptz DEFAULT now()
);

-- Step-level tracking
CREATE TABLE pipeline_steps_v2 (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id uuid REFERENCES pipeline_jobs_v2(id),
  step_name text NOT NULL,
  step_index int NOT NULL,
  status text DEFAULT 'pending',
  input jsonb,
  output jsonb,
  prompt_name text,
  model text,
  started_at timestamptz,
  completed_at timestamptz,
  runtime_seconds numeric,
  error jsonb
);

-- Structured dossier output
CREATE TABLE dossiers_v2 (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id uuid REFERENCES pipeline_jobs_v2(id),
  company_name text NOT NULL,
  domain text,
  status text DEFAULT 'draft',
  metadata jsonb,
  created_at timestamptz DEFAULT now()
);

-- Dossier sections
CREATE TABLE dossier_sections_v2 (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  dossier_id uuid REFERENCES dossiers_v2(id),
  section_key text NOT NULL,
  content jsonb NOT NULL,
  display_order int
);

-- Contacts discovered
CREATE TABLE dossier_contacts_v2 (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  dossier_id uuid REFERENCES dossiers_v2(id),
  name text,
  title text,
  email text,
  linkedin_url text,
  company text,
  fit_score numeric,
  metadata jsonb
);
```

---

## Key Implementation Patterns

### 1. Sync vs Async Execution

```python
# Sync step (blocking)
def run_sync_step(prompt_name: str, input_data: dict) -> dict:
    """Equivalent to Make.com RUN_SYNC_* subscenarios."""
    from workers.ai import prompt
    return prompt(prompt_name, variables=input_data, model="gpt-4.1", log=True)

# Async step (non-blocking with polling)
async def run_async_step(prompt_name: str, input_data: dict) -> str:
    """Equivalent to Make.com START_ASYNC_* + polling loop."""
    from workers.ai import research
    response_id = research(prompt_name, variables=input_data, model="o4-mini-deep-research")
    return response_id  # Caller polls separately
```

### 2. Polling Loop

```python
async def poll_until_complete(response_id: str, timeout: int = 600) -> dict:
    """Equivalent to Make.com BasicRepeater + Sleep + HTTP check pattern."""
    from workers.ai import poll_research
    import asyncio

    start = time.time()
    while time.time() - start < timeout:
        result = poll_research(response_id)
        if result.get("status") == "completed":
            return result
        await asyncio.sleep(30)
    raise TimeoutError(f"Polling timeout for {response_id}")
```

### 3. Parallel Execution

```python
async def run_parallel_enrichment(context: dict) -> dict:
    """Equivalent to Make.com parallel subscenario calls."""
    import asyncio

    # Start all async (get response_ids)
    lead_id = await run_async_step("enrich-lead", context)
    opp_id = await run_async_step("enrich-opportunity", context)
    client_id = await run_async_step("client-specific", context)

    # Poll all in parallel
    results = await asyncio.gather(
        poll_until_complete(lead_id),
        poll_until_complete(opp_id),
        poll_until_complete(client_id),
    )

    return {
        "lead_enrichment": results[0],
        "opportunity_enrichment": results[1],
        "client_specific": results[2],
    }
```

---

## Migration Steps (When Ready)

1. **Create prompt files** - Extract from Google Sheets Prompts tab
2. **Create test fixtures** - Convert CSVs to JSON fixtures
3. **Implement step workers** - One Python file per Make.com subscenario
4. **Create pipeline runner** - Orchestration with polling support
5. **Build admin dashboard** - Prompt editing + testing UI
6. **Create v2 tables** - Supabase migration
7. **Integration testing** - Same input → compare outputs
8. **Gradual cutover** - New leads to v2, existing stay v1

---

## Notes

- **DO NOT** break existing v1 dossiers or live app
- Execution logging goes to existing `execution_logs` table
- New structured data goes to `*_v2` tables
- Admin dashboard runs standalone on automations droplet
- All prompt files use `{{variable}}` interpolation (existing pattern)

---

## External APIs for Contact Enrichment

Step 06 (ENRICH_CONTACTS) uses external APIs to gather contact data.

### AnyMailFinder (Email Lookup)

| Property | Value |
|----------|-------|
| **Endpoint** | `https://api.anymailfinder.com/v5.1/` |
| **Auth** | `Authorization: YOUR_API_KEY` header |
| **Key Methods** | find-email/person, find-email/linkedin, find-email/decision-maker |
| **Email Status** | `valid` (verified), `risky` (unverified), `not_found`, `blacklisted` |
| **Cost** | 1 credit per valid email; risky/not_found = free |
| **Timeout** | 180 seconds (real-time SMTP verification) |

### Apify LinkedIn Scraper

| Property | Value |
|----------|-------|
| **Actor** | `dev_fusion/linkedin-profile-scraper` |
| **Actor ID** | `2SyF0bVxmgGr8IVCZ` |
| **Auth** | Apify API token |
| **No cookies required** | Works without LinkedIn authentication |
| **Returns** | Full profile: name, title, company, work history, skills, auto-discovered email |
| **Cost** | $10 per 1,000 profiles |
| **Rate Limit** | Paid users: unlimited; Free: 10 profiles/run, 10 runs/day |

### Integration Flow

```
Contact Discovery (Agent SDK)
    │
    │  Names + LinkedIn URLs
    ▼
Apify LinkedIn Scraper
    │
    │  Profile data + auto-discovered email
    ▼
AnyMailFinder (if no email found)
    │
    │  SMTP-verified email
    ▼
v2_contacts table
```

**Full documentation:** See [ENRICHMENT_APIS.md](api_migration/docs/ENRICHMENT_APIS.md)

---

## References

- Plan file: `/Users/connorjohnson/.claude/plans/synthetic-finding-perlis.md`
- Make.com exports: `columnline_app/api_migration/make_scenarios_and_csvs/`
- Existing prompt loader: `execution/dossier/lib/prompts/loader.ts`
- Existing fixture loader: `execution/dossier/tests/lib/fixture-loader.ts`
- Existing AI workers: `automations/workers/ai.py`, `automations/workers/agent.py`

---

## API Documentation Index

| Document | Path | Purpose |
|----------|------|---------|
| **ENRICHMENT_APIS.md** | `api_migration/docs/ENRICHMENT_APIS.md` | AnyMailFinder + Apify reference |
| **OPENAI_REFERENCE.md** | `api_migration/docs/OPENAI_REFERENCE.md` | OpenAI APIs (Chat, Deep Research, Agents SDK) |
| **CLAIMS_SYSTEM.md** | `api_migration/docs/CLAIMS_SYSTEM.md` | Claims extraction & merge patterns |
| **CLAIMS_STORAGE_SCHEMA.md** | `api_migration/docs/CLAIMS_STORAGE_SCHEMA.md` | Supabase v2_* tables |
| **PROMPT_WORKBENCH.md** | `api_migration/docs/PROMPT_WORKBENCH.md` | Streamlit admin dashboard spec |
