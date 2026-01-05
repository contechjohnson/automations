# Building Automations Learnings

Self-annealing log for automation implementation patterns.

## Format

Each entry: `DATE | ISSUE | ROOT CAUSE | FIX | PREVENTION`

---

## 2025-01-04 | Initial Setup

Created for Python automations project. Inspired by Columnline's `authoring-execution-scripts` skill but adapted for Python and this project's patterns.

Key design decisions:
- Mandatory `log=True` on all prompt() calls
- ExecutionLogger for multi-step workers
- Deep research MUST use background mode
- All logs go to Supabase `execution_logs` table

---

## Key Insights

### Logging is Critical

**Issue:** Can't debug failed automations
**Root Cause:** Logging was optional
**Fix:** Made `log=True` mandatory, no exceptions
**Prevention:** Skill emphasizes logging throughout

### Deep Research Timeouts

**Issue:** Deep research calls timing out
**Root Cause:** Sync calls to 5-10 min operations
**Fix:** Always use `background=True` for deep research models
**Prevention:** Documented in model table, skill warns about this

### Tags for Filtering

**Issue:** Can't find logs for specific automations
**Root Cause:** No tags on log entries
**Fix:** Always include tags: [automation_slug, model, category]
**Prevention:** All patterns show tags parameter

---

## New Learnings

_Add new learnings below as they occur_

---

### 2025-01-04 | Tools Are OPT-IN, Not Default

**Issue:** Confusion about when to use Agent SDK vs simple prompts
**Root Cause:** Skills didn't clearly state that tools are optional
**Fix:** Added decision tree and clarified that `prompt()` is the default choice. Only use `agent_prompt()` when external data is explicitly needed.
**Prevention:**
- Decision tree added to SKILL.md
- "IMPORTANT: Tools Are OPT-IN" section added
- Default approach emphasized: start with `prompt()`, add tools only when necessary

### 2025-01-04 | Provider-Agnostic Architecture Clarified

**Issue:** Unclear which API to use (Chat Completions vs Responses API vs Agent SDK)
**Root Cause:** OpenAI has multiple APIs, documentation scattered
**Fix:** Documented the architecture:
- `prompt()` uses Chat Completions for standard models, Responses API for deep research
- `agent_prompt()` uses Agent SDK (which internally uses Responses API)
- Provider table added showing OpenAI, Gemini, Perplexity options
**Prevention:** Provider-Agnostic Architecture section added to SKILL.md

### 2025-01-04 | execution_logs Table Never Created

**Issue:** All logging calls were failing silently
**Root Cause:** Schema file `database/execution_logs.sql` existed but was never applied to Supabase
**Fix:** Applied migration to create table, indexes, functions, and views
**Prevention:** Integration Checklist now emphasizes verifying in `execution_logs` table

---

### [YYYY-MM-DD] | [Issue Title]

**Issue:** What happened
**Root Cause:** Why it happened
**Fix:** What was done
**Prevention:** How to avoid in future
