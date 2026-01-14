"""
Columnline API Routes

Clean endpoints for Make.com integration.
No nested arrays, no JavaScript parsing - just clean JSON responses.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime

from .repository import ColumnlineRepository
from .models import (
    RunStartRequest, RunStartResponse,
    RunCreate, RunUpdate, RunStatus,
    PipelineStepCreate, PipelineStepUpdate, PipelineStepComplete,
    ClaimsCreate,
    ConfigsResponse, ClientConfig, PromptConfig,
    OutputsResponse, StepOutput,
    SuccessResponse
)

router = APIRouter(prefix="/columnline", tags=["columnline"])
repo = ColumnlineRepository()


# ============================================================================
# CONFIG ENDPOINTS (for sub-scenarios)
# ============================================================================

@router.get("/configs/{client_id}", response_model=ConfigsResponse)
async def get_configs(client_id: str):
    """
    Fetch client config + all prompts in one call

    Make.com usage:
        [1] HTTP GET /columnline/configs/{{client_id}}
        [2] Set Variables (NO JavaScript!)
            client_name = {{1.client.name}}
            icp_config = {{1.client.icp_config_compressed}}
            search_builder_prompt = {{1.prompts[0].template}}
    """
    client = repo.get_client(client_id)
    if not client:
        raise HTTPException(status_code=404, detail=f"Client not found: {client_id}")

    prompts = repo.get_all_prompts()

    return ConfigsResponse(
        client=ClientConfig(**client),
        prompts=[PromptConfig(**p) for p in prompts]
    )


@router.get("/prompts/{slug}", response_model=PromptConfig)
async def get_prompt(slug: str):
    """Get specific prompt by slug"""
    prompt = repo.get_prompt_by_slug(slug)
    if not prompt:
        raise HTTPException(status_code=404, detail=f"Prompt not found: {slug}")

    return PromptConfig(**prompt)


# ============================================================================
# OUTPUTS ENDPOINTS (for steps that need context)
# ============================================================================

@router.get("/outputs/{run_id}", response_model=OutputsResponse)
async def get_outputs(
    run_id: str,
    steps: Optional[str] = Query(None, description="Comma-separated step names")
):
    """
    Get completed step outputs for a run

    Make.com usage:
        [1] HTTP GET /columnline/outputs/{{run_id}}?steps=1_SEARCH_BUILDER
        [2] Set Variable
            search_queries = {{1.outputs.1_SEARCH_BUILDER.output.queries}}
    """
    step_names = steps.split(',') if steps else None
    outputs = repo.get_completed_outputs(run_id, step_names)

    # Convert to StepOutput models
    step_outputs = {}
    for name, data in outputs.items():
        step_outputs[name] = StepOutput(**data)

    return OutputsResponse(
        run_id=run_id,
        outputs=step_outputs
    )


# ============================================================================
# RUN MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/runs/start", response_model=RunStartResponse)
async def start_run(request: RunStartRequest):
    """
    Start a new dossier run - MAIN PIPELINE ENTRY POINT

    Make.com usage:
        [1] Webhook receives: {client_id, seed}
        [2] HTTP POST /columnline/runs/start
            Body: {
                "client_id": "CLT_EXAMPLE_001",
                "seed_data": {
                    "company_name": "Acme Construction",
                    "signal": "Permit filed for $5M expansion"
                },
                "triggered_by": "make.com"
            }
        [3] Response:
            {
                "run_id": "RUN_20260113_143022",
                "dossier_id": "DOSS_20260113_9472",
                "client_id": "CLT_EXAMPLE_001",
                "started_at": "2026-01-13T14:30:22Z"
            }
        [4] Use {{1.run_id}} and {{1.dossier_id}} for tracking
    """
    from datetime import datetime
    import random

    # Generate IDs
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"RUN_{timestamp}"
    dossier_id = f"DOSS_{datetime.now().strftime('%Y%m%d')}_{random.randint(1000, 9999)}"

    # Verify client exists
    client = repo.get_client(request.client_id)
    if not client:
        raise HTTPException(status_code=404, detail=f"Client not found: {request.client_id}")

    # Create run
    run_data = {
        "run_id": run_id,
        "client_id": request.client_id,
        "status": "running",
        "seed_data": request.seed_data,
        "dossier_id": dossier_id,
        "triggered_by": request.triggered_by,
        "config_snapshot": None  # Could snapshot client config here
    }

    result = repo.create_run(run_data)

    return RunStartResponse(
        success=True,
        run_id=run_id,
        dossier_id=dossier_id,
        client_id=request.client_id,
        started_at=result['started_at'],
        message="Run started successfully"
    )


@router.post("/runs", response_model=SuccessResponse)
async def create_run(run: RunCreate):
    """
    Create a new run

    Make.com usage (main pipeline):
        [1] Generate IDs
            run_id = RUN_{{formatDate(now)}}
            dossier_id = DOSS_{{formatDate(now)}}_{{random}}
        [2] HTTP POST /columnline/runs
            Body: {run_id, client_id, status: "running", seed}
    """
    result = repo.create_run(run.dict())

    return SuccessResponse(
        success=True,
        message="Run created",
        data={"run_id": result['run_id']}
    )


@router.put("/runs/{run_id}", response_model=SuccessResponse)
async def update_run(run_id: str, updates: RunUpdate):
    """
    Update run status

    Make.com usage:
        HTTP PUT /columnline/runs/{{run_id}}
        Body: {status: "completed", completed_at: {{now}}}
    """
    result = repo.update_run(run_id, updates.dict(exclude_unset=True))

    return SuccessResponse(
        success=True,
        message="Run updated",
        data={"run_id": result['run_id']}
    )


@router.get("/runs/{run_id}/status", response_model=RunStatus)
async def get_run_status(run_id: str):
    """
    Get run status with completed steps

    Make.com usage (main pipeline polling):
        [1] Repeater
        [2] Sleep 10s
        [3] HTTP GET /columnline/runs/{{run_id}}/status
        [4] Router: If status = "completed" → Continue
    """
    status = repo.get_run_status(run_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    return RunStatus(**status)


# ============================================================================
# PIPELINE STEP ENDPOINTS (Logging & Polling)
# ============================================================================

@router.post("/pipeline_steps", response_model=SuccessResponse)
async def log_pipeline_step(step: PipelineStepCreate):
    """
    Log a pipeline step execution (dual-write pattern)

    Make.com usage (sub-scenario):
        [1] Log "running" status
            POST /columnline/pipeline_steps
            Body: {
                step_id: "STEP_{{run_id}}_01",
                run_id: {{run_id}},
                prompt_id: "PRM_001",
                step_name: "1_SEARCH_BUILDER",
                status: "running",
                input: {{input_json}},
                started_at: {{now}}
            }

        [2] Call LLM

        [3] Update to "completed"
            PUT /columnline/pipeline_steps/{{step_id}}
            Body: {
                status: "completed",
                output: {{llm_response}},
                tokens_used: {{tokens}},
                runtime_seconds: {{runtime}},
                completed_at: {{now}}
            }
    """
    result = repo.create_pipeline_step(step.dict(exclude_unset=True))

    return SuccessResponse(
        success=True,
        message="Pipeline step logged",
        data={"step_id": result['step_id']}
    )


@router.put("/pipeline_steps/{step_id}", response_model=SuccessResponse)
async def update_pipeline_step(step_id: str, updates: PipelineStepUpdate):
    """
    Update pipeline step (for dual-write pattern)

    See log_pipeline_step for usage example
    """
    result = repo.update_pipeline_step(step_id, updates.dict(exclude_unset=True))

    return SuccessResponse(
        success=True,
        message="Pipeline step updated",
        data={"step_id": result['step_id']}
    )


@router.get("/pipeline_steps/{run_id}/completed", response_model=PipelineStepComplete)
async def check_step_completed(
    run_id: str,
    step_name: str = Query(..., description="Step name to check (e.g., 1_SEARCH_BUILDER)")
):
    """
    Check if specific step completed (for polling)

    Make.com usage (main pipeline):
        [1] Call sub-scenario
        [2] Repeater (max 100)
        [3] Sleep 10s
        [4] HTTP GET /columnline/pipeline_steps/{{run_id}}/completed?step_name=1_SEARCH_BUILDER
        [5] Router
            - If {{4.found}} = true → Continue
            - Else → Back to [2]
    """
    step = repo.get_completed_step(run_id, step_name)

    if step:
        return PipelineStepComplete(found=True, step=step)
    else:
        return PipelineStepComplete(found=False)


# ============================================================================
# CLAIMS ENDPOINTS
# ============================================================================

@router.post("/claims", response_model=SuccessResponse)
async def store_claims(claims: ClaimsCreate):
    """
    Store claims from a research step

    Make.com usage (sub-scenario - if produce_claims = true):
        [1] Parse LLM response for claims
        [2] HTTP POST /columnline/claims
            Body: {
                run_id: {{run_id}},
                step_id: {{step_id}},
                step_name: "3_ENTITY_RESEARCH",
                claims_json: {{parsed_claims}}
            }
    """
    result = repo.create_claims(claims.dict())

    return SuccessResponse(
        success=True,
        message="Claims stored",
        data={
            "run_id": result['run_id'],
            "step_id": result['step_id']
        }
    )


@router.get("/claims/{run_id}")
async def get_claims(run_id: str):
    """Get all claims for a run"""
    claims = repo.get_claims(run_id)

    return {
        "run_id": run_id,
        "claims": claims,
        "count": len(claims)
    }


# ============================================================================
# SECTION ENDPOINTS
# ============================================================================

@router.post("/sections", response_model=SuccessResponse)
async def create_section(section_data: dict):
    """
    Store a dossier section

    Make.com usage (section writer):
        HTTP POST /columnline/sections
        Body: {
            section_id: "SEC_{{run_id}}_INTRO",
            run_id: {{run_id}},
            section_name: "INTRO",
            section_data: {{section_content}},
            produced_by_step: "8A_INTRO_WRITER"
        }
    """
    result = repo.create_section(section_data)

    return SuccessResponse(
        success=True,
        message="Section stored",
        data={"section_id": result['section_id']}
    )


@router.get("/sections/{run_id}")
async def get_sections(run_id: str):
    """Get all sections for a run"""
    sections = repo.get_sections(run_id)

    return {
        "run_id": run_id,
        "sections": sections,
        "count": len(sections)
    }


# ============================================================================
# DOSSIER ENDPOINTS
# ============================================================================

@router.post("/dossiers", response_model=SuccessResponse)
async def create_dossier(dossier_data: dict):
    """
    Create a dossier

    Make.com usage (dossier assembly):
        HTTP POST /columnline/dossiers
        Body: {
            dossier_id: {{dossier_id}},
            run_id: {{run_id}},
            client_id: {{client_id}},
            company_name: {{company_name}},
            lead_score: {{score}},
            ...
        }
    """
    result = repo.create_dossier(dossier_data)

    return SuccessResponse(
        success=True,
        message="Dossier created",
        data={"dossier_id": result['dossier_id']}
    )


@router.put("/dossiers/{dossier_id}", response_model=SuccessResponse)
async def update_dossier(dossier_id: str, updates: dict):
    """Update dossier"""
    result = repo.update_dossier(dossier_id, updates)

    return SuccessResponse(
        success=True,
        message="Dossier updated",
        data={"dossier_id": result['dossier_id']}
    )


@router.get("/dossiers/{dossier_id}")
async def get_dossier(dossier_id: str):
    """Get dossier by ID"""
    dossier = repo.get_dossier(dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail=f"Dossier not found: {dossier_id}")

    return dossier


# ============================================================================
# CONTACT ENDPOINTS
# ============================================================================

@router.post("/contacts", response_model=SuccessResponse)
async def create_contact(contact_data: dict):
    """
    Store a discovered contact

    Make.com usage (contact discovery):
        HTTP POST /columnline/contacts
        Body: {contact fields}
    """
    result = repo.create_contact(contact_data)

    return SuccessResponse(
        success=True,
        message="Contact stored",
        data={"contact_id": result['id']}
    )


@router.get("/contacts/{run_id}")
async def get_contacts(run_id: str):
    """Get all contacts for a run"""
    contacts = repo.get_contacts(run_id)

    return {
        "run_id": run_id,
        "contacts": contacts,
        "count": len(contacts)
    }


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "columnline-api",
        "timestamp": datetime.utcnow().isoformat()
    }
