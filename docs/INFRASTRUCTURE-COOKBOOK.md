# Infrastructure Cookbook: Self-Hosted AI Automation Server

**From Zero to Production in One Day**

This cookbook documents setting up a complete AI automation infrastructure for ~$12/month. By the end, you'll have:
- A 24/7 Linux server running your automations
- API endpoints accessible from anywhere (Vercel, Claude Code, external AI tools)
- Full observability (every AI call logged with input/output)
- Hot-swappable AI models (GPT-4.1, GPT-5.2, o4-mini-deep-research, Gemini)
- Auto-deploy from GitHub pushes

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Phase 1: DigitalOcean Droplet](#phase-1-digitalocean-droplet)
4. [Phase 2: Project Structure](#phase-2-project-structure)
5. [Phase 3: FastAPI Setup](#phase-3-fastapi-setup)
6. [Phase 4: Systemd Services](#phase-4-systemd-services)
7. [Phase 5: GitHub Auto-Deploy](#phase-5-github-auto-deploy)
8. [Phase 6: AI Module](#phase-6-ai-module)
9. [Phase 7: Prompt System](#phase-7-prompt-system)
10. [Phase 8: Supabase Logging](#phase-8-supabase-logging)
11. [Phase 9: ngrok (Temporary Access)](#phase-9-ngrok-temporary-access)
12. [Phase 10: Caddy SSL (Production)](#phase-10-caddy-ssl-production)
13. [Phase 11: Testing & Verification](#phase-11-testing--verification)
14. [Troubleshooting](#troubleshooting)
15. [Cost Breakdown](#cost-breakdown)
16. [Quick Reference](#quick-reference)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    YOUR APPS (Vercel, etc.)                         │
│                    CLAUDE CODE / AI TOOLS                           │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│              https://api.yourdomain.com (Caddy SSL)                │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    DigitalOcean Droplet ($12/mo)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   FastAPI    │  │  AI Module   │  │   Prompts    │              │
│  │   :8000      │  │  workers/    │  │   prompts/   │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                           │                                         │
│                           ▼                                         │
│                    ┌──────────────┐                                 │
│                    │   OpenAI     │                                 │
│                    │   Gemini     │                                 │
│                    │   Claude     │                                 │
│                    └──────────────┘                                 │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Supabase (Free Tier)                        │
│                    execution_logs, automations                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Why this architecture?**

| Alternative | Cost | Limits | Our Solution |
|------------|------|--------|--------------|
| Vercel Functions | Free-$20/mo | 10s timeout, cold starts | No limits, always warm |
| Modal.com | Pay-per-use | 5 cron jobs max | Unlimited crons |
| Railway | $5-20/mo | Memory limits | Full control |
| **DigitalOcean Droplet** | **$12/mo** | **None** | **Full Linux VM** |

---

## Prerequisites

Before starting, you need:

1. **DigitalOcean Account** - Sign up at digitalocean.com
2. **Domain Name** - Any registrar (Porkbun, Namecheap, etc.)
3. **GitHub Account** - For code storage and auto-deploy
4. **Supabase Account** - Free tier at supabase.com
5. **API Keys:**
   - OpenAI API key
   - (Optional) Google AI API key
   - (Optional) Anthropic API key
   - DigitalOcean Personal Access Token (for API management)

---

## Phase 1: DigitalOcean Droplet

### 1.1 Create the Droplet

1. Go to DigitalOcean → Create → Droplets
2. Choose:
   - **Region:** Closest to you (e.g., NYC, SFO)
   - **Image:** Ubuntu 24.04 LTS
   - **Size:** Basic → Regular → $12/mo (2GB RAM, 1 vCPU, 50GB SSD)
   - **Authentication:** Password (simpler) or SSH key
   - **Hostname:** `automations`

3. Note down the IP address (e.g., `64.225.120.95`)

### 1.2 Initial SSH Access

```bash
ssh root@YOUR_IP_ADDRESS
```

Enter your password when prompted.

### 1.3 Initial Server Setup

```bash
# Update system
apt update && apt upgrade -y

# Install essential packages
apt install -y python3.12 python3.12-venv python3-pip git curl ufw redis-server

# Enable firewall
ufw allow OpenSSH
ufw allow 8000/tcp  # FastAPI
ufw allow 80/tcp    # HTTP (for SSL cert)
ufw allow 443/tcp   # HTTPS
ufw --force enable

# Start Redis
systemctl enable redis-server
systemctl start redis-server
```

---

## Phase 2: Project Structure

### 2.1 Create Directory Structure

```bash
mkdir -p /opt/automations
cd /opt/automations

# Create Python virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Create folder structure
mkdir -p api workers prompts database
touch .env
```

### 2.2 Install Python Dependencies

```bash
pip install \
  fastapi \
  uvicorn \
  pydantic \
  python-dotenv \
  requests \
  httpx \
  openai \
  anthropic \
  google-generativeai \
  supabase \
  rq \
  redis
```

### 2.3 Environment Variables

Create `/opt/automations/.env`:

```bash
cat > /opt/automations/.env << 'EOF'
# AI API Keys
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
GOOGLE_API_KEY=your-google-key-here

# DigitalOcean (for API management - create/destroy droplets programmatically)
DIGITALOCEAN_TOKEN=dop_v1_your-token-here

# Supabase
SUPABASE_URL=https://yourproject.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...your-service-role-key

# Optional
APIFY_API_KEY=apify_api_your-key
FIRECRAWL_API_KEY=fc-your-key
EOF
```

---

## Phase 3: FastAPI Setup

### 3.1 Create Main API File

Create `/opt/automations/api/main.py`:

```python
"""
Automations API - FastAPI endpoints with full logging
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = FastAPI(title="Automations API")


class PromptRequest(BaseModel):
    prompt_name: str
    variables: Optional[dict] = None
    model: str = "gpt-4.1"
    background: bool = False
    log: bool = True
    tags: Optional[List[str]] = None


@app.get("/")
def root():
    return {"status": "ok", "service": "automations-api"}


@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/prompts")
def list_prompts():
    from pathlib import Path
    prompts_dir = Path("/opt/automations/prompts")
    if not prompts_dir.exists():
        return {"prompts": [], "count": 0}
    prompts = [{"name": f.stem, "path": str(f)} for f in prompts_dir.glob("*.md")]
    return {"prompts": prompts, "count": len(prompts)}


@app.post("/test/prompt")
def test_prompt(request: PromptRequest):
    """Test a prompt with full logging to Supabase."""
    from workers.ai import prompt
    
    try:
        result = prompt(
            name=request.prompt_name,
            variables=request.variables,
            model=request.model,
            log=request.log,
            tags=request.tags or [],
        )
        return {
            "status": "completed",
            "prompt_name": result["prompt_name"],
            "model": result["model"],
            "elapsed_seconds": result.get("elapsed_seconds"),
            "output": result.get("output"),
            "logged": request.log,
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/logs")
def get_logs(limit: int = 20, status: Optional[str] = None):
    """View recent execution logs."""
    from supabase import create_client
    
    supabase = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    )
    
    query = supabase.table("execution_logs").select("*").order("started_at", desc=True).limit(limit)
    if status:
        query = query.eq("status", status)
    
    result = query.execute()
    return {"logs": result.data, "count": len(result.data)}


@app.get("/logs/{log_id}")
def get_log(log_id: str):
    """Get a specific log entry with full input/output."""
    from supabase import create_client
    
    supabase = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    )
    
    result = supabase.table("execution_logs").select("*").eq("id", log_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Log not found")
    
    return result.data[0]
```

---

## Phase 4: Systemd Services

### 4.1 Create FastAPI Service

Create `/etc/systemd/system/automations-api.service`:

```bash
cat > /etc/systemd/system/automations-api.service << 'EOF'
[Unit]
Description=Automations FastAPI Service
After=network.target redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/automations
Environment="PATH=/opt/automations/venv/bin"
EnvironmentFile=/opt/automations/.env
ExecStart=/opt/automations/venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
```

### 4.2 Enable and Start

```bash
systemctl daemon-reload
systemctl enable automations-api
systemctl start automations-api

# Verify
systemctl status automations-api
curl http://localhost:8000/health
```

---

## Phase 5: GitHub Auto-Deploy

### 5.1 Initialize Git Repository

```bash
cd /opt/automations
git init
git remote add origin https://github.com/yourusername/automations.git
```

### 5.2 Create GitHub Action

Create `.github/workflows/deploy.yml` in your repo:

```yaml
name: Deploy to Droplet

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.DROPLET_IP }}
          username: root
          password: ${{ secrets.DROPLET_PASSWORD }}
          script: |
            cd /opt/automations
            git pull origin main
            source venv/bin/activate
            pip install -r requirements.txt --quiet
            systemctl restart automations-api
```

### 5.3 Add GitHub Secrets

In your GitHub repo → Settings → Secrets → Actions:
- `DROPLET_IP`: Your droplet IP
- `DROPLET_PASSWORD`: Your SSH password

---

## Phase 6: AI Module

### 6.1 Create AI Module

Create `/opt/automations/workers/ai.py`:

```python
"""
Universal AI Module - Hot-swappable models with full logging
"""
import os
import time
from typing import Optional
from dotenv import load_dotenv

load_dotenv("/opt/automations/.env")

# Model configurations
MODELS = {
    # OpenAI Standard
    "gpt-4.1": {"provider": "openai", "model": "gpt-4.1"},
    "gpt-4.1-mini": {"provider": "openai", "model": "gpt-4.1-mini"},
    "gpt-5.2": {"provider": "openai", "model": "gpt-5.2"},
    
    # OpenAI Reasoning
    "o3": {"provider": "openai", "model": "o3"},
    "o4-mini": {"provider": "openai", "model": "o4-mini"},
    "o4-mini-deep-research": {"provider": "openai_responses", "model": "o4-mini"},
    
    # Google
    "gemini-2.5-pro": {"provider": "google", "model": "gemini-2.5-pro-preview-06-05"},
    "gemini-2.5-flash": {"provider": "google", "model": "gemini-2.5-flash-preview-05-20"},
}


def ai(message: str, model: str = "gpt-4.1", system: str = None) -> str:
    """Simple AI call - just returns the response text."""
    config = MODELS.get(model, MODELS["gpt-4.1"])
    
    if config["provider"] == "openai":
        return _openai_call(message, config["model"], system)
    elif config["provider"] == "google":
        return _google_call(message, config["model"], system)
    else:
        raise ValueError(f"Unknown provider: {config['provider']}")


def _openai_call(message: str, model: str, system: str = None) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": message})
    
    response = client.chat.completions.create(model=model, messages=messages)
    return response.choices[0].message.content


def _google_call(message: str, model: str, system: str = None) -> str:
    import google.generativeai as genai
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    
    model_obj = genai.GenerativeModel(model)
    prompt = f"{system}\n\n{message}" if system else message
    response = model_obj.generate_content(prompt)
    return response.text


def prompt(
    name: str,
    variables: dict = None,
    model: str = "gpt-4.1",
    log: bool = True,
    tags: list = None,
) -> dict:
    """Load a prompt template, fill variables, execute, and log."""
    import json
    from pathlib import Path
    
    # Load template
    template_path = Path(f"/opt/automations/prompts/{name}.md")
    if not template_path.exists():
        raise FileNotFoundError(f"Prompt not found: {name}")
    
    template = template_path.read_text()
    
    # Fill variables
    if variables:
        for key, value in variables.items():
            placeholder = "{{" + key + "}}"
            if isinstance(value, (dict, list)):
                value = json.dumps(value, indent=2)
            template = template.replace(placeholder, str(value))
    
    # Optional logging
    logger = None
    if log:
        from workers.logger import ExecutionLogger
        logger = ExecutionLogger(
            worker_name=f"ai.prompt.{model}",
            automation_slug=None,
            input_data={"prompt_name": name, "model": model, "variables": variables},
            tags=tags or [model, name.split(".")[0]],
        )
    
    # Execute
    start = time.time()
    try:
        output = ai(template, model=model)
        elapsed = time.time() - start
        
        result = {
            "prompt_name": name,
            "model": model,
            "input": template,
            "output": output,
            "elapsed_seconds": round(elapsed, 2),
        }
        
        if logger:
            logger.success(result)
        
        return result
        
    except Exception as e:
        if logger:
            logger.fail(e)
        raise
```

---

## Phase 7: Prompt System

### 7.1 Create Prompts Directory

Prompts are Markdown files with `{{variable}}` placeholders.

Create `/opt/automations/prompts/model-test.md`:

```markdown
# Model Test Prompt

You are a helpful assistant. Answer the following question concisely.

## Question

{{question}}

## Instructions

- Be direct and factual
- Keep your response under 200 words
```

### 7.2 Usage

```python
from workers.ai import prompt

result = prompt(
    name="model-test",
    variables={"question": "What is cloud computing?"},
    model="gpt-4.1"
)
print(result["output"])
```

---

## Phase 8: Supabase Logging

### 8.1 Create Tables in Supabase

Run this SQL in your Supabase SQL editor:

```sql
-- Execution logs table
CREATE TABLE public.execution_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  automation_slug TEXT,
  worker_name TEXT,
  started_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  runtime_seconds FLOAT,
  status TEXT DEFAULT 'running',
  input JSONB,
  output JSONB,
  error JSONB,
  metadata JSONB DEFAULT '{}'::JSONB,
  notes TEXT,
  tags TEXT[]
);

-- Indexes
CREATE INDEX idx_execution_logs_started_at ON execution_logs(started_at DESC);
CREATE INDEX idx_execution_logs_status ON execution_logs(status);
CREATE INDEX idx_execution_logs_tags ON execution_logs USING GIN(tags);
```

### 8.2 Create Logger Module

Create `/opt/automations/workers/logger.py`:

```python
"""
Execution Logger - Full transparency for all AI calls
"""
import os
import traceback
from datetime import datetime
from typing import Optional, Any
from supabase import create_client


class ExecutionLogger:
    def __init__(
        self,
        worker_name: str,
        input_data: dict,
        automation_slug: Optional[str] = None,
        notes: Optional[str] = None,
        tags: Optional[list] = None
    ):
        self.supabase = create_client(
            os.environ["SUPABASE_URL"],
            os.environ["SUPABASE_SERVICE_ROLE_KEY"]
        )
        self.worker_name = worker_name
        self.start_time = datetime.utcnow()
        self.log_id = None
        self._tags = tags or []
        
        # Create log entry
        result = self.supabase.table("execution_logs").insert({
            "worker_name": worker_name,
            "automation_slug": automation_slug,
            "input": input_data,
            "notes": notes,
            "tags": self._tags,
            "status": "running"
        }).execute()
        
        if result.data:
            self.log_id = result.data[0]["id"]
    
    def success(self, output: Any):
        runtime = (datetime.utcnow() - self.start_time).total_seconds()
        
        if self.log_id:
            self.supabase.table("execution_logs").update({
                "status": "success",
                "completed_at": datetime.utcnow().isoformat(),
                "runtime_seconds": round(runtime, 2),
                "output": output if isinstance(output, dict) else {"result": output},
            }).eq("id", self.log_id).execute()
        
        return output
    
    def fail(self, error: Exception):
        runtime = (datetime.utcnow() - self.start_time).total_seconds()
        
        if self.log_id:
            self.supabase.table("execution_logs").update({
                "status": "failed",
                "completed_at": datetime.utcnow().isoformat(),
                "runtime_seconds": round(runtime, 2),
                "error": {
                    "type": type(error).__name__,
                    "message": str(error),
                    "traceback": traceback.format_exc()
                },
            }).eq("id", self.log_id).execute()
        
        raise error
```

---

## Phase 9: ngrok (Temporary Access)

**Why ngrok?** Before setting up SSL, ngrok provides a quick way to expose your API externally (useful for testing with Claude.ai or other external tools).

### 9.1 Install ngrok

```bash
snap install ngrok
ngrok config add-authtoken YOUR_NGROK_TOKEN
```

### 9.2 Create Systemd Service for Persistent Tunnel

```bash
cat > /etc/systemd/system/ngrok.service << 'EOF'
[Unit]
Description=ngrok tunnel
After=network.target

[Service]
Type=simple
ExecStart=/snap/bin/ngrok http 8000 --url your-subdomain.ngrok-free.dev
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ngrok
systemctl start ngrok
```

### 9.3 Important: ngrok Header

External requests to ngrok URLs need this header:
```
ngrok-skip-browser-warning: true
```

**Note:** ngrok is a stopgap. For production, use Caddy (Phase 10).

---

## Phase 10: Caddy SSL (Production)

**Why Caddy?** 
- Automatic SSL certificates (Let's Encrypt)
- Auto-renewal
- Simple configuration
- Works everywhere (Claude Code, Vercel, external AI tools)

### 10.1 Point Your Domain

In your DNS provider, create an A record:
```
api.yourdomain.com → YOUR_DROPLET_IP
```

### 10.2 Install Caddy

```bash
apt install -y caddy
```

### 10.3 Configure Caddy

```bash
cat > /etc/caddy/Caddyfile << 'EOF'
api.yourdomain.com {
    reverse_proxy localhost:8000
}
EOF
```

### 10.4 Start Caddy

```bash
systemctl enable caddy
systemctl restart caddy
```

### 10.5 Verify

```bash
curl https://api.yourdomain.com/health
```

**Troubleshooting SSL:**
- Make sure ports 80 and 443 are open: `ufw allow 80/tcp && ufw allow 443/tcp`
- Check Caddy logs: `journalctl -u caddy --no-pager -n 30`
- DNS propagation can take 5-10 minutes

---

## Phase 11: Testing & Verification

### 11.1 Health Check

```bash
curl https://api.yourdomain.com/health
```

Expected:
```json
{"status": "healthy", "timestamp": "2026-01-05T..."}
```

### 11.2 Run a Prompt Test

```bash
curl -X POST https://api.yourdomain.com/test/prompt \
  -H "Content-Type: application/json" \
  -d '{
    "prompt_name": "model-test",
    "model": "gpt-4.1",
    "variables": {"question": "What is 2+2?"}
  }'
```

### 11.3 Check Logs

```bash
curl https://api.yourdomain.com/logs?limit=5
```

### 11.4 View Full Log Entry

```bash
curl https://api.yourdomain.com/logs/YOUR_LOG_ID
```

---

## Troubleshooting

### API Not Responding

```bash
# Check service status
systemctl status automations-api

# View logs
journalctl -u automations-api -n 50 --no-pager

# Restart
systemctl restart automations-api
```

### SSL Certificate Issues

```bash
# Check Caddy logs
journalctl -u caddy -n 30 --no-pager | grep -i error

# Verify DNS
dig api.yourdomain.com +short

# Ensure ports are open
ufw status
```

### Supabase Connection Issues

```bash
# Test from droplet
source /opt/automations/venv/bin/activate
python3 -c "
from supabase import create_client
import os
from dotenv import load_dotenv
load_dotenv('/opt/automations/.env')
client = create_client(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_ROLE_KEY'])
print(client.table('execution_logs').select('*').limit(1).execute())
"
```

### TLS Issues from Local Machine

If your local Mac can't connect via HTTPS (TLS errors), it's likely a Python/LibreSSL version issue. Solutions:
1. Use the direct IP for local testing: `http://YOUR_IP:8000`
2. Use the HTTPS URL from Claude.ai/external tools (they don't have this issue)
3. Upgrade local Python: `brew upgrade python`

---

## Cost Breakdown

| Service | Cost | Notes |
|---------|------|-------|
| DigitalOcean Droplet | $12/mo | 2GB RAM, 1 vCPU, 50GB SSD |
| Supabase | $0 | Free tier (500MB database) |
| Domain | $10/year | Optional if using ngrok |
| ngrok | $0 | Free tier with custom subdomain |
| **Total** | **~$12/mo** | |

**Compare to alternatives:**
- Vercel Pro: $20/mo (with 10s function timeout limits)
- Railway: $5-20/mo (memory limits)
- Modal.com: $0.10+/hr (5 cron job limit)

---

## Quick Reference

### SSH Access
```bash
ssh root@YOUR_IP
# Password: your-password
```

### Service Management
```bash
# Restart API
systemctl restart automations-api

# View logs
journalctl -u automations-api -f

# Check status
systemctl status automations-api
```

### Manual Deploy
```bash
cd /opt/automations
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
systemctl restart automations-api
```

### File Locations
```
/opt/automations/          # Project root
├── api/main.py            # FastAPI endpoints
├── workers/ai.py          # AI module
├── workers/logger.py      # Supabase logger
├── prompts/               # Markdown prompt templates
├── .env                   # Environment variables
└── venv/                  # Python virtual environment

/etc/systemd/system/       # Service files
├── automations-api.service
├── ngrok.service
└── ...

/etc/caddy/Caddyfile       # Caddy config
```

### API Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/prompts` | GET | List available prompts |
| `/test/prompt` | POST | Run a prompt |
| `/logs` | GET | View execution logs |
| `/logs/{id}` | GET | Get full log details |

### URLs
| Type | URL |
|------|-----|
| **Production** | `https://api.yourdomain.com` |
| **Direct IP** | `http://YOUR_IP:8000` |
| **ngrok (backup)** | `https://your-subdomain.ngrok-free.dev` |

---

## What's Next?

With this infrastructure in place, you can:

1. **Add more prompts** - Create `.md` files in `/opt/automations/prompts/`
2. **Build workers** - Add background job processors in `/opt/automations/workers/`
3. **Schedule crons** - Use systemd timers or a cron job scheduler
4. **Scale up** - Upgrade the droplet if needed ($24/mo for 4GB RAM)
5. **Add Redis Queue** - For async job processing with RQ
6. **Programmatic Infrastructure** - Use the DigitalOcean API to spin up/down droplets

### DigitalOcean API Examples

With your DO token, you can manage infrastructure programmatically:

```bash
# List all droplets
curl -s -X GET "https://api.digitalocean.com/v2/droplets" \
  -H "Authorization: Bearer $DIGITALOCEAN_TOKEN" | python3 -m json.tool

# Get droplet details
curl -s -X GET "https://api.digitalocean.com/v2/droplets/DROPLET_ID" \
  -H "Authorization: Bearer $DIGITALOCEAN_TOKEN"

# Create a new droplet
curl -X POST "https://api.digitalocean.com/v2/droplets" \
  -H "Authorization: Bearer $DIGITALOCEAN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "worker-2",
    "region": "nyc1",
    "size": "s-1vcpu-2gb",
    "image": "ubuntu-24-04-x64"
  }'

# Power off a droplet
curl -X POST "https://api.digitalocean.com/v2/droplets/DROPLET_ID/actions" \
  -H "Authorization: Bearer $DIGITALOCEAN_TOKEN" \
  -d '{"type": "power_off"}'

# Destroy a droplet
curl -X DELETE "https://api.digitalocean.com/v2/droplets/DROPLET_ID" \
  -H "Authorization: Bearer $DIGITALOCEAN_TOKEN"
```

This enables auto-scaling: spin up workers when needed, destroy when done.

---

*Document created: January 5, 2026*
*Infrastructure cost: $12/month*
*Setup time: ~4 hours (including troubleshooting)*
