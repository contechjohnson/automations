# Automations

Central automation server for scrapers, research tasks, and background jobs.

## Philosophy

This project follows a **directive-orchestration-execution** framework:

1. **Directives** define what an automation should do (contracts, behavior) in `directives/`
2. **Skills** guide Claude in building automations consistently in `.claude/skills/`
3. **Workers** implement the actual logic using AI abstractions in `workers/`

### Core Principles

- **Skills over slash commands** - Natural language triggers, no memorization needed
- **Directives as contracts** - Define inputs, outputs, behavior in markdown
- **Provider-agnostic AI** - Models/prompts hot-swappable via `workers/ai.py`
- **FULL TRACE LOGGING** - Every LLM call logs inputs, outputs, timing to Supabase (non-negotiable)
- **RQ for background jobs** - Long-running tasks queue via Redis, monitor via Dashboard
- **Self-annealing** - Every skill has LEARNINGS.md for continuous improvement

### New Here?

See [docs/INFRASTRUCTURE-COOKBOOK.md](docs/INFRASTRUCTURE-COOKBOOK.md) for the complete setup guide - covers everything from DigitalOcean droplet creation to SSL configuration.

---

## Skills

Skills trigger automatically based on semantic matching. Just describe what you want.

| Skill | When It Activates |
|-------|-------------------|
| `creating-skills` | "create a skill", "make this reusable", "I keep doing this" |
| `creating-directives` | "new directive", "define automation", "standardize" |
| `building-automations` | "build automation", "implement directive", "create worker" |
| `using-rq-workers` | "queue job", "background", "RQ", "long running" |

### To build a new automation:

1. Write a directive in `directives/{slug}.md`
2. Say "build this automation" or "implement the {name} directive"
3. Claude will follow the `building-automations` skill

---

## Quick Links

| Resource | URL |
|----------|-----|
| **API (production)** | `https://api.columnline.dev` |
| **API (ngrok)** | `https://lazy-bella-unevolutional.ngrok-free.dev` |
| **API (direct)** | `http://64.225.120.95:8000` |
| **API Docs** | https://api.columnline.dev/docs |
| **RQ Dashboard** | http://64.225.120.95:9181 |
| **Droplet SSH** | `root@64.225.120.95` |
| **GitHub** | https://github.com/contechjohnson/automations |

### API URLs

| URL | When to Use | Header Required |
|-----|-------------|-----------------|
| `https://api.columnline.dev` | **Production - works everywhere** | None |
| `https://lazy-bella-unevolutional.ngrok-free.dev` | Backup/legacy | `ngrok-skip-browser-warning: true` |
| `http://64.225.120.95:8000` | Direct IP (fastest) | None |

**Use `api.columnline.dev` by default.** It has proper SSL via Caddy and works from anywhere - local, cloud, AI models, webhooks.

```bash
# Production URL (recommended)
API_URL="https://api.columnline.dev"
curl "$API_URL/health"

# Direct IP (for debugging, fastest)
curl "http://64.225.120.95:8000/health"

# ngrok (backup, requires header)
curl -H "ngrok-skip-browser-warning: true" "https://lazy-bella-unevolutional.ngrok-free.dev/health"
```

---

## Environment Setup

This project shares API keys with Columnline. The `.env` is symlinked:

```bash
# Already set up - .env points to Columnline's .env
ls -la .env  # Should show symlink to ../COLUMNLINE_AI_APP_V1/.env
```

If the symlink is missing, recreate it:
```bash
ln -sf ../COLUMNLINE_AI_APP_V1/.env .env
```

### Required Keys (from Columnline)
- `OPENAI_API_KEY` - GPT-4.1, GPT-5.2, o4-mini, deep research
- `GOOGLE_API_KEY` - Gemini models
- `FIRECRAWL_API_KEY` - Web scraping tools
- `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` - Logging to execution_logs
- `APIFY_API_KEY` - Scraper actors

---

## Temporary Files (`tmp/`)

**All test outputs, reports, downloads, and scratch files go in `tmp/`.**

This folder is gitignored (except `.gitkeep`). Use it for:
- Test run outputs (JSON, CSV, reports)
- Downloaded files and attachments
- Debug dumps and logs
- Any ephemeral artifacts

**Do NOT create files elsewhere** unless there's a clear reason (e.g., new prompt in `prompts/`, new worker in `workers/`).

```python
# Example: Save test output
output_path = "tmp/entity-research-test-2025-01-04.json"
with open(output_path, "w") as f:
    json.dump(result, f, indent=2)
```

---

## Architecture

```
automations/
├── .claude/
│   └── skills/           # Claude Code skills
│       ├── creating-skills/
│       ├── creating-directives/
│       ├── building-automations/
│       └── using-rq-workers/
├── tmp/                  # ALL temporary/test outputs go here (gitignored)
├── directives/           # Automation specifications
├── api/                  # FastAPI endpoints
│   ├── main.py           # Job submission, status
│   └── registry.py       # Automation registry CRUD
├── workers/
│   ├── ai.py             # LLM calls (Chat Completions + Responses API)
│   ├── agent.py          # OpenAI Agent SDK with Firecrawl tools
│   ├── logger.py         # Supabase execution logging
│   ├── runner.py         # Dynamic worker runner
│   ├── templates/        # Reusable scraper templates
│   └── research/         # Research workers
├── prompts/              # Markdown prompt files ({{var}} interpolation)
├── database/             # Supabase schema
└── scripts/              # Utility scripts
```

---

## AI Abstraction Layer

### Decision Flowchart: What to Use

```
Need to call an LLM?
│
├─ Single question/task, no web access needed?
│  └─ Use prompt() with log=True
│
├─ Need to search the web or scrape websites?
│  │
│  ├─ Quick web search + reasoning?
│  │  └─ Use agent_prompt(..., agent_type="research")
│  │
│  ├─ Need to scrape specific URLs?
│  │  └─ Use agent_prompt(..., agent_type="firecrawl")
│  │
│  └─ Deep research (5-10 min, comprehensive)?
│     └─ Use prompt(..., model="o4-mini-deep-research", background=True)
│
└─ Long-running or chained operations?
   └─ Use RQ (see using-rq-workers skill)
```

### Key Difference: prompt() vs agent_prompt()

| | `prompt()` | `agent_prompt()` |
|---|---|---|
| **Calls** | Single LLM call | Multiple LLM calls (turns) |
| **Tools** | None | Web search, Firecrawl scraping |
| **Speed** | Fast (seconds) | Slower (LLM decides when done) |
| **Use for** | Transform, summarize, extract | Research, scrape, verify |

### Simple LLM Calls (`workers/ai.py`)

```python
from workers.ai import ai, prompt, research

# Direct call (no logging)
result = ai("What is 2+2?", model="gpt-4.1")

# With prompt file + MANDATORY logging
result = prompt(
    "entity-research",
    variables={"lead": {...}, "clientName": "Acme"},
    model="gpt-4.1",
    log=True,  # ALWAYS use log=True
    tags=["entity-research", "gpt-4.1"]
)

# Deep research (background mode - returns response_id for polling)
result = prompt(
    "deep-research",
    variables={...},
    model="o4-mini-deep-research",
    background=True,  # Required for deep research
    log=True
)
# Poll with: poll_research(result["response_id"])
```

### Agent SDK with Tools (`workers/agent.py`)

```python
from workers.agent import run_firecrawl_agent, run_research_agent, run_full_agent

# Web search only
result = run_research_agent("Research Acme Corp", model="gpt-4.1")

# Firecrawl tools (scrape, search, map)
result = run_firecrawl_agent("Scrape acmecorp.com and summarize", model="gpt-4.1")

# Full agent (web search + Firecrawl)
result = run_full_agent("Deep research on Acme Corp", model="gpt-5.2")

# With prompt file
from workers.agent import agent_prompt
result = agent_prompt(
    "entity-research",
    variables={...},
    model="gpt-4.1",
    agent_type="firecrawl",  # "research" | "firecrawl" | "full"
    log=True
)
```

### Model Support

| Model | API | Use Case |
|-------|-----|----------|
| `gpt-4.1` | Chat Completions | Default, fast |
| `gpt-4.1-mini` | Chat Completions | Cheaper, still good |
| `gpt-5.2` | Chat Completions | Best quality |
| `o4-mini` | Chat Completions | Reasoning |
| `o4-mini-deep-research` | Responses API | Web research (5-10 min, use background=True) |
| `gemini-2.5-flash` | Gemini | Fast, grounded search |

---

## Execution Logging (NON-NEGOTIABLE)

Every automation MUST log. This provides full observability.

### Option 1: Automatic via `log=True`

```python
result = prompt("name", vars, model="gpt-4.1", log=True, tags=["tag1"])
```

### Option 2: Manual via ExecutionLogger

```python
from workers.logger import ExecutionLogger

log = ExecutionLogger(
    worker_name="scrapers.permits",
    automation_slug="va-permits",
    input_data=params,
    tags=["permits", "va"]
)

try:
    result = do_work()
    log.success(result)
except Exception as e:
    log.fail(e)
```

### What Gets Logged

| Field | Description |
|-------|-------------|
| `worker_name` | e.g., `ai.prompt.gpt-4.1` |
| `automation_slug` | e.g., `entity-research` |
| `input` | Full input parameters (JSONB) |
| `output` | Full output response (JSONB) |
| `runtime_seconds` | Execution time |
| `status` | `running`, `success`, `failed` |
| `tags` | Filterable tags |

### Observability Queries

```sql
-- Recent executions for an automation
SELECT * FROM execution_logs
WHERE automation_slug = 'my-automation'
ORDER BY started_at DESC LIMIT 10;

-- Failed jobs
SELECT * FROM v_failed_logs;

-- All runs for a tag
SELECT * FROM execution_logs WHERE 'entity-research' = ANY(tags);

-- Slow executions
SELECT * FROM execution_logs
WHERE runtime_seconds > 30
ORDER BY runtime_seconds DESC;
```

---

## Prompt Files

Prompts live in `prompts/` as markdown files with `{{variable}}` interpolation.

```markdown
# prompts/entity-research.md

Research this company: {{lead}}

Client context: {{clientName}}
```

**Naming convention:** `{automation-slug}.md` or `{automation-slug}.{step}.md`

---

## RQ Background Jobs

For long-running tasks (deep research, batch processing):

```python
from redis import Redis
from rq import Queue

redis_conn = Redis.from_url(os.environ["REDIS_URL"])
q = Queue(connection=redis_conn)

# Queue job with extended timeout
job = q.enqueue(
    "workers.runner.run_automation",
    "my-automation-slug",
    job_timeout="30m"
)
```

**Monitor:** http://64.225.120.95:9181

See `using-rq-workers` skill for full patterns.

---

## Supabase Tables

| Table | Purpose |
|-------|---------|
| `automations` | Registry of available automations |
| `automation_runs` | Job-level execution history (one per run) |
| `execution_logs` | Detail-level AI traces (one per LLM call) |

### Observability Chain

The three tables link together for full traceability:

```
automations (registry)
    │
    ├── automation_runs (job history)
    │   └── Links via: automation_id
    │   └── Written by: runner.py
    │
    └── execution_logs (LLM traces)
        └── Links via: automation_slug
        └── Written by: prompt(..., log=True)
```

**Key field:** `automation_slug` - auto-derived from prompt name (e.g., `entity-research.md` → `entity-research`)

### Registration

When building a new automation, register it so logs link properly:

```python
from workers.register import register_automation

register_automation(
    slug="entity-research",           # MUST match prompt file name
    name="Entity Research",
    type="research",                  # research | scraper | enrichment | workflow
    category="intelligence",
    worker_path="workers/research/entity.py",
    tags=["research", "gpt-4.1"]
)
```

Or via API:

```bash
curl -X POST "https://api.columnline.dev/automations/register" \
  -H "Content-Type: application/json" \
  -d '{"slug": "entity-research", "name": "Entity Research", "type": "research"}'
```

### Query Examples

```sql
-- All logs for an automation
SELECT * FROM execution_logs
WHERE automation_slug = 'entity-research'
ORDER BY started_at DESC;

-- Join automation with its logs
SELECT a.name, e.status, e.runtime_seconds, e.started_at
FROM automations a
JOIN execution_logs e ON a.slug = e.automation_slug
WHERE a.slug = 'entity-research';

-- Automation registry
SELECT slug, name, type, status FROM automations;
```

---

## Deployment

### Deploy to Droplet

```bash
ssh root@64.225.120.95
cd /opt/automations
git pull
pip install -r requirements.txt  # if deps changed
systemctl restart automations-api automations-worker
```

### View Logs

```bash
journalctl -u automations-api -f      # API logs
journalctl -u automations-worker -f   # Worker logs
```

### Services

```bash
systemctl status automations-api automations-worker automations-dashboard
systemctl restart automations-api automations-worker
```

---

## Testing Workflow

**ALWAYS test via the real API endpoint**, not local scripts. This ensures:
1. Code is deployed and running correctly
2. Logs are captured in Supabase
3. Environment matches production

### API Base URLs

```bash
# Production (recommended - works everywhere)
API_URL="https://api.columnline.dev"

# Direct IP (fastest, for debugging)
API_URL="http://64.225.120.95:8000"
```

### Standard Test Flow

```bash
# 1. Commit and push changes (auto-deploys via GitHub)
git add -A && git commit -m "Your changes" && git push

# 2. Test via API endpoint
curl -X POST "https://api.columnline.dev/test/prompt" \
  -H "Content-Type: application/json" \
  -d '{"prompt_name": "model-test", "variables": {"question": "Your test question"}, "model": "gpt-4.1-mini"}'

# 3. Verify logs were created
curl "https://api.columnline.dev/logs?limit=3"
```

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/test/prompt` | POST | Run any prompt with logging |
| `/research/start` | POST | Start deep research (background) |
| `/research/poll` | POST | Poll for deep research completion |
| `/logs` | GET | View recent execution logs |
| `/logs/{id}` | GET | Get full log entry with input/output |
| `/prompts` | GET | List available prompt files |
| `/health` | GET | Health check |

### Example: Test Model Comparison

```bash
# Test gpt-4.1-mini
curl -X POST "https://api.columnline.dev/test/prompt" \
  -H "Content-Type: application/json" \
  -d '{"prompt_name": "model-test", "variables": {"question": "What is cloud computing?"}, "model": "gpt-4.1-mini"}'

# Test gpt-4.1
curl -X POST "https://api.columnline.dev/test/prompt" \
  -H "Content-Type: application/json" \
  -d '{"prompt_name": "model-test", "variables": {"question": "What is cloud computing?"}, "model": "gpt-4.1"}'

# Compare in logs
curl "https://api.columnline.dev/logs?limit=2"
```

### Local Testing (Only When Necessary)

Use local testing only for rapid iteration before deploying:

```bash
# Run API locally
uvicorn api.main:app --reload --port 8000

# Test via local endpoint
curl -X POST "http://localhost:8000/test/prompt" ...
```

---

## SSH Access

```bash
ssh root@64.225.120.95
# Password in 1Password or directives/automations-droplet.md
```
