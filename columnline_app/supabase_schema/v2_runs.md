# v2_runs

**Layer:** Execution (one per dossier generation)
**Purpose:** Track pipeline run metadata and status.

---

## Columns

| Column | Type | Description |
|--------|------|-------------|
| `run_id` | TEXT (PK) | Timestamp-based ID (e.g., `RUN_20260115_181206`) |
| `client_id` | TEXT (FK) | Reference to `v2_clients.client_id` |
| `dossier_id` | TEXT | Associated dossier ID (generated at run start) |
| `status` | TEXT | `pending`, `running`, `completed`, `failed` |
| `seed_data` | JSONB | Initial trigger data (lead info, signal URL, etc.) |
| `total_tokens` | INTEGER | Sum of all tokens across all steps (updated incrementally) |
| `total_cost` | NUMERIC(10,4) | Sum of estimated costs across all steps in USD |
| `started_at` | TIMESTAMP | Pipeline start time |
| `completed_at` | TIMESTAMP | Pipeline completion time |
| `error_message` | TEXT | Error details if failed |
| `triggered_by` | TEXT | `make.com`, `api`, `manual` |
| `config_snapshot` | JSONB | Snapshot of client config at run time |

---

## ID Generation

IDs are generated at the START of the pipeline (in Make.com):

```javascript
// run_id format
run_id = "RUN_" + formatDate(now, "YYYYMMDD_HHmmss")
// Example: RUN_20260115_181206

// dossier_id format
dossier_id = "DOSS_" + formatDate(now, "YYYYMMDD") + "_" + random(1000, 9999)
// Example: DOSS_20260115_4523
```

---

## Status Flow

```
pending → running → completed
                 ↘ failed
```

---

## Usage

**Create:** Make.com main pipeline start
**Update:** Each step completion updates status + costs
**Read:** Status checks, debugging, analytics, cost analysis

```python
# Example: Create run
run = repo.create_run({
    "run_id": "RUN_20260115_181206",
    "client_id": "CLT_ROGER_ACRES_001",
    "dossier_id": "DOSS_20260115_4523",
    "status": "running",
    "seed_data": {"lead_url": "...", "signal_description": "..."}
})
```

### Cost Tracking Queries

```sql
-- Total cost for a run
SELECT run_id, total_tokens, total_cost
FROM v2_runs
WHERE run_id = 'RUN_...';

-- Average cost per run (for batch analysis)
SELECT AVG(total_cost) as avg_cost,
       AVG(total_tokens) as avg_tokens,
       COUNT(*) as run_count
FROM v2_runs
WHERE status = 'completed';

-- Most expensive runs
SELECT run_id, client_id, total_tokens, total_cost
FROM v2_runs
WHERE status = 'completed'
ORDER BY total_cost DESC
LIMIT 10;
```

---

## Notes from Author

**Last Updated:** 2026-01-18

- Both `run_id` and `dossier_id` generated at START (not end)
- `seed_data` contains the initial trigger info (lead URL, signal, etc.)
- `config_snapshot` captures client config at run time (for audit trail)
- `dossier_id` links to `v2_dossiers` record (created at assembly)
- `total_tokens` and `total_cost` are updated atomically via `increment_run_costs` RPC
- Cost is calculated from model pricing at step completion time (see `api/columnline/pricing.py`)
