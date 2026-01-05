"""
Automations API
===============
Submit jobs, check status, stream progress updates.
"""

import os
import json
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from redis import Redis
from rq import Queue
from rq.job import Job
from rq.registry import StartedJobRegistry, FinishedJobRegistry, FailedJobRegistry

import asyncio

# Import registry router
from api.registry import router as registry_router

# Redis connection
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
redis_conn = Redis.from_url(REDIS_URL)
queue = Queue(connection=redis_conn)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    print(f"🚀 Automations API starting...")
    print(f"📡 Redis: {REDIS_URL[:30]}...")
    yield
    print("👋 Shutting down...")


app = FastAPI(
    title="Automations API",
    description="Queue and monitor automation jobs",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include registry router
app.include_router(registry_router)


# =============================================================================
# Models
# =============================================================================

class JobSubmit(BaseModel):
    """Submit a job to the queue."""
    worker: str  # e.g., "research.entity_research"
    params: dict = {}
    timeout: int = 900  # 15 min default


class JobResponse(BaseModel):
    job_id: str
    status: str
    worker: str
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    result: Optional[dict] = None
    error: Optional[str] = None
    progress: Optional[dict] = None


class PromptTest(BaseModel):
    """Test a prompt with variables."""
    prompt_name: str
    variables: dict = {}
    model: str = "gpt-4.1"


# =============================================================================
# Endpoints
# =============================================================================

@app.get("/")
def root():
    """Health check."""
    return {
        "status": "ok",
        "service": "automations-api",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/test/prompt")
def test_prompt(request: PromptTest):
    """
    Test a prompt synchronously (for quick models like gpt-4.1).
    For deep-research models, use /jobs endpoint instead.
    """
    from workers.ai import prompt
    
    try:
        result = prompt(
            name=request.prompt_name,
            variables=request.variables,
            model=request.model,
        )
        return {
            "status": "success",
            "prompt_name": result["prompt_name"],
            "model": result["model"],
            "elapsed_seconds": result["elapsed_seconds"],
            "output": result["output"],
            "input_length": len(result["input"]),
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/prompts")
def list_prompts():
    """List available prompts."""
    from pathlib import Path
    prompts_dir = Path(__file__).parent.parent / "prompts"
    
    if not prompts_dir.exists():
        return {"prompts": [], "error": "Prompts directory not found"}
    
    prompts = []
    for f in prompts_dir.glob("*.md"):
        prompts.append({
            "name": f.stem,
            "path": str(f),
            "size_bytes": f.stat().st_size,
        })
    
    return {"prompts": prompts, "count": len(prompts)}


@app.get("/workers")
def list_workers():
    """List all available workers."""
    workers = []
    
    try:
        from workers.research import entity_research
        workers.append({
            "name": "research.entity_research",
            "description": "Deep research on a company using o4-mini-deep-research",
            "params": ["client_info", "target_info"]
        })
    except ImportError:
        pass
    
    return {"workers": workers}


@app.post("/jobs", response_model=JobResponse)
def submit_job(job: JobSubmit):
    """Submit a new job to the queue."""
    
    worker_map = {}
    
    try:
        from workers.research.entity_research import run_entity_research
        worker_map["research.entity_research"] = run_entity_research
    except ImportError as e:
        print(f"Could not import entity_research: {e}")
    
    if job.worker not in worker_map:
        raise HTTPException(
            status_code=400, 
            detail=f"Unknown worker: {job.worker}. Available: {list(worker_map.keys())}"
        )
    
    rq_job = queue.enqueue(
        worker_map[job.worker],
        kwargs=job.params,
        job_timeout=job.timeout,
        result_ttl=86400,
        failure_ttl=86400
    )
    
    return JobResponse(
        job_id=rq_job.id,
        status=rq_job.get_status(),
        worker=job.worker,
        created_at=datetime.utcnow().isoformat()
    )


@app.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str):
    """Get job status and result."""
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")
    
    response = JobResponse(
        job_id=job.id,
        status=job.get_status(),
        worker=job.func_name or "unknown",
        created_at=job.created_at.isoformat() if job.created_at else None,
        started_at=job.started_at.isoformat() if job.started_at else None,
        ended_at=job.ended_at.isoformat() if job.ended_at else None
    )
    
    if job.get_status() == "finished":
        response.result = job.result
    
    if job.get_status() == "failed":
        response.error = str(job.exc_info) if job.exc_info else "Unknown error"
    
    if job.meta:
        response.progress = job.meta
    
    return response


@app.get("/jobs/{job_id}/stream")
async def stream_job(job_id: str):
    """Stream job progress via Server-Sent Events."""
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")
    
    async def event_generator():
        last_meta = None
        
        while True:
            try:
                job.refresh()
                status = job.get_status()
                
                if job.meta != last_meta:
                    last_meta = job.meta.copy() if job.meta else {}
                    yield f"data: {json.dumps({'type': 'progress', 'status': status, 'meta': last_meta})}\n\n"
                
                if status == "finished":
                    yield f"data: {json.dumps({'type': 'complete', 'result': job.result})}\n\n"
                    break
                
                if status == "failed":
                    yield f"data: {json.dumps({'type': 'error', 'error': str(job.exc_info)})}\n\n"
                    break
                
                await asyncio.sleep(1)
                
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
                break
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


@app.get("/jobs")
def list_jobs(
    status: Optional[str] = Query(None),
    limit: int = Query(50)
):
    """List recent jobs."""
    jobs = []
    
    if status is None or status == "queued":
        for job_id in queue.job_ids[:limit]:
            try:
                job = Job.fetch(job_id, connection=redis_conn)
                jobs.append({
                    "job_id": job.id,
                    "status": job.get_status(),
                    "worker": job.func_name,
                    "created_at": job.created_at.isoformat() if job.created_at else None
                })
            except:
                pass
    
    if status is None or status == "finished":
        finished = FinishedJobRegistry(queue=queue)
        for job_id in finished.get_job_ids()[:limit]:
            try:
                job = Job.fetch(job_id, connection=redis_conn)
                jobs.append({
                    "job_id": job.id,
                    "status": "finished",
                    "worker": job.func_name,
                    "ended_at": job.ended_at.isoformat() if job.ended_at else None
                })
            except:
                pass
    
    if status is None or status == "failed":
        failed = FailedJobRegistry(queue=queue)
        for job_id in failed.get_job_ids()[:limit]:
            try:
                job = Job.fetch(job_id, connection=redis_conn)
                jobs.append({
                    "job_id": job.id,
                    "status": "failed",
                    "worker": job.func_name,
                    "error": str(job.exc_info)[:200] if job.exc_info else None
                })
            except:
                pass
    
    return {"jobs": jobs[:limit], "count": len(jobs)}


@app.delete("/jobs/{job_id}")
def cancel_job(job_id: str):
    """Cancel a queued job."""
    try:
        job = Job.fetch(job_id, connection=redis_conn)
        job.cancel()
        return {"status": "cancelled", "job_id": job_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class RunAutomation(BaseModel):
    slug: str
    override_config: Optional[dict] = None


@app.post("/run")
def run_automation_endpoint(request: RunAutomation):
    """Run an automation from the registry."""
    from workers.runner import run_automation
    
    rq_job = queue.enqueue(
        run_automation,
        kwargs={
            "slug": request.slug,
            "override_config": request.override_config
        },
        job_timeout=900,
        result_ttl=86400
    )
    
    return {
        "job_id": rq_job.id,
        "status": rq_job.get_status(),
        "automation": request.slug
    }
