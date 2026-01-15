# v2_sections

**Layer:** Execution (~8 per run)
**Purpose:** Store written dossier sections.

---

## Columns

| Column | Type | Description |
|--------|------|-------------|
| `section_id` | TEXT (PK) | Unique section ID |
| `run_id` | TEXT (FK) | Reference to `v2_runs.run_id` |
| `dossier_id` | TEXT (FK) | Reference to `v2_dossiers.dossier_id` |
| `section_name` | TEXT | Section identifier (e.g., `intro`, `signals`, `strategy`) |
| `content` | JSONB | Written section content |
| `created_at` | TIMESTAMP | Writing time |

---

## Section Names

| Section | Writer Step |
|---------|-------------|
| `intro` | `10_WRITER_INTRO` |
| `signals` | `10_WRITER_SIGNALS` |
| `contacts` | `10_WRITER_CONTACTS` |
| `lead_intelligence` | `10_WRITER_LEAD_INTELLIGENCE` |
| `strategy` | `10_WRITER_STRATEGY` |
| `opportunity` | `10_WRITER_OPPORTUNITY` |
| `client_specific` | `10_WRITER_CLIENT_SPECIFIC` |
| `outreach` | `10_WRITER_OUTREACH` |

---

## Notes from Author

**Last Updated:** 2026-01-15

- Each section writer is a separate pipeline step
- Sections can run in parallel (no dependencies between them)
- Assembly step combines all sections into final dossier
