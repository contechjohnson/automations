# Using RQ Workers Learnings

Self-annealing log for RQ/Redis queue usage patterns.

## Format

Each entry: `DATE | ISSUE | ROOT CAUSE | FIX | PREVENTION`

---

## 2025-01-04 | Initial Setup

Created skill for RQ (Redis Queue) background job processing.

Key infrastructure already in place:
- `docker-compose.yml` has api, worker, dashboard services
- `workers/runner.py` has `run_automation()` with progress support
- RQ Dashboard at port 9181

---

## Key Insights

### Default Timeout Too Short

**Issue:** Long jobs failing with timeout
**Root Cause:** RQ default timeout is 180 seconds
**Fix:** Set explicit `job_timeout="30m"` for long jobs
**Prevention:** Always specify timeout based on expected duration

### Progress Updates Important

**Issue:** Can't tell if job is stuck or working
**Root Cause:** No progress updates
**Fix:** Use `job.meta` with `save_meta()` for progress
**Prevention:** All long jobs should update progress

### Dual Logging

**Issue:** RQ job progress not in Supabase
**Root Cause:** Only updating job.meta, not logging
**Fix:** Update both job.meta AND log.meta()
**Prevention:** Pattern shows updating both

---

## RQ-Specific Issues

### Worker Not Processing

**Issue:** Jobs stuck in queue
**Root Cause:** Worker crashed or not started
**Fix:** `systemctl restart automations-worker`
**Prevention:** Monitor worker health

### Redis Connection Errors

**Issue:** Connection refused errors
**Root Cause:** Redis not running or wrong URL
**Fix:** Check `REDIS_URL` env var, verify Redis is up
**Prevention:** Health check in startup

---

## New Learnings

_Add new learnings below as they occur_

### [YYYY-MM-DD] | [Issue Title]

**Issue:** What happened
**Root Cause:** Why it happened
**Fix:** What was done
**Prevention:** How to avoid in future
