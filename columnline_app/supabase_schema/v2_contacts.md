# v2_contacts

**Layer:** Execution (5-20 per run)
**Purpose:** Store enriched contact records.

---

## Columns

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL (PK) | Auto-increment ID |
| `run_id` | TEXT (FK) | Reference to `v2_runs.run_id` |
| `dossier_id` | TEXT (FK) | Reference to `v2_dossiers.dossier_id` |
| `contact_data` | JSONB | Full contact record |
| `created_at` | TIMESTAMP | Enrichment time |

---

## Contact Data Structure

```json
{
  "name": "Sylvain Goyette",
  "title": "COO / VP Projects",
  "company": "Wyloo Metals",
  "email": "s.goyette@wyloo.com",
  "linkedin_url": "https://linkedin.com/in/...",
  "relevance": "Decision-maker for surface facility vendors",
  "outreach_angle": "PEMB expertise for mine surface buildings",
  "enrichment_sources": ["LinkedIn", "company website"]
}
```

---

## Flow

1. `4_CONTACT_DISCOVERY` identifies contacts
2. `6_ENRICH_CONTACTS` passes through contacts (validation)
3. `6_ENRICH_CONTACT_INDIVIDUAL` enriches each contact
4. Contacts stored in `v2_contacts` table
5. Copy step generates personalized outreach

---

## Notes from Author

**Last Updated:** 2026-01-15

- Contacts array returned by `/steps/complete` for 6_ENRICH_CONTACTS
- Each contact gets individual enrichment step
- Copy step references contact IDs for personalized messaging
