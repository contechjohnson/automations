# 80-20 Minimal Implementation Guide

**Goal:** Get a working dossier with minimal API calls and no logging

---

## What You Need (Minimum)

### Import Only 2 CSVs

1. **Clients** (`01_clients.csv`)
2. **Prompts** (`02_prompts.csv`)

**Create these 3 empty sheets manually:**
3. **Claims** - Headers: `run_id, step_id, step_name, claims_json, created_at`
4. **Contacts** - Headers: `id, dossier_id, run_id, name, title, email, linkedin_url, bio_paragraph` (simplified 8 columns)
5. **Dossiers** - Headers: `dossier_id, run_id, client_id, company_name, lead_score, assembled_dossier, created_at` (simplified 7 columns)

**Skip:** All other sheets (Runs, PipelineSteps, etc.)

---

## Scenario Pattern (Simplified)

### Every Scenario Looks Like This:

```
[1] START (receives: {client_id, previous_outputs})
  ↓
[2] Google Sheets > Get Values (Advanced)
    Spreadsheet: {{GOOGLE_SHEETS_ID}}
    Range: Clients!A2:M100
    → Filter by client_id
    → Store: {{client_config}}
  ↓
[3] Google Sheets > Get Values (Advanced)
    Spreadsheet: {{GOOGLE_SHEETS_ID}}
    Range: Prompts!A2:L100
    → Filter by slug (e.g., "enrich-lead")
    → Store: {{prompt}}
  ↓
[4] OpenAI > Create Completion (or your LLM module)
    Prompt: {{prompt.prompt_template}}
    Variables: {{client_config.icp_config}}, {{previous_outputs}}
    → Store: {{llm_output}}
  ↓
[5] IF this step produces claims:
    Google Sheets > Add a Row
    Sheet: Claims
    Values: [run_id, step_id, step_name, {{toString(llm_output.claims)}}, {{now}}]
  ↓
[6] Pass {{llm_output}} to next scenario
```

**No logging to PipelineSteps!**

---

## Native Module Configurations

### Read Client Config

**Module:** Google Sheets > Get Values (Advanced)

**Settings:**
- Spreadsheet: Choose your sheet or use `{{GOOGLE_SHEETS_ID}}`
- Sheet name: `Clients`
- Range: `A2:M100`
- Value render option: `UNFORMATTED_VALUE`

**In next module (Iterator or Array Filter):**
```javascript
// Filter array to find your client
{{filter(1.values; "0"; client_id)}}
// Where "0" is the index of client_id column (column A = index 0)
```

**Or use native Search Rows module:**
- Module: Google Sheets > Search Rows
- Sheet: Clients
- Filter: Column A (client_id) = `{{client_id}}`
- Returns single row

### Read Prompt

**Module:** Google Sheets > Get Values (Advanced)

**Settings:**
- Spreadsheet: `{{GOOGLE_SHEETS_ID}}`
- Sheet name: `Prompts`
- Range: `A2:L100`

**Filter for your prompt:**
```javascript
// Get prompt by slug
{{first(filter(2.values; "1"; "enrich-lead"))}}
// Where "1" is the index of prompt_slug column (column B = index 1)
```

### Write to Claims

**Module:** Google Sheets > Add a Row

**Settings:**
- Spreadsheet: `{{GOOGLE_SHEETS_ID}}`
- Sheet name: `Claims`
- Values:
  - run_id: `{{run_id}}`
  - step_id: `{{step_id}}`
  - step_name: `ENRICH_LEAD`
  - claims_json: `{{toString(llm_output.claims)}}`
  - created_at: `{{formatDate(now; "YYYY-MM-DD HH:mm:ss")}}`

### Write to Contacts

**Module:** Google Sheets > Add a Row (use Iterator for multiple contacts)

**Settings:**
- Spreadsheet: `{{GOOGLE_SHEETS_ID}}`
- Sheet name: `Contacts`
- Values (simplified):
  - id: `CONT_{{random(1000; 9999)}}`
  - dossier_id: `{{dossier_id}}`
  - run_id: `{{run_id}}`
  - name: `{{contact.name}}`
  - title: `{{contact.title}}`
  - email: `{{contact.email}}`
  - linkedin_url: `{{contact.linkedin_url}}`
  - bio_paragraph: `{{contact.bio}}`

### Write to Dossiers (Final)

**Module:** Google Sheets > Add a Row

**Settings:**
- Spreadsheet: `{{GOOGLE_SHEETS_ID}}`
- Sheet name: `Dossiers`
- Values (simplified):
  - dossier_id: `{{dossier_id}}`
  - run_id: `{{run_id}}`
  - client_id: `{{client_id}}`
  - company_name: `{{final_output.company_name}}`
  - lead_score: `{{final_output.lead_score}}`
  - assembled_dossier: `{{toString(final_output)}}`
  - created_at: `{{formatDate(now; "YYYY-MM-DD HH:mm:ss")}}`

---

## What to Pass Between Scenarios

### Main Pipeline → Scenarios

```json
{
  "run_id": "RUN_20260112_143022",
  "dossier_id": "DOSS_20260112_5432",
  "client_id": "CLT_EXAMPLE_001",
  "seed": {"entity": "Acme Corp"}
}
```

### Scenario → Scenario (Pass Outputs Directly)

**Instead of writing to sheets, just pass JSON:**

```json
{
  "run_id": "RUN_20260112_143022",
  "client_id": "CLT_EXAMPLE_001",
  "signal_claims": {...},
  "entity_claims": {...},
  "enrichment_data": {...}
}
```

**When you need it for section writers:**
- Read Claims sheet (filter by run_id)
- Read Contacts sheet (filter by dossier_id)
- Assemble dossier

---

## Priority Implementation Order

### Phase 1: Core Flow (Tonight)

1. ✅ Import Clients + Prompts CSVs
2. ✅ Create Claims, Contacts, Dossiers sheets (empty with headers)
3. ✅ Build one simple scenario (Enrich Lead):
   - Read Clients
   - Read Prompts
   - Call LLM
   - Write to Claims
4. ✅ Test it works

### Phase 2: Full Pipeline (This Week)

1. ✅ Build all research scenarios (Search, Entity, Enrich, etc.)
2. ✅ Write to Claims after each (when produces claims)
3. ✅ Build contact enrichment
4. ✅ Write to Contacts sheet
5. ✅ Build section writers
6. ✅ Read Claims + Contacts → Write Dossiers

### Phase 3: Add Logging (Later)

1. ⏳ Import remaining CSVs (Runs, PipelineSteps)
2. ⏳ Add logging to each scenario
3. ⏳ Debug with full execution history

---

## Simplified API Call Count

**Per Dossier (Minimal):**

| Operation | Count |
|-----------|-------|
| Read Clients | 1 |
| Read Prompts | 1-2 (or read once, store in memory) |
| Write Claims | 8 |
| Write Contacts | 10 |
| Write Dossiers | 1 |
| **TOTAL** | **21-22 calls** |

vs Full Implementation: 132 calls

**You save 110 API calls by skipping logging!**

---

## Example: Minimal Enrich Lead Scenario

**What it looks like in Make.com:**

```
[1] Webhook (Start)
    Receives: {run_id, client_id, dossier_id}

[2] Google Sheets > Search Rows
    Sheet: Clients
    Filter: client_id = {{1.client_id}}
    Output: {{2.client_config}}

[3] Google Sheets > Search Rows
    Sheet: Prompts
    Filter: prompt_slug = "enrich-lead"
    Output: {{3.prompt}}

[4] OpenAI > Create Completion
    Model: {{3.model}}
    Prompt: {{3.prompt_template}}
    System: Use {{2.icp_config}}, {{2.industry_research}}
    Output: {{4.llm_output}}

[5] Google Sheets > Add Row
    Sheet: Claims
    run_id: {{1.run_id}}
    step_id: STEP_{{1.run_id}}_ENRICH
    step_name: ENRICH_LEAD
    claims_json: {{toString(4.claims)}}
    created_at: {{formatDate(now)}}

[6] Response (Return)
    Return: {{4.llm_output}}
```

**That's it! 2 reads, 1 write = 3 API calls**

---

## Common Pitfalls

### ❌ Don't Use "Make an API Call" Module

**Wrong:**
```
Google Sheets > Make an API Call
URL: https://sheets.googleapis.com/v4/spreadsheets/...
Body: {...}
```

**Right:**
```
Google Sheets > Add a Row
Sheet: Claims
Values: [...]
```

**Why:** Native modules are simpler and handle authentication automatically.

### ❌ Don't Filter Rows in Sheets (Slow)

**Wrong:**
```
Read entire Prompts sheet (100 rows)
Filter in Make.com for specific slug
```

**Right:**
```
Google Sheets > Search Rows
Filter: prompt_slug = "enrich-lead"
Returns only matching row
```

**Why:** Faster and cleaner.

### ❌ Don't Pass Huge JSONs Between Scenarios

**Wrong:**
```
Pass all_claims JSON (500KB) through scenario chain
```

**Right:**
```
Write to Claims sheet
Next scenario reads Claims sheet by run_id
```

**Why:** Avoid Make.com variable size limits.

---

## When to Add Logging

**Add logging when:**
- ✅ Core pipeline works (dossiers generate successfully)
- ✅ You need to debug why a step failed
- ✅ You want to see what went into/out of each step
- ✅ You need execution history

**How to add:**
1. Import Runs, PipelineSteps CSVs
2. Add one module after each LLM call:
   ```
   Google Sheets > Add Row (PipelineSteps)
   Values: step_id, run_id, input, output, tokens_used, runtime
   ```
3. Done!

---

## Testing Minimal Implementation

**Test with one dossier:**

1. Create test client in Clients sheet:
   - client_id: `TEST_001`
   - icp_config: `{"signals": ["permit"]}`

2. Run main pipeline with:
   ```json
   {
     "client_id": "TEST_001",
     "seed": {"entity": "Test Corp"}
   }
   ```

3. Check:
   - ✅ Claims sheet has 8 rows (one per claims step)
   - ✅ Contacts sheet has 5-10 rows
   - ✅ Dossiers sheet has 1 row (final dossier)

4. Open dossier JSON in Dossiers sheet
5. Verify it has all expected fields (company_name, lead_score, etc.)

**If yes → You have a minimal viable dossier!**

---

## Summary: Your Action Plan Tonight

**Setup (15 min):**
- [ ] Import Clients CSV to Google Sheets
- [ ] Import Prompts CSV to Google Sheets
- [ ] Create Claims sheet (5 columns, empty)
- [ ] Create Contacts sheet (8 columns, empty)
- [ ] Create Dossiers sheet (7 columns, empty)
- [ ] Get Sheet ID, add to Make.com

**Build First Scenario (30 min):**
- [ ] Pick Enrich Lead scenario
- [ ] Add: Read Clients (Search Rows)
- [ ] Add: Read Prompts (Search Rows)
- [ ] Add: OpenAI call
- [ ] Add: Write to Claims
- [ ] Test it

**Expand (1-2 hours):**
- [ ] Clone scenario for other steps
- [ ] Connect main pipeline
- [ ] Test full dossier
- [ ] Check Dossiers sheet has output

**You're done!** No logging needed yet. Just working dossiers.

---

**Next:** When ready for logging, read `04-complete-api-calls.md` to add PipelineSteps writes.
