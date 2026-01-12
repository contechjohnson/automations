# Other Sheets

This document covers the remaining sheets used in the Make.com pipeline.

---

## Clients Sheet

**Source file:** `DOSSIER_FLOW_TEST - Clients.csv`
**Sheet name:** `Clients`

### Purpose
Stores client metadata. Currently just a placeholder with headers.

### Structure
| Column | Field |
|--------|-------|
| A | CLIENT_ID |
| B+ | ALL OTHER CLIENT INFO... |

### Migration Notes
- Move to `clients` table in Supabase
- Store ICP_CONFIG, INDUSTRY_RESEARCH, RESEARCH_CONTEXT per client

---

## Dossiers Sheet

**Source file:** `DOSSIER_FLOW_TEST - Dossiers.csv`
**Sheet name:** `Dossiers`

### Purpose
Stores completed dossier metadata. Currently just a placeholder.

### Structure
| Column | Field |
|--------|-------|
| A | DOSSIER_ID |
| B | CLIENT_ID |
| C+ | ALL OTHER DOSSIER INFO... |

### Migration Notes
- Move to `dossiers_v2` table
- Add sections as `dossier_sections_v2` rows

---

## Onboarding Sheet

**Source file:** `DOSSIER_FLOW_TEST - Onboarding.csv`
**Sheet name:** `Onboarding`

### Purpose
Captures raw client onboarding information before processing into configs.

### Structure
| Row | Info Type | Purpose |
|-----|-----------|---------|
| 2 | CLIENT INFO | Contact info, emails, website |
| 3 | TRANSCRIPTS | Recorded call transcripts |
| 4 | CLIENT MATERIAL | Do-not-call lists, past clients, scripts |
| 5 | PRE-RESEARCH | Initial research from Perplexity/Claude |
| 6 | ONBOARDING SYSTEM PROMPT | System prompt for processing |
| 7 | ICP_CONFIG | Generated ICP config |
| 8 | INDUSTRY_RESEARCH | Generated industry research |
| 9 | RESEARCH_CONTEXT | Generated research context |
| 10 | BATCH_STRATEGY | Batch processing strategy |

### Data Flow
```
Raw Inputs (rows 2-5)
    ↓
_0A_CLIENT_ONBOARDING
    ↓
Processed Configs (rows 7-10)
    ↓
_0B_PREP_INPUTS
    ↓
Inputs sheet (final configs)
```

---

## PrepInputs Sheet

**Source file:** `DOSSIER_FLOW_TEST - PrepInputs.csv`
**Sheet name:** `PrepInputs`

### Purpose
Intermediate configs from onboarding, before final refinement.

### Structure
| Cell | Field | Content |
|------|-------|---------|
| B2 | PRE_ICP_CONFIG | Raw ICP from onboarding |
| C2 | (prompt) | Refinement prompt |
| B3 | PRE_INDUSTRY_RESEARCH | Raw industry research |
| C3 | (prompt) | Refinement prompt |
| B4 | PRE_RESEARCH_CONTEXT | Raw research context |
| C4 | (prompt) | Refinement prompt |
| B5 | PRE_SEED_DATA | Raw seed data |
| C5 | (prompt) | Refinement prompt |

### Data Flow
```
Onboarding sheet
    ↓
_0A → writes to PrepInputs
    ↓
_0B → reads PrepInputs, refines, writes to Inputs
```

---

## Batch Composer Inputs Sheet

**Source file:** `DOSSIER_FLOW_TEST - Batch Composer Inputs.csv`
**Sheet name:** `Batch Composer Inputs`

### Purpose
Inputs for the batch composition step.

### Structure
| Row | Field | Content |
|-----|-------|---------|
| 2 | BATCH_STRATEGY | Strategy configuration |
| 3 | SEED_POOL_INPUT | (not in scope) |
| 4 | LAST_BATCH | Previous batch reference |
| 5 | RECENT_FEEDBACK | Recent client feedback |

### Used By
- `_0C_BATCH_COMPOSER` blueprint

---

## Summary: Sheet Migration Map

| Sheet | Current Use | Migration Target |
|-------|-------------|------------------|
| Inputs | Client configs | `clients` table |
| Prompts | Prompt templates + live testing | `prompts/*.md` + admin UI |
| MASTER | Control toggles | API parameters |
| DOSSIER SECTIONS | Section writer prompts | `prompts/section-writer-*.md` |
| Contacts | Enriched contacts | `dossier_contacts_v2` table |
| Clients | Client metadata | `clients` table |
| Dossiers | Dossier metadata | `dossiers_v2` table |
| Onboarding | Raw client input | Admin onboarding form |
| PrepInputs | Intermediate configs | Pipeline step output |
| Batch Composer Inputs | Batch planning | Job queue parameters |
