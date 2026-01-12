# _0A_CLIENT_ONBOARDING

**Source file:** `_0A_CLIENT_ONBOARDING.blueprint.json`
**Total modules:** 19
**Execution mode:** Manual trigger (setup step)

## Purpose

Client onboarding flow - processes raw onboarding information and generates the client configurations used by the main pipeline. This is a **setup step**, not part of the main dossier flow.

## Module Flow

```
1. StartSubscenario (manual trigger)
   ↓
2. getCell: GET_ONBOARDING_SYSTEM_PROMPT (Onboarding!B6)
   → System prompt for processing
   ↓
3. getSheetContent: GET_ONBOARDING_INFO (Onboarding sheet)
   → Reads all client onboarding data
   ↓
4. TextAggregator: Combine onboarding info
   ↓
5. createModelResponse: PROCESS_ONBOARDING_INFO
   → Model: gpt-4.1
   → Processes raw onboarding data
   ↓
6. updateCell: LIVE_OUTPUT_PROCESS_STEP
   ↓
7-10. Chain outputs to multiple cells:
   7. updateCell: LIVE_INPUT_IPC_CONFIG (Onboarding!C7)
   8. updateCell: LIVE_INPUT_INDUSTRY_RESEARCH (Onboarding!C8)
   9. updateCell: LIVE_INPUT_RESEARCH_CONTEXT (Onboarding!C9)
   10. updateCell: LIVE_INPUT_SEED_DATA (Onboarding!C10)
   ↓
11. getSheetContent: Read processed configs
   ↓
12. TextAggregator: Combine configs
   ↓
13. createModelResponse: GENERATE_CLIENT_CONFIGS
   → Model: gpt-4.1
   → Generates final client configurations
   ↓
14-18. Write final configs to Inputs sheet:
   - ICP_CONFIG → Inputs!B2
   - INDUSTRY_RESEARCH → Inputs!B3
   - RESEARCH_CONTEXT → Inputs!B4
   - SEED_DATA → Inputs!B5
   ↓
19. CallSubscenario + ReturnData
   → May trigger PREP_INPUTS
```

## LLM Calls (2)

| Step | Name | Model | Purpose |
|------|------|-------|---------|
| 5 | PROCESS_ONBOARDING_INFO | gpt-4.1 | Parse raw onboarding |
| 13 | GENERATE_CLIENT_CONFIGS | gpt-4.1 | Generate structured configs |

## Sheets Operations (12)

| Sheet | Cell | Purpose |
|-------|------|---------|
| Onboarding | B6 | System prompt |
| Onboarding | (all) | Raw onboarding data |
| Onboarding | C7-C10 | Intermediate processed outputs |
| Inputs | B2 | ICP_CONFIG output |
| Inputs | B3 | INDUSTRY_RESEARCH output |
| Inputs | B4 | RESEARCH_CONTEXT output |
| Inputs | B5 | SEED_DATA output |

## Input: Raw Onboarding Data

The Onboarding sheet contains:
- Client company information
- Target market description
- Ideal customer profile (unstructured)
- Products/services offered
- Competitive differentiators
- Sales team context

## Output: Structured Configs

### ICP_CONFIG (Inputs!B2)
```json
{
  "target_signals": ["expansion", "funding", "leadership change"],
  "disqualifiers": ["bankruptcy", "acquisition target"],
  "target_titles": ["VP Sales", "CRO", "Head of Revenue"],
  "target_geography": ["North America", "EMEA"],
  "company_size": {"min": 100, "max": 5000}
}
```

### INDUSTRY_RESEARCH (Inputs!B3)
```json
{
  "industry_context": "Enterprise SaaS for manufacturing",
  "buying_signals": ["digital transformation", "supply chain modernization"],
  "typical_personas": [...],
  "timing_constraints": [...]
}
```

### RESEARCH_CONTEXT (Inputs!B4)
```json
{
  "client_name": "Acme Corp",
  "products": [...],
  "differentiators": [...],
  "past_wins": [...],
  "sales_team": [...]
}
```

### SEED_DATA (Inputs!B5)
```json
{
  "mode": "discovery",  // or "seed"
  "seed_companies": [],  // if seed mode
  "seed_domains": []
}
```

## Workflow Position

```
┌──────────────────────────────────────────────────────────────┐
│                    SETUP PHASE (One-time per client)         │
│                                                              │
│  _0A_CLIENT_ONBOARDING → _0B_PREP_INPUTS → _0C_BATCH_COMPOSER │
│         ↓                      ↓                    ↓        │
│   Parse raw info         Refine configs       Plan batches   │
└──────────────────────────────────────────────────────────────┘
                              ↓
                    Inputs sheet populated
                              ↓
┌──────────────────────────────────────────────────────────────┐
│                    MAIN PIPELINE (Per lead)                  │
│                                                              │
│  MAIN_DOSSIER_PIPELINE → (all research steps) → Dossier     │
└──────────────────────────────────────────────────────────────┘
```

## Migration Notes

1. **One-time setup** - Not part of per-dossier pipeline
2. **Admin dashboard candidate** - Could be a client config UI
3. **Config validation** - Should validate generated configs
4. **Multi-step processing** - Two LLM calls to refine
5. **Sheet-to-DB migration** - Configs should be in clients table
