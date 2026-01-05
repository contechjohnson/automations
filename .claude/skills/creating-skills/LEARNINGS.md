# Creating Skills - Learnings

Self-annealing log for the skill-creation skill itself.

## Format

Each entry: `DATE | ISSUE | ROOT CAUSE | FIX | PREVENTION`

---

## 2025-01-04 | Initial Setup

Copied from Columnline project based on December 2025 Claude Code best practices.

---

## Key Insights (from documentation)

### Description is Everything

**Issue:** Skills not triggering when expected
**Root Cause:** Vague descriptions without trigger terms
**Fix:** Use formula: `[CAPABILITIES]. Use when [TRIGGERS] or when user mentions [KEYWORDS].`
**Prevention:** Always test with natural language before committing

### Gerund Naming

**Issue:** Inconsistent skill naming
**Root Cause:** No standard convention
**Fix:** Use verb-ing form: `creating-skills`, `analyzing-data`
**Prevention:** Check naming before creating directory

### Progressive Disclosure

**Issue:** SKILL.md too long, wasting tokens
**Root Cause:** All content in one file
**Fix:** Split advanced content into reference files, link from SKILL.md
**Prevention:** If SKILL.md > 500 lines, split it

### Self-Annealing Required

**Issue:** Same mistakes repeated
**Root Cause:** No learning capture mechanism
**Fix:** LEARNINGS.md mandatory for every skill
**Prevention:** Template includes LEARNINGS.md from start

---

## New Learnings

_Add new learnings below as they occur_

### [YYYY-MM-DD] | [Issue Title]

**Issue:** What happened
**Root Cause:** Why it happened
**Fix:** What was done
**Prevention:** How to avoid in future
