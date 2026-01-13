# Paste-Ready Google Sheets API Calls

**For use with: Google Sheets > Make an API call (at bottom of module list)**

All calls ready to copy-paste. Just replace `{{variables}}` with your Make.com variables.

---

## Setup

**Base URL:** Already handled by Make.com (you're authenticated)

**Your Sheet ID:** Get from URL, store as `{{GOOGLE_SHEETS_ID}}`

**Content-Type:** `application/json` (already set)

---

## Read Operations

### 1. Read Multiple Sheets at Once (Batch Get)

**Use this to fetch Clients + Prompts + Claims in ONE call**

**Method:** `GET`

**URL:**
```
/v4/spreadsheets/{{GOOGLE_SHEETS_ID}}/values:batchGet?ranges=Clients!A2:M100&ranges=Prompts!A2:L100&ranges=Claims!A2:E1000
```

**Body:** (leave empty for GET)

**Returns:**
```json
{
  "spreadsheetId": "...",
  "valueRanges": [
    {
      "range": "Clients!A2:M100",
      "values": [
        ["CLT_001", "Client Name", "active", "{...}", ...]
      ]
    },
    {
      "range": "Prompts!A2:L100",
      "values": [
        ["PRM_001", "search-builder", "FIND_LEAD", ...]
      ]
    },
    {
      "range": "Claims!A2:E1000",
      "values": [
        ["RUN_001", "STEP_001", "2_SIGNAL_DISCOVERY", "[...]", "2026-01-12"]
      ]
    }
  ]
}
```

**Access in Make.com:**
```javascript
// Clients data
{{1.valueRanges[0].values}}

// Prompts data
{{1.valueRanges[1].values}}

// Claims data
{{1.valueRanges[2].values}}
```

---

### 2. Read Single Sheet

**Method:** `GET`

**URL for Clients:**
```
/v4/spreadsheets/{{GOOGLE_SHEETS_ID}}/values/Clients!A2:M100?valueRenderOption=UNFORMATTED_VALUE
```

**URL for Prompts:**
```
/v4/spreadsheets/{{GOOGLE_SHEETS_ID}}/values/Prompts!A2:L100?valueRenderOption=UNFORMATTED_VALUE
```

**URL for Claims (by run_id - filter in Make.com):**
```
/v4/spreadsheets/{{GOOGLE_SHEETS_ID}}/values/Claims!A2:E1000?valueRenderOption=UNFORMATTED_VALUE
```

**Body:** (empty)

**Returns:**
```json
{
  "range": "Clients!A2:M100",
  "values": [
    ["CLT_001", "Example Client", "active", "...", ...],
    ["CLT_002", "Another Client", "active", "...", ...]
  ]
}
```

**Access:**
```javascript
// All rows
{{1.values}}

// First row
{{first(1.values)}}

// Filter by client_id (column A = index 0)
{{filter(1.values; "0"; client_id)}}
```

---

### 3. Read All Sheets You Need for a Scenario

**Example: Enrich Lead scenario needs Clients, Prompts, Claims, ContextPacks**

**Method:** `GET`

**URL:**
```
/v4/spreadsheets/{{GOOGLE_SHEETS_ID}}/values:batchGet?ranges=Clients!A2:M100&ranges=Prompts!A2:L100&ranges=Claims!A2:E1000&ranges=ContextPacks!A2:G1000
```

**Body:** (empty)

**Returns:** 4 valueRanges arrays

---

## Write Operations

### 4. Append Row to Single Sheet

**Method:** `POST`

**URL for Runs:**
```
/v4/spreadsheets/{{GOOGLE_SHEETS_ID}}/values/Runs!A:J:append?valueInputOption=USER_ENTERED&insertDataOption=INSERT_ROWS
```

**URL for PipelineSteps:**
```
/v4/spreadsheets/{{GOOGLE_SHEETS_ID}}/values/PipelineSteps!A:M:append?valueInputOption=USER_ENTERED&insertDataOption=INSERT_ROWS
```

**URL for Claims:**
```
/v4/spreadsheets/{{GOOGLE_SHEETS_ID}}/values/Claims!A:E:append?valueInputOption=USER_ENTERED&insertDataOption=INSERT_ROWS
```

**Body (example for Claims):**
```json
{
  "values": [
    [
      "{{run_id}}",
      "{{step_id}}",
      "2_SIGNAL_DISCOVERY",
      "{{toString(claims_array)}}",
      "{{formatDate(now; 'YYYY-MM-DD HH:mm:ss')}}"
    ]
  ]
}
```

**Body (example for PipelineSteps with input/output):**
```json
{
  "values": [
    [
      "{{step_id}}",
      "{{run_id}}",
      "PRM_002",
      "2_SIGNAL_DISCOVERY",
      "completed",
      "{{toString(input_object)}}",
      "{{toString(output_object)}}",
      "gpt-4.1",
      "{{tokens_used}}",
      "{{runtime_seconds}}",
      "{{formatDate(step_start; 'YYYY-MM-DD HH:mm:ss')}}",
      "{{formatDate(now; 'YYYY-MM-DD HH:mm:ss')}}",
      ""
    ]
  ]
}
```

**Returns:**
```json
{
  "spreadsheetId": "...",
  "tableRange": "Claims!A2:E1000",
  "updates": {
    "updatedRange": "Claims!A1001:E1001",
    "updatedRows": 1,
    "updatedColumns": 5,
    "updatedCells": 5
  }
}
```

---

### 5. Append Multiple Rows at Once (Batch Append)

**Use this to write multiple contacts or sections at once**

**Method:** `POST`

**URL:**
```
/v4/spreadsheets/{{GOOGLE_SHEETS_ID}}/values/Contacts!A:AG:append?valueInputOption=USER_ENTERED&insertDataOption=INSERT_ROWS
```

**Body (multiple contacts):**
```json
{
  "values": [
    [
      "CONT_001",
      "{{dossier_id}}",
      "{{run_id}}",
      "John Doe",
      "John",
      "Doe",
      "VP Engineering",
      "john@example.com",
      "555-1234",
      "https://linkedin.com/in/johndoe",
      "500+",
      "John is a seasoned engineering leader...",
      "36",
      "[\"Google\", \"Apple\"]",
      "Stanford CS",
      "[\"Python\", \"Leadership\"]",
      "Recently posted about AI...",
      "true",
      "linkedin",
      "primary",
      "Background in enterprise software...",
      "Key decision maker for tech stack...",
      "Led similar migrations...",
      "[\"Built data platform\"]",
      "10 years at tech companies",
      "Found via executive search",
      "Hi John, noticed your...",
      "Reaching out about...",
      "Client-specific: Your team...",
      "Custom client message...",
      "HIGH",
      "{{formatDate(now; 'YYYY-MM-DD HH:mm:ss')}}"
    ],
    [
      "CONT_002",
      "{{dossier_id}}",
      "{{run_id}}",
      "Jane Smith",
      ...
    ]
  ]
}
```

---

### 6. Write to Multiple Sheets at Once (Batch Update)

**Use this to write PipelineSteps + Claims + ContextPacks in ONE call**

**Method:** `POST`

**URL:**
```
/v4/spreadsheets/{{GOOGLE_SHEETS_ID}}/values:batchUpdate
```

**Body:**
```json
{
  "valueInputOption": "USER_ENTERED",
  "data": [
    {
      "range": "PipelineSteps!A:M",
      "values": [
        [
          "{{step_id}}",
          "{{run_id}}",
          "PRM_002",
          "2_SIGNAL_DISCOVERY",
          "completed",
          "{{toString(input)}}",
          "{{toString(output)}}",
          "gpt-4.1",
          "1250",
          "12.5",
          "{{formatDate(start; 'YYYY-MM-DD HH:mm:ss')}}",
          "{{formatDate(now; 'YYYY-MM-DD HH:mm:ss')}}",
          ""
        ]
      ]
    },
    {
      "range": "Claims!A:E",
      "values": [
        [
          "{{run_id}}",
          "{{step_id}}",
          "2_SIGNAL_DISCOVERY",
          "{{toString(claims)}}",
          "{{formatDate(now; 'YYYY-MM-DD HH:mm:ss')}}"
        ]
      ]
    },
    {
      "range": "ContextPacks!A:G",
      "values": [
        [
          "PACK_{{run_id}}_SIGNAL",
          "{{run_id}}",
          "signal_to_entity",
          "{{toString(context_pack)}}",
          "{{step_id}}",
          "[]",
          "{{formatDate(now; 'YYYY-MM-DD HH:mm:ss')}}"
        ]
      ]
    }
  ]
}
```

**Returns:**
```json
{
  "spreadsheetId": "...",
  "totalUpdatedRows": 3,
  "totalUpdatedColumns": 25,
  "totalUpdatedCells": 25,
  "responses": [
    {
      "updatedRange": "PipelineSteps!A1001:M1001",
      "updatedRows": 1
    },
    {
      "updatedRange": "Claims!A501:E501",
      "updatedRows": 1
    },
    {
      "updatedRange": "ContextPacks!A101:G101",
      "updatedRows": 1
    }
  ]
}
```

**This writes 3 sheets in 1 API call!**

---

## Complete Scenario Examples

### Scenario 1: Search & Signal Discovery

**Read (Batch Get - 1 call):**

**Method:** `GET`

**URL:**
```
/v4/spreadsheets/{{GOOGLE_SHEETS_ID}}/values:batchGet?ranges=Clients!A2:M100&ranges=Prompts!A2:L100
```

**Filter in Make.com:**
```javascript
// Get client
{{first(filter(1.valueRanges[0].values; "0"; client_id))}}

// Get search-builder prompt
{{first(filter(1.valueRanges[1].values; "1"; "search-builder"))}}

// Get signal-discovery prompt
{{first(filter(1.valueRanges[1].values; "1"; "signal-discovery"))}}
```

**Write (Batch Update - 1 call):**

**Method:** `POST`

**URL:**
```
/v4/spreadsheets/{{GOOGLE_SHEETS_ID}}/values:batchUpdate
```

**Body:**
```json
{
  "valueInputOption": "USER_ENTERED",
  "data": [
    {
      "range": "PipelineSteps!A:M",
      "values": [
        ["STEP_{{run_id}}_01", "{{run_id}}", "PRM_001", "1_SEARCH_BUILDER", "completed", "{{toString(search_input)}}", "{{toString(search_output)}}", "gpt-4.1", "500", "3.2", "{{start}}", "{{now}}", ""],
        ["STEP_{{run_id}}_02", "{{run_id}}", "PRM_002", "2_SIGNAL_DISCOVERY", "completed", "{{toString(signal_input)}}", "{{toString(signal_output)}}", "o4-mini-deep-research", "2500", "45.0", "{{start}}", "{{now}}", ""]
      ]
    },
    {
      "range": "Claims!A:E",
      "values": [
        ["{{run_id}}", "STEP_{{run_id}}_02", "2_SIGNAL_DISCOVERY", "{{toString(claims)}}", "{{now}}"]
      ]
    },
    {
      "range": "ContextPacks!A:G",
      "values": [
        ["PACK_{{run_id}}_SIGNAL", "{{run_id}}", "signal_to_entity", "{{toString(context_pack)}}", "STEP_{{run_id}}_02", "[]", "{{now}}"]
      ]
    }
  ]
}
```

**Total: 2 API calls (1 read, 1 write)**

---

### Scenario 2: Enrich Lead

**Read (Batch Get - 1 call):**

**Method:** `GET`

**URL:**
```
/v4/spreadsheets/{{GOOGLE_SHEETS_ID}}/values:batchGet?ranges=Clients!A2:M100&ranges=Prompts!A2:L100&ranges=Claims!A2:E1000&ranges=ContextPacks!A2:G1000
```

**Filter:**
```javascript
// Client (from valueRanges[0])
{{first(filter(1.valueRanges[0].values; "0"; client_id))}}

// Prompt (from valueRanges[1])
{{first(filter(1.valueRanges[1].values; "1"; "enrich-lead"))}}

// All claims for this run (from valueRanges[2])
{{filter(1.valueRanges[2].values; "0"; run_id)}}

// Context pack (from valueRanges[3])
{{first(filter(1.valueRanges[3].values; "1"; run_id))}}
```

**Write (Batch Update - 1 call):**

**Method:** `POST`

**URL:**
```
/v4/spreadsheets/{{GOOGLE_SHEETS_ID}}/values:batchUpdate
```

**Body:**
```json
{
  "valueInputOption": "USER_ENTERED",
  "data": [
    {
      "range": "PipelineSteps!A:M",
      "values": [
        ["STEP_{{run_id}}_05", "{{run_id}}", "PRM_006", "5B_ENRICH_LEAD", "completed", "{{toString(input)}}", "{{toString(output)}}", "gpt-4.1", "1800", "15.3", "{{start}}", "{{now}}", ""]
      ]
    },
    {
      "range": "Claims!A:E",
      "values": [
        ["{{run_id}}", "STEP_{{run_id}}_05", "5B_ENRICH_LEAD", "{{toString(claims)}}", "{{now}}"]
      ]
    }
  ]
}
```

**Total: 2 API calls (1 read, 1 write)**

---

### Scenario 3: Enrich Contacts (Bridge with 10 Parallel Sub-Scenarios)

**Bridge Scenario Read (1 call):**

**Method:** `GET`

**URL:**
```
/v4/spreadsheets/{{GOOGLE_SHEETS_ID}}/values:batchGet?ranges=Clients!A2:M100&ranges=Prompts!A2:L100&ranges=Claims!A2:E1000
```

**Bridge Write (1 call):**

**Method:** `POST`

**URL:**
```
/v4/spreadsheets/{{GOOGLE_SHEETS_ID}}/values/PipelineSteps!A:M:append?valueInputOption=USER_ENTERED
```

**Body:**
```json
{
  "values": [
    ["STEP_{{run_id}}_09", "{{run_id}}", "PRM_009", "6_ENRICH_CONTACTS", "completed", "{{toString(input)}}", "{{toString(output)}}", "gpt-4.1", "1200", "8.5", "{{start}}", "{{now}}", ""]
  ]
}
```

**Each Sub-Scenario (×10) Read (1 call per contact):**

**Method:** `GET`

**URL:**
```
/v4/spreadsheets/{{GOOGLE_SHEETS_ID}}/values:batchGet?ranges=Clients!A2:M100&ranges=Prompts!A2:L100&ranges=Claims!A2:E1000&ranges=ContextPacks!A2:G1000
```

**Each Sub-Scenario Write (1 call per contact):**

**Method:** `POST`

**URL:**
```
/v4/spreadsheets/{{GOOGLE_SHEETS_ID}}/values:batchUpdate
```

**Body:**
```json
{
  "valueInputOption": "USER_ENTERED",
  "data": [
    {
      "range": "PipelineSteps!A:M",
      "values": [
        ["STEP_{{run_id}}_09_{{contact_index}}", "{{run_id}}", "PRM_XXX", "6.2_ENRICH_CONTACT", "completed", "{{toString(input)}}", "{{toString(output)}}", "gpt-4.1", "800", "12.0", "{{start}}", "{{now}}", ""]
      ]
    },
    {
      "range": "Contacts!A:AG",
      "values": [
        [
          "CONT_{{random}}",
          "{{dossier_id}}",
          "{{run_id}}",
          "{{contact.name}}",
          "{{contact.first_name}}",
          "{{contact.last_name}}",
          "{{contact.title}}",
          "{{contact.email}}",
          "{{contact.phone}}",
          "{{contact.linkedin_url}}",
          "{{contact.linkedin_connections}}",
          "{{contact.bio_paragraph}}",
          "{{contact.tenure_months}}",
          "{{toString(contact.previous_companies)}}",
          "{{contact.education}}",
          "{{toString(contact.skills)}}",
          "{{contact.recent_post_quote}}",
          "{{contact.is_primary}}",
          "{{contact.source}}",
          "{{contact.tier}}",
          "{{contact.bio_summary}}",
          "{{contact.why_they_matter}}",
          "{{contact.signal_relevance}}",
          "{{toString(contact.interesting_facts)}}",
          "{{contact.linkedin_summary}}",
          "{{contact.web_summary}}",
          "{{contact.email_copy}}",
          "{{contact.linkedin_copy}}",
          "{{contact.client_email_copy}}",
          "{{contact.client_linkedin_copy}}",
          "{{contact.confidence}}",
          "{{now}}"
        ]
      ]
    }
  ]
}
```

**Total for Enrich Contacts: 22 API calls (1+1 bridge, 10×2 subs)**

---

### Scenario 4: Section Writers (Bridge with 7 Parallel Writers)

**Bridge Read (1 call):**

**Method:** `GET`

**URL:**
```
/v4/spreadsheets/{{GOOGLE_SHEETS_ID}}/values:batchGet?ranges=Clients!A2:M100&ranges=Prompts!A2:L100&ranges=MergedClaims!A2:E1000&ranges=Contacts!A2:AG1000
```

**Each Writer Read (if needed - or use bridge data):**

Can skip if bridge passes data directly

**Each Writer Write (1 call per section):**

**Method:** `POST`

**URL:**
```
/v4/spreadsheets/{{GOOGLE_SHEETS_ID}}/values:batchUpdate
```

**Body:**
```json
{
  "valueInputOption": "USER_ENTERED",
  "data": [
    {
      "range": "PipelineSteps!A:M",
      "values": [
        ["STEP_{{run_id}}_INTRO", "{{run_id}}", "PRM_014", "SECTION_WRITER_INTRO", "completed", "{{toString(input)}}", "{{toString(output)}}", "gpt-4.1", "600", "5.2", "{{start}}", "{{now}}", ""]
      ]
    },
    {
      "range": "Sections!A:I",
      "values": [
        ["SECT_{{run_id}}_INTRO", "{{run_id}}", "INTRO", "{{toString(section_data)}}", "[]", "STEP_{{run_id}}_INTRO", "complete", "{{toString(variables_produced)}}", "find_lead", "{{now}}"]
      ]
    }
  ]
}
```

**Total for Section Writers: 8 API calls (1 read, 7 writes)**

---

### Scenario 5: Final Assembly

**Read (1 call):**

**Method:** `GET`

**URL:**
```
/v4/spreadsheets/{{GOOGLE_SHEETS_ID}}/values/Sections!A2:I1000?valueRenderOption=UNFORMATTED_VALUE
```

**Filter:**
```javascript
// Get all sections for this run
{{filter(1.values; "1"; run_id)}}
```

**Write (1 call):**

**Method:** `POST`

**URL:**
```
/v4/spreadsheets/{{GOOGLE_SHEETS_ID}}/values:batchUpdate
```

**Body:**
```json
{
  "valueInputOption": "USER_ENTERED",
  "data": [
    {
      "range": "Dossiers!A:L",
      "values": [
        [
          "{{dossier_id}}",
          "{{run_id}}",
          "{{client_id}}",
          "{{company_name}}",
          "{{lead_score}}",
          "{{timing_urgency}}",
          "{{primary_signal}}",
          "{{toString(find_lead_json)}}",
          "{{toString(enrich_lead_json)}}",
          "{{toString(copy_json)}}",
          "{{toString(insight_json)}}",
          "{{toString(media_json)}}",
          "complete",
          "{{now}}",
          ""
        ]
      ]
    },
    {
      "range": "Runs!A:J",
      "values": [
        [
          "{{run_id}}",
          "{{client_id}}",
          "completed",
          "{{toString(seed_data)}}",
          "{{dossier_id}}",
          "{{started_at}}",
          "{{now}}",
          "",
          "api",
          "{{toString(config_snapshot)}}"
        ]
      ]
    }
  ]
}
```

**Total: 2 API calls (1 read, 1 write)**

---

## Summary: API Calls per Full Dossier

| Scenario | Reads | Writes | Total |
|----------|-------|--------|-------|
| Search & Signal | 1 | 1 | 2 |
| Enrich Lead | 1 | 1 | 2 |
| Enrich Opportunity | 1 | 1 | 2 |
| Client Specific | 1 | 1 | 2 |
| Enrich Contacts (10 contacts) | 11 | 11 | 22 |
| Copy | 1 | 1 | 2 |
| Insight | 1 | 1 | 2 |
| Media | 1 | 1 | 2 |
| Section Writers (7 sections) | 1 | 7 | 8 |
| Final Assembly | 1 | 1 | 2 |
| **TOTAL** | **20** | **26** | **46** |

**Much better than 132!** By using batch operations, we cut API calls by ~65%.

---

## Query Parameters Reference

### valueInputOption

**Use in append/update URLs:**

- `USER_ENTERED` - Parse dates, formulas (recommended)
- `RAW` - Store exactly as is

**Example:**
```
?valueInputOption=USER_ENTERED
```

### valueRenderOption

**Use in read URLs:**

- `FORMATTED_VALUE` - Get formatted strings
- `UNFORMATTED_VALUE` - Get raw values (recommended for JSON)
- `FORMULA` - Get formulas

**Example:**
```
?valueRenderOption=UNFORMATTED_VALUE
```

### insertDataOption

**Use in append URLs:**

- `INSERT_ROWS` - Insert new rows (recommended)
- `OVERWRITE` - Overwrite existing

**Example:**
```
?insertDataOption=INSERT_ROWS
```

---

## Error Handling

**If API call fails, check:**

1. Sheet ID correct? `{{GOOGLE_SHEETS_ID}}`
2. Range valid? `Clients!A2:M100` (case-sensitive)
3. JSON valid? Use `{{toString()}}` for objects
4. Authentication working? (Make.com handles this)

**Common errors:**

- `"Range not found"` → Sheet name typo
- `"Unable to parse range"` → Check A1 notation
- `"Values must be an array"` → Wrap in `[...]`

---

## Next Steps

**For each scenario:**

1. Copy the batch GET URL
2. Paste into "Make an API call" module
3. Run and inspect output structure
4. Filter/map data in next modules
5. Copy the batch UPDATE body
6. Paste into write module
7. Test!

**You now have copy-paste ready API calls for the full pipeline.**
