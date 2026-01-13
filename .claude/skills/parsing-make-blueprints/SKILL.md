---
name: parsing-make-blueprints
description: Parse Make.com blueprint JSON files into human-readable business logic documentation optimized for LLM analysis. Extract workflow patterns, module relationships, data flow, execution logic, and identify potential issues. Use when working with Make.com JSON files, analyzing blueprints, parsing workflows, or when user mentions "Make.com JSON", "parse blueprint", "analyze Make.com workflow", "/parse-make-blueprint", or "/analyze-make-workflow".
allowed-tools: Read, Write, Glob, Bash, Grep
---

# Parsing Make.com Blueprints

Convert Make.com blueprint JSON files into human-readable business logic documentation optimized for LLM analysis.

## When to Use

- Working with Make.com JSON files
- Analyzing Make.com workflows
- Converting blueprints to business logic
- Identifying workflow issues and inefficiencies
- Migrating Make.com workflows to Python
- Understanding complex Make.com automations

## Quick Start

```bash
# Natural language trigger
"Parse the Make.com blueprint at [path]"

# Via script directly
python .claude/skills/parsing-make-blueprints/scripts/make_blueprint_converter.py \
  --input columnline_app/api_migration/make_scenarios_and_csvs/01AND02_SEARCH_AND_SIGNAL.blueprint.json \
  --output tmp/01AND02_SEARCH_AND_SIGNAL_business_logic.md

# With LLM enhancement
python .claude/skills/parsing-make-blueprints/scripts/make_blueprint_converter.py \
  --input columnline_app/api_migration/make_scenarios_and_csvs/01AND02_SEARCH_AND_SIGNAL.blueprint.json \
  --output tmp/01AND02_SEARCH_AND_SIGNAL_business_logic.md \
  --llm-enhance \
  --llm-model gpt-4.1

# Batch processing
python .claude/skills/parsing-make-blueprints/scripts/make_blueprint_converter.py \
  --batch columnline_app/api_migration/make_scenarios_and_csvs/ \
  --output tmp/blueprint_analyses/
```

## Process

1. Load and validate Make.com JSON structure
2. Extract all modules and their configurations
3. Build data flow graph from mapper references (`{{module_id.field}}`)
4. Identify execution patterns (sequential, parallel, async)
5. Extract LLM prompts from AI modules
6. Analyze efficiency and detect potential bugs
7. Generate markdown report with original JSON reference

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/make_blueprint_converter.py` | Main converter - parses JSON and generates business logic markdown |

## Reference Documentation

| Reference | Purpose |
|-----------|---------|
| `reference/MAKE_COM_JSON_STRUCTURE.md` | Make.com JSON structure documentation |
| `reference/MODULE_TYPES.md` | Complete module type reference |
| `reference/MAPPER_SYNTAX.md` | Data mapper syntax and examples |

## Blueprint File Locations

All Make.com blueprints are located in:
- `columnline_app/api_migration/make_scenarios_and_csvs/*.blueprint.json`

Original JSON files are always referenced in output for double-checking. The converter preserves the original file path in every report.

## Output Format

The converter generates markdown reports with:

1. **Overview** - Workflow name, module counts, execution pattern, timestamp, original JSON path
2. **Execution Flow** - Step-by-step module breakdown with inputs, configuration, and prompts
3. **Data Flow Diagram** - Module connections and data transformations
4. **Module Relationships** - Dependency graph showing how modules connect
5. **LLM Prompts Extracted** - System and user prompts from LLM modules
6. **Potential Issues** - Data loss, missing error handlers, etc.
7. **Efficiency Analysis** - Bottlenecks, parallel opportunities, redundant operations
8. **Reference Documentation** - Links to Make.com documentation and original JSON

## Features

- **Automatic data flow detection** - Parses mapper references to build dependency graph
- **LLM prompt extraction** - Extracts system and user prompts from OpenAI modules
- **Pattern detection** - Identifies sequential, parallel, async, and mixed execution patterns
- **Efficiency analysis** - Finds bottlenecks, parallel opportunities, and redundant operations
- **Bug detection** - Identifies potential data loss, missing error handlers
- **Original JSON reference** - Always includes path to original file for verification
- **Optional LLM enhancement** - Uses OpenAI to add context and analysis

## Related Skills

| Skill | Purpose |
|-------|---------|
| `make_migration_to_api` | Migration planning and execution |
| `building-automations` | Building Python automations from directives |

## Self-Annealing

See `LEARNINGS.md` for known issues and improvements.

