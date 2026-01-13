# Prompt Gap Analysis

**Date:** 2026-01-12

---

## Current State

### What I Generated (Placeholder CSV)
- **Location:** `tmp/sheets_export/02_prompts.csv`
- **Content:** 20 rows with basic metadata
- **Prompt Template Column:** Contains placeholders like `[Prompt text for search-builder. See old CSVs for full text.]`
- **Variables:** Populated with arrays like `["icp_config", "seed"]` and `["search_queries", "exclude_domains"]`

### What Actually Exists (Real Prompts)
- **Location:** `columnline_app/api_migration/make_scenarios_and_csvs/prompts/`
- **Content:** 30 detailed markdown files with full prompt text
- **Format:** Each file has:
  - Full prompt instructions (2-5KB of actual content)
  - Metadata sections (Stage, Produces Claims, Context Pack Produced)
  - Placeholders for Variables Used/Produced
  - Usage context sections

---

## The Gap

### 1. Missing Prompts (10 total)
My CSV has 20 prompts. The real folder has **30 prompts**. Missing:

**Compression Prompts (5):**
- compress_icp_config.md
- compress_industry_research.md
- compress_research_context.md
- compress_batch_strategy.md
- compress_seed_data.md

**Additional Pipeline Steps (3):**
- contact_discovery.md (4_CONTACT_DISCOVERY)
- 6_2_enrich_contact.md (6.2_ENRICH_CONTACT - individual contact enrichment)
- 7_2_copy_client_override.md (7.2_COPY - client-specific copy)

**Section Writers (2):**
- section_writer_outreach.md
- section_writer_all_section_writers.md (sources & references)

### 2. Prompt Content Quality
**Current CSV:** Placeholders only - not usable in Make.com
**Real Files:** Full 2-5KB prompt instructions with:
- Detailed task descriptions
- Output format specifications
- Rules and constraints
- Example outputs
- Context sections

### 3. Variable Syntax Issue
**Your Requirement:** Prompts should:
1. Have a tiny variables section with brief descriptions (for Make.com mapping)
2. The rest is variable-free (99% of content)
3. Variables section becomes its own Make.com variable
4. Main prompt content is separate Make.com variable

**Current Real Files:** Use `{{variable}}` syntax throughout (e.g., `{{icp_config}}`, `{{seed}}`)

**What Needs to Happen:** Split each prompt into:
```markdown
## VARIABLES_SECTION (for Make.com mapping)
- icp_config: Client's ideal customer profile configuration
- seed: Optional entity or signal to research
- hint: User direction for search strategy

## PROMPT_CONTENT (the actual 99%)
You are a search strategist for B2B signal discovery...
[Rest of prompt referencing what variables contain but not using {{}} syntax]
```

---

## Alignment Requirements

### For Google Sheets Import
Each prompt needs:
1. **prompt_template** column: VARIABLES_SECTION + PROMPT_CONTENT combined
2. **variables_used** column: JSON array `["icp_config", "seed", "hint"]`
3. **variables_produced** column: JSON array `["search_queries", "exclude_domains"]`
4. **produce_claims** flag: TRUE/FALSE
5. **context_pack_produced** flag: TRUE/FALSE

### For Make.com HTTP Module
Each step will need TWO variables:
1. `variables_section` - Brief descriptions for mapping
2. `prompt_content` - The 99% main instructions

---

## Next Steps

### Option A: Keep Placeholders for Now
- Import current CSV (20 prompts with placeholders)
- Test Google Sheets API integration
- Populate real prompts later in batches

### Option B: Wait for Prompt Cleanup
- Other agent is working on prompt refinement
- Once done, regenerate CSV with real content
- Import to Sheets with complete prompts

### Option C: Hybrid Approach
1. Import current CSV structure (establishes columns, IDs, metadata)
2. Test API integration with placeholders
3. Update prompt_template column via API as real prompts are ready
4. Add missing 10 prompts as new rows

---

## Recommendation: Option C (Hybrid)

**Reasoning:**
1. You want to move forward with API setup (don't wait)
2. Schema/structure is correct (20 prompts match your original design)
3. Missing 10 prompts are "nice to have" extras (compression, additional steps)
4. Can add/update prompts via API later without blocking progress

**Action Plan:**
1. ✅ Import current 02_prompts.csv to Google Sheets (establishes structure)
2. ✅ Build Google Sheets API integration (next section)
3. ⏳ When other agent finishes prompt cleanup, update via API
4. ⏳ Add missing 10 prompts as new rows later

---

## Summary

**Gap Size:** 10 missing prompts + placeholder content for all 30
**Blocker Status:** NOT a blocker - can proceed with API setup
**When to Revisit:** After Sheets API working + other agent completes prompt refinement

The structure is correct. The content is incomplete but doesn't block the next phase (API integration).
