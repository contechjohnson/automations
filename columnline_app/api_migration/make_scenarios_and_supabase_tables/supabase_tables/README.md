# V2 Supabase Tables

This folder contains human-readable documentation for each Supabase table used by the V2 Make.com pipeline.

## Table Categories

### Config Tables (Persist across runs)
| Table | Purpose | Row Count |
|-------|---------|-----------|
| `v2_clients` | Client configurations (ICP, industry research, etc.) | ~5-10 |
| `v2_prompts` | All 31+ prompts used in pipeline steps | ~31 |
| `v2_section_definitions` | Dossier section templates and configs | ~8 |

### Execution Tables (Created per run)
| Table | Purpose | Notes |
|-------|---------|-------|
| `v2_runs` | Pipeline run metadata | One per dossier generation |
| `v2_dossiers` | Final assembled dossiers | Created at assembly step |
| `v2_pipeline_steps` | Individual step executions | ~30-50 per run |
| `v2_claims` | Extracted claims from research | ~100-300 per run |
| `v2_merged_claims` | Consolidated/patched claims | After MERGE_CLAIMS step |
| `v2_context_packs` | Compressed context for later steps | One per run |
| `v2_sections` | Written dossier sections | ~8 per run |
| `v2_contacts` | Enriched contact records | ~5-20 per run |

## Data Flow

```
v2_clients (config)
     ↓
v2_runs (start pipeline)
     ↓
v2_pipeline_steps (each AI step)
     ↓
v2_claims (extracted from research steps)
     ↓
v2_merged_claims (patches applied)
     ↓
v2_context_packs (compressed for downstream)
     ↓
v2_sections (written by section writers)
     ↓
v2_contacts (enriched contacts)
     ↓
v2_dossiers (final assembly)
```

## Notes from Author

**Last Updated:** 2026-01-15

**Key Changes:**
- All data now lives in Supabase (no more Google Sheets CSVs)
- Claims extraction preserves context (mini-narratives, not atomic facts)
- Merge claims uses patch-based approach (not full rewrite)
- Narratives + claims both passed to downstream steps

**Integration Notes:**
- API routes in `/api/columnline/` read/write these tables
- Make.com calls API endpoints (never direct Supabase access)
- All step outputs stored as JSONB for flexibility
