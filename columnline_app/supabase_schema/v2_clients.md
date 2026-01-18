# v2_clients

**Layer:** Config (persists across runs)
**Purpose:** Store client-specific configuration including ICP, industry research, and research context.

---

## Columns

| Column | Type | Description |
|--------|------|-------------|
| `client_id` | TEXT (PK) | Unique identifier (e.g., `CLT_ROGER_ACRES_001`) |
| `client_name` | TEXT | Display name (e.g., `Roger Acres - Span Construction`) |
| `status` | TEXT | `active`, `inactive`, `onboarding` |
| `icp_config` | JSONB | Full ICP configuration (signals, markets, services) |
| `icp_config_compressed` | TEXT | LLM-compressed ICP for context window efficiency |
| `industry_research` | JSONB | Industry-specific research and market intelligence |
| `industry_research_compressed` | TEXT | LLM-compressed industry research |
| `research_context` | JSONB | Historical context, past wins, relationships |
| `research_context_compressed` | TEXT | LLM-compressed research context |
| `client_specific_research` | JSONB | Custom research prompts/rules |
| `drip_schedule` | JSONB | Batch schedule configuration |
| `created_at` | TIMESTAMP | Record creation time |
| `updated_at` | TIMESTAMP | Last update time |

---

## ICP Config Structure

```json
{
  "_meta": {
    "client": "Roger Acres",
    "captured_at": "2026-01-06T18:26:25.853Z"
  },
  "icp_config": {
    "signals": [
      {
        "name": "epcm_award_data_center",
        "tier": "hot",
        "weight": 25,
        "description": "EPCM contract award for data center project"
      }
    ],
    "target_markets": {
      "primary": ["data_centers", "mining"],
      "geographies": ["Virginia", "Texas", "Ontario"]
    },
    "services": [
      "Pre-Engineered Metal Buildings (PEMB)",
      "Structural Steel Fabrication"
    ]
  }
}
```

---

## Usage

**Read:** API endpoints fetch client config at pipeline start
**Write:** Client onboarding process (manual or Make.com scenario)

```python
# Example: Fetch client config
client = repo.get_client("CLT_ROGER_ACRES_001")
icp_compressed = client['icp_config_compressed']
```

---

## Notes from Author

**Last Updated:** 2026-01-15

- The `_compressed` columns are LLM-generated summaries for context efficiency
- ICP config determines which signals to search for and how to score leads
- Industry research provides market context for all research steps
- `client_specific_research` is optional custom guidance per client
