# Directives

Automation specifications that define behavior, contracts, and requirements.

## What is a Directive?

A directive is a markdown file that specifies:
- **What** an automation does
- **Inputs** it accepts (JSON Schema)
- **Outputs** it produces (JSON Schema)
- **AI configuration** (model, logging, etc.)
- **Quality gates** and failure handling
- **Observability** requirements

## Quick Start

1. Copy the template from `.claude/skills/creating-directives/templates/directive-template.md`
2. Fill in all mandatory sections
3. Save as `directives/{slug}.md`
4. Ask Claude: "implement the {slug} directive"

## Naming Convention

Use kebab-case slugs:
- `entity-research.md`
- `permits-scraper.md`
- `batch-processor.md`

## File Structure

```
directives/
├── README.md              # This file
├── entity-research.md     # Example directive
├── permits-scraper.md     # Another example
└── ...
```

## Mandatory Sections

Every directive must include:

1. **Header** - Name, status, implementation path
2. **Overview** - What and why
3. **Step Boundary Contract** - IS/IS NOT responsible for
4. **Input Contract** - JSON Schema
5. **Output Contract** - JSON Schema
6. **AI Configuration** - Model, logging (always `log=True`)
7. **Prompt Index** - Links to prompt files (if LLM)
8. **Process Steps** - Numbered workflow
9. **Quality Gates** - Pass/fail criteria
10. **Failure Handling** - Recovery strategies
11. **Observability** - Logging requirements
12. **Self-Annealing Log** - Issue tracking
13. **Dependencies** - Env vars, APIs
14. **Related** - Links to files

## Key Requirement: Logging

**Every directive MUST specify `Log: true` in AI Configuration.**

This is non-negotiable. All executions must be logged to Supabase `execution_logs` for observability.

## Related Skills

- `creating-directives` - How to write directives
- `building-automations` - How to implement directives
- `using-rq-workers` - For background job directives
