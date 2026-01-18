"""
Logging endpoints for Make.com integration
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import os
from supabase import create_client

router = APIRouter()


def get_supabase():
    """Get Supabase client"""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    return create_client(url, key)


class StepLogRequest(BaseModel):
    """Request body for logging a step execution"""
    step_name: str
    prompt_id: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    model: Optional[str] = None
    runtime_seconds: Optional[float] = None
    status: str = "success"  # success, failed
    error_message: Optional[str] = None
    run_id: Optional[str] = None  # Make.com execution ID or custom identifier
    tags: Optional[list[str]] = None


@router.post("/v2/logs/step")
def log_step(request: StepLogRequest):
    """
    Log a step execution from Make.com.
    Stores in execution_logs table for full traceability.
    """
    supabase = get_supabase()
    
    # Build log entry
    log_entry = {
        "worker_name": f"makecom.{request.step_name}",
        "automation_slug": request.prompt_id or request.step_name,
        "input": request.input_data or {},
        "output": request.output_data or {},
        "status": request.status,
        "runtime_seconds": request.runtime_seconds,
        "tags": request.tags or ["makecom", request.step_name],
        "started_at": datetime.utcnow().isoformat(),
    }
    
    if request.status == "failed":
        log_entry["error_message"] = request.error_message
    
    if request.model:
        log_entry["tags"].append(request.model)
    
    # Insert into execution_logs table
    result = supabase.table("execution_logs").insert(log_entry).execute()
    
    return {
        "log_id": result.data[0]["id"],
        "status": "logged",
        "step_name": request.step_name,
    }


@router.get("/v2/logs/run/{run_id}")
def get_run_logs(run_id: str, limit: int = 100):
    """
    Get all logs for a Make.com run.
    Uses automation_slug or tags to filter by run_id.
    """
    supabase = get_supabase()
    
    # Query logs by run_id (could be in tags or automation_slug)
    # For now, match automation_slug (Make.com can pass run_id as automation_slug)
    # Tags matching would require post-processing
    query = supabase.table("execution_logs").select("*")
    query = query.eq("automation_slug", run_id)
    query = query.order("started_at", desc=False).limit(limit)
    
    result = query.execute()
    
    return {
        "run_id": run_id,
        "logs": result.data,
        "count": len(result.data),
    }


@router.get("/v2/logs/step/{step_name}")
def get_step_logs(step_name: str, limit: int = 50):
    """
    Get recent logs for a specific step.
    """
    supabase = get_supabase()
    
    query = supabase.table("execution_logs").select("*")
    query = query.ilike("worker_name", f"%{step_name}%")
    query = query.order("started_at", desc=True).limit(limit)
    
    result = query.execute()
    
    return {
        "step_name": step_name,
        "logs": result.data,
        "count": len(result.data),
    }

