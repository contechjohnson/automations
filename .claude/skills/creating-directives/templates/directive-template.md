# Directive: {NAME}

> {One-line purpose statement describing what this directive achieves}

**Status:** Active | Draft | Deprecated
**Implementation:** `workers/{category}/{name}.py` | N/A
**API:** `POST /automations/{slug}` | N/A

---

## Overview

{2-3 sentences describing what this directive covers, why it exists, and its role in the system.}

---

## Step Boundary Contract

<!-- Define what this step IS and IS NOT responsible for. This prevents scope creep and clarifies ownership. -->

**This step IS responsible for:**
- {Core responsibility 1}
- {Core responsibility 2}
- {Core responsibility 3}

**This step is NOT responsible for:**
- {Excluded responsibility 1} → {which step owns this}
- {Excluded responsibility 2} → {which step owns this}

---

## Input Contract

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": [],
  "properties": {
    "example_field": {
      "type": "string",
      "description": "Description of the field"
    }
  }
}
```

---

## Output Contract

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": [],
  "properties": {
    "result_field": {
      "type": "string",
      "description": "Description of the output"
    }
  }
}
```

---

## AI Configuration

| Setting | Value | Notes |
|---------|-------|-------|
| Model | gpt-4.1 | Default, can override |
| Agent Type | none | none / firecrawl / research / full |
| Temperature | 0.7 | Adjust for determinism |
| Log | **true** | ALWAYS true - non-negotiable |

---

## Prompt Index

<!-- Include this section if directive has LLM calls. Remove if no LLM usage. -->

| Prompt ID | Purpose | Model | File |
|-----------|---------|-------|------|
| `{slug}.v1` | {What this prompt does} | gpt-4.1 | [prompts/{slug}.md](../prompts/{slug}.md) |

---

## Process Steps

### Step 1: {Name}

{Description of what happens in this step}

- Action 1
- Action 2
- **Gate:** {Pass/fail criteria for this step}

### Step 2: {Name}

{Description}

- Action 1
- **Gate:** {Criteria}

### Step 3: {Name}

{Description}

---

## Quality Gates

| Gate | Criteria | Severity |
|------|----------|----------|
| {gate_name} | {Specific, testable condition} | error |
| {gate_name} | {Condition} | warning |
| {gate_name} | {Condition} | info |

**Severity Levels:**
- `error` - Blocks execution, must fix before continuing
- `warning` - Logs issue, continues with degraded output
- `info` - Informational, no action required

---

## Failure Handling

| Failure Mode | Detection | Recovery |
|--------------|-----------|----------|
| {mode_name} | {How to detect} | {What to do} |
| API timeout | Response exceeds 30s | Retry 2x with exponential backoff |
| Invalid input | Schema validation fails | Return early with error message |
| Partial data | Required field missing | Use fallback value or skip record |

---

## Observability

**Log Prefix:** `[{SLUG}]`
**Tags:** [{slug}, {category}, {model}]

**Required Logging (NON-NEGOTIABLE):**
- Use `log=True` on all `prompt()` calls
- Or use `ExecutionLogger` for multi-step workers
- All executions logged to Supabase `execution_logs` table

**Log Fields:**
- `automation_slug` - This directive's slug
- `worker_name` - Worker identifier (e.g., `research.entity`)
- `input` - Full input parameters (JSONB)
- `output` - Full output (JSONB)
- `runtime_seconds` - Execution time
- `status` - running/success/failed

---

## Self-Annealing Log

| Date | Issue | Resolution |
|------|-------|------------|
| {YYYY-MM-DD} | {Brief description} | {What was done to fix} |

<!-- Add new entries at the top of this table -->

---

## Dependencies

**Environment:**
- `OPENAI_API_KEY` - Required for LLM calls
- `SUPABASE_URL` - Required for logging
- `SUPABASE_SERVICE_ROLE_KEY` - Required for logging

**Database:**
- `execution_logs` - Stores execution traces

**External APIs:**
- {api_name} - {Purpose}

---

## Related

**Directives:**
- {directive}.md - {Relationship: orchestrates, follows, related to}

**Workers:**
- `workers/{category}/{name}.py` - Main implementation

**Skills:**
- `building-automations` - For implementing this directive
- `using-rq-workers` - If this runs as background job
