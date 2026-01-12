# 01AND02_SEARCH_AND_SIGNAL

**Source file:** `01AND02_SEARCH_AND_SIGNAL.blueprint.json`
**Total modules:** 13
**Execution mode:** Sync (called via RUN_SYNC_SEARCH_AND_SIGNAL)

## Purpose

The first step in the dossier pipeline. Takes client configuration and generates search queries, then discovers signals/leads from web search results.

## Module Flow

```
1. StartSubscenario (entry point)
   ↓
2. getCell: SEARCH_BUILDER_PROMPT (Prompts!C2)
3. getCell: SEARCH_BUILDER_LIVE_INPUT (Prompts!D2)
   ↓
4. createModelResponse: SEARCH_BUILDER
   → Model: o4-mini (reasoning model)
   → Output: Search queries to execute
   ↓
5. updateCell: SEARCH_BUILDER_LIVE_OUTPUT (Prompts!E2)
6. updateCell: SET_NEXT_INPUT_2 (Prompts!D3) - chains output as next input
   ↓
7. getCell: SIGNAL_DISCOVERY_PROMPT (Prompts!C3)
   ↓
8. createModelResponse: SIGNAL_DISCOVERY
   → Model: gpt-4.1 with web_search tool
   → Output: Discovered signals/leads
   ↓
9. updateCell: SIGNAL_DISCOVERY_LIVE_OUTPUT (Prompts!E3)
10. updateCell: chains to next step input
    ↓
11. createModelResponse: PRODUCE_CLAIMS
    → Extracts atomic claims from signal discovery
    ↓
12-13. updateCell: Save claims output
```

## LLM Calls (3)

| Step | Name | Model | Purpose |
|------|------|-------|---------|
| 4 | SEARCH_BUILDER | o4-mini | Generate search queries |
| 8 | SIGNAL_DISCOVERY | gpt-4.1 + web_search | Find leads/signals |
| 11 | PRODUCE_CLAIMS | gpt-4.1 | Extract atomic claims |

## Sheets Operations (9)

| Cell | Operation | Purpose |
|------|-----------|---------|
| Prompts!C2 | getCell | SEARCH_BUILDER_PROMPT |
| Prompts!D2 | getCell | SEARCH_BUILDER_LIVE_INPUT |
| Prompts!E2 | updateCell | SEARCH_BUILDER_LIVE_OUTPUT |
| Prompts!D3 | updateCell | SET_NEXT_INPUT_2 (chain) |
| Prompts!C3 | getCell | SIGNAL_DISCOVERY_PROMPT |
| Prompts!E3 | updateCell | SIGNAL_DISCOVERY_LIVE_OUTPUT |
| Prompts!D4 | updateCell | SET_NEXT_INPUT |
| Prompts!I2 | updateCell | SET_CLAIMS (search claims) |
| Prompts!I3 | updateCell | SET_CLAIMS (signal claims) |

## Input Variables

From parent pipeline:
- `ICP_CONFIG` - Ideal customer profile configuration
- `INDUSTRY_RESEARCH` - Industry context
- `RESEARCH_CONTEXT` - Client-specific research context
- `SEED_DATA` - Optional seed company/domain

## Output Variables

- Search queries generated
- Signal discovery results (companies, contacts, news)
- Extracted claims (atomic facts with sources)

## Claims System

The PRODUCE_CLAIMS step at the end extracts atomic facts:

```json
{
  "claims": [
    {
      "claim_id": "SIGNAL_001",
      "claim_type": "company_signal",
      "statement": "Acme Corp announced $50M expansion",
      "source_url": "https://...",
      "source_name": "Press Release",
      "confidence": "high"
    }
  ]
}
```

## Live Testing Pattern

The Google Sheets serves as a live testing harness:
- Column C: Prompt template
- Column D: Live input (auto-populated)
- Column E: Live output (for debugging)
- Column I: Extracted claims

This allows Connor to tweak prompts in the sheet and immediately see results.

## Migration Considerations

1. **Sync execution** - This runs blocking, must complete before pipeline continues
2. **3 sequential LLM calls** - Could potentially parallelize search builder
3. **Claims extraction** - Every research step produces claims for later merge
4. **Live testing** - Replace with admin dashboard prompt testing
