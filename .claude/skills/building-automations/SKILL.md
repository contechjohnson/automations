---
name: building-automations
description: Create or edit Python automation workers including simple LLM calls, agent-based research, scrapers, and multi-step workflows. Use when implementing a new automation, editing workers/, creating prompts, or when user mentions "build automation", "create scraper", "implement directive", "new worker", or "add automation".
allowed-tools: Read, Write, Glob, Grep, Bash
---

# Building Automations

Implement Python automation workers from directives with mandatory logging.

## Related Skills

| When you need to... | Use... |
|---------------------|--------|
| Write the directive first | `creating-directives` |
| Queue as background job | `using-rq-workers` |
| Create a new skill | `creating-skills` |

## Core Philosophy

1. **Directive-driven:** Read directive first, implement to spec
2. **Provider-agnostic:** Use `workers/ai.py` abstraction
3. **MANDATORY LOGGING:** Always `log=True` - no exceptions
4. **Self-annealing:** Update LEARNINGS.md on issues

## Pre-Implementation Checklist

Before writing any code:

- [ ] Read directive at `directives/{slug}.md`
- [ ] Input/Output Contracts defined
- [ ] Prompt Index lists all LLM calls
- [ ] AI Configuration specifies model and settings
- [ ] Logging strategy defined (`log=True` or `ExecutionLogger`)

## Quick Start

### Simple LLM Worker (Most Common)

```python
from workers.ai import prompt

def run(input_data: dict) -> dict:
    """Simple LLM worker with mandatory logging."""
    result = prompt(
        "my-automation",           # Prompt file: prompts/my-automation.md
        variables=input_data,
        model="gpt-4.1",
        log=True,                  # ALWAYS log - non-negotiable
        tags=["my-automation", "gpt-4.1"]
    )
    return result
```

## Worker Patterns

### Pattern 1: Simple LLM Call

For single-step LLM tasks. Most common pattern.

```python
# workers/research/entity.py
from workers.ai import prompt

def run_entity_research(input_data: dict) -> dict:
    """Research an entity using LLM."""
    result = prompt(
        "entity-research",
        variables={
            "target": input_data.get("target"),
            "context": input_data.get("context", "")
        },
        model="gpt-4.1",
        log=True,
        tags=["entity-research", "gpt-4.1"]
    )
    return {
        "status": "success",
        "research": result.get("output"),
        "model": result.get("model"),
        "elapsed": result.get("elapsed_seconds")
    }
```

### Pattern 2: Agent Worker (with Tools)

For tasks needing web search or Firecrawl tools.

```python
# workers/research/deep_research.py
from workers.agent import agent_prompt

def run_deep_research(input_data: dict) -> dict:
    """Deep research using agent with tools."""
    result = agent_prompt(
        "deep-research",
        variables=input_data,
        model="gpt-4.1",
        agent_type="firecrawl",    # "research" | "firecrawl" | "full"
        log=True,
        tags=["deep-research", "agent", "firecrawl"]
    )
    return result
```

### Pattern 3: Multi-Step Worker (with ExecutionLogger)

For complex workflows with multiple phases.

```python
# workers/scrapers/permits.py
from workers.logger import ExecutionLogger
from workers.ai import prompt

def run_permit_scraper(config: dict, geography: dict, job=None) -> dict:
    """Multi-step scraper with detailed logging."""
    log = ExecutionLogger(
        worker_name="scrapers.permits",
        automation_slug=config.get("slug", "permits"),
        input_data={"config": config, "geography": geography},
        tags=["permits", "scraper", geography.get("state", "unknown")]
    )

    try:
        # Step 1: Discovery
        log.meta("step", "discovery")
        log.meta("percent", 10)
        raw_data = fetch_permits(config)

        # Step 2: Processing
        log.meta("step", "processing")
        log.meta("percent", 50)
        processed = process_permits(raw_data)

        # Step 3: Enrichment (optional LLM)
        if config.get("enrich"):
            log.meta("step", "enrichment")
            log.meta("percent", 80)
            enriched = prompt(
                "permits.enrich",
                variables={"permits": processed},
                model="gpt-4.1-mini",
                log=True,
                tags=["permits", "enrichment"]
            )
            processed = enriched.get("output")

        return log.success({
            "records": processed,
            "count": len(processed)
        })

    except Exception as e:
        log.fail(e)
```

### Pattern 4: Deep Research (Background Mode)

For long-running research (5-10 min). Must use background mode.

```python
# workers/research/deep.py
from workers.ai import prompt, poll_research

def start_deep_research(input_data: dict) -> dict:
    """Start deep research in background mode."""
    result = prompt(
        "deep-research",
        variables=input_data,
        model="o4-mini-deep-research",
        background=True,  # Returns immediately with response_id
        log=True,
        tags=["deep-research", "o4-mini"]
    )
    return {
        "status": "submitted",
        "response_id": result.get("response_id"),
        "poll_endpoint": "/research/poll"
    }

def check_deep_research(response_id: str) -> dict:
    """Poll for research completion."""
    return poll_research(response_id)
```

## Understanding the AI Stack

### Decision Tree: What Should I Use?

```
START: What does the automation need?
│
├─► No external data needed (text processing, analysis, generation)
│   └─► Use `prompt()` with Chat Completions
│       • Fast, cheap, predictable
│       • Single LLM call: Input → LLM → Output
│       • Models: gpt-4.1, gpt-4.1-mini, gpt-5.2, gemini-2.5-flash
│
├─► Needs current web information (research, fact-checking)
│   │
│   ├─► Quick lookup (< 30 seconds)
│   │   └─► Use `agent_prompt()` with `agent_type="research"`
│   │       • WebSearchTool for real-time queries
│   │
│   └─► Deep research (5-10 minutes, comprehensive)
│       └─► Use `prompt()` with `model="o4-mini-deep-research"` + `background=True`
│           • Built-in web_search_preview in Responses API
│           • Returns response_id, poll for completion
│
├─► Needs to scrape/crawl specific websites
│   └─► Use `agent_prompt()` with `agent_type="firecrawl"`
│       • Tools: firecrawl_scrape, firecrawl_search, firecrawl_map
│       • For structured data extraction from known URLs
│
└─► Needs BOTH web search AND scraping
    └─► Use `agent_prompt()` with `agent_type="full"`
        • All tools available
        • Most expensive, use sparingly
```

### IMPORTANT: Tools Are OPT-IN, Not Default

**Most automations do NOT need tools.** Only use tools when:
- The directive explicitly specifies tool requirements
- The task requires real-time data (current prices, recent news)
- The task requires scraping specific websites

**Default approach:** Start with `prompt()` (no tools). Only add tools if the task genuinely requires external data.

### Provider-Agnostic Architecture

This system supports multiple AI providers through `workers/ai.py`:

| Provider | API Used | Models | Best For |
|----------|----------|--------|----------|
| **OpenAI** | Responses API (primary) | gpt-4.1, gpt-5.2, o4-mini | Default choice |
| **OpenAI** | Chat Completions (fallback) | Same models | Legacy compatibility |
| **OpenAI** | Agent SDK | gpt-4.1+ | Multi-turn with tools |
| **Google** | Gemini API | gemini-2.5-flash | Fast, grounded search |
| **Perplexity** | (planned) | sonar models | Real-time search |

**The abstraction layer handles this automatically.** Just specify the model name.

### Prompt vs Agent: The Key Difference

**`prompt()`** = Single LLM call, no tools
- Input → LLM → Output
- Fast, cheap, predictable
- Use for: summarization, extraction, generation, classification
- **This is your default choice**

**`agent_prompt()`** = Iterative tool-calling loop
- Input → LLM → (calls tool?) → LLM → (calls tool?) → ... → Output
- LLM decides WHEN and IF to use tools
- Multiple "turns" until task is complete
- Use for: web research, scraping, anything needing external data
- **Only use when tools are explicitly needed**

```python
# Simple prompt - one LLM call (DEFAULT)
result = prompt("summarize", variables={"text": long_text}, model="gpt-4.1", log=True)

# Agent - multiple turns, tool calling (ONLY when tools needed)
result = agent_prompt(
    "research-company",
    variables={"company": "Acme Corp"},
    model="gpt-4.1",
    agent_type="firecrawl",  # Has scrape, search, map tools
    log=True
)
# Agent might: search web → scrape homepage → scrape about page → synthesize
```

### Tool Usage by Model Type

| API | How Tools Work | Available Tools |
|-----|----------------|-----------------|
| **Chat Completions** | No built-in tools | Use Agent SDK for tools |
| **Responses API** (deep research) | `web_search_preview` built-in | Automatic web search |
| **Agent SDK** | `@function_tool` decorators | Firecrawl (scrape/search/map), WebSearch |

### Deep Research (Responses API)

Deep research models (`o4-mini-deep-research`, `o3-deep-research`) automatically use web search:

```python
# This automatically searches the web, takes 5-10 minutes
result = prompt(
    "research-topic",
    variables={"query": "renewable energy trends 2025"},
    model="o4-mini-deep-research",
    background=True,  # REQUIRED - returns response_id
    log=True
)

# Poll for completion
from workers.ai import poll_research
status = poll_research(result["response_id"])
```

### Agent Tools Available

| Agent Type | Tools | Best For |
|------------|-------|----------|
| `research` | WebSearchTool | Quick web searches, fact verification |
| `firecrawl` | scrape, search, map | Website scraping, data extraction |
| `full` | WebSearchTool + Firecrawl | Complex research needing both |

## Available Models

See [reference/available-models.md](reference/available-models.md) for full list.

| Model | Use Case | Background? |
|-------|----------|-------------|
| `gpt-4.1` | Default, fast, good quality | No |
| `gpt-4.1-mini` | Cheaper, still capable | No |
| `gpt-5.2` | Best quality | No |
| `o4-mini` | Reasoning tasks | No |
| `o4-mini-deep-research` | Web research (5-10 min) | **Yes** |
| `gemini-2.5-flash` | Fast with grounded search | No |

## File Locations

| Artifact | Location | Example |
|----------|----------|---------|
| Directive | `directives/{slug}.md` | `directives/entity-research.md` |
| Prompt | `prompts/{slug}.md` | `prompts/entity-research.md` |
| Worker | `workers/{category}/{name}.py` | `workers/research/entity.py` |
| API Endpoint | `api/main.py` | Add new route |

## Integration Checklist

After implementing:

- [ ] Prompt file created in `prompts/`
- [ ] Worker file created with `log=True`
- [ ] API endpoint added (if needed)
- [ ] Added to `template_runners` in `workers/runner.py` (if registry-based)
- [ ] Registered in Supabase `automations` table (if tracked)
- [ ] Test run completed
- [ ] **Verified in `execution_logs` table** (critical!)

## Logging Requirements (NON-NEGOTIABLE)

Every automation MUST log. No exceptions.

### Option 1: Automatic via `log=True`

```python
result = prompt("name", vars, model="gpt-4.1", log=True, tags=["tag1"])
```

### Option 2: Manual via ExecutionLogger

```python
from workers.logger import ExecutionLogger

log = ExecutionLogger("worker.name", input_data, tags=["tag1"])
try:
    result = do_work()
    log.success(result)
except Exception as e:
    log.fail(e)
```

### What Gets Logged

| Field | Description |
|-------|-------------|
| `worker_name` | e.g., `ai.prompt.gpt-4.1` |
| `automation_slug` | e.g., `entity-research` |
| `input` | Full input parameters |
| `output` | Full output response |
| `runtime_seconds` | Execution time |
| `status` | `running`, `success`, `failed` |
| `tags` | Filterable tags |
| `metadata` | Progress updates, stats |

## Prompt File Format

```markdown
# prompts/{slug}.md

{System context or instructions}

## Input
{{variable_name}}

## Task
{What the LLM should do}

## Output Format
{Expected output structure}
```

Variables use `{{variable}}` syntax and are interpolated at runtime.

## Common Patterns

### Adding to Runner (Registry-Based)

```python
# workers/runner.py - add to template_runners dict
template_runners = {
    # ... existing
    "my_template": "workers.category.my_worker:run",
}
```

### Adding API Endpoint

```python
# api/main.py
@app.post("/automations/my-automation")
def run_my_automation(request: MyRequest):
    from workers.category.my_worker import run
    return run(request.dict())
```

## Anti-Patterns

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| `log=False` | No observability | Always `log=True` |
| No tags | Can't filter logs | Add meaningful tags |
| Sync deep research | Times out | Use `background=True` |
| Hardcoded model | Inflexible | Use directive's AI Configuration |
| No error handling | Silent failures | Wrap in try/except with log.fail() |

## Self-Annealing

After any implementation issue:
1. Document in `LEARNINGS.md`
2. Update this skill if pattern needs change
3. Update templates if structure needs refinement

See `LEARNINGS.md` for known issues and fixes.
