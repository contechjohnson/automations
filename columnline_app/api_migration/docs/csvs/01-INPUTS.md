# Inputs Sheet

**Source file:** `DOSSIER_FLOW_TEST - Inputs.csv`
**Sheet name in Make.com:** `Inputs`

## Purpose

The **Inputs** sheet stores the **production-ready client configurations** that drive every dossier in the pipeline. These are the refined, structured configs written by the setup phase (`_0A`, `_0B`) that the main pipeline reads at startup.

## Structure

| Row | Cell | Field | Description |
|-----|------|-------|-------------|
| 2 | B2 | ICP_CONFIG | Ideal Customer Profile configuration |
| 3 | B3 | INDUSTRY_RESEARCH | Industry research configuration |
| 4 | B4 | RESEARCH_CONTEXT | Client-specific research context |
| 5 | B5 | SEED_DATA | Seed data mode and inputs |
| 6 | B6 | CLAIMS_MERGE_PROMPT | Prompt for merging claims |
| 7 | B7 | CLIENT_SPECIFIC | Client-specific research inputs |
| 8 | B8 | CLAIMS_EXTRACTION_PROMPT | Prompt for extracting claims |

## Key Configurations

### ICP_CONFIG (B2)

```json
{
  "signals": [
    {"name": "epcm_award_data_center", "tier": "hot", "weight": 25},
    {"name": "building_permit_filed", "tier": "hot", "weight": 22},
    {"name": "land_acquisition_data_center", "tier": "warm", "weight": 20}
  ],
  "disqualifiers": [
    {"name": "construction_start_before_q4_2026", "strict": true},
    {"name": "project_size_too_small", "strict": true}
  ],
  "target_titles": ["VP of Construction", "VP of Development", ...],
  "excluded_titles": ["CEO", "Founder", "Owner"],
  "scoring_weights": {
    "project_rumored": 8,
    "timing_urgency_high": 25,
    "previous_relationship": 25
  },
  "geography": {
    "tier1": ["Virginia (Loudoun County)", "Texas (Dallas, Austin)"],
    "tier2": ["Ohio", "Iowa", "Nevada", "Ontario, Canada"]
  }
}
```

### INDUSTRY_RESEARCH (B3)

```json
{
  "buying_signals": [...],
  "personas": [
    {"title": "End User", "priority": "High", "triggers": [...]},
    {"title": "Developer", "priority": "Medium", "triggers": [...]},
    {"title": "EPCM Firm", "priority": "High", "triggers": [...]}
  ],
  "industries": [
    {"name": "Data Centers", "priority": "80%"},
    {"name": "Mining", "priority": "15%"}
  ],
  "timing_constraints": ["Construction start Q4 2026 or later"],
  "sources_to_check": ["ENR", "DataCenterDynamics", "Mining.com", ...],
  "key_insights": [...]
}
```

### RESEARCH_CONTEXT (B4)

```json
{
  "client": {
    "name": "Span Construction & Engineering, Inc.",
    "domain": "span.com",
    "tagline": "Leaders in Steel Building Construction"
  },
  "differentiators": [
    "100% Employee Owned (ESOP)",
    "Largest Butler Builder",
    "Ranked #1 Pre-Engineered Steel Builder for 30+ years"
  ],
  "notable_projects": [...],
  "team": [...],
  "competitors": [...],
  "goals": {...},
  "brand_voice": {...}
}
```

### SEED_DATA (B5)

```json
{
  "mode": "discovery",  // or "seed"
  "seed": null          // if mode is "seed", contains target info
}
```

## Usage in Pipeline

These cells are read at the start of `MAIN_DOSSIER_PIPELINE`:

```
Modules 2-7 in MAIN_DOSSIER_PIPELINE:
  - Module 2: getCell Inputs!B2 → ICP_CONFIG
  - Module 3: getCell Inputs!B3 → INDUSTRY_RESEARCH
  - Module 4: getCell Inputs!B4 → RESEARCH_CONTEXT
  - Module 5: getCell Inputs!B5 → SEED_DATA
  - Module 6: getCell Inputs!B8 → PRODUCE_CLAIMS_PROMPT
  - Module 7: getCell Inputs!B6 → CLAIMS_MERGE_PROMPT
```

## Migration Notes

1. **Move to database** - These configs should become rows in a `clients` table
2. **Version control** - Track config changes over time
3. **Validation** - Add JSON schema validation on write
4. **Admin UI** - Create forms for editing each config type
5. **Per-client** - Each client gets their own config set
