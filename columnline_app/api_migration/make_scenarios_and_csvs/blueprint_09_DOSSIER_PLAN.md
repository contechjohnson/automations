# 09_DOSSIER_PLAN

**Source file:** `09_DOSSIER_PLAN.blueprint.json`
**Total modules:** 24
**Execution mode:** Async (called via START_ASYNC_DOSSIER_PLAN_AND_WRITERS)

## Purpose

Plans the dossier structure and **orchestrates all 6 writer subscenarios in parallel**. This is the final content generation phase before assembly.

## Module Flow

```
1. StartSubscenario (entry point)
   ↓
2. SetVariables: Writer scenario IDs
   ↓
3. getCell: GET_CONTEXT_PACK (Prompts!K12)
   → Gets merged context from 07B_INSIGHT
   ↓
4. getCell: DOSSIER_PLAN_PROMPT (Prompts!C14)
5. getCell: DOSSIER_PLAN_LIVE_INPUT (Prompts!D14)
   ↓
6. createModelResponse: DOSSIER_PLAN
   → Model: gpt-4.1
   → Plans which sections to write
   ↓
7. updateCell: DOSSIER_PLAN_LIVE_OUTPUT (Prompts!E14)
   ↓
8-13. LAUNCH 6 WRITER SUBSCENARIOS (parallel):
   8. CallSubscenario: ASYNC_DOSSIER_INTRO → WRITER_INTRO
   9. CallSubscenario: ASYNC_DOSSIER_SIGNALS → WRITER_SIGNALS
   10. CallSubscenario: ASYNC_DOSSIER_LEAD_INTELLIGENCE → WRITER_LEAD_INTELLIGENCE
   11. CallSubscenario: ASYNC_DOSSIER_STRATEGY → WRITER_STRATEGY
   12. CallSubscenario: ASYNC_DOSSIER_OPPORTUNITY_DETAILS → WRITER_OPPORTUNITY_DETAILS
   13. CallSubscenario: ASYNC_DOSSIER_CLIENT_SPECIFIC → WRITER_CLIENT_SPECIFIC
   ↓
14. SetVariable: writers_done = FALSE
   ↓
15-24. POLLING LOOP (wait for all 6 writers):
   15. BasicRepeater
   16. GetVariable
   17. Sleep 30s
   18. HTTP GET /responses/{intro_id}
   19. HTTP GET /responses/{signals_id}
   20. HTTP GET /responses/{lead_id}
   21. HTTP GET /responses/{strategy_id}
   22. HTTP GET /responses/{opp_id}
   23. HTTP GET /responses/{client_id}
   24. SetVariable done if all complete
```

## LLM Calls (1)

| Step | Name | Model | Purpose |
|------|------|-------|---------|
| 6 | DOSSIER_PLAN | gpt-4.1 | Plan dossier structure |

## Subscenario Calls (6)

| Name | Target Blueprint | Section |
|------|------------------|---------|
| ASYNC_DOSSIER_INTRO | WRITER_INTRO | Introduction |
| ASYNC_DOSSIER_SIGNALS | WRITER_SIGNALS | Signals & News |
| ASYNC_DOSSIER_LEAD_INTELLIGENCE | WRITER_LEAD_INTELLIGENCE | Lead Intel |
| ASYNC_DOSSIER_STRATEGY | WRITER_STRATEGY | Strategy |
| ASYNC_DOSSIER_OPPORTUNITY_DETAILS | WRITER_OPPORTUNITY_DETAILS | Opportunity |
| ASYNC_DOSSIER_CLIENT_SPECIFIC | WRITER_CLIENT_SPECIFIC | Client-Specific |

## Dossier Plan Output

The DOSSIER_PLAN step decides:

```json
{
  "dossier_plan": {
    "sections": [
      {
        "section_key": "intro",
        "enabled": true,
        "priority": 1,
        "content_focus": "Executive summary of opportunity"
      },
      {
        "section_key": "signals",
        "enabled": true,
        "priority": 2,
        "content_focus": "Recent news and buying signals"
      }
      // ... etc
    ],
    "tone": "professional",
    "length_guidance": "comprehensive"
  }
}
```

## Parallel Writer Execution

```
                    ┌─────────────────┐
                    │  DOSSIER_PLAN   │
                    └────────┬────────┘
                             │
         ┌───────┬───────┬───┴───┬───────┬───────┐
         ▼       ▼       ▼       ▼       ▼       ▼
     ┌───────┐┌───────┐┌───────┐┌───────┐┌───────┐┌───────┐
     │ INTRO ││SIGNALS││ LEAD  ││STRATEGY│ OPP   ││CLIENT │
     │       ││       ││ INTEL ││       ││DETAILS││SPECIFIC│
     └───┬───┘└───┬───┘└───┬───┘└───┬───┘└───┬───┘└───┬───┘
         │       │       │       │       │       │
         └───────┴───────┴───┬───┴───────┴───────┘
                             │
                       Poll all 6
                             │
                             ▼
                    Final Assembly
```

## Sheets Operations (4)

| Cell | Operation | Purpose |
|------|-----------|---------|
| Prompts!K12 | getCell | GET_CONTEXT_PACK |
| Prompts!C14 | getCell | DOSSIER_PLAN_PROMPT |
| Prompts!D14 | getCell | DOSSIER_PLAN_LIVE_INPUT |
| Prompts!E14 | updateCell | DOSSIER_PLAN_LIVE_OUTPUT |

## HTTP Polling

6 HTTP GET requests to poll each writer:

```
GET /v1/responses/{intro_response_id}
GET /v1/responses/{signals_response_id}
GET /v1/responses/{lead_response_id}
GET /v1/responses/{strategy_response_id}
GET /v1/responses/{opp_response_id}
GET /v1/responses/{client_response_id}
```

All must complete before the polling loop exits.

## Migration Notes

1. **Complex orchestration** - Launches and polls 6 parallel tasks
2. **Context pack input** - Needs K12 data from 07B_INSIGHT
3. **Writer coordination** - All writers must complete
4. **HTTP polling** - 6 status checks per iteration
5. **Dossier plan** - Can be used to conditionally skip sections

## Python Equivalent

```python
async def run_dossier_plan(context_pack: dict) -> dict:
    # Plan the dossier
    plan = await prompt("dossier-plan", {"context": context_pack})

    # Launch all 6 writers in parallel
    writer_tasks = [
        run_writer("intro", context_pack),
        run_writer("signals", context_pack),
        run_writer("lead-intelligence", context_pack),
        run_writer("strategy", context_pack),
        run_writer("opportunity-details", context_pack),
        run_writer("client-specific", context_pack),
    ]

    # Wait for all to complete
    sections = await asyncio.gather(*writer_tasks)

    return {
        "plan": plan,
        "sections": dict(zip(SECTION_KEYS, sections))
    }
```
