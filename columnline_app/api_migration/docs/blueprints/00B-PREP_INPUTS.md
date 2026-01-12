# _0B_PREP_INPUTS

**Source file:** `_0B_PREP_INPUTS.blueprint.json`
**Total modules:** ~20
**Execution mode:** Manual trigger (setup step)

## Purpose

Second setup step - takes raw client configs from onboarding and refines them into production-ready inputs. Reads from `PrepInputs` sheet and writes to `Inputs` sheet.

## Module Flow

```
1. StartSubscenario (entry point)
   |
   ├── ICP_CONFIG REFINEMENT:
   │   2. getCell: PRE_ICP_CONFIG (PrepInputs!B2)
   │   3. getCell: PRE_ICP_CONFIG (PrepInputs!C2) - context
   │   4. createModelResponse: PREP_INPUT_ICP_CONFIG
   │      → Model: gpt-4.1
   │      → Refines raw ICP into structured format
   │   5. updateCell: IPC_CONFIG_LIVE_OUTPUT
   │   6. updateCell: IPC_CONFIG_LIVE_INPUT (chains)
   │
   ├── INDUSTRY_RESEARCH REFINEMENT:
   │   7. getCell: PRE_INDUSTRY_RESEARCH (PrepInputs!B3)
   │   8. getCell: PRE_INDUSTRY_RESEARCH (PrepInputs!C3)
   │   9. createModelResponse: PREP_INDUSTRY_RESEARCH
   │      → Model: gpt-4.1
   │   10. updateCell: INDUSTRY_RESEARCH_LIVE_OUTPUT
   │   11. updateCell: INDUSTRY_RESEARCH_LIVE_INPUT
   │
   ├── RESEARCH_CONTEXT REFINEMENT:
   │   12. getCell: PRE_RESEARCH_CONTEXT (PrepInputs!B4)
   │   13. getCell: PRE_RESEARCH_CONTEXT (PrepInputs!C4)
   │   14. createModelResponse: PREP_RESEARCH_CONTEXT
   │       → Model: gpt-4.1
   │   15. updateCell: RESEARCH_CONTEXT_LIVE_OUTPUT
   │   16. updateCell: RESEARCH_CONTEXT_LIVE_INPUT
   │
   └── SEED_DATA REFINEMENT:
       17. getCell: PRE_SEED_DATA (PrepInputs!B5)
       18. getCell: PRE_SEED_DATA (PrepInputs!C5)
       19. createModelResponse: PREP_SEED_DATA
           → Model: gpt-4.1
       20. updateCell: PREP_SEED_DATA_LIVE_OUTPUT
       21. updateCell: SEED_DATA_LIVE_INPUT
```

## LLM Calls (4)

| Step | Name | Model | Purpose |
|------|------|-------|---------|
| 4 | PREP_INPUT_ICP_CONFIG | gpt-4.1 | Refine ICP config |
| 9 | PREP_INDUSTRY_RESEARCH | gpt-4.1 | Refine industry research |
| 14 | PREP_RESEARCH_CONTEXT | gpt-4.1 | Refine research context |
| 19 | PREP_SEED_DATA | gpt-4.1 | Refine seed data |

## Sheets Operations

### Input Sheet: PrepInputs

| Cell | Content |
|------|---------|
| B2 | Raw ICP config |
| C2 | ICP refinement prompt/context |
| B3 | Raw industry research |
| C3 | Industry refinement prompt/context |
| B4 | Raw research context |
| C4 | Research context refinement prompt/context |
| B5 | Raw seed data |
| C5 | Seed data refinement prompt/context |

### Output: Chained to Inputs

The refined outputs chain forward to become the live inputs for the main pipeline.

## Data Transformation

### Before (Raw from Onboarding)

```
"We sell to mid-size manufacturing companies in the midwest
who are looking to modernize their supply chain..."
```

### After (Structured Config)

```json
{
  "icp": {
    "company_size": {"min": 200, "max": 2000},
    "industries": ["manufacturing", "industrial"],
    "geography": ["midwest-us"],
    "signals": ["supply-chain-modernization", "digital-transformation"],
    "titles": ["VP Operations", "Supply Chain Director", "COO"]
  }
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
│                              ↓                              │
│                    Writes to Inputs sheet                   │
└──────────────────────────────────────────────────────────────┘
```

## Migration Notes

1. **Config refinement** - Transforms human-readable to structured JSON
2. **4 parallel-ish steps** - Could run all 4 refinements in parallel
3. **Prompt engineering** - Each config type has specific refinement prompt
4. **Quality gate** - Should validate refined configs before use
5. **Admin UI candidate** - Let users review/edit refined configs
