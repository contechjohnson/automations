# Available Models

Reference for all models available in `workers/ai.py`.

## Standard Models (Chat Completions API)

| Model ID | Actual API Model | Use Case |
|----------|------------------|----------|
| `gpt-4.1` | `gpt-4.1` | Default, fast, good quality |
| `gpt-4.1-mini` | `gpt-4.1-mini` | Cheaper, still capable |
| `gpt-4.1-nano` | `gpt-4.1-nano` | Cheapest, basic tasks |
| `gpt-5.2` | `gpt-5.2` | Best quality, complex reasoning |
| `o3` | `o3` | Advanced reasoning |
| `o4-mini` | `o4-mini` | Reasoning, efficient |

## Deep Research Models (Responses API)

**WARNING:** These models take 5-10 minutes. ALWAYS use `background=True`.

| Model ID | Actual API Model | Use Case |
|----------|------------------|----------|
| `o4-mini-deep-research` | `o4-mini-deep-research-2025-06-26` | Web research with sources |
| `o3-deep-research` | `o3-deep-research-2025-06-26` | Heavy research tasks |

### Deep Research Usage

```python
# START research (returns immediately)
result = prompt(
    "research-topic",
    variables={"query": "..."},
    model="o4-mini-deep-research",
    background=True,  # REQUIRED
    log=True
)
# Returns: {"response_id": "...", "status": "submitted"}

# POLL for completion
from workers.ai import poll_research
status = poll_research(result["response_id"])
# Returns: {"status": "completed", "output": "...", "annotations": [...]}
```

## Gemini Models (Optional)

Requires `GOOGLE_API_KEY` in environment.

| Model ID | Actual API Model | Use Case |
|----------|------------------|----------|
| `gemini-2.5-flash` | `gemini-2.5-flash-preview-05-20` | Fast, grounded search |
| `gemini-2.5-pro` | `gemini-2.5-pro-preview-06-05` | High quality |
| `gemini-3-flash` | `gemini-3.0-flash-preview` | Latest flash |

### Gemini Usage

```python
from workers.ai import gemini

result = gemini("What is the capital of France?", model="gemini-2.5-flash")
```

## Model Selection Guide

| Task | Recommended Model | Notes |
|------|-------------------|-------|
| General tasks | `gpt-4.1` | Default choice |
| High volume, simple | `gpt-4.1-mini` | Cost-effective |
| Complex reasoning | `gpt-5.2` or `o4-mini` | More expensive |
| Web research | `o4-mini-deep-research` | 5-10 min, background only |
| Grounded facts | `gemini-2.5-flash` | Has search grounding |

## Adding New Models

Edit `workers/ai.py`:

```python
OPENAI_MODELS = {
    # ... existing
    "new-model": "new-model-api-id",
}
```

For deep research models, also add to `DEEP_RESEARCH_MODELS` list.
