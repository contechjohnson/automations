# OpenAI API Reference for Dossier Pipeline

This document consolidates OpenAI documentation relevant to building the v2 dossier pipeline.

---

## Quick Reference

| API | Use Case | Module |
|-----|----------|--------|
| **Chat Completions** | Standard LLM calls (gpt-4.1, gpt-5.2, o4-mini) | `workers/ai.py` |
| **Responses API** | Deep research with web search (o4-mini-deep-research) | `workers/ai.py` |
| **Agents SDK** | Multi-turn tool-using agents (Firecrawl) | `workers/agent.py` |
| **Structured Outputs** | Guaranteed JSON schema compliance | Not yet implemented |

---

## 1. Chat Completions API

**Official Docs:** https://platform.openai.com/docs/api-reference/chat

The standard API for single-turn LLM calls. Used for most pipeline steps.

### Supported Models

| Model | Cost (in/out per 1M) | Use Case |
|-------|---------------------|----------|
| `gpt-4.1` | $2 / $8 | Default, fast |
| `gpt-4.1-mini` | $0.4 / $1.6 | Cheaper, still good |
| `gpt-4.1-nano` | $0.1 / $0.4 | Fastest, cheapest |
| `gpt-5.2` | $10 / $30 | Best quality |
| `o4-mini` | $1.1 / $4.4 | Reasoning |

### Basic Pattern

```python
from openai import OpenAI
client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4.1",
    messages=[
        {"role": "system", "content": "You are a research assistant."},
        {"role": "user", "content": "Research this company: Acme Corp"}
    ],
    temperature=0.7,
)

output = response.choices[0].message.content
```

### Current Implementation (`workers/ai.py`)

```python
from workers.ai import ai, prompt

# Direct call (no logging)
result = ai("What is 2+2?", model="gpt-4.1")

# With prompt file + logging
result = prompt(
    "entity-research",
    variables={"lead": {...}, "clientName": "Acme"},
    model="gpt-4.1",
    log=True,
    tags=["entity-research"]
)
```

---

## 2. Responses API (Deep Research)

**Official Docs:**
- https://platform.openai.com/docs/guides/deep-research
- https://cookbook.openai.com/examples/deep_research_api/introduction_to_deep_research_api

The Responses API supports deep research models that can browse the web autonomously for 5-30 minutes.

### Deep Research Models

| Model | Cost (in/out per 1M) | Speed |
|-------|---------------------|-------|
| `o4-mini-deep-research` | $2 / $8 | Faster, lighter |
| `o3-deep-research` | $10 / $40 | More thorough |

### Key Characteristics

- Takes **5-30 minutes** to complete
- Must include at least one data source tool (web search, file search, or MCP)
- Use `background=True` for production (returns immediately with response_id)
- Model does NOT ask clarifying questions - prompts must be fully-formed
- Returns output with inline citations and source metadata

### Background Mode Pattern

```python
from openai import OpenAI
client = OpenAI()

# Start research (returns immediately)
response = client.responses.create(
    model="o4-mini-deep-research-2025-06-26",
    input="Research Acme Corp's expansion plans",
    tools=[{"type": "web_search_preview"}],
    background=True,
    reasoning={"summary": "auto"},
)

response_id = response.id  # Save this for polling

# Poll for completion
response = client.responses.retrieve(response_id)
if response.status == "completed":
    output = response.output_text
```

### Current Implementation (`workers/ai.py`)

```python
from workers.ai import research, poll_research, prompt

# Direct deep research
result = research("Research Acme Corp", model="o4-mini-deep-research", background=True)
response_id = result["response_id"]

# Poll for results
result = poll_research(response_id)
if result["status"] == "completed":
    output = result["output"]

# Via prompt file
result = prompt(
    "deep-research",
    variables={"entity": "Acme Corp"},
    model="o4-mini-deep-research",
    background=True,
    log=True
)
```

### Output Structure

The Responses API returns:
- `output` array with message items
- Each message has `content` with `text` and `annotations`
- Annotations contain source URLs and metadata

```python
# Parsing deep research output
for item in response.output:
    if hasattr(item, 'content'):
        for content in item.content:
            if hasattr(content, 'text'):
                print(content.text)
            if hasattr(content, 'annotations'):
                for ann in content.annotations:
                    print(f"Source: {ann.url}")
```

### Tool Call Tracing

Deep research returns tool call traces:
- `web_search_call` - Web searches performed
- `code_interpreter_call` - Code execution (if enabled)
- `mcp_tool_call` - MCP server calls (if configured)
- `file_search_call` - Vector store searches (if configured)

### Safety Considerations

1. **Prompt injection risk** - Web search results could contain malicious instructions
2. **Data exfiltration risk** - Model could leak data via tool calls to untrusted servers
3. **Mitigation** - Only enable trusted tools, stage workflows, log all tool calls

---

## 3. Agents SDK

**Official Docs:**
- https://github.com/openai/openai-agents-python
- https://platform.openai.com/docs/guides/agents-sdk

The Agents SDK enables multi-turn, tool-using agent workflows.

### Core Concepts

| Concept | Description |
|---------|-------------|
| **Agent** | LLM configured with instructions and tools |
| **Runner** | Executes agent loops until completion |
| **Function Tools** | Python functions exposed to the model |
| **WebSearchTool** | Built-in web search capability |
| **Handoffs** | Transfer control between agents |
| **Guardrails** | Input/output validation |

### Installation

```bash
pip install openai-agents
```

### Creating an Agent

```python
from agents import Agent, Runner, function_tool, WebSearchTool

@function_tool
def scrape_website(url: str) -> str:
    """Scrape a webpage and return its content."""
    # Implementation
    return content

agent = Agent(
    name="Research Agent",
    model="gpt-4.1",
    instructions="You are a research assistant. Use tools to gather information.",
    tools=[WebSearchTool(), scrape_website],
)

# Run synchronously
result = Runner.run_sync(agent, "Research Acme Corp")
print(result.final_output)

# Run asynchronously
result = await Runner.run(agent, "Research Acme Corp")
```

### Current Implementation (`workers/agent.py`)

Three pre-configured agent types:

```python
from workers.agent import (
    run_research_agent,    # Web search only
    run_firecrawl_agent,   # Firecrawl tools (scrape, search, map)
    run_full_agent,        # Web search + Firecrawl
    agent_prompt,          # With prompt file
)

# Research agent (web search)
result = run_research_agent("Research Acme Corp's recent projects")

# Firecrawl agent (scraping)
result = run_firecrawl_agent("Scrape acmecorp.com and summarize services")

# Full agent (both)
result = run_full_agent("Comprehensive research on Acme Corp")

# With prompt file
result = agent_prompt(
    "entity-research",
    variables={"entity": "Acme Corp"},
    model="gpt-4.1",
    agent_type="firecrawl",
    log=True
)
```

### Firecrawl Tools Available

| Tool | Description |
|------|-------------|
| `firecrawl_scrape(url)` | Get full page content as markdown |
| `firecrawl_search(query, limit)` | Search web and scrape results |
| `firecrawl_map(url, limit)` | Discover all URLs on a site |

### Agent vs Direct API

| Feature | Agent SDK | Direct API |
|---------|-----------|------------|
| **Tool calling** | Automatic loop | Manual handling |
| **Multi-turn** | Built-in | Manual state management |
| **Tracing** | Built-in | Manual logging |
| **Use case** | Complex research | Simple transformations |

---

## 4. Structured Outputs

**Official Docs:**
- https://platform.openai.com/docs/guides/structured-outputs
- https://cookbook.openai.com/examples/structured_outputs_intro

Structured Outputs guarantee the model's response matches a JSON schema exactly.

### Why Use Structured Outputs?

| Feature | JSON Mode | Structured Outputs |
|---------|-----------|-------------------|
| Valid JSON | Yes | Yes |
| Schema adherence | Best effort | **Guaranteed** |
| Reliability | ~40% compliance | **100% compliance** |

### Enabling Structured Outputs

```python
from openai import OpenAI
from pydantic import BaseModel

class Claim(BaseModel):
    claim_id: str
    claim_type: str  # SIGNAL | CONTACT | ENTITY | etc.
    statement: str
    source_url: str
    source_tier: str  # GOV | PRIMARY | NEWS | OTHER
    confidence: str  # HIGH | MEDIUM | LOW

class ClaimsOutput(BaseModel):
    claims: list[Claim]

client = OpenAI()

response = client.responses.parse(
    model="gpt-4o-2024-08-06",  # Must support structured outputs
    input=[
        {"role": "system", "content": "Extract claims from this research."},
        {"role": "user", "content": research_text}
    ],
    text_format=ClaimsOutput,
)

claims = response.output_parsed.claims  # Type-safe access
```

### JSON Schema Method (Without Pydantic)

```python
response = client.chat.completions.create(
    model="gpt-4o-2024-08-06",
    messages=[...],
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "claims_output",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "claims": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "claim_id": {"type": "string"},
                                "statement": {"type": "string"},
                                # ...
                            },
                            "required": ["claim_id", "statement"],
                            "additionalProperties": False
                        }
                    }
                },
                "required": ["claims"],
                "additionalProperties": False
            }
        }
    }
)
```

### Supported Models

- `gpt-4o-2024-08-06` and later
- `gpt-4o-mini-2024-07-18` and later
- `gpt-4.1` (check latest docs for support)

### Limitations

- Root must be an object (not array or anyOf at top level)
- All fields must be `required` (use `"type": ["string", "null"]` for optional)
- Max 100 object properties
- Max 5 nesting levels
- Max 1000 enum values total
- Max 120,000 chars for all property names + enum values combined

### Edge Cases

```python
# Handle truncation
if response.status == "incomplete":
    if response.incomplete_details.reason == "max_output_tokens":
        # Response was cut off - increase max_tokens or chunk input
        pass

# Handle refusals
if response.output[0].content[0].type == "refusal":
    # Model refused due to safety - adjust prompt
    refusal_reason = response.output[0].content[0].refusal
```

---

## 5. Recommended Architecture for v2 Pipeline

### Step-by-API Mapping

| Pipeline Step | API | Model | Notes |
|---------------|-----|-------|-------|
| Search Builder | Chat Completions | gpt-4.1-mini | Fast, simple |
| Signal Discovery | Chat Completions | gpt-4.1 | With structured output |
| Entity Research | **Deep Research** | o4-mini-deep-research | Background mode |
| Contact Discovery | Agents SDK | gpt-4.1 + Firecrawl | Multi-turn scraping |
| Enrich Lead | Chat Completions | gpt-4.1 | With structured output |
| Enrich Opportunity | Chat Completions | gpt-4.1 | With structured output |
| Client Specific | Chat Completions | gpt-4.1 | With structured output |
| Insight (Merge) | Chat Completions | gpt-4.1 | Structured output for claims |
| Dossier Plan | Chat Completions | gpt-4.1 | Routing decisions |
| Section Writers | Chat Completions | gpt-4.1 | Parallel execution |

### Claims Extraction Pattern

For steps that produce claims, use Structured Outputs:

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class ClaimType(str, Enum):
    SIGNAL = "SIGNAL"
    CONTACT = "CONTACT"
    ENTITY = "ENTITY"
    RELATIONSHIP = "RELATIONSHIP"
    OPPORTUNITY = "OPPORTUNITY"
    METRIC = "METRIC"
    ATTRIBUTE = "ATTRIBUTE"
    NOTE = "NOTE"

class SourceTier(str, Enum):
    GOV = "GOV"
    PRIMARY = "PRIMARY"
    NEWS = "NEWS"
    OTHER = "OTHER"

class Confidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class Claim(BaseModel):
    claim_id: str = Field(description="Prefixed ID like entity_001")
    claim_type: ClaimType
    statement: str = Field(max_length=500, description="One atomic fact")
    entities: List[str] = Field(default_factory=list)
    date_in_claim: Optional[str] = Field(default=None, description="YYYY-MM-DD")
    source_url: Optional[str] = None
    source_name: str
    source_tier: SourceTier
    confidence: Confidence

class ClaimsOutput(BaseModel):
    claims: List[Claim]
    summary: str = Field(description="2-3 sentence summary of findings")
```

### Deep Research + Claims Extraction Pattern

Two-stage approach:

```python
# Stage 1: Deep research (5-10 min)
research_result = prompt(
    "entity-research-deep",
    variables={"entity": entity_name},
    model="o4-mini-deep-research",
    background=True,
    log=True
)
response_id = research_result["response_id"]

# Poll until complete
while True:
    result = poll_research(response_id)
    if result["status"] == "completed":
        break
    time.sleep(30)

# Stage 2: Extract claims with structured output
claims_result = client.responses.parse(
    model="gpt-4o-2024-08-06",
    input=[
        {"role": "system", "content": CLAIMS_EXTRACTION_PROMPT},
        {"role": "user", "content": result["output"]}
    ],
    text_format=ClaimsOutput,
)

claims = claims_result.output_parsed.claims
```

---

## 6. Error Handling

### Rate Limits

```python
from openai import RateLimitError
import time

def call_with_retry(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError:
            wait = 2 ** attempt
            time.sleep(wait)
    raise Exception("Max retries exceeded")
```

### Timeouts

```python
from openai import OpenAI
import httpx

# Set longer timeout for deep research
client = OpenAI(
    timeout=httpx.Timeout(600.0, connect=10.0)  # 10 min
)
```

### Validation Errors

```python
from pydantic import ValidationError

try:
    result = ClaimsOutput.model_validate_json(response.content)
except ValidationError as e:
    # Log and handle schema mismatch
    logger.error(f"Schema validation failed: {e}")
```

---

## 7. Cost Estimation

### Per-Dossier Cost Estimate

| Step | Model | Tokens (in/out) | Cost |
|------|-------|-----------------|------|
| Search Builder | gpt-4.1-mini | 500/200 | $0.0005 |
| Signal Discovery | gpt-4.1 | 2000/1500 | $0.016 |
| Entity Research | o4-mini-deep-research | 2000/5000 | $0.044 |
| Contact Discovery | gpt-4.1 (agent, ~5 turns) | 10000/5000 | $0.06 |
| Enrich Lead | gpt-4.1 | 2000/1500 | $0.016 |
| Enrich Opportunity | gpt-4.1 | 2000/1500 | $0.016 |
| Client Specific | gpt-4.1 | 2000/1500 | $0.016 |
| Insight (Merge) | gpt-4.1 | 5000/3000 | $0.034 |
| Dossier Plan | gpt-4.1 | 1500/1000 | $0.011 |
| Section Writers (6x) | gpt-4.1 | 12000/8000 | $0.088 |

**Estimated total per dossier: ~$0.30**

---

## Links

| Resource | URL |
|----------|-----|
| OpenAI Platform | https://platform.openai.com |
| API Reference | https://platform.openai.com/docs/api-reference |
| Python SDK | https://github.com/openai/openai-python |
| Agents SDK | https://github.com/openai/openai-agents-python |
| Deep Research Guide | https://platform.openai.com/docs/guides/deep-research |
| Structured Outputs | https://platform.openai.com/docs/guides/structured-outputs |
| Cookbook | https://cookbook.openai.com |
| Pricing | https://openai.com/api/pricing |

---

## Related Documents

- [CLAIMS_SYSTEM.md](./CLAIMS_SYSTEM.md) - How claims work in the pipeline
- [CLAIMS_STORAGE_SCHEMA.md](./CLAIMS_STORAGE_SCHEMA.md) - Supabase tables for claims
- [PROMPT_WORKBENCH.md](./PROMPT_WORKBENCH.md) - Admin dashboard requirements
