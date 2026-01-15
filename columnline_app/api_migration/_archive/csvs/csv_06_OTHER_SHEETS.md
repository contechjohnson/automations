# Other Sheets

This document covers the remaining sheets used in the Make.com pipeline.

NOTES FROM AUTHOR (MAY OR MAY NOT REFLECT WHATS BELOW):  I've kind of referenced these a little bit in the other CSV, you know, explanation markdown files. But, yeah, we'll go through each of these. Client sheet is more just conceptual. It's not how it's actually going to look. And this one has tons of flexibility, basically. It's just the idea of having, you know, a client's table, which we already have in our app, that is going to be just fine. You know, we're okay. Then beyond that, we have, we've got to probably tie their ICP configs and all that stuff and all their actual, like, reference files in there. You know, their drip schedule, you know, when are they getting the dossiers, when are they, you know, what are the default values for that, I guess, or something. Yeah, their information, contact information, all of it, tenant information, user role level, et cetera. For the dossiers, sheet mentioned this as well. Ultimately, I know we're going to be running a lot of these at the same time and I don't want them to conflict with each other and they need to be able to find the dossier run ID or the dossier ID or the client ID or all this stuff. That has not been considered in this Google Sheet environment. I would like to carefully implement that, however, and make it sort of like an elegant framework that can scale. So not only can I test, but I can also scale. That's one of the main things. The dossier is going to basically have probably all of the rendered sections, I'm guessing, in there. Not sure the best way to really call that out, but maybe it should reference the other stuff, other tables as well related to it. I don't know. I'm open to ideas there.  Onboarding is going to be a critical one. So the idea is that basically I'm going to be able to do just an API call to this onboarding thing, pass in all this information, store it, and...  Yeah, just go from there.  There's probably a few opportunities here. So referring back to the clients table, one thing that would be nice is for all of my clients, every email communication I've had with them and every meeting transcript I've had with them where they were an invitee or on the email, I could basically store those. And I actually do want to do that at some point. And that's easy enough for me to make an API call and just automatically add those to their files, I guess.  When they are onboarded.  Anyway, that's not a huge priority at the moment. But, yeah, the idea is that this will be a priority very soon. When I onboard folks, I needed to be crisp and easily able to create those initial ICP config files that we saw earlier based on what we are given and how we do that research. So that's going to be critical. We will need to...  We're going to work on this a little bit more, of course, but ultimately I think I'd like to just be able to pass in an email at some point with a name and maybe a quick narrative description. And then we're able to query our Fathoms meeting note taker, which is in all of our meetings, to go get all of the calls and then use an API call to store the transcript before trying to parse it. Maybe same deal with all emails that we've received from them as well. That would be helpful. And then we parse all that information and then we're able to generate the...  IPC config, industry research, industry research context, all that stuff.  And we'll have some kind of like onboarding system prompts that we'll probably call other agents, maybe in make.com or something. Yeah, I think I already have that kind of built out. We'll get to that. But those agents will go and craft the actual original and thorough ISCP config before it necessarily gets, well, I guess we could just string it together with the prep inputs table as well.  So there's that. We'll create all those items on there. Then we have prep inputs. I've talked on this before, but really prep inputs is a way to take our...  Main client files and consolidate them for use in LLMs. Sometimes we don't want to use that. We want to use the thorough one. So a good example, to create the bad strategy, we don't need to compress because all the bad strategy is going to refer to is just those files themselves. When we're doing something later, like creating cold email campaigns where we don't need to reference a bunch of other information, but we can just look at the client files. We want the more thorough client files to fall back on and so on. So that's the main purpose of that. In the future, well, in the next couple of steps, like most of the stuff will be using the pre-processed client files rather than the entire dump.  And it gives us another lever that we can use for context engineering and cost savings.  Moving on to Batch Composer. Batch Composer is an interesting one. Basically, it's a step before running the pipeline, but only when we have this thing running in the cloud kind of automatically every so often. What its job is to do is to take the batch strategy and hint at the very end and provide seeds to, you know, anywhere from one to ten pipeline calls that will be made in parallel. And it will send them in different directions.  So that they don't, you know, go get the same shit, basically. So there's that piece. And we want them to not, you know, not return with duplicates and so on. But the other thing it also does is it allows for distributions. So we may say, okay, we're going to do 10% senior housing, 20% multifamily.  70% data center or something and then it flows really nicely into a 10 dossier per week sort of generation schedule.  Yeah, and these are all pretty good. So there's that. And then also it'll have a brief history of, you know, which directions it sent last week and maybe the week before. And then it also gives us a point to where when we receive client feedback, not only can the client give us feedback that adjusts the ICP config automatically and the other items automatically, but we can adjust the batch strategy as well. So that when we feed the batch composer, it produces, you know, different results and so on. It also will be able to, we'll say, select from different seeds within a seed pool, but that's probably out of scope for now.  Yeah, I build out these scrapers and then basically store the seeds for future use. But again, that's out of scope, so don't need to dive too much into that. But ultimately, I need to be able to store the batch composer's prompt somewhere. I need to be able to work with the batch strategy or look at what it's receiving and what inputs and outputs it has, the prompt and all that. 

---

## Clients Sheet

**Source file:** `DOSSIER_FLOW_TEST - Clients.csv`
**Sheet name:** `Clients`

### Purpose
Stores client metadata. Currently just a placeholder with headers.

### Structure
| Column | Field |
|--------|-------|
| A | CLIENT_ID |
| B+ | ALL OTHER CLIENT INFO... |

### Migration Notes
- Move to `clients` table in Supabase
- Store ICP_CONFIG, INDUSTRY_RESEARCH, RESEARCH_CONTEXT per client

---

## Dossiers Sheet

**Source file:** `DOSSIER_FLOW_TEST - Dossiers.csv`
**Sheet name:** `Dossiers`

### Purpose
Stores completed dossier metadata. Currently just a placeholder.

### Structure
| Column | Field |
|--------|-------|
| A | DOSSIER_ID |
| B | CLIENT_ID |
| C+ | ALL OTHER DOSSIER INFO... |

### Migration Notes
- Move to `dossiers_v2` table
- Add sections as `dossier_sections_v2` rows

---

## Onboarding Sheet

**Source file:** `DOSSIER_FLOW_TEST - Onboarding.csv`
**Sheet name:** `Onboarding`

### Purpose
Captures raw client onboarding information before processing into configs.

### Structure
| Row | Info Type | Purpose |
|-----|-----------|---------|
| 2 | CLIENT INFO | Contact info, emails, website |
| 3 | TRANSCRIPTS | Recorded call transcripts |
| 4 | CLIENT MATERIAL | Do-not-call lists, past clients, scripts |
| 5 | PRE-RESEARCH | Initial research from Perplexity/Claude |
| 6 | ONBOARDING SYSTEM PROMPT | System prompt for processing |
| 7 | ICP_CONFIG | Generated ICP config |
| 8 | INDUSTRY_RESEARCH | Generated industry research |
| 9 | RESEARCH_CONTEXT | Generated research context |
| 10 | BATCH_STRATEGY | Batch processing strategy |

### Data Flow
```
Raw Inputs (rows 2-5)
    ↓
_0A_CLIENT_ONBOARDING
    ↓
Processed Configs (rows 7-10)
    ↓
_0B_PREP_INPUTS
    ↓
Inputs sheet (final configs)
```

---

## PrepInputs Sheet

**Source file:** `DOSSIER_FLOW_TEST - PrepInputs.csv`
**Sheet name:** `PrepInputs`

### Purpose
Intermediate configs from onboarding, before final refinement.

### Structure
| Cell | Field | Content |
|------|-------|---------|
| B2 | PRE_ICP_CONFIG | Raw ICP from onboarding |
| C2 | (prompt) | Refinement prompt |
| B3 | PRE_INDUSTRY_RESEARCH | Raw industry research |
| C3 | (prompt) | Refinement prompt |
| B4 | PRE_RESEARCH_CONTEXT | Raw research context |
| C4 | (prompt) | Refinement prompt |
| B5 | PRE_SEED_DATA | Raw seed data |
| C5 | (prompt) | Refinement prompt |

### Data Flow
```
Onboarding sheet
    ↓
_0A → writes to PrepInputs
    ↓
_0B → reads PrepInputs, refines, writes to Inputs
```

---

## Batch Composer Inputs Sheet

**Source file:** `DOSSIER_FLOW_TEST - Batch Composer Inputs.csv`
**Sheet name:** `Batch Composer Inputs`

### Purpose
Inputs for the batch composition step.

### Structure
| Row | Field | Content |
|-----|-------|---------|
| 2 | BATCH_STRATEGY | Strategy configuration |
| 3 | SEED_POOL_INPUT | (not in scope) |
| 4 | LAST_BATCH | Previous batch reference |
| 5 | RECENT_FEEDBACK | Recent client feedback |

### Used By
- `_0C_BATCH_COMPOSER` blueprint

---

## Summary: Sheet Migration Map

| Sheet | Current Use | Migration Target |
|-------|-------------|------------------|
| Inputs | Client configs | `clients` table |
| Prompts | Prompt templates + live testing | `prompts/*.md` + admin UI |
| MASTER | Control toggles | API parameters |
| DOSSIER SECTIONS | Section writer prompts | `prompts/section-writer-*.md` |
| Contacts | Enriched contacts | `dossier_contacts_v2` table |
| Clients | Client metadata | `clients` table |
| Dossiers | Dossier metadata | `dossiers_v2` table |
| Onboarding | Raw client input | Admin onboarding form |
| PrepInputs | Intermediate configs | Pipeline step output |
| Batch Composer Inputs | Batch planning | Job queue parameters |

---

## NOTES FROM CURSOR: Understanding Your Requirements

### What You're Describing

**1. Clients Table as Foundation**
You already have a clients table in your app, and that's fine. You just need to tie in their configs, drip schedule, contact info, tenant info, user roles, etc. The clients table is the foundation - everything else references it.

**What this means:** The clients table stores basic metadata and preferences. Configs are stored separately (with versioning), but they're linked to clients. This separation allows configs to evolve without touching client records.

**2. Dossiers Need Run Context**
When you run many dossiers simultaneously, each one needs to know: which pipeline run created it, which client it's for, and how to find all its related data (contacts, sections, claims). The current Google Sheets approach doesn't handle this well.

**What this means:** Dossiers need clear relationships - link to client, link to pipeline run, link to contacts. This makes it easy to find "all dossiers for this client" or "all data for this run" without conflicts.

**3. Onboarding as an API-Driven Process**
You want to make an API call, pass in client info (maybe just email + name + narrative), and have the system pull transcripts from Fathoms, emails from your email system, then generate the comprehensive configs. The onboarding process should be crisp and automated.

**What this means:** Onboarding is a workflow: receive inputs → fetch additional data (transcripts, emails) → run onboarding agents → generate comprehensive configs → trigger prep inputs to create compressed versions. The system should handle this workflow end-to-end.

**4. Prep Inputs as a Compression Step**
Prep inputs takes comprehensive configs and creates compressed versions. Most pipeline steps use compressed, but some (like batch strategy generation) use comprehensive. This gives you a lever for quality vs. cost.

**What this means:** Prep inputs is a processing step, not a storage table. It reads comprehensive configs, runs compression prompts, and writes compressed configs. Both versions are stored (with versioning), and steps choose which to use.

**5. Batch Composer as Strategic Seed Generation**
Batch composer runs before the main pipeline (when doing automated weekly batches). It takes the batch strategy, considers recent feedback and last week's history, and generates seeds for 1-10 parallel pipeline runs. It ensures diversity (doesn't send all runs in the same direction) and respects distributions (10% senior housing, 20% multifamily, 70% data center).

**What this means:** Batch composer is a planning step. It looks at strategy, history, and feedback, then generates seeds that will trigger multiple pipeline runs in parallel. The system needs to track batch runs and their generated seeds, and link those seeds to the pipeline runs they trigger.

**6. Client Feedback as a Continuous Improvement Loop**
When clients give feedback, it should adjust both configs and batch strategies. This creates a feedback loop where the system improves over time based on what clients actually want.

**What this means:** Feedback needs to be stored and applied. When applied, it creates new versions of configs or strategies. The system should track what feedback was applied and when, so you can see how the system evolved.

### Key Insight

These "other sheets" represent supporting systems: client management, onboarding workflow, batch planning, and feedback loops. They're not core to the dossier generation pipeline, but they're essential for running the business. The system needs to handle these workflows cleanly while keeping them separate from the core pipeline logic.

---

## NOTES FROM CLAUDE: Final Schema Design

**After extensive back-and-forth, here's how these supporting sheets fit into the final schema:**

### What You Really Needed

1. **Three-tier config flow** - You said: "I'm going to be able to do just an API call to this onboarding thing, pass in all this information, store it, and... Yeah, just go from there." Solution:
   - **Onboarding sheet** (execution layer) - Captures raw input, generates thorough configs
   - **PrepInputs sheet** (execution layer) - Compresses configs for cost savings
   - **Clients sheet** (config layer) - Stores BOTH versions (source of truth)

2. **Automated onboarding workflow** - You said: "I'd like to just be able to pass in an email at some point with a name and maybe a quick narrative description. And then we're able to query our Fathoms meeting note taker." Solution: Onboarding sheet tracks the full workflow from raw input → fetching transcripts → generating configs.

3. **Dual-version leverage** - You said: "It gives us another lever that we can use for context engineering and cost savings." Solution: ALL 3 configs (ICP, industry research, research context) get compressed versions. Most steps use compressed, high-impact steps use original.

4. **Batch planning before pipeline** - You said: "It's a step before running the pipeline... What its job is to do is to take the batch strategy and hint at the very end and provide seeds to, you know, anywhere from one to ten pipeline calls that will be made in parallel." Solution: BatchComposer sheet tracks batch planning runs that generate seeds for parallel pipeline execution.

5. **Distribution control** - You said: "We may say, okay, we're going to do 10% senior housing, 20% multifamily, 70% data center." Solution: BatchComposer.distribution field tracks target distribution, seeds_generated shows what was actually produced.

6. **Feedback loop** - You said: "When we receive client feedback, not only can the client give us feedback that adjusts the ICP config automatically and the other items automatically, but we can adjust the batch strategy as well." Solution: BatchComposer.recent_feedback field captures feedback that influences seed generation.

### Final Supporting Sheets Structure

#### 1. Onboarding Sheet (Execution Layer)

**Purpose**: Track client onboarding runs from raw input to thorough configs.

**Columns:**

| Column | Field | Type | Example | Description |
|--------|-------|------|---------|-------------|
| A | `onboarding_id` | Text | `ONB_20250112_001` | Unique onboarding run ID |
| B | `client_name` | Text | `Span Construction` | Client being onboarded |
| C | `status` | Enum | `running`, `completed`, `failed` | Current status |
| D | `client_info` | JSON | `{contact: {...}, website: "span.com"}` | Contact info, emails |
| E | `transcripts` | JSON | Array of call transcripts | Fathom recordings fetched |
| F | `client_material` | JSON | `{dnc_lists: [...], past_clients: [...]}` | Do-not-call lists, scripts |
| G | `pre_research` | Text | Initial research | Perplexity/Claude pre-research |
| H | `onboarding_system_prompt` | Text | System prompt | Onboarding agent logic |
| I | `generated_icp_config` | JSON | Thorough ICP | **Output: original ICP** |
| J | `generated_industry_research` | JSON | Thorough industry | **Output: original industry** |
| K | `generated_research_context` | JSON | Thorough context | **Output: original context** |
| L | `generated_batch_strategy` | JSON | Batch strategy | **Output: batch strategy** |
| M | `client_id` | FK | `CLT_12345` | Links to Clients row created |
| N | `started_at` | DateTime | `2025-01-12 09:00:00` | Onboarding start |
| O | `completed_at` | DateTime | `2025-01-12 09:30:00` | Onboarding complete |

**Why**: One row per onboarding run. Audit trail from raw input → fetched transcripts → generated configs. Links to Clients row created.

**Workflow:**
```
API Call: POST /onboard
    ↓
Create Onboarding row (status: "running")
    ↓
Fetch transcripts from Fathom API (write to transcripts column)
    ↓
Run onboarding agents (generate thorough configs)
    ↓
Write outputs to columns I-L
    ↓
Create Clients row with thorough configs
    ↓
Update Onboarding row (status: "completed", client_id: CLT_12345)
```

---

#### 2. PrepInputs Sheet (Execution Layer)

**Purpose**: Track config compression runs. Takes thorough → compressed for cost savings.

**Columns:**

| Column | Field | Type | Example | Description |
|--------|-------|------|---------|-------------|
| A | `prep_id` | Text | `PREP_20250112_001` | Unique prep run ID |
| B | `client_id` | FK | `CLT_12345` | Links to Clients.client_id |
| C | `status` | Enum | `running`, `completed`, `failed` | Prep status |
| D | `original_icp_config` | JSON | Full ICP | **Input: thorough from Onboarding** |
| E | `compressed_icp_config` | JSON | Compressed ICP | **Output: machine-readable** |
| F | `original_industry_research` | JSON | Full industry | **Input: thorough** |
| G | `compressed_industry_research` | JSON | Compressed industry | **Output: smaller** |
| H | `original_research_context` | JSON | Full context | **Input: thorough** |
| I | `compressed_research_context` | JSON | Compressed context | **Output: smaller** |
| J | `compression_prompt` | Text | Prompt used | LLM prompt for compression |
| K | `token_savings` | Integer | `2500` | Tokens saved (original - compressed) |
| L | `started_at` | DateTime | `2025-01-12 09:35:00` | Prep start |
| M | `completed_at` | DateTime | `2025-01-12 09:40:00` | Prep complete |

**Why**: One row per prep run. Shows compression results with metrics (token savings). Updates Clients sheet with compressed versions.

**Workflow:**
```
After Onboarding completes:
    ↓
Create PrepInputs row (status: "running")
    ↓
Copy thorough configs to columns D, F, H
    ↓
Run 3 LLM calls (compress ICP, industry, context)
    ↓
Write compressed versions to columns E, G, I
    ↓
Calculate token_savings
    ↓
Update Clients row (add compressed versions)
    ↓
Update PrepInputs row (status: "completed")
```

---

#### 3. BatchComposer Sheet (Execution Layer)

**Purpose**: Track batch planning runs. Generates 1-10 seeds for parallel pipeline execution with distribution control.

**Columns:**

| Column | Field | Type | Example | Description |
|--------|-------|------|---------|-------------|
| A | `batch_id` | Text | `BATCH_20250112_001` | Unique batch planning ID |
| B | `client_id` | FK | `CLT_12345` | Links to Clients.client_id |
| C | `status` | Enum | `running`, `completed`, `failed` | Batch planning status |
| D | `batch_strategy` | JSON | Strategy from Clients | **Input: batch rules** |
| E | `seed_pool_input` | JSON | Available seeds (future) | Pool of scraped seeds |
| F | `last_batch_hints` | JSON | Previous batch summary | **Prevents duplicates** |
| G | `recent_feedback` | JSON | Client feedback | **Adjusts seed generation** |
| H | `seeds_generated` | JSON | `[{entity: "Wyloo", hint: "mining"}, ...]` | **Output: 1-10 seeds** |
| I | `distribution` | JSON | `{"data_center": 0.7, "senior_housing": 0.1}` | Target distribution |
| J | `run_ids_created` | JSON | `["RUN_001", "RUN_002", ...]` | Links to Runs created |
| K | `started_at` | DateTime | `2025-01-12 10:00:00` | Batch planning start |
| L | `completed_at` | DateTime | `2025-01-12 10:05:00` | Batch planning complete |

**Why**: One row per batch planning run. Generates diverse seeds → triggers multiple Runs rows. Tracks distribution and prevents duplicates.

**Workflow:**
```
Scheduled job (e.g., Monday 8am):
    ↓
Create BatchComposer row (status: "running")
    ↓
Load inputs: batch_strategy, last_batch_hints, recent_feedback
    ↓
Run batch composer agent:
    - Considers distribution targets
    - Avoids entities from last batch
    - Incorporates recent feedback
    - Generates 1-10 diverse seeds
    ↓
Write seeds_generated (column H)
    ↓
Create Runs rows for each seed (parallel execution)
    ↓
Write run_ids_created (column J)
    ↓
Update BatchComposer row (status: "completed")
```

---

#### 4. Clients Sheet (Config Layer)

**Purpose**: Source of truth for client metadata and configs. Stores BOTH thorough and compressed versions.

**Columns:**

| Column | Field | Type | Example | Description |
|--------|-------|------|---------|-------------|
| A | `client_id` | Text | `CLT_12345` | Unique client ID |
| B | `client_name` | Text | `Span Construction` | Client company name |
| C | `status` | Enum | `active`, `paused`, `churned` | Current status |
| D | `icp_config` | JSON | Thorough ICP config | **Original: for batch strategy** |
| E | `icp_config_compressed` | JSON | Compressed ICP | **Compressed: for most steps** |
| F | `industry_research` | JSON | Thorough industry | **Original: for high-impact** |
| G | `industry_research_compressed` | JSON | Compressed industry | **Compressed: for most steps** |
| H | `research_context` | JSON | Thorough context | **Original: for feedback** |
| I | `research_context_compressed` | JSON | Compressed context | **Compressed: for most steps** |
| J | `batch_strategy` | JSON | `{distribution: {...}, rules: [...]}` | Batch planning strategy |
| K | `client_specific_research` | JSON | `{golf_connections: [...], alumni: [...]}` | Manual notes (ad-hoc) |
| L | `drip_schedule` | JSON | `{days: [0, 3, 7], time: "09:00"}` | Email drip config |
| M | `contact_info` | JSON | `{email: "...", phone: "..."}` | Contact details |
| N | `tenant_info` | JSON | `{org_id: "...", seat_count: 5}` | Tenant details |
| O | `user_roles` | JSON | `{admin: ["user@example.com"]}` | User permissions |
| P | `created_at` | DateTime | `2025-01-11 10:30:00` | Client created |
| Q | `updated_at` | DateTime | `2025-01-11 14:22:00` | Last config update |

**Why**: One row per client. Read-only during runs. Dual-version strategy (thorough + compressed) provides cost/quality lever.

**Key Insight**: Clients sheet is populated by Onboarding (creates row with thorough configs) and PrepInputs (adds compressed versions).

---

### How These Supporting Sheets Fit Together

**The Complete Flow:**

```
1. ONBOARDING WORKFLOW
   └── API POST /onboard {email, name, narrative}
       ↓
   Onboarding sheet (row created)
       ├── Fetch transcripts from Fathom
       ├── Fetch emails from email system
       └── Run onboarding agents
       ↓
   Generate thorough configs (ICP, industry, context, batch strategy)
       ↓
   Create Clients row (with thorough configs)
       ↓
   Trigger PrepInputs

2. CONFIG COMPRESSION WORKFLOW
   └── PrepInputs sheet (row created)
       ↓
   Read thorough configs from Clients
       ↓
   Run 3 LLM compression calls
       ↓
   Update Clients row (add compressed versions)
       ↓
   Client now has BOTH versions available

3. BATCH PLANNING WORKFLOW (Weekly/Scheduled)
   └── BatchComposer sheet (row created)
       ↓
   Load: batch_strategy, last_batch_hints, recent_feedback
       ↓
   Run batch composer agent
       ↓
   Generate 1-10 diverse seeds (respecting distribution)
       ↓
   Create Runs rows (parallel pipeline execution)
       ↓
   Each Run uses client's compressed configs by default
       ↓
   High-impact steps can use client's thorough configs

4. FEEDBACK LOOP (Continuous)
   └── Client provides feedback
       ↓
   Feedback stored in BatchComposer.recent_feedback
       ↓
   Next batch planning incorporates feedback
       ↓
   Can also update Clients configs (creates new version)
```

---

### Key Differences from Original Vision

**Original**: Separate static sheets for Onboarding, PrepInputs, BatchComposer inputs
**Final**: Execution layer sheets that track runs/workflows

**Why**:
1. **Concurrent safety** - Multiple onboardings, prep runs, batch plans don't conflict
2. **Audit trail** - See full history of how configs were generated
3. **Traceability** - Link from Clients back to Onboarding run that created them
4. **Metrics** - Track token savings, compression ratios, batch effectiveness

**Example Query**:
```sql
-- How were this client's configs generated?
SELECT o.started_at, o.transcripts, o.pre_research, p.token_savings
FROM onboarding o
JOIN prep_inputs p ON o.client_id = p.client_id
WHERE o.client_id = 'CLT_12345';

-- What seeds did last week's batch generate?
SELECT batch_id, seeds_generated, distribution, started_at
FROM batch_composer
WHERE started_at > NOW() - INTERVAL '7 days'
ORDER BY started_at DESC;
```

---

### Dual-Version Strategy: When to Use Which

| Step | Config Version Used | Why |
|------|---------------------|-----|
| **Most pipeline steps** | Compressed | Token savings, faster, sufficient context |
| **Batch composer** | Thorough | Needs full strategy, all nuances |
| **Feedback interpreter** | Thorough | Needs complete context to apply feedback |
| **Search builder** | Compressed | Just needs core ICP signals |
| **Entity research** | Compressed | Just needs industry context |
| **Contact discovery** | Compressed | Just needs target titles |
| **Section writers** | Compressed | Claims already contain details |

**Token Savings**: User gets ~40-60% reduction using compressed versions for most steps, while maintaining quality where it matters.

---

### Feedback Loop Implementation

**How feedback gets applied:**

```
1. Client gives feedback via app:
   "Focus more on senior housing opportunities"

2. Feedback stored in feedback table:
   {
     client_id: "CLT_12345",
     feedback_text: "Focus more on senior housing...",
     applied: false
   }

3. Next batch planning run:
   BatchComposer reads recent_feedback
   ↓
   Adjusts distribution: senior_housing: 0.2 → 0.3
   ↓
   Generates seeds with more senior housing focus

4. Optional: Update batch_strategy in Clients:
   {
     distribution: {
       "data_center": 0.6,  // was 0.7
       "senior_housing": 0.3  // was 0.2
     }
   }
   ↓
   Mark feedback as applied
```

**This creates continuous improvement**: System learns from what clients actually want and adjusts future outputs accordingly.

---

**STATUS:** Schema finalized with 4 supporting sheets (Onboarding, PrepInputs, BatchComposer, Clients) plus 10 execution sheets (Runs, PipelineSteps, Claims, MergedClaims, ContextPacks, Contacts, Sections, Dossiers, SectionDefinitions, Prompts). Complete 14-sheet architecture ready for CSV generation and API middleware implementation.
