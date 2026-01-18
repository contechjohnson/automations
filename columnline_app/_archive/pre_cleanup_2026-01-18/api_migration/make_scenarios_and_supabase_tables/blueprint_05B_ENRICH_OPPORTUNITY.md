# 05B_ENRICH_OPPORTUNITY

**Source file:** `05B_ENRICH_OPPORTUNITY.blueprint.json`
**Total modules:** 14
**Execution mode:** Async (called via START_ASYNC_AGENT_ENRICH_OPPORTUNITY)

## Purpose

Research focused on opportunity sizing, deal potential, and business value assessment. Runs in parallel with 05A, 05C, and 08.

## Module Flow

Identical structure to 05A_ENRICH_LEAD:

```
1. StartSubscenario (entry point)
   ↓
2. getCell: ENRICH_OPPORTUNITY_PROMPT (Prompts!C7)
3. getCell: ENRICH_OPPORTUNITY_LIVE_INPUT (Prompts!D7)
   ↓
4. createModelResponse: ENRICH_OPPORTUNITY
   → Model: o4-mini-deep-research
   → background: true
   ↓
5-10. POLLING LOOP
   ↓
11. ExecuteCode: Parse response
   ↓
12. updateCell: ENRICH_OPPORTUNITY_LIVE_OUTPUT (Prompts!E7)
   ↓
13. createModelResponse: PRODUCE_CLAIMS
   ↓
14. updateCell: SET_CLAIMS (Prompts!I7)
```

## LLM Calls (3)

| Step | Name | Model | Mode | Purpose |
|------|------|-------|------|---------|
| 4 | ENRICH_OPPORTUNITY | o4-mini-deep-research | Async | Opportunity research |
| 9 | Poll response | - | Poll | Check completion |
| 13 | PRODUCE_CLAIMS | gpt-4.1 | Sync | Extract claims |

## Sheets Operations (4)

| Cell | Operation | Purpose |
|------|-----------|---------|
| Prompts!C7 | getCell | ENRICH_OPPORTUNITY_PROMPT |
| Prompts!D7 | getCell | ENRICH_OPPORTUNITY_LIVE_INPUT |
| Prompts!E7 | updateCell | ENRICH_OPPORTUNITY_LIVE_OUTPUT |
| Prompts!I7 | updateCell | SET_CLAIMS |

## Output Focus

Opportunity sizing research:
- Market size for their segment
- Competitive landscape
- Potential deal value range
- Growth trajectory indicators
- Strategic importance factors

## Claims Produced

```json
{
  "claims": [
    {
      "claim_id": "OPP_001",
      "claim_type": "market_size",
      "statement": "Target market valued at $2.3B with 12% CAGR",
      "confidence": "medium"
    },
    {
      "claim_id": "OPP_002",
      "claim_type": "deal_potential",
      "statement": "Similar deals in segment average $150-250K ACV",
      "confidence": "medium"
    }
  ]
}
```

## Parallel Execution Context

Part of "Parallel Batch 1":

```
START_ASYNC_DEEP_ENRICH_LEAD ────────┐
START_ASYNC_AGENT_ENRICH_MEDIA ──────┼─→ Poll all 4 together
START_ASYNC_AGENT_ENRICH_OPPORTUNITY ┤ (this)
START_ASYNC_AGENT_CLIENT_SPECIFIC ───┘
```

## Migration Notes

- Structurally identical to 05A - can share base implementation
- Different prompt in C7 vs C6
- Claims feed into 07B_INSIGHT merge step
