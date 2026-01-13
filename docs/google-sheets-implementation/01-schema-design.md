# Google Sheets Schema Design Summary
**For Columnline Dossier Pipeline**
**Date:** 2026-01-12
**Status:** Ready for Review

---

## 🎯 Core Problem Solved

**Your Current Issue:** "Live input/output" columns overwrite each other when running 80+ dossiers concurrently on Monday.

**Solution:** Separate **config** (read-only) from **execution** (per-run rows). Each run gets its own rows, no conflicts.

## 🎨 Design Philosophy

**Key Principle:** "Keep it simple, flexible, non-fragile. JSON stays JSON."

1. **Claims as JSON blobs** - One row per claims-producing step, entire claims array in one cell. Don't parse into individual rows.
2. **No over-structuring** - Avoid rigid columns that force specific structure (like contacts_resolved, timelines_resolved). Keep merge results flexible.
3. **Outputs not in run metadata** - Things like lead_score, target_entity, timing_urgency belong in Dossiers sheet (outputs), not Runs sheet (metadata).
4. **Variables tracking for context engineering** - Track both variables_used and variables_produced in Prompts sheet to organize passing context in Make.com.
5. **07B_INSIGHT is just a regular step** - It's a research step that produces insight about market positioning. It extracts claims like other steps. Completely decoupled from merge claims operation.
6. **Merge claims is a utility operation** - Separate from specific steps. Takes all claims JSONs, removes redundancy/refuted conflicts, outputs consolidated JSON. Can run multiple times per run.
7. **Contacts need both renderable + processing columns** - Renderable fields for app display, processing fields for generating copy later. Both are needed.
8. **All 3 configs get compressed** - ICP config, industry research, AND research context all have compressed versions for cost savings.

---

## 📊 Schema Overview: 14 Sheets

### Config Layer (3 sheets) - Read-only during runs
1. **Clients** - Client metadata, ICP configs, industry research
2. **Prompts** - Prompt template library
3. **SectionDefinitions** - Expected variables per section (for validation)

### Execution Layer (11 sheets) - Per-run mutable state
4. **Onboarding** - Client onboarding runs (transcripts → configs)
5. **PrepInputs** - Config compression runs (original → compressed)
6. **BatchComposer** - Batch planning runs (strategy → seeds)
7. **Runs** - Dossier execution tracking (main run record)
8. **PipelineSteps** - Step execution logs (input/output per step)
9. **Claims** - Extracted facts per run (one row per claims-producing step)
10. **MergedClaims** - Merged/interpreted claims (07B_INSIGHT)
11. **ContextPacks** - Context briefings for downstream steps
12. **Contacts** - Enriched contacts per run (3-10 per dossier)
13. **Sections** - Dossier sections per run (7-8 sections)
14. **Dossiers** - Final assembled dossiers

---

## 🔑 Key Design Decisions

### 1. Config vs Execution Separation

**Config sheets (Clients, Prompts, SectionDefinitions):**
- One row per item
- Read-only during runs
- Shared by all runs

**Execution sheets (everything else):**
- Multiple rows per run
- One run doesn't affect another
- Filter by `run_id` to see one run's complete execution

### 2. Dual-Version Strategy (Your Request)

**Clients sheet has both:**
- `icp_config` (original, thorough) → for batch composer, feedback
- `icp_config_compressed` (smaller) → for most steps (cost savings)

**Why:** Cost/quality lever without data loss. Use original when it matters.

### 3. No MASTER Sheet

**Your note:** "I don't want to overthink this one... more conceptual"

**Solution:** Remove MASTER sheet entirely. Replace with:
- API request parameters: `{client_id, count, seed_data, schedule}`
- Make.com scenario parameters
- No global mutable state to manage

### 4. Testing Built-In

**Your question:** "How do you want to test prompts?"

**Solution:** Use `mode='test'` in Runs sheet
- Test runs use same schema
- Filter by `mode='test'` to see tests vs production
- Same PipelineSteps, Claims, etc.
- Compare prompt versions by comparing run_ids

### 5. Variable Tracking (Your Request)

**Your note:** "Missing: variables that will be rendered. Need to validate output has all required fields."

**Solution:** SectionDefinitions sheet + Sections.variables_produced
- SectionDefinitions lists: `section_name`, `expected_variables`, `variable_types`
- Sections.variables_produced shows what was actually produced
- Easy validation: does output match expected?

### 6. Make.com Scenario Architecture (2026-01-12)

**Key Decision:** Isolated, self-contained scenarios

**Philosophy:** Pass IDs, fetch everything else

**What Gets Passed:**
- Main Pipeline → Bridge/Sub Scenarios: `run_id`, `client_id`, `seed`, `dossier_id`
- Bridge → Sub Scenarios: Same + specific object (e.g., `contact_object`)
- **That's it!** Everything else fetched within scenario

**What Gets Fetched Within Each Scenario:**
- Client config (Clients sheet, filter by client_id)
- Prompts (Prompts sheet, filter by slug)
- Previous outputs (Claims/ContextPacks sheets, filter by run_id)

**Benefits:**
- ✅ Each scenario runnable in isolation (easy testing)
- ✅ Visual debugging (PipelineSteps.input + output columns show everything)
- ✅ Future-proof (switching to Supabase = change modules, not structure)
- ✅ Denormalized for visibility (claims in both Claims sheet AND PipelineSteps.input)

**API Call Count:**
- Per simple scenario: 3-5 calls (2-3 reads, 1-2 writes)
- Per full dossier: ~135 calls (spread over 5-10 minutes)
- Rate limit: 100 calls/100 seconds = 1 call/second
- Our avg: ~0.2-0.4 calls/second ✅ Well within limits

**Flow Example:**
```
Main Pipeline (generates run_id, dossier_id)
  ↓ Passes: {run_id, client_id, seed, dossier_id}
  ↓
Bridge Scenario (e.g., Enrich Contacts)
  ↓ Fetches: client config, prompts, claims
  ↓ Passes: {run_id, client_id, dossier_id, contact_object}
  ↓
Sub Scenario (e.g., Individual Contact Enrichment)
  ↓ Fetches: client config, prompt, claims, context pack
  ↓ Does work
  ↓ Writes: Contacts sheet, PipelineSteps sheet
```

**Denormalization Strategy:**
- PipelineSteps.input = Full JSON of what went into step
- PipelineSteps.output = Full JSON of what came out
- Accept duplication (claims appear in Claims sheet AND input/output columns)
- Gain: "Look at one row to see entire step execution"

**Migration to Supabase:**
```
// Current (Google Sheets)
Google Sheets > Get Values (Clients!A2:M100, filter: client_id)

// Future (Supabase)
HTTP > GET api.columnline.dev/clients/{client_id}
```
Same structure, different module type. Architecture is future-proof.

---

## 📋 Detailed Sheet Schemas

### 1. Clients Sheet (Config)

**Your Intent:** "Store both original (thorough) and compressed versions of ALL 3 client configs. Flow: Onboarding generates original → PrepInputs compresses → Clients stores both."

| Column | Field | Example | Notes |
|--------|-------|---------|-------|
| A | client_id | `CLT_12345` | Unique ID |
| B | client_name | `Span Construction` | Company name |
| C | status | `active` | Current status |
| D | icp_config | `{signals: [...]}` | **Original ICP (thorough)** |
| E | icp_config_compressed | Compressed version | **ICP for most steps** |
| F | industry_research | `{buying_signals: [...]}` | **Original industry research** |
| G | industry_research_compressed | Compressed version | **Industry for most steps** |
| H | research_context | `{client: {...}}` | **Original research context** |
| I | research_context_compressed | Compressed version | **Context for most steps** |
| J | client_specific_research | `{golf: [...]}` | **Manual notes (alumni, etc.)** |
| K | drip_schedule | `{days: [0, 3, 7]}` | Email drip config |
| L-M | created_at, updated_at | Timestamps | Audit trail |

**Config Flow:**
1. **Onboarding sheet** generates original versions (D, F, H)
2. **PrepInputs sheet** compresses them (outputs E, G, I)
3. **Clients sheet** stores both (source of truth)
4. Runs read from Clients sheet, use compressed by default, original for high-impact steps

**Why This Works:** One row per client. **All 3 configs have compressed versions.** Clear flow keeps them synced.

---

### 2. Prompts Sheet (Config)

**Your Intent:** "Prompt template library, NOT execution logs. Prompts describe what they receive (no {{vars}}). Track variables_used and variables_produced for context engineering."

| Column | Field | Example | Notes |
|--------|-------|---------|-------|
| A | prompt_id | `PRM_001` | Unique ID |
| B | prompt_slug | `search-builder` | URL-safe identifier |
| C | stage | `FIND_LEAD` | Pipeline stage |
| D | step | `1_SEARCH_BUILDER` | Step name |
| E | prompt_template | "You will receive..." | **Describes context, no {{vars}}** |
| F | model | `gpt-4.1` | Default model |
| G | produce_claims | `TRUE`/`FALSE` | Extracts claims? |
| H | context_pack_produced | `TRUE`/`FALSE` | Produces context pack? |
| I | variables_used | `["icp_config", "seed", "prev_output"]` | **Inputs to this prompt** |
| J | variables_produced | `["search_queries", "exclude_domains"]` | **Outputs from this prompt** |
| K | version | `v2.3` | Version tracking |
| L | created_at | Timestamp | Audit trail |

**Why This Works:** Templates pulled by ID during runs. Version tracking. **variables_used + variables_produced enables context tracking and helps organize variable passing in Make.com.**

---

### 3. SectionDefinitions Sheet (Config)

**Your Intent:** "Need to validate output has all required fields."

| Column | Field | Example | Notes |
|--------|-------|---------|-------|
| A | section_name | `INTRO` | Section type |
| B | expected_variables | `["title", "one_liner", "lead_score", ...]` | **What must be produced** |
| C | variable_types | `{"lead_score": "integer"}` | Type constraints |
| D | validation_rules | `{"lead_score": {"min": 0, "max": 100}}` | Value constraints |
| E | description | "Intro section..." | Human-readable |
| F | example_output | Example JSON | Sample for reference |

**Why This Works:** Reference data. Validate Sections.variables_produced against this.

---

### 4. Onboarding Sheet (Execution)

**Your Intent:** "I need to be able to pass in an email... query Fathoms... parse and generate ICP config."

| Column | Field | Example | Notes |
|--------|-------|---------|-------|
| A | onboarding_id | `ONB_20250112_001` | Unique ID |
| B | client_name | `Span Construction` | Client being onboarded |
| C | status | `running`/`completed` | Onboarding status |
| D | client_info | `{contact: {...}, website: "..."}` | Raw input |
| E | transcripts | Array of transcripts | **From Fathom API** |
| F | client_material | `{dnc_lists: [...]}` | Do-not-call, scripts |
| G | pre_research | "Initial research..." | Pre-research notes |
| H | onboarding_system_prompt | Prompt text | Onboarding logic |
| I | generated_icp_config | **Thorough ICP** | Output: original |
| J | generated_industry_research | **Thorough industry** | Output: original |
| K | generated_research_context | **Thorough context** | Output: original |
| L | generated_batch_strategy | Batch strategy | Output |
| M | client_id | `CLT_12345` | **Links to created Clients row** |
| N-O | started_at, completed_at | Timestamps | Audit trail |

**Why This Works:** One row per onboarding. Audit trail from raw → configs. Links to Clients row.

---

### 5. PrepInputs Sheet (Execution)

**Your Intent:** "Takes original configs and compresses ALL 3 (ICP, industry, context). Gives us a lever for cost/quality. Flow: Onboarding → PrepInputs → Clients."

| Column | Field | Example | Notes |
|--------|-------|---------|-------|
| A | prep_id | `PREP_20250112_001` | Unique ID |
| B | client_id | `CLT_12345` | Links to Clients |
| C | status | `running`/`completed` | Prep status |
| D | original_icp_config | Full ICP | **Input: from Onboarding.I** |
| E | compressed_icp_config | Compressed ICP | **Output → Clients.E** |
| F | original_industry_research | Full industry | **Input: from Onboarding.J** |
| G | compressed_industry_research | Compressed industry | **Output → Clients.G** |
| H | original_research_context | Full context | **Input: from Onboarding.K** |
| I | compressed_research_context | Compressed context | **Output → Clients.I** |
| J | compression_prompt | Prompt text | LLM prompt used |
| K | token_savings | `2500` | **Tokens saved (total)** |
| L-M | started_at, completed_at | Timestamps | Audit trail |

**Flow:** Onboarding generates originals → PrepInputs compresses → Clients stores both

**Why This Works:** One row per prep run. **All 3 configs compressed.** Shows compression results. Updates Clients sheet.

---

### 6. BatchComposer Sheet (Execution)

**Your Intent:** "Pre-pipeline batch planning. Takes batch_strategy (contains distribution), hints (prevents duplicates), generates 1-10 seeds for parallel runs."

| Column | Field | Example | Notes |
|--------|-------|---------|-------|
| A | batch_id | `BATCH_20250112_001` | Unique ID |
| B | client_id | `CLT_12345` | Links to Clients |
| C | status | `running`/`completed` | Planning status |
| D | batch_strategy | Strategy config (JSON) | **Input: contains distribution** |
| E | seed_pool_input | Array of seeds | **Future: scraped seeds** |
| F | last_batch_hints | Previous dossiers | **Prevents duplicates** |
| G | recent_feedback | Client feedback | Adjustments |
| H | run_ids_created | `["RUN_001", "RUN_002", ...]` | **Links to Runs created** |
| I-J | started_at, completed_at | Timestamps | Audit trail |

**Why This Works:** One row per batch plan. batch_strategy JSON contains distribution (don't duplicate). Links to created Runs.

---

### 7. Runs Sheet (Execution)

**Your Intent:** "Track each dossier run. Status tracking to see '3 running, 12 completed' at a glance. Keep run metadata separate from outputs."

| Column | Field | Example | Notes |
|--------|-------|---------|-------|
| A | run_id | `RUN_20250112_001` | **Unique run ID** |
| B | client_id | `CLT_12345` | Links to Clients |
| C | status | `running`/`completed`/`failed` | **Current status** |
| D | seed_data | `{entity: "Wyloo Metals", hint: "..."}` | Seed if provided (JSON) |
| E | dossier_id | `DOSS_123` | Links to Dossiers (when complete) |
| F-G | started_at, completed_at | Timestamps | Runtime tracking |
| H | error_message | Error text | If failed |
| I | triggered_by | `api`/`scheduled`/`manual` | How run started |
| J | config_snapshot | Config JSON | **Config used for this run** |

**Why This Works:** One row per run. No conflicts. Outputs (lead_score, target_entity, urgency) live in Dossiers sheet, not here.

---

### 8. PipelineSteps Sheet (Execution)

**Your Intent:** "Replaces 'live input/output'. Need per-run execution logs. Full input/output for debugging."

| Column | Field | Example | Notes |
|--------|-------|---------|-------|
| A | step_id | `STEP_RUN001_03` | Unique step execution ID |
| B | run_id | `RUN_20250112_001` | **Links to Runs** |
| C | prompt_id | `PRM_003` | Links to Prompts |
| D | step_name | `3_ENTITY_RESEARCH` | Step identifier |
| E | status | `running`/`completed`/`failed` | Step status |
| F | input | **Full input JSON** | **What went into prompt** |
| G | output | **Full output JSON** | **What came back** |
| H | model_used | `gpt-4.1` | Model actually used |
| I | tokens_used | `1250` | Token count |
| J | runtime_seconds | `12.5` | Execution time |
| K-L | started_at, completed_at | Timestamps | Step timing |
| M | error_message | Error text | If failed |

**Why This Works:** Multiple rows per run. Filter by run_id to see one run's progress. **Solves the "live" problem.**

---

### 9. Claims Sheet (Execution)

**Your Intent:** "One row for every time we produce claims. Extract narrative → produce claims → store as JSON. Don't parse out into individual rows - keep it simple, flexible, non-fragile."

| Column | Field | Example | Notes |
|--------|-------|---------|-------|
| A | run_id | `RUN_20250112_001` | **Links to Runs** |
| B | step_id | `STEP_RUN001_03` | Which step produced this |
| C | step_name | `entity_research` | Step identifier |
| D | claims_json | `[{claim1}, {claim2}, ...]` | **Full claims array as JSON** |
| E | created_at | Timestamp | When extracted |

**Why This Works:** One row per claims-producing step. Entire claims array in one cell. Can parse later if needed. No rigidity.

---

### 10. MergedClaims Sheet (Execution)

**Your Intent:** "Merge claims step - completely decoupled from 07B_INSIGHT (that's just a regular research step). Takes all claims JSONs, merges them, removes redundancy/refuted conflicts. At least one merge per run, possibly more. Output: same format as claims extraction (JSON array)."

| Column | Field | Example | Notes |
|--------|-------|---------|-------|
| A | merge_id | `MERGE_RUN001_01` | Unique merge ID (can have multiple per run) |
| B | run_id | `RUN_20250112_001` | **Links to Runs** |
| C | step_id | `STEP_RUN001_10` | Which step performed merge |
| D | merged_claims_json | **Full merged claims JSON array** | **Same format as Claims.claims_json** |
| E | created_at | Timestamp | When merge happened |

**What Merge Does:**
- Takes all Claims.claims_json for this run
- Removes clearly redundant information (e.g., 3 steps all found same VP)
- Removes refuted conflicts (if conflicting claims, keep stronger one)
- Keeps everything else (don't lose info)
- Output: consolidated claims JSON array

**NOT for:**
- Creating context packs (those are targeted summaries)
- Being used by dossier writers directly (writers use original claims)

**Why This Works:** Multiple rows per run (if merging multiple times). **Same JSON format as claims extraction.** Flexible, non-fragile.

---

### 11. ContextPacks Sheet (Execution)

**Your Intent:** "Consolidate claims for downstream efficiency. Not deduplicating, but summarizing. Takes all claims up to that point."

| Column | Field | Example | Notes |
|--------|-------|---------|-------|
| A | pack_id | `PACK_RUN001_ENTITY` | Unique pack ID |
| B | run_id | `RUN_20250112_001` | **Links to Runs** |
| C | context_type | `signal_to_entity` | Pack type |
| D | pack_content | **Full context pack JSON** | Pack data |
| E | produced_by_step | `STEP_RUN001_03` | Which step created this |
| F | consumed_by_steps | `["STEP_RUN001_04"]` | **Which steps used it** |
| G | created_at | Timestamp | When created |

**Why This Works:** Multiple rows per run (3 typically). Lineage tracking. Efficiency layer.

---

### 12. Contacts Sheet (Execution)

**Your Intent:** "Two sources: Key Contacts + claims extraction. Agent with tools enriches. Chained: enrichment → copy → client-specific copy. Need BOTH: (1) processing columns for generating copy, (2) renderable columns for app display."

**RENDERABLE COLUMNS (for app display):**

| Column | Field | Example | Notes |
|--------|-------|---------|-------|
| A | id | `uuid-here` | Unique contact ID (UUID) |
| B | dossier_id | `DOSS_123` | **Links to Dossiers** |
| C | run_id | `RUN_20250112_001` | Links to Runs |
| D | name | `John Smith` | **[RENDER]** Full name (displayed) |
| E | first_name | `John` | **[RENDER]** For personalization |
| F | last_name | `Smith` | **[RENDER]** For personalization |
| G | title | `VP Operations` | **[RENDER]** Job title |
| H | email | `jsmith@acme.com` | **[RENDER]** Verified email |
| I | phone | `(555) 234-5678` | **[RENDER]** Phone (clickable tel:) |
| J | linkedin_url | `https://linkedin.com/in/johnsmith` | **[RENDER]** LinkedIn profile |
| K | linkedin_connections | `500+` | **[RENDER]** Connection count |
| L | bio_paragraph | "John has led operations..." | **[RENDER]** Full bio paragraph |
| M | tenure_months | `60` | **[RENDER]** Time in role (months) |
| N | previous_companies | `["Turner", "McCarthy"]` | **[RENDER]** Career history (JSON) |
| O | education | `BS Civil Eng, Texas A&M` | **[RENDER]** Education background |
| P | skills | `["Project Mgmt", "Construction"]` | **[RENDER]** Skills (JSON) |
| Q | recent_post_quote | "Excited about..." | **[RENDER]** Recent LinkedIn activity |
| R | is_primary | `true`/`false` | **[RENDER]** Primary contact flag |
| S | source | `apollo`/`linkedin`/`manual` | **[RENDER]** Data source |

**PROCESSING COLUMNS (for generating copy later):**

| Column | Field | Example | Notes |
|--------|-------|---------|-------|
| T | tier | `primary`/`secondary` | **[PROCESS]** Contact priority |
| U | bio_summary | "20+ years in mining..." | **[PROCESS]** Background summary |
| V | why_they_matter | "Owns project execution" | **[PROCESS]** Relevance explanation |
| W | signal_relevance | "Led similar projects" | **[PROCESS]** How they relate to signal |
| X | interesting_facts | `["Alumni...", "Golf..."]` | **[PROCESS]** Notable details (JSON) |
| Y | linkedin_summary | Agent's LinkedIn findings | **[PROCESS]** LinkedIn research output |
| Z | web_summary | Agent's web findings | **[PROCESS]** Web research output |
| AA | email_copy | "Hi John, I noticed..." | **[PROCESS]** Generic email body |
| AB | linkedin_copy | "Hi John - saw your post..." | **[PROCESS]** Generic LinkedIn message |
| AC | client_email_copy | Client-customized email | **[PROCESS]** Personalized email |
| AD | client_linkedin_copy | Client-customized LinkedIn | **[PROCESS]** Personalized LinkedIn |
| AE | confidence | `HIGH`/`MEDIUM`/`LOW` | **[PROCESS]** Data confidence |
| AF | created_at | Timestamp | When enriched |

**Why This Works:**
- Multiple rows per run (3-10)
- **RENDERABLE columns (A-S)** match app's exact field names (snake_case) - ready for display
- **PROCESSING columns (T-AF)** provide context for generating copy and making decisions
- Both sets needed: app can render immediately, copy generation can iterate on processing columns

**Note:** JSON fields can be parsed later if needed for detailed processing, but renderable columns are ready as-is.

---

### 13. Sections Sheet (Execution)

**Your Intent:** "6 section writers parse 200+ claims → JSON sections. Need variable tracking to validate output has all required fields. Sections populate the 5 JSONB columns."

| Column | Field | Example | Notes |
|--------|-------|---------|-------|
| A | section_id | `SECT_RUN001_INTRO` | Unique section ID |
| B | run_id | `RUN_20250112_001` | **Links to Runs** |
| C | section_name | `INTRO`/`SIGNALS`/`CONTACTS`/etc. | Section type |
| D | section_data | **Full section JSON** | Section content |
| E | claim_ids_used | `["entity_001", "signal_003"]` | Claims routed here |
| F | produced_by_step | `STEP_RUN001_15` | Writer step ID |
| G | status | `complete`/`partial`/`failed` | Section status |
| H | variables_produced | `["title", "one_liner", "lead_score"]` | **KEY: Fields produced** |
| I | target_column | `find_lead`/`enrich_lead`/`copy`/etc. | **Which JSONB column this populates** |
| J | created_at | Timestamp | When written |

**Section Types & Their Variables:**

**INTRO** (→ find_lead):
- Variables: `company_name`, `timing_urgency`, `one_liner`, `primary_signal`, `the_angle`, `lead_score`, `score_explanation`, `company_snapshot`, `primary_buying_signal`

**SIGNALS** (→ find_lead, enrich_lead):
- Variables: `primary_buying_signal`, `additional_signals` (array)

**CONTACTS** (→ contacts table):
- Variables: Separate rows per contact with `name`, `title`, `email`, `phone`, `linkedin_url`, `bio_paragraph`, `is_primary`, etc.

**COMPANY_INTEL** (→ enrich_lead):
- Variables: `company_deep_dive` (revenue, employees, founded_year, full_address, coordinates, phones, emails), `project_sites` (array)

**THE_MATH** (→ insight):
- Variables: `the_math` (their_reality, the_opportunity, translation, bottom_line)

**OUTREACH** (→ copy):
- Variables: `outreach` (array), `objections` (array), `conversation_starters` (array)

**NETWORK** (→ enrich_lead):
- Variables: `network_intelligence` (warm_paths array, upcoming_opportunities array)

**COMPETITIVE** (→ insight):
- Variables: `competitive_positioning` (insights_they_dont_know array, landmines_to_avoid array)

**DEAL_STRATEGY** (→ insight):
- Variables: `deal_strategy` (how_they_buy, unique_value_props array), `decision_making_process` (company_type, key_roles array, typical_process, entry_points array)

**MEDIA** (→ media):
- Variables: `logo_url`, `logo_fallback_chain`, `project_images` (array)

**Why This Works:** Multiple rows per run (7-10 sections). **Variables tracking + target_column ensures each section populates the right JSONB column with correct field names.**

---

### 14. Dossiers Sheet (Execution)

**Your Intent:** "Final assembled dossier. Links back to run, client, sections. Must match app's exact 5 JSONB structure. Rendered in app, not Google Docs."

| Column | Field | Example | Notes |
|--------|-------|---------|-------|
| A | dossier_id | `DOSS_123` | Unique dossier ID |
| B | run_id | `RUN_20250112_001` | **Links to Runs** |
| C | client_id | `CLT_12345` | Links to Clients |
| D | company_name | `Acme Construction` | Company name (denormalized) |
| E | lead_score | `82` | Final score (from find_lead) |
| F | timing_urgency | `HIGH`/`MEDIUM`/`LOW` | Urgency (from find_lead) |
| G | primary_signal | `Filed $4M permit` | Primary signal (from find_lead) |
| H | **find_lead** | **JSONB** | **Discovery, scoring, the angle** |
| I | **enrich_lead** | **JSONB** | **Company research, project sites** |
| J | **copy** | **JSONB** | **Outreach scripts, objections** |
| K | **insight** | **JSONB** | **The Math, competitive positioning** |
| L | **media** | **JSONB** | **Logo URL, project images** |
| M | status | `skeleton`/`ready`/`archived` | Dossier status |
| N-O | created_at, delivered_at | Timestamps | Assembly + delivery |

**The 5 JSONB Columns Contain:**

**H. find_lead:**
```json
{
  "company_name": "Acme Construction",
  "timing_urgency": "HIGH",
  "one_liner": "Regional contractor expanding into data centers",
  "primary_signal": "Filed $4M warehouse permit",
  "the_angle": "Their Dallas expansion aligns with our Q1 capacity",
  "lead_score": 82,
  "score_explanation": "Strong signal + verified contacts + geographic fit",
  "company_snapshot": {
    "description": "Acme is a regional...",
    "domain": "acmeconstruction.com",
    "hq_city": "Dallas",
    "hq_state": "TX"
  },
  "primary_buying_signal": {
    "signal": "Filed $4M warehouse permit",
    "description": "Permit filed December 2025...",
    "source_name": "Dallas Building Permits",
    "source_url": "https://..."
  }
}
```

**I. enrich_lead:**
```json
{
  "company_deep_dive": {
    "revenue": "$10M-$50M",
    "employees": "50-100",
    "founded_year": "2015",
    "full_address": "123 Main St, Dallas, TX 75201",
    "coordinates": {"lat": 32.7767, "lng": -96.7970},
    "mainline_phones": [{"number": "(555) 123-4567", "label": "Main"}],
    "general_emails": ["info@acme.com"]
  },
  "project_sites": [
    {
      "name": "Dallas Distribution Center",
      "city": "Dallas",
      "state": "TX",
      "status": "under construction",
      "coordinates": {"lat": 32.78, "lng": -96.80},
      "details": "50K SF warehouse",
      "source_url": "https://..."
    }
  ],
  "additional_signals": [...],
  "network_intelligence": {
    "warm_paths": [
      {
        "name": "Jane Smith",
        "title": "Former PM",
        "linkedin_url": "https://...",
        "approach": "Reference Dallas project",
        "connection_to_targets": "Worked with CEO 2020-2023",
        "why_they_respond": "Maintains relationship"
      }
    ],
    "upcoming_opportunities": ["Conference March 2026"]
  }
}
```

**J. copy:**
```json
{
  "outreach": [
    {
      "contact_id": "uuid",
      "target_name": "John Smith",
      "target_title": "VP Operations",
      "email_subject": "Quick question about Dallas project",
      "email_body": "Hi John,\n\nI noticed...",
      "linkedin_message": "Hi John - saw your post..."
    }
  ],
  "objections": [
    {
      "objection": "We already have a vendor",
      "response": "I understand - many clients..."
    }
  ],
  "conversation_starters": [
    "How's Dallas tracking against Q2 timeline?"
  ]
}
```

**K. insight:**
```json
{
  "the_math": {
    "their_reality": "Expanding into new market with tight timeline",
    "the_opportunity": "Our solution cuts time by 40%",
    "translation": "Potentially $200K in avoided delays",
    "bottom_line": "Every week costs $50K in carrying costs"
  },
  "competitive_positioning": {
    "insights_they_dont_know": [
      {
        "insight": "Competitor lost key PM",
        "advantage": "Capture market share now"
      }
    ],
    "landmines_to_avoid": [
      {
        "topic": "Previous vendor XYZ",
        "reason": "Ended badly in 2024"
      }
    ]
  },
  "deal_strategy": {
    "how_they_buy": "CEO makes call, VP Ops drives eval",
    "unique_value_props": ["Only Dallas-area team", "Fastest turnaround"]
  },
  "decision_making_process": {
    "company_type": "Mid-size regional contractor",
    "key_roles": [
      {
        "role": "CEO",
        "influence": "decision_maker",
        "what_they_care_about": "ROI and risk"
      }
    ],
    "typical_process": "2-3 month cycle",
    "entry_points": [
      {
        "approach": "Warm intro via industry association",
        "rationale": "CEO active in AGC"
      }
    ]
  },
  "sources": [
    {"url": "https://...", "title": "Acme About", "agent": "find-lead"}
  ]
}
```

**L. media:**
```json
{
  "logo_url": "https://logo.clearbit.com/acmeconstruction.com",
  "logo_fallback_chain": ["https://logo.clearbit.com/...", "https://acme.com/logo.png"],
  "project_images": [
    {
      "url": "https://...",
      "caption": "Dallas Distribution Center Rendering",
      "source": "Company Website",
      "source_url": "https://acme.com/projects",
      "project_name": "Dallas Distribution Center"
    }
  ]
}
```

**Why This Works:** One row per successful run. **5 JSONB columns match app's exact structure (snake_case field names).** App can render directly.

---

## 🚀 Concurrent Safety: How It Works

### The Problem You Described

**Your quote:** "If I'm generating 80 of these things on Monday... that's going to be a problem [with live input/output]."

### The Solution

**Time: 10:00 AM** - Run 1 starts (CLT_12345)
- Writes: `Runs` row with `run_id = RUN_20250112_001`, status: "running"

**Time: 10:05 AM** - Run 2 starts (CLT_12345, different seed)
- Writes: `Runs` row with `run_id = RUN_20250112_002`, status: "running"

**Time: 10:10 AM** - Run 3 starts (CLT_99999, different client)
- Writes: `Runs` row with `run_id = RUN_20250112_003`, status: "running"

**All runs proceed independently:**
- Run 1 writes to `PipelineSteps` with `run_id = RUN_20250112_001`
- Run 2 writes to `PipelineSteps` with `run_id = RUN_20250112_002`
- Run 3 writes to `PipelineSteps` with `run_id = RUN_20250112_003`

**No conflicts** - Different `run_id` values, different rows.

---

## 📊 Data Flow: How Sheets Connect

```
API Request (start dossier)
    ↓
Make.com reads CONFIG LAYER:
    ├── Clients sheet (get configs)
    └── Prompts sheet (get templates)
    ↓
Create row in Runs sheet
    ├── status: "running"
    ├── config_snapshot: {copy of configs}
    └── run_id: "RUN_20250112_001"
    ↓
For each pipeline step:
    ├── Read prompt from Prompts sheet
    ├── Execute LLM call
    ├── Write to PipelineSteps sheet (input, output, runtime)
    ├── IF produce_claims → Write ONE row to Claims sheet (full claims_json)
    └── IF context_pack → Write row to ContextPacks sheet
    ↓
Merge Claims Operation (at least once per run, possibly more):
    ├── Read all Claims.claims_json for this run_id
    ├── Execute merge prompt (removes redundancy, resolves conflicts)
    ├── Write row to MergedClaims sheet (merged_claims_json)
    └── Available for downstream steps that need consolidated claims
    ↓
For each discovered contact:
    └── Write row to Contacts sheet
    ↓
For each section (parallel):
    ├── Read Claims + MergedClaims
    ├── Execute section writer
    └── Write row to Sections sheet
    ↓
Assembly:
    ├── Read all Sections for this run_id
    ├── Assemble complete dossier
    ├── Write row to Dossiers sheet
    └── Update Runs sheet (status: "completed")
```

---

## 👀 Human-Readable Patterns

**Your requirement:** "As long as it's so stupid simple that I could figure it out."

### Quick Scan: Runs Sheet
1. Open Runs sheet
2. Sort by `started_at` DESC
3. See most recent runs at top
4. Status column shows "running" / "completed" / "failed"
5. Target_entity shows what company

### Debug One Run: PipelineSteps Sheet
1. Open PipelineSteps sheet
2. Filter by `run_id = RUN_20250112_001`
3. See all steps for that run
4. Check `input` and `output` columns
5. Runtime_seconds shows which steps are slow

### Review Claims: Claims Sheet
1. Open Claims sheet
2. Filter by `run_id = RUN_20250112_001`
3. See one row per claims-producing step (entity_research, signal_discovery, etc.)
4. Check `claims_json` column - full JSON array
5. Parse JSON if need to see individual claims

### Validate Sections: Sections Sheet
1. Open Sections sheet
2. Filter by `run_id = RUN_20250112_001`
3. Check `status` - all "complete"?
4. Check `variables_produced` - match SectionDefinitions?
5. Check `section_data` - JSON looks good?

---

## ✅ Summary: Why This Works

### 1. Concurrent Safety
- Each run gets its own rows
- No overwrites, no conflicts
- Scales to 100+ concurrent runs

### 2. Human Readable
- Open Runs sheet → see all active/recent runs
- Filter by run_id → see one run's complete execution
- Status columns → instant visual feedback

### 3. Same Schema for Testing and Production
- No special "test mode" sheets
- Use `mode='test'` in Runs sheet
- Compare prompt versions by comparing run_ids
- Debug by filtering PipelineSteps and Claims

### 4. Clear Relationships
- Foreign keys (run_id, client_id, prompt_id) are explicit
- Easy to trace: Client → Run → Steps → Claims → Sections → Dossier

### 5. JSON Preservation
- Complex structures stay intact
- No forced flattening
- Schema changes don't break sheets

### 6. Config vs Execution Separation
- Configs (Clients, Prompts, SectionDefinitions) read-only during runs
- Execution state (everything else) per-run
- Testing doesn't pollute production configs

### 7. Your Cost/Quality Lever
- Original vs compressed configs
- Use original for high-impact steps
- Use compressed for most steps
- No data loss, just efficiency

### 8. Audit Trails
- Onboarding: raw input → final configs
- PrepInputs: compression results + token savings
- BatchComposer: batch planning → runs created
- Every step logged in PipelineSteps
- Every claim linked to source step

---

## 🔄 Comparison with Current Approach

### Current (Problematic)
- Prompts sheet has "live input/output" columns
- Running 80 dossiers → columns overwrite each other
- Can't see previous runs' data
- Testing pollutes production data
- No way to track "which config was used for this run?"

### Proposed (Fixed)
- Prompts sheet is config only (templates)
- PipelineSteps sheet has input/output per run
- Each run has separate rows (run_id scoped)
- Can see all runs' data (filter by run_id)
- Testing uses mode='test', same schema
- Runs.config_snapshot captures config used

---

## 🎯 Next Steps

1. **Review this document** - Does the schema make sense?
2. **Ask questions** - Any concerns or missing pieces?
3. **Approve schema** - Ready to generate CSVs?
4. **Generate CSVs** - Script creates 14 CSV files
5. **Create Google Sheet** - Import CSVs, share Sheet ID
6. **Build API** - Endpoints to read/write sheets

---

## 🔄 Recent Updates (Based on Your Feedback)

### 1. **All 3 Configs Get Compressed**
- **Clients sheet** now has compressed versions for: ICP config, industry research, AND research context
- **PrepInputs sheet** compresses all 3 configs
- **Flow:** Onboarding generates originals → PrepInputs compresses → Clients stores both versions
- Clear traceability: can see which columns map where

### 2. **07B_INSIGHT Decoupled from Merge Claims**
- **07B_INSIGHT** is just a regular research step (produces insight about market positioning)
- It extracts claims like other research steps
- **Merge Claims** is a separate utility operation (not tied to specific steps)
- Merge can happen multiple times per run, at least once

### 3. **MergedClaims Sheet Clarified**
- Job: Take all Claims.claims_json, merge them, remove redundancy/refuted conflicts
- Output: Same format as claims extraction (JSON array)
- NOT for creating context packs (those are targeted summaries)
- NOT used directly by dossier writers (writers use original claims)

### 4. **Contacts Sheet: Both Renderable + Processing Columns**
- **Columns A-S:** Renderable fields for app display (id, name, title, email, phone, bio_paragraph, etc.)
- **Columns T-AF:** Processing fields for generating copy (tier, bio_summary, why_they_matter, signal_relevance, email_copy, linkedin_copy, etc.)
- Both sets needed: app can render immediately, copy generation can iterate

### 5. **Sections Populate Dossier JSONB Columns**
- Each section type knows which JSONB column it populates (find_lead, enrich_lead, copy, insight, media)
- Section writers output JSON with exact snake_case field names
- `target_column` field tracks where each section's data goes

### 6. **Dossiers Sheet Shows Full Structure**
- Now includes complete JSON examples for all 5 JSONB columns
- Shows exact field names (snake_case) that app expects
- Denormalized fields (company_name, lead_score, timing_urgency, primary_signal) for querying

---

## ❓ Questions for You

Before we proceed, please confirm:

1. **Onboarding workflow** - Does the Onboarding → PrepInputs → Clients flow match your vision?
2. **BatchComposer** - Is tracking batch planning runs valuable, or overkill?
3. **SectionDefinitions** - Is variable validation important, or can we skip this sheet?
4. **MASTER sheet removal** - Comfortable removing it and using API parameters instead?
5. **Any missing pieces?** - What else needs to be in the schema?

---

**Plan file:** `/Users/connorjohnson/.claude/plans/zany-marinating-wreath.md`
**Status:** Awaiting your review and approval
