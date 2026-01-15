# Config Compression: ICP_CONFIG

**Purpose:** Compress thorough ICP_CONFIG into token-efficient version for most pipeline steps

---

## Prompt Template

ICP_CONFIG Preprocessor

Extract a compact scoring checklist from this ICP config:

1. SIGNALS: List each signal name with tier (hot/warm/passive) and weight
2. DISQUALIFIERS: List each with strict=true/false  
3. TARGET TITLES: Combine apollo_titles + targetCriteria.apollo_titles (dedupe)
4. SCORING WEIGHTS: Extract the weights object as-is
5. GEOGRAPHY: Extract tier1/tier2/tier3 regions with bonus points

Output as JSON with these exact keys:
{
  "signals": [{"name": "", "tier": "", "weight": 0}],
  "disqualifiers": [{"name": "", "strict": true}],
  "target_titles": [],
  "excluded_titles": [],
  "scoring_weights": {},
  "geography": {"tier1": [], "tier2": [], "tier3": [], "bonuses": {}}
}

---

## Notes from Author

<!-- This compresses the comprehensive config into a machine-readable format -->

---

## Variables Used

- `icp_config` (thorough version from Onboarding)

## Variables Produced

- `icp_config_compressed` (compact version)

---

## Usage Context

Part of _0B_PREP_INPUTS phase. Takes thorough configs from onboarding and creates compressed versions for cost savings. Most pipeline steps use compressed; high-impact steps (batch composer, feedback) use thorough.

**Token Savings:** Typically 40-60% reduction while maintaining essential context.
