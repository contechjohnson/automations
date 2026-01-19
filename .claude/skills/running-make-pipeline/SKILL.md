---
name: running-make-pipeline
description: Trigger the Make.com V2 dossier pipeline via API. Use when running dossiers, triggering pipeline, starting a batch, generating leads, or when user mentions "run pipeline", "make dossier", "generate leads for X", "start batch", or any client name.
allowed-tools: Read, Bash, WebFetch
---

# Running the Make.com Dossier Pipeline

Triggers the V2 dossier pipeline in Make.com via API for a specific client.

## When to Use

- User says "run a dossier for [client]" or "generate leads for [client]"
- User says "start a batch" or "run the pipeline"
- User mentions a client name (Berg Group, ARCO Murray, etc.)
- User wants to test the V2 pipeline

## Quick Start

```bash
# Run pipeline for Berg Group with auto-generated batch_id
curl -X POST "https://us2.make.com/api/v2/scenarios/3843924/run" \
  -H "Authorization: Token 1355ec8a-d481-4bb8-86b5-23c084a68f96" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "client_id": "26404e38-99f6-4fcd-a3a9-01a97e6b8d8a",
      "batch_id": "BATCH_20260118_143022"
    }
  }'
```

## Client Lookup Table

When the user mentions a client, match to the correct `client_id`:

| Client Name | Contact | client_id |
|-------------|---------|-----------|
| **Aim to Thrive Nutrition** | Kali Pearson | `b69f2d69-4c0e-4bad-8cb4-cfd14e1a33c0` |
| **ARCO Murray** | Bailey Brandon | `a8fc1197-9dae-44a7-b9ed-a9f0f56bebd9` |
| **Berg Group** | Drew Lynch | `26404e38-99f6-4fcd-a3a9-01a97e6b8d8a` |
| **Columnline AI** | Jeremy Massey | `9953f9eb-0f10-4d3e-b933-a4af6a2fceb8` |
| **DCI Group** | Wade Hiner | `5b1c547c-8cf9-4ec9-b99b-95a56ec29860` |
| **Gresham Smith (DEMO)** | Charles Poat | `4ec27849-db51-4a63-b1e1-fca3b39d8a0a` |
| **H+O Structural** | H+O Structural Engineering | `0de65969-f8bc-4b0c-ad05-d28a3e2b8d77` |
| **Katz LDE** | Dan Katz | `1265fd32-1b12-4db9-b5b3-9fe3ac5b4e25` |
| **Phelan's Interiors** | Paul Phelan | `1df517d7-1b38-47c1-98ee-2b2e7f6a2c82` |
| **SH Commercial Real Estate** | Abi Reiland | `41115775-f1c3-4f63-b29f-eea4a5a5f57a` |
| **Span Construction** | Roger Acres | `fb83b832-cde7-442d-9c7e-0dbf5aca0b4a` |
| **Studer Education** | Courtney Calfee | `3e5cad11-f31c-4b49-b59d-2ecb8c51bcab` |
| **Workforce Connect** | Marty Lessmann | `5246bdce-b5d3-4b7d-9dd8-0e7c2e0c5f94` |

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

## Examples

### Example 1: Basic Run

User: "Run a dossier for Berg Group"

```bash
curl -X POST "https://us2.make.com/api/v2/scenarios/3843924/run" \
  -H "Authorization: Token 1355ec8a-d481-4bb8-86b5-23c084a68f96" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "client_id": "26404e38-99f6-4fcd-a3a9-01a97e6b8d8a",
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
      "client_id": "a8fc1197-9dae-44a7-b9ed-a9f0f56bebd9",
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
      "client_id": "fb83b832-cde7-442d-9c7e-0dbf5aca0b4a",
      "batch_id": "BATCH_TEST_001"
    }
  }'
```

---

## Monitoring

### Check Supabase for Run Status

```sql
SELECT run_id, client_id, status, started_at, completed_at
FROM v2_runs
WHERE client_id = '${CLIENT_ID}'
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
