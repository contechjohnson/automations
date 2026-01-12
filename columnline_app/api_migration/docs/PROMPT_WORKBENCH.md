# Prompt Engineering Workbench Requirements

**Purpose:** Replace Google Sheets-based prompt editing/testing with a Streamlit admin dashboard.

**Location:** `admin/` directory on the automations droplet
**Access:** http://64.225.120.95:8501 (Streamlit default) or proxied via Caddy

---

## Current State (Google Sheets)

The Google Sheets testing harness provides:

| Feature | How It Works |
|---------|--------------|
| **Prompt editing** | Edit cell C{row} directly in Prompts sheet |
| **Live input capture** | Column D shows what was actually sent to LLM |
| **Live output capture** | Column E shows raw LLM response |
| **Claims inspection** | Column I shows extracted claims JSON |
| **Quick iteration** | Change prompt, run pipeline, see results immediately |

**Pain points:**
1. No version history - easy to break working prompts
2. No side-by-side comparison of before/after
3. Cell limits for large prompts
4. Can't easily test single step in isolation
5. No tracking of which client/run produced which output
6. Claims and context packs hard to visualize in cells

---

## Target State (Streamlit Dashboard)

### Page 1: Prompt Engineering (`1_prompts.py`)

**Primary Interface** - where you spend 80% of time iterating on prompts.

```
┌────────────────────────────────────────────────────────────────────┐
│  PROMPT ENGINEERING WORKBENCH                                      │
├──────────────────┬─────────────────────────────────────────────────┤
│ PROMPTS          │                                                  │
│ ─────────────    │  Prompt: entity-research                        │
│ ○ search-builder │  Stage: FIND LEAD | Step: 3 | Model: gpt-4.1   │
│ ○ signal-disc... │                                                  │
│ ● entity-research│  ┌────────────────────────────────────────────┐ │
│ ○ contact-disc...│  │ You are researching {{entity_name}} for    │ │
│ ○ enrich-lead    │  │ {{client_name}}.                           │ │
│ ○ enrich-opp     │  │                                            │ │
│ ○ client-spec    │  │ ICP Context:                               │ │
│ ○ insight        │  │ {{icp_config}}                             │ │
│ ○ dossier-plan   │  │                                            │ │
│ ○ copy           │  │ ...                                        │ │
│                  │  └────────────────────────────────────────────┘ │
│ [+ New Prompt]   │                                                  │
│                  │  [Save Version]  Model: [gpt-4.1 ▼]  Temp: [0.7]│
├──────────────────┴─────────────────────────────────────────────────┤
│  LAST RUN                                                          │
│  Client: Acme Corp | Run: 2025-01-10 14:32 | Duration: 12.4s      │
├──────────────────────────────────────┬─────────────────────────────┤
│  INPUT VARIABLES                     │  OUTPUT                     │
│  {                                   │  {                          │
│    "entity_name": "TechCorp Inc",    │    "corporate_structure": { │
│    "client_name": "Acme",            │      "parent": "...",       │
│    "icp_config": {...}               │      "subsidiaries": [...]  │
│  }                                   │    },                       │
│                                      │    "claims": [...]          │
│                                      │  }                          │
├──────────────────────────────────────┴─────────────────────────────┤
│  CLAIMS PRODUCED (if applicable)                                   │
│  ┌────────┬──────────┬────────────────────────────┬───────────────┐│
│  │ ID     │ Type     │ Statement                  │ Source        ││
│  ├────────┼──────────┼────────────────────────────┼───────────────┤│
│  │ er_001 │ ENTITY   │ TechCorp HQ in Austin      │ corp website  ││
│  │ er_002 │ METRIC   │ Revenue $50M (2024)        │ SEC filing    ││
│  │ er_003 │ CONTACT  │ John Smith is CTO          │ LinkedIn      ││
│  └────────┴──────────┴────────────────────────────┴───────────────┘│
├────────────────────────────────────────────────────────────────────┤
│  [Run Step (Use Last Input)]  [Run with New Input...]             │
└────────────────────────────────────────────────────────────────────┘
```

**Features:**

| Feature | Description |
|---------|-------------|
| **Prompt sidebar** | List all prompts, grouped by stage (FIND LEAD, ENRICH, etc.) |
| **Monaco editor** | Syntax highlighting, {{variable}} highlighting |
| **Version dropdown** | Switch between saved versions |
| **Save Version** | Creates new version with optional change notes |
| **Diff view** | Side-by-side comparison between versions |
| **Config panel** | Model selection, temperature, max tokens |
| **Last run display** | Input/output from most recent execution |
| **Claims table** | If step produces claims, show them in table format |
| **Run button** | Execute step in isolation using last input or custom input |

---

### Page 2: Pipeline Runs (`2_runs.py`)

**Monitoring Interface** - view pipeline execution history.

```
┌────────────────────────────────────────────────────────────────────┐
│  PIPELINE RUNS                                                     │
├────────────────────────────────────────────────────────────────────┤
│  [All Clients ▼]  [All Statuses ▼]  [Last 7 Days ▼]  [Search...]  │
├────────────────────────────────────────────────────────────────────┤
│  ┌────────┬────────────┬──────────────┬────────┬──────────┬──────┐│
│  │ ID     │ Client     │ Status       │ Steps  │ Duration │ Time ││
│  ├────────┼────────────┼──────────────┼────────┼──────────┼──────┤│
│  │ abc123 │ Acme Corp  │ ✓ completed  │ 14/14  │ 47m      │ 2h   ││
│  │ def456 │ TechStart  │ ✗ failed     │ 8/14   │ 23m      │ 5h   ││
│  │ ghi789 │ Acme Corp  │ ⏳ running   │ 6/14   │ 18m      │ now  ││
│  └────────┴────────────┴──────────────┴────────┴──────────┴──────┘│
└────────────────────────────────────────────────────────────────────┘
```

**Click a run** to see step breakdown:

```
┌────────────────────────────────────────────────────────────────────┐
│  RUN: abc123 | Acme Corp | 2025-01-10 14:00                       │
├────────────────────────────────────────────────────────────────────┤
│  STEPS                                                             │
│  ┌────────────────────────┬────────┬──────────┬───────────────────┐│
│  │ Step                   │ Status │ Duration │ Tokens            ││
│  ├────────────────────────┼────────┼──────────┼───────────────────┤│
│  │ 1. search-builder      │ ✓      │ 8.2s     │ 1,234 / 892       ││
│  │ 2. signal-discovery    │ ✓      │ 12.4s    │ 2,100 / 1,450     ││
│  │ 3. entity-research     │ ✓      │ 15.1s    │ 3,200 / 2,100     ││
│  │ 4. contact-discovery   │ ✓      │ 11.3s    │ 2,800 / 1,900     ││
│  │ 5a. enrich-lead        │ ✓      │ 9.8s     │ 2,400 / 1,600     ││
│  │ 5b. enrich-opportunity │ ✓      │ 10.2s    │ 2,600 / 1,800     ││
│  │ 5c. client-specific    │ ✓      │ 8.9s     │ 2,200 / 1,500     ││
│  │ 6. enrich-contacts     │ ✓      │ 45.2s    │ API calls only    ││
│  │ 7b. insight            │ ✓      │ 18.5s    │ 5,100 / 3,400     ││
│  │ 8. media               │ ✓      │ 3.2s     │ API calls only    ││
│  │ 9. dossier-plan        │ ✓      │ 6.1s     │ 1,800 / 1,200     ││
│  │ 10. writers (6x)       │ ✓      │ 42.0s    │ 12,000 / 8,500    ││
│  └────────────────────────┴────────┴──────────┴───────────────────┘│
│                                                                    │
│  TOTAL: 47m 12s | 35,434 tokens in | 24,342 tokens out            │
└────────────────────────────────────────────────────────────────────┘
```

---

### Page 3: Step Detail (`3_step_detail.py`)

**Deep Inspection** - full I/O for a single step.

```
┌────────────────────────────────────────────────────────────────────┐
│  STEP DETAIL: entity-research (Run abc123)                        │
├────────────────────────────────────────────────────────────────────┤
│  Status: ✓ completed | Duration: 15.1s | Model: gpt-4.1          │
│  Prompt Version: 3 | Tokens: 3,200 in / 2,100 out                 │
├────────────────────────────────────────────────────────────────────┤
│  [Input Variables] [Interpolated Prompt] [Raw Output] [Parsed]    │
├────────────────────────────────────────────────────────────────────┤
│  INPUT VARIABLES                                                   │
│  ┌────────────────────────────────────────────────────────────────┐│
│  │ {                                                              ││
│  │   "entity_name": "TechCorp Inc",                              ││
│  │   "signal_context": "Recently announced expansion...",         ││
│  │   "icp_config": {                                             ││
│  │     "signals": [...],                                         ││
│  │     "target_titles": ["VP Operations", "Director..."]         ││
│  │   },                                                          ││
│  │   "research_context": {...}                                   ││
│  │ }                                                              ││
│  └────────────────────────────────────────────────────────────────┘│
├────────────────────────────────────────────────────────────────────┤
│  VARIABLE LINEAGE                                                  │
│  ┌──────────────────┬────────────────┬────────────────────────────┐│
│  │ Variable         │ Source         │ From Step                  ││
│  ├──────────────────┼────────────────┼────────────────────────────┤│
│  │ entity_name      │ previous_step  │ signal-discovery           ││
│  │ signal_context   │ previous_step  │ signal-discovery           ││
│  │ icp_config       │ client_config  │ clients table              ││
│  │ research_context │ client_config  │ clients table              ││
│  └──────────────────┴────────────────┴────────────────────────────┘│
├────────────────────────────────────────────────────────────────────┤
│  [Re-run This Step]  [Copy Input as Test Fixture]  [View Prompt]  │
└────────────────────────────────────────────────────────────────────┘
```

---

### Page 4: Claims Browser (`4_claims.py`)

**Claims Inspection** - view claims across the pipeline.

```
┌────────────────────────────────────────────────────────────────────┐
│  CLAIMS BROWSER                                                    │
├────────────────────────────────────────────────────────────────────┤
│  Run: [abc123 - Acme Corp ▼]  Stage: [All ▼]  Type: [All ▼]       │
├────────────────────────────────────────────────────────────────────┤
│  RAW CLAIMS (before merge)                                         │
│  ┌────────┬──────────┬─────────────────────────┬────────┬────────┐│
│  │ ID     │ Type     │ Statement               │ Source │ Step   ││
│  ├────────┼──────────┼─────────────────────────┼────────┼────────┤│
│  │ er_001 │ ENTITY   │ HQ in Austin, TX        │ website│ entity ││
│  │ er_002 │ METRIC   │ Revenue $50M (2024)     │ SEC    │ entity ││
│  │ er_003 │ CONTACT  │ John Smith is CTO       │ LinkedIn│ entity││
│  │ cd_001 │ CONTACT  │ Jane Doe is VP Ops      │ LinkedIn│ contact││
│  │ cd_002 │ CONTACT  │ John Smith, Chief Tech  │ website│ contact││
│  │ el_001 │ SIGNAL   │ Expansion to Denver     │ news   │ enrich ││
│  │ ...    │          │                         │        │        ││
│  └────────┴──────────┴─────────────────────────┴────────┴────────┘│
├────────────────────────────────────────────────────────────────────┤
│  MERGED CLAIMS (after insight step)                                │
│  ┌───────────┬──────────┬─────────────────────────┬──────────────┐│
│  │ Merged ID │ Type     │ Statement               │ Reconciled   ││
│  ├───────────┼──────────┼─────────────────────────┼──────────────┤│
│  │ MERGED_01 │ CONTACT  │ John Smith is CTO       │ er_003+cd_002││
│  │ MERGED_02 │ ENTITY   │ HQ in Austin, TX        │ er_001       ││
│  │ MERGED_03 │ SIGNAL   │ Expansion to Denver     │ el_001       ││
│  └───────────┴──────────┴─────────────────────────┴──────────────┘│
├────────────────────────────────────────────────────────────────────┤
│  RESOLVED OBJECTS                                                  │
│  Contacts: 2 resolved | Timelines: 1 | Conflicts: 0               │
│                                                                    │
│  [View Contact Resolution Graph]  [View Claim Routing]            │
└────────────────────────────────────────────────────────────────────┘
```

---

## Database Tables (Required)

The dashboard reads/writes these tables (see [CLAIMS_STORAGE_SCHEMA.md](./CLAIMS_STORAGE_SCHEMA.md) for claims tables):

### Prompt Management

```sql
-- Prompt Registry
CREATE TABLE v2_prompts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_id TEXT UNIQUE NOT NULL,       -- "entity-research"
    name TEXT NOT NULL,                    -- "Entity Research"
    stage TEXT NOT NULL,                   -- "FIND LEAD"
    step TEXT NOT NULL,                    -- "3"
    produces_claims BOOLEAN DEFAULT false,
    merges_claims BOOLEAN DEFAULT false,
    produces_context_pack BOOLEAN DEFAULT false,
    model TEXT DEFAULT 'gpt-4.1',
    temperature NUMERIC(3,2) DEFAULT 0.7,
    max_tokens INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Prompt Version History
CREATE TABLE v2_prompt_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_id TEXT NOT NULL REFERENCES v2_prompts(prompt_id),
    version_number INTEGER NOT NULL,
    content TEXT NOT NULL,                 -- Full prompt with {{variables}}
    change_notes TEXT,
    created_by TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(prompt_id, version_number)
);
```

### Execution Tracking

```sql
-- Pipeline Runs
CREATE TABLE v2_pipeline_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id),
    dossier_id UUID,
    seed JSONB,
    status TEXT DEFAULT 'pending',         -- pending | running | completed | failed
    current_step TEXT,
    steps_completed TEXT[] DEFAULT '{}',
    config JSONB DEFAULT '{}',
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Step Runs (I/O capture)
CREATE TABLE v2_step_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline_run_id UUID NOT NULL REFERENCES v2_pipeline_runs(id),
    step TEXT NOT NULL,
    prompt_id TEXT REFERENCES v2_prompts(prompt_id),
    prompt_version INTEGER,
    status TEXT DEFAULT 'pending',
    input_variables JSONB DEFAULT '{}',
    interpolated_prompt TEXT,              -- Prompt after variable substitution
    raw_output TEXT,                       -- Raw LLM response
    parsed_output JSONB,                   -- Parsed JSON output
    model TEXT,
    tokens_in INTEGER,
    tokens_out INTEGER,
    duration_ms INTEGER,
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Variable Lineage (trace where each input came from)
CREATE TABLE v2_variable_lineage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    step_run_id UUID NOT NULL REFERENCES v2_step_runs(id),
    variable_name TEXT NOT NULL,
    source_type TEXT NOT NULL,             -- client_config | previous_step | seed | static
    source_step TEXT,
    source_step_run_id UUID REFERENCES v2_step_runs(id),
    value_preview TEXT,                    -- First 500 chars for display
    created_at TIMESTAMPTZ DEFAULT now()
);
```

### Helpful Views

```sql
-- Last run per prompt (for dashboard display)
CREATE VIEW v2_prompt_last_runs AS
SELECT DISTINCT ON (sr.prompt_id, pr.client_id)
    sr.prompt_id,
    pr.client_id,
    sr.id AS step_run_id,
    sr.status,
    sr.input_variables,
    sr.parsed_output AS output,
    sr.interpolated_prompt,
    sr.started_at,
    sr.duration_ms,
    sr.tokens_in,
    sr.tokens_out,
    sr.error_message
FROM v2_step_runs sr
JOIN v2_pipeline_runs pr ON pr.id = sr.pipeline_run_id
WHERE sr.prompt_id IS NOT NULL
ORDER BY sr.prompt_id, pr.client_id, sr.started_at DESC;

-- Pipeline run summary (for runs list)
CREATE VIEW v2_pipeline_run_summary AS
SELECT
    pr.id,
    pr.client_id,
    c.name AS client_name,
    pr.status,
    pr.current_step,
    array_length(pr.steps_completed, 1) AS steps_completed_count,
    (SELECT COUNT(*) FROM v2_prompts WHERE is_active) AS total_steps,
    EXTRACT(EPOCH FROM (pr.completed_at - pr.started_at)) AS duration_seconds,
    SUM(sr.tokens_in) AS total_tokens_in,
    SUM(sr.tokens_out) AS total_tokens_out,
    pr.created_at
FROM v2_pipeline_runs pr
LEFT JOIN clients c ON c.id = pr.client_id
LEFT JOIN v2_step_runs sr ON sr.pipeline_run_id = pr.id
GROUP BY pr.id, c.name
ORDER BY pr.created_at DESC;
```

---

## API Endpoints (for Dashboard)

```python
# api/admin.py

@router.get("/prompts")
def list_prompts() -> list[PromptSummary]:
    """List all prompts with metadata."""

@router.get("/prompts/{prompt_id}")
def get_prompt(prompt_id: str) -> PromptDetail:
    """Get prompt with current content and version history."""

@router.get("/prompts/{prompt_id}/versions")
def get_prompt_versions(prompt_id: str) -> list[PromptVersion]:
    """Get all versions of a prompt."""

@router.put("/prompts/{prompt_id}")
def update_prompt(prompt_id: str, content: str, notes: str = None) -> PromptVersion:
    """Create new version of prompt."""

@router.post("/prompts/{prompt_id}/test")
def test_prompt(prompt_id: str, input_vars: dict, model: str = None) -> StepRunResult:
    """Run prompt in isolation with provided input."""

@router.get("/runs")
def list_runs(client_id: str = None, status: str = None, limit: int = 50) -> list[PipelineRunSummary]:
    """List pipeline runs with filters."""

@router.get("/runs/{run_id}")
def get_run(run_id: str) -> PipelineRunDetail:
    """Get full run detail with all steps."""

@router.get("/runs/{run_id}/steps/{step}")
def get_step_detail(run_id: str, step: str) -> StepRunDetail:
    """Get detailed I/O for a single step."""

@router.get("/runs/{run_id}/claims")
def get_run_claims(run_id: str) -> ClaimsSummary:
    """Get all claims for a run (raw + merged)."""

@router.post("/fixtures/capture")
def capture_fixture(step_run_id: str, name: str) -> TestFixture:
    """Save step input as test fixture."""
```

---

## Streamlit App Structure

```
admin/
├── app.py                    # Main entry point
├── pages/
│   ├── 1_prompts.py          # Prompt editing & testing
│   ├── 2_runs.py             # Pipeline run history
│   ├── 3_step_detail.py      # Deep step inspection
│   └── 4_claims.py           # Claims browser
├── components/
│   ├── prompt_editor.py      # Monaco editor wrapper
│   ├── json_viewer.py        # Formatted JSON display
│   ├── claims_table.py       # Claims grid component
│   └── diff_viewer.py        # Version diff display
└── db/
    ├── __init__.py
    └── repository.py         # Database queries
```

---

## Key User Workflows

### 1. Edit and Test a Prompt

1. Select prompt from sidebar
2. Edit content in editor
3. Click "Save Version" (with optional notes)
4. Click "Run Step (Use Last Input)"
5. View output in right panel
6. If claims step, inspect claims table
7. Repeat until satisfied

### 2. Debug a Failed Run

1. Go to Pipeline Runs page
2. Filter by status = "failed"
3. Click on failed run
4. Identify which step failed
5. Click on step to see full I/O
6. View error message and interpolated prompt
7. Go to Prompts page, fix issue
8. Re-run step in isolation

### 3. Compare Prompt Versions

1. Select prompt from sidebar
2. Click version dropdown
3. Select two versions to compare
4. View diff in diff viewer
5. Run both versions with same input
6. Compare outputs side-by-side

### 4. Trace Variable Origins

1. Go to step detail page
2. View "Variable Lineage" section
3. See which step produced each input variable
4. Click to navigate to source step
5. Understand data flow through pipeline

---

## Success Criteria

| Criteria | Measure |
|----------|---------|
| **Prompt editing** | Can edit any prompt, save versions, see history |
| **I/O transparency** | Every step shows exact input → prompt → output |
| **Step isolation** | Can run any step using last state or custom input |
| **Claims visibility** | Can see all claims, merges, resolutions for any run |
| **Version control** | Can compare versions, see diffs, revert if needed |
| **Performance** | Page load < 2s, step execution feedback immediate |

---

## Implementation Order

1. **Database migration** - Create v2_* tables
2. **API endpoints** - `/prompts`, `/runs`, `/steps` CRUD
3. **Page 1: Prompts** - Core editing/testing workflow
4. **Page 2: Runs** - Pipeline run listing
5. **Page 3: Step Detail** - Deep I/O inspection
6. **Page 4: Claims** - Claims browser
7. **Polish** - Diff viewer, lineage tracing, fixtures

---

## Related Documents

- [CLAIMS_SYSTEM.md](./CLAIMS_SYSTEM.md) - How claims work in the pipeline
- [CLAIMS_STORAGE_SCHEMA.md](./CLAIMS_STORAGE_SCHEMA.md) - Database schema for claims
- [MIGRATION_PLAN.md](../MIGRATION_PLAN.md) - Full migration plan (Phase 6)
