# Make.com Google Sheets API Reference

**Purpose:** Use native Make.com Google Sheets modules for dossier pipeline
**Pattern:** Keep it simple - read configs once, pass through scenario

---

## Core API Endpoints (What Make.com Uses)

### Read Data
```
GET /v4/spreadsheets/{spreadsheetId}/values/{range}
```

**Make.com Module:** "Google Sheets > Get Values (Advanced)"

**Range Format Examples:**
- `Clients!A2:M2` - Single client row (row 2)
- `Prompts!A2:L100` - All prompts (rows 2-100)
- `Runs!A:J` - All runs, all columns

**Returns:**
```json
{
  "values": [
    ["value1", "value2", "value3"],
    ["value1", "value2", "value3"]
  ]
}
```

### Write Data (Append Row)
```
POST /v4/spreadsheets/{spreadsheetId}/values/{range}:append
```

**Make.com Module:** "Google Sheets > Add a Row"

**Request Body:**
```json
{
  "values": [
    ["col1_value", "col2_value", "col3_value"]
  ]
}
```

**Query Parameters:**
- `valueInputOption=USER_ENTERED` - Interprets input (dates, formulas)
- `valueInputOption=RAW` - Stores exactly as provided

---

## Simple Make.com Pattern (Recommended)

### Pattern: Fetch Once → Pass Through → Write Once Per Step

**Why this works:**
- Avoids refetching same data repeatedly
- Reduces API calls (20-30 per dossier instead of 50+)
- Easy to debug (see all data in scenario flow)

### Scenario Structure

```
[1] HTTP Module (Start Dossier)
    ↓ Receives: { client_id, seed_data }

[2] Google Sheets > Get Values (Clients row)
    ↓ Range: Clients!A2:M100
    ↓ Filter: client_id = {{1.client_id}}
    ↓ Outputs: icp_config, industry_research, research_context, etc.

[3] Google Sheets > Get Values (Prompts sheet)
    ↓ Range: Prompts!A2:L100
    ↓ Outputs: Array of all prompts

[4] Set Variables (Extract what you need)
    ↓ search_builder_prompt = filter(3.prompts, slug="search-builder")
    ↓ signal_discovery_prompt = filter(3.prompts, slug="signal-discovery")
    ↓ etc.

[5] Google Sheets > Add Row (Runs sheet)
    ↓ Creates run record with status="running"
    ↓ Outputs: run_id

[6] LLM Module (Search Builder)
    ↓ Prompt: {{4.search_builder_prompt}}
    ↓ Variables: icp_config={{2.icp_config}}, seed={{1.seed_data}}
    ↓ Outputs: search_queries JSON

[7] Google Sheets > Add Row (PipelineSteps)
    ↓ Logs step execution

[8] LLM Module (Signal Discovery)
    ↓ Prompt: {{4.signal_discovery_prompt}}
    ↓ Variables: search_queries={{6.search_queries}}
    ↓ Outputs: claims_json

[9] Google Sheets > Add Row (PipelineSteps)
[10] Google Sheets > Add Row (Claims)
    ↓ Writes claims_json to Claims sheet

... repeat pattern for remaining steps
```

---

## Data Flow Diagram

```
START
  ↓
READ (2 calls):
  1. Get client config (Clients sheet)
  2. Get all prompts (Prompts sheet)
  ↓
PROCESS (15-20 LLM steps):
  Each step:
    - Uses config from step 1
    - Uses prompt from step 2
    - Outputs to next step
    ↓
    WRITE (1-2 calls per step):
      - Log to PipelineSteps
      - If claims: Log to Claims
      - If contacts: Log to Contacts
  ↓
FINISH:
  - Write to Dossiers sheet
  - Update Runs sheet (status="completed")
```

**Total API Calls:** ~25-35 per dossier (2 reads + 20-30 writes)

---

## All Sheets You'll Use

### Config Sheets (Read at Start)

**1. Clients Sheet**
- **Range:** `Clients!A2:M100`
- **When:** Start of dossier run
- **Get:** icp_config, industry_research, research_context, client_specific_research, drip_schedule
- **Filter by:** client_id column

**2. Prompts Sheet**
- **Range:** `Prompts!A2:L100`
- **When:** Start of dossier run
- **Get:** All 20 prompts with their templates, models, variables
- **Filter by:** prompt_slug column (in Make.com)

### Execution Sheets (Write During Run)

**3. Runs Sheet**
- **Range:** `Runs!A:J`
- **When:** Start (status="running") and end (status="completed")
- **Write:** run_id, client_id, status, seed_data, started_at, completed_at

**4. PipelineSteps Sheet**
- **Range:** `PipelineSteps!A:M`
- **When:** After EVERY LLM call (15-20 times per dossier)
- **Write:** step_id, run_id, prompt_id, step_name, input, output, tokens_used, runtime_seconds

**5. Claims Sheet**
- **Range:** `Claims!A:E`
- **When:** After claims-producing steps (8-10 times)
- **Write:** run_id, step_id, step_name, claims_json, created_at

**6. MergedClaims Sheet**
- **Range:** `MergedClaims!A:E`
- **When:** After merge step (once per dossier)
- **Write:** merge_id, run_id, step_id, merged_claims_json, created_at

**7. ContextPacks Sheet**
- **Range:** `ContextPacks!A:G`
- **When:** After context pack builder (3 times typically)
- **Write:** pack_id, run_id, context_type, pack_content, produced_by_step

**8. Contacts Sheet**
- **Range:** `Contacts!A:AG`
- **When:** After contact enrichment (5-10 times)
- **Write:** id, dossier_id, run_id, name, email, linkedin_url, etc. (32 columns)

**9. Sections Sheet**
- **Range:** `Sections!A:I`
- **When:** After section writers (7-9 times)
- **Write:** section_id, run_id, section_name, section_data, produced_by_step

**10. Dossiers Sheet**
- **Range:** `Dossiers!A:L`
- **When:** Final assembly (once per dossier)
- **Write:** dossier_id, run_id, client_id, company_name, lead_score, timing_urgency, assembled_dossier

---

## Make.com Module Configuration Examples

### Example 1: Get Client Config

**Module:** Google Sheets > Get Values (Advanced)

**Settings:**
- Spreadsheet ID: `{{env.GOOGLE_SHEETS_ID}}`
- Range: `Clients!A2:M100`
- Value Render Option: `UNFORMATTED_VALUE`

**Filter Output:**
```javascript
// In next module, use Filter:
{{map(get; "client_id") = "CLT_001"}}
```

**Access Values:**
```
{{get.0.icp_config}}           // Column D
{{get.0.industry_research}}    // Column F
{{get.0.research_context}}     // Column H
```

### Example 2: Get Specific Prompt

**Module:** Google Sheets > Get Values (Advanced)

**Settings:**
- Spreadsheet ID: `{{env.GOOGLE_SHEETS_ID}}`
- Range: `Prompts!A2:L100`

**Filter in next module:**
```javascript
// Use Array Filter/Map:
{{filter(prompts; "prompt_slug"; "search-builder")}}
```

**Access Prompt:**
```
{{filtered.0.prompt_template}}   // Column E (the actual prompt)
{{filtered.0.model}}             // Column F
{{filtered.0.variables_used}}    // Column I
```

### Example 3: Write to Runs Sheet

**Module:** Google Sheets > Add a Row

**Settings:**
- Spreadsheet ID: `{{env.GOOGLE_SHEETS_ID}}`
- Sheet Name: `Runs`
- Values:
  - Column A: `{{run_id}}` (generate with formatDate(now; 'YYYYMMDDHHmmss'))
  - Column B: `{{client_id}}`
  - Column C: `running`
  - Column D: `{{seed_data}}`
  - Column E: (empty - dossier_id populated later)
  - Column F: `{{formatDate(now; 'YYYY-MM-DD HH:mm:ss')}}`
  - Column G: (empty - completed_at)
  - Column H: (empty - error_message)

### Example 4: Write to PipelineSteps Sheet

**Module:** Google Sheets > Add a Row

**Settings:**
- Spreadsheet ID: `{{env.GOOGLE_SHEETS_ID}}`
- Sheet Name: `PipelineSteps`
- Values:
  - Column A: `STEP_{{run_id}}_{{step_number}}`
  - Column B: `{{run_id}}`
  - Column C: `PRM_001` (prompt_id)
  - Column D: `1_SEARCH_BUILDER`
  - Column E: `completed`
  - Column F: `{{stringify(input_data)}}`  // JSON.stringify
  - Column G: `{{stringify(output_data)}}` // JSON.stringify
  - Column H: `gpt-4.1`
  - Column I: `{{tokens_used}}`
  - Column J: `{{runtime_seconds}}`
  - Column K: `{{formatDate(started_at; 'YYYY-MM-DD HH:mm:ss')}}`
  - Column L: `{{formatDate(now; 'YYYY-MM-DD HH:mm:ss')}}`
  - Column M: (empty - error_message)

### Example 5: Write Claims JSON

**Module:** Google Sheets > Add a Row

**Settings:**
- Spreadsheet ID: `{{env.GOOGLE_SHEETS_ID}}`
- Sheet Name: `Claims`
- Values:
  - Column A: `{{run_id}}`
  - Column B: `{{step_id}}`
  - Column C: `2_SIGNAL_DISCOVERY`
  - Column D: `{{stringify(claims_array)}}` // Full claims as JSON string
  - Column E: `{{formatDate(now; 'YYYY-MM-DD HH:mm:ss')}}`

---

## Helper Functions in Make.com

### Filter Array by Field
```javascript
// Get prompt by slug
{{map(filter(prompts; "prompt_slug"; "search-builder"); "prompt_template")}}

// Get client by ID
{{first(filter(clients; "client_id"; "CLT_001"))}}
```

### JSON Stringify
```javascript
// Convert object/array to JSON string
{{toString(value)}}
{{formatString(value)}}
```

### Generate IDs
```javascript
// Run ID
RUN_{{formatDate(now; 'YYYYMMDDHHmmss')}}

// Step ID
STEP_{{run_id}}_{{add(iterator; 1)}}

// Dossier ID
DOSS_{{formatDate(now; 'YYYYMMDD')}}_{{random(1000; 9999)}}
```

---

## Complete API Call List for Single Dossier

### Reads (2 calls)
1. `GET Clients!A2:M100` - Get client config
2. `GET Prompts!A2:L100` - Get all prompts

### Writes (25-35 calls depending on contacts/sections)

**Runs:** 2 calls
3. `POST Runs!A:J` - Create run (status="running")
4. `POST Runs!A:J` - Update run (status="completed") OR use UPDATE method

**PipelineSteps:** 15-20 calls
5-24. `POST PipelineSteps!A:M` - One per LLM step

**Claims:** 8-10 calls
25-34. `POST Claims!A:E` - One per claims-producing step

**MergedClaims:** 1 call
35. `POST MergedClaims!A:E` - After merge

**ContextPacks:** 3 calls
36-38. `POST ContextPacks!A:G` - Signal→Entity, Entity→Contacts, etc.

**Contacts:** 5-10 calls
39-48. `POST Contacts!A:AG` - One per discovered contact

**Sections:** 7-9 calls
49-57. `POST Sections!A:I` - One per section writer

**Dossiers:** 1 call
58. `POST Dossiers!A:L` - Final assembly

**Total:** ~35-60 calls per dossier (optimized with fetching once)

---

## Optimization: Batch Writes (Advanced)

If you hit rate limits, use batch append:

**Module:** HTTP > Make a Request

```
POST https://sheets.googleapis.com/v4/spreadsheets/{sheetId}/values:batchUpdate

Body:
{
  "valueInputOption": "USER_ENTERED",
  "data": [
    {
      "range": "PipelineSteps!A:M",
      "values": [
        ["step1_data"],
        ["step2_data"],
        ["step3_data"]
      ]
    },
    {
      "range": "Claims!A:E",
      "values": [
        ["claim1_data"],
        ["claim2_data"]
      ]
    }
  ]
}
```

This writes 5 rows in 1 API call instead of 5.

---

## Setup Checklist

### Before You Start
- [ ] Import 14 CSVs to Google Sheets
- [ ] Note Sheet ID from URL: `https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit`
- [ ] Verify Google Sheets connection in Make.com (already done for you)
- [ ] Create environment variable in Make.com: `GOOGLE_SHEETS_ID`

### Testing Workflow
1. Create test client in Clients sheet (CLT_TEST_001)
2. Build simple scenario: Read Clients → Filter by ID → Output
3. Verify you get correct client row
4. Add: Read Prompts → Filter by slug → Output
5. Verify you get correct prompt
6. Add: Write to Runs sheet → Check sheet shows new row
7. Full dossier run with all steps

---

## Common Issues & Solutions

### Issue: "Range not found"
**Cause:** Sheet name typo or doesn't exist
**Fix:** Double-check sheet name matches CSV import (e.g., "Clients" not "Clients Sheet")

### Issue: "Too many columns"
**Cause:** Trying to write more columns than sheet has
**Fix:** Match column count exactly (Runs = 10 columns A-J)

### Issue: "Values not appearing"
**Cause:** Writing to wrong range or sheet
**Fix:** Use `SheetName!A:Z` format, verify in Sheets after write

### Issue: "Rate limit exceeded"
**Cause:** Too many writes (>100 per 100 seconds)
**Fix:** Use batch writes (see Optimization section above)

### Issue: "Can't filter prompts by slug"
**Cause:** Make.com array syntax
**Fix:** Use Iterator module → Filter → Map pattern

---

## Next Steps

1. **Import CSVs to Google Sheets** (you do this)
2. **Copy Sheet ID** from URL
3. **Add to Make.com** as data store or env variable
4. **Build first scenario** (Search + Signal Discovery only)
5. **Test end-to-end** with one dossier
6. **Expand to full pipeline** once working

---

**Key Takeaway:** Fetch configs/prompts ONCE at start, pass through scenario, write outputs after each step. Simple pattern, easy to debug, reduces API calls.
