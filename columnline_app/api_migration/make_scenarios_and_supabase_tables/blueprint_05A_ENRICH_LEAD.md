# 05A_ENRICH_LEAD

**Source file:** `05A_ENRICH_LEAD.blueprint.json`
**Total modules:** 14
**Execution mode:** Async (called via START_ASYNC_DEEP_ENRICH_LEAD)

## Purpose

Enriches lead information with additional research focused on lead qualification, buying signals, and fit assessment. Runs in parallel with 05B, 05C, and 08.

## Module Flow

```
1. StartSubscenario (entry point)
   ↓
2. getCell: ENRICH_LEAD_PROMPT (Prompts!C6)
3. getCell: ENRICH_LEAD_LIVE_INPUT (Prompts!D6)
   ↓
4. createModelResponse: ENRICH_LEAD
   → Model: o4-mini-deep-research
   → background: true
   ↓
5. SetVariable: response_id
   ↓
6-10. POLLING LOOP:
   6. BasicRepeater
   7. GetVariable
   8. Sleep 30s
   9. getModelResponse (poll status)
   10. Break if complete
   ↓
11. ExecuteCode: Parse response
   ↓
12. updateCell: ENRICH_LEAD_LIVE_OUTPUT (Prompts!E6)
   ↓
13. createModelResponse: PRODUCE_CLAIMS
   ↓
14. updateCell: SET_CLAIMS (Prompts!I6)
```

## LLM Calls (3)

| Step | Name | Model | Mode | Purpose |
|------|------|-------|------|---------|
| 4 | ENRICH_LEAD | o4-mini-deep-research | Async | Lead qualification research |
| 9 | Poll response | - | Poll | Check completion |
| 13 | PRODUCE_CLAIMS | gpt-4.1 | Sync | Extract claims |

## Sheets Operations (4)

| Cell | Operation | Purpose |
|------|-----------|---------|
| Prompts!C6 | getCell | ENRICH_LEAD_PROMPT |
| Prompts!D6 | getCell | ENRICH_LEAD_LIVE_INPUT |
| Prompts!E6 | updateCell | ENRICH_LEAD_LIVE_OUTPUT |
| Prompts!I6 | updateCell | SET_CLAIMS |

## Input

Receives from parent pipeline:
- Entity context pack (from step 03/04)
- ICP configuration
- Industry research context

## Output

Lead enrichment including:
- Buying signal strength
- Budget indicators
- Decision maker identification
- Timeline indicators
- Fit score assessment

## Claims Produced

```json
{
  "claims": [
    {
      "claim_id": "LEAD_001",
      "claim_type": "buying_signal",
      "statement": "Company announced digital transformation initiative Q1 2025",
      "confidence": "high"
    },
    {
      "claim_id": "LEAD_002",
      "claim_type": "budget_indicator",
      "statement": "Recently raised $20M Series B",
      "confidence": "medium"
    }
  ]
}
```

## Parallel Execution Context

This runs as part of "Parallel Batch 1" in the main pipeline:

```
START_ASYNC_DEEP_ENRICH_LEAD (this) ─┐
START_ASYNC_AGENT_ENRICH_MEDIA ──────┼─→ Poll all 4 together
START_ASYNC_AGENT_ENRICH_OPPORTUNITY ┤
START_ASYNC_AGENT_CLIENT_SPECIFIC ───┘
```

## Migration Considerations

1. **Standard async pattern** - Same polling loop as other enrichment steps
2. **Parallel execution** - Must support running 4 of these simultaneously
3. **Claims output** - Will be merged in step 07B
4. **Prompt lives in Prompts!C6** - Extract to `prompts/enrich-lead.md`
