"""
Prompt endpoints for Make.com integration
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
from .repository import V2Repository

router = APIRouter()


def get_repo() -> V2Repository:
    return V2Repository()


@router.get("/v2/prompts/{prompt_id}")
def get_prompt(prompt_id: str, version: Optional[int] = None):
    """
    Get prompt content for Make.com.
    Returns prompt metadata with content from specified version (or current version if not specified).
    """
    repo = get_repo()
    prompt = repo.get_prompt_with_content(prompt_id, version)
    
    if not prompt:
        raise HTTPException(status_code=404, detail=f"Prompt {prompt_id} not found")
    
    return {
        "prompt_id": prompt["prompt_id"],
        "name": prompt["name"],
        "stage": prompt["stage"],
        "content": prompt.get("content", ""),
        "system_prompt": prompt.get("system_prompt"),
        "model": prompt.get("model", "gpt-4.1"),
        "temperature": float(prompt.get("temperature", 0.7)),
        "version": prompt.get("current_version", 1),
        "metadata": {
            "produces_claims": prompt.get("produces_claims", False),
            "merges_claims": prompt.get("merges_claims", False),
            "produces_context_pack": prompt.get("produces_context_pack", False),
            "execution_mode": prompt.get("execution_mode", "sync"),
        }
    }


@router.get("/v2/prompts/{prompt_id}/version")
def get_prompt_version(prompt_id: str, version_number: int):
    """
    Get a specific version of a prompt.
    """
    repo = get_repo()
    version = repo.get_prompt_version(prompt_id, version_number)
    
    if not version:
        raise HTTPException(status_code=404, detail=f"Prompt {prompt_id} version {version_number} not found")
    
    return {
        "prompt_id": version["prompt_id"],
        "version_number": version["version_number"],
        "content": version["content"],
        "system_prompt": version.get("system_prompt"),
        "created_at": version["created_at"],
        "change_notes": version.get("change_notes"),
    }

