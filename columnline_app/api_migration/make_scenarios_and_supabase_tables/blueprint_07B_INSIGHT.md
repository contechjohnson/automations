# 07B_INSIGHT

**Source file:** `07B_INSIGHT.blueprint.json`
**Total modules:** 15
**Execution mode:** Sync (called via RUN_SYNC_AGENT_INSIGHT)

## Purpose

The **claims merge and insight synthesis** step. Collects all claims from previous research steps, merges/deduplicates them, and generates strategic insights. This is a critical junction point in the pipeline.

## Module Flow

```
1. StartSubscenario (entry point)
   ↓
2. getCell: INSIGHT_PROMPT (Prompts!C12)
3. getCell: INSIGHT_LIVE_INPUT (Prompts!D12)
4. getCell: GET_MERGE_CLAIMS_PROMPT (Prompts!D12)
5. getCell: GET_CONTEXT_PACK_PROMPT (Prompts!D12)
   ↓
6. getSheetContent: Read all claims (Prompts sheet)
   → Reads columns I (claims) from all rows
   ↓
7. TextAggregator: Combine all claims
   ↓
8. createModelResponse: MERGE_CLAIMS
   → Model: gpt-4.1
   → Deduplicates and reconciles claims
   ↓
9. updateCell: MERGED_CLAIMS_OUTPUT (Prompts!)
   ↓
10. createModelResponse: INSIGHT
    → Model: gpt-4.1
    → Generates strategic analysis
    ↓
11. updateCell: INSIGHT_LIVE_OUTPUT (Prompts!E12)
    ↓
12. createModelResponse: CONTEXT_PACK
    → Builds final context pack for writers
    ↓
13. updateCell: SET_CONTEXT_PACK (Prompts!K12)
14-15. Additional outputs
```

## LLM Calls (3)

| Step | Name | Model | Purpose |
|------|------|-------|---------|
| 8 | MERGE_CLAIMS | gpt-4.1 | Deduplicate & reconcile claims |
| 10 | INSIGHT | gpt-4.1 | Strategic analysis synthesis |
| 12 | CONTEXT_PACK | gpt-4.1 | Build final context for writers |

## Sheets Operations (10)

| Cell | Operation | Purpose |
|------|-----------|---------|
| Prompts!C12 | getCell | INSIGHT_PROMPT |
| Prompts!D12 | getCell | INSIGHT_LIVE_INPUT |
| Prompts!D12 | getCell | GET_MERGE_CLAIMS_PROMPT |
| Prompts!D12 | getCell | GET_CONTEXT_PACK_PROMPT |
| Prompts! | getSheetContent | Read ALL claims |
| Prompts! | updateCell | MERGED_CLAIMS_OUTPUT |
| Prompts!E12 | updateCell | INSIGHT_LIVE_OUTPUT |
| Prompts!K12 | updateCell | SET_CONTEXT_PACK |

## Claims Merge Process

### Input Claims (from multiple sources)

```
Row 2 (I2): Search & Signal claims
Row 3 (I3): Signal discovery claims
Row 4 (I4): Entity research claims
Row 5 (I5): Contact discovery claims
Row 6 (I6): Enrich lead claims
Row 7 (I7): Enrich opportunity claims
Row 8 (I8): Client specific claims
```

### Merge Logic

The MERGE_CLAIMS prompt:
1. Reads all claims from column I
2. Identifies duplicates (same fact, different sources)
3. Reconciles conflicts (contradictory claims)
4. Assigns confidence scores
5. Groups by claim type

### Output: Merged Claims

```json
{
  "merged_claims": [
    {
      "claim_id": "MERGED_001",
      "original_ids": ["ENTITY_003", "LEAD_001"],
      "claim_type": "company_signal",
      "statement": "Acme Corp expanding into APAC market",
      "sources": [
        {"url": "...", "name": "Press Release"},
        {"url": "...", "name": "LinkedIn Post"}
      ],
      "confidence": "high",
      "conflicts_resolved": []
    }
  ]
}
```

## Insight Generation

After merge, the INSIGHT prompt generates:

```json
{
  "strategic_analysis": {
    "opportunity_summary": "...",
    "key_signals": [...],
    "recommended_approach": "...",
    "timing_factors": [...],
    "risk_factors": [...],
    "competitive_landscape": "...",
    "executive_summary": "..."
  }
}
```

## Context Pack Output

The final CONTEXT_PACK prepares data for writers:

```json
{
  "context_pack": {
    "company": {...},
    "contacts": [...],
    "signals": [...],
    "merged_claims": [...],
    "insight": {...},
    "client_context": {...}
  }
}
```

This context pack is stored in Prompts!K12 and read by 09_DOSSIER_PLAN.

## Critical Role

This is the **synchronization point** in the pipeline:

```
                        ┌── Enrich Lead ──┐
Signal Discovery ─┬────►│  Enrich Opp   │────┐
                  │     │  Client Spec  │    │
Entity Research ──┘     │  Media        │    │
Contact Discovery ──────┴────────────────┘    │
                                              ▼
                                    ┌─────────────────┐
                                    │   07B_INSIGHT   │
                                    │  ═══════════════│
                                    │  Merge Claims   │
                                    │  Generate Insight│
                                    │  Build Context  │
                                    └─────────────────┘
                                              │
                                              ▼
                                    09_DOSSIER_PLAN + Writers
```

## Migration Notes

1. **Sync execution** - Blocks pipeline (writers need this output)
2. **Claims aggregation** - Must collect claims from all prior steps
3. **No async/polling** - This is a quick sync operation
4. **Critical output** - Context pack feeds all 6 writers
5. **getSheetContent** - Reads multiple rows, needs equivalent query
