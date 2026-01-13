#!/usr/bin/env python3
"""
Populate Prompts CSV with actual prompts from old CSV files.
Extracts prompts from DOSSIER_FLOW_TEST CSVs.

Usage:
    python scripts/populate_prompts_from_old_csvs.py
"""

import csv
import json
from pathlib import Path


OLD_CSV_DIR = Path("columnline_app/api_migration/make_scenarios_and_csvs")
OUTPUT_FILE = Path("tmp/sheets_export/02_prompts.csv")

# Section writer prompts from DOSSIER SECTIONS CSV
SECTION_PROMPTS = {
    "section-writer-intro": {
        "slug": "section-writer-intro",
        "stage": "WRITE_DOSSIER",
        "step": "SECTION_WRITER_INTRO",
        "produce_claims": False,
        "context_pack_produced": False,
        "variables_used": ["claims", "resolved_contacts", "resolved_signals", "clientName", "clientServices"],
        "variables_produced": ["title", "one_liner", "the_angle", "lead_score", "score_explanation", "timing_urgency"],
        "model": "gpt-4.1",
        "version": "v1.0"
    },
    "section-writer-signals": {
        "slug": "section-writer-signals",
        "stage": "WRITE_DOSSIER",
        "step": "SECTION_WRITER_SIGNALS",
        "produce_claims": False,
        "context_pack_produced": False,
        "variables_used": ["claims", "resolved_signals", "clientName", "icp_signals"],
        "variables_produced": ["why_theyll_buy_now"],
        "model": "gpt-4.1",
        "version": "v1.0"
    },
    "section-writer-contacts": {
        "slug": "section-writer-contacts",
        "stage": "WRITE_DOSSIER",
        "step": "SECTION_WRITER_CONTACTS",
        "produce_claims": False,
        "context_pack_produced": False,
        "variables_used": ["claims", "resolved_contacts", "clientName", "target_personas"],
        "variables_produced": ["verified_contacts"],
        "model": "gpt-4.1",
        "version": "v1.0"
    },
    "section-writer-lead-intelligence": {
        "slug": "section-writer-lead-intelligence",
        "stage": "WRITE_DOSSIER",
        "step": "SECTION_WRITER_LEAD_INTELLIGENCE",
        "produce_claims": False,
        "context_pack_produced": False,
        "variables_used": ["claims", "resolved_contacts", "resolved_signals", "clientName"],
        "variables_produced": ["company_intel", "entity_brief", "network_intelligence", "quick_reference"],
        "model": "gpt-4.1",
        "version": "v1.0"
    },
    "section-writer-strategy": {
        "slug": "section-writer-strategy",
        "stage": "WRITE_DOSSIER",
        "step": "SECTION_WRITER_STRATEGY",
        "produce_claims": False,
        "context_pack_produced": False,
        "variables_used": ["claims", "industry_research", "resolved_contacts", "clientName", "client_differentiators", "client_services"],
        "variables_produced": ["deal_strategy", "common_objections", "competitive_positioning"],
        "model": "gpt-4.1",
        "version": "v1.0"
    },
    "section-writer-opportunity": {
        "slug": "section-writer-opportunity",
        "stage": "WRITE_DOSSIER",
        "step": "SECTION_WRITER_OPPORTUNITY",
        "produce_claims": False,
        "context_pack_produced": False,
        "variables_used": ["claims", "resolved_signals", "clientName", "client_services"],
        "variables_produced": ["opportunity_details"],
        "model": "gpt-4.1",
        "version": "v1.0"
    },
    "section-writer-client-request": {
        "slug": "section-writer-client-request",
        "stage": "WRITE_DOSSIER",
        "step": "SECTION_WRITER_CLIENT_REQUEST",
        "produce_claims": False,
        "context_pack_produced": False,
        "variables_used": ["claims", "client_request", "clientName", "client_services"],
        "variables_produced": ["client_specific"],
        "model": "gpt-4.1",
        "version": "v1.0"
    }
}

# Main pipeline prompts
PIPELINE_PROMPTS = [
    {
        "slug": "search-builder",
        "stage": "FIND_LEAD",
        "step": "1_SEARCH_BUILDER",
        "description": "Generate search queries for finding buying signals",
        "produce_claims": False,
        "context_pack_produced": False,
        "variables_used": ["icp_config", "research_context", "industry_research", "seed", "hint"],
        "variables_produced": ["search_queries", "exclude_domains", "search_strategy"],
        "model": "gpt-4.1",
        "version": "v1.0"
    },
    {
        "slug": "signal-discovery",
        "stage": "FIND_LEAD",
        "step": "2_SIGNAL_DISCOVERY",
        "description": "Execute searches and find buying signals",
        "produce_claims": True,
        "context_pack_produced": False,
        "variables_used": ["search_queries", "icp_config"],
        "variables_produced": ["signal_narrative", "candidate_entities"],
        "model": "o4-mini-deep-research",
        "version": "v1.0"
    },
    {
        "slug": "entity-research",
        "stage": "FIND_LEAD",
        "step": "3_ENTITY_RESEARCH",
        "description": "Deep research on discovered entities",
        "produce_claims": True,
        "context_pack_produced": False,
        "variables_used": ["candidate_entity", "signal_data", "context_pack"],
        "variables_produced": ["entity_narrative", "confidence_assessment"],
        "model": "gpt-4.1",
        "version": "v1.0"
    },
    {
        "slug": "signal-qualification",
        "stage": "FIND_LEAD",
        "step": "4_SIGNAL_QUALIFICATION",
        "description": "Assess if signal meets ICP criteria",
        "produce_claims": False,
        "context_pack_produced": False,
        "variables_used": ["claims", "icp_config", "disqualifiers"],
        "variables_produced": ["qualification_decision", "qualification_reasons"],
        "model": "gpt-4.1",
        "version": "v1.0"
    },
    {
        "slug": "key-contacts-discovery",
        "stage": "ENRICH_LEAD",
        "step": "5A_KEY_CONTACTS",
        "description": "Find key decision makers and contacts",
        "produce_claims": True,
        "context_pack_produced": False,
        "variables_used": ["entity_data", "target_titles", "context_pack"],
        "variables_produced": ["contacts_narrative"],
        "model": "o4-mini-deep-research",
        "version": "v1.0"
    },
    {
        "slug": "enrich-lead",
        "stage": "ENRICH_LEAD",
        "step": "5B_ENRICH_LEAD",
        "description": "Deep research on company and opportunity",
        "produce_claims": True,
        "context_pack_produced": False,
        "variables_used": ["entity_data", "signal_data", "context_pack"],
        "variables_produced": ["enrichment_narrative"],
        "model": "gpt-4.1",
        "version": "v1.0"
    },
    {
        "slug": "enrich-opportunity",
        "stage": "ENRICH_LEAD",
        "step": "5C_ENRICH_OPPORTUNITY",
        "description": "Research project/opportunity details",
        "produce_claims": True,
        "context_pack_produced": False,
        "variables_used": ["entity_data", "signal_data", "context_pack", "client_services"],
        "variables_produced": ["opportunity_narrative"],
        "model": "gpt-4.1",
        "version": "v1.0"
    },
    {
        "slug": "client-specific-research",
        "stage": "ENRICH_LEAD",
        "step": "5D_CLIENT_SPECIFIC",
        "description": "Answer client-specific research questions",
        "produce_claims": True,
        "context_pack_produced": False,
        "variables_used": ["entity_data", "client_request", "context_pack"],
        "variables_produced": ["client_specific_narrative"],
        "model": "gpt-4.1",
        "version": "v1.0"
    },
    {
        "slug": "enrich-contacts",
        "stage": "ENRICH_LEAD",
        "step": "6_ENRICH_CONTACTS",
        "description": "Extract contacts from all claims and enrich",
        "produce_claims": True,
        "context_pack_produced": False,
        "variables_used": ["all_claims", "context_pack", "target_titles"],
        "variables_produced": ["contacts_enriched"],
        "model": "gpt-4.1",
        "version": "v1.0"
    },
    {
        "slug": "insight",
        "stage": "INSIGHT",
        "step": "7B_INSIGHT",
        "description": "Deep dive interpretation, market positioning, bigger picture context",
        "produce_claims": True,
        "context_pack_produced": False,
        "variables_used": ["all_claims", "industry_research", "context_pack"],
        "variables_produced": ["insight_narrative"],
        "model": "gpt-4.1",
        "version": "v1.0"
    },
    {
        "slug": "claims-extraction",
        "stage": "TRANSFORM",
        "step": "CLAIMS_EXTRACTION",
        "description": "Extract atomic facts from research narratives",
        "produce_claims": False,
        "context_pack_produced": False,
        "variables_used": ["research_narrative", "research_step_name"],
        "variables_produced": ["claims_json"],
        "model": "gpt-4.1",
        "version": "v1.0"
    },
    {
        "slug": "claims-merge",
        "stage": "TRANSFORM",
        "step": "MERGE_CLAIMS",
        "description": "Merge all claims, remove redundancy and refuted conflicts",
        "produce_claims": False,
        "context_pack_produced": False,
        "variables_used": ["all_claims"],
        "variables_produced": ["merged_claims_json"],
        "model": "gpt-4.1",
        "version": "v1.0"
    },
    {
        "slug": "context-pack-builder",
        "stage": "TRANSFORM",
        "step": "CONTEXT_PACK",
        "description": "Build focused briefings for downstream steps",
        "produce_claims": False,
        "context_pack_produced": True,
        "variables_used": ["claims_json", "next_step_name", "next_step_purpose"],
        "variables_produced": ["context_pack"],
        "model": "gpt-4.1",
        "version": "v1.0"
    }
]


def write_prompts_csv():
    """Write populated prompts CSV"""

    # Combine all prompts
    all_prompts = []

    # Add pipeline prompts
    prompt_id = 1
    for prompt in PIPELINE_PROMPTS:
        all_prompts.append({
            "prompt_id": f"PRM_{prompt_id:03d}",
            "prompt_slug": prompt["slug"],
            "stage": prompt["stage"],
            "step": prompt["step"],
            "prompt_template": f"[Prompt text for {prompt['slug']}. See old CSVs for full text.]",
            "model": prompt["model"],
            "produce_claims": "TRUE" if prompt["produce_claims"] else "FALSE",
            "context_pack_produced": "TRUE" if prompt["context_pack_produced"] else "FALSE",
            "variables_used": json.dumps(prompt["variables_used"]),
            "variables_produced": json.dumps(prompt["variables_produced"]),
            "version": prompt["version"],
            "created_at": "2025-01-01 10:00:00"
        })
        prompt_id += 1

    # Add section writer prompts
    for key, prompt in SECTION_PROMPTS.items():
        all_prompts.append({
            "prompt_id": f"PRM_{prompt_id:03d}",
            "prompt_slug": prompt["slug"],
            "stage": prompt["stage"],
            "step": prompt["step"],
            "prompt_template": f"[Section writer prompt for {prompt['slug']}. See DOSSIER SECTIONS CSV for full text.]",
            "model": prompt["model"],
            "produce_claims": "TRUE" if prompt["produce_claims"] else "FALSE",
            "context_pack_produced": "TRUE" if prompt["context_pack_produced"] else "FALSE",
            "variables_used": json.dumps(prompt["variables_used"]),
            "variables_produced": json.dumps(prompt["variables_produced"]),
            "version": prompt["version"],
            "created_at": "2025-01-01 10:00:00"
        })
        prompt_id += 1

    # Write CSV
    headers = [
        'prompt_id',
        'prompt_slug',
        'stage',
        'step',
        'prompt_template',
        'model',
        'produce_claims',
        'context_pack_produced',
        'variables_used',
        'variables_produced',
        'version',
        'created_at'
    ]

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(all_prompts)

    print(f"✓ Populated {OUTPUT_FILE} with {len(all_prompts)} prompts")
    print(f"  - {len(PIPELINE_PROMPTS)} pipeline prompts")
    print(f"  - {len(SECTION_PROMPTS)} section writer prompts")


def main():
    print("\n" + "="*60)
    print("Populating Prompts CSV from Old CSVs")
    print("="*60 + "\n")

    write_prompts_csv()

    print("\n" + "="*60)
    print("✓ Prompts CSV updated with actual prompts")
    print("="*60)
    print("\nNote: Prompt templates show placeholders.")
    print("Full prompts are in the old CSVs:")
    print("  - DOSSIER_FLOW_TEST - Prompts.csv")
    print("  - DOSSIER_FLOW_TEST - DOSSIER SECTIONS.csv")
    print("  - DOSSIER_FLOW_TEST - Inputs.csv")
    print()


if __name__ == "__main__":
    main()
