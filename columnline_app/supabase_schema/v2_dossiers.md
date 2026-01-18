# v2_dossiers

**Layer:** Execution (one per completed run)
**Purpose:** Store final assembled dossiers.

---

## Columns

| Column | Type | Description |
|--------|------|-------------|
| `dossier_id` | TEXT (PK) | Unique ID (e.g., `DOSS_20260115_4523`) |
| `run_id` | TEXT (FK) | Reference to `v2_runs.run_id` |
| `client_id` | TEXT (FK) | Reference to `v2_clients.client_id` |
| `target_entity` | TEXT | Company being researched (e.g., `Hut 8 Corp`) |
| `target_project` | TEXT | Specific project (e.g., `River Bend AI Data Center`) |
| `lead_score` | INTEGER | 0-100 score based on signals |
| `status` | TEXT | `draft`, `ready`, `released` |
| `assembled_dossier` | JSONB | Complete dossier content |
| `find_lead` | JSONB | Lead summary (timing, angle, score) |
| `enrich_lead` | JSONB | Deep company intelligence |
| `insight` | JSONB | Competitive analysis, strategy |
| `copy` | JSONB | Outreach templates, objection handling |
| `media` | JSONB | Logo URL, project images |
| `sections` | JSONB | All written sections |
| `created_at` | TIMESTAMP | Assembly time |
| `released_at` | TIMESTAMP | When made available to client |

---

## When Created

The `dossier_id` is generated at run START, but the `v2_dossiers` record is created at the END during assembly:

```
Run Start → generate dossier_id
    ↓
Pipeline executes (30-50 steps)
    ↓
Assembly Step → CREATE v2_dossiers record
```

---

## JSONB Structures

### find_lead
```json
{
  "timing_urgency": "HOT - Construction start Q1 2027",
  "the_angle": "PEMB supplier for data center shell",
  "one_liner": "Hut 8 building $2B AI data center campus",
  "lead_score": 85,
  "score_explanation": "EPCM award + permit filed + timeline match",
  "primary_buying_signal": {...}
}
```

### media
```json
{
  "image_assets": [
    {
      "asset_id": "RB-01",
      "asset_type": "project_rendering",
      "image_url": "https://...",
      "caption_suggested": "...",
      "source_page_url": "..."
    }
  ],
  "notes_for_span_sales_team": {...}
}
```

---

## Future: Production App Integration

When ready to render in Columnline app:
1. Map `v2_dossiers` JSONB to production `dossiers` table schema
2. Create transform functions for each JSONB section
3. Insert into production tables with client_id lookup

---

## Notes from Author

**Last Updated:** 2026-01-15

- Record created ONLY when pipeline completes successfully
- `assembled_dossier` contains everything (for debugging/export)
- Individual JSONB columns (`find_lead`, `insight`, etc.) for direct querying
- Status flow: `draft` → `ready` → `released`
- Media now contains full `image_assets` array from GPT-5.2
