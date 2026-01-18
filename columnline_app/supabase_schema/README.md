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
| `v2_pipeline_logs` | Steps, stages, and all LLM executions | ~30-50 per run, includes event_type for stages |
| `v2_contacts` | Enriched contact records | ~5-20 per run |

### Production Tables (Published dossiers)
| Table | Purpose | Notes |
|-------|---------|-------|
| `dossiers` | Published dossiers | Created by /publish endpoint |
| `contacts` | Published contacts | Created by /publish endpoint |
| `batches` | Batch tracking | Linked to dossiers |

## Data Flow

```
v2_clients (config)
     ↓
v2_runs (start pipeline)
     ↓
v2_pipeline_logs (each AI step + stage completions)
     ↓
v2_contacts (enriched contacts during run)
     ↓
/publish endpoint
     ↓
dossiers + contacts (production tables)
```

## Consolidated Design

**As of 2026-01-18:**

All step and stage data is stored in `v2_pipeline_logs`:
- **Steps:** Regular LLM calls (`event_type = 'step'`)
- **Stages:** Pipeline stage boundaries (`event_type = 'stage_complete'`)

This replaces the previous design with separate tables for claims, sections, etc.

### What Changed
- `v2_claims` → stored in `v2_pipeline_logs.output`
- `v2_merged_claims` → stored in `v2_pipeline_logs.output`
- `v2_context_packs` → stored in `v2_pipeline_logs.output`
- `v2_sections` → stored in `v2_pipeline_logs.output`
- `v2_dossiers` → goes directly to production `dossiers` table via /publish

## Notes from Author

**Last Updated:** 2026-01-18

**Key Changes:**
- Consolidated to 2 core execution tables: `v2_runs` + `v2_pipeline_logs`
- Stage tracking via `event_type` column on `v2_pipeline_logs`
- All step outputs stored as JSONB in `v2_pipeline_logs.output`
- Production dossiers go directly to `dossiers` table (no intermediate v2_dossiers)

**Integration Notes:**
- API routes in `/api/columnline/` read/write these tables
- Make.com calls API endpoints (never direct Supabase access)
- Stage endpoints: `POST /stages/start`, `POST /stages/complete`
