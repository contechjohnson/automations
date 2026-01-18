# v2 Archive

This directory contains the v2 implementation that was built as a Python-first approach to migrating the Columnline dossier pipeline from Make.com.

## What's Here

- `v2/` - Full Python pipeline implementation with step executor, database models, API router
- `admin/` - Streamlit dashboard for pipeline monitoring and prompt editing

## Why It's Archived

The v2 implementation was over-engineered and lacked visibility compared to Make.com's native monitoring. We've pivoted to a **Make.com-first approach** where:

- Make.com handles orchestration, polling, and long-running steps
- Supabase stores prompts and client configs (replacing Google Sheets)
- Our custom API server acts as thin middleware for targeted operations

## Status

This code is preserved for reference but is not actively used. The v2_ database tables remain in Supabase and may be used by the new Make.com-first approach.

## Migration Notes

- Database tables (`v2_*`) remain in Supabase
- Prompt files in `prompts/v2/` remain in use
- API endpoints may be referenced but not imported in the main API

## Future Use

This code may be referenced or partially used if we need to:
- Extract specific patterns or utilities
- Understand the previous implementation approach
- Restore functionality if needed

---

*Archived: January 2025*
*New approach: Make.com-first with Supabase backend*

