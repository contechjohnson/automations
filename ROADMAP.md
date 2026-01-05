# Automation Roadmap

> Living document tracking automation development priorities.
> Last updated: 2025-01-05

---

## 🔥 NOW (Current Sprint)

*Active work - max 3 items*

### Scraper Framework Foundation
**Priority:** P0 | **Effort:** L | **Client:** All
**Status:** In Progress

Building the core scraper framework with 5 reusable templates:
1. ArcGIS Permit Scraper (Template 1)
2. Public API Scraper (Template 2) 
3. Firecrawl Portal Scraper (Template 3)
4. Job Board Scraper (Template 4)
5. Google Maps Business Scraper (Template 5)

**Why:** Foundation for all client-specific scrapers. 80% of scrapers fit these 5 patterns.

**Depends on:** None
**Enables:** All client deployments

---

## 📋 NEXT (Up Next)

*Ready to start when NOW completes. Directives written or nearly ready.*

### Enrichment Layer
**Priority:** P0 | **Effort:** M | **Client:** All
**Status:** Scoped

Build 3 core enrichment modules:
- LinkedIn Contact Finder (Apify integration)
- Company Entity Resolution (domain discovery)
- Signal Cross-Reference (aggregate by company)

**Why:** Scrapers output signals → Enrichment discovers contacts. Can't deliver leads without this.

**Depends on:** Scraper Framework Foundation
**Enables:** LLM Narrative Generation, all client deliverables

---

### LLM Narrative Generation
**Priority:** P0 | **Effort:** M | **Client:** All
**Status:** Scoped

Transform structured data → seed narratives:
- LLM prompt template with ICP parameterization
- Quality scoring (completeness, source count)
- Human review interface (CSV export)
- Cost tracking (tokens per seed)

**Why:** Final transformation layer. Turns raw signals into actionable sales intel.

**Depends on:** Enrichment Layer
**Enables:** Client deliverables

---

## 📊 PRIORITIZED BACKLOG

*Ranked by priority. Rough scope, not fully specified.*

### 1. Span Construction Deployment (Roger Acres)
**Priority:** P1 | **Effort:** M | **Client:** Span Construction
**Status:** Scoped (see Full_framework.)

Configure 10 priority sources for data center signals:
- Loudoun County VA permits
- FERC interconnection queues (PJM, MISO, ERCOT)
- Ohio/Iowa/Texas permits
- LinkedIn DC construction jobs
- Nevada mining commission

**Target:** 400-600 seeds for Q1 2027+ construction
**Why:** First paying client deliverable. Proves the framework.

---

### 2. ICP Configuration Library
**Priority:** P1 | **Effort:** M | **Client:** Internal
**Status:** Idea

Create ICP templates that auto-select scrapers:
- `icp/data_center_contractor.yaml`
- `icp/commercial_broker.yaml`
- `icp/ffe_contractor.yaml`
- Scoring system (Success Probability × Client Relevance)

**Why:** Makes framework truly reusable. New client = new YAML, not new code.

---

### 3. Abi Reiland Deployment
**Priority:** P2 | **Effort:** M | **Client:** Abi Reiland
**Status:** Scoped

Configure sources for Eastern Iowa commercial broker:
- Iowa Secretary of State LLC filings
- Iowa Board of Medicine/Dental licenses
- SAMHSA grants (Iowa)
- SBA WOSB certifications

**Target:** 200-300 business formation signals
**Why:** Second client. Different ICP validates framework flexibility.

---

### 4. Paul Phelan Deployment (Healthcare FFE)
**Priority:** P2 | **Effort:** M | **Client:** Phelan's Interiors
**Status:** Scoped

Configure sources for healthcare FFE contractor:
- Iowa CON applications
- Google Maps behavioral health facilities
- SAMHSA grants
- Iowa HHS inspection citations

**Target:** Behavioral health facilities in 11-county Eastern Iowa
**Why:** Third client type. Proves healthcare vertical.

---

### 5. Modal.com Deployment
**Priority:** P2 | **Effort:** S | **Client:** Internal
**Status:** Idea

Production deployment infrastructure:
- Scheduled scraper runs (daily/weekly)
- Cost tracking
- Error alerting
- Summary emails

**Why:** Can't run scrapers manually forever. Need automation.

---

### 6. Supabase Dashboard Views
**Priority:** P3 | **Effort:** S | **Client:** Internal
**Status:** Idea

Pre-built views for common queries:
- `v_recent_logs`
- `v_failed_logs`
- `v_active_scrapers`
- `v_automations_by_state`

**Why:** Makes debugging and monitoring easier.

---

## 💡 IDEAS

*Unscoped ideas. Needs discussion before prioritizing.*

### Deep Research Integration
Use o4-mini-deep-research for company intel enrichment. Currently using gpt-4.1 which doesn't have web search.

**Questions:** Cost per seed? Quality improvement? Background job handling?

---

### Webhook Triggers
Let external systems trigger automations (e.g., new permit filed → auto-enrich).

**Questions:** Security? Rate limiting? Which events?

---

### Seed Quality Scoring
Automated scoring of generated seeds:
- Signal strength (multiple sources?)
- Contact quality (right titles?)
- Timing fit (within ICP window?)

**Questions:** Thresholds? Human review workflow?

---

### Historical Backfill
Scrape historical permits (not just rolling 90 days) for initial client deliverables.

**Questions:** Data availability? Storage costs? One-time vs ongoing?

---

## ✅ COMPLETED

*Done items with completion date.*

### Infrastructure Setup — 2025-01-04
- DigitalOcean droplet deployed
- FastAPI running at api.columnline.dev
- Supabase execution_logs table created
- GitHub auto-deploy configured

### Maricopa Permit Scraper (Proof of Concept) — 2025-01-03
- ArcGIS permit scraper working
- 2-hop spatial enrichment (permit → parcel)
- 114/114 permits enriched (100%)
- Validated the pattern

### AI Abstraction Layer — 2025-01-04
- `workers/ai.py` with prompt() function
- Multi-model support (gpt-4.1, gemini, etc.)
- Mandatory logging to Supabase
- Deep research with background mode

---

## Priority Definitions

| Priority | Meaning | Timeline |
|----------|---------|----------|
| **P0** | Critical path - blocks everything | This week |
| **P1** | High value - do soon | Next 2 weeks |
| **P2** | Important - scheduled | This month |
| **P3** | Nice to have | When time permits |

## Effort Definitions

| Effort | Meaning | Time |
|--------|---------|------|
| **S** | Quick win | < 1 day |
| **M** | Medium | 2-4 days |
| **L** | Large | 1-2 weeks |
| **XL** | Epic | 2+ weeks, consider splitting |
