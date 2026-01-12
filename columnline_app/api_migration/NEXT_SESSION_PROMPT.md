# Next Session Prompt: Build the Full Dossier Pipeline Stack

Copy this prompt into a fresh Claude Code terminal:

---

## Context

I'm migrating a Make.com visual automation pipeline to production Python code. The existing system uses **10 Google Sheets CSVs as a testing harness** - they serve as both config storage and live I/O visibility during development.

**The goal:** Build the complete stack - database tables, API endpoints, pipeline runner, AND dashboard - so I can run real dossier jobs and watch them execute in real-time.

## Documentation (READ THESE FIRST)

The following docs in `columnline_app/api_migration/docs/` explain the full system:

1. **`MIGRATION_PLAN.md`** - Complete technical spec (1500+ lines)
2. **`CLAIMS_SYSTEM.md`** - How claims extraction/merge works
3. **`CLAIMS_STORAGE_SCHEMA.md`** - Supabase tables for claims
4. **`PROMPT_WORKBENCH.md`** - Dashboard UI requirements
5. **`docs/csvs/*.md`** - Documentation of each CSV's purpose
6. **`docs/blueprints/*.md`** - Documentation of each Make.com scenario

## What the 10 CSVs Represent (What I Need to Replicate)

| CSV | Purpose | What We're Building |
|-----|---------|---------------------|
| **MASTER** | Control panel - toggles for what runs | API endpoint + job submission UI |
| **Inputs** | Client configs (ICP, Industry, Research Context) | `v2_clients` table + config editor |
| **Prompts** | All pipeline prompts + live I/O columns | `v2_prompts` + `v2_step_runs` tables + workbench UI |
| **DOSSIER SECTIONS** | Section writer prompts + outputs | `v2_dossier_sections` + section preview |
| **Contacts** | Enriched contacts accumulating | `v2_contacts` table + live table UI |
| **Dossiers** | Completed dossier metadata | `v2_dossiers` table + list view |
| **Clients** | Client metadata | `v2_clients` table + management UI |
| **Onboarding** | Raw client intake → processed configs | Onboarding API + wizard UI |
| **PrepInputs** | Intermediate refinement step | Pipeline step outputs |
| **Batch Composer Inputs** | Batch planning configs | Job queue parameters |

## The Full Stack We Need

### Layer 1: Database (Supabase)

```
v2_clients          - Client configs (ICP, Industry, Research Context)
v2_prompts          - Prompt registry with metadata
v2_prompt_versions  - Version history for prompts
v2_pipeline_runs    - Job-level tracking
v2_step_runs        - Step-level I/O capture (THE KEY TABLE)
v2_claims           - Raw claims before merge
v2_merged_claims    - Claims after insight merge
v2_context_packs    - Context packs for downstream steps
v2_dossiers         - Completed dossier metadata
v2_dossier_sections - Section content (intro, signals, strategy, etc.)
v2_contacts         - Enriched contacts per dossier
```

### Layer 2: API Endpoints (FastAPI)

```python
# Client Management
POST   /v2/clients                    # Create client with configs
GET    /v2/clients                    # List clients
GET    /v2/clients/{id}               # Get client with full configs
PUT    /v2/clients/{id}               # Update client configs

# Prompt Management
GET    /v2/prompts                    # List all prompts
GET    /v2/prompts/{id}               # Get prompt with versions
PUT    /v2/prompts/{id}               # Save new version
POST   /v2/prompts/{id}/test          # Run prompt in isolation

# Pipeline Execution
POST   /v2/pipeline/start             # Start new pipeline run
GET    /v2/pipeline/runs              # List runs (with filters)
GET    /v2/pipeline/runs/{id}         # Get run with all steps
GET    /v2/pipeline/runs/{id}/steps   # Get step details
POST   /v2/pipeline/runs/{id}/retry   # Retry failed step

# Real-time Data (for dashboard polling)
GET    /v2/pipeline/runs/{id}/live    # Current state + recent updates
GET    /v2/contacts?run_id={id}       # Contacts for a run (growing)
GET    /v2/claims?run_id={id}         # Claims for a run

# Dossiers
GET    /v2/dossiers                   # List completed dossiers
GET    /v2/dossiers/{id}              # Full dossier with sections
```

### Layer 3: Pipeline Runner

```python
# columnline_app/v2/pipeline/runner.py

class PipelineRunner:
    """Executes pipeline steps, writing to Supabase after each."""

    def __init__(self, run_id: str, client_id: str):
        self.run_id = run_id
        self.client_id = client_id

    async def run_step(self, step_name: str, input_data: dict) -> dict:
        """
        1. Create v2_step_runs record (status=running)
        2. Load prompt from v2_prompts
        3. Interpolate variables
        4. Call LLM via workers/ai.py
        5. Parse output
        6. Update v2_step_runs with output
        7. If claims step: write to v2_claims
        8. Return output for next step
        """

    async def run_full_pipeline(self, seed: dict = None):
        """Execute all stages in order."""
```

### Layer 4: Dashboard (Streamlit)

```
admin/
├── app.py                 # Main entry
├── pages/
│   ├── 1_pipeline.py      # Submit jobs, watch runs
│   ├── 2_prompts.py       # Edit prompts, test in isolation
│   ├── 3_clients.py       # Manage client configs
│   ├── 4_dossiers.py      # View completed dossiers
│   ├── 5_contacts.py      # Browse contacts
│   └── 6_claims.py        # Claims browser
```

## What I Want Built This Session

### Phase 1: Database Foundation
1. Create all v2_* tables in Supabase
2. Seed with prompts from the CSVs (extract actual prompt text)
3. Create one test client with configs

### Phase 2: Core API
1. Client CRUD endpoints
2. Prompt CRUD endpoints
3. Pipeline start/status endpoints
4. Step run query endpoints

### Phase 3: Pipeline Runner (One Stage)
1. Build runner skeleton
2. Implement FIND LEAD stage (search_builder → signal_discovery)
3. Write step outputs to v2_step_runs
4. Verify data appears in Supabase

### Phase 4: Dashboard (Core Pages)
1. Pipeline page - submit job, watch steps complete
2. Prompts page - view/edit prompts, see last I/O
3. Make it actually talk to the API

### Phase 5: Wire It Together
1. Submit job from dashboard
2. Runner executes steps
3. Dashboard polls and shows progress
4. View step I/O in real-time

## Key Insight: What Made Google Sheets Valuable

The sheets weren't just storage - they were **live visibility**:
- Column D showed what INPUT went to each prompt
- Column E showed what OUTPUT came back
- I could watch data populate as the pipeline ran
- I could edit a prompt, re-run, immediately see the difference

**The `v2_step_runs` table IS the new Prompts sheet.** Every row captures:
- `input_variables` (Column D)
- `interpolated_prompt` (what actually went to LLM)
- `raw_output` (Column E)
- `parsed_output` (structured JSON)

## Technical Details

### Existing Infrastructure
- **Droplet**: 64.225.120.95
- **API**: https://api.columnline.dev (FastAPI via Caddy)
- **Supabase**: Already set up, credentials in .env
- **LLM Layer**: `workers/ai.py` with `prompt()` function

### Key Files to Create/Modify
```
columnline_app/
└── v2/
    ├── __init__.py
    ├── db/
    │   ├── __init__.py
    │   ├── models.py          # Pydantic models
    │   └── repository.py      # Supabase queries
    ├── pipeline/
    │   ├── __init__.py
    │   ├── runner.py          # Main orchestrator
    │   └── steps/
    │       ├── __init__.py
    │       ├── search_builder.py
    │       ├── signal_discovery.py
    │       └── ...
    └── api/
        ├── __init__.py
        ├── clients.py         # Client endpoints
        ├── prompts.py         # Prompt endpoints
        └── pipeline.py        # Pipeline endpoints

admin/
├── app.py
└── pages/
    ├── 1_pipeline.py
    ├── 2_prompts.py
    └── 3_clients.py

database/
└── migrations/
    └── 002_v2_pipeline_tables.sql
```

## Success Criteria

1. ✅ Tables exist in Supabase with sample data
2. ✅ Can create/read clients via API
3. ✅ Can view/edit prompts via API
4. ✅ Can start a pipeline run via API
5. ✅ Runner executes at least 2 steps, writing to v2_step_runs
6. ✅ Dashboard shows run progress in real-time
7. ✅ Can view step I/O in dashboard (input/output side by side)

## Important Guidelines

- **Read the docs first** - especially `CLAIMS_STORAGE_SCHEMA.md` for table schemas
- **Use existing `workers/ai.py`** - don't reinvent LLM calling
- **Write to Supabase after each step** - that's how we get real-time visibility
- **Start with FIND LEAD stage** - it's the simplest (2 steps, no parallelism)
- **Test incrementally** - verify each layer works before building the next
- **The CSVs have real prompt text** - extract and seed the prompts table

## Prompts Location

The actual prompt text lives in:
- `make_scenarios_and_csvs/DOSSIER_FLOW_TEST - Prompts.csv` (Column C)
- `make_scenarios_and_csvs/DOSSIER_FLOW_TEST - Inputs.csv` (B6, B7, B8 for claims prompts)
- `make_scenarios_and_csvs/DOSSIER_FLOW_TEST - DOSSIER SECTIONS.csv` (Column C for writers)

Let's start by having you read `CLAIMS_STORAGE_SCHEMA.md` and `PROMPT_WORKBENCH.md`, then create the database migration SQL, then build out from there.

---

**End of prompt. Paste the above into a fresh terminal.**
