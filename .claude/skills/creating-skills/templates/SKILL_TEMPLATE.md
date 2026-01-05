---
name: {skill-name-in-gerund-form}
description: {Specific capabilities}. Use when {trigger 1}, {trigger 2}, or when user mentions {keywords}.
allowed-tools: Read, Write, Glob, Bash
---

# {Skill Title}

{One sentence describing what this skill does.}

## When to Use

- {Trigger scenario 1}
- {Trigger scenario 2}
- {Trigger scenario 3}

## Quick Start

{Most common use case - keep under 50 lines}

```bash
# Example command
python3 scripts/main.py --input data.csv
```

## Process

### Step 1: {First Step}

{Brief description}

### Step 2: {Second Step}

{Brief description}

### Step 3: {Third Step}

{Brief description}

---

## Advanced Features

**{Feature A}**: See [{FEATURE_A.md}]({FEATURE_A.md})
**{Feature B}**: See [{FEATURE_B.md}]({FEATURE_B.md})

---

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/main.py` | {What it does} |
| `scripts/helper.py` | {What it does} |

---

## Resources

**Repository:** [contechjohnson/automations](https://github.com/contechjohnson/automations)

### Files Referenced by This Skill

| Resource | Path |
|----------|------|
| {Script Name} | `.claude/skills/{skill-name}/scripts/{script}.py` |
| {Template Name} | `.claude/skills/{skill-name}/templates/{template}.md` |

### API Endpoints (if applicable)

| Endpoint | URL |
|----------|-----|
| Production API | `https://api.columnline.dev` |

### Environment Variables Required (if applicable)

| Variable | Purpose |
|----------|---------|
| `{VARIABLE_NAME}` | {What it's used for} - from `.env` locally, paste directly in web |

### Related Skills

| Skill | Purpose |
|-------|---------|
| `{related-skill}` | {When to use it} |

---

## Self-Annealing

**MANDATORY:** After any failure or unexpected behavior:
1. Document in LEARNINGS.md with date
2. Update this skill if process needs change
3. Update scripts if logic needs fix

See `LEARNINGS.md` for known issues and fixes.
