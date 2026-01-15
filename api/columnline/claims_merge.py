"""
Claims Merge - Programmatic Patch Application

Applies LLM-generated patches to claims arrays instead of having LLM rewrite everything.

Benefits:
- Efficient (apply ~20 patches vs rewrite 200+ claims)
- Transparent (clear audit trail)
- Preserves originals
- Flexible (can adjust patches)
"""

from typing import List, Dict, Any
from copy import deepcopy


def apply_merge_patches(all_claims: List[Dict[str, Any]], patches: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Apply merge patches to claims arrays programmatically

    Args:
        all_claims: List of {step: str, claims: [...]} objects
        patches: List of patch operations from MERGE_CLAIMS LLM step

    Returns:
        {
            "merged_claims": [...],  # Consolidated claims with patches applied
            "application_summary": {...}  # Stats about patches applied
        }
    """
    # Index all claims by qualified ID (step.claim_id)
    claims_by_id = {}
    for step_claims in all_claims:
        step_name = step_claims.get('step', 'unknown')
        claims = step_claims.get('claims', [])

        for claim in claims:
            claim_id = claim.get('claim_id', 'unknown')
            qualified_id = f"{step_name}.{claim_id}"
            claims_by_id[qualified_id] = {
                "claim": deepcopy(claim),
                "step": step_name,
                "merged_into": None,  # Track if claim was merged into another
                "invalidated": False,
                "patches_applied": []
            }

    # Apply each patch
    merge_count = 0
    invalidate_count = 0
    conflict_count = 0
    enhance_count = 0

    for patch in patches:
        operation = patch.get('operation')

        if operation == 'merge':
            merge_count += 1
            _apply_merge_patch(patch, claims_by_id)

        elif operation == 'merge_contact':
            merge_count += 1
            _apply_contact_merge_patch(patch, claims_by_id)

        elif operation == 'invalidate':
            invalidate_count += 1
            _apply_invalidate_patch(patch, claims_by_id)

        elif operation == 'flag_conflict':
            conflict_count += 1
            _apply_conflict_patch(patch, claims_by_id)

        elif operation == 'enhance':
            enhance_count += 1
            _apply_enhance_patch(patch, claims_by_id)

    # Build final merged claims array (exclude merged-into and invalidated claims)
    merged_claims = []
    for qualified_id, claim_data in claims_by_id.items():
        # Skip if this claim was merged into another
        if claim_data['merged_into']:
            continue

        # Include invalidated claims but mark them clearly
        merged_claims.append(claim_data['claim'])

    return {
        "merged_claims": merged_claims,
        "application_summary": {
            "total_input_claims": len(claims_by_id),
            "patches_applied": len(patches),
            "merges": merge_count,
            "invalidations": invalidate_count,
            "conflicts_flagged": conflict_count,
            "enhancements": enhance_count,
            "final_claim_count": len(merged_claims)
        }
    }


def _apply_merge_patch(patch: Dict[str, Any], claims_by_id: Dict[str, Any]):
    """
    Apply merge patch: combine duplicate claims

    Example patch:
    {
        "operation": "merge",
        "claim_ids": ["entity_research.entity_001", "enrich_lead.entity_015"],
        "keep_claim_id": "entity_research.entity_001",
        "merge_reason": "Exact duplicate",
        "add_metadata": {...}
    }
    """
    claim_ids = patch.get('claim_ids', [])
    keep_id = patch.get('keep_claim_id')
    add_metadata = patch.get('add_metadata', {})

    if not keep_id or keep_id not in claims_by_id:
        return

    # Mark other claims as merged into the kept claim
    for cid in claim_ids:
        if cid != keep_id and cid in claims_by_id:
            claims_by_id[cid]['merged_into'] = keep_id
            claims_by_id[cid]['patches_applied'].append('merge')

    # Add metadata to kept claim
    if add_metadata:
        kept_claim = claims_by_id[keep_id]['claim']
        for key, value in add_metadata.items():
            kept_claim[key] = value

        claims_by_id[keep_id]['patches_applied'].append('merge')


def _apply_contact_merge_patch(patch: Dict[str, Any], claims_by_id: Dict[str, Any]):
    """
    Apply contact merge patch: combine mentions of same person

    Example patch:
    {
        "operation": "merge_contact",
        "claim_ids": ["entity_research.contact_001", "contact_discovery.contact_007"],
        "keep_claim_id": "contact_discovery.contact_007",
        "contact_name": "Sylvain Goyette",
        "merge_reason": "Same person",
        "add_metadata": {...}
    }
    """
    # Same logic as merge, but specifically for contacts
    _apply_merge_patch(patch, claims_by_id)


def _apply_invalidate_patch(patch: Dict[str, Any], claims_by_id: Dict[str, Any]):
    """
    Apply invalidate patch: mark claim as superseded/refuted

    Example patch:
    {
        "operation": "invalidate",
        "claim_id": "entity_research.opportunity_005",
        "reason": "Superseded by updated budget",
        "superseded_by": "enrich_opportunity.opportunity_012",
        "add_metadata": {...}
    }
    """
    claim_id = patch.get('claim_id')
    add_metadata = patch.get('add_metadata', {})

    if not claim_id or claim_id not in claims_by_id:
        return

    # Mark as invalidated
    claims_by_id[claim_id]['invalidated'] = True
    claims_by_id[claim_id]['patches_applied'].append('invalidate')

    # Add metadata
    if add_metadata:
        claim = claims_by_id[claim_id]['claim']
        for key, value in add_metadata.items():
            claim[key] = value


def _apply_conflict_patch(patch: Dict[str, Any], claims_by_id: Dict[str, Any]):
    """
    Apply conflict patch: flag contradictory claims

    Example patch:
    {
        "operation": "flag_conflict",
        "claim_ids": ["entity_research.opportunity_003", "enrich_opportunity.opportunity_008"],
        "conflict_description": "Construction start differs",
        "add_metadata": {...}
    }
    """
    claim_ids = patch.get('claim_ids', [])
    add_metadata = patch.get('add_metadata', {})

    # Add conflict metadata to ALL conflicting claims
    for cid in claim_ids:
        if cid in claims_by_id:
            claims_by_id[cid]['patches_applied'].append('flag_conflict')

            if add_metadata:
                claim = claims_by_id[cid]['claim']
                for key, value in add_metadata.items():
                    claim[key] = value


def _apply_enhance_patch(patch: Dict[str, Any], claims_by_id: Dict[str, Any]):
    """
    Apply enhance patch: add cross-references and metadata

    Example patch:
    {
        "operation": "enhance",
        "claim_id": "entity_research.signal_001",
        "add_metadata": {
            "related_claims": [...],
            "strategic_importance": "HIGH"
        }
    }
    """
    claim_id = patch.get('claim_id')
    add_metadata = patch.get('add_metadata', {})

    if not claim_id or claim_id not in claims_by_id:
        return

    # Add metadata
    if add_metadata:
        claim = claims_by_id[claim_id]['claim']
        for key, value in add_metadata.items():
            claim[key] = value

        claims_by_id[claim_id]['patches_applied'].append('enhance')
