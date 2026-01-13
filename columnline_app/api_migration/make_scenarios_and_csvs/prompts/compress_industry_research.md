# Config Compression: INDUSTRY_RESEARCH

**Purpose:** Compress thorough INDUSTRY_RESEARCH into token-efficient version for most pipeline steps

---

## Prompt Template

INDUSTRY_RESEARCH Preprocessor

Extract actionable intelligence from this industry research:

1. BUYING_SIGNALS: Flatten all tiers into one list with signal name, weight, and source
2. PERSONAS: List each persona with title, priority, and triggers
3. INDUSTRIES: List with priority percentages
4. TIMING: Extract all timing constraints (e.g. "Q4 2026+")
5. SOURCES: List data sources to check
6. KEY_INSIGHTS: Extract the most actionable insights (max 5)

Output as JSON:
{
  "buying_signals": [{"signal": "", "weight": 0, "source": ""}],
  "personas": [{"title": "", "priority": "", "triggers": []}],
  "industries": [{"name": "", "priority": ""}],
  "timing_constraints": [],
  "sources_to_check": [],
  "key_insights": []
}

---

## Notes from Author

<!-- This compresses the comprehensive config into a machine-readable format -->

---

## Variables Used

- `industry_research` (thorough version from Onboarding)

## Variables Produced

- `industry_research_compressed` (compact version)

---

## Usage Context

Part of _0B_PREP_INPUTS phase. Takes thorough configs from onboarding and creates compressed versions for cost savings. Most pipeline steps use compressed; high-impact steps (batch composer, feedback) use thorough.

**Token Savings:** Typically 40-60% reduction while maintaining essential context.
