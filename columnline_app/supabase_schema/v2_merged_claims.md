# v2_merged_claims

**Layer:** Execution (one per run)
**Purpose:** Store claims consolidation patches and merged output.

---

## Columns

| Column | Type | Description |
|--------|------|-------------|
| `merge_id` | TEXT (PK) | Unique merge operation ID |
| `run_id` | TEXT (FK) | Reference to `v2_runs.run_id` |
| `patches` | JSONB | Array of patch operations from MERGE_CLAIMS step |
| `merged_claims` | JSONB | Final consolidated claims (patches applied) |
| `merge_summary` | JSONB | Stats about merge operation |
| `created_at` | TIMESTAMP | Merge time |

---

## Patch-Based Merge

Instead of LLM rewriting all claims, we use targeted patches:

```json
{
  "patches": [
    {"operation": "merge", "claim_ids": ["...", "..."], "keep_claim_id": "..."},
    {"operation": "invalidate", "claim_id": "...", "reason": "..."},
    {"operation": "flag_conflict", "claim_ids": ["...", "..."]}
  ],
  "merge_summary": {
    "total_input_claims": 247,
    "patches_applied": 18,
    "final_claim_count": 235
  }
}
```

---

## Notes from Author

**Last Updated:** 2026-01-15

- Patches applied programmatically via `claims_merge.py`
- Original claims preserved, patches add metadata
- More efficient than full LLM rewrite (~20 patches vs 200+ claims)
