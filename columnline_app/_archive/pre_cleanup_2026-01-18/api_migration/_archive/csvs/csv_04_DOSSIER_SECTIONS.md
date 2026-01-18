# DOSSIER SECTIONS Sheet

NOTES FROM AUTHOR (MAY OR MAY NOT REFLECT WHATS BELOW): Okay, so the dossier section is probably one of the ones that looks like it's all fleshed out, but in reality, this is more conceptual than anything else. So we have a full dossier generating system in our existing production app that I'm trying to get a rough idea of what it takes to take everything and produce JSON that is parsable to be rendered on the page. And we are doing that by not trying to eat the elephant at once, but rather break it up into sections and take all of the claims and the dossier plans. So there's a dossier planning agent that also reviews the claims and it makes suggestions for each of the different section writer agents to select from those sections. But the section writers, I want to have the ability to modify via prompt and so on so I can get specific...  I can get specific output from them. Yeah, that would be helpful in that case.  But ultimately, these writers need to create...  These sections that may or may not be rendered in order, you know, but I'm going to parse the JSON and then render via the app itself. So I just need to make sure that the JSON sections that get generated are high quality and that they're consistent in which section does what. And that they have the context that they need to do what they need to do without being, you know, hallucinating or anything. So that's the main goal there. Keep in mind, you know, we may have 200 different claims and the dossier plan and the context config stuff as well, as well as the prompt. So I imagine that that is quite a bit of text to have to parse through. So we may need to think about this and what each section writer is receiving, but that's less of a CSV or schema question than a prompt engineering one, which we should be able to work with later. So with that said, right now I just have the section writers outputting JSON to...  Just like one of the columns and this is again live input, live output, which, you know, for running hundreds of these at a time, probably not going to work. We've got to figure out a different way to do that. It's the same thing with all of the different CSVs, to be honest. This is sort of a very initial, you know, mental model thing that we were doing. But I can't see the differences between runs or clients or config files and all that. So, yeah, that might have to change. But, yeah, ultimately I need to be able to see the section writer, the sections that it's responsible for, the prompt, the, you know, the prompt that it's going to use, the input, the output. The human readable section for testing can, I don't really care too much about that. One thing that's missing from this schema is sort of the actual variables that will be rendered in the end product. That, I think, is something that would be helpful to have, just like a list of what it is. That way we can make sure that all of them actually get generated and, you know, which ones belong and which sections would be great. Stuff like that, I think, would be very valuable. That way we can look at the prompt, look at the input, look at the output. Okay, does the output contain the variables that we need to actually render the final product? Is it parsable? Because if it is, then we're basically there. That means that we've made it to an actual product that, you know, can get generated and rendered. That being said, you know, we also have an associated table, sort of this dossier table as well. It's, like, barely empty. It's just conceptual. I don't even think you made a markdown file for it. But, yeah, that's the idea is, like, I want to see all of that in there as well so we can see, okay, these dossiers. We've got a dossier ID, client ID, you know, all the other info, including what gets rendered, right? So that is the concept. One more thing I just remembered is you'll notice that I think contacts are missing here as well as the ready to send outreach. Basically, with that, we need to generate contacts in a different way. Or maybe it's not, and I'm overthinking it, but right now we have a key contacts step. It's a deep research step. It goes and finds roughly people who are related to the signal. Then we have an enriched contacts step, which basically takes all of the claims up to that point. Because, again, just because we ran a key contacts step does not mean that we have captured everybody. We are running a bunch of steps before that anyway. So might as well just use all of the claims, run the enriched contacts step to go parse those claims for anything related to finding really good information on these contacts. It's basically a claims extraction step that is really good just for, it's basically tailor-made for contacts. And then when it extracts just the contacts and gives that information, we're going to pass each contact to another agent asynchronously, so all in parallel, and those will generate all the information that you see on that contacts table, or the idea of the contacts table, which includes sort of the bio, the email, the LinkedIn, the LinkedIn scrape, because we have a scraper. We have, you know, all that stuff gets generated. And then with that, we have a chain within that asynchronous step running in parallel. Within that, we have the copy, which does copywriting for email and LinkedIn. And then we have the client copy. And the reason I have that is because there is a, this is just something I've tested in the past where clients want to write the emails in their own particular style. And that's cool. However, I can't just add that as a modifier to the prompt, original prompt, because it's just, they, it's just too, too much going on. And I don't want to have to keep track of that. I want one standard sort of format that will apply to all of my clients, and then they can modify mine, but they can't just make it from scratch, you know. And I want to be able to see, you know, what mine generates versus what their end result looks like. So anyway, that's why there's two of them. All of that gets written into the contacts table, and, you know, that stuff will get rendered. Shouldn't be a problem, I don't think.

**Source file:** `DOSSIER_FLOW_TEST - DOSSIER SECTIONS.csv`
**Sheet name in Make.com:** `DOSSIER SECTIONS`

## Purpose

The **DOSSIER SECTIONS** sheet contains the **prompt templates for all 6 dossier section writers** and serves as their live testing harness.

## Structure

| Col | Name | Purpose |
|-----|------|---------|
| A | SECTION WRITER | Writer name (INTRO, SIGNALS, etc.) |
| B | SECTIONS | Fields this writer produces |
| C | PROMPT | Full prompt template |
| D | INPUT | Live input for testing |
| E | OUTPUT | Live output JSON |
| F | HUMAN READABLE OUTPUT | Formatted output for review |

## Rows (Section Writers)

| Row | Writer | Sections Produced |
|-----|--------|-------------------|
| 2 | INTRO | TITLE, ONE_LINER, ANGLE, SCORE, SCORE_DESCRIPTION, URGENCY |
| 3 | SIGNALS | WHY_THEYLL_BUY_NOW |
| 4 | (reserved for CONTACTS) | VERIFIED_CONTACTS |
| 5 | LEAD INTELLIGENCE | COMPANY_INTEL, ENTITY_BRIEF, NETWORK_INTELLIGENCE, QUICK_REFERENCE |
| 6 | STRATEGY | DEAL_STRATEGY, COMMON_OBJECTIONS, COMPETITIVE_POSITIONING |
| 7 | OPPORTUNITY INTELLIGENCE | OPPORTUNITY_DETAILS |
| 8 | CLIENT REQUEST | CLIENT_SPECIFIC |

## Section Output Formats

### INTRO Section (Row 2)

```json
{
  "title": "Wyloo Metals",
  "one_liner": "January 2026 Eagle's Nest mine approval triggers $1.2B construction",
  "the_angle": "They are starting construction... You offer... You can help...",
  "lead_score": 82,
  "score_explanation": "Score of 82 reflects...",
  "timing_urgency": "HIGH"
}
```

### SIGNALS Section (Row 3)

```json
{
  "why_theyll_buy_now": [
    {
      "signal_type": "REGULATORY",
      "headline": "Ontario removes EA requirement",
      "status": "APPROVED",
      "date": "2025-07-01",
      "source_url": "https://...",
      "relevance": "Removes 2-year hurdle..."
    }
  ]
}
```

### LEAD INTELLIGENCE Section (Row 5)

```json
{
  "company_intel": "2 paragraphs about the company...",
  "entity_brief": "2-3 sentence summary",
  "network_intelligence": [
    {"type": "partner", "name": "Hatch Ltd", "connection": "...", "approach": "..."}
  ],
  "quick_reference": ["Question 1...", "Question 2..."]
}
```

### STRATEGY Section (Row 6)

```json
{
  "deal_strategy": {
    "how_they_buy": "Sylvain Goyette owns decisions...",
    "unique_value_props": ["Prop 1", "Prop 2"]
  },
  "common_objections": [
    {"objection": "...", "response": "..."}
  ],
  "competitive_positioning": {
    "insights_they_dont_know": [...],
    "landmines_to_avoid": [...]
  }
}
```

### OPPORTUNITY INTELLIGENCE Section (Row 7)

```json
{
  "opportunity_details": {
    "project_name": "Eagle's Nest Nickel-Copper Mine",
    "project_type": "mining_facility",
    "location": {"city": "...", "state": "...", "country": "..."},
    "estimated_value": "$1.2 billion total",
    "timeline": [...],
    "scope_relevant_to_client": "...",
    "procurement_status": "...",
    "key_players": [...]
  }
}
```

## Prompt Guidelines

All section writers follow these rules:
- Use only claims provided (no fabrication)
- Simple words (3rd-5th grade reading level)
- No em dashes, no semicolons
- Specific to this company (not generic)
- Cite evidence claims

## Migration Notes

1. **Prompts to files** - Move to `prompts/section-writer-*.md`
2. **Output schema** - Define TypeScript interfaces for each section
3. **Validation** - Validate outputs against schema
4. **Assembly** - Combine all sections into final dossier JSON
5. **Testing** - Create fixtures for each section writer

---

## NOTES FROM CURSOR: Understanding Your Requirements

### What You're Describing

**1. Section Writers as Editable Prompts**
You want section writer prompts to be editable so you can tune the output. These are prompts like any other - they just happen to produce dossier sections. The key is being able to modify them to get specific output.

**What this means:** Section writers should be stored and versioned like any other prompt. When you edit one, you create a new version. The system should make it easy to see what prompt version was used for any section.

**2. The Output Validation Need**
You want to ensure that section outputs contain all the fields needed for rendering. You want to be able to check: "Does this output have all the variables we need? Is it parsable? Can we render it?"

**What this means:** The system needs to know what fields each section should produce, and validate that those fields are present in the output. This is a quality check - making sure the JSON is complete and renderable.

**3. Section Writers Receive Three Inputs**
Each section writer gets: (1) all merged claims, (2) the dossier plan (routing suggestions), and (3) a context pack (compact summary). These three inputs help the writer understand what to emphasize and what context to use.

**What this means:** The system needs to assemble these three inputs and pass them to each section writer. The writers run in parallel, each receiving the same three inputs but producing different sections.

**4. Dossier Assembly from Sections**
After all section writers complete, their outputs need to be assembled into the final dossier structure that matches your frontend. Some sections combine (intro + signals), some extract root-level fields (lead_score, timing_urgency), and some come from other sources (copy from contacts table).

**What this means:** There's a mapping step between section writer outputs and the final dossier structure. The system needs to know how to combine sections, extract fields, and assemble the final JSON.

**5. The Observability Challenge**
You want to see what each section writer received (inputs) and what it produced (output), but you can't have "last one overwrites" when running many dossiers. You need per-run visibility.

**What this means:** Store each section writer execution as a separate record, linked to its pipeline run. This way you can see what any section writer did for any run, while still having a simple "show me the latest" view.

**6. Contacts Are Separate**
Contacts are handled differently - they're discovered, enriched, and have copy generated through a separate workflow. They end up in the dossier, but they're not produced by section writers.

**What this means:** The contacts workflow is parallel to the section writers workflow. They both contribute to the final dossier, but they're separate processes with separate storage.

### Key Insight

The DOSSIER SECTIONS sheet represents "the prompts and outputs for section writers" - but like everything else, this needs to be per-run. When you run 80 dossiers, each one has its own section writer executions. The system should make it easy to see "what did the intro writer produce for this dossier?" while also providing "what did the intro writer produce most recently?" for quick inspection.

---

## NOTES FROM CLAUDE: Final Schema Design

**After extensive back-and-forth, here's how section writers fit into the final schema:**

### What You Really Needed

1. **Section writers populate the 5 JSONB columns** - You provided the complete dossier variable reference showing your app expects these exact structures:
   - `find_lead` - Discovery data, scoring, the angle
   - `enrich_lead` - Company research, project sites, network intel
   - `copy` - Outreach scripts, objections
   - `insight` - The Math, competitive positioning, deal strategy
   - `media` - Logo URL, project images

2. **Variable validation** - You said: "Missing: variables that will be rendered. Need to validate output has all required fields." Solution:
   - **SectionDefinitions sheet** (config layer) - Lists expected_variables per section type
   - **Sections sheet** (execution layer) - Has `variables_produced` column showing what was actually generated
   - Easy validation: does Sections.variables_produced match SectionDefinitions.expected_variables?

3. **Section-to-column mapping** - Each section writer needs to know which JSONB column it populates:
   - **INTRO** → find_lead (company_name, timing_urgency, one_liner, primary_signal, the_angle, lead_score, score_explanation, company_snapshot, primary_buying_signal)
   - **SIGNALS** → find_lead + enrich_lead (primary_buying_signal, additional_signals)
   - **COMPANY_INTEL** → enrich_lead (company_deep_dive, project_sites)
   - **THE_MATH** → insight (their_reality, the_opportunity, translation, bottom_line)
   - **OUTREACH** → copy (outreach[], objections[], conversation_starters[])
   - **NETWORK** → enrich_lead (network_intelligence)
   - **COMPETITIVE** → insight (competitive_positioning)
   - **DEAL_STRATEGY** → insight (deal_strategy, decision_making_process)
   - **MEDIA** → media (logo_url, project_images[])
   - **CONTACTS** → contacts table (separate rows, not JSONB)

### Final Sections Sheet Structure

The Sections sheet (execution layer) now has:
- `section_id`, `run_id` (links to specific run)
- `section_name` (INTRO, SIGNALS, CONTACTS, etc.)
- `section_data` (full section JSON)
- `claim_ids_used` (which claims were routed to this section)
- `produced_by_step` (which step_id generated this)
- `status` (complete, partial, failed)
- `variables_produced` (KEY: fields actually generated)
- `target_column` (KEY: which Dossier JSONB column this populates)
- `created_at`

### How Sections Become Dossiers

**Final assembly flow:**
1. Section writers run in parallel (6-10 sections)
2. Each writes ONE row to Sections sheet with section_data JSON
3. Assembly step:
   - Read all Sections for this run_id
   - Group by target_column (find_lead, enrich_lead, copy, insight, media)
   - Merge sections that go to the same column
   - Write ONE row to Dossiers sheet with all 5 JSONB columns populated
4. Dossiers sheet has:
   - `find_lead` (JSON) - Contains INTRO + SIGNALS data
   - `enrich_lead` (JSON) - Contains COMPANY_INTEL + NETWORK + SIGNALS.additional_signals
   - `copy` (JSON) - Contains OUTREACH data
   - `insight` (JSON) - Contains THE_MATH + COMPETITIVE + DEAL_STRATEGY + sources
   - `media` (JSON) - Contains MEDIA data
   - Plus denormalized fields for querying: company_name, lead_score, timing_urgency, primary_signal

### SectionDefinitions Sheet (New)

This config sheet lists what each section type should produce:
- `section_name` (INTRO, SIGNALS, etc.)
- `expected_variables` (JSON array: what fields must be present)
- `variable_types` (JSON: type constraints)
- `validation_rules` (JSON: value constraints like min/max for lead_score)
- `description` (human-readable explanation)
- `example_output` (JSON: sample section for reference)

**Purpose:** Validation. After a section writer runs, compare Sections.variables_produced against SectionDefinitions.expected_variables. If mismatch, flag it.

### Key Insight: snake_case Field Names

You provided the complete variable reference showing all fields use **snake_case** (database convention):
- ✅ `company_name`, `lead_score`, `timing_urgency`, `project_sites`, `warm_paths`
- ❌ NOT camelCase: `companyName`, `leadScore`, `timingUrgency`

Section writers must output JSON with these exact field names so the app can render without transformation.

### Contacts Are Separate

Contacts don't go in Dossiers JSONB columns. They're separate rows in the Contacts table (execution layer):
- Each contact is ONE row with fields: id, dossier_id, name, title, email, phone, linkedin_url, bio_paragraph, is_primary, etc.
- Multiple contacts per run (3-10 typically)
- Links to dossier via dossier_id

**Why separate:** Contacts have many fields (20+) and variable count (3-10 per dossier). Better as separate rows than nested JSON array.

**STATUS:** Schema finalized with Sections sheet, SectionDefinitions sheet, and Dossiers sheet. Section writers populate 5 JSONB columns with snake_case field names matching app expectations.
