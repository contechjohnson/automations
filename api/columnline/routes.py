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
    StepTransitionRequest, StepTransitionResponse,
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
    all_claims_steps = repo.client.table('v2_pipeline_steps').select('*').eq('run_id', run_id).eq('step_name', 'CLAIMS_EXTRACTION').eq('status', 'completed').execute()

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
            narrative_step = repo.client.table('v2_pipeline_steps').select('*').eq('run_id', run_id).eq('step_name', source_step_name).eq('status', 'completed').execute()

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
            signal_claims_step = repo.client.table('v2_pipeline_steps').select('*').eq('run_id', request.run_id).eq('step_name', 'CLAIMS_EXTRACTION').eq('status', 'completed').execute()

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
            all_claims_steps = repo.client.table('v2_pipeline_steps').select('*').eq('run_id', request.run_id).eq('step_name', 'CLAIMS_EXTRACTION').eq('status', 'completed').execute()

            for claims_step in all_claims_steps.data:
                step_input_data = claims_step.get('input', {})
                claims_output = extract_clean_content(claims_step.get('output'))

                if '2_signal_discovery_output' in step_input_data:
                    step_input["signal_discovery_claims"] = claims_output
                elif '3_entity_research_output' in step_input_data:
                    step_input["entity_research_claims"] = claims_output
                elif '4_contact_discovery_output' in step_input_data:
                    step_input["contact_discovery_claims"] = claims_output

        # Insight needs ALL individual claims (not merged yet)
        if step_name == "07B_INSIGHT":
            # Find all completed claims extraction steps
            all_claims_steps = repo.client.table('v2_pipeline_steps').select('*').eq('run_id', request.run_id).eq('step_name', 'CLAIMS_EXTRACTION').eq('status', 'completed').execute()

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

        # Dossier Plan needs context pack + ALL individual claims
        if step_name == "9_DOSSIER_PLAN":
            context_pack_output = repo.get_completed_step(request.run_id, "CONTEXT_PACK")
            if context_pack_output:
                step_input["context_pack"] = extract_clean_content(context_pack_output.get('output'))

            # Pass ALL individual claims (not merged)
            all_claims = fetch_all_individual_claims(repo, request.run_id)
            step_input.update(all_claims)

        # Enrich Contacts needs context pack from 7B + ALL individual claims
        if step_name == "6_ENRICH_CONTACTS":
            context_pack_output = repo.get_completed_step(request.run_id, "CONTEXT_PACK")
            if context_pack_output:
                step_input["context_pack"] = extract_clean_content(context_pack_output.get('output'))

            # Pass ALL individual claims (not merged - merged was bottleneck with only 24 claims)
            all_claims = fetch_all_individual_claims(repo, request.run_id)
            step_input.update(all_claims)

        # Individual contact enrichment needs ALL individual claims (contact_data passed by Make.com)
        if step_name == "6_ENRICH_CONTACT_INDIVIDUAL":
            # Pass ALL individual claims (not merged)
            all_claims = fetch_all_individual_claims(repo, request.run_id)
            step_input.update(all_claims)

        # Media enrichment needs context pack + ALL individual claims
        if step_name == "8_MEDIA":
            # Fetch context pack
            context_pack_output = repo.get_completed_step(request.run_id, "CONTEXT_PACK")
            if context_pack_output:
                step_input["context_pack"] = extract_clean_content(context_pack_output.get('output'))

            # Pass ALL individual claims (not merged)
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

        # Merge Claims needs ALL claims including insight claims
        if step_name == "MERGE_CLAIMS":
            # Find all completed claims extraction steps
            all_claims_steps = repo.client.table('v2_pipeline_steps').select('*').eq('run_id', request.run_id).eq('step_name', 'CLAIMS_EXTRACTION').eq('status', 'completed').execute()

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
            "10B_COPY_CLIENT_OVERRIDE": "gpt-4.1"
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
    contacts_array = None
    media_data = None

    for output_item in request.outputs:
        # Find the pipeline step
        step = None

        # If step_id provided, find by ID directly (for parallel steps with same name)
        if output_item.step_id:
            result = repo.client.table('v2_pipeline_steps').select('*').eq('step_id', output_item.step_id).eq('run_id', request.run_id).execute()
            if result.data:
                step = result.data[0]
        else:
            # Otherwise use step_name (existing logic)
            step = repo.get_completed_step(request.run_id, output_item.step_name)

            # If not found, try to find the "running" step
            if not step:
                result = repo.client.table('v2_pipeline_steps').select('*').eq('run_id', request.run_id).eq('step_name', output_item.step_name).eq('status', 'running').execute()
                if result.data:
                    step = result.data[0]

        if not step:
            raise HTTPException(status_code=404, detail=f"Step not found: {output_item.step_id or output_item.step_name}")

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
    result = repo.client.table('v2_pipeline_steps').select('*').eq('run_id', request.run_id).eq('step_name', request.completed_step_name).eq('status', 'running').execute()

    if not result.data:
        # Not in "running" status - try to find it with any status
        result = repo.client.table('v2_pipeline_steps').select('*').eq('run_id', request.run_id).eq('step_name', request.completed_step_name).execute()

    # If we found the step, update it to completed
    if result.data:
        completed_step = result.data[0]
        repo.update_pipeline_step(completed_step['step_id'], {
            "status": "completed",
            "output": parsed['full_output'],  # Store full response
            "tokens_used": parsed['tokens_used'],
            "runtime_seconds": parsed['runtime_seconds'],
            "completed_at": datetime.now().isoformat()
        })
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
        all_claims_steps = repo.client.table('v2_pipeline_steps').select('*').eq('run_id', request.run_id).eq('step_name', 'CLAIMS_EXTRACTION').eq('status', 'completed').execute()

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
            all_claims_steps = repo.client.table('v2_pipeline_steps').select('*').eq('run_id', request.run_id).eq('step_name', 'CLAIMS_EXTRACTION').eq('status', 'completed').execute()

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
        # Contact discovery needs the entity context pack (just completed)
        step_input["entity_context_pack"] = clean_output

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
        all_claims_steps = repo.client.table('v2_pipeline_steps').select('*').eq('run_id', request.run_id).eq('step_name', 'CLAIMS_EXTRACTION').eq('status', 'completed').execute()

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
        all_claims_steps = repo.client.table('v2_pipeline_steps').select('*').eq('run_id', request.run_id).eq('step_name', 'CLAIMS_EXTRACTION').eq('status', 'completed').execute()

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
        "10B_COPY_CLIENT_OVERRIDE": "gpt-4.1"
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
            find_lead['primary_buying_signal'] = clean.get('primary_buying_signal') or {}
            # Additional signals go to enrich_lead

    # From WRITER_OPPORTUNITY (10_WRITER_OPPORTUNITY)
    opp_output = step_outputs.get('10_WRITER_OPPORTUNITY', {})
    if opp_output:
        clean = extract_clean_content(opp_output.get('output', {}))
        if isinstance(clean, dict):
            find_lead['company_snapshot'] = clean.get('company_snapshot') or {}

    # Add company_name from seed
    if seed_data:
        find_lead['company_name'] = seed_data.get('company_name') or seed_data.get('name') or ''

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

    return enrich_lead


def assemble_insight(step_outputs: dict) -> dict:
    """Assemble insight JSONB from WRITER_STRATEGY output."""
    insight = {
        'the_math': {},
        'deal_strategy': {},
        'competitive_positioning': {},
        'decision_making_process': {},
        'sources': []
    }

    # From WRITER_STRATEGY (10_WRITER_STRATEGY)
    strategy_output = step_outputs.get('10_WRITER_STRATEGY', {})
    if strategy_output:
        clean = extract_clean_content(strategy_output.get('output', {}))
        if isinstance(clean, dict):
            insight['the_math'] = clean.get('the_math') or {}
            insight['deal_strategy'] = clean.get('deal_strategy') or {}
            insight['competitive_positioning'] = clean.get('competitive_positioning') or {}
            insight['decision_making_process'] = clean.get('decision_making_process') or {}

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
            copy_data['objections'] = clean.get('objections') or []
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
    steps = repo.client.table('v2_pipeline_steps').select('*').eq('run_id', run_id).eq('status', 'completed').execute()
    for step in steps.data:
        step_outputs[step['step_name']] = step

    # Validate we have minimum required outputs
    required_writers = ['10_WRITER_INTRO', '10_WRITER_SIGNALS']  # At minimum need these
    missing_writers = [w for w in required_writers if w not in step_outputs]
    if missing_writers:
        # Check if we have any writer outputs at all
        writer_steps = [s for s in step_outputs.keys() if s.startswith('10_WRITER')]
        if not writer_steps:
            raise HTTPException(
                status_code=400,
                detail=f"No writer outputs found for run {run_id}. Run the writers first before publishing."
            )
        # Log warning but continue - may have partial data
        print(f"Warning: Missing some writer outputs for {run_id}: {missing_writers}")

    # 5. Get seed data (handle None explicitly)
    seed_data = run.get('seed_data') or {}

    # 6. Assemble JSONB columns
    find_lead = assemble_find_lead(step_outputs, seed_data)
    enrich_lead = assemble_enrich_lead(step_outputs)
    insight_data = assemble_insight(step_outputs)
    media_data = assemble_media(step_outputs)

    # 7. Insert contacts and build ID map
    contact_id_map = {}
    contacts_created = 0

    # Get contacts from 6_ENRICH_CONTACTS output
    contacts_step = step_outputs.get('6_ENRICH_CONTACTS', {})
    contacts_list = []
    if contacts_step:
        clean = extract_clean_content(contacts_step.get('output', {}))
        if isinstance(clean, dict):
            contacts_list = clean.get('contacts', clean.get('enriched_contacts', clean.get('key_contacts', [])))
        elif isinstance(clean, list):
            contacts_list = clean

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

        contact_data = {
            'dossier_id': production_dossier_id,
            'name': contact_name,
            'first_name': contact.get('first_name'),
            'last_name': contact.get('last_name'),
            'title': contact.get('title') or contact.get('role'),
            'email': contact.get('email'),
            'phone': contact.get('phone'),
            'linkedin_url': contact.get('linkedin_url') or contact.get('linkedin'),
            'bio_paragraph': contact.get('bio_paragraph') or contact.get('bio') or contact.get('why_they_matter', ''),
            'is_primary': idx == 0,  # First contact is primary
            'source': contact.get('source', 'v2_pipeline'),
            'created_at': datetime.now().isoformat()
        }

        # Insert contact
        try:
            result = repo.client.table('contacts').insert(contact_data).execute()
            if result.data:
                prod_contact_id = result.data[0]['id']
                contact_id_map[idx] = prod_contact_id
                contacts_created += 1

                # Build outreach entry for this contact
                # Handle various formats for email/linkedin copy
                email_copy = contact.get('email_copy', {})
                if isinstance(email_copy, str):
                    email_subject = ''
                    email_body = email_copy
                else:
                    email_subject = contact.get('email_subject') or email_copy.get('subject', '')
                    email_body = contact.get('email_body') or email_copy.get('body', '')

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

    return PublishResponse(
        success=True,
        run_id=run_id,
        production_dossier_id=production_dossier_id,
        production_batch_id=batch['id'],
        contacts_created=contacts_created,
        pipeline_version='v2',
        released_at=released_at,
        release_date=release_date,
        message=f"Dossier published to production with {contacts_created} contacts"
    )
