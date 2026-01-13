"""
Transformation endpoints for Make.com integration
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from workers.ai import prompt
from workers.logger import ExecutionLogger

router = APIRouter()


class ClaimsExtractRequest(BaseModel):
    """Request body for claims extraction"""
    narrative: str
    source_step: str
    company_name: str
    run_id: Optional[str] = None


class ContextPackRequest(BaseModel):
    """Request body for context pack generation"""
    merged_claims: List[Dict[str, Any]]
    pack_type: str  # signal_to_entity, entity_to_contacts, contacts_to_enrichment
    company_name: str
    target_step: Optional[str] = None
    run_id: Optional[str] = None


@router.post("/v2/transform/claims-extract")
def extract_claims(request: ClaimsExtractRequest):
    """
    Extract atomic claims from narrative research output.
    Uses the claims-extraction prompt to parse narrative into structured claims.
    """
    try:
        # Call claims extraction prompt
        result = prompt(
            name="claims-extraction",
            variables={
                "narrative": request.narrative,
                "source_step": request.source_step,
                "company_name": request.company_name,
            },
            model="gpt-4.1",
            log=True,
            tags=["makecom", "claims-extraction", request.source_step],
            automation_slug="claims-extraction",
        )
        
        # Parse JSON output
        import json
        output_text = result.get("output", "")
        
        # Try to extract JSON from output (may have markdown code blocks)
        if "```json" in output_text:
            json_start = output_text.find("```json") + 7
            json_end = output_text.find("```", json_start)
            output_text = output_text[json_start:json_end].strip()
        elif "```" in output_text:
            json_start = output_text.find("```") + 3
            json_end = output_text.find("```", json_start)
            output_text = output_text[json_start:json_end].strip()
        
        parsed_output = json.loads(output_text)
        
        return {
            "status": "success",
            "claims": parsed_output.get("claims", []),
            "extraction_summary": parsed_output.get("extraction_summary", {}),
            "runtime_seconds": result.get("elapsed_seconds"),
        }
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse claims JSON: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/v2/transform/context-pack")
def build_context_pack(request: ContextPackRequest):
    """
    Build a context pack from merged claims.
    Uses the context-pack prompt to create a focused summary for downstream steps.
    """
    try:
        import json
        from datetime import datetime
        
        # Call context pack prompt
        result = prompt(
            name="context-pack",
            variables={
                "merged_claims": json.dumps(request.merged_claims, indent=2),
                "pack_type": request.pack_type,
                "company_name": request.company_name,
                "target_step": request.target_step or "next",
                "claims_count": len(request.merged_claims),
                "timestamp": datetime.utcnow().isoformat(),
            },
            model="gpt-4.1",
            log=True,
            tags=["makecom", "context-pack", request.pack_type],
            automation_slug="context-pack",
        )
        
        # Parse JSON output
        output_text = result.get("output", "")
        
        # Try to extract JSON from output (may have markdown code blocks)
        if "```json" in output_text:
            json_start = output_text.find("```json") + 7
            json_end = output_text.find("```", json_start)
            output_text = output_text[json_start:json_end].strip()
        elif "```" in output_text:
            json_start = output_text.find("```") + 3
            json_end = output_text.find("```", json_start)
            output_text = output_text[json_start:json_end].strip()
        
        parsed_output = json.loads(output_text)
        
        return {
            "status": "success",
            "context_pack": parsed_output,
            "runtime_seconds": result.get("elapsed_seconds"),
        }
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse context pack JSON: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

