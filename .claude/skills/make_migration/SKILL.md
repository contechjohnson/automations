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
| Claims Merge | ✅ Active | `api/columnline/claims_merge.py` |
| Prompts (v2) | ✅ Active | `columnline_app/api_migration/make_scenarios_and_supabase_tables/prompts_v2/` |
| Table Docs | ✅ Active | `columnline_app/api_migration/make_scenarios_and_supabase_tables/supabase_tables/` |

---

## Directory Structure

| Path | Purpose |
|------|---------|
| `api/columnline/` | **Active API code** - routes, models, repository |
| `columnline_app/api_migration/make_scenarios_and_supabase_tables/` | Make.com exports + table docs |
| `columnline_app/api_migration/make_scenarios_and_supabase_tables/prompts_v2/` | **Active prompts** (sync to v2_prompts table) |
| `columnline_app/api_migration/make_scenarios_and_supabase_tables/supabase_tables/` | Human-readable table documentation |
| `columnline_app/api_migration/_archive/` | Archived CSVs, old docs (historical only) |

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
| `v2_dossiers` | Final assembled dossiers |
| `v2_pipeline_steps` | Individual step executions |
| `v2_claims` | Extracted claims from research |
| `v2_merged_claims` | Consolidated claims (patches applied) |
| `v2_context_packs` | Compressed context for downstream |
| `v2_sections` | Written dossier sections |
| `v2_contacts` | Enriched contact records |

See `supabase_tables/*.md` for detailed docs on each table.

---

## Key API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/columnline/configs/{client_id}` | GET | Fetch client config + all prompts |
| `/columnline/runs` | POST | Create new pipeline run |
| `/columnline/steps/prepare` | POST | Prepare step input + return prompt |
| `/columnline/steps/complete` | POST | Store step output |
| `/columnline/steps/transition` | POST | Complete + prepare next (combined) |

---

## Key Patterns

### Claims + Narratives
Downstream steps receive BOTH:
- `signal_discovery_claims` + `signal_discovery_narrative`
- `entity_research_claims` + `entity_research_narrative`
- etc.

### Patch-Based Merge
Instead of LLM rewriting all claims:
1. LLM generates ~20 targeted patches
2. Python code applies patches programmatically
3. More efficient, preserves originals, transparent

### Model Usage
| Model | Use Case |
|-------|----------|
| `gpt-4.1` | Sync calls (most steps) |
| `gpt-5.2` | Media step (Firecrawl MCP) |
| `o4-mini-deep-research` | Async deep research (background) |

---

## Make.com Blueprint Files

Raw exports from Make.com (for reference/parsing):

| File | Scenario |
|------|----------|
| `MAIN_DOSSIER_PIPELINE.json` | Master orchestrator |
| `01AND02_SEARCH_AND_SIGNAL.blueprint.json` | Search + Signal Discovery |
| `03_AND_04_SEQUENTIAL_DEEP_RESEARCH_STEPS.blueprint.json` | Entity + Contact Research |
| `05A_ENRICH_LEAD.blueprint.json` | Lead Enrichment |
| `05B_ENRICH_OPPORTUNITY.blueprint.json` | Opportunity Enrichment |
| `05C_CLIENT_SPECIFIC.blueprint.json` | Client-Specific Research |
| `06_ENRICH_CONTACTS.blueprint.json` | Contact Enrichment |
| `07B_INSIGHT.blueprint.json` | Insight + Claims Merge |
| `08_MEDIA.blueprint.json` | Media/Images |
| `09_DOSSIER_PLAN.blueprint.json` | Dossier Planning |
| `WRITER_*.blueprint.json` | Section Writers (6 files) |

Use `/parsing-make-blueprints` skill to parse these into business logic docs.

---

## Quick Reference

### Test Run
```bash
# Get latest IDs
curl "https://api.columnline.dev/columnline/runs?limit=1"

# Prepare a step
curl -X POST "https://api.columnline.dev/columnline/steps/prepare" \
  -H "Content-Type: application/json" \
  -d '{"run_id": "RUN_...", "client_id": "CLT_...", "step_names": ["2_SIGNAL_DISCOVERY"]}'
```

### Deploy Changes
```bash
git add -A && git commit -m "..." && git push
# GitHub Actions auto-deploys to api.columnline.dev
```

### Clear Test Data
Use the clear script: `tmp/clear_v2_runs.py`

---

## Next Steps (Integration)

When ready to render dossiers in Columnline app:
1. Add `production_client_id` column to `v2_clients`
2. Create transform layer (`v2_dossiers` → production `dossiers` table)
3. Add `/columnline/publish/{run_id}` endpoint
4. Map v2 JSONB output to production schema

See plan notes in `~/.claude/plans/` for full integration strategy.
