# Dossier Pipeline Prompts

**Total Prompts:** 30
**Extracted From:** DOSSIER_FLOW_TEST CSVs
**Status:** Ready for review and refinement

---

## Directory Structure

### Pipeline Steps (15 prompts)

**Phase 0: Setup & Planning**
- `batch_composer.md` - Pre-pipeline batch planning, generates 1-10 seeds
- `compress_icp_config.md` - Compress ICP config for cost savings
- `compress_industry_research.md` - Compress industry research
- `compress_research_context.md` - Compress research context
- `compress_batch_strategy.md` - Compress batch strategy
- `compress_seed_data.md` - Compress seed data

**Phase 1: Discovery**
- `search_builder.md` - 1_SEARCH_BUILDER - Generate search queries
- `signal_discovery.md` - 2_SIGNAL_DISCOVERY - Web search for signals
- `entitiy_research.md` - 3_ENTITY_RESEARCH - Deep dive on company
- `contact_discovery.md` - 4_CONTACT_DISCOVERY - Find decision-makers

**Phase 2: Enrichment**
- `enrich_lead.md` - 5A_ENRICH_LEAD - Enrich company data
- `enrich_opportunity.md` - 5B_ENRICH_OPPORTUNITY - Enrich project details
- `client_specific.md` - 5C_CLIENT_SPECIFIC - Client-specific research

**Phase 3: Contacts**
- `enrich_contacts.md` - 6_ENRICH_CONTACTS - Initialize contact enrichment
- `6_2_enrich_contact.md` - 6.2_ENRICH_CONTACT - Individual contact enrichment (parallel)
- `copy.md` - 7A_COPY - Generate generic outreach copy
- `7_2_copy_client_override.md` - 7.2_COPY (CLIENT OVERRIDE) - Client-specific copy

**Phase 4: Synthesis**
- `insight.md` - 7B_INSIGHT - Generate insights (NOT merge claims)
- `media.md` - 8_MEDIA - Find logo and project images
- `dossier_plan.md` - 9_DOSSIER_PLAN - Plan section routing

### Section Writers (9 prompts)

- `section_writer_intro.md` - INTRO section (title, score, angle, urgency)
- `section_writer_signals.md` - SIGNALS section (why they'll buy now)
- `section_writer_contacts.md` - CONTACTS section (verified contacts)
- `section_writer_lead_intelligence.md` - LEAD INTELLIGENCE (company intel, network)
- `section_writer_strategy.md` - STRATEGY (deal strategy, objections, positioning)
- `section_writer_opportunity_intelligence.md` - OPPORTUNITY INTELLIGENCE (project details)
- `section_writer_client_request.md` - CLIENT REQUEST (client-specific section)
- `section_writer_outreach.md` - OUTREACH (ready-to-send messages)
- `section_writer_all_section_writers.md` - ALL SECTION WRITERS (sources & references)

### Utility Prompts (1 prompt)

- `context_pack_builder.md` - Build context packs for efficiency

**Note:** Claims extraction and merge prompts will be added when found in source CSVs.

---

## Next Steps

### 1. Review Each Prompt
- [ ] Add "Notes from Author" sections
- [ ] Verify variables_used and variables_produced
- [ ] Remove any {{variable}} syntax (prompts should describe what they receive)
- [ ] Ensure prompts follow schema design (snake_case outputs, etc.)

### 2. Standardize Format
All prompts should follow this structure:
```markdown
# {Prompt Name}

**Stage:** {Stage}
**Produces Claims:** YES/NO
**Context Pack Produced:** YES/NO

---

## Prompt Template

{Full prompt content}

---

## Notes from Author

{Your observations and intentions}

---

## Variables Used

- List of inputs this prompt receives

## Variables Produced

- List of outputs this prompt generates

---

## Usage Context

When/how this prompt is used in the pipeline
```

### 3. Align with Schema
- Section writers should specify which JSONB column they populate
- Claims-producing steps should clarify output format
- Compression prompts should note token savings metrics

### 4. Import to Google Sheets
Once prompts are finalized:
1. Copy each prompt to Prompts sheet
2. Add to row with matching slug
3. Populate variables_used and variables_produced columns
4. Set produce_claims and context_pack_produced flags

---

## Design Notes

**Key Principles:**
- Prompts describe what they receive, not {{variable}} syntax
- Make.com handles variable interpolation
- snake_case for all output field names
- Claims as JSON blobs (not normalized)
- Section writers produce JSON matching app structure

**Variables Tracking:**
- `variables_used`: What this prompt receives as input
- `variables_produced`: What this prompt outputs
- Helps with context engineering and Make.com HTTP module setup

**Two Config Versions:**
- **Compressed**: For most steps (cost savings)
- **Thorough**: For high-impact steps (batch composer, feedback)
- Compression prompts maintain essential context while reducing tokens 40-60%

---

## Prompt Status

| Prompt | Status | Notes |
|--------|--------|-------|
| All 30 prompts | ✅ Extracted | Ready for author review |
| Variables tracking | 🔄 To be populated | Need to analyze each prompt |
| Format standardization | 🔄 In progress | Some need cleanup |
| Schema alignment | 🔄 To be verified | Check snake_case, JSONB columns |

---

**Last Updated:** 2026-01-12
**Extracted By:** Claude Code automation
**Source:** DOSSIER_FLOW_TEST CSVs
