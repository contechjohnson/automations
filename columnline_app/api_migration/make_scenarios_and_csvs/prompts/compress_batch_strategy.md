# Config Compression: BATCH_STRATEGY

**Purpose:** Compress thorough BATCH_STRATEGY into token-efficient version for most pipeline steps

---

## Prompt Template

SEE ONBOARDING TABLE

---

## Notes from Author

<!-- This compresses the comprehensive config into a machine-readable format -->

---

## Variables Used

- `batch_strategy` (thorough version from Onboarding)

## Variables Produced

- `batch_strategy_compressed` (compact version)

---

## Usage Context

Part of _0B_PREP_INPUTS phase. Takes thorough configs from onboarding and creates compressed versions for cost savings. Most pipeline steps use compressed; high-impact steps (batch composer, feedback) use thorough.

**Token Savings:** Typically 40-60% reduction while maintaining essential context.
