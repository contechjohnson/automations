# Prompts Sheet

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
