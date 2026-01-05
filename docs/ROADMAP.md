# Automation Roadmap

> **Last Updated:** 2025-01-05
>
> Single source of truth for what we're building and why.

---

## Guiding Principles

1. **Solve real problems** - Every item must have a clear pain point it addresses
2. **Client-driven priority** - What's blocking revenue or causing friction?
3. **Start simple** - Build the minimum that solves the problem, iterate from feedback
4. **Reuse patterns** - Extract templates only after building 2-3 similar automations

---

## Priority Levels

| Level | Meaning | Timeline |
|-------|---------|----------|
| **P1** | Critical - blocks revenue or core capability | This week |
| **P2** | Important - significant value, clear need | This month |
| **P3** | Nice to have - valuable but not urgent | When time allows |

---

## In Progress

*Currently being worked on*

<!--
### Item Name
**Status:** In progress / Blocked / Testing
**Problem:** ...
**Notes:** ...
-->

---

## P1 - Critical

*Must happen this week*

<!--
### [P1] Example Item
**Problem:** What specific pain point does this solve?
**Value:** Who benefits? Revenue impact? Time saved?
**Scope:** Small / Medium / Large
**Dependencies:** What needs to exist first?
**Notes:** Context, alternatives considered
-->

---

## P2 - Important

*Should happen this month*

<!--
### [P2] Example Item
**Problem:** ...
**Value:** ...
**Scope:** ...
**Dependencies:** ...
-->

---

## P3 - Nice to Have

*When time allows*

<!--
### [P3] Example Item
**Problem:** ...
**Value:** ...
**Scope:** ...
-->

---

## Backlog

*Ideas not yet validated or scoped. Lightweight notes only.*

<!--
- **Idea name** - Brief description of what and why
-->

---

## Completed

*Recently finished items for reference*

| Item | Completed | Notes |
|------|-----------|-------|
| Execution logging system | 2025-01-04 | Full trace logging to Supabase |
| AI abstraction layer | 2025-01-04 | prompt(), agent_prompt() with logging |
| Automation registry | 2025-01-04 | Register/track automations in DB |
| Entity research worker | 2025-01-04 | Deep research via o4-mini |

---

## Parking Lot

*Things we explicitly decided NOT to do (and why)*

<!--
| Item | Reason | Date |
|------|--------|------|
| Example | Solved by simpler approach X | 2025-01-05 |
-->

---

## Decision Log

*Key decisions that affect the roadmap*

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-01-04 | API-first architecture | Enables web access, testing, observability |
| 2025-01-04 | Single .env symlinked from Columnline | Avoid key duplication, single source |
| 2025-01-04 | Supabase for all logging | Already have it, good JSONB support |
