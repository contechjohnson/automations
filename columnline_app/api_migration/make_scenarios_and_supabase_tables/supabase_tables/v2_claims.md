# v2_claims

**Layer:** Execution (100-300 per run)
**Purpose:** Store extracted claims from research steps.

---

## Columns

| Column | Type | Description |
|--------|------|-------------|
| `run_id` | TEXT (FK) | Reference to `v2_runs.run_id` |
| `step_id` | TEXT (FK) | Reference to `v2_pipeline_steps.step_id` |
| `source_step_name` | TEXT | Which research step produced these (e.g., `2_SIGNAL_DISCOVERY`) |
| `claims_json` | JSONB | Array of extracted claims |
| `claims_count` | INTEGER | Number of claims in array |
| `created_at` | TIMESTAMP | Extraction time |

---

## Claim Structure (Context-Rich)

Claims now preserve context, relationships, and strategic meaning:

```json
{
  "claims": [
    {
      "claim_id": "signal_001",
      "claim_type": "SIGNAL",
      "statement": "Ontario removed EA requirement for Eagle's Nest access road on July 4, 2025, enabling Wyloo to begin road construction in Q4 2025 and advance mine construction by 6 months to Q1 2027 start",
      "entities": ["Ontario", "Wyloo Metals", "Eagle's Nest"],
      "date_in_claim": "2025-07-04",
      "source_url": "https://ero.ontario.ca/notice/019-8827",
      "source_name": "Environmental Registry of Ontario",
      "source_tier": "GOV",
      "confidence": "HIGH",
      "context_preserved": "Causal: EA removal enables road. Temporal: July → Q4 → Q1. Impact: 6-month acceleration"
    }
  ],
  "claims_count": 47,
  "claim_types_breakdown": {...},
  "extraction_metadata": {...}
}
```

---

## Claim Types

| Type | Description |
|------|-------------|
| `ENTITY` | Company identity, ownership, business model |
| `SIGNAL` | Buying readiness events + implications |
| `OPPORTUNITY` | Project specs, procurement, vendor opportunities |
| `CONTACT` | Decision-maker info + buying influence |
| `LEAD_PROFILE` | Strategic moves, competitive positioning |
| `CLIENT_SPECIFIC` | Warm paths, relationships, insider knowledge |
| `INSIGHT` | Competitive analysis, win factors, positioning |
| `NETWORK` | Entity relationships, partnerships, alliances |

---

## Context Preservation Philosophy

**OLD (Over-Atomized):**
- "Company raised $50M Series B"
- "CEO is John Smith"
- "Headquarters in Austin"

**NEW (Context-Rich):**
"Following their $50M Series B led by Sequoia in Q3 2024, CEO John Smith relocated HQ from SF to Austin to tap Texas tech talent and reduce costs by 40%"

**What's Preserved:**
- Temporal relationships (following, then, after)
- Causal relationships (to, because, resulting in)
- Strategic intent (why moves are made)
- Quantified impacts (40% reduction)
- Key actors (Sequoia)

---

## Notes from Author

**Last Updated:** 2026-01-15

- Claims extraction now produces mini-narratives, not atomic facts
- Downstream steps receive BOTH claims AND full narrative
- Claims are keyed by source step (signal_discovery_claims, entity_research_claims, etc.)
- `context_preserved` field helps debugging and quality assessment
