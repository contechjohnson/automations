# Make.com Google Sheets API Calls Reference

**Complete list of all reads/writes for dossier pipeline**
**Date:** 2026-01-12

---

## Sheet ID Setup

**In Make.com, create variable:**
- Name: `GOOGLE_SHEETS_ID`
- Value: `{your_sheet_id_from_url}`
- Use in all modules: `{{GOOGLE_SHEETS_ID}}`

---

## Main Pipeline Scenario

**Receives:** API call with `{client_id, seed}`

**Generates:**
```javascript
run_id = "RUN_" + formatDate(now, "YYYYMMDDHHmmss")
dossier_id = "DOSS_" + formatDate(now, "YYYYMMDD") + "_" + random(1000, 9999)
```

**Passes to sub-scenarios:** `{run_id, client_id, seed, dossier_id}`

### API Call 1: Write to Runs Sheet (Create Run)

**Module:** Google Sheets > Add a Row

**Config:**
- Spreadsheet ID: `{{GOOGLE_SHEETS_ID}}`
- Sheet Name: `Runs`

**Values:**
- A (run_id): `{{run_id}}`
- B (client_id): `{{client_id}}`
- C (status): `running`
- D (seed_data): `{{toString(seed)}}`
- E (dossier_id): `{{dossier_id}}`
- F (started_at): `{{formatDate(now, "YYYY-MM-DD HH:mm:ss")}}`
- G (completed_at): (empty)
- H (error_message): (empty)
- I (triggered_by): `api`
- J (config_snapshot): (empty or snapshot JSON)

### Call Sub-Scenarios

Each receives: `{run_id, client_id, seed, dossier_id}`

1. Run Sync Search & Signal
2. Enrich Lead
3. Enrich Opportunity
4. Client Specific
5. Enrich Contacts (bridge)
6. Copy Generation
7. Insight
8. Media
9. Section Writers (bridge)

### API Call 2: Update Runs Sheet (Complete Run)

**Module:** Google Sheets > Update a Row

**Config:**
- Spreadsheet ID: `{{GOOGLE_SHEETS_ID}}`
- Sheet Name: `Runs`
- Row: Search by run_id = `{{run_id}}`

**Values:**
- C (status): `completed`
- G (completed_at): `{{formatDate(now, "YYYY-MM-DD HH:mm:ss")}}`

---

## Bridge/Sub Scenario Pattern (Generic)

**Example: Enrich Lead Scenario**

**Receives:** `{run_id, client_id, seed, dossier_id}`

### API Call 1: Read Client Config

**Module:** Google Sheets > Get Values (Advanced)

**Config:**
- Spreadsheet ID: `{{GOOGLE_SHEETS_ID}}`
- Range: `Clients!A2:M100`
- Value Render Option: `UNFORMATTED_VALUE`

**Filter Output (Next Module):**
```javascript
// Use Array Iterator + Filter
{{map(get; "client_id")}} = {{client_id}}
```

**Access Values:**
```
{{filtered.icp_config}}              // Column D
{{filtered.icp_config_compressed}}   // Column E
{{filtered.industry_research}}       // Column F
{{filtered.industry_research_compressed}} // Column G
{{filtered.research_context}}        // Column H
{{filtered.research_context_compressed}}  // Column I
{{filtered.client_specific_research}} // Column J
```

### API Call 2: Read Prompt

**Module:** Google Sheets > Get Values (Advanced)

**Config:**
- Spreadsheet ID: `{{GOOGLE_SHEETS_ID}}`
- Range: `Prompts!A2:L100`

**Filter Output:**
```javascript
// Filter by prompt_slug
{{filter(get; "prompt_slug"; "enrich-lead")}}
```

**Access Values:**
```
{{filtered.0.prompt_template}}    // Column E (the actual prompt)
{{filtered.0.model}}              // Column F
{{filtered.0.variables_used}}     // Column I
{{filtered.0.variables_produced}} // Column J
```

### API Call 3: Read Previous Claims (If Needed)

**Module:** Google Sheets > Get Values (Advanced)

**Config:**
- Spreadsheet ID: `{{GOOGLE_SHEETS_ID}}`
- Range: `Claims!A2:E1000`

**Filter Output:**
```javascript
// Filter by run_id
{{filter(get; "run_id"; run_id)}}
```

**Access Values:**
```
{{array.claims_json}}  // Column D - All claims for this run
```

### API Call 4: Read Context Pack (If Needed)

**Module:** Google Sheets > Get Values (Advanced)

**Config:**
- Spreadsheet ID: `{{GOOGLE_SHEETS_ID}}`
- Range: `ContextPacks!A2:G1000`

**Filter Output:**
```javascript
// Filter by run_id
{{filter(get; "run_id"; run_id)}}
```

### LLM Call (Not a Sheets API Call)

**Module:** OpenAI > Create a Completion (or your LLM module)

**Inputs:**
- Prompt: `{{prompt.prompt_template}}`
- Variables: Interpolate client config, claims, etc.

**Outputs:**
- `{{llm_output}}`
- `{{tokens_used}}`
- Track runtime

### API Call 5: Write to PipelineSteps

**Module:** Google Sheets > Add a Row

**Config:**
- Spreadsheet ID: `{{GOOGLE_SHEETS_ID}}`
- Sheet Name: `PipelineSteps`

**Values:**
- A (step_id): `STEP_{{run_id}}_{{iterator}}`
- B (run_id): `{{run_id}}`
- C (prompt_id): `{{prompt.prompt_id}}`
- D (step_name): `5B_ENRICH_LEAD`
- E (status): `completed`
- F (input): `{{toString(input_object)}}` - Full input JSON
- G (output): `{{toString(llm_output)}}` - Full output JSON
- H (model_used): `{{prompt.model}}`
- I (tokens_used): `{{tokens_used}}`
- J (runtime_seconds): `{{runtime}}`
- K (started_at): `{{step_start_time}}`
- L (completed_at): `{{formatDate(now, "YYYY-MM-DD HH:mm:ss")}}`
- M (error_message): (empty)

### API Call 6: Write to Claims (If Produces Claims)

**Module:** Google Sheets > Add a Row

**Config:**
- Spreadsheet ID: `{{GOOGLE_SHEETS_ID}}`
- Sheet Name: `Claims`

**Values:**
- A (run_id): `{{run_id}}`
- B (step_id): `{{step_id}}`
- C (step_name): `5B_ENRICH_LEAD`
- D (claims_json): `{{toString(claims_array)}}` - Full claims as JSON
- E (created_at): `{{formatDate(now, "YYYY-MM-DD HH:mm:ss")}}`

---

## All Scenarios: Read/Write Breakdown

### 1. Run Sync Search & Signal

**Reads:**
- Clients!A2:M100 (get client config by client_id)
- Prompts!A2:L100 (get search-builder prompt)
- Prompts!A2:L100 (get signal-discovery prompt)

**Writes:**
- PipelineSteps (2 rows: search builder + signal discovery)
- Claims (1 row: signal discovery claims)
- ContextPacks (1 row: signal context pack)

**Total:** 3 reads, 4 writes = 7 API calls

### 2. Enrich Lead

**Reads:**
- Clients!A2:M100 (client config)
- Prompts!A2:L100 (enrich-lead prompt)
- Claims!A2:E1000 (previous claims by run_id)
- ContextPacks!A2:G1000 (context pack by run_id)

**Writes:**
- PipelineSteps (1 row)
- Claims (1 row)

**Total:** 4 reads, 2 writes = 6 API calls

### 3. Enrich Opportunity

**Reads:**
- Clients!A2:M100
- Prompts!A2:L100 (enrich-opportunity prompt)
- Claims!A2:E1000
- ContextPacks!A2:G1000

**Writes:**
- PipelineSteps (1 row)
- Claims (1 row)

**Total:** 4 reads, 2 writes = 6 API calls

### 4. Client Specific

**Reads:**
- Clients!A2:M100
- Prompts!A2:L100 (client-specific prompt)
- Claims!A2:E1000
- ContextPacks!A2:G1000

**Writes:**
- PipelineSteps (1 row)
- Claims (1 row)

**Total:** 4 reads, 2 writes = 6 API calls

### 5. Enrich Contacts (Bridge)

**Bridge Scenario Reads:**
- Clients!A2:M100
- Prompts!A2:L100 (enrich-contacts prompt)
- Claims!A2:E1000

**Bridge Writes:**
- PipelineSteps (1 row: initialize)

**Calls:** 10 × Individual Contact Enrichment sub-scenarios

**Sub-Scenario (per contact) Reads:**
- Clients!A2:M100
- Prompts!A2:L100 (6_2_enrich_contact prompt)
- Claims!A2:E1000
- ContextPacks!A2:G1000

**Sub-Scenario Writes:**
- Contacts (1 row: 32 columns)
- PipelineSteps (1 row)

**Total Bridge:** 3 reads, 1 write
**Total Per Sub:** 4 reads, 2 writes
**Total for 10 contacts:** 3 + (10 × 6) = 63 API calls

### 6. Copy Generation

**Reads:**
- Clients!A2:M100
- Prompts!A2:L100 (copy prompt)
- Contacts!A2:AG1000 (contacts by dossier_id)

**Writes:**
- PipelineSteps (1 row)
- Contacts (update with copy columns)

**Total:** 3 reads, 2 writes = 5 API calls

### 7. Insight

**Reads:**
- Clients!A2:M100
- Prompts!A2:L100 (insight prompt)
- Claims!A2:E1000

**Writes:**
- PipelineSteps (1 row)
- Claims (1 row: insight claims)

**Total:** 3 reads, 2 writes = 5 API calls

### 8. Media

**Reads:**
- Clients!A2:M100
- Prompts!A2:L100 (media prompt)
- Claims!A2:E1000

**Writes:**
- PipelineSteps (1 row)

**Total:** 3 reads, 1 write = 4 API calls

### 9. Section Writers (Bridge)

**Bridge Reads:**
- Clients!A2:M100
- Prompts!A2:L100 (all section writer prompts)
- MergedClaims!A2:E1000 (merged claims by run_id)
- Contacts!A2:AG1000 (contacts by dossier_id)

**Bridge Writes:**
- None (just orchestrates)

**Calls:** 7 × Section Writer sub-scenarios

**Sub-Scenario (per section) Reads:**
- Prompts!A2:L100 (specific section writer prompt)

**Sub-Scenario Writes:**
- Sections (1 row: section data)
- PipelineSteps (1 row)

**Total Bridge:** 4 reads, 0 writes
**Total Per Sub:** 1 read, 2 writes
**Total for 7 sections:** 4 + (7 × 3) = 25 API calls

### 10. Final Assembly (in Main Pipeline)

**Reads:**
- Sections!A2:I1000 (all sections by run_id)

**Writes:**
- Dossiers (1 row: final dossier)
- Runs (update status to completed)

**Total:** 1 read, 2 writes = 3 API calls

---

## Complete Dossier Run: Total API Calls

| Scenario | Reads | Writes | Total |
|----------|-------|--------|-------|
| Main (Create Run) | 0 | 1 | 1 |
| Search & Signal | 3 | 4 | 7 |
| Enrich Lead | 4 | 2 | 6 |
| Enrich Opportunity | 4 | 2 | 6 |
| Client Specific | 4 | 2 | 6 |
| Enrich Contacts (10 contacts) | 43 | 21 | 64 |
| Copy | 3 | 2 | 5 |
| Insight | 3 | 2 | 5 |
| Media | 3 | 1 | 4 |
| Section Writers (7 sections) | 11 | 14 | 25 |
| Final Assembly | 1 | 2 | 3 |
| **TOTAL** | **79** | **53** | **132** |

**Average over 5-10 minutes:** ~0.2-0.4 calls/second
**Rate Limit:** 1 call/second (100 per 100 seconds)
**Status:** ✅ Well within limits

---

## JSON Formatting in Make.com

### Converting to JSON String

**For input/output columns:**
```javascript
{{toString(value)}}
```

**For complex objects:**
```javascript
{{formatString(toJSON(value))}}
```

**Example:**
```javascript
// PipelineSteps.input column
{
  "icp_config": {{client.icp_config}},
  "seed": {{seed}},
  "previous_claims": {{toString(claims)}}
}
```

---

## Filtering Arrays in Make.com

### Filter by Field Value

```javascript
// Get client by ID
{{first(filter(clients; "client_id"; client_id))}}

// Get prompt by slug
{{first(filter(prompts; "prompt_slug"; "enrich-lead"))}}

// Get all claims for run
{{filter(claims; "run_id"; run_id)}}
```

### Map Array to Extract Field

```javascript
// Get all claim JSONs
{{map(filtered_claims; "claims_json")}}
```

---

## ID Generation Patterns

```javascript
// Run ID
RUN_{{formatDate(now, "YYYYMMDDHHmmss")}}

// Dossier ID
DOSS_{{formatDate(now, "YYYYMMDD")}}_{{random(1000, 9999)}}

// Step ID
STEP_{{run_id}}_{{add(iterator, 1)}}

// Merge ID
MERGE_{{run_id}}_{{iterator}}

// Pack ID
PACK_{{run_id}}_{{context_type}}
```

---

## Error Handling Pattern

**In each scenario, add error handler:**

```
[LLM Call] → [Error Handler]
  ↓
[Google Sheets > Add Row to PipelineSteps]
  - status: "failed"
  - error_message: {{error.message}}
```

---

## Testing Individual Scenarios

**To test "Enrich Lead" in isolation:**

1. Manually create test data in Runs sheet:
   - run_id: TEST_RUN_001
   - client_id: CLT_EXAMPLE_001
   - status: running

2. Manually create test claims in Claims sheet:
   - run_id: TEST_RUN_001
   - step_name: 2_SIGNAL_DISCOVERY
   - claims_json: `[{"claim": "test"}]`

3. Run "Enrich Lead" scenario with:
   ```json
   {
     "run_id": "TEST_RUN_001",
     "client_id": "CLT_EXAMPLE_001",
     "seed": null,
     "dossier_id": "DOSS_TEST_001"
   }
   ```

4. Scenario fetches config, prompt, claims
5. Runs LLM call
6. Writes to PipelineSteps + Claims

**No dependency on main pipeline!**

---

## Optimization: Batch Reads (If Needed)

If you hit rate limits, batch multiple sheet reads:

**Instead of:**
```
Read Clients → Filter
Read Prompts → Filter
Read Claims → Filter
```

**Do:**
```
HTTP > Make Request to batchGet endpoint

POST https://sheets.googleapis.com/v4/spreadsheets/{sheetId}/values:batchGet?ranges=Clients!A2:M100&ranges=Prompts!A2:L100&ranges=Claims!A2:E1000

Returns:
{
  "valueRanges": [
    { "range": "Clients!A2:M100", "values": [...] },
    { "range": "Prompts!A2:L100", "values": [...] },
    { "range": "Claims!A2:E1000", "values": [...] }
  ]
}
```

**3 reads in 1 API call!**

---

## Summary Checklist

- [ ] Import 14 CSVs to Google Sheets
- [ ] Get Sheet ID from URL
- [ ] Add GOOGLE_SHEETS_ID variable to Make.com
- [ ] Test read Clients + Prompts
- [ ] Test write to Runs
- [ ] Build first scenario (Enrich Lead) using this reference
- [ ] Test in isolation
- [ ] Expand to full pipeline

**You're equipped to build tonight!** 🚀
