# Prompts CSV Updated - Status Report

**Date:** 2026-01-12
**Status:** ✅ Complete

---

## What Was Done

1. **Parsed all 31 prompt files** from `prompts_v2` folder
2. **Extracted full prompt content** - No more placeholders!
3. **Updated `02_prompts.csv`** with complete prompts

---

## Results

**Total Prompts:** 31 (was 20 placeholders, now 31 real prompts)

**What Was Extracted From Each File:**
- Full prompt template (Main Prompt Template section)
- Stage (e.g., FIND_LEAD, ENRICH, WRITE)
- Step (e.g., 1_SEARCH_BUILDER, 3_ENTITY_RESEARCH)
- Model (e.g., gpt-4.1, o4-mini-deep-research)
- Produces Claims (TRUE/FALSE)
- Context Pack Produced (TRUE/FALSE)
- Input variables (from ## Input Variables section)
- Output variables (from ## Variables Produced section)

---

## Breakdown by Type

**Claims-Producing Prompts (11):**
- PRM_003 - entity-research
- PRM_004 - contact-discovery
- PRM_005 - enrich-lead
- PRM_006 - enrich-opportunity
- PRM_007 - client-specific
- PRM_013 - insight
- PRM_017 - section-writer-signals
- PRM_018 - section-writer-contacts
- PRM_023 - section-writer-outreach
- PRM_030 - claims-extraction
- PRM_099 - claims-merge

**Non-Claims Prompts (20):**
All other prompts (search builder, discovery, section writers, compression, etc.)

---

## Sample Prompts

**PRM_001 - search-builder**
- Stage: FIND_LEAD
- Model: gpt-4.1
- Input: current_date, icp_config_compressed, research_context_compressed, seed, hint
- Output: queries, search_strategy, domains_to_exclude

**PRM_002 - signal-discovery**
- Stage: FIND_LEAD
- Model: o4-mini-deep-research (async)
- Input: queries, search_strategy, domains_to_exclude
- Output: discoveries, sources_found, exclude_domains_updated

**PRM_030 - claims-extraction**
- Stage: UTILITY
- Model: gpt-4.1
- Input: research_narrative, step_name, extraction_rules
- Output: claims, claims_count, claim_types_breakdown

---

## Files Created/Updated

**Script:**
```bash
scripts/populate_prompts_from_v2.py
```

**Updated CSV:**
```bash
tmp/sheets_export/02_prompts.csv
```
- Headers: 12 columns
- Rows: 31 prompts (plus 1 header row)
- Size: ~215KB (was 5.8KB placeholders)

---

## What's Different From Old CSV

**Before (Old CSV):**
- 20 prompts
- placeholder text like "[Prompt text for search-builder. See old CSVs for full text.]"
- Total size: 5.8KB

**After (New CSV):**
- 31 prompts (all 30 from prompts_v2 + claims_merge)
- Full prompt templates (2-5KB each)
- Real input/output variables
- Correct metadata (stage, step, model)
- Total size: ~215KB

**Added Prompts (11 new):**
1. contact-discovery (PRM_004)
2. enrich-contact (PRM_009) - individual contact enrichment
3. copy-client-override (PRM_012)
4. insight (PRM_013)
5. media (PRM_014)
6. section-writer-outreach (PRM_023)
7. section-writer-sources (PRM_024)
8. compress-icp-config (PRM_025)
9. compress-industry-research (PRM_026)
10. compress-research-context (PRM_027)
11. compress-batch-strategy (PRM_028)

---

## Verification

Run this to verify:
```bash
python3 -c "import csv; rows = list(csv.DictReader(open('tmp/sheets_export/02_prompts.csv'))); print(f'Total: {len(rows)} prompts')"
```

Expected output: `Total: 31 prompts`

---

## Next: Test Google Sheets API

Now that the CSV is updated, test the Google Sheets API:

```bash
python3 scripts/test_google_sheets_api.py
```

**Before running:**
1. Create service account in Google Cloud Console
2. Download credentials JSON
3. Save as `credentials.json` in project root
4. Share the Google Sheet with service account email
5. Run the test

---

## Ready for Import

The CSV is ready to import to Google Sheets:

**Sheet ID:** `1G70bxnt_P_2_qAqssrjnzkhBCPUa7gVAKMmc_mTn9fQ`

**Import Steps:**
1. Open the Google Sheet
2. Delete existing Prompts sheet (if any)
3. Import `tmp/sheets_export/02_prompts.csv` as new tab
4. Rename tab to "Prompts"
5. Verify 31 rows (plus header)

---

## Script Details

**Location:** `scripts/populate_prompts_from_v2.py`

**What It Does:**
1. Scans `prompts_v2` folder for all `.md` files
2. Parses markdown structure:
   - Extracts metadata from **Key:** value format
   - Extracts ## Input Variables section
   - Extracts ## Main Prompt Template section
   - Extracts ## Variables Produced section
3. Generates prompt_id based on filename number (01_ → PRM_001)
4. Generates slug from filename (01_search_builder.md → search-builder)
5. Writes all data to CSV with proper escaping

**Key Functions:**
- `parse_metadata()` - Extract Stage, Step, Model, etc.
- `extract_section()` - Extract markdown sections
- `extract_input_variables()` - Parse input variable list
- `extract_output_variables()` - Parse output variable list
- `extract_full_prompt()` - Get full prompt template

---

## Status: ✅ READY

- ✅ All 31 prompts parsed
- ✅ CSV updated with full content
- ✅ Test script created
- ⏳ Waiting: Google Sheets API test
- ⏳ Waiting: Import to Google Sheets

---

**Next Step:** Run `python3 scripts/test_google_sheets_api.py` to verify API connectivity.
