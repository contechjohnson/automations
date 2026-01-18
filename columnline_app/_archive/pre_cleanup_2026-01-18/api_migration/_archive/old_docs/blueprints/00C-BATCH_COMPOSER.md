# _0C_BATCH_COMPOSER

**Source file:** `_0C_BATCH_COMPOSER.blueprint.json`
**Total modules:** ~10
**Execution mode:** Manual trigger (setup step)

## Purpose

Third and final setup step - takes client configs and creates a batch execution plan. Determines how many leads to process, in what order, with what parameters.

## Module Flow

```
1. StartSubscenario (entry point)
   ↓
2. getCell: GET_BATCH_COMPOSER_PROMPT (Prompts!C16)
   → System prompt for batch planning
   ↓
3. getCell: GET_BATCH_STRATEGY (Batch Composer Inputs!B2)
   → Batch processing strategy
   ↓
4. getCell: GET_IPC_CONFIG (Batch Composer Inputs!B3)
   → ICP config from Inputs
   ↓
5. getCell: GET_INDUSTRY_CONTEXT (Batch Composer Inputs!B4)
   → Industry research from Inputs
   ↓
6. getCell: GET_RESEARCH_CONTEXT (Batch Composer Inputs!B6)
   → Research context from Inputs
   ↓
7. createModelResponse: BATCH_COMPOSER
   → Model: gpt-4.1
   → Plans the batch execution
   ↓
8. updateCell: STATUS output
```

## LLM Calls (1)

| Step | Name | Model | Purpose |
|------|------|-------|---------|
| 7 | BATCH_COMPOSER | gpt-4.1 | Plan batch execution |

## Sheets Operations

### Input Sheet: Batch Composer Inputs

| Cell | Content |
|------|---------|
| B2 | Batch strategy (how many, priority order) |
| B3 | ICP_CONFIG (from Inputs) |
| B4 | INDUSTRY_CONTEXT |
| B6 | RESEARCH_CONTEXT |

### Prompt Location

| Cell | Content |
|------|---------|
| Prompts!C16 | BATCH_COMPOSER_PROMPT |

## Batch Plan Output

```json
{
  "batch_plan": {
    "total_leads": 50,
    "batch_size": 10,
    "priority_order": "signal_strength",
    "batches": [
      {
        "batch_id": 1,
        "leads": ["lead_001", "lead_002", ...],
        "estimated_time": "30min"
      },
      {
        "batch_id": 2,
        "leads": [...],
        "estimated_time": "30min"
      }
    ],
    "throttling": {
      "api_calls_per_minute": 10,
      "concurrent_dossiers": 3
    }
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
└──────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────┐
│                    MAIN PIPELINE (Per batch)                 │
│                                                              │
│  For each batch in batch_plan:                               │
│      MAIN_DOSSIER_PIPELINE → Dossiers                        │
└──────────────────────────────────────────────────────────────┘
```

## Migration Notes

1. **Batch orchestration** - Plans work distribution
2. **Single LLM call** - Simple, could be deterministic logic
3. **Rate limiting** - Batch plan includes throttling params
4. **Progress tracking** - Each batch can be tracked independently
5. **Queue system candidate** - Natural fit for RQ job queues

## Python Equivalent

```python
async def compose_batch_plan(
    strategy: dict,
    icp_config: dict,
    industry_context: dict,
    research_context: dict
) -> dict:
    """Plan batch execution based on configs"""

    # Could be LLM-driven or deterministic
    plan = await prompt(
        "batch-composer",
        variables={
            "strategy": strategy,
            "icp_config": icp_config,
            "industry_context": industry_context,
            "research_context": research_context
        },
        model="gpt-4.1"
    )

    return plan

# Or deterministic:
def compose_batch_plan_simple(leads: list, batch_size: int = 10) -> dict:
    return {
        "batches": [
            {"batch_id": i, "leads": leads[i:i+batch_size]}
            for i in range(0, len(leads), batch_size)
        ]
    }
```
