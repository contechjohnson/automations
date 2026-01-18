# v2_context_packs

**Layer:** Execution (one per run)
**Purpose:** Store compressed context for downstream steps.

---

## Columns

| Column | Type | Description |
|--------|------|-------------|
| `pack_id` | TEXT (PK) | Unique pack ID |
| `run_id` | TEXT (FK) | Reference to `v2_runs.run_id` |
| `context_pack` | JSONB | Compressed context object |
| `created_at` | TIMESTAMP | Creation time |

---

## Context Pack Contents

Combines compressed versions of:
- ICP config
- Industry research
- Research context
- Key findings from research steps
- Signal summary
- Entity summary

Used by steps that need rich context without token overflow.

---

## Notes from Author

**Last Updated:** 2026-01-15

- Created by CONTEXT_PACK step after research completes
- Downstream steps can use this instead of raw research outputs
- Helps manage token limits for complex prompts
