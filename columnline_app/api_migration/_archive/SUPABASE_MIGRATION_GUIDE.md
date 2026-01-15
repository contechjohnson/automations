# Supabase Migration: Lessons Learned & Next Steps

**Date:** 2026-01-14
**Status:** Phase 1 Complete (Search Builder → Signal Discovery → Claims)
**Success:** ✅ First 3-step scenario working end-to-end

---

## What We Built

Successfully migrated the first Make.com scenario from Google Sheets to Supabase:

**Scenario:** `01_SEARCH_AND_SIGNAL` (with Claims Extraction)
**Steps Migrated:**
1. Search Builder (o4-mini reasoning)
2. Signal Discovery (gpt-4.1 + web_search)
3. Claims Extraction (gpt-4.1)

**Database:** 14 tables with v2_ prefix (isolated from production)
**API:** Clean JSON endpoints, no JavaScript parsing needed
**Pattern:** Prepare → LLM → Transition → LLM → Transition → Complete

---

## The Winning Pattern

### Make.com Flow (3 AI Modules)

```
[1] HTTP: POST /steps/prepare
    Body: {
      "run_id": "{{run_id}}",
      "client_id": "{{client_id}}",
      "dossier_id": "{{dossier_id}}",
      "step_names": ["1_SEARCH_BUILDER"]
    }
    → Returns prepared input for Search Builder

[2] OpenAI: Run Search Builder
    System: {{1.steps[0].prompt_template}}
    User: {{toString(1.steps[0].input)}}
    Model: {{1.steps[0].model_used}}

[3] HTTP: POST /steps/transition
    Body: {
      "run_id": "{{run_id}}",
      "client_id": "{{client_id}}",
      "dossier_id": "{{dossier_id}}",
      "completed_step_name": "1_SEARCH_BUILDER",
      "completed_step_output": {{2}},  // <-- ENTIRE OpenAI response
      "next_step_name": "2_SIGNAL_DISCOVERY"
    }
    → Stores Search Builder output
    → Returns prepared input for Signal Discovery (auto-fetches Search output)

[4] OpenAI: Run Signal Discovery
    System: {{3.next_step.prompt_template}}
    User: {{toString(3.next_step.input)}}
    Model: {{3.next_step.model_used}}
    Tools: web_search

[5] HTTP: POST /steps/transition
    Body: {
      "completed_step_name": "2_SIGNAL_DISCOVERY",
      "completed_step_output": {{4}},
      "next_step_name": "CLAIMS_EXTRACTION"
    }
    → Stores Signal Discovery output
    → Returns prepared input for Claims (auto-fetches Signal output)

[6] OpenAI: Run Claims Extraction
    System: {{5.next_step.prompt_template}}
    User: {{toString(5.next_step.input)}}
    Model: {{5.next_step.model_used}}

[7] HTTP: POST /steps/complete
    Body: {
      "run_id": "{{run_id}}",
      "outputs": [{
        "step_name": "CLAIMS_EXTRACTION",
        "output": {{6}}  // <-- ENTIRE OpenAI response
      }]
    }
    → Stores Claims output (auto-extracts tokens/runtime)
```

---

## Key Lessons Learned

### ✅ What Worked

1. **Pass Entire OpenAI Response**
   - Don't manually extract fields in Make.com
   - Just pass `{{module_number}}` - API parses automatically
   - Tokens, runtime, and response all extracted server-side

2. **One API Call Between AI Modules**
   - `/steps/transition` does: store previous + prepare next
   - Reduces API calls from 2 to 1 between each AI module
   - Cleaner Make.com flow

3. **Auto-Fetch Dependencies**
   - API automatically fetches previous step outputs
   - Signal Discovery gets `search_builder_output` in input
   - Claims Extraction gets `signal_discovery_output` in input
   - No manual wiring needed

4. **v2_ Table Prefix**
   - Isolated from production (13 clients, 3,876 contacts, 734 dossiers untouched)
   - Can test freely without breaking existing system
   - Easy to identify new vs old in database

5. **Step Names Matter**
   - Use exact step names from CSV: `CLAIMS_EXTRACTION` not `PRODUCE_CLAIMS`
   - Check available steps: `curl api.columnline.dev/columnline/configs/CLT_EXAMPLE_001 | jq '.prompts[].step'`

### ❌ Common Pitfalls (And Fixes)

1. **Extra Spaces in Variables**
   - ❌ `"client_id": " CLT_EXAMPLE_001"` (space before CLT)
   - ✅ `"client_id": "{{client_id}}"` (no space before `{{`)
   - Error: "Client not found"

2. **Wrong Step Names**
   - ❌ `"next_step_name": "PRODUCE_CLAIMS"`
   - ✅ `"next_step_name": "CLAIMS_EXTRACTION"`
   - Error: "Prompt not found for step"

3. **Wrong Endpoint**
   - ❌ `/steps/prepare` for transitions (expects `step_names` array)
   - ✅ `/steps/transition` for store + prepare (expects `completed_step_name` + `next_step_name`)
   - Error: "Field required: step_names"

4. **Manual Token Extraction**
   - ❌ Trying to extract `{{response.usage.total_tokens}}` in Make.com
   - ✅ Just pass entire response, API extracts automatically
   - Benefit: Consistent parsing, no Make.com JavaScript

---

## API Endpoints Reference

### **POST /runs/start**
Create new dossier run (main pipeline entry point)

**Input:**
```json
{
  "client_id": "CLT_EXAMPLE_001",
  "seed_data": {...}  // Optional, any JSON structure
}
```

**Output:**
```json
{
  "run_id": "RUN_20260114_002901",
  "dossier_id": "DOSS_20260114_1550",
  "client_id": "CLT_EXAMPLE_001",
  "started_at": "2026-01-14T00:29:02Z"
}
```

---

### **POST /steps/prepare**
Prepare first step (or any isolated step)

**Input:**
```json
{
  "run_id": "RUN_20260114_002901",
  "client_id": "CLT_EXAMPLE_001",
  "dossier_id": "DOSS_20260114_1550",
  "step_names": ["1_SEARCH_BUILDER"]
}
```

**Output:**
```json
{
  "run_id": "RUN_20260114_002901",
  "steps": [{
    "step_id": "STEP_RUN_20260114_002901_01",
    "step_name": "1_SEARCH_BUILDER",
    "prompt_template": "### Role\n...",
    "model_used": "o4-mini",
    "input": {
      "current_date": "2026-01-14",
      "icp_config_compressed": {...},
      "seed_data": {...}
    },
    "produce_claims": false
  }]
}
```

---

### **POST /steps/transition**
Store previous output + prepare next step (one call)

**Input:**
```json
{
  "run_id": "RUN_20260114_002901",
  "client_id": "CLT_EXAMPLE_001",
  "dossier_id": "DOSS_20260114_1550",
  "completed_step_name": "1_SEARCH_BUILDER",
  "completed_step_output": {{entireOpenAIResponse}},
  "next_step_name": "2_SIGNAL_DISCOVERY"
}
```

**Output:**
```json
{
  "success": true,
  "run_id": "RUN_20260114_002901",
  "completed_step": "1_SEARCH_BUILDER",
  "tokens_used": 1249,
  "runtime_seconds": 14.0,
  "next_step": {
    "step_id": "STEP_RUN_20260114_002901_02",
    "step_name": "2_SIGNAL_DISCOVERY",
    "prompt_template": "...",
    "model_used": "gpt-4.1",
    "input": {
      ...configs...,
      "search_builder_output": {...}  // <-- AUTO-FETCHED
    }
  }
}
```

---

### **POST /steps/complete**
Store final step output (no next step)

**Input:**
```json
{
  "run_id": "RUN_20260114_002901",
  "outputs": [{
    "step_name": "CLAIMS_EXTRACTION",
    "output": {{entireOpenAIResponse}}
  }]
}
```

**Output:**
```json
{
  "success": true,
  "run_id": "RUN_20260114_002901",
  "steps_completed": ["CLAIMS_EXTRACTION"],
  "message": "1 step(s) completed successfully"
}
```

---

## Available Step Names (from v2_prompts)

Use these exact names when calling API endpoints:

### **Core Pipeline Steps**
```
1_SEARCH_BUILDER         - Generate search queries (o4-mini)
2_SIGNAL_DISCOVERY       - Find signals via web search (gpt-4.1 + web_search)
CLAIMS_EXTRACTION        - Extract atomic facts from signal output
3_ENTITY_RESEARCH        - Deep research on discovered entities
4_CONTACT_DISCOVERY      - Find contacts at target companies
```

### **Enrichment Steps**
```
5A_ENRICH_LEAD          - Enrich lead/company data
5B_ENRICH_OPPORTUNITY   - Enrich opportunity details
5C_CLIENT_SPECIFIC      - Client-specific enrichment
6_ENRICH_CONTACTS       - Batch enrich contacts
6_ENRICH_CONTACT_INDIVIDUAL - Individual contact enrichment
```

### **Content Generation**
```
10A_COPY                - Generate outreach copy
10B_COPY_CLIENT_OVERRIDE - Client-specific copy overrides
7B_INSIGHT              - Generate insights from research
8_MEDIA                 - Media/content recommendations
9_DOSSIER_PLAN          - Plan dossier structure
```

### **Section Writers** (Parallel execution)
```
10_WRITER_INTRO                - Write intro section
10_WRITER_SIGNALS              - Write signals section
10_WRITER_CONTACTS             - Write contacts section
10_WRITER_LEAD_INTELLIGENCE    - Write lead intelligence
10_WRITER_OPPORTUNITY          - Write opportunity section
10_WRITER_STRATEGY             - Write strategy section
10_WRITER_CLIENT_SPECIFIC      - Write client-specific section
10_WRITER_OUTREACH             - Write outreach section
10_WRITER_SOURCES              - Write sources section
```

### **Utility Steps**
```
MERGE_CLAIMS             - Merge and deduplicate claims
CONTEXT_PACK             - Build context pack for next step
00B_COMPRESS_ICP         - Compress ICP config
00B_COMPRESS_INDUSTRY    - Compress industry research
00B_COMPRESS_CONTEXT     - Compress research context
00B_COMPRESS_BATCH_STRATEGY - Compress batch strategy
00C_BATCH_COMPOSER       - Compose weekly batch
```

---

## Next Scenarios to Migrate

### **Priority Order (by frequency/importance)**

1. **✅ 01_SEARCH_AND_SIGNAL** (DONE)
   - 3 steps: Search Builder → Signal Discovery → Claims

2. **03_DEEP_RESEARCH_STEPS** (Next)
   - Entity Research (async deep research with o4-mini-deep-research)
   - Contact Discovery
   - Pattern: Sequential with async reasoning

3. **05_ENRICH_LEAD + 05_ENRICH_OPPORTUNITY + 05_CLIENT_SPECIFIC**
   - All enrichment steps
   - Pattern: Can run in parallel or sequential

4. **06_ENRICH_CONTACTS**
   - Batch contact enrichment
   - Individual contact enrichment loop
   - Pattern: Iterator pattern (one API call per contact)

5. **07B_INSIGHT + 10A_COPY + 10B_COPY_CLIENT_OVERRIDE**
   - Content generation steps
   - Pattern: Sequential, depends on merged claims

6. **08_MEDIA + 09_DOSSIER_PLAN**
   - Media recommendations and dossier planning
   - Pattern: Sequential

7. **10_WRITERS (6 parallel steps)**
   - All section writers run in parallel
   - Pattern: Parallel execution, all depend on merged claims
   - Use Make.com's parallel routes or CallSubscenario

---

## Migration Strategy for Next Scenarios

### **For Sequential Steps (like Deep Research)**

Same pattern as Search → Signal → Claims:
```
Prepare → LLM → Transition → LLM → Transition → Complete
```

### **For Parallel Steps (like Section Writers)**

Option A: **Sequential in Make.com** (simpler)
```
Prepare(writer_1) → LLM → Complete
Prepare(writer_2) → LLM → Complete
...
```

Option B: **True Parallel** (faster)
```
[1] Prepare all writers at once:
    POST /steps/prepare
    Body: {
      "step_names": [
        "10_WRITER_INTRO",
        "10_WRITER_SIGNALS",
        "10_WRITER_CONTACTS",
        ...
      ]
    }

[2-7] Run 6 OpenAI calls in parallel (Make.com parallel routes)

[8] Complete all at once:
    POST /steps/complete
    Body: {
      "outputs": [
        {"step_name": "10_WRITER_INTRO", "output": {{2}}},
        {"step_name": "10_WRITER_SIGNALS", "output": {{3}}},
        ...
      ]
    }
```

### **For Async Steps (like o4-mini-deep-research)**

Deep research takes 5-10 minutes. Pattern:
```
[1] Prepare step
[2] OpenAI Responses API (background=true)
    → Returns response_id
[3] Poll for completion:
    Repeater → Sleep 30s → Check status
[4] Get result when complete
[5] Store via /steps/complete
```

### **For Iterator Patterns (like Enrich Contacts)**

One API call per contact:
```
[1] Get list of contacts to enrich
[2] Iterator: For each contact
    [a] Prepare step (with contact data)
    [b] Run LLM
    [c] Complete step
[3] Aggregate results
```

---

## Database Structure

### **Tables Created (v2_ prefix)**

**Config Layer (3 tables):**
- `v2_clients` - Client configurations (1 row: CLT_EXAMPLE_001)
- `v2_prompts` - All 31 prompt templates
- `v2_section_definitions` - Expected section structures

**Execution Layer (11 tables):**
- `v2_runs` - One per dossier generation
- `v2_pipeline_steps` - Detailed step logging (input/output/tokens/runtime)
- `v2_claims` - Atomic facts extracted
- `v2_merged_claims` - Deduplicated claims
- `v2_context_packs` - Compressed context passed between steps
- `v2_contacts` - Discovered contacts
- `v2_sections` - Individual dossier sections
- `v2_dossiers` - Final assembled dossiers
- `v2_onboarding` - Client onboarding
- `v2_prep_inputs` - Config compression
- `v2_batch_composer` - Weekly batch planning

### **Query Examples**

**Get all steps for a run:**
```sql
SELECT step_name, status, tokens_used, runtime_seconds, completed_at
FROM v2_pipeline_steps
WHERE run_id = 'RUN_20260114_002901'
ORDER BY step_id;
```

**Get completed step output:**
```bash
curl "https://api.columnline.dev/columnline/outputs/RUN_20260114_002901?steps=2_SIGNAL_DISCOVERY"
```

**Check run status:**
```bash
curl "https://api.columnline.dev/columnline/runs/RUN_20260114_002901/status"
```

---

## Performance Metrics (First Run)

| Step | Model | Tokens | Runtime | Cost (est) |
|------|-------|--------|---------|------------|
| Search Builder | o4-mini | 1,249 | 14s | $0.01 |
| Signal Discovery | gpt-4.1 + web_search | 27,112 | 73s | $0.27 |
| Claims Extraction | gpt-4.1 | TBD | TBD | TBD |

**Total:** ~28k tokens, ~90s runtime, ~$0.28 per dossier (for first 3 steps)

**Notes:**
- Signal Discovery tokens are high due to web_search context
- This is expected and acceptable
- o4-mini reasoning is fast and cheap

---

## Make.com Best Practices

### **Variable Naming**
```
✅ "{{1.run_id}}"           - Clean
❌ " {{1.run_id}}"          - Extra space causes errors
❌ "{{1.data.run_id}}"      - Over-nested (our API returns flat)
```

### **Passing OpenAI Responses**
```
✅ "output": {{2}}           - Entire response
❌ "output": "{{2}}"         - Stringified (breaks parsing)
❌ "output": {{2.result}}    - Only text (loses metadata)
```

### **Model Selection**
```
✅ "model": "{{1.steps[0].model_used}}"  - From API
❌ "model": "gpt-4"                      - Hardcoded (may be wrong)
```

### **Error Handling**
- Use Make.com's automatic error handler routes
- Check for 404 (step not found) and 400 (validation errors)
- Extra spaces are the #1 cause of 404 errors

---

## Testing Checklist

Before marking a scenario as "migrated":

- [ ] All steps prepare correctly (GET prepared input)
- [ ] All LLM calls return valid responses
- [ ] All transitions store + prepare successfully
- [ ] Final complete stores output
- [ ] Check database: all steps have status="completed"
- [ ] Check database: tokens_used and runtime_seconds populated
- [ ] Check database: full outputs stored
- [ ] Verify auto-fetch worked (next steps got previous outputs)
- [ ] Compare output quality to Google Sheets baseline

**Query to verify:**
```bash
curl "https://api.columnline.dev/columnline/runs/{run_id}/status"
```

Expected:
```json
{
  "status": "running",
  "completed_steps": ["1_SEARCH_BUILDER", "2_SIGNAL_DISCOVERY", "CLAIMS_EXTRACTION"],
  "current_step": null
}
```

---

## Troubleshooting

### **404: Client not found**
- Check for extra spaces in `client_id`
- Verify client exists: `curl api.columnline.dev/columnline/configs/CLT_EXAMPLE_001`

### **404: Prompt not found for step**
- Use exact step name from database
- Check available steps: `curl api.columnline.dev/columnline/configs/CLT_EXAMPLE_001 | jq '.prompts[].step'`

### **500: Internal Server Error**
- Check API logs: `ssh root@64.225.120.95` → `journalctl -u automations-api -n 50`
- Usually means: parsing failed, database query error, or missing dependency

### **Auto-fetch not working**
- Verify previous step is marked "completed" in database
- Check step name matches exactly (case-sensitive)
- API only auto-fetches for known dependencies:
  - Signal Discovery gets Search Builder output
  - Claims Extraction gets Signal Discovery output

---

## Next Session Checklist

1. **Choose next scenario** (recommend: 03_DEEP_RESEARCH_STEPS)
2. **Review step names** for that scenario
3. **Check for async patterns** (o4-mini-deep-research)
4. **Create Make.com scenario** using proven pattern
5. **Test end-to-end**
6. **Update this guide** with new learnings

---

## Files Reference

| File | Purpose |
|------|---------|
| `database/columnline_schema_v2.sql` | Complete 14-table schema |
| `api/columnline/routes.py` | All API endpoints |
| `api/columnline/models.py` | Pydantic request/response models |
| `api/columnline/repository.py` | Database operations |
| `scripts/import_csvs_to_supabase.py` | CSV import script (31 prompts) |
| `tmp/sheets_export/` | CSV exports from Google Sheets |
| `.claude/skills/deploying-automations-api/` | GitHub Actions deployment guide |

---

## Success Criteria (Phase 1 ✅)

- [x] v2 schema deployed to Supabase
- [x] 31 prompts imported from CSV
- [x] 1 client imported (CLT_EXAMPLE_001)
- [x] API endpoints working (prepare, transition, complete)
- [x] First scenario migrated (Search → Signal → Claims)
- [x] Full OpenAI responses stored with metrics
- [x] Auto-fetch dependencies working
- [x] Make.com integration tested end-to-end

---

**Status:** Ready to migrate remaining 13 scenarios using proven pattern!
