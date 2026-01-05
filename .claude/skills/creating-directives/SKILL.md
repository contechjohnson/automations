---
name: creating-directives
description: Create or update directives with standardized format and prompt indexes. Use when creating new directive, updating existing directive, adding prompt index, standardizing documentation, or when user mentions "directive template", "standardize directive", "new directive", or "define automation".
allowed-tools: Read, Write, Glob, Grep, Bash
---

# Creating Directives

Build standardized directives that follow the DoE framework with explicit prompt references.

## Related Skills

| When your directive... | Also use... |
|------------------------|-------------|
| Has LLM calls (Prompt Index section) | `building-automations` - for the implementation |
| Needs RQ background jobs | `using-rq-workers` - for queue patterns |

## When to Use This Skill

- Creating a new directive for an automation workflow
- Updating an existing directive to the standardized format
- Adding a Prompt Index section to a directive
- Reviewing directive compliance with the standard

## Prime Directives (Reference First)

Before creating any directive, reference the prime directives to ensure alignment:

| File | Check |
|------|-------|
| `directives/prime/columnline.md` | Does this serve a Columnline priority or client? |
| `directives/prime/prologis.md` | Does this affect day job capacity? |
| `directives/prime/life.md` | Is there bandwidth for this? |

Prime directives capture the "why" behind work. Regular directives capture the "how."

## Quick Start

1. Determine directive type (Simple LLM, Agent, Scraper, or Background Job)
2. Copy template from `templates/directive-template.md`
3. Fill in all mandatory sections
4. If directive has LLM calls, add Prompt Index section
5. Validate against quality gates

## Directive Types

| Type | Has LLM | Examples |
|------|---------|----------|
| Simple LLM | Yes | entity-research, content-generation |
| Agent-based | Yes | deep-research, web-analysis |
| Scraper | Maybe | permits-scraper, job-board-scraper |
| Background Job | Maybe | batch-processing, data-pipeline |

## Mandatory Sections

Every directive MUST have these sections in order:

### 1. Header Block

```markdown
# Directive: {Name}

> {One-line purpose statement}

**Status:** Active | Draft | Deprecated
**Implementation:** `workers/{category}/{name}.py` | N/A
**API:** `POST /automations/{slug}` | N/A
```

### 2. Overview

2-3 sentences describing what this directive covers and why it exists.

### 3. Step Boundary Contract

Defines what this step IS and IS NOT responsible for. Prevents scope creep and clarifies ownership.

```markdown
## Step Boundary Contract

**This step IS responsible for:**
- Core responsibility 1
- Core responsibility 2

**This step is NOT responsible for:**
- Excluded item 1 → which step owns it
- Excluded item 2 → which step owns it
```

### 4. Input Contract

JSON Schema defining black-box inputs. What does this step receive?

```markdown
## Input Contract

\`\`\`json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["client_id"],
  "properties": {
    "client_id": {"type": "string", "format": "uuid"},
    ...
  }
}
\`\`\`
```

### 5. Output Contract

JSON Schema defining black-box outputs. What does this step produce?

### 6. AI Configuration

Settings for LLM calls:

```markdown
## AI Configuration

| Setting | Value | Notes |
|---------|-------|-------|
| Model | gpt-4.1 | Default, can override |
| Agent Type | none | **Default: none** (simple prompt) |
| Tools | none | Only specify if explicitly needed |
| Temperature | 0.7 | Adjust for determinism |
| Log | true | **ALWAYS true** |
```

**Agent Type Values:**
- `none` (default) - Simple `prompt()` call, no tools, fast and cheap
- `research` - Adds WebSearchTool for real-time web queries
- `firecrawl` - Adds Firecrawl tools (scrape, search, map) for website extraction
- `full` - All tools enabled (expensive, use sparingly)

**IMPORTANT:** Tools are OPT-IN. Most automations do NOT need tools.
Only specify `Agent Type: research/firecrawl/full` when the task genuinely requires external data.

### 7. Prompt Index (if directive has LLM calls)

Table linking to prompt files in `prompts/`:

```markdown
## Prompt Index

| Prompt ID | Purpose | Model | File |
|-----------|---------|-------|------|
| `{slug}.v1` | Main prompt | gpt-4.1 | [prompts/{slug}.md](../prompts/{slug}.md) |
```

### 8. Process Steps

Numbered phases with inline quality gates:

```markdown
## Process Steps

### Step 1: Initial Discovery
- Run signal discovery with query
- **Gate:** Must return at least 3 candidates
```

### 9. Quality Gates

Explicit pass/fail criteria:

```markdown
## Quality Gates

| Gate | Criteria | Severity |
|------|----------|----------|
| Valid input | All required fields present | error |
| Results found | At least 1 result | warning |
```

### 10. Failure Handling

What happens when things go wrong:

```markdown
## Failure Handling

| Failure Mode | Detection | Recovery |
|--------------|-----------|----------|
| API timeout | 30s exceeded | Retry with backoff |
| No results | Empty response | Log and return empty |
```

### 11. Observability

**CRITICAL:** Logging requirements (non-negotiable):

```markdown
## Observability

**Log Prefix:** `[{SLUG}]`
**Tags:** [{slug}, {category}, {model}]

**Required Logging:**
- Always use `log=True` on prompt() calls
- Or use ExecutionLogger for multi-step workers
- All calls logged to Supabase `execution_logs`
```

### 12. Self-Annealing Log

Learning journal for edge cases:

```markdown
## Self-Annealing Log

| Date | Issue | Resolution |
|------|-------|------------|
| 2025-01-15 | Web search returning 403 | Added retry with backoff |
```

### 13. Dependencies

What's required to run:

```markdown
## Dependencies

- `OPENAI_API_KEY` - Required
- `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` - For logging
```

### 14. Related

Links to related resources:

```markdown
## Related

**Directives:** {related directives}
**Skills:** building-automations, using-rq-workers
```

## File Locations

| Artifact | Location |
|----------|----------|
| Directive | `directives/{slug}.md` |
| Prompt | `prompts/{slug}.md` |
| Worker | `workers/{category}/{name}.py` |
| API Endpoint | `api/main.py` |

## Quality Gates for Directive Compliance

Before finalizing a directive, verify:

- [ ] Has all mandatory sections
- [ ] Step Boundary Contract clearly defines IS/IS NOT responsibilities
- [ ] Input/Output Contracts use JSON Schema format
- [ ] Prompt Index lists all LLM calls (if applicable)
- [ ] AI Configuration specifies `Log: true`
- [ ] Quality Gates have severity levels
- [ ] Failure Handling covers at least 2 modes
- [ ] Observability section specifies logging strategy
- [ ] Self-Annealing Log has date format
- [ ] Related links to actual files (verify paths exist)

## Anti-Patterns

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| Missing Prompt Index | LLM calls not tracked | Audit code for LLM calls |
| Log: false | No observability | Always use log=True |
| Vague Quality Gates | Can't validate | Use specific, testable criteria |
| No Self-Annealing Log | Can't learn from failures | Add table even if empty |
| Broken file links | References don't work | Verify paths before commit |

## Templates

- [Directive Template](templates/directive-template.md) - Full template to copy

## Self-Annealing

After any directive update issue:
1. Document in `LEARNINGS.md`
2. Update this skill if pattern needs change
3. Update template if section needs refinement

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
