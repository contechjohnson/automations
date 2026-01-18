# v2_section_definitions

**Layer:** Config (persists across runs)
**Purpose:** Define dossier section templates and requirements.

---

## Columns

| Column | Type | Description |
|--------|------|-------------|
| `section_id` | TEXT (PK) | Section identifier |
| `section_name` | TEXT | Display name |
| `section_template` | JSONB | Template structure |
| `required_inputs` | JSONB | What data this section needs |
| `created_at` | TIMESTAMP | Creation time |
| `updated_at` | TIMESTAMP | Last update time |

---

## Purpose

Defines the structure and requirements for each dossier section:
- What fields each section should have
- What inputs are required to write the section
- Template for consistent output formatting

---

## Notes from Author

**Last Updated:** 2026-01-15

- Mainly used for section writer steps
- Helps ensure consistent output structure
- Can be customized per client if needed
