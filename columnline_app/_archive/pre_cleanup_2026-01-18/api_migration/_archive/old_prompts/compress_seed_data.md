# Config Compression: SEED_DATA

**Purpose:** Compress thorough SEED_DATA into token-efficient version for most pipeline steps

---

## Prompt Template

SEED_DATA Preprocessor

Normalize seed data into a standard format:

If seed is provided:
1. Extract: company_name, signal, source_url, geography, notes
2. Normalize: Convert any freeform text into structured fields
3. Acknowledge: any antipatterns requested
4. YOU MUST KEEP THE INTENT OF THE USER'S REQUEST IN YOUR OUTPUT YOUR GOAL IS TO PASS ON STRUCTURED INFORMATION WITHOUT LOSING THE CONTEXT
If seed is empty or null:
Output: {"mode": "discovery", "seed": null}

Output as JSON:
{
  "mode": "seed" | "discovery",
  "seed": {
    "company_name": "",
    "signal": "",
    "source_url": "",
    "geography": "",
    "notes": ""
  } | null
}

---

## Notes from Author

<!-- This compresses the comprehensive config into a machine-readable format -->

---

## Variables Used

- `seed_data` (thorough version from Onboarding)

## Variables Produced

- `seed_data_compressed` (compact version)

---

## Usage Context

Part of _0B_PREP_INPUTS phase. Takes thorough configs from onboarding and creates compressed versions for cost savings. Most pipeline steps use compressed; high-impact steps (batch composer, feedback) use thorough.

**Token Savings:** Typically 40-60% reduction while maintaining essential context.
