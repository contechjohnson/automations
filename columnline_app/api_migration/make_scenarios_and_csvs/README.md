# Make.com Scenarios + Documentation

This folder contains everything related to the Columnline dossier pipeline Make.com integration:

- **JSON Blueprints** - Exported Make.com scenario definitions (`.blueprint.json`)
- **CSV Exports** - Data exports from Google Sheets (`DOSSIER_FLOW_TEST - *.csv`)
- **Blueprint Documentation** - Markdown docs explaining each scenario (`blueprint_*.md`)
- **CSV Documentation** - Markdown docs explaining the data structure (`csv_*.md`)

---

## Plan Reference

**Full Implementation Plan:** `~/.claude/plans/zany-marinating-wreath.md`

**Approach:** Gradual migration (Sheets → Supabase → Dashboard)
- **Phase 1 (NOW):** Google Sheets + API middleware
- **Phase 2 (LATER):** Migrate to Supabase backend
- **Phase 3 (PENDING):** Build dashboard

---

## Multi-Session Workflow

### Session 1: Organization & Documentation (✅ COMPLETED)
- [x] Reorganized all docs into this folder
- [x] Renamed with prefixes for easy navigation
- [x] Created this README

**YOUR NEXT STEP:** Review the markdown files below and annotate where API integrations make sense.

### Session 2-3: Sheets Setup & CSV Generation
1. Design Google Sheets structure (7 tabs: prompts, clients, logs, claims, dossiers, contacts, runs)
2. Generate CSVs from existing data
3. Import CSVs to Google Sheets
4. Share Sheet ID for API integration

### Sessions 4-5: API Middleware (Sheets Backend)
1. Build API endpoints that read/write Google Sheets:
   - `GET /sheets/prompts/{id}` - Read prompt
   - `GET /sheets/clients/{slug}/config` - Read client config
   - `POST /sheets/logs/step` - Log execution
   - `POST /sheets/transform/claims-extract` - Extract claims (code-based)
2. Test endpoints with curl

### Sessions 6-10: Make.com Integration
1. Replace Google Sheets modules with HTTP calls to API
2. Keep LLM calls in Make.com (unchanged)
3. Test each scenario individually
4. Iterate: one scenario at a time

### Session 11: Validation
1. Run full pipeline end-to-end
2. Verify Sheets populate correctly
3. Compare dossier quality to baseline

---

## File Organization

### Blueprint Documentation (Scenarios)
- `blueprint_00_MAIN_DOSSIER_PIPELINE.md` - Main orchestrator (40 modules, coordinates all subscenarios)
- `blueprint_00A_CLIENT_ONBOARDING.md` - Setup: Create dossier skeleton, init contacts
- `blueprint_00B_PREP_INPUTS.md` - Load client configs, prepare variables
- `blueprint_00C_BATCH_COMPOSER.md` - Batch processing for multiple leads
- `blueprint_01_SEARCH_AND_SIGNAL.md` - Steps 01 & 02: Search builder + Signal discovery
- `blueprint_03_DEEP_RESEARCH_STEPS.md` - Steps 02-04: Entity research, Contact discovery, Media research
- `blueprint_05A_ENRICH_LEAD.md` - Enrich lead information
- `blueprint_05B_ENRICH_OPPORTUNITY.md` - Enrich opportunity details
- `blueprint_05C_CLIENT_SPECIFIC.md` - Client-specific research
- `blueprint_06_ENRICH_CONTACTS.md` - Contact enrichment (Apollo, LinkedIn)
- `blueprint_07B_INSIGHT.md` - Claims merge + Insight generation (THE MERGE POINT)
- `blueprint_08_MEDIA.md` - Media research step
- `blueprint_09_DOSSIER_PLAN.md` - Route claims to sections
- `blueprint_10_WRITERS.md` - 6 parallel section writers

### CSV Documentation (Data Structure)
- `csv_01_INPUTS.md` - Client configs (ICP, Industry Research, Research Context)
- `csv_02_PROMPTS.md` - All prompts with metadata
- `csv_03_MASTER.md` - Master control panel (trigger runs)
- `csv_04_DOSSIER_SECTIONS.md` - 6 section writers (Intro, Signals, Contacts, etc.)
- `csv_05_CONTACTS.md` - Contact data structure
- `csv_06_OTHER_SHEETS.md` - Supporting sheets (Signals, Enrichment)

### JSON Blueprints (Actual Scenarios)
- `_0A_CLIENT_ONBOARDING.blueprint.json`
- `_0B_PREP_INPUTS.blueprint.json`
- `_0C_BATCH_COMPOSER.blueprint.json`
- `01AND02_SEARCH_AND_SIGNAL.blueprint.json`
- `03_AND_04_SEQUENTIAL_DEEP_RESEARCH_STEPS.blueprint.json`
- `05A_ENRICH_LEAD.blueprint.json`
- `05B_ENRICH_OPPORTUNITY.blueprint.json`
- `05C_CLIENT_SPECIFIC.blueprint.json`
- `06_ENRICH_CONTACTS.blueprint.json`
- `06.2_ENRICH_CONTACT.blueprint.json`
- `07B_INSIGHT.blueprint.json`
- `08_MEDIA.blueprint.json`
- `09_DOSSIER_PLAN.blueprint.json`
- (Writer blueprints in WRITERS.md)

### CSV Exports (Current Data)
- `DOSSIER_FLOW_TEST - Batch Composer Inputs.csv`
- `DOSSIER_FLOW_TEST - Clients.csv`
- `DOSSIER_FLOW_TEST - Contacts.csv`
- `DOSSIER_FLOW_TEST - DOSSIER SECTIONS.csv`
- (More in the folder)

---

## Integration Strategy

### When to Use Make.com vs API

| Task | Make.com | API | Reason |
|------|----------|-----|--------|
| **LLM calls** (GPT-4, O4, etc.) | ✅ | ❌ | Make.com has built-in OpenAI, visual history |
| **Async deep research** | ✅ | ❌ | Make.com handles polling well, visible progress |
| **Claims extraction** (code-based) | ❌ | ✅ | Deterministic Python logic, faster, testable |
| **Context pack generation** | ❌ | ✅ | Code-based summarization |
| **Prompt retrieval** | ❌ | ✅ | API serves from Sheets/Supabase with versioning |
| **Client config retrieval** | ❌ | ✅ | API serves from Sheets/Supabase |
| **Execution logging** | ❌ | ✅ | API writes to Sheets/Supabase, non-blocking |
| **Error routing, retries** | ✅ | ❌ | Make.com's visual error handling is excellent |
| **Parallel subscenarios** | ✅ | ❌ | Make.com orchestrates parallel async jobs well |

**Rule of thumb:** If it's AI or needs visual monitoring → Make.com. If it's code or data → API.

---

## Key Patterns

### Pattern 1: Prompt Retrieval
```
Make.com:
1. HTTP GET https://api.columnline.dev/sheets/prompts/entity-research
2. Response: {content: "...", version: 12, model: "o4-mini-deep-research"}
3. Interpolate {{variables}} in Make.com
4. Call OpenAI (unchanged)
5. POST /sheets/logs/step (log execution)
```

### Pattern 2: Claims Extraction (Code-Based)
```
Make.com:
1. OpenAI completes → narrative received
2. POST https://api.columnline.dev/sheets/transform/claims-extract
   Body: {narrative, step_name, run_id, context}
3. API extracts claims using Python code (not LLM)
4. API writes claims to Sheets Claims tab
5. Returns: {claims: [...], claims_count: 47}
```

### Pattern 3: Execution Logging
```
Make.com (after EVERY step):
1. POST https://api.columnline.dev/sheets/logs/step
   Body: {run_id, step_name, input, output, model, duration_ms, status}
2. Set "Ignore errors" (non-blocking)
3. Continue with pipeline
```

---

## Your Annotation Task (Next Step)

As you review each markdown file, annotate where you think API integration makes sense:

**Questions to consider:**
1. **Which steps should call API for prompts?** (All? Some? None?)
2. **Which transforms should be code-based?** (Claims extraction? Context packs? Others?)
3. **Where should logging happen?** (After every LLM call? Certain steps only?)
4. **What data should flow through API?** (Prompts, configs, logs, claims, all?)

**Annotation format:** Just add notes/comments directly in the markdown files. For example:
```markdown
## Module 5: OpenAI Chat Completion (Entity Research)

**API INTEGRATION:**
- GET /sheets/prompts/entity-research for prompt content
- POST /sheets/logs/step after completion
- Keep OpenAI call in Make.com

**RATIONALE:** Prompt may change frequently, want version control
```

---

## Future Phases (Reference)

### Phase 2: Supabase Migration (LATER)
- Create Supabase tables (mirror Sheets structure)
- Swap API backend: `api/sheets/repository.py` → `api/supabase/repository.py`
- Make.com unchanged (still calls same endpoints)
- Test full pipeline with Supabase backend

### Phase 3: Dashboard (PENDING)
- Build Streamlit dashboard
- Pages: Prompts, Clients, Runs, Logs, Claims
- Edit prompts, test them, view execution history
- Deploy to droplet

---

## Benefits of This Approach

### Phase 1 (Sheets + API Middleware):
1. **Make.com cleanup** - HTTP calls to API instead of 1000 Sheets modules
2. **Abstraction** - API handles Sheets complexity
3. **Visibility** - Google Sheets shows all data (logs, claims, dossiers)
4. **Prototype** - Proves flow works before Supabase investment
5. **Low risk** - Incremental, testable, iterate quickly

### Phase 2 (Supabase):
1. **Performance** - Database faster than Sheets API
2. **Scalability** - Handle more data, concurrent runs
3. **Proper schema** - Relational integrity, indexes, views
4. **Same API** - Make.com unchanged, just swap backend

### Phase 3 (Dashboard):
1. **Prompt management** - Edit, test, version control
2. **Run inspection** - Debug pipeline, view I/O
3. **Claims analysis** - Query, filter, understand data

---

## Timeline

**Session 1:** ✅ Documentation organized
**Sessions 2-3:** Sheets design + CSV generation
**Sessions 4-5:** API middleware build
**Sessions 6-10:** Make.com integration (19 scenarios)
**Session 11:** Full pipeline validation

**Total:** ~11 sessions to working Sheets-based pipeline

**LATER:**
- Supabase migration
- Dashboard build

---

## Questions or Issues?

Refer to the full plan: `~/.claude/plans/zany-marinating-wreath.md`

This is a multi-session implementation. Take your time, annotate thoughtfully, and we'll build incrementally.
