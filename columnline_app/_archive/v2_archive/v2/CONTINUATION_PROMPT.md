# Columnline v2 - Session Continuation

## What Was Built

Complete production pipeline for Columnline dossier generation:

### Database (Supabase - 15 tables)
All tables created with `v2_` prefix. Verified working:
- 1 client (Span Construction)
- 14 prompts
- 14 prompt versions

### Code (Committed to main)
- `columnline_app/v2/` - Full pipeline implementation
- `admin/` - Streamlit dashboard
- `prompts/v2/` - 14 prompt files
- `database/migrations/` - SQL schema

### Key Files
- `columnline_app/v2/config.py` - Step definitions
- `columnline_app/v2/pipeline/runner.py` - Main orchestrator
- `columnline_app/v2/api/router.py` - API endpoints
- `admin/app.py` - Dashboard entry

## What Needs Testing

The code is complete but needs to be tested on the droplet where Python environment is set up.

### Test Commands (on droplet)
```bash
# 1. Pull latest code
cd /opt/automations
git pull

# 2. Run tests
python -m columnline_app.v2.test_pipeline

# 3. Start API and dashboard
uvicorn api.main:app --host 0.0.0.0 --port 8000
streamlit run admin/app.py --server.port 8501 --server.headless true
```

### What to Verify
1. API endpoints work: `curl https://api.columnline.dev/v2/health`
2. Dashboard loads: `http://64.225.120.95:8501`
3. Single step test passes
4. Full pipeline generates dossier with contacts

## Current State

### Completed
- [x] Database tables created
- [x] Prompts extracted from CSV
- [x] Prompts seeded to database
- [x] Test client created
- [x] API router built
- [x] Pipeline runner implemented
- [x] Dashboard pages created
- [x] Code committed and pushed

### Pending
- [ ] Test on droplet (Python env issues locally)
- [ ] Run full pipeline end-to-end
- [ ] Verify contacts have email/LinkedIn copy
- [ ] Verify claims extraction and merge

## Quick Reference

### Database
- Project ID: `uqqjzkbgiivhbazehljv`
- Tables all start with `v2_`
- Client ID: `8c996b78-7838-415f-9f37-16faf21c7ecd` (Span Construction)

### Pipeline Steps
1. `1-search-builder` (sync)
2. `2-signal-discovery` (agent)
3. `3-entity-research` (background - deep research)
4. `4-contact-discovery` (background - deep research)
5. `5a/5b/5c-enrich-*` (agent - parallel)
6. `6/6.2-enrich-contacts` (sync + agent per contact)
7. `7a/7.2-copy` (sync)
8. `7b-insight` (sync - MERGE POINT)
9. `8-media` (agent)
10. `9-dossier-plan` (sync)

### API Endpoints
- `GET /v2/health` - Health check
- `GET /v2/clients` - List clients
- `GET /v2/prompts` - List prompts
- `POST /v2/pipeline/start` - Start pipeline
- `GET /v2/pipeline/runs/{id}/live` - Poll status

## If Context Resets

1. Read `columnline_app/v2/README.md` for architecture overview
2. Read `~/.claude/plans/polished-swinging-gosling.md` for full plan
3. Check `columnline_app/v2/test_pipeline.py` for test logic
4. Run tests on droplet to verify everything works
