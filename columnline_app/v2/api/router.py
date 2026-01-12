"""
v2 API Router - Complete API for Columnline v2 pipeline
"""
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from ..db.repository import V2Repository
from ..db.models import (
    ClientConfig, PromptConfig, PromptVersion,
    PipelineRun, PipelineStatus, StepRun, StepStatus,
    StartPipelineRequest, PipelineRunResponse, StepRunResponse,
    Claim, Contact, Dossier
)
from ..config import PIPELINE_STEPS, STAGE_ORDER, Stage
from ..pipeline.runner import PipelineRunner, run_pipeline


router = APIRouter(prefix="/v2", tags=["v2"])


def get_repo() -> V2Repository:
    return V2Repository()


# ---------- Clients ----------

@router.get("/clients")
async def list_clients(status: Optional[str] = "active"):
    """List all clients"""
    repo = get_repo()
    clients = repo.get_clients(status)
    return {"clients": [c.model_dump() for c in clients]}


@router.get("/clients/{client_id}")
async def get_client(client_id: str):
    """Get client by ID"""
    repo = get_repo()
    client = repo.get_client(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client.model_dump()


@router.post("/clients")
async def create_client(client: ClientConfig):
    """Create a new client"""
    repo = get_repo()
    created = repo.create_client(client)
    return created.model_dump()


@router.put("/clients/{client_id}")
async def update_client(client_id: str, updates: Dict[str, Any]):
    """Update client configuration"""
    repo = get_repo()
    updated = repo.update_client(client_id, updates)
    return updated.model_dump()


# ---------- Prompts ----------

class CreatePromptRequest(BaseModel):
    prompt_id: str
    name: str
    content: Optional[str] = None
    description: Optional[str] = None


@router.post("/prompts")
async def create_prompt(request: CreatePromptRequest):
    """Create a new prompt with optional initial content"""
    repo = get_repo()

    # Check if prompt already exists
    existing = repo.get_prompt(request.prompt_id)
    if existing:
        raise HTTPException(status_code=400, detail=f"Prompt {request.prompt_id} already exists")

    # Try to load content from file if not provided
    content = request.content
    if not content:
        prompt_file = f"prompts/v2/{request.prompt_id}.md"
        if os.path.exists(prompt_file):
            with open(prompt_file, "r") as f:
                content = f.read()
        else:
            content = f"# {request.name}\n\nPrompt content here..."

    # Insert into v2_prompts table
    prompt_data = {
        "prompt_id": request.prompt_id,
        "name": request.name,
        "description": request.description,
        "current_version": 1,
        "is_active": True,
    }
    result = repo.client.table("v2_prompts").insert(prompt_data).execute()

    # Create initial version
    version_data = {
        "prompt_id": request.prompt_id,
        "version_number": 1,
        "content": content,
        "change_notes": "Initial version",
        "created_by": "api",
    }
    repo.client.table("v2_prompt_versions").insert(version_data).execute()

    return {
        "prompt_id": request.prompt_id,
        "message": "Prompt created successfully",
        "content_loaded_from_file": request.content is None
    }


@router.get("/prompts")
async def list_prompts(is_active: bool = True):
    """List all prompts with metadata"""
    repo = get_repo()
    prompts = repo.get_prompts(is_active)

    # Enhance with step config info
    result = []
    for p in prompts:
        data = p.model_dump()
        step_config = PIPELINE_STEPS.get(p.prompt_id)
        if step_config:
            data["execution_mode"] = step_config.execution_mode.value
            data["parallel_group"] = step_config.parallel_group
        result.append(data)

    return {"prompts": result}


@router.get("/prompts/{prompt_id}")
async def get_prompt(prompt_id: str):
    """Get prompt with current content"""
    repo = get_repo()
    prompt = repo.get_prompt_with_content(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt.model_dump()


@router.put("/prompts/{prompt_id}")
async def update_prompt(
    prompt_id: str,
    content: str,
    change_notes: Optional[str] = None
):
    """
    Update prompt content (creates new version).
    Also updates the prompt file on disk.
    """
    repo = get_repo()

    # Get current prompt
    prompt = repo.get_prompt(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")

    # Create new version
    new_version = prompt.current_version + 1
    version = repo.create_prompt_version(PromptVersion(
        prompt_id=prompt_id,
        version_number=new_version,
        content=content,
        change_notes=change_notes,
        created_by="dashboard",
    ))

    # Update file on disk
    prompt_file = f"prompts/v2/{prompt_id}.md"
    os.makedirs(os.path.dirname(prompt_file), exist_ok=True)
    with open(prompt_file, "w") as f:
        f.write(content)

    return {
        "prompt_id": prompt_id,
        "version": new_version,
        "message": "Prompt updated successfully"
    }


@router.get("/prompts/{prompt_id}/versions")
async def list_prompt_versions(prompt_id: str):
    """List all versions of a prompt"""
    repo = get_repo()
    versions = repo.get_prompt_versions(prompt_id)
    return {"versions": [v.model_dump() for v in versions]}


class TestPromptRequest(BaseModel):
    variables: Dict[str, Any] = {}
    model: Optional[str] = None


@router.post("/prompts/{prompt_id}/test")
async def test_prompt(prompt_id: str, request: TestPromptRequest):
    """
    Test a prompt in isolation.
    Creates a test pipeline run and executes just this step.
    """
    repo = get_repo()

    # Get a test client
    clients = repo.get_clients("active")
    if not clients:
        raise HTTPException(status_code=400, detail="No active clients found")
    client = clients[0]

    # Create a test pipeline run
    pipeline_run = repo.create_pipeline_run(PipelineRun(
        client_id=client.id,
        seed=request.variables,
        status=PipelineStatus.RUNNING,
        config={"test_mode": True},
        started_at=datetime.utcnow(),
    ))

    try:
        runner = PipelineRunner(repo)
        result = await runner.run_single_step(
            pipeline_run.id,
            prompt_id,
            request.variables
        )

        # Mark as complete
        repo.update_pipeline_run(pipeline_run.id, {
            "status": PipelineStatus.COMPLETED.value,
            "completed_at": datetime.utcnow().isoformat(),
        })

        return result

    except Exception as e:
        repo.update_pipeline_run(pipeline_run.id, {
            "status": PipelineStatus.FAILED.value,
            "error_message": str(e),
            "completed_at": datetime.utcnow().isoformat(),
        })
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prompts/{prompt_id}/last-run")
async def get_prompt_last_run(prompt_id: str, client_id: Optional[str] = None):
    """Get the last run for a prompt (for viewing I/O in dashboard)"""
    repo = get_repo()

    last_runs = repo.get_prompt_last_runs(client_id)
    for run in last_runs:
        if run.get("prompt_id") == prompt_id:
            return run

    return {"message": "No runs found for this prompt"}


# ---------- Pipeline ----------

@router.post("/pipeline/start")
async def start_pipeline(request: StartPipelineRequest, background_tasks: BackgroundTasks):
    """
    Start a new pipeline run.
    Returns immediately with run ID; pipeline executes in background.
    """
    repo = get_repo()

    # Verify client exists
    client = repo.get_client(request.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    # Create pipeline run
    pipeline_run = repo.create_pipeline_run(PipelineRun(
        client_id=request.client_id,
        seed=request.seed,
        config=request.config,
        status=PipelineStatus.PENDING,
    ))

    # Run in background using sync wrapper
    def run_in_background():
        try:
            runner = PipelineRunner()
            import asyncio
            asyncio.run(runner.run_pipeline_with_id(
                pipeline_run.id,
                request.client_id,
                request.seed,
                request.config
            ))
        except Exception as e:
            import traceback
            print(f"Pipeline failed: {e}")
            print(traceback.format_exc())
            # Update run to failed status
            repo.update_pipeline_run(pipeline_run.id, {
                "status": PipelineStatus.FAILED.value,
                "error_message": str(e),
                "completed_at": datetime.utcnow().isoformat(),
            })

    background_tasks.add_task(run_in_background)

    return {
        "id": pipeline_run.id,
        "status": pipeline_run.status.value,
        "message": "Pipeline started"
    }


@router.get("/pipeline/runs")
async def list_pipeline_runs(
    client_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
):
    """List pipeline runs with optional filters"""
    repo = get_repo()
    status_enum = PipelineStatus(status) if status else None
    runs = repo.get_pipeline_runs(client_id, status_enum, limit)

    # Enhance with client names
    result = []
    for run in runs:
        data = run.model_dump()
        if run.client_id:
            client = repo.get_client(run.client_id)
            data["client_name"] = client.name if client else None
        result.append(data)

    return {"runs": result}


@router.get("/pipeline/runs/{run_id}")
async def get_pipeline_run(run_id: str):
    """Get pipeline run with all steps"""
    repo = get_repo()

    run = repo.get_pipeline_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")

    # Get steps
    steps = repo.get_step_runs(run_id)

    # Get client
    client = repo.get_client(run.client_id) if run.client_id else None

    # Calculate totals
    total_tokens_in = sum(s.tokens_in or 0 for s in steps)
    total_tokens_out = sum(s.tokens_out or 0 for s in steps)

    return {
        "run": run.model_dump(),
        "client": client.model_dump() if client else None,
        "steps": [s.model_dump() for s in steps],
        "total_tokens_in": total_tokens_in,
        "total_tokens_out": total_tokens_out,
        "total_steps": len(PIPELINE_STEPS),
    }


@router.get("/pipeline/runs/{run_id}/live")
async def get_pipeline_run_live(run_id: str):
    """
    Get current state of pipeline run (for polling).
    Lightweight endpoint for real-time dashboard updates.
    """
    repo = get_repo()

    run = repo.get_pipeline_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")

    steps = repo.get_step_runs(run_id)

    return {
        "id": run.id,
        "status": run.status.value if hasattr(run.status, 'value') else run.status,
        "current_step": run.current_step,
        "steps_completed": run.steps_completed,
        "total_steps": len(PIPELINE_STEPS),
        "steps": [
            {
                "step": s.step,
                "status": s.status.value if hasattr(s.status, 'value') else s.status,
                "duration_ms": s.duration_ms,
                "started_at": s.started_at.isoformat() if s.started_at else None,
            }
            for s in steps
        ],
        "error_message": run.error_message,
    }


@router.post("/pipeline/runs/{run_id}/cancel")
async def cancel_pipeline_run(run_id: str):
    """Cancel a running pipeline"""
    repo = get_repo()

    run = repo.get_pipeline_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")

    if run.status not in [PipelineStatus.PENDING, PipelineStatus.RUNNING]:
        raise HTTPException(status_code=400, detail="Cannot cancel completed/failed run")

    repo.update_pipeline_run(run_id, {
        "status": PipelineStatus.CANCELLED.value,
        "completed_at": datetime.utcnow().isoformat(),
    })

    return {"message": "Pipeline cancelled"}


# ---------- Steps ----------

@router.get("/pipeline/runs/{run_id}/steps")
async def list_step_runs(run_id: str):
    """Get all steps for a pipeline run"""
    repo = get_repo()
    steps = repo.get_step_runs(run_id)
    return {"steps": [s.model_dump() for s in steps]}


@router.get("/pipeline/runs/{run_id}/steps/{step_id}")
async def get_step_run(run_id: str, step_id: str):
    """Get detailed step run info"""
    repo = get_repo()
    step = repo.get_step_run_by_step(run_id, step_id)
    if not step:
        raise HTTPException(status_code=404, detail="Step run not found")
    return step.model_dump()


class RerunStepRequest(BaseModel):
    """Request to re-run a step with optional variable overrides"""
    variable_overrides: Dict[str, Any] = {}


@router.post("/pipeline/runs/{run_id}/steps/{step_id}/rerun")
async def rerun_step(run_id: str, step_id: str, request: RerunStepRequest):
    """
    Re-run a specific step with its stored input (or with overrides).
    Creates a new step_run record with fresh execution.
    """
    repo = get_repo()

    # Get the original step run
    original_step = repo.get_step_run_by_step(run_id, step_id)
    if not original_step:
        raise HTTPException(status_code=404, detail="Step run not found")

    # Get the pipeline run
    pipeline_run = repo.get_pipeline_run(run_id)
    if not pipeline_run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")

    # Get input variables from original step
    input_vars = original_step.input_variables or {}

    # Merge with overrides
    final_vars = {**input_vars, **request.variable_overrides}

    try:
        runner = PipelineRunner(repo)
        result = await runner.run_single_step(
            run_id,
            step_id,
            final_vars
        )
        return {
            "status": "completed",
            "step_run_id": result.get("step_run_id"),
            "output": result.get("output"),
            "claims_count": result.get("claims_count", 0),
            "duration_ms": result.get("duration_ms"),
        }
    except Exception as e:
        import traceback
        raise HTTPException(status_code=500, detail=str(e))


# ---------- Claims ----------

@router.get("/claims/runs/{run_id}")
async def get_run_claims(run_id: str, merged: Optional[bool] = None):
    """Get claims for a pipeline run"""
    repo = get_repo()

    if merged is None:
        # Return both raw and merged
        raw_claims = repo.get_claims(run_id, is_merged=False)
        merged_claims = repo.get_claims(run_id, is_merged=True)
        return {
            "raw_claims": [c.model_dump() for c in raw_claims],
            "merged_claims": [c.model_dump() for c in merged_claims],
        }
    elif merged:
        claims = repo.get_claims(run_id, is_merged=True)
        return {"claims": [c.model_dump() for c in claims]}
    else:
        claims = repo.get_claims(run_id, is_merged=False)
        return {"claims": [c.model_dump() for c in claims]}


@router.get("/claims/runs/{run_id}/summary")
async def get_claims_summary(run_id: str):
    """Get claims summary by type"""
    repo = get_repo()
    summary = repo.get_claims_summary(run_id)
    return {"summary": summary}


# ---------- Dossiers ----------

@router.get("/dossiers/{dossier_id}")
async def get_dossier(dossier_id: str):
    """Get dossier with sections and contacts"""
    repo = get_repo()

    dossier = repo.get_dossier(dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier not found")

    sections = repo.get_dossier_sections(dossier_id)
    contacts = repo.get_contacts(dossier_id)

    return {
        "dossier": dossier.model_dump(),
        "sections": [s.model_dump() for s in sections],
        "contacts": [c.model_dump() for c in contacts],
    }


@router.get("/dossiers/pipeline/{run_id}")
async def get_dossier_by_pipeline(run_id: str):
    """Get dossier for a pipeline run"""
    repo = get_repo()

    dossier = repo.get_dossier_by_pipeline(run_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier not found for this run")

    sections = repo.get_dossier_sections(dossier.id)
    contacts = repo.get_contacts(dossier.id)

    return {
        "dossier": dossier.model_dump(),
        "sections": [s.model_dump() for s in sections],
        "contacts": [c.model_dump() for c in contacts],
    }


# ---------- Contacts ----------

@router.get("/contacts/{dossier_id}")
async def get_contacts(dossier_id: str):
    """Get all contacts for a dossier"""
    repo = get_repo()
    contacts = repo.get_contacts(dossier_id)
    return {"contacts": [c.model_dump() for c in contacts]}


# ---------- Config / Meta ----------

@router.get("/config/steps")
async def get_pipeline_config():
    """Get pipeline step configuration"""
    return {
        "steps": {
            k: {
                "prompt_id": v.prompt_id,
                "name": v.name,
                "stage": v.stage.value,
                "step_order": v.step_order,
                "execution_mode": v.execution_mode.value,
                "model": v.model,
                "produces_claims": v.produces_claims,
                "merges_claims": v.merges_claims,
                "produces_context_pack": v.produces_context_pack,
                "parallel_group": v.parallel_group,
            }
            for k, v in PIPELINE_STEPS.items()
        },
        "stages": [s.value for s in STAGE_ORDER],
    }


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }
