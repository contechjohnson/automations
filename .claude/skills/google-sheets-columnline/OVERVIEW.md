# Google Sheets Columnline Skill

**Type:** Temporary Implementation Skill
**Status:** Active during Google Sheets implementation phase
**Will be removed:** After migration to Supabase

---

## Purpose

Provides quick reference for working with Columnline's Google Sheets pseudo-database during Make.com implementation. Contains schema, API call templates, and formatting guides.

---

## When to Activate

Activate this skill when the user asks about:

- **Columnline app** + Google Sheets
- **Make.com modules** for Columnline
- **Writing to Google Sheets** database
- **Schema** or CSV structure questions
- **API calls** to Google Sheets for Make.com
- **Sheet ranges**, columns, or data structure

**Keywords:** "columnline", "google sheet", "make.com", "write to sheet", "schema", "csv", "api call", "sheet range"

---

## What This Skill Provides

1. **Sheet ID** - Quick access to sheet identifier
2. **14 Sheet Schema** - All tables/sheets with columns
3. **API Call Templates** - Paste-ready for Make.com
4. **Range References** - Correct A1 notation for each sheet
5. **Data Formatting** - JSON structure, toString() usage
6. **Documentation Links** - Full implementation guides

---

## Key Information

**Google Sheet ID:** `1G70bxnt_P_2_qAqssrjnzkhBCPUa7gVAKMmc_mTn9fQ`

**Sheet URL:**
https://docs.google.com/spreadsheets/d/1G70bxnt_P_2_qAqssrjnzkhBCPUa7gVAKMmc_mTn9fQ/edit

**Documentation:**
`docs/google-sheets-implementation/`

**CSV Templates:**
`tmp/sheets_export/`

---

## Quick Reference

See DETAILS.md for:
- Complete 14-sheet schema
- API call templates for Make.com
- Range references (A2:M100, etc.)
- JSON formatting examples
- Common operations (read, write, batch)

---

## Invocation Examples

**User:** "How do I write to the Claims sheet?"
**User:** "What's the schema for Contacts?"
**User:** "Give me the API call for reading Prompts"
**User:** "What columns are in PipelineSteps?"
**User:** "How do I format the run_id for Make.com?"

All should activate this skill.
