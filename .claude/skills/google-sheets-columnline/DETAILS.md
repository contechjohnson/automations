# Google Sheets Columnline - Detailed Reference

**Sheet ID:** `1G70bxnt_P_2_qAqssrjnzkhBCPUa7gVAKMmc_mTn9fQ`

**Sheet URL:** https://docs.google.com/spreadsheets/d/1G70bxnt_P_2_qAqssrjnzkhBCPUa7gVAKMmc_mTn9fQ/edit

---

## Complete 14-Sheet Schema

### Config Layer (Read-Only During Runs)

#### 1. Clients (`01_clients` or `Clients`)
**Range:** `A2:M100`

| Col | Field | Type |
|-----|-------|------|
| A | client_id | Text |
| B | client_name | Text |
| C | status | Enum (active/inactive) |
| D | icp_config | JSON (original) |
| E | icp_config_compressed | JSON |
| F | industry_research | JSON (original) |
| G | industry_research_compressed | JSON |
| H | research_context | JSON (original) |
| I | research_context_compressed | JSON |
| J | client_specific_research | JSON |
| K | drip_schedule | JSON |
| L | created_at | DateTime |
| M | updated_at | DateTime |

#### 2. Prompts (`02_prompts` or `Prompts`)
**Range:** `A2:L100`

| Col | Field | Type |
|-----|-------|------|
| A | prompt_id | Text (PRM_001) |
| B | prompt_slug | Text (search-builder) |
| C | stage | Text (FIND_LEAD) |
| D | step | Text (1_SEARCH_BUILDER) |
| E | prompt_template | Text (full prompt) |
| F | model | Text (gpt-4.1) |
| G | produce_claims | Boolean |
| H | context_pack_produced | Boolean |
| I | variables_used | JSON array |
| J | variables_produced | JSON array |
| K | version | Text |
| L | created_at | DateTime |

#### 3. SectionDefinitions (`03_section_definitions`)
**Range:** `A2:F100`

| Col | Field | Type |
|-----|-------|------|
| A | section_name | Text |
| B | expected_variables | JSON array |
| C | variable_types | JSON object |
| D | validation_rules | JSON object |
| E | description | Text |
| F | example_output | JSON |

---

### Execution Layer (Per-Run Mutable)

#### 4. Onboarding (`04_onboarding`)
**Range:** `A2:O100`

| Col | Field |
|-----|-------|
| A | onboarding_id |
| B | client_name |
| C | status |
| D | client_info |
| E | transcripts |
| F | client_material |
| G | pre_research |
| H | onboarding_system_prompt |
| I | generated_icp_config |
| J | generated_industry_research |
| K | generated_research_context |
| L | generated_batch_strategy |
| M | client_id |
| N | started_at |
| O | completed_at |

#### 5. PrepInputs (`05_prep_inputs`)
**Range:** `A2:M100`

| Col | Field |
|-----|-------|
| A | prep_id |
| B | client_id |
| C | status |
| D | original_icp_config |
| E | compressed_icp_config |
| F | original_industry_research |
| G | compressed_industry_research |
| H | original_research_context |
| I | compressed_research_context |
| J | compression_prompt |
| K | token_savings |
| L | started_at |
| M | completed_at |

#### 6. BatchComposer (`06_batch_composer`)
**Range:** `A2:J100`

| Col | Field |
|-----|-------|
| A | batch_id |
| B | client_id |
| C | status |
| D | batch_strategy |
| E | seed_pool_input |
| F | last_batch_hints |
| G | recent_feedback |
| H | run_ids_created |
| I | started_at |
| J | completed_at |

#### 7. Runs (`07_runs`)
**Range:** `A2:J1000`

| Col | Field |
|-----|-------|
| A | run_id |
| B | client_id |
| C | status |
| D | seed_data |
| E | dossier_id |
| F | started_at |
| G | completed_at |
| H | error_message |
| I | triggered_by |
| J | config_snapshot |

#### 8. PipelineSteps (`08_pipeline_steps`)
**Range:** `A2:M5000`

| Col | Field | Notes |
|-----|-------|-------|
| A | step_id | |
| B | run_id | FK to Runs |
| C | prompt_id | FK to Prompts |
| D | step_name | |
| E | status | |
| F | input | **Full input JSON** |
| G | output | **Full output JSON** |
| H | model_used | |
| I | tokens_used | |
| J | runtime_seconds | |
| K | started_at | |
| L | completed_at | |
| M | error_message | |

#### 9. Claims (`09_claims`)
**Range:** `A2:E5000`

| Col | Field | Notes |
|-----|-------|-------|
| A | run_id | |
| B | step_id | |
| C | step_name | |
| D | claims_json | **Full claims array as JSON blob** |
| E | created_at | |

#### 10. MergedClaims (`10_merged_claims`)
**Range:** `A2:E100`

| Col | Field |
|-----|-------|
| A | merge_id |
| B | run_id |
| C | step_id |
| D | merged_claims_json |
| E | created_at |

#### 11. ContextPacks (`11_context_packs`)
**Range:** `A2:G100`

| Col | Field |
|-----|-------|
| A | pack_id |
| B | run_id |
| C | context_type |
| D | pack_content |
| E | produced_by_step |
| F | consumed_by_steps |
| G | created_at |

#### 12. Contacts (`12_contacts`)
**Range:** `A2:AG1000`

33 columns total (A through AG). Key columns:
- A: id
- B: dossier_id
- C: run_id
- D-M: Generation columns (name, title, email, linkedin, etc.)
- N-AG: Renderable columns (for app display)

#### 13. Sections (`13_sections`)
**Range:** `A2:I1000`

| Col | Field |
|-----|-------|
| A | section_id |
| B | run_id |
| C | section_name |
| D | section_data |
| E | claim_ids_used |
| F | produced_by_step |
| G | status |
| H | variables_produced |
| I | created_at |

#### 14. Dossiers (`14_dossiers`)
**Range:** `A2:L100`

| Col | Field |
|-----|-------|
| A | dossier_id |
| B | run_id |
| C | client_id |
| D | target_entity |
| E | lead_score |
| F | timing_urgency |
| G | assembled_dossier |
| H | sources |
| I | sections_complete |
| J | sections_missing |
| K | created_at |
| L | delivered_at |

---

## Make.com API Call Templates

**Important:** Sheet tabs might be named `01_clients`, `02_prompts` etc. Use exact names from your sheet.

### Read Single Sheet

**Method:** GET
**URL:**
```
/spreadsheets/{{GOOGLE_SHEETS_ID}}/values/'01_clients'!A2:M100
```

### Read Multiple Sheets (Batch)

**Method:** GET
**URL:**
```
/spreadsheets/{{GOOGLE_SHEETS_ID}}/values:batchGet?ranges='01_clients'!A2:M100&ranges='02_prompts'!A2:L100
```

**Access data:**
```
{{1.body.valueRanges[0].values}}  // First range (Clients)
{{1.body.valueRanges[1].values}}  // Second range (Prompts)
```

### Append Row to Single Sheet

**Method:** POST
**URL:**
```
/spreadsheets/{{GOOGLE_SHEETS_ID}}/values/'07_runs'!A:J:append?valueInputOption=USER_ENTERED
```

**Body:**
```json
{
  "values": [[
    "{{run_id}}",
    "{{client_id}}",
    "running",
    "{{toString(seed_data)}}",
    "",
    "{{formatDate(now; 'YYYY-MM-DD HH:mm:ss')}}",
    "",
    "",
    "api",
    "{{toString(config_snapshot)}}"
  ]]
}
```

### Write to Multiple Sheets (Batch)

**Method:** POST
**URL:**
```
/spreadsheets/{{GOOGLE_SHEETS_ID}}/values:batchUpdate
```

**Body:**
```json
{
  "valueInputOption": "USER_ENTERED",
  "data": [
    {
      "range": "'08_pipeline_steps'!A:M",
      "values": [[
        "{{step_id}}",
        "{{run_id}}",
        "{{prompt_id}}",
        "{{step_name}}",
        "completed",
        "{{toString(input)}}",
        "{{toString(output)}}",
        "{{model}}",
        "{{tokens}}",
        "{{runtime}}",
        "{{started_at}}",
        "{{formatDate(now; 'YYYY-MM-DD HH:mm:ss')}}",
        ""
      ]]
    },
    {
      "range": "'09_claims'!A:E",
      "values": [[
        "{{run_id}}",
        "{{step_id}}",
        "{{step_name}}",
        "{{toString(claims)}}",
        "{{formatDate(now; 'YYYY-MM-DD HH:mm:ss')}}"
      ]]
    }
  ]
}
```

### Update Existing Row

**Method:** PUT
**URL:**
```
/spreadsheets/{{GOOGLE_SHEETS_ID}}/values/'07_runs'!A{{row_number}}:J{{row_number}}?valueInputOption=USER_ENTERED
```

**Body:**
```json
{
  "values": [[
    "{{run_id}}",
    "{{client_id}}",
    "completed",
    "{{toString(seed_data)}}",
    "{{dossier_id}}",
    "{{started_at}}",
    "{{formatDate(now; 'YYYY-MM-DD HH:mm:ss')}}",
    "",
    "api",
    "{{toString(config_snapshot)}}"
  ]]
}
```

---

## Common Patterns

### Generate IDs

```javascript
// run_id
"RUN_" + formatDate(now; "YYYYMMDDHHmmss")
// Example: RUN_20260112143022

// dossier_id
"DOSS_" + formatDate(now; "YYYYMMDD") + "_" + random(1000; 9999)
// Example: DOSS_20260112_5432

// step_id
"STEP_" + run_id + "_" + {{iterator}}
// Example: STEP_RUN_20260112_143022_03
```

### JSON Formatting

**Always use `toString()` for JSON fields:**
```javascript
{{toString(claims)}}
{{toString(config_snapshot)}}
{{toString(input)}}
{{toString(output)}}
```

### DateTime Formatting

```javascript
{{formatDate(now; "YYYY-MM-DD HH:mm:ss")}}
// Example: 2026-01-12 14:30:22
```

### Filter Arrays from Batch Response

```javascript
// Get first client row
{{first(1.body.valueRanges[0].values)}}

// Get specific column (0-indexed)
{{first(1.body.valueRanges[0].values)[0]}}  // client_id (column A)
{{first(1.body.valueRanges[0].values)[3]}}  // icp_config (column D)
```

---

## Common Operations

### Start a New Run

1. **Read client config:**
```
GET /spreadsheets/{ID}/values:batchGet?ranges='01_clients'!A2:M100&ranges='02_prompts'!A2:L100
```

2. **Create run:**
```
POST /spreadsheets/{ID}/values/'07_runs'!A:J:append
Body: [run_id, client_id, "running", seed, "", now, "", "", "api", config]
```

3. **Execute step + log:**
```
POST /spreadsheets/{ID}/values:batchUpdate
Body: {
  data: [
    {range: '08_pipeline_steps'!A:M, values: [...]},
    {range: '09_claims'!A:E, values: [...]}  // if produces claims
  ]
}
```

### Update Run Status

```
// Find row number first, then:
PUT /spreadsheets/{ID}/values/'07_runs'!A{row}:J{row}
Body: {values: [[run_id, client_id, "completed", seed, dossier_id, ...]]}
```

---

## Architecture Notes

**Pass IDs, Fetch Everything:**
- Main → Scenarios: pass `run_id`, `client_id`, `dossier_id`
- Each scenario fetches configs from Clients/Prompts sheets
- Write execution logs to PipelineSteps + Claims

**Denormalization:**
- PipelineSteps has full `input` and `output` JSON
- Claims also logged in PipelineSteps.output
- Accept duplication for debugging visibility

**Per-Run Isolation:**
- Each run gets unique `run_id`
- All execution data scoped by `run_id`
- No conflicts between concurrent runs

---

## Documentation Files

**Main README:**
`docs/google-sheets-implementation/README.md`

**Key Documents:**
- `01-schema-design.md` - Complete schema reference
- `02-scenario-architecture.md` - Make.com scenario patterns
- `09-paste-ready-api-calls.md` - All API call templates
- `10-prompts-updated.md` - Prompts CSV status

**CSVs:**
`tmp/sheets_export/*.csv` (14 files)

---

## Variables to Set in Make.com

```
GOOGLE_SHEETS_ID = 1G70bxnt_P_2_qAqssrjnzkhBCPUa7gVAKMmc_mTn9fQ
```

Set this as a scenario variable or organization variable for reuse across all scenarios.

---

## Quick Troubleshooting

**Error: "Unable to parse range"**
- Check exact sheet tab name (might be `01_clients` not `Clients`)
- Use single quotes around sheet names with underscores: `'01_clients'!A2:M100`

**Error: "404 /v4/v4/spreadsheets"**
- Remove `/v4` from URL start (Make.com base already has it)
- Use: `/spreadsheets/{ID}/...` not `/v4/spreadsheets/{ID}/...`

**Error: "Permission denied"**
- Share sheet with service account email
- Or ensure Make.com Google Sheets connection has access

**Empty response:**
- Check range includes data rows (A2:M100 not A1:M100)
- Verify sheet has data in those rows

---

## Implementation Patterns (LESSONS LEARNED)

### Architecture: Orchestrator + Workers

**Key Insight:** Main pipeline does NO AI calls. Sub-scenarios do ALL the work.

**Main Pipeline (Orchestrator):**
- ❌ No LLM calls
- ❌ No input building
- ❌ No PipelineSteps writes
- ✅ Generate IDs (run_id, dossier_id)
- ✅ Write to Runs sheet (start/end)
- ✅ Call sub-scenarios
- ✅ Poll for completion
- ✅ Pass IDs only: {run_id, client_id, dossier_id, seed}

**Sub-Scenarios (Workers):**
- ✅ Fetch configs (Clients + Prompts + Previous Outputs)
- ✅ Build input JSON
- ✅ Log "running" status
- ✅ Call LLM
- ✅ Log "completed" status
- ✅ Write to Claims/Contacts/etc.
- ✅ Return output

---

### Main Pipeline Pattern (Orchestrator)

```
[1] Webhook
    Input: {client_id, seed}

[2] Generate IDs (Set Variable)
    run_id = "RUN_" + formatDate(now; "YYYYMMDDHHmmss")
    dossier_id = "DOSS_" + formatDate(now; "YYYYMMDD") + "_" + random(1000; 9999)

[3] Fetch Configs (batchGet) - OPTIONAL (for validation only)
    GET Clients + Prompts

[4] Parse Configs (JavaScript) - OPTIONAL
    Just for reference/validation

[5] Write to Runs Sheet
    POST /values/'07_runs'!A:J:append
    Values: [run_id, client_id, "running", toString(seed), "", now, "", "", "api", toString(config)]

[6] Call Search Builder Sub-Scenario
    Pass: {run_id, client_id, dossier_id, seed}

[7] Poll for Search Builder Completion
    Repeater (max 100 iterations)
    → Sleep 10 seconds
    → GET /values/'08_pipeline_steps'!A2:M5000
    → Filter: run_id={{run_id}} AND step_name='1_SEARCH_BUILDER' AND status='completed'
    → Router: If found → continue, else repeat

[8] Call Entity Research Sub-Scenario
    Pass: {run_id, client_id, dossier_id, seed}

[9] Poll for Entity Research Completion
    (same pattern)

[10] ... (repeat for all sub-scenarios)

[11] Update Runs Sheet
    PUT /values/'07_runs'!A{row}:J{row}
    Values: [..., "completed", dossier_id, now]
```

---

### Sub-Scenario Pattern (Worker)

**Example: Search Builder**

```
[1] Webhook/Start
    Input: {run_id, client_id, dossier_id, seed, hint, exclude_domains}

[2] Fetch Configs + Previous Outputs (batchGet)
    GET /values:batchGet?ranges='01_clients'!A2:M100&ranges='02_prompts'!A2:L100&ranges='08_pipeline_steps'!A2:M5000

    Returns:
    - valueRanges[0] = Clients
    - valueRanges[1] = Prompts
    - valueRanges[2] = PipelineSteps (for previous outputs)

[3] Parse + Build Input (JavaScript - COMBINED)
    See code below

[4] Write "running" Status
    POST /values:'08_pipeline_steps'!A:M:append
    Values: [step_id, run_id, prompt_id, step_name, "running", toString(input_json), "", model, "", "", now, "", ""]

[5] OpenAI Call
    System: {{3.prompts['search-builder'].template}}
    User: {{toString(3.input_json)}}
    Model: {{3.prompts['search-builder'].model}}

[6] Write "completed" Status
    POST /values:'08_pipeline_steps'!A:M:append
    Values: [step_id, run_id, prompt_id, step_name, "completed", toString(input_json), toString(output), model, tokens, runtime, started_at, now, ""]

[7] Write Claims (if produces claims)
    POST /values:'09_claims'!A:E:append
    Values: [run_id, step_id, step_name, toString(claims), now]

[8] Return Output
    Response: {{5.choices[0].message.content}}
```

---

### JavaScript: Parse + Build Input (Combined Module)

**This is the critical module. Handles Make.com wrapper + builds input.**

```javascript
// Handle Make.com's variable wrapper format
let sheetsData, clientId, seed, hint, excludeDomains, prevOutput, runId, stepNumber;

if (Array.isArray(input)) {
  input.forEach(item => {
    if (item.name === 'input') sheetsData = item.value;
    if (item.name === 'client_id') clientId = item.value;
    if (item.name === 'run_id') runId = item.value;
    if (item.name === 'seed') seed = item.value;
    if (item.name === 'hint') hint = item.value;
    if (item.name === 'exclude_domains') excludeDomains = item.value;
    if (item.name === 'step_number') stepNumber = item.value;
  });
} else {
  sheetsData = input.input || input;
  clientId = input.client_id || client_id;
  runId = input.run_id || run_id;
  seed = input.seed || seed;
  hint = input.hint || hint;
  excludeDomains = input.exclude_domains || exclude_domains;
  stepNumber = input.step_number || step_number;
}

// Parse sheets data
const clientsRows = sheetsData.valueRanges[0].values;
const promptsRows = sheetsData.valueRanges[1].values;
const pipelineRows = sheetsData.valueRanges[2]?.values || [];

// Find client
const clientRow = clientsRows.find(row => row[0] === clientId) || clientsRows[0];

// Parse ALL 31 prompts
const prompts = {};
promptsRows.forEach(row => {
  const slug = row[1];
  prompts[slug] = {
    id: row[0],
    slug: row[1],
    stage: row[2],
    step: row[3],
    template: row[4],
    model: row[5],
    produce_claims: row[6],
    context_pack: row[7],
    variables_used: row[8],
    variables_produced: row[9]
  };
});

// Find previous step output (if needed)
const previousStep = pipelineRows.find(row =>
  row[1] === runId &&
  row[3] === 'PREVIOUS_STEP_NAME' &&
  row[4] === 'completed'
);
const previousOutput = previousStep ? JSON.parse(previousStep[6]) : {};

// Build input JSON for THIS STEP (customize per step)
const inputJson = {
  current_date: new Date().toISOString().split('T')[0],
  icp_config_compressed: JSON.parse(clientRow[4]),
  research_context_compressed: JSON.parse(clientRow[8]),
  seed: seed || null,
  hint: hint || null,
  exclude_domains: excludeDomains || [],
  // Add previous output if needed:
  context_pack: previousOutput.context_pack || null
};

// Generate step_id
const stepId = `STEP_${runId}_${stepNumber.padStart(2, '0')}`;

return {
  client: {
    id: clientRow[0],
    name: clientRow[1],
    status: clientRow[2],
    icp_config: clientRow[3],
    icp_config_compressed: clientRow[4],
    industry_research: clientRow[5],
    industry_research_compressed: clientRow[6],
    research_context: clientRow[7],
    research_context_compressed: clientRow[8],
    client_specific_research: clientRow[9],
    drip_schedule: clientRow[10]
  },
  prompts: prompts,
  input_json: inputJson,
  step_id: stepId
};
```

**Key Points:**
- Handles Make.com's array wrapper (name/value pairs)
- Parses ALL 31 prompts at once
- Builds input_json specific to current step
- Can fetch previous step outputs from PipelineSteps
- Returns everything needed for rest of scenario

---

### Logging Pattern: Two Rows Per Step

**Why two rows?**
- Row 1 (running): Input logged BEFORE AI call (if AI fails, you still have it)
- Row 2 (completed): Output logged AFTER AI call

**Benefits:**
- ✅ No race conditions (just appending)
- ✅ No need to find/update specific rows
- ✅ Simple queries: `WHERE status='completed' AND step_id='...'`
- ✅ Can see exactly when step started vs completed

**Query for completed output:**
```javascript
const completedRow = pipelineRows.find(row =>
  row[1] === run_id &&
  row[3] === 'STEP_NAME' &&
  row[4] === 'completed'
);
const output = completedRow ? completedRow[6] : null;  // Column G
```

---

### Polling Pattern (in Main Pipeline)

```
[After calling sub-scenario]

[7A] Repeater
    Max iterations: 100

[7B] Sleep
    Duration: 10 seconds

[7C] GET PipelineSteps
    GET /values/'08_pipeline_steps'!A2:M5000

[7D] Filter (JavaScript)
    const rows = input.values || [];
    const completed = rows.find(row =>
      row[1] === run_id &&
      row[3] === '1_SEARCH_BUILDER' &&
      row[4] === 'completed'
    );

    return {
      found: !!completed,
      output: completed ? completed[6] : null
    };

[7E] Router
    Route 1: {{7D.found}} = true → Continue to next step
    Route 2: Else → Go back to [7B] Sleep
```

**Timeout:** Max 100 iterations × 10 seconds = ~16 minutes

---

### When to Fetch Previous Outputs

**Rule:** Only fetch PipelineSteps if your step needs output from a previous step.

**Examples:**

**Search Builder (Step 1):**
- No previous outputs needed
- Just fetch Clients + Prompts

**Entity Research (Step 3):**
- Needs Search Builder output (queries, strategy)
- Fetch: Clients + Prompts + PipelineSteps
- Filter for: step_name='1_SEARCH_BUILDER' AND status='completed'

**Claims Extraction:**
- Needs narrative from previous research step
- Fetch: Clients + Prompts + PipelineSteps
- Filter for specific step that produced narrative

**Section Writers:**
- Need merged claims
- Fetch: Clients + Prompts + Claims + MergedClaims
- Filter by run_id

---

### Common Mistakes to Avoid

❌ **Don't put LLM calls in main pipeline**
- Main pipeline only orchestrates

❌ **Don't try to update rows in place**
- Just append new rows (simpler, no race conditions)

❌ **Don't pass full config objects between scenarios**
- Only pass IDs: run_id, client_id, dossier_id, seed
- Each scenario fetches what it needs

❌ **Don't forget to handle Make.com's array wrapper**
- Variables come as `[{name: 'x', value: 'y'}]`
- Use the wrapper-handling code above

❌ **Don't read back what you just wrote in same scenario**
- Use variables directly: `{{3.input_json}}`, `{{5.output}}`
- Only read from sheets for previous step outputs

✅ **Do use the same batchGet + parse pattern everywhere**
- Standard pattern for all sub-scenarios
- Just customize the input_json building per step

---

### Performance Notes

**Batch operations are fast:**
- batchGet (Clients + Prompts + PipelineSteps) = 1 API call
- Still well under rate limits

**Polling is acceptable:**
- Deep research steps (o4-mini-deep-research) take 5-10 minutes
- Polling every 10 seconds is fine
- Make.com handles this natively

**Each scenario is independent:**
- Can test sub-scenarios in isolation
- Just pass test IDs: `{run_id: "TEST_001", client_id: "CLT_EXAMPLE_001"}`

---

## Status

**Current Phase:** Active implementation
**Sheet Status:** Configured with 14 tabs
**Prompts Status:** 31 prompts loaded
**Next:** Build Make.com scenarios using this reference

**When Complete:** Remove this skill, migrate to Supabase
