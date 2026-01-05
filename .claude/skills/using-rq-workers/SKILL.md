---
name: using-rq-workers
description: Queue and run background jobs with RQ (Redis Queue). Use when creating long-running automations, background tasks, jobs that need progress tracking, or when user mentions "queue job", "background", "RQ", "Redis", "async worker", "long running", "job queue", or "progress updates".
allowed-tools: Read, Write, Glob, Grep, Bash
---

# Using RQ Workers

Queue and process background jobs with Redis Queue (RQ).

## When to Use RQ

**Use RQ when ANY of these apply:**

| Trigger | Example | Why RQ? |
|---------|---------|---------|
| **Long-running (>30s)** | Deep research, large scrapes | HTTP timeout would kill it |
| **Chained prompts** | Step 1 → Step 2 → Step 3 | Each step can be retried independently |
| **Multiple API calls** | Scraper hitting 50 pages | Rate limiting, partial progress |
| **Webhook chains** | Service A → Service B → Service C | Async handoffs, retry on failure |
| **Rate-limited APIs** | Google Maps, LinkedIn | Queue respects rate limits |
| **Progress needed** | User wants % complete | `job.meta` provides real-time updates |
| **Retryable work** | Network-dependent tasks | Failed jobs can be retried from dashboard |

**DON'T use RQ for:**
- Simple single prompts (<30s)
- Synchronous API responses needed immediately
- One-off tests/debugging

## Architecture Overview

```
┌──────────┐     ┌─────────────┐     ┌──────────┐
│   API    │────▶│ Redis Queue │◀────│  Worker  │
│  (8000)  │     │             │     │          │
└──────────┘     └─────────────┘     └──────────┘
                        │
                        ▼
              ┌─────────────────┐
              │  RQ Dashboard   │
              │     (9181)      │
              └─────────────────┘
```

**Services (from docker-compose.yml):**
- `api` - FastAPI, receives requests, queues jobs
- `worker` - RQ worker, processes jobs from queue
- `dashboard` - Web UI at port 9181 for monitoring

## Quick Start

### 1. Queue a Job

```python
from redis import Redis
from rq import Queue

redis_conn = Redis.from_url(os.environ["REDIS_URL"])
q = Queue(connection=redis_conn)

# Queue the job
job = q.enqueue(
    "workers.runner.run_automation",  # Function path
    "my-automation-slug",              # Args
    job_timeout="30m"                  # Set timeout for long jobs
)

return {
    "job_id": job.id,
    "status": "queued"
}
```

### 2. Check Job Status

```python
from rq.job import Job

job = Job.fetch(job_id, connection=redis_conn)

status = {
    "id": job.id,
    "status": job.get_status(),  # queued, started, finished, failed
    "progress": job.meta,         # Your custom progress
    "result": job.result if job.is_finished else None,
    "error": str(job.exc_info) if job.is_failed else None
}
```

### 3. Monitor in Dashboard

- **URL:** http://64.225.120.95:9181 (HTTP only - access from trusted network)
- View queues, jobs, workers
- See failed jobs with tracebacks
- Retry failed jobs from UI

**Note:** The RQ Dashboard is internal-only (HTTP). Access directly when on the network or via SSH tunnel.

## Progress Updates (Streamable)

Workers can update progress visible in dashboard and via polling.

```python
from rq import get_current_job

def my_worker(items: list):
    job = get_current_job()

    for i, item in enumerate(items):
        # Update progress - visible in RQ Dashboard
        job.meta = {
            "progress": f"{i+1}/{len(items)}",
            "percent": int((i+1) * 100 / len(items)),
            "current_item": item.get("name", "unknown")
        }
        job.save_meta()

        # Do the work
        process(item)

    return {"processed": len(items)}
```

**Client polling:**
```python
# Poll job.meta for progress
while True:
    job = Job.fetch(job_id, connection=redis)
    if job.get_status() in ["finished", "failed"]:
        break
    print(f"Progress: {job.meta.get('percent', 0)}%")
    time.sleep(2)
```

## Common Timeouts

| Task Type | Timeout | Notes |
|-----------|---------|-------|
| Default | 180s | RQ default, often too short |
| Standard job | `5m` | Most automations |
| Deep research | `30m` | o4-mini-deep-research |
| Large batch | `1h` | Batch processing |

```python
job = q.enqueue(func, arg, job_timeout="30m")
```

## Result TTL

Control how long results are kept:

```python
job = q.enqueue(
    func,
    arg,
    result_ttl=3600,      # Keep result for 1 hour
    failure_ttl=86400,    # Keep failed jobs for 24 hours
)
```

## Existing Infrastructure

### workers/runner.py

Dynamic automation runner with progress support:

```python
def run_automation(slug: str, override_config: dict = None) -> dict:
    job = get_current_job()

    def update_progress(message: str, percent: int):
        if job:
            job.meta = {"message": message, "percent": percent}
            job.save_meta()

    # ... runs automation from registry
```

### Template Runners

Add new automation types to `template_runners` dict:

```python
template_runners = {
    "arcgis_permits": "workers.templates.arcgis_permits:run",
    "entity_research": "workers.research.entity_research:run_entity_research",
    # Add yours here
    "my_template": "workers.my_category.my_worker:run",
}
```

### API Endpoints

- `POST /test/prompt` - Test prompt (sync or background)
- `POST /research/start` - Start deep research
- `POST /research/poll` - Poll research status

## RQ Dashboard Guide

**URL:** http://64.225.120.95:9181

### Dashboard Views

| Tab | Shows |
|-----|-------|
| **Overview** | All queues, worker status |
| **Jobs** | List of all jobs |
| **Workers** | Active worker processes |
| **Failed** | Failed jobs with tracebacks |

### Common Actions

1. **View job details:** Click job ID
2. **See progress:** Check job.meta in details
3. **Retry failed:** Click "Requeue" button
4. **Delete failed:** Click "Delete" button

## Scaling Workers

```bash
# Scale to 3 workers
docker-compose up -d --scale worker=3
```

Each worker processes jobs independently. More workers = higher throughput.

## Debugging Failed Jobs

### 1. Check Dashboard

Go to Failed tab, click job, see traceback.

### 2. Query Redis

```bash
# Connect to Redis
redis-cli -u $REDIS_URL

# List failed jobs
LRANGE rq:queue:failed 0 -1
```

### 3. Check Worker Logs

```bash
# On droplet
journalctl -u automations-worker -f

# Or in Docker
docker-compose logs -f worker
```

## Integration with Logging

RQ jobs should still log to Supabase:

```python
from rq import get_current_job
from workers.logger import ExecutionLogger

def my_rq_worker(config: dict):
    job = get_current_job()

    log = ExecutionLogger(
        worker_name="rq.my_worker",
        automation_slug=config.get("slug"),
        input_data=config,
        tags=["rq", config.get("slug")]
    )

    def update_progress(msg: str, pct: int):
        if job:
            job.meta = {"message": msg, "percent": pct}
            job.save_meta()
        log.meta("progress", {"message": msg, "percent": pct})

    try:
        update_progress("Starting", 0)
        result = do_work()
        update_progress("Complete", 100)
        return log.success(result)
    except Exception as e:
        log.fail(e)
```

## Anti-Patterns

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| No timeout | Job runs forever | Set `job_timeout` |
| No progress | Can't monitor | Use `job.meta` |
| No logging | Can't debug | Use ExecutionLogger |
| Sync deep research | Times out | Use RQ background job |

## Self-Annealing

After any RQ issue:
1. Document in `LEARNINGS.md`
2. Update this skill if pattern needs change
3. Check if common issue needs template update

See `LEARNINGS.md` for known issues and fixes.

---

## Resources

**Repository:** [contechjohnson/automations](https://github.com/contechjohnson/automations)

### Infrastructure URLs

| Resource | URL | Notes |
|----------|-----|-------|
| Production API | `https://api.columnline.dev` | Primary endpoint |
| Health Check | `https://api.columnline.dev/health` | - |
| Test Prompt | `https://api.columnline.dev/test/prompt` | POST endpoint |
| Logs | `https://api.columnline.dev/logs` | - |
| RQ Dashboard | `http://64.225.120.95:9181` | HTTP only, internal access |
| Droplet SSH | `root@64.225.120.95` | For debugging |

### Files Referenced by This Skill

| Resource | Path |
|----------|------|
| Runner | `workers/runner.py` |
| Logger | `workers/logger.py` |

### Environment Variables Required

| Variable | Purpose |
|----------|---------|
| `REDIS_URL` | Redis connection - from `.env` locally, paste directly in web |

**Credentials:** Add `CREDENTIALS.md` to your Claude project for API keys. Cannot be stored in repo due to GitHub secret scanning.

### Related Skills

| Skill | Purpose |
|-------|---------|
| `building-automations` | Create workers that RQ will run |
| `querying-database` | View execution logs from RQ jobs |
