# Prompts Sheet

NOTES FROM AUTHOR (MAY OR MAY NOT REFLECT WHATS BELOW): Okay, prompts. Prompts was the place I originally started. It's probably the core one here. The way that I'd like to think about prompts is, you know, this is, you know, sort of the main bread and butter of the intent. I'd like to have some sort of rough stage, you know, of the entire workflow. Then the specific step, which, you know, I have been a little inconsistent with the naming convention, but I want to do a little bit better with that. Then we have the prompt itself. And yes, this is the actual prompts that will be called and literally taken and input there. The prompts that I have in there, I actually are doing pretty good. So, well, relatively good. I don't think that they're optimized for the way that I'm using them. In fact,  I'm not even passing variables in there in that way.  I'm just giving it sort of this entire blob and then I'm passing in other blobs to it, specific variables. In fact, I don't know if we can include variables in this way using the make.com interface. So what we may need to do instead is...  Structure it in such a way where the prompts have, they understand that there's going to be context that's going to be passed in, but it's folk, but we'll handle that with the actual AI module. Like the prompt itself has stuff that isn't containing like the variables, if that makes sense.  So what we will say in the prompt is you will receive this information, this type of configuration, this research context, this whatever, without trying to map in the actual variables just yet for this exercise.  But going through the list here, you can see we have, beyond the prompt, we have the input, the output, and these, in the way that I originally set this up, these are live. So they just pass in sort of the last input or output that we ran through, so I can just use it for testing. Now, this is an area where, you know, we don't have to follow to the letter. There might be a better way to do this, but as long as it's so stupid simple that I could figure it out, you know, and just open my Google Sheet and say, okay, I know what's going on here, then we should be good. In fact, maybe we just leave it like that, where it's just the last one, the live input and output, that's fine. Per...  Well, shoot, we might need to do something a little bit different.  Last one per dossier and client run because now that I'm thinking of it, we may have an issue where I'm generating like, you know, 80 of these things on Monday. And if it's reading and writing to this specific input and output, then that's going to be a problem. So this was sort of more conceptual in nature, but I do need some way to just go look, hey, there's the input and there's the output. Whether that's for the run, whether it's for whatever, I don't care. I need a place to store and read these things effectively.  You can see the other pieces of it, produce claims, claims merged. You know, some of these steps produce claims. Basically, if we're trying to ground the report, include some information. Yes, we will have claims. If it's like a copywriting exercise, there's no claims there. Some of them don't need claims, like Enriched Contacts doesn't need claims because it's one of the last steps, despite where its position is on the CSV.  Instead, what's going to happen with it is basically it has its own workflow.  Enrich contacts, you know, initializes enrich contacts. Enrich contacts is an agent step that fills out a bunch of information, but then it chains with copy and copy client override before finishing that. And we may run many of those and those will be stored in a sort of a different way. So there's that. And we have produce claims. So we talk produce claims. So if it does produce claims, you can see that there is a the claims output there. So I have literally all the claims. I can see them. That is going to be important. I'm not tied to whether or not that exists on this table or another table. But what I am tied to is that we don't turn this into a big database. Instead, the steps that produce the JSON objects, they remain JSON objects. And then we may have, you know, claims for signal entity, signal discovery, entity research, contact discovery, enrich lead, enrich opportunity, client specific. And then I'm on the fence, but we may use insight as well, despite it not being grounded in sources. But it is still useful to incorporate that way because it does get included into the merged claims, which would be nice. So anyway, those claim outputs are there. And again, we talked about the original prompt for claims lives on, I think, input. Same deal with merged claims and context packs. Merge claims is just simply a point where we say, cool, we're going to take all of these claims and we're going to just use one giant LLM to merge them in from, you know, seven JSON objects or however many to one JSON object. That's basically the main point. When it's merging the claims, it's just doing a bit of deduplication, you know, removing, obviously, refuted claims, but, you know, still leaving all the others. I don't know the best way to do that without an LLM, but definitely deterministically, it does not work. So there's so many LLMs that name things slightly differently, and it's just too difficult to work that out. So at the end, we may end up having to pull out merged claims to be several AI modules instead of just one, sort of breaking down it into smaller chunks, you know, feeding the first couple to each other, sort of.  We're doing a few calls instead of one. Context packs, the outputs of those are there. So say we run Entity Research, we're going to generate a context pack because now we have both Signal and Entity Research claims. And rather than pass all of those claims to the contact discovery input, basically what we want to do is consolidate those to a context pack instead. We don't necessarily need to be deduplicating claims at this point, but we want to pass on the context so we can make the contact discovery step work better. Same thing with the follow-on one, which is contact discovery. We're going to create a context pack. And that context pack, again, is going to take all of the claims to that point, by the way. That's the purpose of it. It takes all the claims. It's not looking at just that step's claims. So that's important to call out and then puts it there. So, um...  Yeah, we have some other things on there. Media, Batch, Composer. I just was thinking maybe we put the prompt there. I don't know if that's the best place for it or not. Not entirely sure. That's a new addition, actually, probably from what you have on there. So no worries.

**Source file:** `DOSSIER_FLOW_TEST - Prompts.csv`
**Sheet name in Make.com:** `Prompts`

## Purpose

The **Prompts** sheet is the **live testing harness** for all dossier pipeline prompts. Each row represents a step in the pipeline with:
- Column C: The prompt template
- Column D: Live input (auto-populated during run)
- Column E: Live output (for debugging)
- Column I: Claims extracted from this step
- Column K: Context packs produced

This allows rapid prompt iteration without redeploying code.

## Structure

| Col | Name | Purpose |
|-----|------|---------|
| A | STAGE | Pipeline phase (FIND LEAD, ENTITY RESEARCH, etc.) |
| B | STEP | Step number and name (1 SEARCH_BUILDER, 2 SIGNAL_DISCOVERY, etc.) |
| C | PROMPT | Full prompt template with `{{variables}}` |
| D | INPUT | Live input populated during run |
| E | OUTPUT | Live output for debugging |
| F | PRODUCE CLAIMS? | Whether this step extracts claims |
| G | CLAIMS MERGED? | Whether claims are merged here |
| H | CONTEXT PACK PRODUCED? | Whether context pack is built here |
| I | CLAIMS | Extracted claims JSON |
| J | MERGED CLAIMS | Merged claims (at 07B_INSIGHT) |
| K | CONTEXT PACKS | Context pack JSON for downstream steps |

## Rows (Pipeline Steps)

| Row | Step | Cell Refs in Blueprints |
|-----|------|------------------------|
| 2 | SEARCH_BUILDER | C2, D2, E2, I2 |
| 3 | SIGNAL_DISCOVERY | C3, D3, E3, I3 |
| 4 | LEAD_SELECTION | C4, D4, E4, I4 |
| 5 | ENTITY_RESEARCH | C5, D5, E5, I5 |
| 6 | ENRICH_LEAD | C6, D6, E6, I6 |
| 7 | ENRICH_OPPORTUNITY | C7, D7, E7, I7 |
| 8 | CLIENT_SPECIFIC | C8, D8, E8, I8 |
| 9 | CONTACT_DISCOVERY | C9, D9, E9, I9 |
| 10 | ENRICH_CONTACTS_TEMPLATE | C10, D10, E10 |
| 11 | (reserved) | - |
| 12 | INSIGHT | K12 (context pack output) |
| 13 | MEDIA | C13, D13, E13 |
| 14 | DOSSIER_PLAN | C14, D14, E14 |
| 15 | ASSEMBLY | C15 |
| 16 | BATCH_COMPOSER | C16 |

## Key Prompts

### SEARCH_BUILDER (Row 2)

Generates search queries for signal discovery.

Variables: `{{current_date}}`, `{{icp_config}}`, `{{research_context}}`, `{{industry_research}}`, `{{seed}}`, `{{hint}}`, `{{attempt_log}}`, `{{exclude_domains}}`

### SIGNAL_DISCOVERY (Row 3)

Uses web search to discover leads/signals. Uses `web_search` tool.

### CLAIMS_EXTRACTION (Inputs!B8)

Extracts atomic facts from research narratives into structured claims.

Types: SIGNAL, CONTACT, ENTITY, RELATIONSHIP, OPPORTUNITY, METRIC, ATTRIBUTE, NOTE

### CLAIMS_MERGE (Inputs!B6)

Reconciles claims across all research steps:
- Contact resolution (same person detection)
- Timeline resolution (supersession)
- Conflict detection
- Ambiguity flagging

### CONTEXT_PACK (Row 12)

Builds focused briefings for downstream steps:
- `signal_to_entity` - Before entity research
- `entity_to_contacts` - Before contact discovery
- `contacts_to_enrichment` - Before parallel enrichment

## Live Testing Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                     Google Sheets                          │
├─────────────┬─────────────┬─────────────┬─────────────────┤
│ Col C       │ Col D       │ Col E       │ Col I           │
│ PROMPT      │ INPUT       │ OUTPUT      │ CLAIMS          │
├─────────────┼─────────────┼─────────────┼─────────────────┤
│ Template    │ Auto-filled │ LLM output  │ Extracted facts │
│ with {{}}   │ from prev   │ for debug   │ for merge       │
└─────────────┴─────────────┴─────────────┴─────────────────┘
```

## Migration Notes

1. **Prompts to files** - Move to `prompts/*.md` with metadata headers
2. **Admin dashboard** - Replace sheet editing with web UI
3. **Test fixtures** - Save inputs as test cases, not live in sheet
4. **Version history** - Track prompt changes in git
5. **Claims system** - Build database tables for claims storage

---

## NOTES FROM CURSOR: Understanding Your Requirements

### What You're Describing

**1. Prompts as the Core System**
Prompts are the heart of the pipeline - they define what each step does. You want them organized by stage and step, with clear naming. The prompts themselves are descriptive about what context they'll receive, rather than using variable syntax. The runtime system handles passing the actual data.

**What this means:** Prompts should be stored in a way that makes them easy to find, edit, and version. They describe what they need, and the system figures out how to provide it.

**2. The "Stupid Simple" Observability Problem**
You want to be able to open something and see "here's the input, here's the output" - just like your Google Sheets live cells. But when you run 80 dossiers, they can't all overwrite the same cell. You need to see input/output per run, but still have that simple "show me the last one" experience.

**What this means:** Store every execution as a separate record (so runs don't conflict), but provide a simple way to see "the latest run" for any prompt. This gives you both: the simplicity of "show me the last one" and the power of "show me run #47."

**3. Claims as JSON Objects (Not a Big Database)**
You're explicit: "we don't turn this into a big database. Instead, the steps that produce the JSON objects, they remain JSON objects." Claims stay as JSON arrays that get passed around, not normalized into individual rows.

**What this means:** When a step produces claims, store the full JSON array. When you need to merge claims, pass the JSON objects to the merge step. The mental model is "pass JSON around," not "query a normalized database."

**4. Context Packs as Strategic Summaries**
Context packs are built at key points in the pipeline (after entity research, after contact discovery, after insight). They contain ALL claims up to that point, not just the current step's claims. They're efficiency tools - compact summaries that help downstream steps work better without re-reading everything.

**What this means:** Context packs are summaries that accumulate. When you build one after entity research, it includes claims from both signal discovery and entity research. When you build one after contact discovery, it includes everything up to that point.

**5. Claims Merge as a Consolidation Point**
The merge step takes ALL claims from all producing steps and consolidates them into one JSON object. It deduplicates, resolves conflicts, and invalidates weak claims. You're considering breaking this into multiple LLM calls if the claim set gets too large.

**What this means:** The merge step is a critical consolidation point. It takes many JSON arrays and produces one merged array. The system needs to handle this potentially large operation, possibly by chunking it if needed.

### The Variable Interpolation Question

You mentioned prompts should be descriptive about what they'll receive, and the runtime system handles passing the data. The question is: how should the system actually pass the variables? Should it automatically append them as structured context? Should the prompt explicitly list what it expects? This is a design decision that affects how prompts are written and how the runtime system works.

### Key Insight

The Prompts sheet represents "the current prompt for each step" - but like configs, this needs versioning. When you edit a prompt, you want to create a new version (not overwrite), so you can see what prompt version was used for any run. The system should make it easy to get "the current active prompt" while preserving full history.

---

## NOTES FROM CLAUDE: Final Schema Design

**After extensive back-and-forth, here's how the Prompts concept evolved:**

### What You Really Needed

1. **Prompts as templates, NOT execution logs** - The "live input/output" columns were causing conflicts when running 80 dossiers. Solution: Move execution logs to **PipelineSteps sheet** (one row per step per run). Prompts sheet becomes pure config (templates only).

2. **Variables tracking for context engineering** - You said "Variables is a smart move. I think a variables_used and a variables_produced would be good to see." This helps organize what goes where in Make.com:
   - `variables_used`: What this prompt receives (e.g., `["icp_config", "seed", "prev_output"]`)
   - `variables_produced`: What this prompt outputs (e.g., `["search_queries", "exclude_domains"]`)

   This solves: "My make.com solution doesn't really account for a really organized way of passing context from one step to the other."

3. **No {{vars}} in prompt text** - You said prompts should describe what they'll receive, not use variable syntax. Make.com handles passing actual data via HTTP POST body or interpolation. Prompt text says "You will receive ICP config, seed data..." but doesn't have `{{icp_config}}` syntax.

4. **Claims prompts are just prompts** - Claims merge and claims extraction prompts belong in the Prompts sheet, not Clients sheet. They're reusable steps, just like other prompts. You said: "They are prompts after all, just like the others. They basically are their own step in a way, just one that is reused."

### Final Prompts Sheet Structure

The Prompts sheet (config layer) now has:
- `prompt_id`, `prompt_slug`, `stage`, `step` (organization)
- `prompt_template` (describes what it receives, no {{vars}})
- `model` (default model)
- `produce_claims` (flag: does this step extract claims?)
- `context_pack_produced` (flag: does this step create a context pack?)
- `variables_used` (inputs: what this prompt receives)
- `variables_produced` (outputs: what this prompt generates)
- `version`, `created_at` (versioning/audit)

**Removed:** `claims_merged` flag - You said "I don't know necessarily if claims merged makes sense." Merge claims is just a regular prompt that happens to merge things, not a special flag.

### How Claims Work in Final Schema

1. **Claims extraction happens per step:**
   - Step produces narrative/output
   - If `produce_claims = TRUE`, extract claims from that output
   - Write ONE row to Claims sheet with full `claims_json` array
   - Keep as JSON blob (don't parse into individual rows)

2. **Merge claims is a separate operation:**
   - **Decoupled from 07B_INSIGHT** (that's just a regular research step)
   - Takes all Claims.claims_json for a run_id
   - Removes redundancy, resolves conflicts
   - Outputs consolidated claims_json (same format)
   - Can happen multiple times per run (at least once)

3. **Context packs are different from merged claims:**
   - Context packs are targeted summaries for efficiency
   - Merge claims is about consolidation and deduplication
   - Both exist, both needed, different purposes

### What Replaced "Live Testing Pattern"

**Original:** Columns D (INPUT) and E (OUTPUT) would update during runs.
**Problem:** 80 dossiers overwrite each other.
**Solution:** **PipelineSteps sheet** (execution layer):
- One row per step per run
- Columns: run_id, prompt_id, step_name, status, input (JSON), output (JSON), model_used, tokens_used, runtime_seconds
- Filter by run_id to see one run's complete execution
- "Show me the last one" = filter by latest timestamp

This gives you both: simplicity of "show me the last run" AND power of "show me run #47."

### Key Difference from Original Vision

**Original:** Prompts sheet with live input/output columns that update.
**Final:** Two-sheet system:
1. **Prompts sheet** (config layer) - Templates only, read-only during runs
2. **PipelineSteps sheet** (execution layer) - Captures every execution with full I/O

This solves concurrency, preserves history, enables debugging without conflicts.

**STATUS:** Schema finalized. Prompts are templates with variable tracking. Execution logs live in PipelineSteps sheet.
