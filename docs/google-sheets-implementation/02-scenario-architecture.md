# Scenario Architecture: Isolated & Self-Contained

**Philosophy:** Each scenario should be runnable in isolation with minimal context

---

## Core Principle

**Pass IDs, Fetch Everything Else**

Instead of:
```
Main → Pass 50 variables → Scenario
```

Do this:
```
Main → Pass (run_id, client_id, seed) → Scenario
Scenario → Fetch what it needs → Do work → Write outputs
```

---

## What Gets Passed Through Start of Scenario

### Main Pipeline → Bridge Scenarios

**Minimal Context Only:**
- `run_id` - Links everything together
- `client_id` - For fetching client config
- `seed` (optional) - If provided by user
- `dossier_id` (later stages) - After dossier created

**That's it!** Everything else fetched within scenario.

### Bridge Scenarios → Sub-Scenarios (Parallel)

**Example: Enrich Contacts → Individual Contact Enrichment**

Pass:
- `run_id`
- `client_id`
- `dossier_id`
- `contact_object` - The specific contact to enrich

Fetch within sub-scenario:
- Client config (by client_id)
- Prompts (by slug)
- All claims (by run_id)
- Context pack (by run_id)

---

## What Gets Fetched Within Each Scenario

### Standard Fetch Pattern (Start of Every Scenario)

```
[1] Google Sheets > Get Values
    Range: Clients!A2:M100
    Filter: client_id = {{start.client_id}}
    Output: icp_config, industry_research, research_context, etc.

[2] Google Sheets > Get Values
    Range: Prompts!A2:L100
    Filter: prompt_slug = "enrich-lead"  // Or whatever this scenario needs
    Output: prompt_template, model, variables_used

[3] Google Sheets > Get Values (if needed)
    Range: Claims!A:E
    Filter: run_id = {{start.run_id}}
    Output: All claims produced so far

[4] Do work with fetched data
[5] Write outputs
```

**API Calls per Scenario:** ~2-4 reads (config + prompts + maybe previous outputs)

---

## Scenario Breakdown: What Each Needs

### 1. Main Dossier Pipeline Scenario

**Receives:** Nothing (user starts it)

**Generates:**
- `run_id` (RUN_20260112_143022)
- `client_id` (from user input or API call)
- `seed` (from user input)

**Fetches:**
- Nothing (just orchestrates)

**Writes:**
- Runs sheet: Initial row (status="running")

**Calls These Scenarios:**
1. Run Sync Search & Signal (pass: run_id, client_id, seed)
2. Enrich Lead (pass: run_id, client_id)
3. Enrich Opportunity (pass: run_id, client_id)
4. Client Specific (pass: run_id, client_id)
5. Enrich Contacts (pass: run_id, client_id)
6. Copy Generation (pass: run_id, client_id)
7. Insight (pass: run_id, client_id)
8. Media (pass: run_id, client_id)
9. Section Writers (pass: run_id, client_id, dossier_id)

---

### 2. Run Sync Search & Signal Scenario

**Receives:**
- run_id
- client_id
- seed

**Fetches:**
- Client config (Clients sheet, filter by client_id)
- Search Builder prompt (Prompts sheet, slug="search-builder")
- Signal Discovery prompt (Prompts sheet, slug="signal-discovery")

**Does:**
1. Search Builder LLM call
2. Signal Discovery LLM call (web search)
3. Extract claims

**Writes:**
- PipelineSteps: 2 rows (search builder + signal discovery)
- Claims: 1 row (signal discovery claims)
- ContextPacks: 1 row (signal context pack)

**Returns:** Nothing (writes to sheets)

---

### 3. Enrich Lead Scenario

**Receives:**
- run_id
- client_id

**Fetches:**
- Client config (Clients sheet)
- Enrich Lead prompt (Prompts sheet, slug="enrich-lead")
- Signal claims (Claims sheet, filter by run_id)
- Signal context pack (ContextPacks sheet, filter by run_id)

**Does:**
1. Enrich Lead LLM call

**Writes:**
- PipelineSteps: 1 row
- Claims: 1 row (enrich lead claims)

---

### 4. Enrich Contacts Scenario (Bridge)

**Receives:**
- run_id
- client_id

**Fetches:**
- Client config (Clients sheet)
- All claims (Claims sheet, filter by run_id)
- Enrich Contacts prompt (Prompts sheet, slug="enrich-contacts")

**Does:**
1. Initialize contact enrichment (extracts contacts from claims)
2. For each contact → Call Individual Contact Enrichment sub-scenario

**Calls Sub-Scenario:**
- Individual Contact Enrichment (pass: run_id, client_id, dossier_id, contact_object)
  - Runs 5-10 times in parallel

**Writes:**
- PipelineSteps: 1 row (initialize)
- (Sub-scenarios write their own contact rows)

---

### 5. Individual Contact Enrichment Sub-Scenario

**Receives:**
- run_id
- client_id
- dossier_id
- contact_object (the specific contact to enrich)

**Fetches:**
- Client config (Clients sheet)
- Enrich Contact prompt (Prompts sheet, slug="6_2_enrich_contact")
- All claims (Claims sheet, filter by run_id)
- Context pack (ContextPacks sheet, filter by run_id)

**Does:**
1. Enrich contact LLM call
2. Apollo/LinkedIn lookup (if tools available)
3. Extract contact details

**Writes:**
- Contacts sheet: 1 row (full 32 columns)
- PipelineSteps: 1 row (log enrichment step)

---

### 6. Section Writers Scenario (Bridge)

**Receives:**
- run_id
- client_id
- dossier_id

**Fetches:**
- Client config (Clients sheet)
- All section writer prompts (Prompts sheet, filter by stage="WRITE_DOSSIER")
- Merged claims (MergedClaims sheet, filter by run_id)
- All contacts (Contacts sheet, filter by dossier_id)

**Calls Sub-Scenarios:**
- Section Writer Intro (pass: run_id, client_id, claims, contacts)
- Section Writer Signals (pass: run_id, client_id, claims)
- Section Writer Contacts (pass: run_id, client_id, contacts)
- Section Writer Lead Intelligence (pass: run_id, client_id, claims)
- Section Writer Strategy (pass: run_id, client_id, claims)
- Section Writer Opportunity (pass: run_id, client_id, claims)
- Section Writer Client Request (pass: run_id, client_id, claims)

**Writes:**
- Nothing directly (sub-scenarios write sections)

---

### 7. Individual Section Writer Sub-Scenario

**Receives:**
- run_id
- client_id
- claims (pre-fetched and passed in)
- contacts (pre-fetched and passed in)

**Fetches:**
- Section writer prompt (Prompts sheet, slug="section-writer-intro")
- Client config (Clients sheet) - if not passed in

**Does:**
1. Section writer LLM call

**Writes:**
- Sections sheet: 1 row (section_name, section_data JSON)
- PipelineSteps: 1 row

---

## API Call Count Breakdown

### Per Scenario Type

**Simple Scenario (e.g., Enrich Lead):**
- Reads: 3 (client config, prompt, previous claims)
- Writes: 2 (PipelineSteps, Claims)
- Total: 5 API calls

**Bridge Scenario (e.g., Enrich Contacts):**
- Reads: 3 (client config, prompts, claims)
- Writes: 1 (PipelineSteps)
- Sub-scenarios: 10 × 5 = 50 API calls
- Total: 54 API calls

**Full Dossier Run:**
- Main pipeline: 1 write (Runs)
- Search & Signal: 5 calls
- Enrich Lead: 5 calls
- Enrich Opportunity: 5 calls
- Client Specific: 5 calls
- Enrich Contacts: 54 calls (includes 10 parallel sub-scenarios)
- Copy: 5 calls
- Insight: 5 calls
- Media: 5 calls
- Section Writers: 42 calls (7 parallel × 6 each)
- Final Assembly: 2 calls (Dossiers, update Runs)

**Total: ~135 API calls per dossier**

**Is this okay?**
- Rate limit: 100 calls per 100 seconds
- 135 calls over ~5-10 minutes = ~0.2-0.4 calls/second
- **Well within limits!**

---

## Denormalization Strategy: Input/Output Columns

You mentioned wanting to see input/output clearly. Here's how:

### PipelineSteps Sheet (Current)

```csv
step_id, run_id, prompt_id, step_name, status, input, output, model_used, tokens_used
```

**Input column:** Full JSON of what went into the LLM
**Output column:** Full JSON of what came out

**Example Row:**
```
STEP_RUN001_03, RUN_001, PRM_003, 3_ENTITY_RESEARCH, completed,
{"candidate_entity": "Acme Corp", "signal_data": {...}, "context_pack": {...}},
{"entity_narrative": "Acme Corp is...", "confidence": "HIGH"},
gpt-4.1, 1250, 3.2, 2026-01-12 14:30:22, 2026-01-12 14:30:25
```

**Benefits:**
- ✅ See exact input to step
- ✅ See exact output from step
- ✅ Reconstruct flow by reading rows
- ✅ Debug: "Why did this step fail? Look at input column"

**Tradeoff:**
- Slightly denormalized (claims might be in both Claims sheet AND PipelineSteps.input)
- Extra storage (JSON duplicated)

**Verdict:** WORTH IT for debugging visibility

---

## Example: Running Enrich Contact in Isolation

**Scenario:** You want to test contact enrichment for one contact without running full dossier.

**What you'd do:**

1. Open Make.com → Individual Contact Enrichment scenario
2. Click "Run this module only"
3. Provide test inputs:
```json
{
  "run_id": "TEST_RUN_001",
  "client_id": "CLT_EXAMPLE_001",
  "dossier_id": "DOSS_001",
  "contact_object": {
    "name": "John Doe",
    "title": "VP Engineering",
    "company": "Acme Corp"
  }
}
```
4. Scenario fetches everything it needs (client config, prompt, claims)
5. Runs enrichment
6. Writes to Contacts sheet
7. Done!

**No need to:**
- Run full pipeline
- Fetch data beforehand
- Pass 50 variables

**Self-contained!**

---

## When to Pass vs Fetch: Decision Tree

```
Is it an ID?
  YES → Pass it (run_id, client_id, dossier_id)
  NO → Continue

Is it large static config? (icp_config, prompts)
  YES → Fetch it (will be same for all parallel executions)
  NO → Continue

Is it dynamic per-execution? (contact_object, specific entity)
  YES → Pass it
  NO → Continue

Is it shared across many steps? (all_claims, merged_claims)
  YES → Fetch it (avoid passing huge JSON blobs)
  NO → Continue

Default: FETCH within scenario
```

---

## Visual Debugging: How to Reconstruct Flow

**Question:** "What claims were used to enrich Contact #3?"

**Query PipelineSteps:**
```
Filter: run_id = RUN_001 AND step_name = "6.2_ENRICH_CONTACT_003"
Look at: input column
```

**Input column shows:**
```json
{
  "contact": {"name": "John Doe", "title": "VP Eng"},
  "claims": [
    {"claim_id": "C1", "statement": "Acme Corp filed permit"},
    {"claim_id": "C5", "statement": "John Doe promoted to VP"}
  ],
  "context_pack": {...}
}
```

**Answer:** Claims C1 and C5 were used!

**No complex joins needed** - it's right there in the input column.

---

## Architecture Benefits

### ✅ Isolation
- Each scenario runnable independently
- Easy to test one step without full pipeline
- Can replay failed steps

### ✅ Debugging
- See input/output for every step
- No "where did this value come from?" confusion
- Reconstruct flow from sheets

### ✅ Simplicity
- Pass 3-4 IDs, fetch everything else
- No complex context passing
- Less coupling between scenarios

### ✅ Flexibility
- Change prompts in sheet → scenarios fetch new version
- Update client config → next run uses it
- No hardcoded context

### ✅ Scalability
- Parallel scenarios don't conflict (each fetches independently)
- Rate limits easily managed (2-5 calls per scenario)
- Clear concurrency boundaries

---

## Migration to Supabase

When you switch to Supabase, **Make.com scenarios don't change**:

**Current:**
```
[1] Google Sheets > Get Values (Clients)
[2] Google Sheets > Get Values (Prompts)
[3] LLM call
[4] Google Sheets > Add Row (Claims)
```

**Future:**
```
[1] HTTP > GET api.columnline.dev/clients/{client_id}
[2] HTTP > GET api.columnline.dev/prompts/enrich-lead
[3] LLM call
[4] HTTP > POST api.columnline.dev/claims
```

Same structure, different modules. **Your architecture is future-proof.**

---

## Next Steps

1. **Import CSVs to Google Sheets** (you do this)
2. **Build one simple scenario** (Enrich Lead in isolation):
   - Start with test inputs (run_id, client_id)
   - Fetch client config
   - Fetch prompt
   - Run LLM
   - Write to PipelineSteps + Claims
   - Test it!
3. **Expand to full pipeline** once pattern is proven

---

**Key Takeaway:** Pass IDs, fetch everything else. Each scenario is self-contained and debuggable. Accept some denormalization for visibility. Future-proof for Supabase migration.
