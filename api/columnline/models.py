"""
Pydantic models for Columnline API

Request/response schemas for clean API integration.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================================
# RUN MODELS
# ============================================================================

class RunStartRequest(BaseModel):
    """Start a new dossier run - main pipeline input"""
    client_id: str
    seed_data: Optional[Dict[str, Any]] = Field(default=None, description="Any data to start the run - company name, signal, URL, or any JSON structure")
    triggered_by: str = Field(default="make.com", description="Source that triggered the run")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "client_id": "CLT_EXAMPLE_001",
                    "seed_data": {
                        "company_name": "Acme Construction",
                        "signal": "Permit filed for $5M expansion"
                    }
                },
                {
                    "client_id": "CLT_EXAMPLE_001",
                    "seed_data": {
                        "linkedin_url": "https://linkedin.com/company/acme"
                    }
                },
                {
                    "client_id": "CLT_EXAMPLE_001",
                    "seed_data": {
                        "custom_field": "any data structure"
                    }
                },
                {
                    "client_id": "CLT_EXAMPLE_001"
                }
            ]
        }


class RunStartResponse(BaseModel):
    """Response from starting a run"""
    success: bool = True
    run_id: str
    dossier_id: str
    client_id: str
    started_at: datetime
    message: str = "Run created successfully"


class RunCreate(BaseModel):
    """Create a new dossier run (internal use)"""
    run_id: str
    client_id: str
    status: str = "running"
    seed_data: Optional[Dict[str, Any]] = None
    dossier_id: Optional[str] = None
    triggered_by: Optional[str] = None
    config_snapshot: Optional[Dict[str, Any]] = None


class RunUpdate(BaseModel):
    """Update run status"""
    status: Optional[str] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    dossier_id: Optional[str] = None


class RunStatus(BaseModel):
    """Run status response"""
    run_id: str
    status: str
    completed_steps: List[str]
    current_step: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


# ============================================================================
# PIPELINE STEP MODELS
# ============================================================================

class PipelineStepCreate(BaseModel):
    """Create/log a pipeline step"""
    step_id: str
    run_id: str
    prompt_id: str
    step_name: str
    status: str = "running"
    input: Optional[Dict[str, Any]] = None
    output: Optional[Dict[str, Any]] = None
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None
    runtime_seconds: Optional[float] = None
    started_at: Optional[datetime] = None
    error_message: Optional[str] = None


class PipelineStepUpdate(BaseModel):
    """Update pipeline step (for dual-write pattern)"""
    status: Optional[str] = None
    output: Optional[Dict[str, Any]] = None
    tokens_used: Optional[int] = None
    runtime_seconds: Optional[float] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class PipelineStepComplete(BaseModel):
    """Response for checking step completion"""
    found: bool
    step: Optional[Dict[str, Any]] = None


# ============================================================================
# CLAIMS MODELS
# ============================================================================

class ClaimsCreate(BaseModel):
    """Store claims from a research step"""
    run_id: str
    step_id: str
    step_name: str
    claims_json: List[Dict[str, Any]]


# ============================================================================
# CONFIG RESPONSE MODELS
# ============================================================================

class ClientConfig(BaseModel):
    """Client configuration response"""
    client_id: str
    client_name: str
    status: str
    icp_config_compressed: Optional[Dict[str, Any]] = None
    industry_research_compressed: Optional[Dict[str, Any]] = None
    research_context_compressed: Optional[Dict[str, Any]] = None
    client_specific_research: Optional[Dict[str, Any]] = None
    drip_schedule: Optional[Dict[str, Any]] = None


class PromptConfig(BaseModel):
    """Prompt configuration response"""
    prompt_id: str
    prompt_slug: str
    stage: Optional[str] = None
    step: Optional[str] = None
    prompt_template: str
    produce_claims: bool = False
    context_pack_produced: bool = False
    variables_used: Optional[List[str]] = None
    variables_produced: Optional[List[str]] = None


class ConfigsResponse(BaseModel):
    """Combined configs response for sub-scenarios"""
    client: ClientConfig
    prompts: List[PromptConfig]


# ============================================================================
# OUTPUTS RESPONSE MODELS
# ============================================================================

class StepOutput(BaseModel):
    """Single step output"""
    step_id: str
    output: Dict[str, Any]
    completed_at: datetime
    tokens_used: Optional[int] = None
    runtime_seconds: Optional[float] = None


class OutputsResponse(BaseModel):
    """Outputs from previous steps"""
    run_id: str
    outputs: Dict[str, StepOutput]  # Key: step_name


# ============================================================================
# GENERIC SUCCESS RESPONSE
# ============================================================================

class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


# ============================================================================
# BATCH STEP EXECUTION MODELS
# ============================================================================

class StepPrepareRequest(BaseModel):
    """Prepare inputs for one or more steps"""
    run_id: str
    client_id: str
    dossier_id: str
    step_names: List[str] = Field(..., description="Steps to prepare (e.g., ['1_SEARCH_BUILDER', '2_SIGNAL_DISCOVERY'])")


class PreparedStep(BaseModel):
    """Single prepared step with input ready"""
    step_id: str
    step_name: str
    prompt_id: str
    prompt_slug: str
    prompt_template: str
    model_used: str
    input: Dict[str, Any]
    produce_claims: bool


class StepPrepareResponse(BaseModel):
    """Response with all prepared steps"""
    run_id: str
    steps: List[PreparedStep]


class StepOutputItem(BaseModel):
    """Single step output to store - pass full OpenAI response, we'll parse it"""
    step_name: str
    output: Any = Field(..., description="Full OpenAI response - we extract tokens/runtime automatically")
    step_id: Optional[str] = None  # Optional - specify exact step to complete (useful for parallel steps with same name)
    tokens_used: Optional[int] = None  # Optional - will be extracted if not provided
    runtime_seconds: Optional[float] = None  # Optional - will be extracted if not provided


class StepCompleteRequest(BaseModel):
    """Store outputs for completed steps"""
    run_id: str
    outputs: List[StepOutputItem]


class StepCompleteResponse(BaseModel):
    """Response after storing outputs"""
    success: bool = True
    run_id: str
    steps_completed: List[str]
    message: str = "Steps completed successfully"
    contacts: Optional[List[Dict[str, Any]]] = None  # For 6_ENRICH_CONTACTS step - array for Make.com iteration
    media_data: Optional[Dict[str, Any]] = None  # For 8_MEDIA step - complete media output with image_assets array


class StepTransitionRequest(BaseModel):
    """Store previous step output and prepare next step - ONE CALL"""
    run_id: str
    client_id: str
    dossier_id: str

    # Previous step (to complete)
    completed_step_name: str
    completed_step_output: Any = Field(..., description="Full OpenAI API response (we'll parse it)")

    # Next step (to prepare)
    next_step_name: str


class StepTransitionResponse(BaseModel):
    """Response with completed step stored and next step prepared"""
    success: bool = True
    run_id: str

    # What was stored
    completed_step: str
    tokens_used: int
    runtime_seconds: float

    # What's prepared for next
    next_step: PreparedStep


# ============================================================================
# BATCH COMPOSER MODELS
# ============================================================================

class BatchStartRequest(BaseModel):
    """Start a new batch for seed direction generation"""
    client_id: str
    batch_size: Optional[int] = Field(default=None, description="Number of directions to generate (defaults to batch_strategy setting)")

    class Config:
        json_schema_extra = {
            "example": {
                "client_id": "CLT_EXAMPLE_001",
                "batch_size": 10
            }
        }


class BatchStartResponse(BaseModel):
    """Response from starting a batch"""
    success: bool = True
    batch_id: str
    client_id: str
    thread_id: str
    batch_number: int
    message: str = "Batch created successfully"


class BatchPrepareRequest(BaseModel):
    """Prepare inputs for batch composer LLM call"""
    batch_id: str


class BatchPrepareResponse(BaseModel):
    """Prepared batch with prompt and inputs ready for LLM"""
    batch_id: str
    prompt_id: str
    prompt_template: str
    model_used: str = "gpt-4.1"
    input: Dict[str, Any]  # Contains compressed configs + recent_directions + existing_leads


class BatchCompleteRequest(BaseModel):
    """Complete batch with LLM output"""
    batch_id: str
    output: Any = Field(..., description="Full OpenAI response with directions")


class BatchDirection(BaseModel):
    """Single direction/hint for pipeline"""
    project_type: str
    geography: str
    signal_type: Optional[str] = None
    hint: str


class BatchCompleteResponse(BaseModel):
    """Response after storing batch output"""
    success: bool = True
    batch_id: str
    directions: List[BatchDirection]
    directions_count: int
    distribution_achieved: Optional[Dict[str, int]] = None
    message: str = "Batch completed successfully"


# ============================================================================
# PREP INPUTS (COMPRESSION) MODELS
# ============================================================================

class PrepStartRequest(BaseModel):
    """Start config compression for a client"""
    client_id: str


class PrepStartResponse(BaseModel):
    """Response from starting prep inputs"""
    success: bool = True
    prep_id: str
    client_id: str
    steps: List[str]
    first_step: str
    message: str = "Prep started successfully"


class PrepPrepareRequest(BaseModel):
    """Prepare a compression step"""
    prep_id: str
    step_name: str = Field(..., description="compress_icp, compress_industry, compress_research_context, or compress_batch_strategy")


class PrepPrepareResponse(BaseModel):
    """Prepared compression step with prompt and input"""
    prep_id: str
    step_name: str
    prompt_id: str
    prompt_template: str
    model_used: str = "gpt-4.1"
    input: Dict[str, Any]  # Contains full config to compress


class PrepCompleteRequest(BaseModel):
    """Complete a compression step"""
    prep_id: str
    step_name: str
    output: Any = Field(..., description="Full OpenAI response with compressed config")


class PrepCompleteResponse(BaseModel):
    """Response after storing compressed config"""
    success: bool = True
    prep_id: str
    step_name: str
    next_step: Optional[str] = None  # None if done
    tokens_saved: Optional[int] = None
    message: str = "Step completed successfully"


# ============================================================================
# CLIENT ONBOARDING MODELS
# ============================================================================

class OnboardStartRequest(BaseModel):
    """Start client onboarding"""
    client_name: str
    intake_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Raw intake data: transcripts, website, narrative, pre_research, materials (all optional)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "client_name": "Acme Construction",
                "intake_data": {
                    "transcripts": "Sales call transcript...",
                    "website": "acme-construction.com",
                    "narrative": "Acme is a commercial construction firm...",
                    "materials": "PDF content or notes..."
                }
            }
        }


class OnboardStartResponse(BaseModel):
    """Response from starting onboarding"""
    success: bool = True
    onboarding_id: str
    client_id: str
    steps: List[str]
    first_step: str
    message: str = "Onboarding started successfully"


class OnboardPrepareRequest(BaseModel):
    """Prepare an onboarding step"""
    onboarding_id: str
    step_name: str = Field(..., description="consolidate_intake or generate_configs")


class OnboardPrepareResponse(BaseModel):
    """Prepared onboarding step with prompt and input"""
    onboarding_id: str
    step_name: str
    prompt_id: str
    prompt_template: str
    model_used: str = "gpt-4.1"
    input: Dict[str, Any]


class OnboardCompleteRequest(BaseModel):
    """Complete an onboarding step"""
    onboarding_id: str
    step_name: str
    output: Any = Field(..., description="Full OpenAI response")


class OnboardCompleteResponse(BaseModel):
    """Response after completing onboarding step"""
    success: bool = True
    onboarding_id: str
    step_name: str
    next_step: Optional[str] = None  # None if done
    configs_generated: Optional[List[str]] = None  # Set on final step
    message: str = "Step completed successfully"


# ============================================================================
# PUBLISH TO PRODUCTION MODELS
# ============================================================================

class PublishRequest(BaseModel):
    """Publish a v2 dossier to production tables"""
    release_date: Optional[str] = Field(
        default=None,
        description="Scheduled release date (YYYY-MM-DD). If not provided, releases immediately."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "release_date": "2026-01-20"
            }
        }


class PublishResponse(BaseModel):
    """Response from publishing to production"""
    success: bool = True
    run_id: str
    production_dossier_id: str
    production_batch_id: str
    contacts_created: int
    pipeline_version: str = "v2"
    released_at: Optional[str] = None
    release_date: Optional[str] = None
    message: str = "Dossier published to production successfully"
    rendered: Optional[dict] = Field(
        default=None,
        description="Full rendered dossier data as it appears in production"
    )
