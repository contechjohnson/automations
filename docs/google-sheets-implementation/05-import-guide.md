# Next Steps: Import CSVs to Google Sheets

**Goal:** Get all 14 CSV files into Google Sheets so Make.com can read/write

---

## Step 1: Create Google Sheet

1. Go to https://sheets.google.com
2. Click **"Blank"** to create new spreadsheet
3. Name it: **"Columnline Dossier Pipeline - Database"**

---

## Step 2: Import CSVs as Tabs (14 times)

For each CSV file in `tmp/sheets_export/`:

### Import Process

1. Click **File → Import**
2. Click **Upload** tab
3. Drag CSV file or click **Browse**
4. Select file (e.g., `01_clients.csv`)

### Import Settings (CRITICAL)

- **Import location:** "Insert new sheet(s)"
- **Separator type:** Comma
- **Convert text to numbers:** **NO** (IMPORTANT - keep as text)
- **Convert dates:** NO

5. Click **Import data**
6. Rename the new tab (double-click tab name):

### Tab Naming (Must Match Exactly)

| CSV File | Tab Name |
|----------|----------|
| 01_clients.csv | Clients |
| 02_prompts.csv | Prompts |
| 03_section_definitions.csv | SectionDefinitions |
| 04_onboarding.csv | Onboarding |
| 05_prep_inputs.csv | PrepInputs |
| 06_batch_composer.csv | BatchComposer |
| 07_runs.csv | Runs |
| 08_pipeline_steps.csv | PipelineSteps |
| 09_claims.csv | Claims |
| 10_merged_claims.csv | MergedClaims |
| 11_context_packs.csv | ContextPacks |
| 12_contacts.csv | Contacts |
| 13_sections.csv | Sections |
| 14_dossiers.csv | Dossiers |

7. Delete the original "Sheet1" tab (right-click → Delete)

---

## Step 3: Verify Structure

After importing all 14, you should see:

**Config Layer Tabs (with data):**
- Clients (1 example row)
- Prompts (20 rows)
- SectionDefinitions (2 example rows)

**Execution Layer Tabs (empty templates):**
- Onboarding (headers only)
- PrepInputs (headers only)
- BatchComposer (headers only)
- Runs (headers only)
- PipelineSteps (headers only)
- Claims (headers only)
- MergedClaims (headers only)
- ContextPacks (headers only)
- Contacts (headers only)
- Sections (headers only)
- Dossiers (headers only)

---

## Step 4: Get Sheet ID

1. Look at the URL in your browser
2. Copy the part between `/d/` and `/edit`:

```
https://docs.google.com/spreadsheets/d/1a2b3c4d5e6f7g8h9i0j/edit

Sheet ID = 1a2b3c4d5e6f7g8h9i0j
```

3. Save this somewhere (you'll use it in Make.com)

---

## Step 5: Add to Make.com

### Option A: Data Store (Recommended)
1. In Make.com, go to your scenario
2. Add module: **Tools > Set Variable**
3. Variable name: `GOOGLE_SHEETS_ID`
4. Value: `{your_sheet_id}`
5. Reference in other modules: `{{GOOGLE_SHEETS_ID}}`

### Option B: Environment Variable
1. In Make.com organization settings
2. Add environment variable: `GOOGLE_SHEETS_ID`
3. Value: `{your_sheet_id}`
4. Available across all scenarios

---

## Step 6: Test Read Access

### Create Simple Test Scenario

1. **Module 1:** Google Sheets > Get Values (Advanced)
   - Spreadsheet ID: `{{GOOGLE_SHEETS_ID}}` (or paste directly)
   - Range: `Clients!A1:M2`
   - Should return: Headers + 1 example client row

2. **Module 2:** Google Sheets > Get Values (Advanced)
   - Spreadsheet ID: `{{GOOGLE_SHEETS_ID}}`
   - Range: `Prompts!A1:L21`
   - Should return: Headers + 20 prompt rows

3. Run scenario → Verify output

If both work, you're ready to build the full pipeline!

---

## Step 7: Test Write Access

1. **Module 1:** Google Sheets > Add a Row
   - Spreadsheet ID: `{{GOOGLE_SHEETS_ID}}`
   - Sheet Name: `Runs`
   - Values:
     - Column A: `TEST_RUN_001`
     - Column B: `CLT_TEST`
     - Column C: `running`
     - Column D: `{}`
     - Column E: (empty)
     - Column F: `{{formatDate(now; "YYYY-MM-DD HH:mm:ss")}}`

2. Run scenario
3. Check Runs tab in Google Sheets → Should see new row

If it works, delete test row and proceed!

---

## Common Import Issues

### Issue: "Convert text to numbers" is checked
**Problem:** JSON columns get corrupted (e.g., `{"key": "value"}` becomes `#ERROR`)
**Fix:** Re-import with "Convert text to numbers" UNCHECKED

### Issue: Tab names don't match
**Problem:** Make.com can't find "Clients Sheet" when it's looking for "Clients"
**Fix:** Rename tabs to match exactly (case-sensitive)

### Issue: Extra columns or missing columns
**Problem:** CSV didn't import correctly
**Fix:** Delete tab, re-import with correct settings

### Issue: Headers are missing
**Problem:** Import skipped first row
**Fix:** Should see headers in row 1 (client_id, client_name, etc.)

---

## Validation Checklist

Before moving to Make.com:

- [ ] All 14 tabs exist
- [ ] Tab names match exactly (Clients, Prompts, Runs, etc.)
- [ ] Clients tab has 1 example row (CLT_EXAMPLE_001)
- [ ] Prompts tab has 20 rows (PRM_001 through PRM_020)
- [ ] All execution tabs are empty (headers only)
- [ ] Sheet ID copied from URL
- [ ] Test read works in Make.com
- [ ] Test write works in Make.com

---

## You're Ready When...

✅ All 14 tabs imported
✅ Sheet ID saved
✅ Make.com can read Clients + Prompts
✅ Make.com can write to Runs

**Next:** Build first scenario (Search + Signal Discovery)

---

## Quick Reference: Your Sheet Structure

```
Columnline Dossier Pipeline - Database
│
├── Clients (1 row, 13 columns)
├── Prompts (20 rows, 12 columns)
├── SectionDefinitions (2 rows, 6 columns)
│
├── Onboarding (empty, 15 columns)
├── PrepInputs (empty, 13 columns)
├── BatchComposer (empty, 10 columns)
├── Runs (empty, 10 columns)
├── PipelineSteps (empty, 13 columns)
├── Claims (empty, 5 columns)
├── MergedClaims (empty, 5 columns)
├── ContextPacks (empty, 7 columns)
├── Contacts (empty, 32 columns)
├── Sections (empty, 9 columns)
└── Dossiers (empty, 12 columns)
```

---

**Estimated Time:** 15-20 minutes to import all CSVs
**Difficulty:** Easy (mostly clicking through import dialogs)
