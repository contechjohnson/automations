---
name: querying-database
description: Query the automations database for logs, automation registry, and runs. Use when user asks about execution history, wants to check logs, list automations, debug failures, or when Supabase MCP is unavailable. Skip if Supabase MCP tools are available.
allowed-tools: Read, Bash, Glob
---

# Querying the Automations Database

Query execution logs, automations registry, and run history via the API when Supabase MCP is unavailable.

## When to Use This Skill

- **MCP unavailable**: Web version of Claude Code, or MCP not configured
- **Quick lookups**: "What automations are registered?", "Show recent logs"
- **Debugging**: "Why did entity-research fail?", "What's the error?"
- **Stats**: "How many runs today?", "Success rate for scraper X"

## When NOT to Use This Skill

If Supabase MCP tools are available (`mcp__plugin_supabase_supabase__*`), use those directly for more flexibility. This skill is a fallback.

---

## Quick Reference: API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/logs` | GET | List recent execution logs |
| `/logs/{id}` | GET | Get full log with input/output |
| `/automations` | GET | List registered automations |
| `/automations/{slug}` | GET | Get automation details |
| `/automations/register` | POST | Register new automation |

**Base URL**: `https://api.columnline.dev`

---

## Common Queries

### 1. Recent Execution Logs

```bash
# Last 10 logs
curl -s "https://api.columnline.dev/logs?limit=10" | python3 -m json.tool

# Filter by automation
curl -s "https://api.columnline.dev/logs?automation_slug=entity-research&limit=5"

# Filter by status
curl -s "https://api.columnline.dev/logs?status=failed&limit=10"

# Filter by tag
curl -s "https://api.columnline.dev/logs?tag=gpt-4.1&limit=10"
```

### 2. Get Full Log Details

```bash
# Get complete log entry with full input/output
curl -s "https://api.columnline.dev/logs/{log_id}" | python3 -m json.tool
```

### 3. List Registered Automations

```bash
# All automations
curl -s "https://api.columnline.dev/automations" | python3 -m json.tool

# Filter by type
curl -s "https://api.columnline.dev/automations?type=research"

# Filter by status
curl -s "https://api.columnline.dev/automations?status=active"
```

### 4. Get Automation Details

```bash
curl -s "https://api.columnline.dev/automations/entity-research" | python3 -m json.tool
```

---

## Database Schema Reference

### execution_logs Table

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Log entry ID |
| `automation_slug` | VARCHAR | Links to automation |
| `worker_name` | VARCHAR | e.g., `ai.prompt.gpt-4.1` |
| `started_at` | TIMESTAMP | When it started |
| `completed_at` | TIMESTAMP | When it finished |
| `runtime_seconds` | FLOAT | Duration |
| `status` | VARCHAR | `running`, `success`, `failed` |
| `input` | JSONB | Full input parameters |
| `output` | JSONB | Full response |
| `error` | JSONB | Error details if failed |
| `tags` | TEXT[] | Filterable tags |

### automations Table

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Automation ID |
| `slug` | VARCHAR | Unique identifier |
| `name` | VARCHAR | Display name |
| `type` | VARCHAR | `scraper`, `research`, `enrichment`, `workflow` |
| `category` | VARCHAR | `permits`, `intelligence`, etc. |
| `status` | VARCHAR | `draft`, `active`, `paused`, `deprecated` |
| `worker_path` | VARCHAR | Path to worker file |
| `last_run_at` | TIMESTAMP | Last execution time |
| `last_run_status` | VARCHAR | Last run result |
| `run_count` | INT | Total runs |
| `success_count` | INT | Successful runs |
| `fail_count` | INT | Failed runs |

### automation_runs Table

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Run ID |
| `automation_id` | UUID | FK to automations |
| `started_at` | TIMESTAMP | Start time |
| `completed_at` | TIMESTAMP | End time |
| `duration_seconds` | FLOAT | Runtime |
| `status` | VARCHAR | `queued`, `running`, `success`, `failed` |
| `records_found` | INT | Items found |
| `records_new` | INT | New items |
| `error_message` | TEXT | Error if failed |
| `result` | JSONB | Full result data |

---

## Helper Script

For complex queries, use the helper script:

**Note:** The helper script requires local Python with dependencies. For web Claude Code, use the API endpoints above (no credentials needed).

```bash
# Run from project root
python3 .claude/skills/querying-database/scripts/query_db.py --help

# Examples:
python3 .claude/skills/querying-database/scripts/query_db.py logs --limit 5
python3 .claude/skills/querying-database/scripts/query_db.py logs --status failed
python3 .claude/skills/querying-database/scripts/query_db.py automations --type research
python3 .claude/skills/querying-database/scripts/query_db.py log-detail <log_id>
```

---

## Direct SQL (If Needed)

If you need raw SQL access and have Supabase credentials:

```python
from supabase import create_client
import os

supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_ROLE_KEY"]
)

# Recent logs
logs = supabase.table("execution_logs") \
    .select("*") \
    .order("started_at", desc=True) \
    .limit(10) \
    .execute()

# Failed logs
failed = supabase.table("execution_logs") \
    .select("*") \
    .eq("status", "failed") \
    .order("started_at", desc=True) \
    .execute()

# Automations by type
research = supabase.table("automations") \
    .select("slug, name, status, last_run_at") \
    .eq("type", "research") \
    .execute()
```

---

## Example Workflows

### Debug a Failed Run

1. Find failed logs:
   ```bash
   curl -s "https://api.columnline.dev/logs?status=failed&limit=5"
   ```

2. Get full error details:
   ```bash
   curl -s "https://api.columnline.dev/logs/{id}" | python3 -m json.tool
   ```

3. Check the error field for traceback and message

### Check Automation Health

1. List automations with stats:
   ```bash
   curl -s "https://api.columnline.dev/automations"
   ```

2. Look at `success_count`, `fail_count`, `last_run_status`

3. For problematic ones, dig into recent logs

### Find Logs by Tag

```bash
# All entity-research runs
curl -s "https://api.columnline.dev/logs?tag=entity-research&limit=20"

# All GPT-4.1 calls
curl -s "https://api.columnline.dev/logs?tag=gpt-4.1&limit=20"
```

---

## Writing to the Database

### Register an Automation

```bash
curl -X POST "https://api.columnline.dev/automations/register" \
  -H "Content-Type: application/json" \
  -d '{
    "slug": "my-automation",
    "name": "My Automation",
    "type": "research",
    "category": "intelligence",
    "worker_path": "workers/my_automation.py",
    "tags": ["research", "gpt-4.1"]
  }'
```

### Update Automation Status

```bash
curl -X PATCH "https://api.columnline.dev/automations/my-automation" \
  -H "Content-Type: application/json" \
  -d '{"status": "active"}'
```

---

## Views Available

These pre-built views simplify common queries:

| View | Purpose |
|------|---------|
| `v_recent_logs` | Last 50 logs with truncated previews |
| `v_failed_logs` | Recent failed runs |
| `v_active_scrapers` | Active scraper automations |
| `v_failed_automations` | Automations with recent failures |
| `v_automations_by_state` | Geographic breakdown |

Access via Supabase client or raw SQL.

---

## Resources

**Repository:** [contechjohnson/automations](https://github.com/contechjohnson/automations)

### Web vs Local Usage

| Method | Web Claude | Local Claude | Credentials |
|--------|-----------|--------------|-------------|
| API endpoints (`/logs`, `/automations`) | ✅ Works | ✅ Works | None needed |
| Helper script | ❌ Requires Python | ✅ Works | None |
| Direct Supabase SQL | ❌ Needs env vars | ✅ Works | `SUPABASE_*` from `.env` |

**For web Claude Code:** Use the API endpoints - they work without any credentials and provide full query capabilities.

### Files Referenced by This Skill

| Resource | Path |
|----------|------|
| Helper Script | `.claude/skills/querying-database/scripts/query_db.py` |

### API Endpoints

| Endpoint | URL |
|----------|-----|
| Production API | `https://api.columnline.dev` |
| Logs Endpoint | `https://api.columnline.dev/logs` |
| Automations Endpoint | `https://api.columnline.dev/automations` |

### Environment Variables (for Direct SQL only)

| Variable | Purpose |
|----------|---------|
| `SUPABASE_URL` | Database URL - from `.env` locally |
| `SUPABASE_SERVICE_ROLE_KEY` | Admin access - from `.env` locally |

### Related Skills

| Skill | Purpose |
|-------|---------|
| `building-automations` | Create automations that log to this database |
| `using-rq-workers` | Background jobs also log here |
