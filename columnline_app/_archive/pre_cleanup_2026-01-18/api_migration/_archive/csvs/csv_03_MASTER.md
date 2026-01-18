# MASTER Sheet

NOTES FROM AUTHOR (MAY OR MAY NOT REFLECT WHATS BELOW): Okay, so I don't want to overthink this one. In fact, I don't even think it's used in my make.com workflow to this point. It's more conceptually there so I can imagine what it looks like for me to have some sort of controls that I could even edit on my end. That is the main point of it. When I'm thinking of the actual controls, a lot of this is for testing, which maybe will take a different shape in the future, and I'm fine with that. But some of this is, yes, I will want to run this by client, for example. Run the workflow by client. So this is more maybe of an admin-level dashboard control system. I don't know. But, yeah, I can imagine for the actual, well, not only for the testing piece. Again, I don't want to build like a cool test. I want to actually make a production app. So maybe there's a way to reframe this into something that fits within the architecture of the overall project. I just, again, want to know maybe it's a table per client or maybe it's just my client's table with all their information there. But, again, you know, this is, again, there's probably just a client's table, you know, so I don't know if that's necessary. At the end of the day, what I'm trying to describe is just a simple control panel that I can run, that I can use for a specific, you know, run or batch or something without it like editing or overwriting some of the client information. Like, I just want to run for a particular client, one dossier. I don't want to prep the input. I don't want the batch composer involved with it. I want it to, you know, schedule on, I want it to be sent on Monday and, or I want it to execute on Monday and then I want, you know, around eight hours to review it before it gets released. You know, stuff like that is kind of what I'm looking for. Right now, again, this thing is not built out. It has no function. It's something that is nice to have. And I would like to be able to edit and press a run button afterwards. That way it's all good. But maybe this is not the way we do it in the future. I'm open to ideas.

**Source file:** `DOSSIER_FLOW_TEST - MASTER.csv`
**Sheet name in Make.com:** `MASTER`

## Purpose

The **MASTER** sheet is the **control panel** for the dossier pipeline. It contains toggle switches and configuration options that determine which phases run.

## Structure

| Row | Field | Value | Notes |
|-----|-------|-------|-------|
| 2 | PREP INPUT | NO | Whether to run _0B_PREP_INPUTS |
| 3 | BATCH COMPOSER | NO | Whether to run _0C_BATCH_COMPOSER |
| 4 | NUMBER | 1 | Number of dossiers to generate |
| 5 | CLIENT | 12345 | Client ID for this run |
| 6 | SEED | NO | Whether using seed mode |
| 7 | SCHEDULE | NO | Whether to schedule (date in client config) |
| 8 | RELEASE AFTER _HRS | 1 | Hours before releasing dossier |

## Toggle Values

- `YES` / `NO` - Boolean switches
- Numbers - Numeric configuration
- Text - IDs or strings

## Usage in Pipeline

These controls determine pipeline behavior:

```
IF PREP INPUT = YES:
    Run _0B_PREP_INPUTS first

IF BATCH COMPOSER = YES:
    Run _0C_BATCH_COMPOSER to plan batches

NUMBER = How many leads to process

IF SEED = YES:
    Use SEED_DATA from Inputs!B5
ELSE:
    Discovery mode (find new leads)

IF SCHEDULE = YES:
    Queue job for scheduled time
```

## Migration Notes

1. **Job parameters** - Move to API request body
2. **Client config** - Look up from clients table
3. **Job queue** - Use RQ for scheduling
4. **Remove toggles** - Each run is explicit, no global state

---

## NOTES FROM CURSOR: Understanding Your Requirements

### What You're Describing

**1. A Control Panel Concept (Not a Database Table)**
You explicitly say this is "conceptual" and "not built out." The MASTER sheet represents run-time parameters - the options you set when triggering a pipeline run. It's not persistent configuration that lives in a database. It's more like a form you fill out: "Run for this client, skip prep inputs, use this seed, schedule for Monday, review for 8 hours."

**What this means:** This should become API parameters or a UI form, not a database table. When you trigger a run, you're setting options for that specific run, not changing global state.

**2. The Safety Concern**
You want to run a dossier for a client without risking changes to that client's configs. You also want to be able to see exactly what configs were used for any run, even if those configs have been updated since.

**What this means:** When a pipeline run starts, it should capture a snapshot of which config versions it's using. This snapshot stays with the run forever, so you can always see what that run used, even if configs change later.

**3. Scheduling as a First-Class Feature**
You want to schedule runs ("execute on Monday") and control when dossiers become visible ("review for 8 hours, then release"). This is about timing and visibility, not just execution.

**What this means:** The system needs to support scheduling pipeline execution and scheduling dossier release. These are two separate timing concerns: when to start the pipeline, and when to make the results visible.

**4. A Simple Control Panel UI**
You want a place where you can set these options and press a "run" button. It should be simple - select client, set options, schedule if needed, go.

**What this means:** This is a UI/UX concern, not a data modeling concern. The UI needs to make it easy to set run parameters, but the underlying system just needs to accept those parameters and store them with the run.

### Key Insight

The MASTER sheet represents "the options for the next run" - but in a production system, you don't want global state like that. Instead, each run should be explicit about its options. The control panel is just a convenient way to set those options before triggering a run. The options get stored with the run, not in a global "master" table.

---

## NOTES FROM CLAUDE: Final Schema Design

**After extensive back-and-forth, here's what happened to the MASTER sheet concept:**

### What You Said

"I don't want to overthink this one. In fact, I don't even think it's used in my make.com workflow to this point. It's more conceptually there... This is more maybe of an admin-level dashboard control system... I just want to run for a particular client, one dossier. I don't want to prep the input. I don't want the batch composer involved... I want it to execute on Monday and then I want around eight hours to review it before it gets released."

**Translation:** You want a simple control panel to set run parameters, NOT a persistent database table that holds global state.

### Final Solution: MASTER Sheet → Removed Entirely

**Replaced with:**

1. **API request parameters** when triggering a run:
```json
{
  "client_id": "CLT_12345",
  "count": 1,
  "seed_data": {"entity": "Wyloo Metals", "hint": "mining expansion"},
  "skip_prep_input": true,
  "skip_batch_composer": true,
  "schedule": "2026-01-13T08:00:00Z",
  "review_hours": 8
}
```

2. **Make.com scenario parameters** - Same fields, passed when invoking scenario

3. **Runs sheet captures what was used:**
   - `seed_data` (JSON) - If seed mode, what seed was provided
   - `triggered_by` - "api", "scheduled", "manual"
   - `config_snapshot` (JSON) - Captures which configs were used
   - No global mutable state

### What This Achieves

**Your Requirements:**
- ✅ "Run for a particular client, one dossier" → API: `{client_id: "CLT_12345", count: 1}`
- ✅ "Don't want to prep the input" → API: `{skip_prep_input: true}`
- ✅ "Don't want batch composer involved" → API: `{skip_batch_composer: true}`
- ✅ "Execute on Monday, 8 hours to review" → API: `{schedule: "...", review_hours: 8}`
- ✅ "Without editing or overwriting client information" → Runs.config_snapshot captures what was used, Clients sheet unchanged

**No Global State:**
- Each API request is explicit about its options
- Each run stores its options in Runs sheet
- Multiple runs don't conflict
- Testing doesn't pollute production

### The Control Panel (UI Concept)

When you want that "simple control panel" experience later:

**Dashboard UI (Phase 3 - after Supabase):**
- Dropdown: Select client
- Number input: How many dossiers
- Checkbox: Skip prep input
- Checkbox: Skip batch composer
- DateTime picker: Schedule for when
- Number input: Review hours before release
- Text area: Seed data (optional JSON)
- Button: "Run Now" or "Schedule Run"

Behind the scenes, this just makes an API POST with those parameters. No MASTER sheet involved.

### Key Insight

You said: "Maybe there's a way to reframe this into something that fits within the architecture of the overall project."

**Reframe:**
- **NOT** a database table with global state
- **IS** a set of parameters you provide when triggering a run
- Think of it like a function call: `run_dossier(client_id, count, options)`
- The UI (later) is just a form that collects these parameters before calling the API

**Benefit:** No concurrency issues, no global state management, explicit about every run's parameters.

**STATUS:** MASTER sheet removed from schema. Run parameters passed via API request body. Runs sheet captures what was used for each run.
