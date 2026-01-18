# v2_prompts

**Layer:** Config (persists across runs)
**Purpose:** Store all prompt templates used by pipeline steps.

---

## Columns

| Column | Type | Description |
|--------|------|-------------|
| `prompt_id` | TEXT (PK) | Unique identifier (e.g., `PROMPT_01_SEARCH_BUILDER`) |
| `prompt_slug` | TEXT | URL-friendly name (e.g., `search-builder`) |
| `prompt_name` | TEXT | Display name (e.g., `Search Builder`) |
| `step_name` | TEXT | Pipeline step name (e.g., `1_SEARCH_BUILDER`) |
| `prompt_template` | TEXT | Full prompt content with `{{variable}}` placeholders |
| `input_variables` | JSONB | List of required input variables |
| `output_schema` | JSONB | Expected output structure |
| `produce_claims` | BOOLEAN | Whether this step should extract claims |
| `created_at` | TIMESTAMP | Record creation time |
| `updated_at` | TIMESTAMP | Last update time |

---

## Prompt Files → Table Mapping

Source prompts live in `prompts_v2/*.md` and are synced to this table.

| File | step_name | produce_claims |
|------|-----------|----------------|
| `01_search_builder.md` | `1_SEARCH_BUILDER` | FALSE |
| `02_signal_discovery.md` | `2_SIGNAL_DISCOVERY` | TRUE |
| `03_entity_research.md` | `3_ENTITY_RESEARCH` | TRUE |
| `04_contact_discovery.md` | `4_CONTACT_DISCOVERY` | TRUE |
| `05_enrich_lead.md` | `5A_ENRICH_LEAD` | TRUE |
| `06_enrich_opportunity.md` | `5B_ENRICH_OPPORTUNITY` | TRUE |
| `07_client_specific.md` | `5C_CLIENT_SPECIFIC` | TRUE |
| `08_enrich_contacts.md` | `6_ENRICH_CONTACTS` | FALSE |
| `09_enrich_contact.md` | `6_ENRICH_CONTACT_INDIVIDUAL` | FALSE |
| `13_insight.md` | `07B_INSIGHT` | TRUE |
| `14_media.md` | `8_MEDIA` | FALSE |
| `15_dossier_plan.md` | `9_DOSSIER_PLAN` | FALSE |
| `10_section_writer_intro.md` | `10_WRITER_INTRO` | FALSE |
| ... | ... | ... |
| `30_claims_extraction.md` | `CLAIMS_EXTRACTION` | TRUE |
| `99_claims_merge.md` | `MERGE_CLAIMS` | FALSE |
| `29_context_pack_builder.md` | `CONTEXT_PACK` | FALSE |

---

## Usage

**Read:** `/steps/prepare` fetches prompt template for each step
**Write:** Prompt sync script (from markdown files)

```python
# Example: Get prompt for a step
prompt = repo.get_prompt_by_step_name("2_SIGNAL_DISCOVERY")
template = prompt['prompt_template']
variables = prompt['input_variables']
```

---

## Notes from Author

**Last Updated:** 2026-01-15

- Prompts are the "source of truth" for what each pipeline step does
- `produce_claims=TRUE` means CLAIMS_EXTRACTION runs after this step
- `input_variables` defines what data the step needs
- Changes to prompts require re-seeding the table
