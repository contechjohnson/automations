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
