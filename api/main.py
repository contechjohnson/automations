"""
Automations API - FastAPI endpoints with full logging
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = FastAPI(title="Automations API")

# CORS middleware for dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v2 router (ARCHIVED - commented out for Make.com-first approach)
# from columnline_app.v2.api.router import router as v2_router
# app.include_router(v2_router)

# Include Make.com API endpoints
from api.v2.prompts import router as prompts_router
from api.v2.clients import router as clients_router
from api.v2.logs import router as logs_router
from api.v2.transform import router as transform_router

app.include_router(prompts_router)
app.include_router(clients_router)
app.include_router(logs_router)
app.include_router(transform_router)

# Include Columnline Supabase API
from api.columnline import router as columnline_router
app.include_router(columnline_router)


class PromptRequest(BaseModel):
    prompt_name: str
    variables: Optional[dict] = None
    model: str = "gpt-4.1"
    background: bool = False
    log: bool = True  # Default to logging everything
    tags: Optional[List[str]] = None


class ResearchPollRequest(BaseModel):
    response_id: str


@app.get("/")
def root():
    return {"status": "ok", "service": "automations-api", "timestamp": datetime.now().isoformat()}


@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/prompts")
def list_prompts():
    from pathlib import Path
    prompts_dir = Path("/opt/automations/prompts")
    if not prompts_dir.exists():
        return {"prompts": [], "count": 0}
    prompts = []
    for f in prompts_dir.glob("*.md"):
        prompts.append({"name": f.stem, "path": str(f), "size_bytes": f.stat().st_size})
    return {"prompts": prompts, "count": len(prompts)}


@app.post("/test/prompt")
def test_prompt(request: PromptRequest):
    """Test a prompt with full logging to Supabase."""
    from workers.ai import prompt, DEEP_RESEARCH_MODELS

    try:
        is_deep_research = (
            request.model in DEEP_RESEARCH_MODELS or
            request.model.startswith("o4-mini-deep") or
            request.model.startswith("o3-deep")
        )

        if is_deep_research and not request.background:
            return {
                "error": "Deep research models require background=True",
                "hint": "Set background=True, then poll /research/poll with the response_id"
            }

        # Build tags - always include model and prompt name
        tags = request.tags or []
        tags.extend(["api", request.model, request.prompt_name])

        result = prompt(
            name=request.prompt_name,
            variables=request.variables,
            model=request.model,
            background=request.background,
            log=True,  # ALWAYS log - non-negotiable
            tags=list(set(tags)),  # Dedupe tags
        )

        return {
            "status": "submitted" if request.background else "completed",
            "prompt_name": result["prompt_name"],
            "model": result["model"],
            "elapsed_seconds": result.get("elapsed_seconds"),
            "output": result.get("output"),
            "response_id": result.get("response_id"),
            "input_length": len(result.get("input", "")) if result.get("input") else 0,
            "logged": True,
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/research/start")
def start_research(request: PromptRequest):
    """Start deep research in background mode."""
    from workers.ai import prompt

    try:
        if not request.model.startswith("o"):
            request.model = "o4-mini-deep-research"

        tags = request.tags or []
        tags.extend(["api", "research", request.model, request.prompt_name])

        result = prompt(
            name=request.prompt_name,
            variables=request.variables,
            model=request.model,
            background=True,
            log=True,  # ALWAYS log - non-negotiable
            tags=list(set(tags)),
        )

        return {
            "status": "submitted",
            "response_id": result.get("response_id"),
            "model": result["model"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/research/poll")
def poll_research(request: ResearchPollRequest):
    """Poll for deep research completion."""
    from workers.ai import poll_research as poll_fn

    try:
        result = poll_fn(request.response_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/logs")
def get_logs(limit: int = 20, status: Optional[str] = None, prompt_name: Optional[str] = None):
    """View recent execution logs."""
    from supabase import create_client

    supabase = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    )

    query = supabase.table("execution_logs").select("*").order("started_at", desc=True).limit(limit)

    if status:
        query = query.eq("status", status)
    if prompt_name:
        query = query.ilike("worker_name", f"%{prompt_name}%")

    result = query.execute()

    return {
        "logs": result.data,
        "count": len(result.data)
    }


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


@app.get("/workers")
def list_workers():
    return {
        "workers": [
            {
                "name": "research.entity_research",
                "description": "Deep research on a company using o4-mini-deep-research",
                "params": ["client_info", "target_info"]
            }
        ]
    }


# =============================================================================
# AUTOMATION REGISTRY ENDPOINTS
# =============================================================================

class AutomationRegister(BaseModel):
    slug: str
    name: str
    type: str  # research, scraper, enrichment, workflow
    category: Optional[str] = None
    description: Optional[str] = None
    worker_path: Optional[str] = None
    tags: Optional[List[str]] = None
    status: str = "active"


@app.post("/automations/register")
def register_automation_endpoint(request: AutomationRegister):
    """Register a new automation in the registry."""
    from workers.register import register_automation

    try:
        # Only pass status if explicitly set (not the default)
        status = request.status if request.status != "active" else None
        result = register_automation(
            slug=request.slug,
            name=request.name,
            type=request.type,
            category=request.category,
            description=request.description,
            worker_path=request.worker_path,
            tags=request.tags,
            status=status,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/automations/{slug}/status")
def check_automation_status(slug: str):
    """Check if an automation is registered and get its status."""
    from workers.register import check_registration
    return check_registration(slug)


@app.get("/automations")
def list_automations_endpoint(
    type: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None
):
    """List all automations with optional filters."""
    from workers.register import list_automations
    automations = list_automations(type=type, status=status, category=category)
    return {"automations": automations, "count": len(automations)}
