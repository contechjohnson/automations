# Google Sheets Columnline Skill

Quick reference for working with Columnline's Google Sheets implementation in Make.com.

## When to Use

Activate when user asks about:
- Columnline + Google Sheets
- Make.com API modules
- Schema/CSV structure
- Writing to sheets
- Range references
- API call formatting

## What It Provides

- **Sheet ID:** `1G70bxnt_P_2_qAqssrjnzkhBCPUa7gVAKMmc_mTn9fQ`
- **14 Sheet Schema:** Complete column reference
- **API Templates:** Paste-ready for Make.com "Make an API call" module
- **Common Patterns:** ID generation, JSON formatting, datetime
- **Troubleshooting:** Quick fixes for common errors

## Files

- `OVERVIEW.md` - Skill purpose and activation triggers
- `DETAILS.md` - Complete schema + API reference (use this most)

## Key Sections in DETAILS.md

1. **Complete 14-Sheet Schema** - All columns for all sheets
2. **Make.com API Call Templates** - GET, POST, PUT, batchGet, batchUpdate
3. **Common Patterns** - IDs, JSON formatting, datetime
4. **Common Operations** - Full scenario examples
5. **Troubleshooting** - Quick fixes

## Quick Start

**Read multiple sheets:**
```
GET /spreadsheets/{ID}/values:batchGet?ranges='01_clients'!A2:M100&ranges='02_prompts'!A2:L100
```

**Write to sheet:**
```
POST /spreadsheets/{ID}/values:'07_runs'!A:J:append
Body: {"values": [[...]]}
```

**Write to multiple sheets:**
```
POST /spreadsheets/{ID}/values:batchUpdate
Body: {"valueInputOption": "USER_ENTERED", "data": [...]}
```

## Status

**Type:** Temporary (will be removed after Supabase migration)
**Phase:** Active implementation
**Documentation:** `docs/google-sheets-implementation/`

## Related

- Main docs: `docs/google-sheets-implementation/README.md`
- CSV templates: `tmp/sheets_export/`
- Test script: `scripts/test_google_sheets_api.py`
