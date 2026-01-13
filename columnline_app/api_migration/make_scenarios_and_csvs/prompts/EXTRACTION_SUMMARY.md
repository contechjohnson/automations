# Prompt Extraction Complete ✅

**Date:** 2026-01-12
**Total Prompts Extracted:** 30

---

## What Was Extracted

### Source CSVs
1. **DOSSIER_FLOW_TEST - Prompts.csv** → 15 pipeline step prompts
2. **DOSSIER_FLOW_TEST - DOSSIER SECTIONS.csv** → 9 section writer prompts
3. **DOSSIER_FLOW_TEST - PrepInputs.csv** → 5 config compression prompts
4. **DOSSIER_FLOW_TEST - Inputs.csv** → 1 context pack builder prompt

### Output Location
```
columnline_app/api_migration/make_scenarios_and_csvs/prompts/
├── README.md (index with all 30 prompts)
├── EXTRACTION_SUMMARY.md (this file)
│
├── Pipeline Steps (15 files)
│   ├── batch_composer.md
│   ├── search_builder.md
│   ├── signal_discovery.md
│   ├── entitiy_research.md
│   ├── contact_discovery.md
│   ├── enrich_lead.md
│   ├── enrich_opportunity.md
│   ├── client_specific.md
│   ├── enrich_contacts.md
│   ├── 6_2_enrich_contact.md
│   ├── copy.md
│   ├── 7_2_copy_client_override.md
│   ├── insight.md
│   ├── media.md
│   └── dossier_plan.md
│
├── Section Writers (9 files)
│   ├── section_writer_intro.md
│   ├── section_writer_signals.md
│   ├── section_writer_contacts.md
│   ├── section_writer_lead_intelligence.md
│   ├── section_writer_strategy.md
│   ├── section_writer_opportunity_intelligence.md
│   ├── section_writer_client_request.md
│   ├── section_writer_outreach.md
│   └── section_writer_all_section_writers.md
│
└── Compression & Utility (6 files)
    ├── compress_icp_config.md
    ├── compress_industry_research.md
    ├── compress_research_context.md
    ├── compress_batch_strategy.md
    ├── compress_seed_data.md
    └── context_pack_builder.md
```

---

## File Format

Each markdown file includes:

```markdown
# {Prompt Name}

**Stage:** {Stage}
**Produces Claims:** YES/NO
**Context Pack Produced:** YES/NO

---

## Prompt Template

{Full prompt content from CSV}

---

## Notes from Author

<!-- Placeholder for your notes -->

---

## Variables Used

<!-- To be populated -->

## Variables Produced

<!-- To be populated -->

---

## Usage Context

<!-- When/how this is used -->
```

---

## What's Next

### Your Actions
1. **Review each prompt file** - Add your "Notes from Author"
2. **Populate variables** - Fill in variables_used and variables_produced
3. **Align with schema** - Ensure outputs match snake_case, JSONB structure
4. **Update prompts** - Edit prompt content as needed
5. **Mark ready** - When satisfied, copy to Google Sheets

### Schema Alignment Checklist
- [ ] Remove {{variable}} syntax (describe what they receive instead)
- [ ] Output field names use snake_case (company_name, not companyName)
- [ ] Section writers specify target JSONB column (find_lead, enrich_lead, copy, insight, media)
- [ ] Claims-producing steps clarify JSON output format
- [ ] Compression prompts note token savings

### Variables to Track
For each prompt, identify:
- **Variables Used** - What inputs does this prompt receive?
  - Examples: `icp_config_compressed`, `seed_data`, `prev_claims`, `context_pack`
- **Variables Produced** - What outputs does this prompt generate?
  - Examples: `search_queries`, `entity_claims`, `contact_info`, `section_json`

---

## Observations

### Strong Prompts (Likely Need Minor Tweaks)
Based on extraction, these prompts appear well-formed:
- search_builder.md
- entity_research.md
- section writer prompts (detailed, specific)

### May Need More Work
- Some prompts might have {{variable}} syntax that needs removal
- Variables_used and variables_produced need population
- Alignment with finalized schema (dual configs, claims as JSON blobs, etc.)

### Missing
- Claims extraction prompt (not found in CSVs - may need to create)
- Claims merge prompt (not found in CSVs - may need to create)
- Onboarding system prompt (if it exists)

---

## Integration with Schema

These prompts will populate the **Prompts sheet** with columns:
- prompt_id (e.g., PRM_001)
- prompt_slug (e.g., search-builder)
- stage (e.g., FIND_LEAD)
- step (e.g., 1_SEARCH_BUILDER)
- prompt_template (full content)
- model (default model)
- produce_claims (TRUE/FALSE)
- context_pack_produced (TRUE/FALSE)
- **variables_used** (JSON array)
- **variables_produced** (JSON array)
- version (e.g., v1.0)
- created_at

---

## Quick Reference: Prompt Categories

**Discovery (4):** search_builder, signal_discovery, entity_research, contact_discovery
**Enrichment (3):** enrich_lead, enrich_opportunity, client_specific
**Contacts (4):** enrich_contacts, 6.2_enrich_contact, copy, 7.2_copy (client)
**Synthesis (3):** insight, media, dossier_plan
**Section Writers (9):** intro, signals, contacts, lead_intel, strategy, opportunity, client, outreach, sources
**Compression (5):** ICP, industry, context, batch, seed
**Utility (2):** batch_composer, context_pack_builder

---

**Status:** ✅ Extraction complete, ready for author review and refinement
**Next Session:** Review, refine, populate variables, import to Google Sheets
