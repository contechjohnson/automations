"""
Automations API - FastAPI endpoints with async deep research support
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime
import os
import sys

# Add workers to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = FastAPI(title="Automations API")


class PromptRequest(BaseModel):
    prompt_name: str
    variables: Optional[dict] = None
    model: str = "gpt-4.1"
    background: bool = False  # For deep research


class ResearchPollRequest(BaseModel):
    response_id: str


@app.get("/")
def root():
    return {"status": "ok", "service": "automations-api", "timestamp": datetime.now().isoformat()}


@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/prompts")
def list_prompts():
    """List all available prompt templates."""
    from pathlib import Path
    prompts_dir = Path("/opt/automations/prompts")
    
    if not prompts_dir.exists():
        return {"prompts": [], "count": 0}
    
    prompts = []
    for f in prompts_dir.glob("*.md"):
        prompts.append({
            "name": f.stem,
            "path": str(f),
            "size_bytes": f.stat().st_size
        })
    
    return {"prompts": prompts, "count": len(prompts)}


@app.post("/test/prompt")
def test_prompt(request: PromptRequest):
    """
    Test a prompt template with variables.
    For deep research models, set background=True to get a response_id for polling.
    """
    from workers.ai import prompt, DEEP_RESEARCH_MODELS
    
    try:
        # Check if this is a deep research model
        is_deep_research = (
            request.model in DEEP_RESEARCH_MODELS or 
            request.model.startswith("o4-mini-deep") or 
            request.model.startswith("o3-deep")
        )
        
        if is_deep_research and not request.background:
            # Force background mode for deep research (takes too long for sync)
            return {
                "error": "Deep research models require background=True due to long execution time (5-10 min)",
                "hint": "Set background=True, then poll /research/poll with the response_id"
            }
        
        result = prompt(
            name=request.prompt_name,
            variables=request.variables,
            model=request.model,
        )
        
        return {
            "status": "completed" if not request.background else "submitted",
            "prompt_name": result["prompt_name"],
            "model": result["model"],
            "elapsed_seconds": result.get("elapsed_seconds"),
            "output": result.get("output"),
            "response_id": result.get("response_id"),  # For background mode
            "input_length": len(result.get("input", "")),
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/research/start")
def start_research(request: PromptRequest):
    """
    Start a deep research task in background mode.
    Returns a response_id for polling.
    """
    from workers.ai import prompt
    
    try:
        # Override model to deep research
        if not request.model.startswith("o"):
            request.model = "o4-mini-deep-research"
        
        result = prompt(
            name=request.prompt_name,
            variables=request.variables,
            model=request.model,
        )
        
        return {
            "status": "submitted",
            "response_id": result.get("response_id"),
            "model": result["model"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/research/poll")
def poll_research(request: ResearchPollRequest):
    """
    Poll for deep research completion.
    """
    from workers.ai import poll_research as poll_fn
    
    try:
        result = poll_fn(request.response_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workers")
def list_workers():
    """List available worker functions."""
    return {
        "workers": [
            {
                "name": "research.entity_research",
                "description": "Deep research on a company using o4-mini-deep-research",
                "params": ["client_info", "target_info"]
            }
        ]
    }
