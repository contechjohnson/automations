"""
Columnline API Routes

Clean endpoints for Make.com integration.
No nested arrays, no JavaScript parsing - just clean JSON responses.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime

from .repository import ColumnlineRepository
from .pricing import calculate_cost
from .models import (
    RunStartRequest, RunStartResponse,
    RunCreate, RunUpdate, RunStatus,
    PipelineStepCreate, PipelineStepUpdate, PipelineStepComplete,
    ConfigsResponse, ClientConfig, PromptConfig,
    OutputsResponse, StepOutput,
    SuccessResponse,
    StepPrepareRequest, StepPrepareResponse, PreparedStep,
    StepCompleteRequest, StepCompleteResponse, StepOutputItem,
    StepTransitionRequest, StepTransitionResponse,
    # Stage Logging
    StageStartRequest, StageStartResponse,
    StageCompleteRequest, StageCompleteResponse,
    # Batch Composer
    BatchStartRequest, BatchStartResponse,
    BatchPrepareRequest, BatchPrepareResponse,
    BatchCompleteRequest, BatchCompleteResponse, BatchDirection,
    # Prep Inputs
    PrepStartRequest, PrepStartResponse,
    PrepPrepareRequest, PrepPrepareResponse,
    PrepCompleteRequest, PrepCompleteResponse,
    # Onboarding
    OnboardStartRequest, OnboardStartResponse,
    OnboardPrepareRequest, OnboardPrepareResponse,
    OnboardCompleteRequest, OnboardCompleteResponse,
    # Publish to Production
    PublishRequest, PublishResponse
)

router = APIRouter(prefix="/columnline", tags=["columnline"])
repo = ColumnlineRepository()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def parse_openai_response(openai_output):
    """
    Parse OpenAI API response to extract text, tokens, model, and runtime

    Handles both array format and single response format.
    Extracts input_tokens and output_tokens separately for cost calculation.
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

    # Extract tokens (detailed breakdown)
    input_tokens = 0
    output_tokens = 0
    tokens_used = 0
    if 'usage' in openai_output:
        usage = openai_output['usage']
        # OpenAI uses both naming conventions depending on API
        input_tokens = usage.get('input_tokens', usage.get('prompt_tokens', 0))
        output_tokens = usage.get('output_tokens', usage.get('completion_tokens', 0))
        tokens_used = usage.get('total_tokens', input_tokens + output_tokens)

    # Extract actual model from response (may differ from requested model)
    model_used = openai_output.get('model', None)

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
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "model_used": model_used,
        "runtime_seconds": runtime_seconds,
        "full_output": openai_output  # Store full response for debugging
    }


def extract_clean_content(openai_output):
    """
    Extract ONLY the clean content for passing to next step's input

    Removes all metadata, nested arrays, and irrelevant fields.
    Returns just what the next LLM needs to see.

    Handles different response formats:
    - Claims Extraction: Returns the claims array
    - Deep Research: Returns the narrative text
    - Context Pack: Returns the context pack content
    """
    # If it's an array, take first element
    if isinstance(openai_output, list):
        openai_output = openai_output[0]

    # Pattern 1: Claims Extraction format - has "result.claims"
    if 'result' in openai_output and isinstance(openai_output['result'], dict):
        if 'claims' in openai_output['result']:
            return openai_output['result']['claims']  # Just the claims array
        return openai_output['result']  # Or the whole result object if no claims

    # Pattern 2: Deep Research format - has "output" array with message content
    if 'output' in openai_output and isinstance(openai_output['output'], list):
        # Find the message content (skip reasoning/web_search_call)
        for output_item in openai_output['output']:
            if output_item.get('type') == 'message' and output_item.get('status') == 'completed':
                content = output_item.get('content', [])
                if content and isinstance(content, list):
                    for content_item in content:
                        if content_item.get('type') == 'output_text':
                            return content_item.get('text', '')  # Just the text

    # Pattern 3: Simple text response (fallback)
    if 'text' in openai_output:
        return openai_output['text']

    # Fallback: return the whole thing if we can't parse it
    return openai_output


def fetch_all_individual_claims(repo, run_id):
    """
    Fetch ALL individual claims AND narratives from all extraction steps

    For each research step, returns BOTH:
    - The extracted claims (from CLAIMS_EXTRACTION)
    - The original narrative (from the research step itself)

    Returns dict with keys like:
    - signal_discovery_claims + signal_discovery_narrative
    - entity_research_claims + entity_research_narrative
    - contact_discovery_claims + contact_discovery_narrative
    - enrich_lead_claims + enrich_lead_narrative
    - enrich_opportunity_claims + enrich_opportunity_narrative
    - client_specific_claims + client_specific_narrative
    - insight_claims + insight_narrative
    """
    claims_dict = {}

    # Find all completed claims extraction steps
    all_claims_steps = repo.client.table('v2_pipeline_logs').select('*').eq('run_id', run_id).eq('step_name', 'CLAIMS_EXTRACTION').eq('status', 'completed').execute()

    # Mapping of research step names to dict keys
    step_mappings = {
        '2_SIGNAL_DISCOVERY': ('signal_discovery_claims', 'signal_discovery_narrative'),
        '3_ENTITY_RESEARCH': ('entity_research_claims', 'entity_research_narrative'),
        '4_CONTACT_DISCOVERY': ('contact_discovery_claims', 'contact_discovery_narrative'),
        '5A_ENRICH_LEAD': ('enrich_lead_claims', 'enrich_lead_narrative'),
        '5B_ENRICH_OPPORTUNITY': ('enrich_opportunity_claims', 'enrich_opportunity_narrative'),
        '5C_CLIENT_SPECIFIC': ('client_specific_claims', 'client_specific_narrative'),
        '07B_INSIGHT': ('insight_claims', 'insight_narrative')
    }

    for claims_step in all_claims_steps.data:
        # Figure out which research step this came from by looking at the input
        step_input_data = claims_step.get('input', {})
        claims_output = extract_clean_content(claims_step.get('output'))

        # Determine the source research step
        source_step_name = None
        if '2_signal_discovery_output' in step_input_data:
            source_step_name = '2_SIGNAL_DISCOVERY'
        elif '3_entity_research_output' in step_input_data:
            source_step_name = '3_ENTITY_RESEARCH'
        elif '4_contact_discovery_output' in step_input_data:
            source_step_name = '4_CONTACT_DISCOVERY'
        elif '5a_enrich_lead_output' in step_input_data:
            source_step_name = '5A_ENRICH_LEAD'
        elif '5b_enrich_opportunity_output' in step_input_data:
            source_step_name = '5B_ENRICH_OPPORTUNITY'
        elif '5c_client_specific_output' in step_input_data:
            source_step_name = '5C_CLIENT_SPECIFIC'
        elif '07b_insight_output' in step_input_data:
            source_step_name = '07B_INSIGHT'

        if source_step_name and source_step_name in step_mappings:
            claims_key, narrative_key = step_mappings[source_step_name]

            # Store the claims
            claims_dict[claims_key] = claims_output

            # Fetch the original narrative from the research step
            narrative_step = repo.client.table('v2_pipeline_logs').select('*').eq('run_id', run_id).eq('step_name', source_step_name).eq('status', 'completed').execute()

            if narrative_step.data:
                narrative_output = extract_clean_content(narrative_step.data[0].get('output'))
                claims_dict[narrative_key] = narrative_output

    return claims_dict


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
# PIPELINE LOG ENDPOINTS (Logging & Polling)
# ============================================================================

@router.post("/pipeline_logs", response_model=SuccessResponse)
async def log_pipeline_step(step: PipelineStepCreate):
    """
    Log a pipeline step execution (dual-write pattern)

    Make.com usage (sub-scenario):
        [1] Log "running" status
            POST /columnline/pipeline_logs
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
            PUT /columnline/pipeline_logs/{{step_id}}
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
        message="Pipeline log created",
        data={"step_id": result['step_id']}
    )


@router.put("/pipeline_logs/{step_id}", response_model=SuccessResponse)
async def update_pipeline_step(step_id: str, updates: PipelineStepUpdate):
    """
    Update pipeline log (for dual-write pattern)

    See log_pipeline_step for usage example
    """
    result = repo.update_pipeline_step(step_id, updates.dict(exclude_unset=True))

    return SuccessResponse(
        success=True,
        message="Pipeline log updated",
        data={"step_id": result['step_id']}
    )


@router.get("/pipeline_logs/{run_id}/completed", response_model=PipelineStepComplete)
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
        [4] HTTP GET /columnline/pipeline_logs/{{run_id}}/completed?step_name=1_SEARCH_BUILDER
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

# NOTE: POST/GET /claims removed - claims stored in v2_pipeline_logs.output

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
        existing_steps = repo.client.table('v2_pipeline_logs').select('step_id').eq('run_id', request.run_id).execute()
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
        # Extract clean content (no metadata) for LLM consumption

        # Signal Discovery needs Search Builder output
        if step_name == "2_SIGNAL_DISCOVERY":
            search_output = repo.get_completed_step(request.run_id, "1_SEARCH_BUILDER")
            if search_output:
                step_input["search_builder_output"] = extract_clean_content(search_output.get('output'))

        # Entity Research needs Signal Discovery output
        if step_name == "3_ENTITY_RESEARCH":
            signal_output = repo.get_completed_step(request.run_id, "2_SIGNAL_DISCOVERY")
            if signal_output:
                step_input["signal_discovery_output"] = extract_clean_content(signal_output.get('output'))

        # Claims extraction needs the previous research/enrich output
        if "CLAIM" in step_name.upper() or step_name == "CLAIMS_EXTRACTION":
            # Try to get most recent research/enrich output (could be signal, entity, contact, or enrich steps)
            for research_step in ["5C_CLIENT_SPECIFIC", "5B_ENRICH_OPPORTUNITY", "5A_ENRICH_LEAD", "4_CONTACT_DISCOVERY", "3_ENTITY_RESEARCH", "2_SIGNAL_DISCOVERY"]:
                research_output = repo.get_completed_step(request.run_id, research_step)
                if research_output:
                    step_input[f"{research_step.lower()}_output"] = extract_clean_content(research_output.get('output'))
                    break  # Use most recent research/enrich step

        # Context Pack needs ALL claims extracted so far
        if step_name == "CONTEXT_PACK":
            # Find all completed claims extraction steps and get their outputs
            all_claims = []

            # Check for claims from Signal Discovery
            signal_claims_step = repo.client.table('v2_pipeline_logs').select('*').eq('run_id', request.run_id).eq('step_name', 'CLAIMS_EXTRACTION').eq('status', 'completed').execute()

            for claims_step in signal_claims_step.data:
                # Figure out which research step this came from by looking at the input
                step_input_data = claims_step.get('input', {})
                claims_output = extract_clean_content(claims_step.get('output'))

                # Add with descriptive key
                if '2_signal_discovery_output' in step_input_data:
                    step_input["signal_discovery_claims"] = claims_output
                elif '3_entity_research_output' in step_input_data:
                    step_input["entity_research_claims"] = claims_output
                elif '4_contact_discovery_output' in step_input_data:
                    step_input["contact_discovery_claims"] = claims_output

        # Enrich steps need signal, entity, contact outputs AND available claims
        if step_name in ["5A_ENRICH_LEAD", "5B_ENRICH_OPPORTUNITY", "5C_CLIENT_SPECIFIC"]:
            # Fetch signal discovery output
            signal_output = repo.get_completed_step(request.run_id, "2_SIGNAL_DISCOVERY")
            if signal_output:
                step_input["signal_discovery_output"] = extract_clean_content(signal_output.get('output'))

            # Fetch entity research output
            entity_output = repo.get_completed_step(request.run_id, "3_ENTITY_RESEARCH")
            if entity_output:
                step_input["entity_research_output"] = extract_clean_content(entity_output.get('output'))

            # Fetch contact discovery output
            contact_output = repo.get_completed_step(request.run_id, "4_CONTACT_DISCOVERY")
            if contact_output:
                step_input["contact_discovery_output"] = extract_clean_content(contact_output.get('output'))

            # Add all available claims (signal, entity, contact)
            all_claims_steps = repo.client.table('v2_pipeline_logs').select('*').eq('run_id', request.run_id).eq('step_name', 'CLAIMS_EXTRACTION').eq('status', 'completed').execute()

            for claims_step in all_claims_steps.data:
                step_input_data = claims_step.get('input', {})
                claims_output = extract_clean_content(claims_step.get('output'))

                if '2_signal_discovery_output' in step_input_data:
                    step_input["signal_discovery_claims"] = claims_output
                elif '3_entity_research_output' in step_input_data:
                    step_input["entity_research_claims"] = claims_output
                elif '4_contact_discovery_output' in step_input_data:
                    step_input["contact_discovery_claims"] = claims_output

        # Contact Discovery needs Signal Discovery + Entity Research outputs
        if step_name == "4_CONTACT_DISCOVERY":
            print(f"[PREPARE 4_CONTACT_DISCOVERY] Fetching dependencies for run {request.run_id}")
            signal_output = repo.get_completed_step(request.run_id, "2_SIGNAL_DISCOVERY")
            print(f"[PREPARE 4_CONTACT_DISCOVERY] 2_SIGNAL_DISCOVERY found: {bool(signal_output)}")
            if signal_output:
                step_input["signal_discovery_output"] = extract_clean_content(signal_output.get('output'))
                print(f"[PREPARE 4_CONTACT_DISCOVERY] Added signal_discovery_output")
            entity_output = repo.get_completed_step(request.run_id, "3_ENTITY_RESEARCH")
            print(f"[PREPARE 4_CONTACT_DISCOVERY] 3_ENTITY_RESEARCH found: {bool(entity_output)}")
            if entity_output:
                step_input["entity_research_output"] = extract_clean_content(entity_output.get('output'))
                print(f"[PREPARE 4_CONTACT_DISCOVERY] Added entity_research_output")

        # Insight needs ALL research narratives (not claims)
        if step_name == "07B_INSIGHT":
            print(f"[PREPARE 07B_INSIGHT] Fetching research narratives for run {request.run_id}")

            # Fetch all research narratives
            signal = repo.get_completed_step(request.run_id, "2_SIGNAL_DISCOVERY")
            print(f"[PREPARE 07B_INSIGHT] 2_SIGNAL_DISCOVERY found: {bool(signal)}")
            if signal:
                step_input["signal_discovery_narrative"] = extract_clean_content(signal.get('output'))

            entity = repo.get_completed_step(request.run_id, "3_ENTITY_RESEARCH")
            print(f"[PREPARE 07B_INSIGHT] 3_ENTITY_RESEARCH found: {bool(entity)}")
            if entity:
                step_input["entity_research_narrative"] = extract_clean_content(entity.get('output'))

            contacts = repo.get_completed_step(request.run_id, "4_CONTACT_DISCOVERY")
            print(f"[PREPARE 07B_INSIGHT] 4_CONTACT_DISCOVERY found: {bool(contacts)}")
            if contacts:
                step_input["contact_discovery_narrative"] = extract_clean_content(contacts.get('output'))

            # Enrichment outputs
            for step, key in [
                ("5A_ENRICH_LEAD", "enrich_lead_output"),
                ("5B_ENRICH_OPPORTUNITY", "enrich_opportunity_output"),
                ("5C_CLIENT_SPECIFIC", "client_specific_output"),
            ]:
                output = repo.get_completed_step(request.run_id, step)
                print(f"[PREPARE 07B_INSIGHT] {step} found: {bool(output)}")
                if output:
                    step_input[key] = extract_clean_content(output.get('output'))

        # Dossier Plan needs context pack + ALL individual claims
        if step_name == "9_DOSSIER_PLAN":
            context_pack_output = repo.get_completed_step(request.run_id, "CONTEXT_PACK")
            if context_pack_output:
                step_input["context_pack"] = extract_clean_content(context_pack_output.get('output'))

            # Pass ALL individual claims (not merged)
            all_claims = fetch_all_individual_claims(repo, request.run_id)
            step_input.update(all_claims)

        # Enrich Contacts needs ALL research narratives (V2 pipeline)
        # CRITICAL: contact_discovery_narrative contains the key_contacts to extract from!
        if step_name == "6_ENRICH_CONTACTS":
            # Fetch all research narratives up to this point
            signal = repo.get_completed_step(request.run_id, "2_SIGNAL_DISCOVERY")
            if signal:
                step_input["signal_discovery_narrative"] = extract_clean_content(signal.get('output'))

            entity = repo.get_completed_step(request.run_id, "3_ENTITY_RESEARCH")
            if entity:
                step_input["entity_research_narrative"] = extract_clean_content(entity.get('output'))

            # CRITICAL: This contains key_contacts from contact discovery research!
            contacts = repo.get_completed_step(request.run_id, "4_CONTACT_DISCOVERY")
            if contacts:
                step_input["contact_discovery_narrative"] = extract_clean_content(contacts.get('output'))

            # Enrichment outputs that may exist at this point
            for step, key in [
                ("5A_ENRICH_LEAD", "enrich_lead_output"),
                ("5B_ENRICH_OPPORTUNITY", "enrich_opportunity_output"),
                ("5C_CLIENT_SPECIFIC", "client_specific_output"),
            ]:
                output = repo.get_completed_step(request.run_id, step)
                if output:
                    step_input[key] = extract_clean_content(output.get('output'))

            # Backwards compatibility: still try old claims method
            context_pack_output = repo.get_completed_step(request.run_id, "CONTEXT_PACK")
            if context_pack_output:
                step_input["context_pack"] = extract_clean_content(context_pack_output.get('output'))
            all_claims = fetch_all_individual_claims(repo, request.run_id)
            step_input.update(all_claims)

        # Individual contact enrichment needs ALL research narratives (V2 pipeline)
        if step_name == "6_ENRICH_CONTACT_INDIVIDUAL":
            # Fetch all research narratives for context
            signal = repo.get_completed_step(request.run_id, "2_SIGNAL_DISCOVERY")
            if signal:
                step_input["signal_discovery_narrative"] = extract_clean_content(signal.get('output'))

            entity = repo.get_completed_step(request.run_id, "3_ENTITY_RESEARCH")
            if entity:
                step_input["entity_research_narrative"] = extract_clean_content(entity.get('output'))

            contacts = repo.get_completed_step(request.run_id, "4_CONTACT_DISCOVERY")
            if contacts:
                step_input["contact_discovery_narrative"] = extract_clean_content(contacts.get('output'))

            # Enrichment outputs for context
            for step, key in [
                ("5A_ENRICH_LEAD", "enrich_lead_output"),
                ("5B_ENRICH_OPPORTUNITY", "enrich_opportunity_output"),
            ]:
                output = repo.get_completed_step(request.run_id, step)
                if output:
                    step_input[key] = extract_clean_content(output.get('output'))

            # Backwards compatibility
            all_claims = fetch_all_individual_claims(repo, request.run_id)
            step_input.update(all_claims)

        # Media enrichment needs all research narratives (V2 pipeline)
        if step_name == "8_MEDIA":
            # Fetch all research narratives up to this point
            signal = repo.get_completed_step(request.run_id, "2_SIGNAL_DISCOVERY")
            if signal:
                signal_data = extract_clean_content(signal.get('output'))
                step_input["signal_discovery_narrative"] = signal_data
                # Extract company name and domain from signal discovery
                if isinstance(signal_data, dict) and 'lead' in signal_data:
                    step_input["target_company_name"] = signal_data['lead'].get('company_name', '')
                    step_input["target_company_domain"] = signal_data['lead'].get('company_domain', '')

            entity = repo.get_completed_step(request.run_id, "3_ENTITY_RESEARCH")
            if entity:
                step_input["entity_research_narrative"] = extract_clean_content(entity.get('output'))

            contacts = repo.get_completed_step(request.run_id, "4_CONTACT_DISCOVERY")
            if contacts:
                step_input["contact_discovery_narrative"] = extract_clean_content(contacts.get('output'))

            # Enrichment outputs
            for step, key in [
                ("5A_ENRICH_LEAD", "enrich_lead_output"),
                ("5B_ENRICH_OPPORTUNITY", "enrich_opportunity_output"),
                ("5C_CLIENT_SPECIFIC", "client_specific_output"),
                ("6_ENRICH_CONTACTS", "enriched_contacts"),
                ("07B_INSIGHT", "insight_output")
            ]:
                output = repo.get_completed_step(request.run_id, step)
                if output:
                    step_input[key] = extract_clean_content(output.get('output'))

            # Backwards compatibility: still try old claims method
            context_pack_output = repo.get_completed_step(request.run_id, "CONTEXT_PACK")
            if context_pack_output:
                step_input["context_pack"] = extract_clean_content(context_pack_output.get('output'))
            all_claims = fetch_all_individual_claims(repo, request.run_id)
            step_input.update(all_claims)

        # Copy needs enriched contact data (will be passed via transition or Make.com)
        # 10A_COPY and 10B_COPY_CLIENT_OVERRIDE auto-fetch handled in transition logic

        # All section writers need: dossier_plan + context_pack + ALL individual claims
        if step_name in ["10_WRITER_INTRO", "10_WRITER_SIGNALS", "10_WRITER_LEAD_INTELLIGENCE", "10_WRITER_STRATEGY", "10_WRITER_OPPORTUNITY", "10_WRITER_CLIENT_SPECIFIC"]:
            # Fetch dossier plan
            dossier_plan_output = repo.get_completed_step(request.run_id, "9_DOSSIER_PLAN")
            if dossier_plan_output:
                step_input["dossier_plan"] = extract_clean_content(dossier_plan_output.get('output'))

            # Fetch context pack
            context_pack_output = repo.get_completed_step(request.run_id, "CONTEXT_PACK")
            if context_pack_output:
                step_input["context_pack"] = extract_clean_content(context_pack_output.get('output'))

            # Pass ALL individual claims (not merged)
            all_claims = fetch_all_individual_claims(repo, request.run_id)
            step_input.update(all_claims)

        # Dossier Composer needs ALL research narratives (not claims)
        if step_name == "11_DOSSIER_COMPOSER":
            # Fetch all research narratives directly
            signal = repo.get_completed_step(request.run_id, "2_SIGNAL_DISCOVERY")
            if signal:
                step_input["signal_discovery_narrative"] = extract_clean_content(signal.get('output'))

            entity = repo.get_completed_step(request.run_id, "3_ENTITY_RESEARCH")
            if entity:
                step_input["entity_research_narrative"] = extract_clean_content(entity.get('output'))

            contacts = repo.get_completed_step(request.run_id, "4_CONTACT_DISCOVERY")
            if contacts:
                step_input["contact_discovery_narrative"] = extract_clean_content(contacts.get('output'))

            # Enrichment outputs + Insight
            for step, key in [
                ("5A_ENRICH_LEAD", "enrich_lead_output"),
                ("5B_ENRICH_OPPORTUNITY", "enrich_opportunity_output"),
                ("5C_CLIENT_SPECIFIC", "client_specific_output"),
                ("07B_INSIGHT", "insight_output"),
                ("6_ENRICH_CONTACTS", "enriched_contacts")
            ]:
                output = repo.get_completed_step(request.run_id, step)
                if output:
                    step_input[key] = extract_clean_content(output.get('output'))

            # Try to get pre-calculated lead_score from 5A_ENRICH_LEAD or seed_data
            # If not available, composer will calculate (fallback)
            enrich_lead = step_input.get("enrich_lead_output", {})
            if isinstance(enrich_lead, dict):
                if enrich_lead.get("lead_score"):
                    step_input["lead_score"] = enrich_lead["lead_score"]
                if enrich_lead.get("timing_urgency"):
                    step_input["timing_urgency"] = enrich_lead["timing_urgency"]
                if enrich_lead.get("score_explanation"):
                    step_input["score_explanation"] = enrich_lead["score_explanation"]

            # Fallback to seed_data if available
            run = repo.get_run(request.run_id)
            if run:
                seed = run.get("seed_data", {}) or {}
                if not step_input.get("lead_score") and seed.get("lead_score"):
                    step_input["lead_score"] = seed["lead_score"]
                if not step_input.get("timing_urgency") and seed.get("timing_urgency"):
                    step_input["timing_urgency"] = seed["timing_urgency"]

        # Merge Claims needs ALL claims including insight claims
        if step_name == "MERGE_CLAIMS":
            # Find all completed claims extraction steps
            all_claims_steps = repo.client.table('v2_pipeline_logs').select('*').eq('run_id', request.run_id).eq('step_name', 'CLAIMS_EXTRACTION').eq('status', 'completed').execute()

            for claims_step in all_claims_steps.data:
                # Figure out which research step this came from
                step_input_data = claims_step.get('input', {})
                claims_output = extract_clean_content(claims_step.get('output'))

                # Add with descriptive key based on which step produced these claims
                if '2_signal_discovery_output' in step_input_data:
                    step_input["signal_discovery_claims"] = claims_output
                elif '3_entity_research_output' in step_input_data:
                    step_input["entity_research_claims"] = claims_output
                elif '4_contact_discovery_output' in step_input_data:
                    step_input["contact_discovery_claims"] = claims_output
                elif '5a_enrich_lead_output' in step_input_data:
                    step_input["enrich_lead_claims"] = claims_output
                elif '5b_enrich_opportunity_output' in step_input_data:
                    step_input["enrich_opportunity_claims"] = claims_output
                elif '5c_client_specific_output' in step_input_data:
                    step_input["client_specific_claims"] = claims_output
                elif '07b_insight_output' in step_input_data:
                    step_input["insight_claims"] = claims_output

        # Get model from prompt (defaulting to gpt-4.1)
        model_map = {
            "1_SEARCH_BUILDER": "o4-mini",
            "2_SIGNAL_DISCOVERY": "gpt-4.1",
            "3_ENTITY_RESEARCH": "o4-mini-deep-research",
            "4_CONTACT_DISCOVERY": "o4-mini-deep-research",
            "5A_ENRICH_LEAD": "gpt-4.1",
            "5B_ENRICH_OPPORTUNITY": "gpt-4.1",
            "5C_CLIENT_SPECIFIC": "gpt-4.1",
            "07B_INSIGHT": "gpt-4.1",
            "MERGE_CLAIMS": "gpt-4.1",
            "CLAIMS_EXTRACTION": "gpt-4.1",
            "CONTEXT_PACK": "gpt-4.1",
            "8_MEDIA": "gpt-5.2",
            "9_DOSSIER_PLAN": "gpt-4.1",
            "10_WRITER_INTRO": "gpt-4.1",
            "10_WRITER_SIGNALS": "gpt-4.1",
            "10_WRITER_LEAD_INTELLIGENCE": "gpt-4.1",
            "10_WRITER_STRATEGY": "gpt-4.1",
            "10_WRITER_OPPORTUNITY": "gpt-4.1",
            "10_WRITER_CLIENT_SPECIFIC": "gpt-4.1",
            "6_ENRICH_CONTACTS": "gpt-4.1",
            "6_ENRICH_CONTACT_INDIVIDUAL": "gpt-4.1",
            "10A_COPY": "gpt-4.1",
            "10B_COPY_CLIENT_OVERRIDE": "gpt-4.1",
            "11_DOSSIER_COMPOSER": "gpt-4.1"  # Make.com can override this
        }
        model_used = model_map.get(step_name, "gpt-4.1")

        prepared_steps.append(PreparedStep(
            step_id=step_id,
            step_name=step_name,
            prompt_id=prompt['prompt_id'],
            prompt_slug=prompt['prompt_slug'],
            prompt_template=prompt['prompt_template'],
            model_used=model_used,
            input=step_input
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
    contacts_array = None
    media_data = None

    for output_item in request.outputs:
        # Find the pipeline step
        step = None

        print(f"[COMPLETE] Processing step: name={output_item.step_name}, step_id={output_item.step_id}")

        # If step_id provided, find by ID directly (for parallel steps with same name)
        if output_item.step_id:
            result = repo.client.table('v2_pipeline_logs').select('*').eq('step_id', output_item.step_id).eq('run_id', request.run_id).execute()
            if result.data:
                step = result.data[0]
                print(f"[COMPLETE] Found by step_id: {step['step_id']}")
            else:
                print(f"[COMPLETE] NOT FOUND by step_id: {output_item.step_id}")
        else:
            # Otherwise use step_name (existing logic)
            step = repo.get_completed_step(request.run_id, output_item.step_name)

            # If not found, try to find the "running" step
            if not step:
                result = repo.client.table('v2_pipeline_logs').select('*').eq('run_id', request.run_id).eq('step_name', output_item.step_name).eq('status', 'running').execute()
                if result.data:
                    # WARN if multiple running steps found
                    if len(result.data) > 1:
                        print(f"[COMPLETE] WARNING: Found {len(result.data)} running steps for {output_item.step_name}! Picking first one.")
                    step = result.data[0]
                    print(f"[COMPLETE] Found running step: {step['step_id']}")
            else:
                print(f"[COMPLETE] Found completed step: {step['step_id']}")

        if not step:
            print(f"[COMPLETE] ERROR: Step not found: {output_item.step_id or output_item.step_name}")
            raise HTTPException(status_code=404, detail=f"Step not found: {output_item.step_id or output_item.step_name}")

        # AUTO-PARSE: Extract tokens, runtime, model, and calculate cost
        parsed = parse_openai_response(output_item.output)
        tokens_used = output_item.tokens_used if output_item.tokens_used is not None else parsed['tokens_used']
        runtime_seconds = output_item.runtime_seconds if output_item.runtime_seconds is not None else parsed['runtime_seconds']
        output_to_store = parsed['full_output']

        # Extract detailed token info and model for cost calculation
        input_tokens = parsed['input_tokens']
        output_tokens = parsed['output_tokens']
        model_used = parsed['model_used'] or step.get('model_used')  # Fallback to step's model if not in response

        # Calculate estimated cost
        estimated_cost = 0.0
        if model_used and (input_tokens > 0 or output_tokens > 0):
            estimated_cost = calculate_cost(model_used, input_tokens, output_tokens)

        # Update step to completed with cost tracking
        repo.update_pipeline_step(step['step_id'], {
            "status": "completed",
            "output": output_to_store,
            "tokens_used": tokens_used,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "model_used": model_used,
            "estimated_cost": estimated_cost,
            "runtime_seconds": runtime_seconds,
            "completed_at": datetime.now().isoformat()
        })

        # Increment run totals
        if tokens_used > 0 or estimated_cost > 0:
            repo.increment_run_costs(request.run_id, tokens_used, estimated_cost)

        completed_steps.append(output_item.step_name)

        # SPECIAL: If completing 6_ENRICH_CONTACTS, extract contacts array for Make.com iteration
        if output_item.step_name == "6_ENRICH_CONTACTS":
            clean_content = extract_clean_content(output_to_store)
            contacts_array = []

            if isinstance(clean_content, dict):
                # Try multiple possible locations for contacts array
                if "contacts" in clean_content:
                    contacts_array = clean_content["contacts"]
                elif "enriched_contacts" in clean_content:
                    contacts_array = clean_content["enriched_contacts"]
                elif "key_contacts" in clean_content:
                    contacts_array = clean_content["key_contacts"]
                # Handle nested structure: {result: {key_contacts: [...]}}
                elif "result" in clean_content and isinstance(clean_content["result"], dict):
                    result = clean_content["result"]
                    if "contacts" in result:
                        contacts_array = result["contacts"]
                    elif "key_contacts" in result:
                        contacts_array = result["key_contacts"]
                    elif "enriched_contacts" in result:
                        contacts_array = result["enriched_contacts"]
            elif isinstance(clean_content, list):
                contacts_array = clean_content

            # Filter out companies - only keep entries that are actual people
            # A person has a "name" that looks like a person name (not a company name)
            filtered_contacts = []
            for contact in contacts_array:
                if isinstance(contact, dict):
                    name = contact.get("name", "")
                    # Skip if name looks like a company (contains Inc, LLC, Ltd, Corp, Architects, etc.)
                    company_indicators = ["Inc", "LLC", "Ltd", "Corp", "Company", "Architects", "Partners", "Group", "Associates", "Engineering", "Consulting"]
                    is_company = any(indicator.lower() in name.lower() for indicator in company_indicators)
                    # Also skip if there's no personal name indicators (no spaces or very short)
                    looks_like_person = " " in name and len(name.split()) >= 2

                    if looks_like_person and not is_company:
                        filtered_contacts.append(contact)

            contacts_array = filtered_contacts
            print(f"6_ENRICH_CONTACTS: Extracted {len(contacts_array)} people contacts (filtered out companies)")

        # SPECIAL: If completing 8_MEDIA, extract complete media output (as-is from GPT-5.2)
        if output_item.step_name == "8_MEDIA":
            try:
                clean_content = extract_clean_content(output_to_store)
                if isinstance(clean_content, dict):
                    # Store the entire media output (GPT-5.2 returns in .result):
                    # - as_of_date, entity
                    # - recommended_project_images (array)
                    # - optional_additional_visual_sources_to_check_next (array)
                    # - notes_for_sales_dossier_use
                    media_data = clean_content
                elif isinstance(clean_content, str):
                    # Sometimes LLM returns JSON as string - try to parse it
                    import json
                    try:
                        media_data = json.loads(clean_content)
                    except:
                        media_data = {"raw_text": clean_content}
                else:
                    # Fallback: wrap whatever we got
                    media_data = {"raw_content": str(clean_content)}
            except Exception as e:
                # Log error but don't fail the request
                print(f"Warning: Error extracting 8_MEDIA content: {e}")
                media_data = {"error": str(e), "raw_output_type": str(type(output_to_store))}

    return StepCompleteResponse(
        success=True,
        run_id=request.run_id,
        steps_completed=completed_steps,
        message=f"{len(completed_steps)} step(s) completed successfully",
        contacts=contacts_array,
        media_data=media_data
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

    # Find the step to complete - try "running" first, then any status
    result = repo.client.table('v2_pipeline_logs').select('*').eq('run_id', request.run_id).eq('step_name', request.completed_step_name).eq('status', 'running').execute()

    if not result.data:
        # Not in "running" status - try to find it with any status
        result = repo.client.table('v2_pipeline_logs').select('*').eq('run_id', request.run_id).eq('step_name', request.completed_step_name).execute()

    # If we found the step, update it to completed with cost tracking
    if result.data:
        completed_step = result.data[0]

        # Extract detailed token info and model for cost calculation
        input_tokens = parsed['input_tokens']
        output_tokens = parsed['output_tokens']
        model_used = parsed['model_used'] or completed_step.get('model_used')

        # Calculate estimated cost
        estimated_cost = 0.0
        if model_used and (input_tokens > 0 or output_tokens > 0):
            estimated_cost = calculate_cost(model_used, input_tokens, output_tokens)

        repo.update_pipeline_step(completed_step['step_id'], {
            "status": "completed",
            "output": parsed['full_output'],
            "tokens_used": parsed['tokens_used'],
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "model_used": model_used,
            "estimated_cost": estimated_cost,
            "runtime_seconds": parsed['runtime_seconds'],
            "completed_at": datetime.now().isoformat()
        })

        # Increment run totals
        if parsed['tokens_used'] > 0 or estimated_cost > 0:
            repo.increment_run_costs(request.run_id, parsed['tokens_used'], estimated_cost)
    # If step doesn't exist at all, that's okay - just proceed to create the next one

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
    existing_steps = repo.client.table('v2_pipeline_logs').select('step_id').eq('run_id', request.run_id).execute()
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
    # Extract CLEAN content (no metadata) for next step's input

    clean_output = extract_clean_content(request.completed_step_output)

    if request.next_step_name == "2_SIGNAL_DISCOVERY":
        # Signal Discovery needs Search Builder (just completed)
        step_input["search_builder_output"] = clean_output

    if request.next_step_name == "CLAIMS_EXTRACTION":
        # Claims needs the research/enrich/insight output (just completed)
        if request.completed_step_name in ["3_ENTITY_RESEARCH", "4_CONTACT_DISCOVERY", "2_SIGNAL_DISCOVERY", "5A_ENRICH_LEAD", "5B_ENRICH_OPPORTUNITY", "5C_CLIENT_SPECIFIC", "07B_INSIGHT"]:
            step_input[f"{request.completed_step_name.lower()}_output"] = clean_output

    if request.next_step_name == "MERGE_CLAIMS":
        # Merge Claims needs ALL claims including insight claims
        all_claims_steps = repo.client.table('v2_pipeline_logs').select('*').eq('run_id', request.run_id).eq('step_name', 'CLAIMS_EXTRACTION').eq('status', 'completed').execute()

        for claims_step in all_claims_steps.data:
            # Figure out which research step this came from
            step_input_data = claims_step.get('input', {})
            claims_output = extract_clean_content(claims_step.get('output'))

            # Add with descriptive key
            if '2_signal_discovery_output' in step_input_data:
                step_input["signal_discovery_claims"] = claims_output
            elif '3_entity_research_output' in step_input_data:
                step_input["entity_research_claims"] = claims_output
            elif '4_contact_discovery_output' in step_input_data:
                step_input["contact_discovery_claims"] = claims_output
            elif '5a_enrich_lead_output' in step_input_data:
                step_input["enrich_lead_claims"] = claims_output
            elif '5b_enrich_opportunity_output' in step_input_data:
                step_input["enrich_opportunity_claims"] = claims_output
            elif '5c_client_specific_output' in step_input_data:
                step_input["client_specific_claims"] = claims_output
            elif '07b_insight_output' in step_input_data:
                step_input["insight_claims"] = claims_output

    if request.next_step_name == "CONTEXT_PACK":
        # Context Pack logic depends on what came before it
        if request.completed_step_name == "MERGE_CLAIMS":
            # After merge claims, just pass the merged output
            step_input["merged_claims_output"] = clean_output
        else:
            # Legacy: Context pack after individual claims (not in 07B flow)
            # Context pack needs ALL claims extracted so far, not just the most recent
            # Find all completed claims extraction steps
            all_claims_steps = repo.client.table('v2_pipeline_logs').select('*').eq('run_id', request.run_id).eq('step_name', 'CLAIMS_EXTRACTION').eq('status', 'completed').execute()

            for claims_step in all_claims_steps.data:
                # Figure out which research step this came from
                step_input_data = claims_step.get('input', {})
                claims_output = extract_clean_content(claims_step.get('output'))

                # Add with descriptive key
                if '2_signal_discovery_output' in step_input_data:
                    step_input["signal_discovery_claims"] = claims_output
                elif '3_entity_research_output' in step_input_data:
                    step_input["entity_research_claims"] = claims_output
                elif '4_contact_discovery_output' in step_input_data:
                    step_input["contact_discovery_claims"] = claims_output

            # Also add the just-completed claims (in case the above query didn't catch it yet)
            if request.completed_step_name == "CLAIMS_EXTRACTION":
                # Need to figure out which research step this came from the transition request
                # We can look at what we just stored to figure this out
                # For now, just add it as "latest_claims"
                step_input["latest_claims"] = clean_output

    if request.next_step_name == "4_CONTACT_DISCOVERY":
        # Contact discovery needs signal + entity research outputs
        signal_output = repo.get_completed_step(request.run_id, "2_SIGNAL_DISCOVERY")
        if signal_output:
            step_input["signal_discovery_output"] = extract_clean_content(signal_output.get('output'))
        # Entity research just completed - pass as entity_research_output (not context pack)
        step_input["entity_research_output"] = clean_output

    if request.next_step_name in ["5A_ENRICH_LEAD", "5B_ENRICH_OPPORTUNITY", "5C_CLIENT_SPECIFIC"]:
        # Enrich steps need signal, entity, contact outputs AND available claims
        # Fetch signal discovery output
        signal_output = repo.get_completed_step(request.run_id, "2_SIGNAL_DISCOVERY")
        if signal_output:
            step_input["signal_discovery_output"] = extract_clean_content(signal_output.get('output'))

        # Fetch entity research output
        entity_output = repo.get_completed_step(request.run_id, "3_ENTITY_RESEARCH")
        if entity_output:
            step_input["entity_research_output"] = extract_clean_content(entity_output.get('output'))

        # Fetch contact discovery output
        contact_output = repo.get_completed_step(request.run_id, "4_CONTACT_DISCOVERY")
        if contact_output:
            step_input["contact_discovery_output"] = extract_clean_content(contact_output.get('output'))

        # Add all available claims (signal, entity, contact)
        all_claims_steps = repo.client.table('v2_pipeline_logs').select('*').eq('run_id', request.run_id).eq('step_name', 'CLAIMS_EXTRACTION').eq('status', 'completed').execute()

        for claims_step in all_claims_steps.data:
            step_input_data = claims_step.get('input', {})
            claims_output = extract_clean_content(claims_step.get('output'))

            if '2_signal_discovery_output' in step_input_data:
                step_input["signal_discovery_claims"] = claims_output
            elif '3_entity_research_output' in step_input_data:
                step_input["entity_research_claims"] = claims_output
            elif '4_contact_discovery_output' in step_input_data:
                step_input["contact_discovery_claims"] = claims_output

    if request.next_step_name == "07B_INSIGHT":
        # Insight (merge claims) needs ALL claims extracted so far
        all_claims_steps = repo.client.table('v2_pipeline_logs').select('*').eq('run_id', request.run_id).eq('step_name', 'CLAIMS_EXTRACTION').eq('status', 'completed').execute()

        for claims_step in all_claims_steps.data:
            # Figure out which research step this came from
            step_input_data = claims_step.get('input', {})
            claims_output = extract_clean_content(claims_step.get('output'))

            # Add with descriptive key
            if '2_signal_discovery_output' in step_input_data:
                step_input["signal_discovery_claims"] = claims_output
            elif '3_entity_research_output' in step_input_data:
                step_input["entity_research_claims"] = claims_output
            elif '4_contact_discovery_output' in step_input_data:
                step_input["contact_discovery_claims"] = claims_output
            elif '5a_enrich_lead_output' in step_input_data:
                step_input["enrich_lead_claims"] = claims_output
            elif '5b_enrich_opportunity_output' in step_input_data:
                step_input["enrich_opportunity_claims"] = claims_output
            elif '5c_client_specific_output' in step_input_data:
                step_input["client_specific_claims"] = claims_output

    # Contact enrichment flow transitions
    if request.next_step_name == "10A_COPY":
        # Copy needs enriched contact data (just completed)
        if request.completed_step_name == "6_ENRICH_CONTACT_INDIVIDUAL":
            step_input["enriched_contact_data"] = clean_output

    if request.next_step_name == "10B_COPY_CLIENT_OVERRIDE":
        # Client override copy needs the base copy (just completed)
        if request.completed_step_name == "10A_COPY":
            step_input["base_copy"] = clean_output

    if request.next_step_name == "6_ENRICH_CONTACTS":
        # Enrich contacts needs ALL research narratives (V2 pipeline)
        # CRITICAL: contact_discovery_narrative contains the key_contacts!
        signal = repo.get_completed_step(request.run_id, "2_SIGNAL_DISCOVERY")
        if signal:
            step_input["signal_discovery_narrative"] = extract_clean_content(signal.get('output'))

        entity = repo.get_completed_step(request.run_id, "3_ENTITY_RESEARCH")
        if entity:
            step_input["entity_research_narrative"] = extract_clean_content(entity.get('output'))

        # CRITICAL: This contains key_contacts from contact discovery research!
        contacts = repo.get_completed_step(request.run_id, "4_CONTACT_DISCOVERY")
        if contacts:
            step_input["contact_discovery_narrative"] = extract_clean_content(contacts.get('output'))

        # Enrichment outputs that may exist at this point
        for step, key in [
            ("5A_ENRICH_LEAD", "enrich_lead_output"),
            ("5B_ENRICH_OPPORTUNITY", "enrich_opportunity_output"),
            ("5C_CLIENT_SPECIFIC", "client_specific_output"),
        ]:
            output = repo.get_completed_step(request.run_id, step)
            if output:
                step_input[key] = extract_clean_content(output.get('output'))

    if request.next_step_name == "6_ENRICH_CONTACT_INDIVIDUAL":
        # Individual contact enrichment needs ALL research narratives (V2 pipeline)
        signal = repo.get_completed_step(request.run_id, "2_SIGNAL_DISCOVERY")
        if signal:
            step_input["signal_discovery_narrative"] = extract_clean_content(signal.get('output'))

        entity = repo.get_completed_step(request.run_id, "3_ENTITY_RESEARCH")
        if entity:
            step_input["entity_research_narrative"] = extract_clean_content(entity.get('output'))

        contacts = repo.get_completed_step(request.run_id, "4_CONTACT_DISCOVERY")
        if contacts:
            step_input["contact_discovery_narrative"] = extract_clean_content(contacts.get('output'))

        # Enrichment outputs for context
        for step, key in [
            ("5A_ENRICH_LEAD", "enrich_lead_output"),
            ("5B_ENRICH_OPPORTUNITY", "enrich_opportunity_output"),
        ]:
            output = repo.get_completed_step(request.run_id, step)
            if output:
                step_input[key] = extract_clean_content(output.get('output'))

    if request.next_step_name == "11_DOSSIER_COMPOSER":
        # Dossier composer needs all research narratives and enrichment outputs
        # Fetch research narratives
        signal = repo.get_completed_step(request.run_id, "2_SIGNAL_DISCOVERY")
        if signal:
            step_input["signal_discovery_narrative"] = extract_clean_content(signal.get('output'))

        entity = repo.get_completed_step(request.run_id, "3_ENTITY_RESEARCH")
        if entity:
            step_input["entity_research_narrative"] = extract_clean_content(entity.get('output'))

        contacts = repo.get_completed_step(request.run_id, "4_CONTACT_DISCOVERY")
        if contacts:
            step_input["contact_discovery_narrative"] = extract_clean_content(contacts.get('output'))

        # Enrichment outputs + Insight
        for step, key in [
            ("5A_ENRICH_LEAD", "enrich_lead_output"),
            ("5B_ENRICH_OPPORTUNITY", "enrich_opportunity_output"),
            ("5C_CLIENT_SPECIFIC", "client_specific_output"),
            ("07B_INSIGHT", "insight_output"),
            ("6_ENRICH_CONTACTS", "enriched_contacts")
        ]:
            output = repo.get_completed_step(request.run_id, step)
            if output:
                step_input[key] = extract_clean_content(output.get('output'))

        # Client context for composer prompt
        step_input["client_name"] = client.get('client_name', '')
        step_input["client_services"] = client.get('services', client.get('client_services', ''))
        step_input["client_differentiators"] = client.get('differentiators', client.get('client_differentiators', ''))

        # Pre-calculated scores from enrich_lead
        enrich_lead = step_input.get("enrich_lead_output", {})
        if isinstance(enrich_lead, dict):
            if enrich_lead.get("lead_score"):
                step_input["lead_score"] = enrich_lead["lead_score"]
            if enrich_lead.get("timing_urgency"):
                step_input["timing_urgency"] = enrich_lead["timing_urgency"]
            if enrich_lead.get("score_explanation"):
                step_input["score_explanation"] = enrich_lead["score_explanation"]

        # Fallback to seed_data if scores not in enrich_lead
        seed = run.get("seed_data", {}) or {}
        if not step_input.get("lead_score") and seed.get("lead_score"):
            step_input["lead_score"] = seed["lead_score"]
        if not step_input.get("timing_urgency") and seed.get("timing_urgency"):
            step_input["timing_urgency"] = seed["timing_urgency"]

    # Get model
    model_map = {
        "1_SEARCH_BUILDER": "o4-mini",
        "2_SIGNAL_DISCOVERY": "gpt-4.1",
        "3_ENTITY_RESEARCH": "o4-mini-deep-research",
        "4_CONTACT_DISCOVERY": "o4-mini-deep-research",
        "5A_ENRICH_LEAD": "gpt-4.1",
        "5B_ENRICH_OPPORTUNITY": "gpt-4.1",
        "5C_CLIENT_SPECIFIC": "gpt-4.1",
        "07B_INSIGHT": "gpt-4.1",
        "MERGE_CLAIMS": "gpt-4.1",
        "CLAIMS_EXTRACTION": "gpt-4.1",
        "CONTEXT_PACK": "gpt-4.1",
        "8_MEDIA": "gpt-5.2",
        "9_DOSSIER_PLAN": "gpt-4.1",
        "10_WRITER_INTRO": "gpt-4.1",
        "10_WRITER_SIGNALS": "gpt-4.1",
        "10_WRITER_LEAD_INTELLIGENCE": "gpt-4.1",
        "10_WRITER_STRATEGY": "gpt-4.1",
        "10_WRITER_OPPORTUNITY": "gpt-4.1",
        "10_WRITER_CLIENT_SPECIFIC": "gpt-4.1",
        "6_ENRICH_CONTACTS": "gpt-4.1",
        "6_ENRICH_CONTACT_INDIVIDUAL": "gpt-4.1",
        "10A_COPY": "gpt-4.1",
        "10B_COPY_CLIENT_OVERRIDE": "gpt-4.1",
        "11_DOSSIER_COMPOSER": "gpt-4.1"
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
        input=step_input
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
# STAGE LOGGING ENDPOINTS
# ============================================================================

# Stage name mapping for consistent naming
STAGE_NAMES = {
    1: "search_signal",
    2: "entity_research",
    3: "parallel_research",
    4: "parallel_agents",
    5: "publish"
}


@router.post("/stages/start", response_model=StageStartResponse)
async def stage_start(request: StageStartRequest):
    """
    Log the start of a pipeline stage.

    Inserts a row into v2_pipeline_logs with event_type='stage_start'.
    Called by Make.com Prime Pipeline before each stage begins.
    """
    import uuid

    # Validate stage name matches expected
    expected_name = STAGE_NAMES.get(request.stage_number)
    if expected_name and request.stage_name != expected_name:
        # Warn but allow - use provided name
        pass

    step_id = f"STAGE_{uuid.uuid4().hex[:8].upper()}"
    step_name = f"STAGE_{request.stage_number}_{request.stage_name.upper()}"
    now = datetime.utcnow()

    # Insert into v2_pipeline_logs with event_type
    step_data = {
        "step_id": step_id,
        "run_id": request.run_id,
        "prompt_id": None,  # Stages don't have prompts
        "step_name": step_name,
        "status": "running",
        "event_type": "stage_start",
        "input": {
            "stage_number": request.stage_number,
            "stage_name": request.stage_name
        },
        "started_at": now.isoformat()
    }

    repo.create_pipeline_step(step_data)

    return StageStartResponse(
        success=True,
        step_id=step_id,
        run_id=request.run_id,
        stage_number=request.stage_number,
        stage_name=request.stage_name,
        started_at=now,
        message=f"Stage {request.stage_number} ({request.stage_name}) started"
    )


@router.post("/stages/complete", response_model=StageCompleteResponse)
async def stage_complete(request: StageCompleteRequest):
    """
    Log the completion of a pipeline stage.

    Updates the stage_start row OR inserts a stage_complete row.
    Called by Make.com Prime Pipeline after each stage's polling completes.
    """
    now = datetime.utcnow()

    # Find the stage_start row to calculate duration
    stage_name = STAGE_NAMES.get(request.stage_number, f"stage_{request.stage_number}")
    step_name_pattern = f"STAGE_{request.stage_number}_%"

    # Look for the running stage_start row
    result = repo.client.table('v2_pipeline_logs').select('*').eq(
        'run_id', request.run_id
    ).eq(
        'event_type', 'stage_start'
    ).eq(
        'status', 'running'
    ).ilike(
        'step_name', step_name_pattern
    ).execute()

    started_at = None
    duration_seconds = None
    step_id = None

    if result.data:
        # Found the stage_start row - update it
        stage_row = result.data[0]
        step_id = stage_row['step_id']
        started_at_str = stage_row.get('started_at')

        if started_at_str:
            started_at = datetime.fromisoformat(started_at_str.replace('Z', '+00:00').replace('+00:00', ''))
            duration_seconds = (now - started_at).total_seconds()

        # Determine status
        status = "failed" if request.error_message else "completed"

        # Update the row
        update_data = {
            "status": status,
            "completed_at": now.isoformat(),
            "runtime_seconds": duration_seconds,
            "event_type": "stage_complete"  # Change from stage_start to stage_complete
        }

        if request.error_message:
            update_data["error_message"] = request.error_message

        repo.update_pipeline_step(step_id, update_data)

        # Get stage_name from the row
        stage_name = stage_row.get('input', {}).get('stage_name', stage_name)

    else:
        # No stage_start found - insert a stage_complete row directly
        import uuid
        step_id = f"STAGE_{uuid.uuid4().hex[:8].upper()}"

        status = "failed" if request.error_message else "completed"

        step_data = {
            "step_id": step_id,
            "run_id": request.run_id,
            "prompt_id": None,
            "step_name": f"STAGE_{request.stage_number}_{stage_name.upper()}",
            "status": status,
            "event_type": "stage_complete",
            "input": {
                "stage_number": request.stage_number,
                "stage_name": stage_name
            },
            "completed_at": now.isoformat(),
            "error_message": request.error_message
        }

        repo.create_pipeline_step(step_data)

    return StageCompleteResponse(
        success=True,
        step_id=step_id,
        run_id=request.run_id,
        stage_number=request.stage_number,
        stage_name=stage_name,
        started_at=started_at,
        completed_at=now,
        duration_seconds=duration_seconds,
        status="failed" if request.error_message else "completed",
        message=f"Stage {request.stage_number} ({stage_name}) {'failed' if request.error_message else 'completed'}"
    )


# ============================================================================
# SECTION ENDPOINTS
# ============================================================================

# NOTE: POST/GET /sections removed - sections stored in v2_pipeline_logs.output

# ============================================================================
# DOSSIER ENDPOINTS
# ============================================================================

# NOTE: POST/PUT/GET v2_dossiers removed - dossiers go to production via /publish
# DELETE endpoint kept below in PUBLISH section for cleanup

# ============================================================================
# CONTACT ENDPOINTS
# ============================================================================

# NOTE: POST /contacts removed - contacts populated via /publish dual-write

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


# ============================================================================
# BATCH COMPOSER ENDPOINTS
# ============================================================================

@router.post("/batches/start", response_model=BatchStartResponse)
async def start_batch(request: BatchStartRequest):
    """
    Start a new batch for generating seed directions.

    Creates a batch record and assigns it to a thread for memory continuity.

    Make.com usage:
        HTTP POST /columnline/batches/start
        Body: {"client_id": "CLT_EXAMPLE_001", "batch_size": 10}

        Response: {
            "batch_id": "BATCH_20260115_001",
            "thread_id": "THREAD_CLT_EXAMPLE_001_v1",
            "batch_number": 5
        }
    """
    # Validate client exists
    client = repo.get_client(request.client_id)
    if not client:
        raise HTTPException(status_code=404, detail=f"Client not found: {request.client_id}")

    # Get or create thread_id
    thread_id = repo.get_client_thread(request.client_id)
    if not thread_id:
        thread_id = f"THREAD_{request.client_id}_v1"

    # Get next batch number
    batch_number = repo.get_next_batch_number(request.client_id, thread_id)

    # Generate batch_id
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_id = f"BATCH_{timestamp}_{batch_number:03d}"

    # Create batch record
    batch_data = {
        "batch_id": batch_id,
        "client_id": request.client_id,
        "status": "pending",
        "thread_id": thread_id,
        "batch_number": batch_number,
        "batch_strategy": client.get('batch_strategy'),
        "started_at": datetime.now().isoformat()
    }

    repo.create_batch(batch_data)

    return BatchStartResponse(
        success=True,
        batch_id=batch_id,
        client_id=request.client_id,
        thread_id=thread_id,
        batch_number=batch_number,
        message="Batch created successfully"
    )


@router.post("/batches/prepare", response_model=BatchPrepareResponse)
async def prepare_batch(request: BatchPrepareRequest):
    """
    Prepare inputs for batch composer LLM call.

    Fetches compressed configs, recent batches (thread memory), and existing leads.

    Make.com usage:
        HTTP POST /columnline/batches/prepare
        Body: {"batch_id": "BATCH_20260115_001"}

        Response: {
            "batch_id": "...",
            "prompt_id": "16_batch_composer",
            "prompt_template": "...",
            "model_used": "gpt-4.1",
            "input": {
                "icp_config_compressed": {...},
                "industry_research_compressed": {...},
                "research_context_compressed": {...},
                "batch_strategy_compressed": {...},
                "recent_directions": [...],
                "existing_leads": [...],
                "batch_size": 10
            }
        }

        Then Make.com runs the LLM with prompt_template + input
    """
    # Get batch record
    batch = repo.get_batch(request.batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail=f"Batch not found: {request.batch_id}")

    # Get client
    client = repo.get_client(batch['client_id'])
    if not client:
        raise HTTPException(status_code=404, detail=f"Client not found: {batch['client_id']}")

    # Get batch composer prompt (prompt 16)
    prompt = repo.get_prompt_by_step("16_BATCH_COMPOSER")
    if not prompt:
        # Try by slug
        prompt = repo.get_prompt_by_slug("batch-composer")
    if not prompt:
        raise HTTPException(status_code=404, detail="Batch composer prompt not found (step: 16_BATCH_COMPOSER)")

    # Get thread memory - recent batches in this thread
    recent_batches = repo.get_recent_batches(batch['client_id'], batch['thread_id'], limit=3)
    recent_directions = []
    for rb in recent_batches:
        if rb.get('directions'):
            recent_directions.extend(rb['directions'])

    # Get existing leads to avoid duplicates
    existing_leads = repo.get_existing_leads(batch['client_id'], limit=30)

    # Get batch size from strategy or use default
    batch_strategy = client.get('batch_strategy', {})
    batch_size = batch_strategy.get('seed_generation_rules', {}).get('count_per_batch', {}).get('max', 10)

    # Build input
    batch_input = {
        "current_date": datetime.now().strftime("%Y-%m-%d"),
        "icp_config_compressed": client.get('icp_config_compressed'),
        "industry_research_compressed": client.get('industry_research_compressed'),
        "research_context_compressed": client.get('research_context_compressed'),
        "batch_strategy_compressed": client.get('batch_strategy_compressed'),
        "recent_directions": recent_directions,
        "existing_leads": existing_leads,
        "batch_size": batch_size,
        "batch_number": batch['batch_number'],
        "thread_id": batch['thread_id']
    }

    # Store snapshots for debugging
    repo.update_batch(request.batch_id, {
        "existing_leads_snapshot": existing_leads,
        "recent_directions_snapshot": recent_directions
    })

    return BatchPrepareResponse(
        batch_id=request.batch_id,
        prompt_id=prompt['prompt_id'],
        prompt_template=prompt['prompt_template'],
        model_used="gpt-4.1",
        input=batch_input
    )


@router.post("/batches/complete", response_model=BatchCompleteResponse)
async def complete_batch(request: BatchCompleteRequest):
    """
    Complete batch with LLM output containing directions.

    Stores directions and returns them for Make.com to iterate and trigger pipelines.

    Make.com usage:
        HTTP POST /columnline/batches/complete
        Body: {
            "batch_id": "BATCH_20260115_001",
            "output": {{entire_openai_response}}
        }

        Response: {
            "success": true,
            "batch_id": "...",
            "directions": [
                {"project_type": "data_center", "geography": "Virginia", "signal_type": "epcm_award", "hint": "Hyperscale"},
                ...
            ],
            "directions_count": 10,
            "distribution_achieved": {"data_center": 7, "mining": 1, ...}
        }

        Make.com then iterates over directions array to trigger pipelines
    """
    # Get batch record
    batch = repo.get_batch(request.batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail=f"Batch not found: {request.batch_id}")

    # Parse LLM output
    parsed = parse_openai_response(request.output)
    clean_output = extract_clean_content(request.output)

    # Extract directions from output
    directions = []
    distribution_achieved = None

    if isinstance(clean_output, dict):
        # Look for directions in various locations
        if 'directions' in clean_output:
            directions = clean_output['directions']
        elif 'seeds' in clean_output:
            directions = clean_output['seeds']
        elif 'result' in clean_output and isinstance(clean_output['result'], dict):
            result = clean_output['result']
            if 'directions' in result:
                directions = result['directions']
            elif 'seeds' in result:
                directions = result['seeds']

        # Extract distribution achieved
        if 'distribution_achieved' in clean_output:
            distribution_achieved = clean_output['distribution_achieved']
        elif 'result' in clean_output and isinstance(clean_output['result'], dict):
            distribution_achieved = clean_output['result'].get('distribution_achieved')

    # Convert to BatchDirection objects
    direction_objects = []
    for d in directions:
        if isinstance(d, dict):
            direction_objects.append(BatchDirection(
                project_type=d.get('project_type', 'unknown'),
                geography=d.get('geography', 'unknown'),
                signal_type=d.get('signal_type'),
                hint=d.get('hint', '')
            ))

    # Update batch record
    repo.update_batch(request.batch_id, {
        "status": "completed",
        "directions": [d.model_dump() for d in direction_objects],
        "distribution_achieved": distribution_achieved,
        "completed_at": datetime.now().isoformat()
    })

    return BatchCompleteResponse(
        success=True,
        batch_id=request.batch_id,
        directions=direction_objects,
        directions_count=len(direction_objects),
        distribution_achieved=distribution_achieved,
        message=f"Batch completed with {len(direction_objects)} directions"
    )


# ============================================================================
# PUBLISH TO PRODUCTION ENDPOINTS
# ============================================================================

def get_or_create_v2_batch(production_client_id: str) -> dict:
    """
    Get or create a daily V2 batch for this client.
    Returns batch record with 'id' field.
    """
    from datetime import date
    today = date.today().strftime('%Y%m%d')
    batch_number = f"V2_{today}"

    # Check if batch exists for today
    result = repo.client.table('batches').select('*').match({
        'client_id': production_client_id,
        'batch_number': batch_number
    }).execute()

    if result.data:
        return result.data[0]

    # Create new batch
    new_batch = repo.client.table('batches').insert({
        'client_id': production_client_id,
        'batch_number': batch_number,
        'status': 'complete',  # V2 dossiers arrive ready
        'total_dossiers': 0,
        'completed_dossiers': 0,
        'created_at': datetime.now().isoformat()
    }).execute()

    return new_batch.data[0]


def assemble_find_lead(step_outputs: dict, seed_data: dict) -> dict:
    """Assemble find_lead JSONB from writer outputs."""
    find_lead = {
        'one_liner': '',
        'the_angle': '',
        'score_explanation': '',
        'lead_score': 0,
        'timing_urgency': 'MEDIUM',
        'primary_buying_signal': {},
        'company_snapshot': {},
        'company_name': ''
    }

    # From WRITER_INTRO (10_WRITER_INTRO)
    intro_output = step_outputs.get('10_WRITER_INTRO', {})
    if intro_output:
        clean = extract_clean_content(intro_output.get('output', {}))
        if isinstance(clean, dict):
            find_lead['one_liner'] = clean.get('one_liner') or ''
            find_lead['the_angle'] = clean.get('the_angle') or ''
            find_lead['score_explanation'] = clean.get('score_explanation') or ''
            find_lead['lead_score'] = clean.get('lead_score') or 0

    # From WRITER_SIGNALS (10_WRITER_SIGNALS)
    signals_output = step_outputs.get('10_WRITER_SIGNALS', {})
    if signals_output:
        clean = extract_clean_content(signals_output.get('output', {}))
        if isinstance(clean, dict):
            find_lead['timing_urgency'] = clean.get('timing_urgency') or 'MEDIUM'
            pbs = clean.get('primary_buying_signal') or {}
            # Transform V2 field names to V1 expected names:
            # - signal_type -> signal
            # - source_tier -> source_name
            if pbs.get('signal_type') and not pbs.get('signal'):
                pbs['signal'] = pbs['signal_type']
            if pbs.get('source_tier') and not pbs.get('source_name'):
                pbs['source_name'] = pbs['source_tier']
            find_lead['primary_buying_signal'] = pbs
            # Additional signals go to enrich_lead

    # From WRITER_OPPORTUNITY (10_WRITER_OPPORTUNITY)
    opp_output = step_outputs.get('10_WRITER_OPPORTUNITY', {})
    if opp_output:
        clean = extract_clean_content(opp_output.get('output', {}))
        if isinstance(clean, dict):
            find_lead['company_snapshot'] = clean.get('company_snapshot') or {}
            # NEW: opportunity_intelligence for UI section
            if clean.get('opportunity_intelligence'):
                find_lead['opportunity_intelligence'] = clean['opportunity_intelligence']

    # From WRITER_CLIENT_SPECIFIC (10_WRITER_CLIENT_SPECIFIC)
    client_specific_output = step_outputs.get('10_WRITER_CLIENT_SPECIFIC', {})
    if client_specific_output:
        clean = extract_clean_content(client_specific_output.get('output', {}))
        if isinstance(clean, dict):
            # NEW: custom_research for UI section (golfers, alumni, associations, etc.)
            if clean.get('custom_research'):
                find_lead['custom_research'] = clean['custom_research']

    # Get company_name - prefer company_snapshot, fall back to seed_data
    company_snapshot = find_lead.get('company_snapshot', {})
    find_lead['company_name'] = (
        company_snapshot.get('company_name') or
        company_snapshot.get('name') or
        (seed_data.get('company_name') if seed_data else None) or
        (seed_data.get('name') if seed_data else None) or
        ''
    )

    # Extract resolved_entity from 3_ENTITY_RESEARCH
    entity_output = step_outputs.get('3_ENTITY_RESEARCH', {})
    if entity_output:
        clean = extract_clean_content(entity_output.get('output', {}))
        if isinstance(clean, dict):
            resolved_entity = clean.get('resolved_entity', {})
            if resolved_entity:
                find_lead['resolved_entity'] = resolved_entity
                # Ensure company_intel.network_intelligence is properly nested
                company_intel = resolved_entity.get('company_intel', {})
                if company_intel:
                    find_lead['resolved_entity']['company_intel'] = company_intel

    return find_lead


def assemble_enrich_lead(step_outputs: dict) -> dict:
    """Assemble enrich_lead JSONB from writer outputs."""
    enrich_lead = {
        'company_deep_dive': {},
        'network_intelligence': {},
        'project_sites': [],
        'additional_signals': []
    }

    # From WRITER_LEAD_INTELLIGENCE (10_WRITER_LEAD_INTELLIGENCE)
    intel_output = step_outputs.get('10_WRITER_LEAD_INTELLIGENCE', {})
    if intel_output:
        clean = extract_clean_content(intel_output.get('output', {}))
        if isinstance(clean, dict):
            enrich_lead['company_deep_dive'] = clean.get('company_deep_dive') or {}
            enrich_lead['network_intelligence'] = clean.get('network_intelligence') or {}

    # From WRITER_OPPORTUNITY (10_WRITER_OPPORTUNITY) - project_sites
    opp_output = step_outputs.get('10_WRITER_OPPORTUNITY', {})
    if opp_output:
        clean = extract_clean_content(opp_output.get('output', {}))
        if isinstance(clean, dict):
            enrich_lead['project_sites'] = clean.get('project_sites') or []

    # From WRITER_SIGNALS (10_WRITER_SIGNALS) - additional_signals
    signals_output = step_outputs.get('10_WRITER_SIGNALS', {})
    if signals_output:
        clean = extract_clean_content(signals_output.get('output', {}))
        if isinstance(clean, dict):
            enrich_lead['additional_signals'] = clean.get('additional_signals') or []

    # From WRITER_OPPORTUNITY (10_WRITER_OPPORTUNITY) - opportunity_details
    opp_output = step_outputs.get('10_WRITER_OPPORTUNITY', {})
    if opp_output:
        clean = extract_clean_content(opp_output.get('output', {}))
        if isinstance(clean, dict):
            if clean.get('opportunity_details'):
                enrich_lead['opportunity_details'] = clean['opportunity_details']

    # From WRITER_CLIENT_SPECIFIC (10_WRITER_CLIENT_SPECIFIC) - client_specific
    client_specific_output = step_outputs.get('10_WRITER_CLIENT_SPECIFIC', {})
    if client_specific_output:
        clean = extract_clean_content(client_specific_output.get('output', {}))
        if isinstance(clean, dict):
            if clean.get('client_specific'):
                enrich_lead['client_specific'] = clean['client_specific']

    return enrich_lead


def assemble_insight(step_outputs: dict) -> dict:
    """Assemble insight JSONB from WRITER_STRATEGY and 07B_INSIGHT outputs."""
    insight = {
        'the_math': {},
        'deal_strategy': {},
        'competitive_positioning': {},
        'decision_making_process': {},
        'sources': []
    }

    # First try from 07B_INSIGHT (raw insight data)
    insight_output = step_outputs.get('07B_INSIGHT', {})
    if insight_output:
        clean = extract_clean_content(insight_output.get('output', {}))
        if isinstance(clean, dict):
            insight['the_math'] = clean.get('the_math') or {}
            insight['deal_strategy'] = clean.get('deal_strategy') or {}
            insight['competitive_positioning'] = clean.get('competitive_positioning') or {}
            insight['decision_making_process'] = clean.get('decision_making_process') or {}

    # Then try from WRITER_STRATEGY (10_WRITER_STRATEGY) - can override/fill gaps
    strategy_output = step_outputs.get('10_WRITER_STRATEGY', {})
    if strategy_output:
        clean = extract_clean_content(strategy_output.get('output', {}))
        if isinstance(clean, dict):
            # Only override if we have better data
            if clean.get('the_math'):
                insight['the_math'] = clean['the_math']
            if clean.get('deal_strategy'):
                insight['deal_strategy'] = clean['deal_strategy']
            if clean.get('competitive_positioning'):
                insight['competitive_positioning'] = clean['competitive_positioning']
            if clean.get('decision_making_process'):
                insight['decision_making_process'] = clean['decision_making_process']

    # Collect sources from all steps
    sources = []
    for step_name, step_data in step_outputs.items():
        if isinstance(step_data, dict):
            clean = extract_clean_content(step_data.get('output', {}))
            if isinstance(clean, dict) and clean.get('sources'):
                step_sources = clean['sources']
                if isinstance(step_sources, list):
                    sources.extend(step_sources)
    insight['sources'] = sources

    return insight


def assemble_copy(step_outputs: dict, contact_id_map: dict) -> dict:
    """
    Assemble copy JSONB from contact outputs and WRITER_STRATEGY.
    contact_id_map: {index: production_contact_uuid}
    """
    copy_data = {
        'outreach': [],
        'objections': [],
        'conversation_starters': []
    }

    # From WRITER_STRATEGY - objections and conversation_starters
    strategy_output = step_outputs.get('10_WRITER_STRATEGY', {})
    if strategy_output:
        clean = extract_clean_content(strategy_output.get('output', {}))
        if isinstance(clean, dict):
            # Transform objections - response may be object or string
            raw_objections = clean.get('objections') or []
            transformed_objections = []
            for obj in raw_objections:
                if isinstance(obj, dict):
                    response = obj.get('response', '')
                    # If response is an object, concatenate its parts into a string
                    if isinstance(response, dict):
                        parts = []
                        if response.get('acknowledge'):
                            parts.append(response['acknowledge'])
                        if response.get('reframe'):
                            parts.append(response['reframe'])
                        if response.get('evidence'):
                            parts.append(response['evidence'])
                        if response.get('close'):
                            parts.append(response['close'])
                        response = ' '.join(parts)
                    transformed_objections.append({
                        'objection': obj.get('objection', ''),
                        'response': response
                    })
            copy_data['objections'] = transformed_objections
            copy_data['conversation_starters'] = clean.get('conversation_starters') or []

    # Outreach is built per-contact during contact insertion
    # The contact_id_map will be populated with production UUIDs

    return copy_data


def assemble_media(step_outputs: dict) -> dict:
    """Assemble media JSONB from 8_MEDIA output."""
    media = {
        'logo_url': '',
        'logo_fallback_chain': [],
        'project_images': []
    }

    media_output = step_outputs.get('8_MEDIA', {})
    if media_output:
        clean = extract_clean_content(media_output.get('output', {}))
        if isinstance(clean, dict):
            media['logo_url'] = clean.get('logo_url') or ''
            media['logo_fallback_chain'] = clean.get('logo_fallback_chain') or []
            # Try multiple field names for project images
            media['project_images'] = (
                clean.get('project_images') or
                clean.get('recommended_project_images') or
                clean.get('image_assets') or
                []
            )

    return media


@router.post("/publish/{run_id}", response_model=PublishResponse)
async def publish_to_production(run_id: str, request: PublishRequest = None):
    """
    Publish a v2 dossier to production tables.

    This endpoint:
    1. Fetches all completed step outputs for the run
    2. Resolves v2_client → production client UUID
    3. Gets or creates a daily V2 batch
    4. Assembles JSONB columns (find_lead, enrich_lead, copy, insight, media)
    5. Inserts contacts into production contacts table
    6. Builds outreach array with production contact UUIDs
    7. Inserts dossier into production dossiers table

    Make.com usage (final step after all writers complete):
        HTTP POST /columnline/publish/{{run_id}}
        Body: {"release_date": "2026-01-20"}  // Optional - immediate if not provided

        Response: {
            "success": true,
            "run_id": "RUN_...",
            "production_dossier_id": "uuid-...",
            "production_batch_id": "uuid-...",
            "contacts_created": 3,
            "pipeline_version": "v2"
        }
    """
    import uuid
    import traceback

    try:
        return await _publish_to_production_impl(run_id, request)
    except HTTPException:
        raise
    except Exception as e:
        print(f"PUBLISH ERROR for {run_id}: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Publish failed: {str(e)}")


async def _publish_to_production_impl(run_id: str, request: PublishRequest = None):
    """Internal implementation of publish_to_production"""
    import uuid

    if request is None:
        request = PublishRequest()

    # 1. Get the v2 run
    run = repo.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    # 2. Get v2 client and resolve to production client
    v2_client = repo.get_client(run['client_id'])
    if not v2_client:
        raise HTTPException(status_code=404, detail=f"V2 client not found: {run['client_id']}")

    production_client_id = v2_client.get('production_client_id')
    if not production_client_id:
        raise HTTPException(
            status_code=400,
            detail=f"V2 client {run['client_id']} has no production_client_id mapping. Run the migration first."
        )

    # 3. Get or create daily V2 batch
    batch = get_or_create_v2_batch(production_client_id)

    # 4. Fetch all completed step outputs
    step_outputs = {}
    steps = repo.client.table('v2_pipeline_logs').select('*').eq('run_id', run_id).eq('status', 'completed').execute()
    for step in steps.data:
        step_outputs[step['step_name']] = step

    # Validate we have minimum required outputs (either composers OR writers)
    has_composer = '11_DOSSIER_COMPOSER' in step_outputs

    # Check for writer/copy steps (new naming: 10A_COPY, 10B_COPY; old naming: 10_WRITER_*)
    copy_steps = [s for s in step_outputs.keys() if s.startswith('10A_COPY') or s.startswith('10B_COPY')]
    writer_steps = [s for s in step_outputs.keys() if s.startswith('10_WRITER')]
    has_writers_or_copy = len(copy_steps) > 0 or len(writer_steps) > 0

    print(f"  Publish validation: has_composer={has_composer}, copy_steps={len(copy_steps)}, writer_steps={len(writer_steps)}")
    print(f"  Step outputs found: {list(step_outputs.keys())}")

    if not has_composer and not has_writers_or_copy:
        raise HTTPException(
            status_code=400,
            detail=f"No writer or composer outputs found for run {run_id}. Run 11_DOSSIER_COMPOSER or writers first. Found steps: {list(step_outputs.keys())}"
        )

    if has_composer:
        print(f"Using 11_DOSSIER_COMPOSER for dossier assembly (dynamic sections)")

    # 5. Get seed data (handle None explicitly)
    seed_data = run.get('seed_data') or {}

    # 6. Assemble JSONB columns
    find_lead = assemble_find_lead(step_outputs, seed_data)
    enrich_lead = assemble_enrich_lead(step_outputs)
    insight_data = assemble_insight(step_outputs)
    media_data = assemble_media(step_outputs)

    # 6b. Extract V1 fields from Dossier Composer (if available)
    # NOTE: V2 composer outputs flat V1 JSON fields, NOT sections[]
    sections = None  # Keep null to disable DynamicDossierView, use V1 rendering
    composer_step = step_outputs.get('11_DOSSIER_COMPOSER', {})
    print(f"  [DEBUG] composer_step exists: {bool(composer_step)}")
    print(f"  [DEBUG] composer_step keys: {list(composer_step.keys()) if composer_step else 'N/A'}")
    if composer_step:
        raw_output = composer_step.get('output', {})
        print(f"  [DEBUG] raw_output type: {type(raw_output)}, keys: {list(raw_output.keys()) if isinstance(raw_output, dict) else 'N/A'}")
        composer_output = extract_clean_content(raw_output)
        print(f"  [DEBUG] composer_output type: {type(composer_output)}, keys: {list(composer_output.keys()) if isinstance(composer_output, dict) else 'N/A'}")
        if isinstance(composer_output, dict):
            print(f"  [DEBUG] Mapping V1 composer output to dossier fields")

            # Map V1 composer output to find_lead fields
            if composer_output.get('companyName'):
                find_lead['company_name'] = composer_output['companyName']
            if composer_output.get('domain'):
                find_lead['company_snapshot'] = find_lead.get('company_snapshot', {})
                find_lead['company_snapshot']['domain'] = composer_output['domain']
            if composer_output.get('whatTheyDo'):
                find_lead['what_they_do'] = composer_output['whatTheyDo']
            if composer_output.get('theAngle'):
                find_lead['the_angle'] = composer_output['theAngle']
            if composer_output.get('leadScore'):
                find_lead['lead_score'] = composer_output['leadScore']
            if composer_output.get('explanation'):
                find_lead['score_explanation'] = composer_output['explanation']
            if composer_output.get('urgency'):
                find_lead['timing_urgency'] = composer_output['urgency']
            if composer_output.get('timingContext'):
                find_lead['one_liner'] = composer_output['timingContext']
            if composer_output.get('opportunityIntelligence'):
                find_lead['opportunity_intelligence'] = composer_output['opportunityIntelligence']
            if composer_output.get('customResearch'):
                find_lead['custom_research'] = composer_output['customResearch']

            # Map V1 composer output to enrich_lead fields
            if composer_output.get('companyIntel'):
                enrich_lead['company_intel'] = composer_output['companyIntel']
            if composer_output.get('whyNow'):
                enrich_lead['why_now'] = composer_output['whyNow']
            if composer_output.get('corporateStructure'):
                enrich_lead['corporate_structure'] = composer_output['corporateStructure']
            if composer_output.get('networkIntelligence'):
                enrich_lead['network_intelligence'] = composer_output['networkIntelligence']

            # Map V1 composer output to insight fields
            if composer_output.get('theMathStructured'):
                insight_data['the_math'] = composer_output['theMathStructured']
            if composer_output.get('dealStrategy'):
                insight_data['deal_strategy'] = composer_output['dealStrategy']
            if composer_output.get('competitivePositioning'):
                insight_data['competitive_positioning'] = composer_output['competitivePositioning']
            if composer_output.get('decisionStrategy'):
                insight_data['decision_strategy'] = composer_output['decisionStrategy']
            if composer_output.get('commonObjections'):
                insight_data['common_objections'] = composer_output['commonObjections']
            if composer_output.get('quickReference'):
                insight_data['quick_reference'] = composer_output['quickReference']
            if composer_output.get('sources'):
                insight_data['sources'] = composer_output['sources']

            print(f"  [DEBUG] V1 mapping complete: lead_score={find_lead.get('lead_score')}, the_angle present={bool(find_lead.get('the_angle'))}")

    # 6c. Extract client-specific output DIRECTLY (runs ASYNC with composer)
    # This handles the case where 5C_CLIENT_SPECIFIC runs in parallel and outputs V1 JSON directly
    client_specific_step = step_outputs.get('5C_CLIENT_SPECIFIC', {})
    if client_specific_step:
        cs_output = extract_clean_content(client_specific_step.get('output', {}))
        if isinstance(cs_output, dict):
            # customResearch goes to find_lead (if not already set by composer)
            if cs_output.get('customResearch') and not find_lead.get('custom_research'):
                find_lead['custom_research'] = cs_output['customResearch']

            # warmPathsIn goes to network_intelligence (MERGE with existing)
            if cs_output.get('warmPathsIn'):
                if not enrich_lead.get('network_intelligence'):
                    enrich_lead['network_intelligence'] = {}
                existing_warm_paths = enrich_lead['network_intelligence'].get('warm_paths_in', [])
                enrich_lead['network_intelligence']['warm_paths_in'] = existing_warm_paths + cs_output['warmPathsIn']

            # Merge sources
            if cs_output.get('sources'):
                existing_sources = insight_data.get('sources', [])
                insight_data['sources'] = existing_sources + cs_output['sources']

            print(f"  [DEBUG] 5C_CLIENT_SPECIFIC extracted: customResearch={bool(cs_output.get('customResearch'))}, warmPathsIn={bool(cs_output.get('warmPathsIn'))}")

    # 7. Insert contacts and build ID map
    contact_id_map = {}
    contacts_created = 0

    # Get contacts from 6_ENRICH_CONTACTS output (base list with why_they_matter, role_in_project)
    contacts_step = step_outputs.get('6_ENRICH_CONTACTS', {})
    contacts_list = []
    if contacts_step:
        clean = extract_clean_content(contacts_step.get('output', {}))
        if isinstance(clean, dict):
            contacts_list = clean.get('contacts', clean.get('enriched_contacts', clean.get('key_contacts', [])))
        elif isinstance(clean, list):
            contacts_list = clean

    # Get individual contact enrichments (email, linkedin, signal_relevance, etc.)
    # Query directly since multiple steps share the same step_name
    individual_enrichments = {}
    individual_steps = repo.client.table('v2_pipeline_logs').select('output').eq(
        'run_id', run_id
    ).eq('step_name', '6_ENRICH_CONTACT_INDIVIDUAL').eq('status', 'completed').execute()

    for step in individual_steps.data:
        enrichment = extract_clean_content(step.get('output', {}))
        if isinstance(enrichment, dict):
            # Try multiple field name patterns (uppercase from old prompts, lowercase from new)
            first = enrichment.get('FIRST_NAME') or enrichment.get('first_name') or ''
            last = enrichment.get('LAST_NAME') or enrichment.get('last_name') or ''
            contact_name = enrichment.get('name') or f"{first} {last}".strip()
            if contact_name:
                individual_enrichments[contact_name.lower()] = enrichment
                print(f"  Found enrichment for: {contact_name}")

    # Get copy data from 10A_COPY and 10B_COPY_CLIENT_OVERRIDE steps
    # Query directly since multiple steps share the same step_name
    contact_copy_data = {}
    copy_steps = repo.client.table('v2_pipeline_logs').select('output').eq(
        'run_id', run_id
    ).eq('step_name', '10A_COPY').eq('status', 'completed').execute()

    for step in copy_steps.data:
        copy_output = extract_clean_content(step.get('output', {}))
        if isinstance(copy_output, dict):
            copy_outputs = copy_output.get('copy_outputs', [])
            for copy_item in copy_outputs:
                if isinstance(copy_item, dict):
                    contact_name = copy_item.get('contact_name', '')
                    if contact_name:
                        contact_copy_data[contact_name.lower()] = copy_item
                        print(f"  Found copy for: {contact_name}")

    # Also check for client override copy (takes precedence)
    override_steps = repo.client.table('v2_pipeline_logs').select('output').eq(
        'run_id', run_id
    ).eq('step_name', '10B_COPY_CLIENT_OVERRIDE').eq('status', 'completed').execute()

    for step in override_steps.data:
        copy_output = extract_clean_content(step.get('output', {}))
        if isinstance(copy_output, dict):
            copy_outputs = copy_output.get('copy_outputs', copy_output.get('override_copy', []))
            for copy_item in copy_outputs:
                if isinstance(copy_item, dict):
                    contact_name = copy_item.get('contact_name', '')
                    if contact_name:
                        # Override existing copy with client-specific version
                        contact_copy_data[contact_name.lower()] = copy_item
                        print(f"  Found client override copy for: {contact_name}")

    # Generate production dossier ID
    production_dossier_id = str(uuid.uuid4())

    # 8. Assemble initial copy data (without contact IDs - will update after contacts inserted)
    copy_data = assemble_copy(step_outputs, contact_id_map)

    # 9. Determine release timing
    released_at = None
    release_date = request.release_date
    if not release_date:
        # Immediate release
        released_at = datetime.now().isoformat()

    # 10. Get company info for dossier
    company_name = (
        seed_data.get('company_name') or
        seed_data.get('name') or
        seed_data.get('company') or
        find_lead.get('company_name') or
        find_lead.get('company_snapshot', {}).get('name') or
        # Try to extract from contacts
        (contacts_list[0].get('company') if contacts_list else None) or
        f"Dossier_{run_id}"  # Last resort fallback
    )
    company_domain = (
        seed_data.get('domain') or
        seed_data.get('company_domain') or
        find_lead.get('company_snapshot', {}).get('domain')
    )

    # 11. CHECK FOR EXISTING DOSSIER (unique constraint on client_id + company_domain)
    existing_dossier = None
    if company_domain:
        existing_check = repo.client.table('dossiers').select('id').eq(
            'client_id', production_client_id
        ).eq('company_domain', company_domain).execute()
        if existing_check.data:
            existing_dossier = existing_check.data[0]
            production_dossier_id = existing_dossier['id']
            print(f"Found existing dossier {production_dossier_id} for {company_domain}, will update")

    dossier_data = {
        'id': production_dossier_id,
        'client_id': production_client_id,
        'batch_id': batch['id'],
        'company_name': company_name,
        'company_domain': company_domain,
        'find_leads': find_lead,  # Note: column is 'find_leads' with 's'
        'enrich_lead': enrich_lead,
        'copy': copy_data,  # Initial copy without outreach - will update after contacts
        'insight': insight_data,
        'media': media_data,
        'sections': sections,  # Dynamic sections from 11_DOSSIER_COMPOSER (null for legacy dossiers)
        'lead_score': find_lead.get('lead_score', 0),
        'timing_urgency': find_lead.get('timing_urgency', 'MEDIUM'),
        'primary_signal': find_lead.get('primary_buying_signal', {}).get('signal', ''),
        'status': 'ready',
        'pipeline_version': 'v2',
        'agents_completed': ['find-lead', 'enrich-contacts', 'enrich-lead', 'write-copy', 'insight', 'enrich-media'],
        'release_date': release_date,
        'released_at': released_at,
        'updated_at': datetime.now().isoformat()
    }

    if existing_dossier:
        # Update existing dossier
        repo.client.table('dossiers').update(dossier_data).eq('id', production_dossier_id).execute()
        # Delete existing contacts for this dossier (will re-create fresh)
        repo.client.table('contacts').delete().eq('dossier_id', production_dossier_id).execute()
    else:
        # Insert new dossier
        dossier_data['created_at'] = datetime.now().isoformat()
        repo.client.table('dossiers').insert(dossier_data).execute()

    # 12. NOW insert contacts (dossier exists, FK constraint satisfied)
    outreach_list = []
    for idx, contact in enumerate(contacts_list):
        if not isinstance(contact, dict):
            continue

        # Build contact name - prefer 'name' field, fall back to first+last
        contact_name = contact.get('name', '')
        if not contact_name:
            first = contact.get('first_name', '') or ''
            last = contact.get('last_name', '') or ''
            contact_name = f"{first} {last}".strip()
        if not contact_name:
            contact_name = 'Unknown Contact'

        # Look up individual enrichment data by name
        enrichment = individual_enrichments.get(contact_name.lower(), {})

        # Merge base contact data with individual enrichment
        # Support both uppercase (old prompts) and lowercase (new prompts) field names
        first_name = (
            enrichment.get('FIRST_NAME') or enrichment.get('first_name') or
            contact.get('first_name') or
            (contact_name.split()[0] if contact_name else '')
        )
        last_name = (
            enrichment.get('LAST_NAME') or enrichment.get('last_name') or
            contact.get('last_name') or
            (contact_name.split()[-1] if contact_name and len(contact_name.split()) > 1 else '')
        )
        email = (
            enrichment.get('EMAIL') or enrichment.get('email') or
            contact.get('email')
        )
        linkedin_url = (
            enrichment.get('LINKEDIN_URL') or enrichment.get('linkedin_url') or
            contact.get('linkedin_url') or contact.get('linkedin')
        )
        phone = (
            enrichment.get('PHONE') or enrichment.get('phone') or
            contact.get('phone')
        )

        # Build rich bio from multiple sources
        bio_parts = []
        if contact.get('why_they_matter'):
            bio_parts.append(contact['why_they_matter'])
        if enrichment.get('LINKEDIN_SUMMARY') or enrichment.get('linkedin_summary'):
            bio_parts.append(enrichment.get('LINKEDIN_SUMMARY') or enrichment.get('linkedin_summary'))
        if enrichment.get('WEB_SUMMARY') or enrichment.get('web_summary'):
            bio_parts.append(enrichment.get('WEB_SUMMARY') or enrichment.get('web_summary'))
        bio_paragraph = ' '.join(bio_parts) if bio_parts else contact.get('bio_paragraph', '')

        # Store ALL enrichment data in JSONB column (nothing lost!)
        # Support both uppercase and lowercase field names
        enrichment_data = {
            # From 6_ENRICH_CONTACTS (base contact info)
            'role_in_project': contact.get('role_in_project'),
            'why_they_matter': contact.get('why_they_matter'),
            'notes': contact.get('notes'),
            'confidence': contact.get('confidence'),
            # From 6_ENRICH_CONTACT_INDIVIDUAL (rich enrichment) - try both cases
            'signal_relevance': enrichment.get('SIGNAL_RELEVANCE') or enrichment.get('signal_relevance'),
            'interesting_facts': enrichment.get('INTERESTING_FACTS') or enrichment.get('interesting_facts', []),
            'linkedin_summary': enrichment.get('LINKEDIN_SUMMARY') or enrichment.get('linkedin_summary'),
            'web_summary': enrichment.get('WEB_SUMMARY') or enrichment.get('web_summary'),
            'email_confidence': enrichment.get('EMAIL_CONFIDENCE') or enrichment.get('email_confidence'),
            'email_source': enrichment.get('EMAIL_SOURCE') or enrichment.get('email_source'),
            'linkedin_source': enrichment.get('LINKEDIN_SOURCE') or enrichment.get('linkedin_source'),
        }
        # Remove None values to keep it clean
        enrichment_data = {k: v for k, v in enrichment_data.items() if v is not None}

        contact_data = {
            'dossier_id': production_dossier_id,
            'name': contact_name or 'Unknown Contact',
            'first_name': first_name or '',
            'last_name': last_name or '',
            'title': contact.get('title') or contact.get('role') or '',
            'email': email or '',
            'phone': phone or '',
            'linkedin_url': linkedin_url or '',
            'bio_paragraph': bio_paragraph or '',
            'is_primary': idx == 0,  # First contact is primary
            'source': 'v2_pipeline',
            'created_at': datetime.now().isoformat()
        }

        # Add enrichment_data if the column exists (JSONB with all the rich data)
        if enrichment_data:
            contact_data['enrichment_data'] = enrichment_data

        # Insert contact
        try:
            result = repo.client.table('contacts').insert(contact_data).execute()
            if result.data:
                prod_contact_id = result.data[0]['id']
                contact_id_map[idx] = prod_contact_id
                contacts_created += 1

                # DUAL-WRITE: Also store in v2_contacts for observability
                v2_contact_id = f"V2C_{run_id}_{idx}"
                v2_contact_data = {
                    'id': v2_contact_id,
                    'run_id': run_id,
                    'dossier_id': run.get('dossier_id'),  # v2 dossier_id
                    'name': contact_name,
                    'first_name': first_name,
                    'last_name': last_name,
                    'title': contact_data.get('title'),
                    'email': email,
                    'phone': contact.get('phone'),
                    'linkedin_url': linkedin_url,
                    'bio_paragraph': bio_paragraph,
                    'is_primary': idx == 0,
                    'source': 'v2_pipeline',
                    'why_they_matter': contact.get('why_they_matter'),
                    'signal_relevance': enrichment.get('SIGNAL_RELEVANCE'),
                    'interesting_facts': enrichment.get('INTERESTING_FACTS'),
                    'linkedin_summary': enrichment.get('LINKEDIN_SUMMARY'),
                    'web_summary': enrichment.get('WEB_SUMMARY'),
                    'confidence': contact.get('confidence')
                }
                # Remove None values
                v2_contact_data = {k: v for k, v in v2_contact_data.items() if v is not None}
                try:
                    repo.create_contact(v2_contact_data)
                except Exception as v2_err:
                    print(f"Warning: Failed to write v2_contact for {contact_name}: {v2_err}")

                # Build outreach entry for this contact
                # First check contact_copy_data (from 10A_COPY / 10B_COPY_CLIENT_OVERRIDE)
                copy_info = contact_copy_data.get(contact_name.lower(), {})

                # Get email copy - prefer copy_info from 10A_COPY steps
                email_subject = copy_info.get('email_subject', '')
                email_body = copy_info.get('email_body', '')
                linkedin_message = copy_info.get('linkedin_message', copy_info.get('linkedin_copy', ''))

                # Fall back to contact fields if no copy found
                if not email_body:
                    email_copy = contact.get('email_copy', {})
                    if isinstance(email_copy, str):
                        email_body = email_copy
                    else:
                        email_subject = email_subject or contact.get('email_subject') or email_copy.get('subject', '')
                        email_body = contact.get('email_body') or email_copy.get('body', '')

                if not linkedin_message:
                    linkedin_copy = contact.get('linkedin_copy', '')
                    if isinstance(linkedin_copy, dict):
                        linkedin_message = linkedin_copy.get('message', '')
                    else:
                        linkedin_message = contact.get('linkedin_message') or linkedin_copy

                outreach_entry = {
                    'contact_id': str(prod_contact_id),
                    'target_name': contact_name,
                    'target_title': contact_data['title'] or '',
                    'email_subject': email_subject,
                    'email_body': email_body,
                    'linkedin_message': linkedin_message
                }
                outreach_list.append(outreach_entry)
        except Exception as e:
            print(f"Warning: Failed to insert contact {contact_name}: {e}")

    # 13. Update dossier's copy field with outreach list (now that contacts exist with IDs)
    if outreach_list:
        copy_data['outreach'] = outreach_list
        repo.client.table('dossiers').update({'copy': copy_data}).eq('id', production_dossier_id).execute()

    # 14. Update batch counts (only if new dossier, not update)
    if not existing_dossier:
        repo.client.table('batches').update({
            'total_dossiers': batch.get('total_dossiers', 0) + 1,
            'completed_dossiers': batch.get('completed_dossiers', 0) + 1
        }).eq('id', batch['id']).execute()

    # 12. Update v2 run status (store production_dossier_id in seed_data for reference)
    current_seed = run.get('seed_data') or {}
    current_seed['_production_dossier_id'] = production_dossier_id
    repo.update_run(run_id, {
        'seed_data': current_seed,
        'status': 'published'
    })

    # Build rendered object in V1 UI format (matches DossierView.tsx expectations)
    # This mirrors the transformDossier function in web/lib/transforms.ts
    primary_signal = find_lead.get('primary_buying_signal', {})
    company_snapshot = find_lead.get('company_snapshot', {})
    company_deep_dive = enrich_lead.get('company_deep_dive', {})
    network_intel = enrich_lead.get('network_intelligence', {})
    the_math = insight_data.get('the_math', {})
    competitive = insight_data.get('competitive_positioning', {})
    decision_making = insight_data.get('decision_making_process', {})
    deal_strat = insight_data.get('deal_strategy', {})

    # Build whyNow signals array
    why_now_signals = []
    if primary_signal:
        why_now_signals.append({
            'signal': primary_signal.get('signal', ''),
            'happening': primary_signal.get('description', ''),
            'proof': {
                'text': primary_signal.get('source_name', ''),
                'url': primary_signal.get('source_url', '')
            }
        })
    for sig in enrich_lead.get('additional_signals', []):
        why_now_signals.append({
            'signal': sig.get('signal', ''),
            'happening': sig.get('description', ''),
            'proof': {
                'text': sig.get('source_name', ''),
                'url': sig.get('source_url', '')
            }
        })

    # Build emailScripts from copy outreach
    email_scripts = []
    for idx, o in enumerate(copy_data.get('outreach', [])):
        email_scripts.append({
            'id': o.get('contact_id', f'script-{idx}'),
            'targetName': o.get('target_name', ''),
            'subject': o.get('email_subject', ''),
            'body': o.get('email_body', ''),
            'linkedinMessage': o.get('linkedin_message', '')
        })

    # Build contacts in V1 format
    v1_contacts = []
    for idx, c in enumerate(contacts_list):
        if not isinstance(c, dict):
            continue
        contact_name = c.get('name', '')
        if not contact_name:
            contact_name = f"{c.get('first_name', '')} {c.get('last_name', '')}".strip() or 'Unknown'
        v1_contacts.append({
            'id': c.get('id', f'contact-{idx}'),
            'name': contact_name,
            'role': c.get('title') or c.get('role', ''),
            'email': c.get('email', ''),
            'linkedin': c.get('linkedin_url') or c.get('linkedin', ''),
            'phone': c.get('phone', ''),
            'bio': c.get('why_they_matter') or c.get('bio_paragraph', ''),
            'highlight': 'PRIMARY' if idx == 0 else ''
        })

    rendered = {
        # Header fields
        'companyName': company_name,
        'domain': company_domain,
        'whatTheyDo': find_lead.get('what_they_do') or company_snapshot.get('description', ''),
        'theAngle': find_lead.get('the_angle', ''),
        'leadScore': find_lead.get('lead_score', 0),
        'explanation': find_lead.get('score_explanation', ''),
        'urgency': find_lead.get('timing_urgency', 'Medium'),
        'timingContext': find_lead.get('one_liner', ''),

        # Signals
        'whyNow': why_now_signals,

        # The Math (structured)
        'theMathStructured': {
            'theirReality': the_math.get('their_reality', ''),
            'theOpportunity': the_math.get('the_opportunity', ''),
            'translation': the_math.get('translation', ''),
            'bottomLine': the_math.get('bottom_line', '')
        } if the_math else None,

        # Company Intel
        'companyIntel': {
            'summary': company_deep_dive.get('description') or company_deep_dive.get('company_overview') or company_snapshot.get('description', ''),
            'numbers': [
                f"{company_deep_dive.get('employees', '')} employees" if company_deep_dive.get('employees') else None,
                company_deep_dive.get('revenue'),
                f"Founded {company_deep_dive.get('founded_year')}" if company_deep_dive.get('founded_year') else None,
            ],
            'mainlinePhones': company_deep_dive.get('mainline_phones', []),
            'generalEmails': company_deep_dive.get('general_emails', [])
        },

        # Opportunity Intelligence (V2)
        'opportunityIntelligence': find_lead.get('opportunity_intelligence'),

        # Custom Research (V2)
        'customResearch': find_lead.get('custom_research'),

        # Corporate Structure
        'corporateStructure': enrich_lead.get('corporate_structure'),

        # Network Intelligence
        'networkIntelligence': {
            'warmPathsIn': [
                {
                    'title': wp.get('name') or wp.get('title', ''),
                    'description': wp.get('title') or wp.get('role', ''),
                    'approach': wp.get('approach', ''),
                    'connectionToTargets': wp.get('linkedin_url') or wp.get('connection_to_targets', '')
                }
                for wp in (network_intel.get('warm_paths') or network_intel.get('warm_intro_paths') or [])
            ],
            'associations': network_intel.get('associations', []),
            'partnerships': network_intel.get('partnerships', []),
            'conferences': network_intel.get('conferences', []),
            'awards': network_intel.get('awards', [])
        },

        # Competitive Positioning
        'competitivePositioning': {
            'whatTheyDontKnow': competitive.get('insights_they_dont_know', []),
            'landminesToAvoid': competitive.get('landmines_to_avoid', [])
        },

        # Deal Strategy
        'dealStrategy': {
            'howTheyBuy': deal_strat.get('how_they_buy', ''),
            'uniqueValue': deal_strat.get('unique_value', [])
        },

        # Decision Strategy
        'decisionStrategy': {
            'companyType': decision_making.get('company_type', ''),
            'organizationalStructure': decision_making.get('organizational_structure', ''),
            'keyRoles': decision_making.get('key_roles', []),
            'typicalProcess': decision_making.get('typical_process', ''),
            'entryPoints': decision_making.get('entry_points', [])
        },

        # Common Objections
        'commonObjections': copy_data.get('objections', []),

        # Quick Reference
        'quickReference': {
            'conversationStarters': copy_data.get('conversation_starters', [])
        },

        # Contacts
        'contacts': v1_contacts,

        # Email Scripts
        'emailScripts': email_scripts,

        # Media
        'media': media_data,

        # Sources
        'sources': insight_data.get('sources', []),

        # Dynamic sections (if present)
        'sections': sections
    }

    # Clean up None values from companyIntel.numbers
    rendered['companyIntel']['numbers'] = [n for n in rendered['companyIntel']['numbers'] if n]

    return PublishResponse(
        success=True,
        run_id=run_id,
        production_dossier_id=production_dossier_id,
        production_batch_id=batch['id'],
        contacts_created=contacts_created,
        pipeline_version='v2',
        released_at=released_at,
        release_date=release_date,
        message=f"Dossier published to production with {contacts_created} contacts",
        rendered=rendered
    )


# ============================================================================
# DELETE PRODUCTION DOSSIER
# ============================================================================

@router.delete("/dossiers/{dossier_id}")
async def delete_production_dossier(dossier_id: str):
    """
    Delete a production dossier and its contacts.

    Use this to clean up broken/test dossiers.

    Usage:
        DELETE /columnline/dossiers/295e4b86-5b5d-4c01-8be6-8448376ab8f0
    """
    # Delete contacts first (FK constraint)
    contacts_result = repo.client.table('contacts').delete().eq('dossier_id', dossier_id).execute()
    contacts_deleted = len(contacts_result.data) if contacts_result.data else 0

    # Delete dossier
    dossier_result = repo.client.table('dossiers').delete().eq('id', dossier_id).execute()

    if not dossier_result.data:
        raise HTTPException(status_code=404, detail=f"Dossier not found: {dossier_id}")

    return {
        "success": True,
        "dossier_id": dossier_id,
        "contacts_deleted": contacts_deleted,
        "message": f"Dossier deleted with {contacts_deleted} contacts"
    }


# ============================================================================
# DEBUG DUMP ENDPOINT
# ============================================================================

@router.get("/debug/{run_id}")
async def debug_dump(run_id: str):
    """
    Get a complete debug dump of everything for a run.

    Returns ALL data from v2 pipeline AND production tables.
    Use this after /publish to verify what was generated vs stored.

    Usage:
        GET /columnline/debug/RUN_20260116_004445
    """
    dump = {
        "run_id": run_id,
        "generated_at": datetime.now().isoformat(),

        # V2 Pipeline Data
        "v2": {
            "run": None,
            "pipeline_steps": [],
            "contacts": []
        },

        # Production Data (after publish)
        "production": {
            "dossier": None,
            "contacts": [],
            "batch": None
        },

        # Summary
        "summary": {
            "status": None,
            "published": False,
            "production_dossier_id": None,
            "v2_steps_completed": 0,
            "v2_contacts_created": 0,
            "production_contacts_created": 0
        }
    }

    # 1. Get v2 run
    run = repo.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")

    dump["v2"]["run"] = run
    dump["summary"]["status"] = run.get("status")

    # 2. Get all v2 pipeline steps with full output
    steps = repo.client.table('v2_pipeline_logs').select('*').eq('run_id', run_id).order('started_at').execute()
    dump["v2"]["pipeline_steps"] = steps.data
    dump["summary"]["v2_steps_completed"] = len([s for s in steps.data if s.get('status') == 'completed'])

    # 3. Get v2 contacts (observability)
    v2_contacts = repo.get_contacts(run_id)
    dump["v2"]["contacts"] = v2_contacts
    dump["summary"]["v2_contacts_created"] = len(v2_contacts)

    # 4. Check if published - look for production_dossier_id in seed_data
    seed_data = run.get('seed_data') or {}
    production_dossier_id = seed_data.get('_production_dossier_id')

    if production_dossier_id:
        dump["summary"]["published"] = True
        dump["summary"]["production_dossier_id"] = production_dossier_id

        # 5. Get production dossier
        prod_dossier = repo.client.table('dossiers').select('*').eq('id', production_dossier_id).execute()
        if prod_dossier.data:
            dump["production"]["dossier"] = prod_dossier.data[0]

            # 6. Get production batch
            batch_id = prod_dossier.data[0].get('batch_id')
            if batch_id:
                batch = repo.client.table('batches').select('*').eq('id', batch_id).execute()
                if batch.data:
                    dump["production"]["batch"] = batch.data[0]

        # 7. Get production contacts
        prod_contacts = repo.client.table('contacts').select('*').eq('dossier_id', production_dossier_id).execute()
        dump["production"]["contacts"] = prod_contacts.data
        dump["summary"]["production_contacts_created"] = len(prod_contacts.data)

    return dump


# ============================================================================
# PREP INPUTS (COMPRESSION) ENDPOINTS
# ============================================================================

PREP_STEPS = ["compress_icp", "compress_industry", "compress_research_context", "compress_batch_strategy"]

PREP_STEP_CONFIG = {
    "compress_icp": {
        "prompt_step": "00B_COMPRESS_ICP",
        "prompt_slug": "compress-icp-config",
        "source_field": "icp_config",
        "target_field": "icp_config_compressed"
    },
    "compress_industry": {
        "prompt_step": "00B_COMPRESS_INDUSTRY",
        "prompt_slug": "compress-industry-research",
        "source_field": "industry_research",
        "target_field": "industry_research_compressed"
    },
    "compress_research_context": {
        "prompt_step": "00B_COMPRESS_RESEARCH_CONTEXT",
        "prompt_slug": "compress-research-context",
        "source_field": "research_context",
        "target_field": "research_context_compressed"
    },
    "compress_batch_strategy": {
        "prompt_step": "00B_COMPRESS_BATCH_STRATEGY",
        "prompt_slug": "compress-batch-strategy",
        "source_field": "batch_strategy",
        "target_field": "batch_strategy_compressed"
    }
}


@router.post("/clients/prep/start", response_model=PrepStartResponse)
async def start_prep(request: PrepStartRequest):
    """
    Start config compression for a client.

    Compresses ICP, industry research, research context, and batch strategy
    from verbose originals to token-efficient versions (40-60% reduction).

    Make.com usage:
        HTTP POST /columnline/clients/prep/start
        Body: {"client_id": "CLT_EXAMPLE_001"}

        Response: {
            "prep_id": "PREP_...",
            "steps": ["compress_icp", "compress_industry", ...],
            "first_step": "compress_icp"
        }
    """
    # Validate client exists
    client = repo.get_client(request.client_id)
    if not client:
        raise HTTPException(status_code=404, detail=f"Client not found: {request.client_id}")

    # Generate prep_id
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prep_id = f"PREP_{timestamp}"

    # Create prep record
    prep_data = {
        "prep_id": prep_id,
        "client_id": request.client_id,
        "status": "pending",
        "current_step": PREP_STEPS[0],
        "steps_completed": [],
        "original_icp_config": client.get('icp_config'),
        "original_industry_research": client.get('industry_research'),
        "original_research_context": client.get('research_context'),
        "original_batch_strategy": client.get('batch_strategy'),
        "started_at": datetime.now().isoformat()
    }

    repo.create_prep(prep_data)

    return PrepStartResponse(
        success=True,
        prep_id=prep_id,
        client_id=request.client_id,
        steps=PREP_STEPS,
        first_step=PREP_STEPS[0],
        message="Prep started successfully"
    )


@router.post("/clients/prep/prepare", response_model=PrepPrepareResponse)
async def prepare_prep_step(request: PrepPrepareRequest):
    """
    Prepare a compression step with prompt and full config to compress.

    Make.com usage:
        HTTP POST /columnline/clients/prep/prepare
        Body: {"prep_id": "PREP_...", "step_name": "compress_icp"}

        Response: {
            "prompt_template": "...",
            "input": {"icp_config": {...}}  // Full config to compress
        }

        Then Make.com runs the LLM with prompt_template + input
    """
    # Get prep record
    prep = repo.get_prep(request.prep_id)
    if not prep:
        raise HTTPException(status_code=404, detail=f"Prep not found: {request.prep_id}")

    # Validate step name
    if request.step_name not in PREP_STEP_CONFIG:
        raise HTTPException(status_code=400, detail=f"Invalid step name: {request.step_name}. Valid steps: {list(PREP_STEP_CONFIG.keys())}")

    step_config = PREP_STEP_CONFIG[request.step_name]

    # Get client for source config
    client = repo.get_client(prep['client_id'])
    if not client:
        raise HTTPException(status_code=404, detail=f"Client not found: {prep['client_id']}")

    # Get prompt
    prompt = repo.get_prompt_by_step(step_config['prompt_step'])
    if not prompt:
        prompt = repo.get_prompt_by_slug(step_config['prompt_slug'])
    if not prompt:
        raise HTTPException(status_code=404, detail=f"Prompt not found for step: {step_config['prompt_step']}")

    # Build input with the full config to compress
    source_config = client.get(step_config['source_field'])
    step_input = {
        step_config['source_field']: source_config,
        "client_name": client.get('client_name')
    }

    # Update prep status
    repo.update_prep(request.prep_id, {"current_step": request.step_name})

    return PrepPrepareResponse(
        prep_id=request.prep_id,
        step_name=request.step_name,
        prompt_id=prompt['prompt_id'],
        prompt_template=prompt['prompt_template'],
        model_used="gpt-4.1",
        input=step_input
    )


@router.post("/clients/prep/complete", response_model=PrepCompleteResponse)
async def complete_prep_step(request: PrepCompleteRequest):
    """
    Complete a compression step and store the compressed config.

    Make.com usage:
        HTTP POST /columnline/clients/prep/complete
        Body: {
            "prep_id": "PREP_...",
            "step_name": "compress_icp",
            "output": {{entire_openai_response}}
        }

        Response: {
            "success": true,
            "next_step": "compress_industry",  // or null if done
            "tokens_saved": 1200
        }
    """
    # Get prep record
    prep = repo.get_prep(request.prep_id)
    if not prep:
        raise HTTPException(status_code=404, detail=f"Prep not found: {request.prep_id}")

    # Validate step name
    if request.step_name not in PREP_STEP_CONFIG:
        raise HTTPException(status_code=400, detail=f"Invalid step name: {request.step_name}")

    step_config = PREP_STEP_CONFIG[request.step_name]

    # Parse LLM output
    clean_output = extract_clean_content(request.output)

    # Calculate token savings (rough estimate based on JSON size)
    original_config = prep.get(f"original_{step_config['source_field'].replace('_config', '')}_config") or prep.get(f"original_{step_config['source_field']}")
    import json
    original_tokens = len(json.dumps(original_config or {})) // 4  # Rough estimate
    compressed_tokens = len(json.dumps(clean_output or {})) // 4
    tokens_saved = max(0, original_tokens - compressed_tokens)

    # Update client with compressed field
    repo.update_client_compressed(prep['client_id'], step_config['target_field'], clean_output)

    # Update prep record
    steps_completed = prep.get('steps_completed', []) or []
    steps_completed.append(request.step_name)

    # Determine next step
    current_index = PREP_STEPS.index(request.step_name)
    next_step = PREP_STEPS[current_index + 1] if current_index + 1 < len(PREP_STEPS) else None

    # Update prep
    prep_updates = {
        "steps_completed": steps_completed,
        f"compressed_{step_config['source_field']}": clean_output
    }
    if next_step:
        prep_updates["current_step"] = next_step
    else:
        prep_updates["status"] = "completed"
        prep_updates["completed_at"] = datetime.now().isoformat()

    repo.update_prep(request.prep_id, prep_updates)

    return PrepCompleteResponse(
        success=True,
        prep_id=request.prep_id,
        step_name=request.step_name,
        next_step=next_step,
        tokens_saved=tokens_saved,
        message=f"Step {request.step_name} completed" + (f", next: {next_step}" if next_step else ", all steps done")
    )


# ============================================================================
# CLIENT ONBOARDING ENDPOINTS
# ============================================================================

ONBOARD_STEPS = ["consolidate_intake", "generate_configs"]


@router.post("/clients/onboard/start", response_model=OnboardStartResponse)
async def start_onboarding(request: OnboardStartRequest):
    """
    Start client onboarding from raw intake data.

    Takes transcripts, website, narrative, materials and generates
    the 4 client configs (ICP, industry, research_context, batch_strategy).

    Make.com usage:
        HTTP POST /columnline/clients/onboard/start
        Body: {
            "client_name": "Acme Construction",
            "intake_data": {
                "transcripts": "...",
                "website": "acme.com",
                "narrative": "...",
                "materials": "..."
            }
        }

        Response: {
            "onboarding_id": "ONB_...",
            "client_id": "CLT_...",
            "steps": ["consolidate_intake", "generate_configs"],
            "first_step": "consolidate_intake"
        }
    """
    # Generate IDs
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    onboarding_id = f"ONB_{timestamp}"

    # Create client_id from client name (sanitized)
    import re
    sanitized_name = re.sub(r'[^a-zA-Z0-9]', '_', request.client_name.upper())[:20]
    client_id = f"CLT_{sanitized_name}_{timestamp[-6:]}"

    # Create client record first
    client_data = {
        "client_id": client_id,
        "client_name": request.client_name,
        "status": "onboarding"
    }
    repo.create_client(client_data)

    # Create onboarding record
    onboarding_data = {
        "onboarding_id": onboarding_id,
        "client_name": request.client_name,
        "client_id": client_id,
        "status": "in_progress",
        "intake_data": request.intake_data,
        "current_step": ONBOARD_STEPS[0],
        "steps_completed": [],
        "started_at": datetime.now().isoformat()
    }

    repo.create_onboarding(onboarding_data)

    return OnboardStartResponse(
        success=True,
        onboarding_id=onboarding_id,
        client_id=client_id,
        steps=ONBOARD_STEPS,
        first_step=ONBOARD_STEPS[0],
        message="Onboarding started successfully"
    )


@router.post("/clients/onboard/prepare", response_model=OnboardPrepareResponse)
async def prepare_onboarding_step(request: OnboardPrepareRequest):
    """
    Prepare an onboarding step with prompt and inputs.

    Step 1 (consolidate_intake): Process all raw inputs into unified format
    Step 2 (generate_configs): Generate all 4 configs from consolidated info

    Make.com usage:
        HTTP POST /columnline/clients/onboard/prepare
        Body: {"onboarding_id": "ONB_...", "step_name": "consolidate_intake"}

        Response: {
            "prompt_template": "...",
            "input": {...}
        }
    """
    # Get onboarding record
    onboarding = repo.get_onboarding(request.onboarding_id)
    if not onboarding:
        raise HTTPException(status_code=404, detail=f"Onboarding not found: {request.onboarding_id}")

    # Validate step name
    if request.step_name not in ONBOARD_STEPS:
        raise HTTPException(status_code=400, detail=f"Invalid step name: {request.step_name}. Valid steps: {ONBOARD_STEPS}")

    # Get prompt based on step
    if request.step_name == "consolidate_intake":
        prompt = repo.get_prompt_by_step("00A_CONSOLIDATE_INTAKE")
        if not prompt:
            prompt = repo.get_prompt_by_slug("consolidate-intake")

        step_input = {
            "client_name": onboarding.get('client_name'),
            "transcripts": onboarding.get('intake_data', {}).get('transcripts'),
            "website": onboarding.get('intake_data', {}).get('website'),
            "narrative": onboarding.get('intake_data', {}).get('narrative'),
            "pre_research": onboarding.get('intake_data', {}).get('pre_research'),
            "materials": onboarding.get('intake_data', {}).get('materials')
        }
        # Remove None values
        step_input = {k: v for k, v in step_input.items() if v is not None}

    elif request.step_name == "generate_configs":
        prompt = repo.get_prompt_by_step("00A_GENERATE_CONFIGS")
        if not prompt:
            prompt = repo.get_prompt_by_slug("generate-configs")

        step_input = {
            "client_name": onboarding.get('client_name'),
            "consolidated_info": onboarding.get('consolidated_info', {})
        }

    if not prompt:
        raise HTTPException(status_code=404, detail=f"Prompt not found for step: {request.step_name}. You may need to create it first.")

    # Update current step
    repo.update_onboarding(request.onboarding_id, {"current_step": request.step_name})

    return OnboardPrepareResponse(
        onboarding_id=request.onboarding_id,
        step_name=request.step_name,
        prompt_id=prompt['prompt_id'],
        prompt_template=prompt['prompt_template'],
        model_used="gpt-4.1",
        input=step_input
    )


@router.post("/clients/onboard/complete", response_model=OnboardCompleteResponse)
async def complete_onboarding_step(request: OnboardCompleteRequest):
    """
    Complete an onboarding step and store results.

    Step 1 output: consolidated_info (stored for step 2)
    Step 2 output: All 4 configs (stored to v2_clients)

    Make.com usage:
        HTTP POST /columnline/clients/onboard/complete
        Body: {
            "onboarding_id": "ONB_...",
            "step_name": "consolidate_intake",
            "output": {{entire_openai_response}}
        }

        Response: {
            "success": true,
            "next_step": "generate_configs"  // or null if done
        }
    """
    # Get onboarding record
    onboarding = repo.get_onboarding(request.onboarding_id)
    if not onboarding:
        raise HTTPException(status_code=404, detail=f"Onboarding not found: {request.onboarding_id}")

    # Validate step name
    if request.step_name not in ONBOARD_STEPS:
        raise HTTPException(status_code=400, detail=f"Invalid step name: {request.step_name}")

    # Parse LLM output
    clean_output = extract_clean_content(request.output)

    # Update based on step
    steps_completed = onboarding.get('steps_completed', []) or []
    steps_completed.append(request.step_name)

    current_index = ONBOARD_STEPS.index(request.step_name)
    next_step = ONBOARD_STEPS[current_index + 1] if current_index + 1 < len(ONBOARD_STEPS) else None

    configs_generated = None

    if request.step_name == "consolidate_intake":
        # Store consolidated info for next step
        repo.update_onboarding(request.onboarding_id, {
            "consolidated_info": clean_output,
            "steps_completed": steps_completed,
            "current_step": next_step
        })

    elif request.step_name == "generate_configs":
        # Extract and store all 4 configs to v2_clients
        client_updates = {}

        if isinstance(clean_output, dict):
            if 'icp_config' in clean_output:
                client_updates['icp_config'] = clean_output['icp_config']
            if 'industry_research' in clean_output:
                client_updates['industry_research'] = clean_output['industry_research']
            if 'research_context' in clean_output:
                client_updates['research_context'] = clean_output['research_context']
            if 'batch_strategy' in clean_output:
                client_updates['batch_strategy'] = clean_output['batch_strategy']

        # Update client with generated configs
        if client_updates:
            client_updates['status'] = 'active'  # Client is now fully onboarded
            repo.update_client(onboarding['client_id'], client_updates)
            configs_generated = list(client_updates.keys())
            configs_generated = [c for c in configs_generated if c != 'status']

        # Store generated configs in onboarding record too
        repo.update_onboarding(request.onboarding_id, {
            "generated_icp_config": clean_output.get('icp_config') if isinstance(clean_output, dict) else None,
            "generated_industry_research": clean_output.get('industry_research') if isinstance(clean_output, dict) else None,
            "generated_research_context": clean_output.get('research_context') if isinstance(clean_output, dict) else None,
            "generated_batch_strategy": clean_output.get('batch_strategy') if isinstance(clean_output, dict) else None,
            "steps_completed": steps_completed,
            "status": "completed",
            "completed_at": datetime.now().isoformat()
        })

    return OnboardCompleteResponse(
        success=True,
        onboarding_id=request.onboarding_id,
        step_name=request.step_name,
        next_step=next_step,
        configs_generated=configs_generated,
        message=f"Step {request.step_name} completed" + (f", next: {next_step}" if next_step else ", onboarding complete")
    )
