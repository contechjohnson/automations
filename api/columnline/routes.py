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
    SuccessResponse,
    StepPrepareRequest, StepPrepareResponse, PreparedStep,
    StepCompleteRequest, StepCompleteResponse, StepOutputItem,
    StepTransitionRequest, StepTransitionResponse
)

router = APIRouter(prefix="/columnline", tags=["columnline"])
repo = ColumnlineRepository()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def parse_openai_response(openai_output):
    """
    Parse OpenAI API response to extract text, tokens, and runtime

    Handles both array format and single response format
    """
    # If it's an array, take first element
    if isinstance(openai_output, list):
        openai_output = openai_output[0]

    # Extract response text
    response_text = None
    if 'result' in openai_output:
        response_text = openai_output['result']
    elif 'output' in openai_output and isinstance(openai_output['output'], list):
        # From output[0].content[0].text
        if openai_output['output'] and 'content' in openai_output['output'][0]:
            content = openai_output['output'][0]['content']
            if content and 'text' in content[0]:
                response_text = content[0]['text']

    # Extract tokens
    tokens_used = 0
    if 'usage' in openai_output:
        usage = openai_output['usage']
        tokens_used = usage.get('total_tokens', 0)
        if tokens_used == 0:
            tokens_used = usage.get('input_tokens', 0) + usage.get('output_tokens', 0)

    # Calculate runtime (completed_at - created_at)
    runtime_seconds = 0
    if 'completed_at' in openai_output and 'created_at' in openai_output:
        # completed_at is unix timestamp, created_at is ISO string
        completed_ts = openai_output['completed_at']
        created_at_str = openai_output['created_at']
        # Parse ISO timestamp to unix
        from datetime import datetime
        created_dt = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
        created_ts = created_dt.timestamp()
        runtime_seconds = completed_ts - created_ts

    return {
        "text": response_text,
        "tokens_used": tokens_used,
        "runtime_seconds": runtime_seconds,
        "full_output": openai_output  # Store full response for debugging
    }


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
        [1] HTTP POST /columnline/runs/start
            Body: {
                "client_id": "CLT_EXAMPLE_001",
                "seed_data": {...any JSON structure...},  // OPTIONAL - can be anything
                "triggered_by": "make.com"
            }
        [2] Response:
            {
                "run_id": "RUN_20260113_143022",
                "dossier_id": "DOSS_20260113_9472",
                "client_id": "CLT_EXAMPLE_001",
                "started_at": "2026-01-13T14:30:22Z"
            }
        [3] Use {{1.run_id}} and {{1.dossier_id}} for tracking

    seed_data is completely flexible:
        - {"company_name": "Acme", "signal": "expansion"}
        - {"linkedin_url": "https://..."}
        - {"whatever": "you want"}
        - null (omit entirely)
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
# BATCH STEP EXECUTION (Prepare + Complete)
# ============================================================================

@router.post("/steps/prepare", response_model=StepPrepareResponse)
async def prepare_steps(request: StepPrepareRequest):
    """
    Prepare inputs for one or more steps - API BUILDS THE INPUTS

    ISOLATED TESTING - Prepare one step at a time:
        [1] Prepare Search Builder:
            POST /columnline/steps/prepare
            Body: {
                "run_id": "RUN_20260114_002901",
                "client_id": "CLT_EXAMPLE_001",
                "dossier_id": "DOSS_20260114_1550",
                "step_names": ["1_SEARCH_BUILDER"]
            }

        [2] Run Search Builder LLM
        [3] POST /steps/complete with output

        [4] Prepare Signal Discovery (auto-fetches Search Builder output):
            POST /columnline/steps/prepare
            Body: {
                "run_id": "RUN_20260114_002901",
                "client_id": "CLT_EXAMPLE_001",
                "dossier_id": "DOSS_20260114_1550",
                "step_names": ["2_SIGNAL_DISCOVERY"]
            }

            Response includes:
            {
                "input": {
                    ...base configs...,
                    "search_builder_output": {...}  <-- AUTO-FETCHED
                }
            }

        [5] Run Signal Discovery LLM
        [6] POST /steps/complete with output

        [7] Prepare Claims Extraction (auto-fetches Signal Discovery output):
            POST /columnline/steps/prepare
            Body: {
                "step_names": ["PRODUCE_CLAIMS"]
            }

            Response includes signal_discovery_output in input

    AUTO-FETCH LOGIC:
    - Signal Discovery gets search_builder_output automatically
    - Claims steps get signal_discovery_output automatically
    - API fetches completed previous steps you need

    BATCHED (if you want to skip isolated testing):
        step_names: ["1_SEARCH_BUILDER", "2_SIGNAL_DISCOVERY"]
    """
    # Verify run exists
    run = repo.get_run(request.run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run not found: {request.run_id}")

    # Fetch client config
    client = repo.get_client(request.client_id)
    if not client:
        raise HTTPException(status_code=404, detail=f"Client not found: {request.client_id}")

    # Prepare each step
    prepared_steps = []
    for idx, step_name in enumerate(request.step_names, 1):
        # Get prompt for this step
        prompt = repo.get_prompt_by_step(step_name)
        if not prompt:
            raise HTTPException(status_code=404, detail=f"Prompt not found for step: {step_name}")

        # Generate step_id (use actual step count from DB to avoid conflicts)
        existing_steps = repo.client.table('v2_pipeline_steps').select('step_id').eq('run_id', request.run_id).execute()
        step_num = len(existing_steps.data) + 1
        step_id = f"STEP_{request.run_id}_{step_num:02d}"

        # Build base input (client config + seed data)
        step_input = {
            "current_date": datetime.now().strftime("%Y-%m-%d"),
            "icp_config_compressed": client.get('icp_config_compressed'),
            "industry_research_compressed": client.get('industry_research_compressed'),
            "research_context_compressed": client.get('research_context_compressed'),
            "client_specific_research": client.get('client_specific_research'),
            "seed_data": run.get('seed_data'),
            "dossier_id": request.dossier_id
        }

        # AUTO-FETCH: Get outputs from previous steps that this step depends on
        # Signal Discovery needs Search Builder output
        if step_name == "2_SIGNAL_DISCOVERY":
            search_output = repo.get_completed_step(request.run_id, "1_SEARCH_BUILDER")
            if search_output:
                step_input["search_builder_output"] = search_output.get('output')

        # Entity Research needs Signal Discovery output
        if step_name == "3_ENTITY_RESEARCH":
            signal_output = repo.get_completed_step(request.run_id, "2_SIGNAL_DISCOVERY")
            if signal_output:
                step_input["signal_discovery_output"] = signal_output.get('output')

        # Claims extraction needs the previous research output
        if "CLAIM" in step_name.upper() or step_name == "CLAIMS_EXTRACTION":
            # Try to get most recent research output (could be signal, entity, or contact)
            for research_step in ["4_CONTACT_DISCOVERY", "3_ENTITY_RESEARCH", "2_SIGNAL_DISCOVERY"]:
                research_output = repo.get_completed_step(request.run_id, research_step)
                if research_output:
                    step_input[f"{research_step.lower()}_output"] = research_output.get('output')
                    break  # Use most recent research step

        # Get model from prompt (defaulting to gpt-4.1)
        model_map = {
            "1_SEARCH_BUILDER": "o4-mini",
            "2_SIGNAL_DISCOVERY": "gpt-4.1",
            "3_ENTITY_RESEARCH": "o4-mini-deep-research",
            "4_CONTACT_DISCOVERY": "o4-mini-deep-research",
            "CLAIMS_EXTRACTION": "gpt-4.1",
            "CONTEXT_PACK_BUILDER": "gpt-4.1"
        }
        model_used = model_map.get(step_name, "gpt-4.1")

        prepared_steps.append(PreparedStep(
            step_id=step_id,
            step_name=step_name,
            prompt_id=prompt['prompt_id'],
            prompt_slug=prompt['prompt_slug'],
            prompt_template=prompt['prompt_template'],
            model_used=model_used,
            input=step_input,
            produce_claims=prompt.get('produce_claims', False)
        ))

        # Log step as "running" in database
        repo.create_pipeline_step({
            "step_id": step_id,
            "run_id": request.run_id,
            "prompt_id": prompt['prompt_id'],
            "step_name": step_name,
            "status": "running",
            "input": step_input,
            "model_used": model_used,
            "started_at": datetime.now().isoformat()
        })

    return StepPrepareResponse(
        run_id=request.run_id,
        steps=prepared_steps
    )


@router.post("/steps/complete", response_model=StepCompleteResponse)
async def complete_steps(request: StepCompleteRequest):
    """
    Store outputs for completed steps - JUST PASS THE ENTIRE OPENAI RESPONSE

    Make.com usage (final step):
        [1] POST /steps/complete
            Body: {
                "run_id": "RUN_20260114_002901",
                "outputs": [{
                    "step_name": "CLAIMS_EXTRACTION",
                    "output": {{6}}  // <-- Pass ENTIRE OpenAI response
                }]
            }

        We automatically extract:
        - tokens_used from response.usage
        - runtime_seconds from response timestamps
        - Full output stored for debugging

        [2] Response:
            {
                "success": true,
                "run_id": "RUN_20260114_002901",
                "steps_completed": ["CLAIMS_EXTRACTION"],
                "message": "1 step(s) completed successfully"
            }

    BATCHED (if you want to complete multiple at once):
        Body: {
            "run_id": "...",
            "outputs": [
                {"step_name": "STEP_A", "output": {{response_a}}},
                {"step_name": "STEP_B", "output": {{response_b}}}
            ]
        }
    """
    # Find step_ids for these step names
    completed_steps = []

    for output_item in request.outputs:
        # Find the pipeline step
        step = repo.get_completed_step(request.run_id, output_item.step_name)

        # If not found, try to find the "running" step
        if not step:
            result = repo.client.table('v2_pipeline_steps').select('*').eq('run_id', request.run_id).eq('step_name', output_item.step_name).eq('status', 'running').execute()
            if result.data:
                step = result.data[0]

        if not step:
            raise HTTPException(status_code=404, detail=f"Step not found: {output_item.step_name}")

        # AUTO-PARSE: If tokens/runtime not provided, extract from output
        tokens_used = output_item.tokens_used
        runtime_seconds = output_item.runtime_seconds
        output_to_store = output_item.output

        if tokens_used is None or runtime_seconds is None:
            parsed = parse_openai_response(output_item.output)
            tokens_used = parsed['tokens_used'] if tokens_used is None else tokens_used
            runtime_seconds = parsed['runtime_seconds'] if runtime_seconds is None else runtime_seconds
            output_to_store = parsed['full_output']

        # Update step to completed
        repo.update_pipeline_step(step['step_id'], {
            "status": "completed",
            "output": output_to_store,
            "tokens_used": tokens_used,
            "runtime_seconds": runtime_seconds,
            "completed_at": datetime.now().isoformat()
        })

        completed_steps.append(output_item.step_name)

    return StepCompleteResponse(
        success=True,
        run_id=request.run_id,
        steps_completed=completed_steps,
        message=f"{len(completed_steps)} step(s) completed successfully"
    )


@router.post("/steps/transition", response_model=StepTransitionResponse)
async def transition_step(request: StepTransitionRequest):
    """
    STORE PREVIOUS OUTPUT + PREPARE NEXT INPUT - ONE API CALL

    Perfect for chaining: Search Builder → Signal Discovery → Claims

    Make.com flow:
        [1] POST /steps/prepare (just for first step)
            Body: {"step_names": ["1_SEARCH_BUILDER"], ...}

        [2] Run Search Builder LLM

        [3] POST /steps/transition (store Search Builder, prepare Signal Discovery)
            Body: {
                "run_id": "RUN_...",
                "client_id": "CLT_...",
                "dossier_id": "DOSS_...",
                "completed_step_name": "1_SEARCH_BUILDER",
                "completed_step_output": {{2.entireOpenAIResponse}},  // Pass the WHOLE thing
                "next_step_name": "2_SIGNAL_DISCOVERY"
            }

        [4] Run Signal Discovery LLM with {{3.next_step.prompt_template}} and {{3.next_step.input}}

        [5] POST /steps/transition (store Signal Discovery, prepare Claims)
            Body: {
                "completed_step_name": "2_SIGNAL_DISCOVERY",
                "completed_step_output": {{4.entireOpenAIResponse}},
                "next_step_name": "PRODUCE_CLAIMS"
            }

        [6] Run Claims Extractor LLM

        [7] POST /steps/complete (final step - just store)

    Benefits:
    - ONE API call between AI modules (not two)
    - Automatic output parsing (we extract text, tokens, runtime)
    - Auto-fetch dependencies (Signal gets Search output, Claims gets Signal output)
    """
    # Parse the OpenAI output
    parsed = parse_openai_response(request.completed_step_output)

    # Find the running step to complete
    result = repo.client.table('v2_pipeline_steps').select('*').eq('run_id', request.run_id).eq('step_name', request.completed_step_name).eq('status', 'running').execute()

    if not result.data:
        raise HTTPException(status_code=404, detail=f"Running step not found: {request.completed_step_name}")

    completed_step = result.data[0]

    # Store the completed step output
    repo.update_pipeline_step(completed_step['step_id'], {
        "status": "completed",
        "output": parsed['full_output'],  # Store full response
        "tokens_used": parsed['tokens_used'],
        "runtime_seconds": parsed['runtime_seconds'],
        "completed_at": datetime.now().isoformat()
    })

    # Now prepare the next step (same logic as /steps/prepare but for one step)
    run = repo.get_run(request.run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run not found: {request.run_id}")

    client = repo.get_client(request.client_id)
    if not client:
        raise HTTPException(status_code=404, detail=f"Client not found: {request.client_id}")

    # Get prompt for next step
    prompt = repo.get_prompt_by_step(request.next_step_name)
    if not prompt:
        raise HTTPException(status_code=404, detail=f"Prompt not found for step: {request.next_step_name}")

    # Generate step_id
    existing_steps = repo.client.table('v2_pipeline_steps').select('step_id').eq('run_id', request.run_id).execute()
    step_num = len(existing_steps.data) + 1
    next_step_id = f"STEP_{request.run_id}_{step_num:02d}"

    # Build input
    step_input = {
        "current_date": datetime.now().strftime("%Y-%m-%d"),
        "icp_config_compressed": client.get('icp_config_compressed'),
        "industry_research_compressed": client.get('industry_research_compressed'),
        "research_context_compressed": client.get('research_context_compressed'),
        "client_specific_research": client.get('client_specific_research'),
        "seed_data": run.get('seed_data'),
        "dossier_id": request.dossier_id
    }

    # AUTO-FETCH: Add previous step output based on the transition
    # Use just-completed output when possible (cleaner than fetching from DB)

    if request.next_step_name == "2_SIGNAL_DISCOVERY":
        # Signal Discovery needs Search Builder (just completed)
        step_input["search_builder_output"] = parsed['full_output']

    if request.next_step_name == "CLAIMS_EXTRACTION":
        # Claims needs the research output (just completed)
        if request.completed_step_name in ["3_ENTITY_RESEARCH", "4_CONTACT_DISCOVERY", "2_SIGNAL_DISCOVERY"]:
            step_input[f"{request.completed_step_name.lower()}_output"] = parsed['full_output']

    if request.next_step_name == "CONTEXT_PACK_BUILDER":
        # Context pack needs the claims (just completed)
        step_input["claims_output"] = parsed['full_output']

    if request.next_step_name == "4_CONTACT_DISCOVERY":
        # Contact discovery needs the entity context pack (just completed)
        step_input["entity_context_pack"] = parsed['full_output']

    # Get model
    model_map = {
        "1_SEARCH_BUILDER": "o4-mini",
        "2_SIGNAL_DISCOVERY": "gpt-4.1",
        "3_ENTITY_RESEARCH": "o4-mini-deep-research",
        "4_CONTACT_DISCOVERY": "o4-mini-deep-research",
        "CLAIMS_EXTRACTION": "gpt-4.1",
        "CONTEXT_PACK_BUILDER": "gpt-4.1"
    }
    model_used = model_map.get(request.next_step_name, "gpt-4.1")

    # Log next step as "running"
    repo.create_pipeline_step({
        "step_id": next_step_id,
        "run_id": request.run_id,
        "prompt_id": prompt['prompt_id'],
        "step_name": request.next_step_name,
        "status": "running",
        "input": step_input,
        "model_used": model_used,
        "started_at": datetime.now().isoformat()
    })

    # Prepare response
    next_step_prepared = PreparedStep(
        step_id=next_step_id,
        step_name=request.next_step_name,
        prompt_id=prompt['prompt_id'],
        prompt_slug=prompt['prompt_slug'],
        prompt_template=prompt['prompt_template'],
        model_used=model_used,
        input=step_input,
        produce_claims=prompt.get('produce_claims', False)
    )

    return StepTransitionResponse(
        success=True,
        run_id=request.run_id,
        completed_step=request.completed_step_name,
        tokens_used=parsed['tokens_used'],
        runtime_seconds=parsed['runtime_seconds'],
        next_step=next_step_prepared
    )


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
