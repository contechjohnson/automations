"""
Client configuration endpoints for Make.com integration
"""
from fastapi import APIRouter, HTTPException
from .repository import V2Repository

router = APIRouter()


def get_repo() -> V2Repository:
    return V2Repository()


@router.get("/v2/clients/{client_id}/config")
def get_client_config(client_id: str):
    """
    Get all client configurations (ICP, Industry, Research Context).
    Returns complete config object for Make.com.
    """
    repo = get_repo()
    client = repo.get_client(client_id)
    
    if not client:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")
    
    return {
        "client_id": client["id"],
        "slug": client["slug"],
        "name": client["name"],
        "icp_config": client.get("icp_config", {}),
        "industry_research": client.get("industry_research", {}),
        "research_context": client.get("research_context", {}),
    }


@router.get("/v2/clients/{client_id}/icp")
def get_client_icp(client_id: str):
    """
    Get ICP_CONFIG (replaces Google Sheets Inputs!B2).
    """
    repo = get_repo()
    client = repo.get_client(client_id)
    
    if not client:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")
    
    return client.get("icp_config", {})


@router.get("/v2/clients/{client_id}/industry")
def get_client_industry(client_id: str):
    """
    Get INDUSTRY_RESEARCH (replaces Google Sheets Inputs!B3).
    """
    repo = get_repo()
    client = repo.get_client(client_id)
    
    if not client:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")
    
    return client.get("industry_research", {})


@router.get("/v2/clients/{client_id}/context")
def get_client_context(client_id: str):
    """
    Get RESEARCH_CONTEXT (replaces Google Sheets Inputs!B4).
    """
    repo = get_repo()
    client = repo.get_client(client_id)
    
    if not client:
        raise HTTPException(status_code=404, detail=f"Client {client_id} not found")
    
    return client.get("research_context", {})


@router.get("/v2/clients/slug/{slug}")
def get_client_by_slug(slug: str):
    """
    Get client by slug (useful for Make.com if using slugs instead of IDs).
    """
    repo = get_repo()
    client = repo.get_client_by_slug(slug)
    
    if not client:
        raise HTTPException(status_code=404, detail=f"Client with slug {slug} not found")
    
    return {
        "client_id": client["id"],
        "slug": client["slug"],
        "name": client["name"],
        "icp_config": client.get("icp_config", {}),
        "industry_research": client.get("industry_research", {}),
        "research_context": client.get("research_context", {}),
    }

