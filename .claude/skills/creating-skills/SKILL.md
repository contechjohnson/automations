---
name: creating-skills
description: Create new Claude Code skills with proper structure and self-annealing. Use when building a new skill, making repeated workflows reusable, extracting patterns into skills, or when user says "create a skill", "make this a skill", or "I keep doing this".
allowed-tools: Read, Write, Glob, Bash
---

# Creating Skills

Build reusable Claude Code skills that self-anneal over time.

## When to Create a Skill

- **Repeated pattern:** You've done the same thing 3+ times
- **Complex workflow:** Multi-step process that benefits from documentation
- **Team sharing:** Others need the same capability
- **Self-annealing:** Workflow that improves from learnings

## Quick Start

```bash
# Create skill structure
mkdir -p .claude/skills/{skill-name}/scripts
```

Then create these files:
1. `SKILL.md` - Main skill document (triggers discovery)
2. `LEARNINGS.md` - Self-annealing log

## Skill Structure

```
.claude/skills/
└── {skill-name}/
    ├── SKILL.md           # Required: Main skill doc
    ├── LEARNINGS.md       # Required: Self-annealing log
    ├── scripts/           # Optional: Python/bash utilities
    │   └── helper.py
    ├── templates/         # Optional: Reusable templates
    │   └── template.json
    └── REFERENCE.md       # Optional: Detailed docs (loaded on-demand)
```

## SKILL.md Template

See [templates/SKILL_TEMPLATE.md](templates/SKILL_TEMPLATE.md) for full template.

**Critical frontmatter:**

```yaml
---
name: analyzing-sales-data
description: Analyze sales spreadsheets, calculate metrics, generate reports. Use when working with Excel/CSV sales data, pipeline analysis, or when user mentions sales reports.
allowed-tools: Read, Write, Bash, Glob
---
```

## Description: The Magic

**The description determines when Claude loads your skill.** This is semantic matching, not keyword matching.

### Formula

```
description: [CAPABILITIES]. Use when [TRIGGER 1], [TRIGGER 2], or when user mentions [KEYWORDS].
```

### Good Examples

```yaml
# Specific capabilities + clear triggers
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.

# Action verbs + use cases
description: Generate commit messages by analyzing git diffs. Use when the user asks for help writing commits or reviewing staged changes.

# Domain terms included
description: Analyze Excel spreadsheets, create pivot tables, generate charts. Use when analyzing Excel files, spreadsheets, tabular data, or .xlsx files.
```

### Bad Examples

```yaml
# Too vague - won't trigger
description: Helps with documents

# Missing triggers
description: PDF processing tool

# No specifics
description: Useful for data work
```

## Naming Convention

Use **gerund form** (verb + -ing):
- `creating-skills`
- `analyzing-data`
- `processing-pdfs`
- `managing-campaigns`

**Avoid:** `helper`, `utils`, `tools`, `misc`

## Self-Annealing Pattern

Every skill MUST have `LEARNINGS.md`:

```markdown
# {Skill Name} Learnings

## Format
DATE | ISSUE | ROOT CAUSE | FIX | PREVENTION

---

## Learnings

### YYYY-MM-DD | Issue Title
**Issue:** What happened
**Root Cause:** Why it happened
**Fix:** What was done
**Prevention:** How to avoid in future
```

**After any failure:**
1. Document in LEARNINGS.md
2. Update SKILL.md if process needs change
3. Future runs benefit automatically

## Progressive Disclosure

Keep SKILL.md under 500 lines. Split advanced content:

```markdown
## Quick start
[Common use case - 50 lines max]

## Advanced features
**Feature A**: See [FEATURE_A.md](FEATURE_A.md)
**Feature B**: See [FEATURE_B.md](FEATURE_B.md)
```

Claude loads reference files **only when needed**, saving tokens.

## Validation Checklist

Before committing a new skill:

- [ ] Description has specific capabilities + trigger terms
- [ ] SKILL.md body under 500 lines
- [ ] LEARNINGS.md exists with template
- [ ] Tested with real usage scenario
- [ ] Scripts handle errors explicitly
- [ ] No magic numbers (all values justified)

## Skill vs Agent vs Command

| Type | Discovery | Use When |
|------|-----------|----------|
| **Skill** | Automatic (semantic) | Extending capabilities, reusable patterns |
| **Agent** | Delegated | Complex reasoning, deep domain expertise |
| **Command** | User-invoked (`/cmd`) | Quick shortcuts, explicit triggers |

## Example: Creating a Skill

User says: "I keep manually checking campaign analytics"

**Step 1: Identify the pattern**
- What actions repeat? (API calls, formatting, thresholds)
- What varies? (campaign name, date range)
- What's the output? (formatted report)

**Step 2: Create structure**
```bash
mkdir -p .claude/skills/checking-analytics/scripts
```

**Step 3: Write SKILL.md**
- Frontmatter with specific description
- Quick start (most common use)
- Reference to scripts

**Step 4: Add LEARNINGS.md**
- Empty template ready for first learnings

**Step 5: Test**
- Try triggering with natural language
- Verify it activates on relevant requests

## Anti-Patterns

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| Vague description | Won't trigger | Be specific with capabilities + triggers |
| Giant SKILL.md | Wastes tokens | Split into reference files |
| No LEARNINGS.md | Can't improve | Always include self-annealing log |
| Hardcoded values | Inflexible | Use parameters or config |
| No error handling | Fails silently | Scripts should handle errors explicitly |

## Token Optimization (CRITICAL)

**Skills consume tokens when loaded.** Full SKILL.md content is loaded into context when Claude determines the skill is relevant.

### Token Budget Guidelines

| Skill Size | Tokens | Guidance |
|------------|--------|----------|
| Small | <500 | Fine as single file |
| Medium | 500-2000 | Consider splitting |
| Large | 2000+ | MUST use progressive disclosure |

### Progressive Disclosure Pattern

For skills over 500 lines or 2000 tokens:

```
my-skill/
├── SKILL.md              # Core instructions ONLY (~500 lines max)
├── reference/
│   ├── patterns.md       # Loaded when Claude needs patterns
│   ├── examples.md       # Loaded when Claude needs examples
│   └── troubleshooting.md # Loaded on errors
├── scripts/
│   └── helper.py         # Executed, NOT loaded into context
└── LEARNINGS.md
```

**Key insight:** Scripts are *executed* (only output uses tokens), but reference files are *read* (full content uses tokens). Prefer scripts for complex logic.

### Auditing Existing Skills

Run `/context` to see token usage per skill. Skills over 2000 tokens should be refactored:

1. Move detailed examples to `reference/examples.md`
2. Move edge case handling to `reference/troubleshooting.md`
3. Keep SKILL.md focused on core workflow
4. Link to reference files: "For examples, see [examples.md](reference/examples.md)"

---

## Resources

**Repository:** [contechjohnson/automations](https://github.com/contechjohnson/automations)

**API Endpoints:**
| Endpoint | URL |
|----------|-----|
| Production API | `https://api.columnline.dev` |
| Health Check | `https://api.columnline.dev/health` |
| Test Prompt | `POST https://api.columnline.dev/test/prompt` |
| Logs | `https://api.columnline.dev/logs` |

**Infrastructure:**
| Resource | Location |
|----------|----------|
| Droplet IP | `64.225.120.95` |
| RQ Dashboard | `http://64.225.120.95:9181` |

**Credentials:** Add `CREDENTIALS.md` to your Claude project for API keys. Cannot be stored in repo due to GitHub secret scanning.
