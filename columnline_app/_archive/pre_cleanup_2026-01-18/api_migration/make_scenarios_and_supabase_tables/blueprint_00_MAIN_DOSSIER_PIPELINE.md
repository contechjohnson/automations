# MAIN_DOSSIER_PIPELINE

**Source file:** `MAIN_DOSSIER_PIPELINE.json`
**Internal name:** `COLUMNLINE_PROMPT_TESTING`
**Total modules:** 40

## Purpose

This is the **main orchestrator** for the entire dossier generation pipeline. It coordinates all subscenarios, manages async polling loops, and sequences the multi-phase research and writing process.

## Execution Flow

### Phase 1: Load Inputs (Modules 1-8)

Load all client configuration from Google Sheets `Inputs` tab:

| Module | Cell | Variable |
|--------|------|----------|
| 1 | - | Entry point (trigger) |
| 2 | Inputs!B2 | ICP_CONFIG |
| 3 | Inputs!B3 | INDUSTRY_RESEARCH |
| 4 | Inputs!B4 | RESEARCH_CONTEXT |
| 5 | Inputs!B5 | SEED_DATA |
| 6 | Inputs!B8 | PRODUCE_CLAIMS_PROMPT |
| 7 | Inputs!B6 | CLAIMS_MERGE_PROMPT |
| 8 | - | Additional prompts |

### Phase 2: Signal Discovery (Module 9-10)

**Sync execution** - blocks until complete

```
9. SET_SCENARIO_IDS (SetVariables)
10. RUN_SYNC_SEARCH_AND_SIGNAL (CallSubscenario) → calls 01AND02_SEARCH_AND_SIGNAL
```

Outputs: Discovered lead signals, search results

### Phase 3: Deep Research with Polling (Modules 11-17)

**Async execution** with polling loop

```
11. START_ASYNC_DEEP_ENTITY_AND_CONTACTS (CallSubscenario)
    → calls 03_AND_04_SEQUENTIAL_DEEP_RESEARCH_STEPS
    → background: true

12. SET entity_contacts_done = FALSE

13-17. POLLING LOOP:
    13. BasicRepeater (max iterations)
    14. GetVariable (check status)
    15. Sleep 30 seconds
    16. HTTP GET status check
    17. Break if done
```

### Phase 4: Parallel Enrichment Batch 1 (Modules 18-30)

**4 async subscenarios launched in parallel**, then polled together:

```
18. START_ASYNC_DEEP_ENRICH_LEAD → 05A_ENRICH_LEAD
19. START_ASYNC_AGENT_ENRICH_MEDIA → 08_MEDIA
20. START_ASYNC_AGENT_ENRICH_OPPORTUNITY → 05B_ENRICH_OPPORTUNITY
21. START_ASYNC_AGENT_CLIENT_SPECIFIC → 05C_CLIENT_SPECIFIC

22. SET parallel_batch_1_done = FALSE

23-30. POLLING LOOP (checks all 4):
    - HTTP GET /responses/{id} for each
    - Break when all complete
```

### Phase 5: Insight Synthesis (Modules 31-32)

**Sync execution** - blocks until complete

```
31. RUN_SYNC_AGENT_INSIGHT (CallSubscenario) → 07B_INSIGHT
32. Process results
```

Outputs: Merged claims, strategic insight, context packs

### Phase 6: Writers + Contact Enrichment (Modules 33-40)

**Async execution** with polling

```
33. START_ASYNC_DOSSIER_PLAN_AND_WRITERS → 09_DOSSIER_PLAN
    (This internally triggers 6 writer subscenarios)

34. START_ASYNC_BATCH_ENRICH_CONTACTS → 06_ENRICH_CONTACTS

35. SET final_batch_done = FALSE

36-40. POLLING LOOP:
    - Sleep 30 seconds
    - HTTP check writer status
    - HTTP check contacts status
    - Break when both complete
```

## Key Patterns

### Polling Pattern

Make.com uses this pattern for async operations:

```
1. CallSubscenario (background: true)
2. SetVariable done_flag = FALSE
3. BasicRepeater (max 100)
   4. GetVariable
   5. Sleep 30s
   6. HTTP GET status
   7. SetVariable if complete
   8. Break if done
```

**Python equivalent:**
```python
async def poll_until_complete(response_id: str, timeout: int = 600):
    start = time.time()
    while time.time() - start < timeout:
        status = await check_status(response_id)
        if status["completed"]:
            return status["output"]
        await asyncio.sleep(30)
    raise TimeoutError()
```

### Subscenario Calls

| Name | Target | Mode |
|------|--------|------|
| RUN_SYNC_SEARCH_AND_SIGNAL | 01AND02 | Sync (blocking) |
| START_ASYNC_DEEP_ENTITY_AND_CONTACTS | 03_AND_04 | Async (background) |
| START_ASYNC_DEEP_ENRICH_LEAD | 05A | Async (background) |
| START_ASYNC_AGENT_ENRICH_MEDIA | 08 | Async (background) |
| START_ASYNC_AGENT_ENRICH_OPPORTUNITY | 05B | Async (background) |
| START_ASYNC_AGENT_CLIENT_SPECIFIC | 05C | Async (background) |
| RUN_SYNC_AGENT_INSIGHT | 07B | Sync (blocking) |
| START_ASYNC_DOSSIER_PLAN_AND_WRITERS | 09 | Async (background) |
| START_ASYNC_BATCH_ENRICH_CONTACTS | 06 | Async (background) |

## Data Flow

```
Inputs (Sheets)
    ↓
Signal Discovery (sync)
    ↓
Entity + Contact Research (async, poll)
    ↓
┌──────────────┬───────────────┬───────────────┬───────────────┐
│ Enrich Lead  │ Enrich Media  │ Enrich Opp    │ Client Spec   │
│ (async)      │ (async)       │ (async)       │ (async)       │
└──────────────┴───────────────┴───────────────┴───────────────┘
    ↓ (poll all 4)
Insight Synthesis (sync)
    ↓
┌──────────────────────────────┬──────────────────────────────┐
│ Dossier Plan + 6 Writers     │ Contact Enrichment (batch)   │
│ (async)                      │ (async)                      │
└──────────────────────────────┴──────────────────────────────┘
    ↓ (poll both)
Final Assembly
```

## Module Type Summary

| Type | Count |
|------|-------|
| scenario-service:StartSubscenario | 1 |
| google-sheets:getCell | 7 |
| util:SetVariables | 1 |
| scenario-service:CallSubscenario | 9 |
| util:SetVariable2 | 6 |
| builtin:BasicRepeater | 3 |
| util:GetVariable2 | 3 |
| util:FunctionSleep | 3 |
| http:MakeRequest | 7 |

## Migration Notes

- **No direct LLM calls** in this file - all LLM work is delegated to subscenarios
- Main pipeline is purely orchestration logic
- 3 polling loops for 3 async batches
- HTTP calls are for OpenAI Responses API status checks
- Sleep intervals are 30 seconds between polls
