# Parsing Make.com Blueprints Learnings

Self-annealing log for the parsing-make-blueprints skill. Document failures, root causes, and fixes.

## Format

Each entry: `DATE | ISSUE | ROOT CAUSE | FIX | PREVENTION`

---

## 2025-01-04 | Initial Setup

**Issue:** Need to parse Make.com blueprint JSON files into human-readable business logic for LLM analysis

**Root Cause:** Make.com JSON structure is complex and not easily readable by humans or LLMs

**Fix:** Created Claude Code skill to automatically parse blueprints and generate structured markdown documentation

**Prevention:** Skill includes reference documentation for Make.com JSON structure to help with future parsing needs

---

## Migrated Learnings

### Make.com JSON Structure Insights

**Issue:** Make.com blueprints use implicit connections via mapper references (`{{module_id.field}}`) rather than explicit connection arrays

**Root Cause:** Make.com's visual workflow builder stores connections in mapper objects, not separate connection arrays like n8n

**Fix:** Parser extracts data flow by parsing mapper references to build dependency graph

**Prevention:** Document mapper syntax patterns in reference/MAPPER_SYNTAX.md

---

## New Learnings

_Add new learnings below as they occur_

