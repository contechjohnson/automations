# Creating Directives Learnings

Self-annealing log for directive creation and standardization.

## Format

Each entry: `DATE | ISSUE | ROOT CAUSE | FIX | PREVENTION`

---

## 2025-01-04 | Initial Setup

Adapted from Columnline project for Python-based automations.

Key changes from Columnline version:
- Updated file paths for Python project (workers/ instead of execution/)
- Simplified for Python (no TypeScript)
- Added mandatory AI Configuration section with `Log: true`
- Added Observability section emphasizing logging
- Updated prompt path to `prompts/{slug}.md`

---

## Key Insights

### Logging is Non-Negotiable

**Issue:** Missing observability for debugging
**Root Cause:** Logging was optional in original design
**Fix:** Made `Log: true` mandatory in AI Configuration
**Prevention:** Directive template includes logging by default

### Python vs TypeScript Paths

**Issue:** File paths from Columnline don't match automations project
**Root Cause:** Different project structures
**Fix:** Updated all paths to use `workers/`, `prompts/`, `directives/`
**Prevention:** Template uses correct paths

---

## New Learnings

_Add new learnings below as they occur_

### [YYYY-MM-DD] | [Issue Title]

**Issue:** ...
**Root Cause:** ...
**Fix:** ...
**Prevention:** ...
