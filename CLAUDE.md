# Automations

Central automation server for scrapers, research tasks, and background jobs.

## Quick Links

| Resource | URL |
|----------|-----|
| **Droplet** | `64.225.120.95` (SSH: `root@64.225.120.95`) |
| **API Docs** | http://64.225.120.95:8000/docs |
| **RQ Dashboard** | http://64.225.120.95:9181 |
| **GitHub** | https://github.com/contechjohnson/automations |

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

## Architecture

```
automations/
├── api/                  # FastAPI endpoints
│   ├── main.py           # Job submission, status
│   └── registry.py       # Automation registry CRUD
├── workers/
│   ├── ai.py             # LLM calls (Chat Completions + Responses API)
│   ├── agent.py          # OpenAI Agent SDK with Firecrawl tools
│   ├── logger.py         # Supabase execution logging
│   ├── runner.py         # Dynamic worker runner
│   ├── templates/        # Reusable scraper templates
│   ├── scrapers/         # Custom scrapers
│   └── research/         # Research workers
├── prompts/              # Markdown prompt files ({{var}} interpolation)
├── database/             # Supabase schema
└── scripts/              # Utility scripts
```

---

## AI Abstraction Layer

### Simple LLM Calls (`workers/ai.py`)

```python
from workers.ai import ai, prompt, research

# Direct call
result = ai("What is 2+2?", model="gpt-4.1")

# With prompt file + logging
result = prompt(
    "find-lead.entity-research",
    variables={"lead": {...}, "clientName": "Acme"},
    model="gpt-5.2",
    log=True,  # Logs to Supabase execution_logs
    tags=["test", "entity-research"]
)

# Deep research (background mode - returns response_id for polling)
result = prompt(
    "find-lead.entity-research",
    variables={...},
    model="o4-mini-deep-research",
    background=True
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
    "find-lead.entity-research",
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
| `o4-mini-deep-research` | Responses API | Web research (5-10 min) |
| `gemini-2.5-flash` | Gemini | Fast, grounded search |

---

## Prompt Files

Prompts live in `prompts/` as markdown files with `{{variable}}` interpolation.

```markdown
# prompts/find-lead.entity-research.md

Research this company: {{lead}}

Client context: {{clientName}}
```

**Naming convention:** `{automation-slug}.{step}.md`

---

## Execution Logging

All executions can be logged to Supabase `execution_logs` table:

```python
# Automatic via log=True parameter
result = prompt("my-prompt", vars, model="gpt-4.1", log=True, tags=["test"])

# Manual via ExecutionLogger
from workers.logger import ExecutionLogger

log = ExecutionLogger("scrapers.permits", input_params)
log.note("Testing new endpoint")
log.tag("test", "permits")

try:
    result = do_work()
    log.success(result)
except Exception as e:
    log.fail(e)
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

## Testing Locally

```bash
# Run a prompt test
python test_entity_research.py gpt-4.1

# Run API locally
uvicorn api.main:app --reload --port 8000
```

---

## Supabase Tables

| Table | Purpose |
|-------|---------|
| `automations` | Registry of available automations |
| `automation_runs` | Execution history |
| `execution_logs` | Detailed AI execution logs (inputs/outputs) |

---

## SSH Access

```bash
ssh root@64.225.120.95
# Password in 1Password or directives/automations-droplet.md
```
