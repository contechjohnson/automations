# Automations

A scalable worker queue system for managing thousands of automations across different geographies, clients, and use cases.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           REGISTRY (Supabase)                            │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ automations table                                                  │  │
│  │ • 3000+ county scrapers (config-driven, not separate files)       │  │
│  │ • Query by: state, county, client, ICP, template, status          │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          TEMPLATES (Git Repo)                            │
│  • arcgis_permits.py    - 750+ jurisdictions                            │
│  • state_portal.py      - State government portals                       │
│  • public_api.py        - FERC, SAM.gov, etc.                           │
│  • entity_research.py   - Deep company research                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         WORKER QUEUE (Redis + RQ)                        │
│  • Submit jobs via API                                                   │
│  • Stream progress updates                                               │
│  • Dashboard for visibility                                              │
└─────────────────────────────────────────────────────────────────────────┘
```

## Key Concept: Config-Driven Automations

You don't need 3,000 Python files. You need:
- **~10 Templates** (by scraper type)
- **~3,000 Configs** (stored in Supabase, not files)
- **1 Runner** (loads config → runs template)

```python
# Register a new county scraper (just add to database)
POST /registry/automations
{
    "slug": "loudoun-va-permits",
    "name": "Loudoun County VA Building Permits",
    "type": "scraper",
    "category": "permits",
    "template": "arcgis_permits",
    "geography": {"state": "VA", "county": "Loudoun"},
    "icp_types": ["gc", "trades", "developer"],
    "config": {
        "permit_endpoint": "https://gis.loudoun.gov/...",
        "case_types": ["Building Commercial", "Site Development"],
        "keywords": ["DATA CENTER", "INDUSTRIAL"]
    }
}

# Run it
POST /run
{"slug": "loudoun-va-permits"}
```

## API Endpoints

### Jobs
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/jobs` | POST | Submit a job to queue |
| `/jobs` | GET | List jobs (filter by status) |
| `/jobs/{id}` | GET | Get job status & result |
| `/jobs/{id}/stream` | GET | Stream progress (SSE) |
| `/run` | POST | Run automation by slug |

### Registry
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/registry/automations` | GET | Query automations |
| `/registry/automations` | POST | Create automation |
| `/registry/automations/{slug}` | GET | Get automation details |
| `/registry/automations/{slug}` | PATCH | Update automation |
| `/registry/templates` | GET | List available templates |
| `/registry/clients` | GET | List clients |
| `/registry/geography/states` | GET | Automations by state |
| `/registry/stats` | GET | Overall statistics |

### Query Examples

```bash
# All Virginia scrapers
curl "http://YOUR_IP:8000/registry/automations?state=VA&type=scraper"

# All data center permits
curl "http://YOUR_IP:8000/registry/automations?category=permits&tag=data-centers"

# Failed automations
curl "http://YOUR_IP:8000/registry/automations?status=failed"

# For a specific client
curl "http://YOUR_IP:8000/registry/automations?client_id=xxx"

# Search by name
curl "http://YOUR_IP:8000/registry/automations?search=maricopa"
```

## Quick Start

### 1. Create DigitalOcean Resources

1. **Droplet**: Docker on Ubuntu, $24/mo (4GB RAM)
2. **Managed Redis**: $15/mo

### 2. Setup Supabase

1. Create project at [supabase.com](https://supabase.com)
2. Run `database/schema.sql` in SQL Editor
3. Copy your URL and service role key

### 3. Setup Droplet

```bash
ssh root@YOUR_DROPLET_IP
mkdir -p /opt/automations
cd /opt/automations
git clone https://github.com/contechjohnson/automations.git .

# Create .env
nano .env
```

Add to `.env`:
```
REDIS_URL=rediss://default:xxx@xxx.db.ondigitalocean.com:25061
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJxxx
OPENAI_API_KEY=sk-xxx
```

Start:
```bash
docker-compose build
docker-compose up -d
```

### 4. Access

- **API Docs**: `http://YOUR_IP:8000/docs`
- **Dashboard**: `http://YOUR_IP:9181`

## Project Structure

```
automations/
├── api/
│   ├── main.py           # FastAPI app + job endpoints
│   └── registry.py       # Registry API (query, create, update)
├── workers/
│   ├── runner.py         # Dynamic runner (loads config → runs template)
│   ├── templates/        # Reusable templates
│   │   ├── arcgis_permits.py
│   │   ├── state_portal.py
│   │   └── public_api.py
│   ├── research/
│   │   └── entity_research.py
│   └── base.py           # Base worker class
├── database/
│   └── schema.sql        # Supabase schema
├── docker-compose.yml
└── requirements.txt
```

## Templates

| Template | Use Case | Jurisdictions |
|----------|----------|---------------|
| `arcgis_permits` | Building permits | 750+ (Accela/Tyler) |
| `state_portal` | State gov portals (Firecrawl) | Any |
| `public_api` | FERC, SAM.gov, etc. | Federal |
| `job_board` | LinkedIn, Indeed | Any |
| `google_maps` | Business discovery | Any |
| `entity_research` | Deep company research | Any |

## Adding a New Scraper

### Option 1: Via API (recommended for Claude)

```bash
curl -X POST "http://YOUR_IP:8000/registry/automations" \
  -H "Content-Type: application/json" \
  -d '{
    "slug": "travis-tx-permits",
    "name": "Travis County TX Building Permits",
    "type": "scraper",
    "category": "permits", 
    "template": "arcgis_permits",
    "geography": {"state": "TX", "county": "Travis"},
    "icp_types": ["gc", "developer"],
    "config": {
        "permit_endpoint": "https://gis.traviscountytx.gov/...",
        "case_types": ["Commercial Building"],
        "keywords": ["DATA CENTER", "WAREHOUSE"]
    }
}'
```

### Option 2: Via Supabase Dashboard

Insert directly into `automations` table.

## Running Automations

```bash
# Run by slug
curl -X POST "http://YOUR_IP:8000/run" \
  -H "Content-Type: application/json" \
  -d '{"slug": "maricopa-az-permits"}'

# Get job status
curl "http://YOUR_IP:8000/jobs/JOB_ID"

# Stream progress
curl "http://YOUR_IP:8000/jobs/JOB_ID/stream"
```

## Claude's Interface

Claude can manage automations through the registry API:

```
"Show me all Virginia scrapers" → GET /registry/automations?state=VA
"Create a new permit scraper for Loudoun County" → POST /registry/automations
"What scrapers are failing?" → GET /registry/automations?status=failed
"Run the Maricopa permits scraper" → POST /run {"slug": "maricopa-az-permits"}
"Show me everything for client Span Construction" → GET /registry/automations?client_id=xxx
```

## Scaling

```bash
# Scale workers
docker-compose up -d --scale worker=5
```

## Costs

- Droplet (4GB): $24/mo
- Managed Redis: $15/mo
- Supabase (Free tier): $0
- **Total**: ~$39/mo

## License

MIT
