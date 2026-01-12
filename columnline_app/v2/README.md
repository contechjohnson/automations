# Columnline v2 Pipeline

Production dossier generation pipeline migrated from Make.com.

## Quick Start

### 1. Start API Server
```bash
# On droplet
cd /opt/automations
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### 2. Start Dashboard
```bash
# On droplet
cd /opt/automations
streamlit run admin/app.py --server.port 8501 --server.headless true
```

### 3. Run Pipeline Test
```bash
cd /opt/automations
python -m columnline_app.v2.test_pipeline
```

## Architecture

### Pipeline Stages

| Stage | Steps | Execution Mode |
|-------|-------|----------------|
| **FIND_LEAD** | 1-search-builder | Sync |
|  | 2-signal-discovery | Agent (web search) |
|  | 3-entity-research | Background (deep research) |
|  | 4-contact-discovery | Background (deep research) |
| **ENRICH_LEAD** | 5a-enrich-lead | Agent (parallel) |
|  | 5b-enrich-opportunity | Agent (parallel) |
|  | 5c-client-specific | Agent (parallel) |
| **ENRICH_CONTACTS** | 6-enrich-contacts | Sync |
|  | 6.2-enrich-contact | Agent (per contact) |
| **COPY** | 7a-copy | Sync |
|  | 7.2-copy-client-override | Sync |
| **INSIGHT** | 7b-insight | Sync (merge claims) |
| **MEDIA** | 8-media | Agent |
| **DOSSIER_PLAN** | 9-dossier-plan | Sync |

### Claims System

1. **Extraction**: Steps 2-7b extract atomic claims with:
   - claim_id, claim_type, statement
   - source_url, source_name, source_tier
   - confidence level

2. **Accumulation**: Claims accumulate without merging

3. **Merge (7b-insight)**: Single merge point that:
   - Deduplicates identical claims
   - Resolves conflicts (GOV > PRIMARY > NEWS > OTHER)
   - Creates contact/timeline resolutions
   - Produces merged claims for section writers

### Context Packs

Efficiency summaries passed between stages:

| Pack Type | Produced By | Contains |
|-----------|-------------|----------|
| signal_to_entity | 3-entity-research | Signal summary, company info |
| entity_to_contacts | 4-contact-discovery | Key contacts, org structure |
| contacts_to_enrichment | 7b-insight | Merged facts, insights |

## Database Schema

All tables use `v2_` prefix (no conflicts with existing tables).

### Core Tables

- `v2_clients` - Client configurations
- `v2_prompts` - Prompt registry
- `v2_prompt_versions` - Version history
- `v2_pipeline_runs` - Pipeline execution tracking
- `v2_step_runs` - Per-step I/O capture

### Claims Tables

- `v2_claims` - Raw claims before merge
- `v2_merged_claims` - Deduplicated claims
- `v2_resolved_objects` - Contact/timeline resolutions
- `v2_context_packs` - Efficiency summaries
- `v2_claim_assignments` - Section routing
- `v2_merge_stats` - Merge observability

### Output Tables

- `v2_dossiers` - Generated dossiers
- `v2_dossier_sections` - Section content
- `v2_contacts` - Enriched contacts with copy

## API Endpoints

```
/v2/clients/         - Client CRUD
/v2/prompts/         - Prompt view/edit
/v2/pipeline/start   - Start new run
/v2/pipeline/runs    - List runs
/v2/pipeline/runs/{id}/live  - Real-time status (polling)
/v2/claims/runs/{id} - View claims
/v2/dossiers/{id}    - View dossier with contacts
```

## Dashboard Pages

1. **Pipeline** - Start runs, monitor progress, step timeline
2. **Prompts** - Edit prompts, view I/O, version history
3. **Step Detail** - Deep I/O inspection, variable lineage
4. **Claims** - Browse raw/merged claims by type
5. **Contacts** - View contacts with email/LinkedIn copy

## File Structure

```
columnline_app/v2/
├── api/router.py          # FastAPI endpoints
├── config.py              # Step definitions
├── db/
│   ├── models.py          # Pydantic models
│   └── repository.py      # Supabase CRUD
├── pipeline/
│   ├── runner.py          # Main orchestrator
│   ├── state.py           # Pipeline state
│   └── step_executor.py   # Step execution
└── test_pipeline.py       # Test script

admin/
├── app.py                 # Streamlit entry
└── pages/
    ├── pipeline.py
    ├── prompts.py
    ├── step_detail.py
    ├── claims.py
    └── contacts.py

prompts/v2/                # 14 prompt files
database/migrations/       # SQL schema
```

## Environment Variables

```bash
OPENAI_API_KEY=           # Required for LLM calls
SUPABASE_URL=             # Database
SUPABASE_SERVICE_ROLE_KEY # Database auth
FIRECRAWL_API_KEY=        # Web scraping
APOLLO_API_KEY=           # Contact enrichment
ANYMAILFINDER_API_KEY=    # Email discovery
```

## Testing

```bash
# Run database and prompt loading tests
python -m columnline_app.v2.test_pipeline

# Run full pipeline (takes 5-10 minutes)
RUN_FULL_PIPELINE_TEST=true python -m columnline_app.v2.test_pipeline
```

## Deployment

```bash
# Deploy code
ssh root@64.225.120.95
cd /opt/automations
git pull
pip install -r requirements.txt

# Restart services
systemctl restart automations-api

# Start dashboard
streamlit run admin/app.py --server.port 8501 --server.headless true
```

## Access

| Service | URL |
|---------|-----|
| API | https://api.columnline.dev/v2/health |
| Dashboard | http://64.225.120.95:8501 |
| API Docs | https://api.columnline.dev/docs |
