# Automations Development Skill

## Purpose
Help build, manage, and debug automations for the scraper/worker system. This project contains workers that run on a DigitalOcean droplet, managed via a Supabase registry.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  SUPABASE REGISTRY                                          │
│  Tables: automations, clients, templates, automation_runs   │
│  Query: by state, county, client, tags, status, template    │
└─────────────────────────────────────────────────────────────┘
                           │
              POST /run {"slug": "va-loudoun-permits"}
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  DIGITALOCEAN DROPLET                                       │
│  ├── FastAPI (port 8000) - receives job requests           │
│  ├── RQ Worker - executes jobs from Redis queue            │
│  ├── RQ Dashboard (port 9181) - visual job monitoring      │
│  └── Redis - job queue                                      │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  WORKERS (this repo)                                        │
│  workers/                                                    │
│  ├── scrapers/     - Data collection from various sources  │
│  ├── research/     - Deep company research (OpenAI)        │
│  ├── enrichment/   - Contact/lead enrichment               │
│  └── workflows/    - Multi-step pipelines                  │
└─────────────────────────────────────────────────────────────┘
```

## Scraper Patterns (Templates)

When building a new scraper, identify which pattern applies:

### Pattern 1: ArcGIS Permits
**Use for:** Counties using Accela, Tyler, or ArcGIS-based permit systems
**File:** `workers/scrapers/permits.py`
**識別:** URL contains `FeatureServer`, `MapServer`, or `arcgis`

```python
# Config structure
{
    "permit_endpoint": "https://gis.county.gov/.../PermitHistory/FeatureServer/0",
    "parcel_endpoint": "https://gis.county.gov/.../Parcels/MapServer/1",  # optional
    "case_types": ["Building Commercial", "Site Development"],
    "keywords": ["INDUSTRIAL", "DATA CENTER", "WAREHOUSE"],
    "min_lot_size": 5.0  # acres
}
```

### Pattern 2: State Portal (Firecrawl)
**Use for:** State government websites, CON applications, licensing boards
**File:** `workers/scrapers/portals.py`
**識別:** Standard HTML tables, pagination, form submissions

```python
# Config structure
{
    "portal_url": "https://state.gov/applications",
    "extraction_schema": {
        "table_selector": ".data-table",
        "fields": ["facility_name", "project_description", "estimated_cost"]
    },
    "pagination": {"type": "next_button", "selector": ".pagination-next"}
}
```

### Pattern 3: Public API
**Use for:** FERC, SAM.gov, SAMHSA, USAspending, EPA
**File:** `workers/scrapers/apis.py`
**識別:** Has documented API, returns JSON

```python
# Config structure
{
    "api_endpoint": "https://api.example.gov/v1/records",
    "auth": {"type": "api_key", "header": "X-API-Key"},
    "query_params": {"state": "VA", "min_value": 1000000},
    "field_mapping": {"source_field": "target_field"}
}
```

### Pattern 4: Browser Automation (Playwright)
**Use for:** JavaScript-heavy sites, login required, dynamic content
**File:** `workers/scrapers/browser.py`
**識別:** Content loads via JavaScript, requires interaction

```python
# Config structure
{
    "start_url": "https://portal.example.com/search",
    "login": {"username_field": "#email", "password_field": "#pass"},
    "steps": [
        {"action": "click", "selector": "#search-btn"},
        {"action": "wait", "selector": ".results"},
        {"action": "extract", "selector": ".result-item"}
    ]
}
```

### Pattern 5: Google Maps
**Use for:** Business discovery, facility mapping
**File:** `workers/scrapers/maps.py`
**識別:** Need to find businesses by category + location

```python
# Config structure
{
    "categories": ["behavioral health center", "mental health facility"],
    "locations": ["Cedar Rapids, IA", "Iowa City, IA"],
    "filters": {"min_reviews": 5, "max_reviews": 200}
}
```

## Naming Convention

**Slug format:** `{geography}-{source-type}`

Examples:
- `va-loudoun-permits` - Loudoun County VA building permits
- `az-maricopa-permits` - Maricopa County AZ building permits  
- `ia-statewide-llc-filings` - Iowa LLC filings (statewide)
- `ferc-pjm-interconnections` - FERC PJM region utility queue
- `gmaps-ia-eastern-behavioral-health` - Google Maps Iowa behavioral health

## Creating a New Automation

### Step 1: Identify the Pattern
Ask these questions:
1. What's the data source URL?
2. Does it have an API? → Pattern 3
3. Is it ArcGIS/Accela? → Pattern 1
4. Is it a state government portal? → Pattern 2
5. Does it require JavaScript/login? → Pattern 4
6. Is it business discovery? → Pattern 5

### Step 2: Check if Template Exists
```bash
# Look at existing scrapers
ls workers/scrapers/

# Check if similar automation exists
# Query Supabase or grep the codebase
```

### Step 3: Create or Extend

**If template exists:** Just add config to registry
```sql
INSERT INTO automations (slug, name, type, template, geography, config, ...)
VALUES ('va-fairfax-permits', 'Fairfax County VA Permits', 'scraper', 'arcgis_permits', 
        '{"state": "VA", "county": "Fairfax"}',
        '{"permit_endpoint": "https://...", "case_types": [...]}',
        ...);
```

**If new pattern needed:** Create worker file first, then register

### Step 4: Test
```bash
# Via API
curl -X POST http://DROPLET_IP:8000/run \
  -H "Content-Type: application/json" \
  -d '{"slug": "va-loudoun-permits"}'

# Check job status
curl http://DROPLET_IP:8000/jobs/JOB_ID
```

## Registry Queries

### Find automations
```sql
-- All Virginia scrapers
SELECT * FROM automations WHERE geography->>'state' = 'VA';

-- All permit scrapers
SELECT * FROM automations WHERE category = 'permits';

-- All scrapers for a client
SELECT * FROM automations WHERE client_id = 'uuid...';

-- Failed automations
SELECT * FROM automations WHERE last_run_status = 'failed';

-- By tag
SELECT * FROM automations WHERE 'data-center' = ANY(tags);
```

### Via API
```bash
GET /registry/automations?state=VA
GET /registry/automations?category=permits
GET /registry/automations?client_id=xxx
GET /registry/automations?status=failed
GET /registry/automations?tag=data-center
```

## File Structure

```
automations/
├── api/
│   ├── main.py              # FastAPI endpoints
│   └── registry.py          # Registry CRUD endpoints
├── workers/
│   ├── runner.py            # Dynamic runner (loads config → runs template)
│   ├── base.py              # Base worker class with progress updates
│   ├── scrapers/
│   │   ├── permits.py       # ArcGIS permit scraper
│   │   ├── portals.py       # State portal scraper (Firecrawl)
│   │   ├── apis.py          # Public API fetcher
│   │   ├── browser.py       # Playwright browser automation
│   │   └── maps.py          # Google Maps scraper
│   ├── research/
│   │   └── entity_research.py  # Deep company research
│   ├── enrichment/
│   │   └── leads.py         # Contact/lead enrichment
│   └── workflows/
│       └── pipelines.py     # Multi-step workflows
├── database/
│   └── schema.sql           # Supabase schema
└── requirements.txt
```

## Deployment

After making changes:
```bash
# SSH to droplet
ssh root@DROPLET_IP

# Pull latest
cd /opt/automations
git pull origin main

# Restart workers
systemctl restart automations-api automations-worker
```

## Common Tasks

### "Build a scraper for [County] permits"
1. Find their GIS/permit portal
2. Identify pattern (usually ArcGIS)
3. Get the FeatureServer endpoint
4. Add to registry with config
5. Test run

### "This scraper is failing"
1. Check dashboard: http://DROPLET_IP:9181
2. Find the failed job
3. Read error message
4. Check if endpoint changed (common)
5. Update config or fix code

### "Add a new client"
```sql
INSERT INTO clients (slug, name, icp_type, industry, target_geography)
VALUES ('new-client', 'New Client Name', 'gc', 'data_center_electrical',
        '{"states": ["VA", "TX"]}');
```

### "What scrapers do we have for [state]?"
```sql
SELECT slug, name, status, last_run_status 
FROM automations 
WHERE geography->>'state' = 'VA'
ORDER BY last_run_at DESC;
```

## Environment Variables

```
REDIS_URL=redis://localhost:6379
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
OPENAI_API_KEY=sk-...
APIFY_API_KEY=apify_api_...
FIRECRAWL_API_KEY=fc-...
```

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/run` | POST | Run automation by slug |
| `/jobs` | GET | List jobs |
| `/jobs/{id}` | GET | Get job status |
| `/jobs/{id}/stream` | GET | Stream progress (SSE) |
| `/registry/automations` | GET | Query automations |
| `/registry/automations` | POST | Create automation |
| `/registry/automations/{slug}` | GET | Get automation details |
| `/registry/templates` | GET | List templates |
| `/registry/clients` | GET | List clients |
| `/registry/stats` | GET | Registry statistics |
