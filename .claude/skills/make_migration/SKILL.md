---
name: make_migration
description: Build, edit, and understand the v2 Make.com pipeline, API routes, and Supabase tables for the Columnline dossier system.
---

## Current State (Jan 2026)

The v2 Make.com → Supabase pipeline is **operational**. Key components:

| Component | Status | Location |
|-----------|--------|----------|
| API Routes | ✅ Active | `api/columnline/routes.py` |
| Models | ✅ Active | `api/columnline/models.py` |
| Repository | ✅ Active | `api/columnline/repository.py` |
| Schema Docs | ✅ Active | `columnline_app/supabase_schema/` |
| Prompts | ✅ Active | `prompts/v2/` |

---

## Directory Structure

| Path | Purpose |
|------|---------|
| `api/columnline/` | **Active API code** - routes, models, repository |
| `columnline_app/supabase_schema/` | Human-readable table documentation |
| `prompts/v2/` | **Active prompts** (sync to v2_prompts table) |

---

## Supabase Tables

### Config Tables (Persist across runs)
| Table | Purpose |
|-------|---------|
| `v2_clients` | Client configurations (ICP, industry research) |
| `v2_prompts` | All 31+ prompts used in pipeline steps |
| `v2_section_definitions` | Dossier section templates |

### Execution Tables (Created per run)
| Table | Purpose |
|-------|---------|
| `v2_runs` | Pipeline run metadata |
| `v2_pipeline_logs` | Steps + stages (all LLM calls and stage completions) |
| `v2_contacts` | Enriched contact records |

### Production Tables (Published dossiers)
| Table | Purpose |
|-------|---------|
| `dossiers` | Published dossiers (created by /publish) |
| `contacts` | Published contacts (created by /publish) |
| `batches` | Batch tracking |

See `columnline_app/supabase_schema/*.md` for detailed docs on each table.

---

## Key API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/columnline/configs/{client_id}` | GET | Fetch client config + all prompts |
| `/columnline/runs/start` | POST | Create new pipeline run |
| `/columnline/steps/prepare` | POST | Prepare step input + return prompt |
| `/columnline/steps/complete` | POST | Store step output |
| `/columnline/steps/transition` | POST | Complete + prepare next (combined) |
| `/columnline/stages/start` | POST | Log stage start |
| `/columnline/stages/complete` | POST | Log stage completion |
| `/columnline/publish/{run_id}` | POST | Publish to production tables |

---

## Key Patterns

### Claims + Narratives
Downstream steps receive BOTH:
- `signal_discovery_claims` + `signal_discovery_narrative`
- `entity_research_claims` + `entity_research_narrative`
- etc.

### Stage Logging
Pipeline stages logged to `v2_pipeline_logs` with `event_type = 'stage_complete'`:
- Stage 1: search_signal
- Stage 2: entity_research
- Stage 3: parallel_research
- Stage 4: parallel_agents
- Stage 5: publish

### Model Usage
| Model | Use Case |
|-------|----------|
| `gpt-4.1` | Sync calls (most steps) |
| `gpt-5.2` | Media step (Firecrawl MCP) |
| `o4-mini-deep-research` | Async deep research (background) |

---

## Quick Reference

### Test Run
```bash
# Start a run
curl -X POST "https://api.columnline.dev/columnline/runs/start" \
  -H "Content-Type: application/json" \
  -d '{"client_id": "CLT_...", "seed_data": {"company_name": "Acme"}}'

# Prepare a step
curl -X POST "https://api.columnline.dev/columnline/steps/prepare" \
  -H "Content-Type: application/json" \
  -d '{"run_id": "RUN_...", "client_id": "CLT_...", "dossier_id": "DOS_...", "step_names": ["2_SIGNAL_DISCOVERY"]}'
```

### Deploy Changes
```bash
git add -A && git commit -m "..." && git push
# GitHub Actions auto-deploys to api.columnline.dev
```
