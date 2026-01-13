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

class RunCreate(BaseModel):
    """Create a new dossier run"""
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
