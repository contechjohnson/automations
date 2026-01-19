---
name: running-make-pipeline
description: Trigger Make.com V2 dossier pipeline or enrich single contacts via API. Use when running dossiers, triggering pipeline, starting a batch, generating leads, adding contacts to existing dossier, or when user mentions "run pipeline", "make dossier", "generate leads for X", "start batch", "add contact", "enrich contact", or any client name.
allowed-tools: Read, Bash, WebFetch
---

# Running the Make.com Dossier Pipeline

Triggers the V2 dossier pipeline in Make.com via API for a specific client. Also supports adding/enriching single contacts to existing dossiers.

## When to Use

- User says "run a dossier for [client]" or "generate leads for [client]"
- User says "start a batch" or "run the pipeline"
- User mentions a client name (Berg Group, ARCO Murray, etc.)
- User wants to test the V2 pipeline
- User says "add a contact to the dossier" or "enrich this contact"
- User discovers new contacts through research that should be added to an existing dossier

## Quick Start

```bash
# Run pipeline for Berg Group with auto-generated batch_id
curl -X POST "https://us2.make.com/api/v2/scenarios/3843924/run" \
  -H "Authorization: Token 1355ec8a-d481-4bb8-86b5-23c084a68f96" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "client_id": "CLT_DREW_LYNCH_001",
      "batch_id": "BATCH_20260118_143022"
    }
  }'
```

## Client Lookup Table

When the user mentions a client, use the **V2 client_id** (TEXT format, e.g., `CLT_WADE_HINER_001`):

| Client Name | Contact | V2 client_id |
|-------------|---------|--------------|
| **Aim to Thrive Nutrition** | Kali Pearson | `CLT_KALI_PEARSON_001` |
| **ARCO Murray** | Bailey Brandon | `CLT_BAILEY_BRANDON_001` |
| **Berg Group** | Drew Lynch | `CLT_DREW_LYNCH_001` |
| **Columnline AI** | Jeremy Massey | `CLT_JEREMY_MASSEY_001` |
| **DCI Group** | Wade Hiner | `CLT_WADE_HINER_001` |
| **Gresham Smith (DEMO)** | Charles Poat | `CLT_CHARLES_POAT_001` |
| **H+O Structural** | Rens Hayes | `CLT_RENS_HAYES_001` |
| **Katz LDE** | Dan Katz | `CLT_DAN_KATZ_001` |
| **Phelan's Interiors** | Paul Phelan | `CLT_PAUL_PHELAN_001` |
| **SH Commercial Real Estate** | Abi Reiland | `CLT_ABI_REILAND_001` |
| **Span Construction** | Roger Acres | `CLT_ROGER_ACRES_001` |
| **Studer Education (DEMO)** | Marty Lessmann | `CLT_MARTY_LESSMANN_001` |
| **Workforce Connect** | Marty Lessmann | `CLT_MARTY_LESSMANN_002` |

> **Note:** These are V2 client_ids from the `v2_clients` table, NOT the production UUID client IDs.

### Semantic Matching

The user may say things like:
- "Berg" → Berg Group
- "ARCO" → ARCO Murray
- "Drew's company" → Berg Group (Drew Lynch)
- "the nutrition client" → Aim to Thrive Nutrition
- "Gresham" → Gresham Smith (DEMO)
- "SH" or "SH Commercial" → SH Commercial Real Estate

## Process

### Step 1: Identify the Client

Match user's request to a client in the lookup table above. If ambiguous, ask for clarification.

### Step 2: Generate Batch ID (if not provided)

Format: `BATCH_YYYYMMDD_HHMMSS`

```python
from datetime import datetime
batch_id = f"BATCH_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
```

### Step 3: Prepare Seed Data (optional)

If the user provides seed data (company names, domains, signals), structure it as:

```json
{
  "seeds": [
    {"company_name": "Example Corp", "domain": "example.com"},
    {"company_name": "Another Inc", "signal": "New data center project"}
  ]
}
```

### Step 4: Trigger the Pipeline

```bash
curl -X POST "https://us2.make.com/api/v2/scenarios/${SCENARIO_ID}/run" \
  -H "Authorization: Token 1355ec8a-d481-4bb8-86b5-23c084a68f96" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "client_id": "${CLIENT_ID}",
      "batch_id": "${BATCH_ID}",
      "seed_data": ${SEED_JSON_OR_NULL}
    }
  }'
```

## Configuration

### Make.com API Details

| Setting | Value |
|---------|-------|
| **Zone** | `us2.make.com` |
| **Auth Token** | `1355ec8a-d481-4bb8-86b5-23c084a68f96` |
| **Scenario ID** | `3843924` |
| **API Endpoint** | `POST https://us2.make.com/api/v2/scenarios/{scenarioId}/run` |

### Scenario URL

Main pipeline: https://us2.make.com/58867/scenarios/3843924/edit

## API Response

Successful trigger returns:

```json
{
  "executionId": "abc123",
  "status": "accepted"
}
```

Check execution status:

```bash
curl "https://us2.make.com/api/v2/scenarios/${SCENARIO_ID}/executions/${EXECUTION_ID}" \
  -H "Authorization: Token 1355ec8a-d481-4bb8-86b5-23c084a68f96"
```

### Execution Status Values

| Status | Meaning |
|--------|---------|
| `SUCCESS` | Completed successfully |
| `WARNING` | Completed but with warnings (e.g., empty data, filtered results) |
| `FAILED` | Failed with error |
| `RUNNING` | Still executing |
| `WAITING` | Queued, waiting to start |

### How to Check on Running Scenarios

**Option 1: Make.com Dashboard**
Open the scenario in Make.com to see real-time execution:
https://us2.make.com/58867/scenarios/3843924/edit

Click "History" tab to see past executions with full details.

**Option 2: API Status Check**
```bash
# Check specific execution
curl -s "https://us2.make.com/api/v2/scenarios/3843924/executions/${EXECUTION_ID}" \
  -H "Authorization: Token 1355ec8a-d481-4bb8-86b5-23c084a68f96"
```

**Option 3: Supabase v2_runs Table**
Query the `v2_runs` table to see run status with detailed step-by-step logs:
```sql
SELECT run_id, status, current_step, started_at, error_message
FROM v2_runs
WHERE client_id = 'CLT_WADE_HINER_001'
ORDER BY started_at DESC
LIMIT 5;
```

**Option 4: Quick Batch Status Check**
To check multiple executions at once, chain curl calls with a brief pause to avoid rate limits:

```bash
# Check multiple executions (add sleep between batches to avoid rate limits)
echo "=== Client 1 ===" && \
curl -s 'https://us2.make.com/api/v2/scenarios/3843924/executions/EXEC_ID_1' -H 'Authorization: Token 1355ec8a-d481-4bb8-86b5-23c084a68f96' && echo "" && \
curl -s 'https://us2.make.com/api/v2/scenarios/3843924/executions/EXEC_ID_2' -H 'Authorization: Token 1355ec8a-d481-4bb8-86b5-23c084a68f96' && echo "" && \
curl -s 'https://us2.make.com/api/v2/scenarios/3843924/executions/EXEC_ID_3' -H 'Authorization: Token 1355ec8a-d481-4bb8-86b5-23c084a68f96'
```

> **Rate Limit Note:** Make.com API has request limits. If you see "Requests limit for organization exceeded", wait 2-3 seconds and retry. This only affects status checks - your triggered pipelines continue running unaffected.

## Examples

### Example 1: Basic Run

User: "Run a dossier for Berg Group"

```bash
curl -X POST "https://us2.make.com/api/v2/scenarios/3843924/run" \
  -H "Authorization: Token 1355ec8a-d481-4bb8-86b5-23c084a68f96" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "client_id": "CLT_DREW_LYNCH_001",
      "batch_id": "BATCH_20260118_143022"
    }
  }'
```

### Example 2: With Seed Data

User: "Generate leads for ARCO Murray - look at Tesla's new factory in Austin"

```bash
curl -X POST "https://us2.make.com/api/v2/scenarios/3843924/run" \
  -H "Authorization: Token 1355ec8a-d481-4bb8-86b5-23c084a68f96" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "client_id": "CLT_BAILEY_BRANDON_001",
      "batch_id": "BATCH_20260118_143500",
      "seed_data": {
        "seeds": [
          {"company_name": "Tesla", "signal": "New factory in Austin"}
        ]
      }
    }
  }'
```

### Example 3: With Specific Batch ID

User: "Run batch BATCH_TEST_001 for Span Construction"

```bash
curl -X POST "https://us2.make.com/api/v2/scenarios/3843924/run" \
  -H "Authorization: Token 1355ec8a-d481-4bb8-86b5-23c084a68f96" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "client_id": "CLT_ROGER_ACRES_001",
      "batch_id": "BATCH_TEST_001"
    }
  }'
```

---

## Single Contact Enrichment

Use this to add or enrich individual contacts after a dossier pipeline has already run. This is useful when:
- You discover additional contacts during research (e.g., GC contacts for a data center project)
- A contact was missed during initial contact discovery
- You want to add a specific person to an existing dossier

### Scenario Details

| Setting | Value |
|---------|-------|
| **Scenario ID** | `3872773` |
| **Scenario URL** | https://us2.make.com/58867/scenarios/3872773/edit |

### Required Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `run_id` | text | The V2 run ID (e.g., `RUN_20260119_025011`) |
| `client_id` | text | The V2 client_id (e.g., `CLT_ROGER_ACRES_001`) |
| `dossier_id` | text | The V2 dossier ID (e.g., `DOSS_20260119_3998`) |
| `contact` | text | JSON string with contact info |

### Contact JSON Format

```json
{
  "name": "Aaron Martens",
  "title": "VP & Co-Business Unit Leader, Mission Critical",
  "company": "HITT Contracting",
  "linkedin_url": "https://linkedin.com/in/aaronmartens",
  "relevance": "HITT is QTS's primary GC partner, delivered 7M+ SF of data centers"
}
```

### Example: Add a Single Contact

```bash
curl -X POST "https://us2.make.com/api/v2/scenarios/3872773/run" \
  -H "Authorization: Token 1355ec8a-d481-4bb8-86b5-23c084a68f96" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "run_id": "RUN_20260119_025011",
      "client_id": "CLT_ROGER_ACRES_001",
      "dossier_id": "DOSS_20260119_3998",
      "contact": "{\"name\": \"Aaron Martens\", \"title\": \"VP & Co-Business Unit Leader, Mission Critical\", \"company\": \"HITT Contracting\", \"linkedin_url\": \"https://linkedin.com/in/aaronmartens\", \"relevance\": \"HITT is QTS primary GC partner for data centers\"}"
    }
  }'
```

### Example: Add Multiple Contacts (run sequentially)

When adding multiple contacts, trigger each one separately:

```bash
# Contact 1
curl -X POST "https://us2.make.com/api/v2/scenarios/3872773/run" \
  -H "Authorization: Token 1355ec8a-d481-4bb8-86b5-23c084a68f96" \
  -H "Content-Type: application/json" \
  -d '{"data": {"run_id": "RUN_XXX", "client_id": "CLT_XXX", "dossier_id": "DOSS_XXX", "contact": "{...}"}}'

# Contact 2
curl -X POST "https://us2.make.com/api/v2/scenarios/3872773/run" \
  -H "Authorization: Token 1355ec8a-d481-4bb8-86b5-23c084a68f96" \
  -H "Content-Type: application/json" \
  -d '{"data": {"run_id": "RUN_XXX", "client_id": "CLT_XXX", "dossier_id": "DOSS_XXX", "contact": "{...}"}}'
```

### When to Use Single Contact Enrichment

1. **Post-pipeline discovery** - Found a key person through deeper research
2. **GC/subcontractor contacts** - Adding general contractor leadership for construction projects
3. **Network connections** - Adding warm paths discovered after initial run
4. **Missed contacts** - Contact discovery missed someone important

---

## Step-Level Scenarios (Rerun/Fix Broken Dossiers)

Each pipeline step has its own Make.com scenario. Use these to rerun specific steps when:
- A step failed or timed out
- Deep research polling didn't complete in time
- You need to regenerate just one part of a dossier

### Scenario IDs by Step

| Step | Scenario ID | Scenario URL | Description |
|------|-------------|--------------|-------------|
| **Main Pipeline** | `3843924` | [Edit](https://us2.make.com/58867/scenarios/3843924/edit) | Full dossier generation |
| **Search & Signal** | `3870955` | [Edit](https://us2.make.com/58867/scenarios/3870955/edit) | Find leads, discover signals |
| **Entity Research** | `3872107` | [Edit](https://us2.make.com/58867/scenarios/3872107/edit) | Deep company research |
| **Enrich Lead** | `3870998` | [Edit](https://us2.make.com/58867/scenarios/3870998/edit) | Enrich lead data |
| **Enrich Opportunity** | `3871030` | [Edit](https://us2.make.com/58867/scenarios/3871030/edit) | Opportunity analysis |
| **Client Specific** | `3871037` | [Edit](https://us2.make.com/58867/scenarios/3871037/edit) | Client-specific research |
| **Contact Discovery** | `3925759` | [Edit](https://us2.make.com/58867/scenarios/3925759/edit) | Find contacts at company |
| **Enrich Contacts** | `3871051` | [Edit](https://us2.make.com/58867/scenarios/3871051/edit) | Enrich all contacts (batch) |
| **Enrich Contact** | `3872773` | [Edit](https://us2.make.com/58867/scenarios/3872773/edit) | Enrich single contact |
| **Insight** | `3871066` | [Edit](https://us2.make.com/58867/scenarios/3871066/edit) | Generate insights |
| **Media** | `3871140` | [Edit](https://us2.make.com/58867/scenarios/3871140/edit) | Find media/images |
| **Dossier Plan** | `3871141` | [Edit](https://us2.make.com/58867/scenarios/3871141/edit) | Plan dossier structure |

### Check Step Execution Status

```bash
# Check status of any step scenario execution
SCENARIO_ID="3872107"  # e.g., Entity Research
EXECUTION_ID="abc123"
curl -s "https://us2.make.com/api/v2/scenarios/${SCENARIO_ID}/executions/${EXECUTION_ID}" \
  -H "Authorization: Token 1355ec8a-d481-4bb8-86b5-23c084a68f96"
```

### Rerun a Specific Step

To rerun a step, you need to pass the appropriate context (run_id, dossier_id, client_id, etc.). Check the scenario in Make.com to see required input parameters.

```bash
# Example: Rerun Entity Research for a specific dossier
curl -X POST "https://us2.make.com/api/v2/scenarios/3872107/run" \
  -H "Authorization: Token 1355ec8a-d481-4bb8-86b5-23c084a68f96" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "run_id": "RUN_20260119_XXXX",
      "client_id": "CLT_XXX_001",
      "dossier_id": "DOSS_20260119_XXXX"
    }
  }'
```

### Common Fix Scenarios

**1. Deep Research Timeout**
If entity research or other deep research steps time out (polling didn't complete):
- Check v2_runs for the stuck run
- Rerun the Entity Research scenario (3872107) with the run context

**2. Missing Contacts**
If contact discovery found no contacts or missed key people:
- Use Contact Discovery (3925759) to rerun discovery
- Or use Enrich Contact (3872773) to add specific contacts manually

**3. Incomplete Dossier**
If dossier is stuck in "running" status:
- Check which step failed in Make.com execution history
- Rerun that specific step scenario

---

## Monitoring

### Check Supabase for Run Status

```sql
-- Example: Check runs for DCI Group
SELECT run_id, client_id, status, started_at, completed_at
FROM v2_runs
WHERE client_id = 'CLT_WADE_HINER_001'
ORDER BY started_at DESC
LIMIT 5;
```

### View Pipeline Logs

```sql
SELECT step_name, status, completed_at, tokens_used
FROM v2_pipeline_logs
WHERE run_id = '${RUN_ID}'
ORDER BY completed_at;
```

---

## Resources

### Files Referenced by This Skill

| Resource | Path |
|----------|------|
| V2 Routes | `api/columnline/routes.py` |
| Repository | `api/columnline/repository.py` |
| Rendered Schema | `COLUMNLINE_AI_APP_V1/execution/dossier/lib/schemas/rendered.ts` |

### Related Skills

| Skill | Purpose |
|-------|---------|
| `make_migration` | Build/edit the V2 pipeline code |
| `querying-database` | Check logs and run status |

---

## Self-Annealing

**MANDATORY:** After any failure or unexpected behavior:
1. Document in LEARNINGS.md with date
2. Update this skill if process needs change
3. Add new clients to the lookup table when onboarded

See `LEARNINGS.md` for known issues and fixes.
