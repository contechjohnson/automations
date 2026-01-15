# Inputs Sheet

NOTES FROM AUTHOR (MAY OR MAY NOT REFLECT WHATS BELOW): Okay, some comments specifically on the inputs table here. So inputs, yes, the IPC config, industry research, research context, those are sort of the core files that we have referring to the client and files I'm using loosely. But we generate these during the onboarding process. I want them initially when we do the onboarding to be comprehensive and robust. However, by the time they get to this table, it looks like they have been pre-processed. So we have kind of compressed them down to more of a machine readable version. And so if you look at the prep inputs table, there is the original ICP config and industry research and research context. That gets put into the output as the compressed version.  And that also gets put into the input column. So the reason for that is I discovered that when I'm running these prompts, sometimes it makes sense to pass in the original, more comprehensive version of it, and sometimes it makes sense to pass in the sort of prepared or compressed version of it. It just depends on what task I'm trying to do. Most of the tasks are fine with the compressed version, but some are not.  Some benefit from having the original context, like the batch composer in some cases, and the feedback interpreter. Basically, we want to have more detail to have a higher impact on the feedback.  The batch strategy, for example, will be generated using these original files, not the pre-processed ones, which makes sense.  It also gives us another level of a lever that we can pull for the overall downstream quality and cost without compromising sort of the full research and analysis and losing any sort of data. We can always call it when it's appropriate. So that's the main intent there. The seed data, again, this has been a big sticking point, but the seed data is really just seeding the pipeline in any way, shape or form. So this is either going to be a hint from the batch composer or it's going to be an input given directly by the end user themselves. So the actual people on my app have a button that they can push that can seed the pipeline. And me as well, I will build actual scrapers that go and scrape the Internet, scrape open data. And then I have like a pool of seeds that can either be passed directly through via my manual efforts or... ... ... ... ... ... ... ... ...  selected, picked by the badge composer as part of the input to the pipeline. So that's one of them as well. Claims merge prompt, this is the prompt that is responsible for  Merging claims, it's relatively standardized. Basically, its job is simply to take a long list of claims in JSON and return JSON, except deduplicate claims that are there or invalidate claims that have weak positioning. Although, just because it's weak positioning doesn't mean it doesn't belong there. It just means that if we have a directly conflicting claim that refutes one that's on our table, we don't want to poison the context downstream. So, that's what that's for. It merges them, kind of keeps the whole list up to date and sort of itemized in an effective way. We have client-specific research inputs. Now, this is something that I am still workshopping, but basically, there are certain things that clients want and certain notes they have that I'd like to incorporate specifically to them.  And this is something that might get entered manually downstream. Like it could be sort of a golf connection or it could be an alumni connection or something like that. And we'll basically have a section in the dossier downstream that will contain that information. And that's generally it.  But ultimately that's kind of where it goes for now.

**Source file:** `DOSSIER_FLOW_TEST - Inputs.csv`
**Sheet name in Make.com:** `Inputs`

## Purpose

The **Inputs** sheet stores the **production-ready client configurations** that drive every dossier in the pipeline. These are the refined, structured configs written by the setup phase (`_0A`, `_0B`) that the main pipeline reads at startup.

## Structure

| Row | Cell | Field | Description |
|-----|------|-------|-------------|
| 2 | B2 | ICP_CONFIG | Ideal Customer Profile configuration |
| 3 | B3 | INDUSTRY_RESEARCH | Industry research configuration |
| 4 | B4 | RESEARCH_CONTEXT | Client-specific research context |
| 5 | B5 | SEED_DATA | Seed data mode and inputs |
| 6 | B6 | CLAIMS_MERGE_PROMPT | Prompt for merging claims |
| 7 | B7 | CLIENT_SPECIFIC | Client-specific research inputs |
| 8 | B8 | CLAIMS_EXTRACTION_PROMPT | Prompt for extracting claims |

## Key Configurations

### ICP_CONFIG (B2)

```json
{
  "signals": [
    {"name": "epcm_award_data_center", "tier": "hot", "weight": 25},
    {"name": "building_permit_filed", "tier": "hot", "weight": 22},
    {"name": "land_acquisition_data_center", "tier": "warm", "weight": 20}
  ],
  "disqualifiers": [
    {"name": "construction_start_before_q4_2026", "strict": true},
    {"name": "project_size_too_small", "strict": true}
  ],
  "target_titles": ["VP of Construction", "VP of Development", ...],
  "excluded_titles": ["CEO", "Founder", "Owner"],
  "scoring_weights": {
    "project_rumored": 8,
    "timing_urgency_high": 25,
    "previous_relationship": 25
  },
  "geography": {
    "tier1": ["Virginia (Loudoun County)", "Texas (Dallas, Austin)"],
    "tier2": ["Ohio", "Iowa", "Nevada", "Ontario, Canada"]
  }
}
```

### INDUSTRY_RESEARCH (B3)

```json
{
  "buying_signals": [...],
  "personas": [
    {"title": "End User", "priority": "High", "triggers": [...]},
    {"title": "Developer", "priority": "Medium", "triggers": [...]},
    {"title": "EPCM Firm", "priority": "High", "triggers": [...]}
  ],
  "industries": [
    {"name": "Data Centers", "priority": "80%"},
    {"name": "Mining", "priority": "15%"}
  ],
  "timing_constraints": ["Construction start Q4 2026 or later"],
  "sources_to_check": ["ENR", "DataCenterDynamics", "Mining.com", ...],
  "key_insights": [...]
}
```

### RESEARCH_CONTEXT (B4)

```json
{
  "client": {
    "name": "Span Construction & Engineering, Inc.",
    "domain": "span.com",
    "tagline": "Leaders in Steel Building Construction"
  },
  "differentiators": [
    "100% Employee Owned (ESOP)",
    "Largest Butler Builder",
    "Ranked #1 Pre-Engineered Steel Builder for 30+ years"
  ],
  "notable_projects": [...],
  "team": [...],
  "competitors": [...],
  "goals": {...},
  "brand_voice": {...}
}
```

### SEED_DATA (B5)

```json
{
  "mode": "discovery",  // or "seed"
  "seed": null          // if mode is "seed", contains target info
}
```

## Usage in Pipeline

These cells are read at the start of `MAIN_DOSSIER_PIPELINE`:

```
Modules 2-7 in MAIN_DOSSIER_PIPELINE:
  - Module 2: getCell Inputs!B2 → ICP_CONFIG
  - Module 3: getCell Inputs!B3 → INDUSTRY_RESEARCH
  - Module 4: getCell Inputs!B4 → RESEARCH_CONTEXT
  - Module 5: getCell Inputs!B5 → SEED_DATA
  - Module 6: getCell Inputs!B8 → PRODUCE_CLAIMS_PROMPT
  - Module 7: getCell Inputs!B6 → CLAIMS_MERGE_PROMPT
```

## Migration Notes

1. **Move to database** - These configs should become rows in a `clients` table
2. **Version control** - Track config changes over time
3. **Validation** - Add JSON schema validation on write
4. **Admin UI** - Create forms for editing each config type
5. **Per-client** - Each client gets their own config set

---

## NOTES FROM CURSOR: Understanding Your Requirements

### What You're Describing

**1. The Tiered Context Discovery**
You've discovered that not every step needs the full, comprehensive client configs. Some steps (like batch composer, feedback interpreter) work better with the original, detailed versions. Most steps work fine with a compressed, token-optimized version. This gives you a lever to balance quality and cost - you can always use the comprehensive version when it matters, but default to compressed for efficiency.

**What this means:** The system needs to maintain both versions of each config (ICP config, industry research, research context). When a step runs, it should know which version to use based on what it's trying to accomplish.

**2. Seed Data as a Flexible Input**
Seeds can come from multiple places: batch composer hints, end user button clicks, or your scraped seed pool. The key insight is that seeds are just "ways to start the pipeline" - they're not fundamentally different, just different sources.

**What this means:** The system needs to handle seeds from any source and treat them consistently. Whether it's a manual input or a batch composer hint, it's still just seed data that kicks off the pipeline.

**3. Claims System as Standardized Utilities**
The claims extraction and merge prompts are standardized tools that get used across the pipeline. They're not step-specific - they're system-level utilities.

**What this means:** These prompts should be accessible globally, not tied to a specific step. They're reusable tools that multiple steps might call.

**4. Client-Specific Notes as Ad-Hoc Context**
These are manual notes (golf connections, alumni, etc.) that get incorporated into dossiers. They're not part of the standard config flow - they're special additions that clients might want.

**What this means:** These need to be stored separately from the main configs, but easily accessible when building dossiers. They're optional, client-specific additions.

### The Concurrency Challenge

Your current Google Sheets approach stores one config per cell. When you run 80 dossiers, they all try to read/write the same cells. The solution is to version everything - each config change creates a new version, and each pipeline run captures a snapshot of which versions it used. This way, runs don't conflict, and you can always see exactly what configs any run used, even if those configs have changed since.

### Key Insight

The Inputs sheet represents "the current production configs" - but in a concurrent world, "current" needs to mean "the latest version" rather than "the single cell everyone overwrites." The system should make it easy to get "the latest compressed config" or "the latest comprehensive config" without worrying about version numbers, while still preserving full history for debugging and reproducibility.

---

## NOTES FROM CLAUDE: Final Schema Design

**After extensive back-and-forth, here's how the Inputs concept evolved into the final schema:**

### What You Really Needed

1. **ALL 3 configs get compressed versions** - Not just ICP config. Industry research AND research context also need compressed versions for cost savings.

2. **Clear flow: Onboarding → PrepInputs → Clients**
   - **Onboarding sheet** generates thorough/original versions from raw input (transcripts, emails, pre-research)
   - **PrepInputs sheet** takes those originals and compresses them (3 LLM calls)
   - **Clients sheet** stores BOTH versions (source of truth)
   - Each run reads from Clients sheet, uses compressed by default, original for high-impact steps (batch composer, feedback)

3. **No MASTER sheet** - You said "I don't want to overthink this" and "it's more conceptual." Solution: Remove it entirely. Replace with API request parameters: `{client_id, count, seed_data, schedule}`. No global mutable state to manage.

4. **Config snapshot per run** - Runs.config_snapshot captures what was actually used for that run, even if configs change later. Solves the safety concern: "I want to run a dossier without risking changes to client's configs."

### Final Clients Sheet Structure

The Clients sheet (config layer) now has:
- `icp_config` + `icp_config_compressed`
- `industry_research` + `industry_research_compressed`
- `research_context` + `research_context_compressed`
- `client_specific_research` (manual notes like golf connections, alumni)
- `drip_schedule` (email drip config)

This gives you the cost/quality lever: use compressed for most steps (token savings), use original when it matters (batch strategy, feedback interpretation).

### What Replaced the "Live Input/Output" Problem

The original Inputs sheet had "live" columns that would overwrite when running 80 dossiers. Final solution:
- **PipelineSteps sheet** captures input/output per step per run (separate rows, no conflicts)
- **Claims sheet** captures claims per step (one row per claims-producing step, full JSON)
- **MergedClaims sheet** captures merge operations (at least once per run, possibly more)

Each run gets its own rows, filtered by `run_id`. No overwrites, no conflicts, full traceability.

### Key Difference from Original Vision

**Original:** One Inputs sheet with cells that get updated.
**Final:** Three-tier system:
1. **Onboarding sheet** (execution layer) - Captures onboarding runs
2. **PrepInputs sheet** (execution layer) - Captures compression runs
3. **Clients sheet** (config layer) - Source of truth with both versions

This separates "generating configs" (execution, auditable) from "storing configs" (config, read-only during runs).

**STATUS:** Schema finalized with 14 sheets. CSV generation next, then API middleware to abstract Google Sheets complexity from Make.com.
