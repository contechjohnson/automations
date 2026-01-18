# MASTER Sheet

**Source file:** `DOSSIER_FLOW_TEST - MASTER.csv`
**Sheet name in Make.com:** `MASTER`

## Purpose

The **MASTER** sheet is the **control panel** for the dossier pipeline. It contains toggle switches and configuration options that determine which phases run.

## Structure

| Row | Field | Value | Notes |
|-----|-------|-------|-------|
| 2 | PREP INPUT | NO | Whether to run _0B_PREP_INPUTS |
| 3 | BATCH COMPOSER | NO | Whether to run _0C_BATCH_COMPOSER |
| 4 | NUMBER | 1 | Number of dossiers to generate |
| 5 | CLIENT | 12345 | Client ID for this run |
| 6 | SEED | NO | Whether using seed mode |
| 7 | SCHEDULE | NO | Whether to schedule (date in client config) |
| 8 | RELEASE AFTER _HRS | 1 | Hours before releasing dossier |

## Toggle Values

- `YES` / `NO` - Boolean switches
- Numbers - Numeric configuration
- Text - IDs or strings

## Usage in Pipeline

These controls determine pipeline behavior:

```
IF PREP INPUT = YES:
    Run _0B_PREP_INPUTS first

IF BATCH COMPOSER = YES:
    Run _0C_BATCH_COMPOSER to plan batches

NUMBER = How many leads to process

IF SEED = YES:
    Use SEED_DATA from Inputs!B5
ELSE:
    Discovery mode (find new leads)

IF SCHEDULE = YES:
    Queue job for scheduled time
```

## Migration Notes

1. **Job parameters** - Move to API request body
2. **Client config** - Look up from clients table
3. **Job queue** - Use RQ for scheduling
4. **Remove toggles** - Each run is explicit, no global state
