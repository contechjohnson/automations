# 05C_CLIENT_SPECIFIC

**Source file:** `05C_CLIENT_SPECIFIC.blueprint.json`
**Total modules:** 14
**Execution mode:** Async (called via START_ASYNC_AGENT_CLIENT_SPECIFIC)

## Purpose

Research tailored to the specific client's needs, products, and competitive positioning. Uses client context to find relevant connections between the lead and the client's offerings.

## Module Flow

Identical structure to 05A and 05B:

```
1. StartSubscenario (entry point)
   ↓
2. getCell: CLIENT_SPECIFIC_PROMPT (Prompts!C8)
3. getCell: CLIENT_SPECIFIC_LIVE_INPUT (Prompts!D8)
   ↓
4. createModelResponse: CLIENT_SPECIFIC
   → Model: o4-mini-deep-research
   → background: true
   ↓
5-10. POLLING LOOP
   ↓
11. ExecuteCode: Parse response
   ↓
12. updateCell: CLIENT_SPECIFIC_LIVE_OUTPUT (Prompts!E8)
   ↓
13. createModelResponse: PRODUCE_CLAIMS
   ↓
14. updateCell: SET_CLAIMS (Prompts!I8)
```

## LLM Calls (3)

| Step | Name | Model | Mode | Purpose |
|------|------|-------|------|---------|
| 4 | CLIENT_SPECIFIC | o4-mini-deep-research | Async | Client-tailored research |
| 9 | Poll response | - | Poll | Check completion |
| 13 | PRODUCE_CLAIMS | gpt-4.1 | Sync | Extract claims |

## Sheets Operations (4)

| Cell | Operation | Purpose |
|------|-----------|---------|
| Prompts!C8 | getCell | CLIENT_SPECIFIC_PROMPT |
| Prompts!D8 | getCell | CLIENT_SPECIFIC_LIVE_INPUT |
| Prompts!E8 | updateCell | CLIENT_SPECIFIC_LIVE_OUTPUT |
| Prompts!I8 | updateCell | SET_CLAIMS |

## Input Context

This step receives:
- Entity context (from 03/04)
- **RESEARCH_CONTEXT** - Client's specific context including:
  - Client company info
  - Products/services offered
  - Target personas
  - Competitive differentiators
  - Past wins in similar accounts

## Output Focus

Client-specific intelligence:
- How lead's needs map to client offerings
- Competitor presence at the account
- Relevant case studies/references
- Pain points that match client solutions
- Timing/trigger events

## Claims Produced

```json
{
  "claims": [
    {
      "claim_id": "CLIENT_001",
      "claim_type": "product_fit",
      "statement": "Lead uses competitor Salesforce, client has migration playbook",
      "confidence": "high"
    },
    {
      "claim_id": "CLIENT_002",
      "claim_type": "reference_match",
      "statement": "Client won similar deal at Acme Industries in 2024",
      "confidence": "high"
    }
  ]
}
```

## Parallel Execution Context

Part of "Parallel Batch 1":

```
START_ASYNC_DEEP_ENRICH_LEAD ────────┐
START_ASYNC_AGENT_ENRICH_MEDIA ──────┼─→ Poll all 4 together
START_ASYNC_AGENT_ENRICH_OPPORTUNITY ┤
START_ASYNC_AGENT_CLIENT_SPECIFIC ───┘ (this)
```

## Unique Characteristics

Unlike 05A/05B which are more generic:
- This step is **personalized per client**
- Uses RESEARCH_CONTEXT which varies by client
- Produces claims that directly tie to sales strategy
- Feeds the CLIENT_SPECIFIC dossier section

## Migration Notes

- Same base implementation as 05A/05B
- Prompt in C8 is client-aware
- Claims critically important for WRITER_CLIENT_SPECIFIC
