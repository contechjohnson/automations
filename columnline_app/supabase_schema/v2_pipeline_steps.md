# v2_pipeline_steps

**Layer:** Execution (30-50 per run)
**Purpose:** Track individual step executions AND stage completions with inputs, outputs, and timing.

---

## Columns

| Column | Type | Description |
|--------|------|-------------|
| `step_id` | TEXT (PK) | Unique step ID (e.g., `STEP_20260115_181206_2_SIGNAL`) |
| `run_id` | TEXT (FK) | Reference to `v2_runs.run_id` |
| `prompt_id` | TEXT (FK) | Reference to `v2_prompts.prompt_id` (null for stages) |
| `step_name` | TEXT | Pipeline step name (e.g., `2_SIGNAL_DISCOVERY`) or stage name (e.g., `STAGE_1_SEARCH_SIGNAL`) |
| `status` | TEXT | `pending`, `running`, `completed`, `failed` |
| `event_type` | TEXT | `step` (default), `stage_start`, or `stage_complete` |
| `input` | JSONB | Input data passed to the step |
| `output` | JSONB | Full output from the step (LLM response) |
| `tokens_used` | INTEGER | Total tokens (input + output) |
| `runtime_seconds` | FLOAT | Step execution time |
| `model_used` | TEXT | Model used (e.g., `gpt-4.1`, `o4-mini-deep-research`) |
| `started_at` | TIMESTAMP | Step start time |
| `completed_at` | TIMESTAMP | Step completion time |
| `error_message` | TEXT | Error details if failed |

---

## Event Types

| Type | Description | Example step_name |
|------|-------------|-------------------|
| `step` | Regular pipeline step (LLM call) | `2_SIGNAL_DISCOVERY`, `5A_ENRICH_LEAD` |
| `stage_start` | Stage began (deprecated: use stage_complete only) | `STAGE_1_SEARCH_SIGNAL` |
| `stage_complete` | Stage finished | `STAGE_1_SEARCH_SIGNAL` |

### Query Examples

```sql
-- All events for a run (chronological)
SELECT event_type, step_name, status, started_at, completed_at, runtime_seconds
FROM v2_pipeline_steps
WHERE run_id = 'RUN_...'
ORDER BY started_at;

-- Stage completions only
SELECT step_name, runtime_seconds, completed_at
FROM v2_pipeline_steps
WHERE run_id = 'RUN_...' AND event_type = 'stage_complete';

-- Steps only (exclude stages)
SELECT step_name, tokens_used, runtime_seconds
FROM v2_pipeline_steps
WHERE run_id = 'RUN_...' AND event_type = 'step';

-- Failed stages
SELECT * FROM v2_pipeline_steps
WHERE event_type = 'stage_complete' AND status = 'failed';
```

---

## Key Points

### Input Contains BOTH Claims AND Narratives

For downstream steps, input now includes:
```json
{
  "signal_discovery_claims": [...],
  "signal_discovery_narrative": "Full narrative text...",
  "entity_research_claims": [...],
  "entity_research_narrative": "Full narrative text...",
  "contact_discovery_claims": [...],
  "contact_discovery_narrative": "Full narrative text...",
  // ... etc for all research steps
}
```

### Output Stored As-Is

The full OpenAI response is stored, including:
- Token usage
- Timing info
- Complete response content

```python
# Example output structure
{
  "id": "chatcmpl-...",
  "model": "gpt-4.1",
  "usage": {"prompt_tokens": 1234, "completion_tokens": 567},
  "choices": [{"message": {"content": "..."}}]
}
```

---

## Status Flow

```
pending → running → completed
                 ↘ failed
```

---

## API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /steps/prepare` | Create step(s), populate input, return prompt |
| `POST /steps/complete` | Store output, mark completed |
| `POST /steps/transition` | Complete one step + prepare next (combined) |
| `POST /stages/start` | Log stage start (event_type=stage_start) |
| `POST /stages/complete` | Log stage completion (event_type=stage_complete) |

---

## Usage

```python
# Example: Prepare a step
step = repo.create_pipeline_step({
    "step_id": "STEP_20260115_181206_2_SIGNAL",
    "run_id": "RUN_20260115_181206",
    "step_name": "2_SIGNAL_DISCOVERY",
    "status": "running",
    "input": {...},
    "model_used": "gpt-4.1"
})

# Example: Complete a step
repo.update_pipeline_step(step_id, {
    "status": "completed",
    "output": openai_response,
    "tokens_used": 1801,
    "runtime_seconds": 12.5
})
```

---

## Notes from Author

**Last Updated:** 2026-01-18

- Steps with `produce_claims=TRUE` trigger a follow-up `CLAIMS_EXTRACTION` step
- Input contains ALL available context (claims + narratives) - Make.com maps what it needs
- Output is stored as-is for debugging and audit trail
- Multiple steps can have same `step_name` in a run (e.g., parallel writers)
- Stages (event_type != 'step') track pipeline stage boundaries for timing analysis
