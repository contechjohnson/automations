---
name: make_migration_to_api
description: Build, edit, and understand automation, API, and functions, scripts related to the columnline_app, and make.com. So, anything related to column line app or make.com go here.
---

## Directory Structure

| Path | Purpose |
|------|---------|
| `columnline_app/` | All migration work is isolated here |
| `columnline_app/api_migration/execution/` | Production-ready scripts |
| `columnline_app/api_migration/make_scenarios_and_csvs/` | Raw Make.com exports and Google Sheets CSVs |
| `columnline_app/api_migration/docs/` | **Documentation for all blueprints and data sheets** |
| `columnline_app/api_migration/temp/` | Temporary/scratch files |

---

## Documentation Reference

All Make.com blueprints and CSV data sheets have been analyzed and documented.

### Blueprint Documentation (`docs/blueprints/`)

| File | Blueprint | Purpose |
|------|-----------|---------|
| [00-MAIN_DOSSIER_PIPELINE.md](columnline_app/api_migration/docs/blueprints/00-MAIN_DOSSIER_PIPELINE.md) | MAIN_DOSSIER_PIPELINE.json | Master orchestrator - calls all child blueprints |
| [00A-CLIENT_ONBOARDING.md](columnline_app/api_migration/docs/blueprints/00A-CLIENT_ONBOARDING.md) | _0A_CLIENT_ONBOARDING | Processes raw client input into configs |
| [00B-PREP_INPUTS.md](columnline_app/api_migration/docs/blueprints/00B-PREP_INPUTS.md) | _0B_PREP_INPUTS | Refines ICP, Industry, Research, Seed configs |
| [00C-BATCH_COMPOSER.md](columnline_app/api_migration/docs/blueprints/00C-BATCH_COMPOSER.md) | _0C_BATCH_COMPOSER | Plans batch execution strategy |
| [01-SEARCH_AND_SIGNAL.md](columnline_app/api_migration/docs/blueprints/01-SEARCH_AND_SIGNAL.md) | 01AND02_SEARCH_AND_SIGNAL | Discovers leads via web search |
| [03-DEEP_RESEARCH_STEPS.md](columnline_app/api_migration/docs/blueprints/03-DEEP_RESEARCH_STEPS.md) | 03_AND_04_SEQUENTIAL_DEEP_RESEARCH | Entity + Signal deep research (async) |
| [05A-ENRICH_LEAD.md](columnline_app/api_migration/docs/blueprints/05A-ENRICH_LEAD.md) | 05A_ENRICH_LEAD | Lead enrichment research |
| [05B-ENRICH_OPPORTUNITY.md](columnline_app/api_migration/docs/blueprints/05B-ENRICH_OPPORTUNITY.md) | 05B_ENRICH_OPPORTUNITY | Opportunity enrichment research |
| [05C-CLIENT_SPECIFIC.md](columnline_app/api_migration/docs/blueprints/05C-CLIENT_SPECIFIC.md) | 05C_CLIENT_SPECIFIC | Client-specific research |
| [06-ENRICH_CONTACTS.md](columnline_app/api_migration/docs/blueprints/06-ENRICH_CONTACTS.md) | 06_ENRICH_CONTACTS + 06.2 | Contact discovery + parallel enrichment |
| [07B-INSIGHT.md](columnline_app/api_migration/docs/blueprints/07B-INSIGHT.md) | 07B_INSIGHT | Claims merge + context pack building |
| [08-MEDIA.md](columnline_app/api_migration/docs/blueprints/08-MEDIA.md) | 08_MEDIA | Media/news discovery |
| [09-DOSSIER_PLAN.md](columnline_app/api_migration/docs/blueprints/09-DOSSIER_PLAN.md) | 09_DOSSIER_PLAN | Dossier structure planning |
| [10-WRITERS.md](columnline_app/api_migration/docs/blueprints/10-WRITERS.md) | WRITER_* (6 blueprints) | Section writers run in parallel |

### CSV/Data Sheet Documentation (`docs/csvs/`)

| File | Sheet | Purpose |
|------|-------|---------|
| [01-INPUTS.md](columnline_app/api_migration/docs/csvs/01-INPUTS.md) | Inputs | Client configs (ICP, Industry, Research Context, Seed) |
| [02-PROMPTS.md](columnline_app/api_migration/docs/csvs/02-PROMPTS.md) | Prompts | Live testing harness for all prompts |
| [03-MASTER.md](columnline_app/api_migration/docs/csvs/03-MASTER.md) | MASTER | Control panel toggles |
| [04-DOSSIER_SECTIONS.md](columnline_app/api_migration/docs/csvs/04-DOSSIER_SECTIONS.md) | DOSSIER SECTIONS | Section writer prompts + output schemas |
| [05-CONTACTS.md](columnline_app/api_migration/docs/csvs/05-CONTACTS.md) | Contacts | Enriched contact data |
| [06-OTHER_SHEETS.md](columnline_app/api_migration/docs/csvs/06-OTHER_SHEETS.md) | Clients, Dossiers, Onboarding, etc. | Supporting sheets |

---

## Key Patterns Discovered

### Async Polling Pattern
Make.com uses a polling pattern for async operations:
```
Trigger → BasicRepeater → Sleep(30s) → HTTP GET status → Router (break if complete)
```

### Claims System
1. Each research step extracts atomic claims (types: SIGNAL, CONTACT, ENTITY, RELATIONSHIP, OPPORTUNITY, METRIC, ATTRIBUTE, NOTE)
2. Claims merge at `07B_INSIGHT` step
3. Context packs built for downstream consumers

### Parallel Execution
- Writers (WRITER_*) run in parallel via `CallSubscenario`
- Contact enrichment (06.2) runs in parallel for each contact

### Model Usage
| Model | Use Case |
|-------|----------|
| `gpt-4.1` | Sync calls (most steps) |
| `o4-mini-deep-research` | Async deep research (03, 04, 05A, 05B, 05C) |

### Contact Enrichment Flow
1. Contact Discovery (Agent SDK) → Names + LinkedIn URLs
2. Apify LinkedIn Scraper → Profile data, company info, auto-discovered email
3. AnyMailFinder → SMTP-verified email (if not found by Apify)
4. Store in v2_contacts table

---

## Migration Roadmap

See the full plan: `~/.claude/plans/synthetic-finding-perlis.md`

**Phase 1**: Understand workflows (COMPLETE - all docs generated)
**Phase 2**: Create v2 Supabase schema
**Phase 3**: Build pipeline runner
**Phase 4**: Build prompt admin dashboard
**Phase 5**: Migrate steps to Python workers
**Phase 6**: Integrate with Next.js app
**Phase 7**: Testing & cutover

---

## Quick Reference

### Project Directive
Reference `columnline_app/columnline_app_directive.md` for current project state.

### External Resources
- Use Context7 for Make.com documentation
- Use Firecrawl for web scraping needs

### Raw Files Location
- Make.com JSON exports: `api_migration/make_scenarios_and_csvs/*.blueprint.json`
- Google Sheets CSVs: `api_migration/make_scenarios_and_csvs/*.csv`

---

## API Reference Documentation (`docs/`)

| File | APIs | Purpose |
|------|------|---------|
| [ENRICHMENT_APIS.md](columnline_app/api_migration/docs/ENRICHMENT_APIS.md) | AnyMailFinder, Apify | Contact email lookup, LinkedIn profile scraping |
| [OPENAI_REFERENCE.md](columnline_app/api_migration/docs/OPENAI_REFERENCE.md) | OpenAI | Chat Completions, Deep Research, Agents SDK, Structured Outputs |
| [CLAIMS_SYSTEM.md](columnline_app/api_migration/docs/CLAIMS_SYSTEM.md) | - | Claims extraction, merge, and routing patterns |
| [CLAIMS_STORAGE_SCHEMA.md](columnline_app/api_migration/docs/CLAIMS_STORAGE_SCHEMA.md) | Supabase | v2_* database tables for claims storage |
| [PROMPT_WORKBENCH.md](columnline_app/api_migration/docs/PROMPT_WORKBENCH.md) | - | Streamlit admin dashboard specification |

### External API Quick Reference

| API | Base URL | Auth | Cost |
|-----|----------|------|------|
| **AnyMailFinder** | `https://api.anymailfinder.com/v5.1/` | `Authorization: API_KEY` | 1 credit/valid email |
| **Apify LinkedIn** | `dev_fusion/linkedin-profile-scraper` | Apify token | $10/1000 profiles |
| **OpenAI Chat** | `https://api.openai.com/v1/chat/completions` | Bearer token | See pricing |
| **OpenAI Deep Research** | `https://api.openai.com/v1/responses` | Bearer token | $2-10/M tokens |
