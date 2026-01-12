# DOSSIER SECTIONS Sheet

**Source file:** `DOSSIER_FLOW_TEST - DOSSIER SECTIONS.csv`
**Sheet name in Make.com:** `DOSSIER SECTIONS`

## Purpose

The **DOSSIER SECTIONS** sheet contains the **prompt templates for all 6 dossier section writers** and serves as their live testing harness.

## Structure

| Col | Name | Purpose |
|-----|------|---------|
| A | SECTION WRITER | Writer name (INTRO, SIGNALS, etc.) |
| B | SECTIONS | Fields this writer produces |
| C | PROMPT | Full prompt template |
| D | INPUT | Live input for testing |
| E | OUTPUT | Live output JSON |
| F | HUMAN READABLE OUTPUT | Formatted output for review |

## Rows (Section Writers)

| Row | Writer | Sections Produced |
|-----|--------|-------------------|
| 2 | INTRO | TITLE, ONE_LINER, ANGLE, SCORE, SCORE_DESCRIPTION, URGENCY |
| 3 | SIGNALS | WHY_THEYLL_BUY_NOW |
| 4 | (reserved for CONTACTS) | VERIFIED_CONTACTS |
| 5 | LEAD INTELLIGENCE | COMPANY_INTEL, ENTITY_BRIEF, NETWORK_INTELLIGENCE, QUICK_REFERENCE |
| 6 | STRATEGY | DEAL_STRATEGY, COMMON_OBJECTIONS, COMPETITIVE_POSITIONING |
| 7 | OPPORTUNITY INTELLIGENCE | OPPORTUNITY_DETAILS |
| 8 | CLIENT REQUEST | CLIENT_SPECIFIC |

## Section Output Formats

### INTRO Section (Row 2)

```json
{
  "title": "Wyloo Metals",
  "one_liner": "January 2026 Eagle's Nest mine approval triggers $1.2B construction",
  "the_angle": "They are starting construction... You offer... You can help...",
  "lead_score": 82,
  "score_explanation": "Score of 82 reflects...",
  "timing_urgency": "HIGH"
}
```

### SIGNALS Section (Row 3)

```json
{
  "why_theyll_buy_now": [
    {
      "signal_type": "REGULATORY",
      "headline": "Ontario removes EA requirement",
      "status": "APPROVED",
      "date": "2025-07-01",
      "source_url": "https://...",
      "relevance": "Removes 2-year hurdle..."
    }
  ]
}
```

### LEAD INTELLIGENCE Section (Row 5)

```json
{
  "company_intel": "2 paragraphs about the company...",
  "entity_brief": "2-3 sentence summary",
  "network_intelligence": [
    {"type": "partner", "name": "Hatch Ltd", "connection": "...", "approach": "..."}
  ],
  "quick_reference": ["Question 1...", "Question 2..."]
}
```

### STRATEGY Section (Row 6)

```json
{
  "deal_strategy": {
    "how_they_buy": "Sylvain Goyette owns decisions...",
    "unique_value_props": ["Prop 1", "Prop 2"]
  },
  "common_objections": [
    {"objection": "...", "response": "..."}
  ],
  "competitive_positioning": {
    "insights_they_dont_know": [...],
    "landmines_to_avoid": [...]
  }
}
```

### OPPORTUNITY INTELLIGENCE Section (Row 7)

```json
{
  "opportunity_details": {
    "project_name": "Eagle's Nest Nickel-Copper Mine",
    "project_type": "mining_facility",
    "location": {"city": "...", "state": "...", "country": "..."},
    "estimated_value": "$1.2 billion total",
    "timeline": [...],
    "scope_relevant_to_client": "...",
    "procurement_status": "...",
    "key_players": [...]
  }
}
```

## Prompt Guidelines

All section writers follow these rules:
- Use only claims provided (no fabrication)
- Simple words (3rd-5th grade reading level)
- No em dashes, no semicolons
- Specific to this company (not generic)
- Cite evidence claims

## Migration Notes

1. **Prompts to files** - Move to `prompts/section-writer-*.md`
2. **Output schema** - Define TypeScript interfaces for each section
3. **Validation** - Validate outputs against schema
4. **Assembly** - Combine all sections into final dossier JSON
5. **Testing** - Create fixtures for each section writer
