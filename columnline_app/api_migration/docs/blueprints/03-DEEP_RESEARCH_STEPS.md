# 03_AND_04_SEQUENTIAL_DEEP_RESEARCH_STEPS

**Source file:** `03_AND_04_SEQUENTIAL_DEEP_RESEARCH_STEPS.blueprint.json`
**Total modules:** 39
**Execution mode:** Async (called via START_ASYNC_DEEP_ENTITY_AND_CONTACTS)

## Purpose

Deep research phase that resolves entity details and discovers contacts. This is one of the longest-running steps, using OpenAI's deep research model with `background: true` for extended web research.

## Module Flow

### Part 1: Entity Research (Modules 1-18)

```
1. StartSubscenario (entry point)
   ↓
2. getCell: ENTITY_RESEARCH_PROMPT (Prompts!C4)
3. getCell: ENTITY_RESEARCH_LIVE_INPUT (Prompts!D4)
   ↓
4. createModelResponse: ENTITY_RESEARCH
   → Model: o4-mini-deep-research
   → background: true
   → max_output_tokens: 200000
   ↓
5. SetVariable: entity_research_response_id
   ↓
6-11. POLLING LOOP:
   6. BasicRepeater
   7. GetVariable
   8. Sleep 30s
   9. getModelResponse (poll status)
   10. Break if complete
   11. SetVariable done
   ↓
12. ExecuteCode: Parse response
   ↓
13. updateCell: ENTITY_RESEARCH_LIVE_OUTPUT (Prompts!E4)
   ↓
14. createModelResponse: PRODUCE_CLAIMS
   ↓
15. updateCell: SET_CLAIMS (Prompts!I4)
   ↓
16. createModelResponse: CONTEXT_PACK
   ↓
17. updateCell: SET_CONTEXT_PACK (Prompts!K4)
18. updateCell: SET_NEXT_INPUT (Prompts!D5) - chain to contacts
```

### Part 2: Contact Discovery (Modules 19-39)

Same pattern as Entity Research:

```
19. getCell: CONTACT_DISCOVERY_PROMPT (Prompts!C5)
20. getCell: CONTACT_DISCOVERY_LIVE_INPUT (Prompts!D5)
   ↓
21. createModelResponse: CONTACT_DISCOVERY
   → Model: o4-mini-deep-research
   → background: true
   → max_output_tokens: 200000
   ↓
22-27. POLLING LOOP (same pattern)
   ↓
28. ExecuteCode: Parse contacts
   ↓
29. updateCell: CONTACT_DISCOVERY_LIVE_OUTPUT (Prompts!E5)
   ↓
30. createModelResponse: PRODUCE_CLAIMS
   ↓
31. updateCell: SET_CLAIMS (Prompts!I5)
   ↓
32. createModelResponse: CONTEXT_PACK
   ↓
33-39. Final outputs and chaining
```

## LLM Calls (8)

| Step | Name | Model | Mode | Purpose |
|------|------|-------|------|---------|
| 4 | ENTITY_RESEARCH | o4-mini-deep-research | Async | Deep company research |
| 9 | Poll response | - | Poll | Check completion |
| 14 | PRODUCE_CLAIMS | gpt-4.1 | Sync | Extract claims |
| 16 | CONTEXT_PACK | gpt-4.1 | Sync | Build context pack |
| 21 | CONTACT_DISCOVERY | o4-mini-deep-research | Async | Find contacts |
| 27 | Poll response | - | Poll | Check completion |
| 30 | PRODUCE_CLAIMS | gpt-4.1 | Sync | Extract claims |
| 32 | CONTEXT_PACK | gpt-4.1 | Sync | Build context pack |

## Sheets Operations (18)

Two parallel sets for entity + contacts:

| Phase | Cells |
|-------|-------|
| Entity Research | C4, D4, E4, I4, K4 |
| Contact Discovery | C5, D5, E5, I5, K5 |

## Deep Research Pattern

This blueprint demonstrates the async deep research pattern:

```python
# Conceptual equivalent
response_id = await openai.responses.create(
    model="o4-mini-deep-research",
    input=prompt,
    background=True,
    tools=[{"type": "web_search_preview"}],
    max_output_tokens=200000
)

# Poll until complete
while True:
    response = await openai.responses.retrieve(response_id)
    if response.status == "completed":
        return response.output
    await asyncio.sleep(30)
```

## Context Pack System

After each research step, a CONTEXT_PACK is generated:

```json
{
  "entity_context": {
    "company_name": "...",
    "domain": "...",
    "key_facts": [...],
    "recent_news": [...],
    "leadership": [...]
  }
}
```

Context packs are stored in column K and used by downstream steps.

## Claims System

Same as other steps - atomic fact extraction:

| Field | Purpose |
|-------|---------|
| claim_id | ENTITY_001, CONTACT_001 |
| claim_type | entity_fact, contact_info |
| statement | The atomic claim |
| source_url | Where it came from |
| confidence | high/medium/low |

## Migration Considerations

1. **Long-running** - Can take 5-10 minutes per research call
2. **2 sequential deep research calls** - Could potentially parallelize
3. **Heavy token usage** - 200k max output tokens
4. **Internal polling loop** - Make.com polls OpenAI, we need to do the same
5. **Context pack output** - Critical for downstream steps
