# Automations

A simple, scalable worker queue system for running automations, scrapers, and background jobs.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  DigitalOcean Droplet                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌───────────────────┐   │
│  │ FastAPI     │  │ RQ Workers  │  │ RQ Dashboard      │   │
│  │ :8000       │  │ (scalable)  │  │ :9181             │   │
│  └──────┬──────┘  └──────┬──────┘  └─────────┬─────────┘   │
│         └────────────────┼───────────────────┘             │
│                          ▼                                  │
│                  DigitalOcean Managed Redis                │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Create DigitalOcean Resources

1. **Droplet**: Docker on Ubuntu, $24/mo (4GB RAM)
2. **Managed Redis**: $15/mo

### 2. Setup Droplet

SSH into your droplet and run:

```bash
curl -sSL https://raw.githubusercontent.com/YOUR_USERNAME/automations/main/scripts/setup.sh | bash
```

Then edit `.env` with your API keys:

```bash
nano /opt/automations/.env
```

### 3. Add GitHub Secrets for Auto-Deploy

Go to GitHub → Settings → Secrets → Actions:
- `DROPLET_IP`: Your droplet's IP address
- `SSH_PRIVATE_KEY`: Your SSH private key

Now every push to `main` will auto-deploy!

## Usage

### Submit a Job

```bash
curl -X POST http://YOUR_IP:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "worker": "research.entity_research",
    "params": {
      "client_info": "Client name and context...",
      "target_info": "Company to research..."
    }
  }'
```

Response:
```json
{
  "job_id": "abc123",
  "status": "queued",
  "worker": "research.entity_research"
}
```

### Check Job Status

```bash
curl http://YOUR_IP:8000/jobs/abc123
```

### Stream Job Progress (for real-time UI updates)

```bash
curl http://YOUR_IP:8000/jobs/abc123/stream
```

### View Dashboard

Open `http://YOUR_IP:9181` in your browser to see:
- All queued jobs
- Running jobs
- Completed jobs
- Failed jobs (with error details)

## Adding New Workers

1. Create a new file in `workers/`:

```python
# workers/scrapers/my_scraper.py
from rq import get_current_job

def run_my_scraper(url: str, config: dict) -> dict:
    job = get_current_job()
    
    # Update progress
    job.meta = {"message": "Starting...", "percent": 10}
    job.save_meta()
    
    # Do work...
    result = {"data": "scraped stuff"}
    
    job.meta = {"message": "Done!", "percent": 100}
    job.save_meta()
    
    return result
```

2. Register it in `api/main.py`:

```python
from workers.scrapers.my_scraper import run_my_scraper
worker_map["scrapers.my_scraper"] = run_my_scraper
```

3. Push to GitHub - it auto-deploys!

## Project Structure

```
automations/
├── api/
│   └── main.py           # FastAPI endpoints
├── workers/
│   ├── base.py           # Base worker class
│   ├── scrapers/         # Scraper workers
│   ├── research/         # Research workers
│   ├── enrichment/       # Data enrichment workers
│   └── notifications/    # Email/Slack workers
├── scripts/
│   └── setup.sh          # Server setup script
├── docker-compose.yml    # Container orchestration
├── Dockerfile
├── requirements.txt
└── .github/workflows/
    └── deploy.yml        # Auto-deploy on push
```

## Scaling

Scale workers when you have many jobs:

```bash
docker-compose up -d --scale worker=5
```

## Monitoring

- **Dashboard**: `http://YOUR_IP:9181` - Visual job monitoring
- **API Health**: `http://YOUR_IP:8000/` - Health check
- **API Docs**: `http://YOUR_IP:8000/docs` - Swagger UI
- **Docker Logs**: `docker-compose logs -f worker` - Live logs

## Available Workers

| Worker | Description | Params |
|--------|-------------|--------|
| `research.entity_research` | Deep company research using o4-mini | `client_info`, `target_info` |

## Costs

- Droplet (4GB): $24/mo
- Managed Redis: $15/mo
- **Total**: ~$39/mo

## License

MIT
