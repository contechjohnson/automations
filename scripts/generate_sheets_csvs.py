#!/usr/bin/env python3
"""
Generate 14 CSV templates for Google Sheets schema.
Based on: tmp/google-sheets-schema-summary.md

Usage:
    python scripts/generate_sheets_csvs.py

Output:
    tmp/sheets_export/*.csv (14 files)
"""

import csv
import os
from pathlib import Path


def ensure_output_dir():
    """Create output directory if it doesn't exist."""
    output_dir = Path("tmp/sheets_export")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def write_csv(filename, headers, rows=None):
    """Write CSV file with headers and optional rows."""
    output_dir = ensure_output_dir()
    filepath = output_dir / filename

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        if rows:
            writer.writerows(rows)

    print(f"✓ Created {filename}")


# =============================================================================
# CONFIG LAYER (3 sheets) - With example data
# =============================================================================

def generate_clients_sheet():
    """1. Clients Sheet (Config)"""
    headers = [
        'client_id',
        'client_name',
        'status',
        'icp_config',
        'icp_config_compressed',
        'industry_research',
        'industry_research_compressed',
        'research_context',
        'research_context_compressed',
        'client_specific_research',
        'drip_schedule',
        'created_at',
        'updated_at'
    ]

    # Example rows
    rows = [
        [
            'CLT_EXAMPLE_001',
            'Example Construction Co',
            'active',
            '{"signals": ["permit_filings", "expansion_news"], "geographic_focus": ["TX", "CA"]}',
            '{"signals": ["permits", "expansion"], "geo": ["TX", "CA"]}',
            '{"buying_signals": ["Q1_expansion", "new_projects"], "competitors": ["CompetitorA", "CompetitorB"]}',
            '{"signals": ["Q1_exp", "projects"], "comp": ["A", "B"]}',
            '{"client": {"name": "Example Construction", "focus": "commercial"}, "context": "Mid-size regional"}',
            '{"client": "Example Const", "focus": "commercial"}',
            '{"alumni_connections": ["John Doe - Stanford 2015"], "interests": ["golf", "industry_conferences"]}',
            '{"days": [0, 3, 7, 14]}',
            '2025-01-01 10:00:00',
            '2025-01-12 14:30:00'
        ]
    ]

    write_csv('01_clients.csv', headers, rows)


def generate_prompts_sheet():
    """2. Prompts Sheet (Config)"""
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

    # Example rows
    rows = [
        [
            'PRM_001',
            'search-builder',
            'FIND_LEAD',
            '1_SEARCH_BUILDER',
            'You will receive: ICP config, seed data. Your task: Generate search queries for finding companies matching the ICP.',
            'gpt-4.1',
            'FALSE',
            'FALSE',
            '["icp_config", "seed"]',
            '["search_queries", "exclude_domains"]',
            'v1.0',
            '2025-01-01 10:00:00'
        ],
        [
            'PRM_002',
            'entity-research',
            'FIND_LEAD',
            '3_ENTITY_RESEARCH',
            'You will receive: Company name, initial data. Your task: Research the company and extract key facts.',
            'gpt-4.1',
            'TRUE',
            'FALSE',
            '["company_name", "initial_data"]',
            '["entity_claims"]',
            'v1.0',
            '2025-01-01 10:00:00'
        ],
        [
            'PRM_003',
            'claims-merge',
            'TRANSFORM',
            'MERGE_CLAIMS',
            'You will receive: All claims from previous steps. Your task: Merge claims, remove redundancy and refuted conflicts.',
            'gpt-4.1',
            'FALSE',
            'FALSE',
            '["all_claims"]',
            '["merged_claims"]',
            'v1.0',
            '2025-01-01 10:00:00'
        ]
    ]

    write_csv('02_prompts.csv', headers, rows)


def generate_section_definitions_sheet():
    """3. SectionDefinitions Sheet (Config)"""
    headers = [
        'section_name',
        'expected_variables',
        'variable_types',
        'validation_rules',
        'description',
        'example_output'
    ]

    # Example rows
    rows = [
        [
            'INTRO',
            '["company_name", "timing_urgency", "one_liner", "primary_signal", "the_angle", "lead_score", "score_explanation"]',
            '{"lead_score": "integer", "timing_urgency": "enum"}',
            '{"lead_score": {"min": 0, "max": 100}, "timing_urgency": {"values": ["HIGH", "MEDIUM", "LOW"]}}',
            'Intro section with company overview, score, and angle',
            '{"company_name": "Acme Corp", "lead_score": 85, "timing_urgency": "HIGH"}'
        ],
        [
            'SIGNALS',
            '["primary_buying_signal", "additional_signals"]',
            '{"primary_buying_signal": "object", "additional_signals": "array"}',
            '{}',
            'Buying signals section with primary and additional signals',
            '{"primary_buying_signal": {"signal": "Filed permit", "description": "..."}}'
        ]
    ]

    write_csv('03_section_definitions.csv', headers, rows)


# =============================================================================
# EXECUTION LAYER (11 sheets) - Empty templates
# =============================================================================

def generate_onboarding_sheet():
    """4. Onboarding Sheet (Execution)"""
    headers = [
        'onboarding_id',
        'client_name',
        'status',
        'client_info',
        'transcripts',
        'client_material',
        'pre_research',
        'onboarding_system_prompt',
        'generated_icp_config',
        'generated_industry_research',
        'generated_research_context',
        'generated_batch_strategy',
        'client_id',
        'started_at',
        'completed_at'
    ]

    write_csv('04_onboarding.csv', headers)


def generate_prep_inputs_sheet():
    """5. PrepInputs Sheet (Execution)"""
    headers = [
        'prep_id',
        'client_id',
        'status',
        'original_icp_config',
        'compressed_icp_config',
        'original_industry_research',
        'compressed_industry_research',
        'original_research_context',
        'compressed_research_context',
        'compression_prompt',
        'token_savings',
        'started_at',
        'completed_at'
    ]

    write_csv('05_prep_inputs.csv', headers)


def generate_batch_composer_sheet():
    """6. BatchComposer Sheet (Execution)"""
    headers = [
        'batch_id',
        'client_id',
        'status',
        'batch_strategy',
        'seed_pool_input',
        'last_batch_hints',
        'recent_feedback',
        'run_ids_created',
        'started_at',
        'completed_at'
    ]

    write_csv('06_batch_composer.csv', headers)


def generate_runs_sheet():
    """7. Runs Sheet (Execution)"""
    headers = [
        'run_id',
        'client_id',
        'status',
        'seed_data',
        'dossier_id',
        'started_at',
        'completed_at',
        'error_message',
        'triggered_by',
        'config_snapshot'
    ]

    write_csv('07_runs.csv', headers)


def generate_pipeline_steps_sheet():
    """8. PipelineSteps Sheet (Execution)"""
    headers = [
        'step_id',
        'run_id',
        'prompt_id',
        'step_name',
        'status',
        'input',
        'output',
        'model_used',
        'tokens_used',
        'runtime_seconds',
        'started_at',
        'completed_at',
        'error_message'
    ]

    write_csv('08_pipeline_steps.csv', headers)


def generate_claims_sheet():
    """9. Claims Sheet (Execution)"""
    headers = [
        'run_id',
        'step_id',
        'step_name',
        'claims_json',
        'created_at'
    ]

    write_csv('09_claims.csv', headers)


def generate_merged_claims_sheet():
    """10. MergedClaims Sheet (Execution)"""
    headers = [
        'merge_id',
        'run_id',
        'step_id',
        'merged_claims_json',
        'created_at'
    ]

    write_csv('10_merged_claims.csv', headers)


def generate_context_packs_sheet():
    """11. ContextPacks Sheet (Execution)"""
    headers = [
        'pack_id',
        'run_id',
        'context_type',
        'pack_content',
        'produced_by_step',
        'consumed_by_steps',
        'created_at'
    ]

    write_csv('11_context_packs.csv', headers)


def generate_contacts_sheet():
    """12. Contacts Sheet (Execution) - Both renderable + processing columns"""
    headers = [
        # System columns
        'id',
        'dossier_id',
        'run_id',
        # Renderable columns (A-S)
        'name',
        'first_name',
        'last_name',
        'title',
        'email',
        'phone',
        'linkedin_url',
        'linkedin_connections',
        'bio_paragraph',
        'tenure_months',
        'previous_companies',
        'education',
        'skills',
        'recent_post_quote',
        'is_primary',
        'source',
        # Processing columns (T-AF)
        'tier',
        'bio_summary',
        'why_they_matter',
        'signal_relevance',
        'interesting_facts',
        'linkedin_summary',
        'web_summary',
        'email_copy',
        'linkedin_copy',
        'client_email_copy',
        'client_linkedin_copy',
        'confidence',
        'created_at'
    ]

    write_csv('12_contacts.csv', headers)


def generate_sections_sheet():
    """13. Sections Sheet (Execution)"""
    headers = [
        'section_id',
        'run_id',
        'section_name',
        'section_data',
        'claim_ids_used',
        'produced_by_step',
        'status',
        'variables_produced',
        'target_column',
        'created_at'
    ]

    write_csv('13_sections.csv', headers)


def generate_dossiers_sheet():
    """14. Dossiers Sheet (Execution)"""
    headers = [
        'dossier_id',
        'run_id',
        'client_id',
        'company_name',
        'lead_score',
        'timing_urgency',
        'primary_signal',
        'find_lead',
        'enrich_lead',
        'copy',
        'insight',
        'media',
        'status',
        'created_at',
        'delivered_at'
    ]

    write_csv('14_dossiers.csv', headers)


# =============================================================================
# Main execution
# =============================================================================

def main():
    """Generate all 14 CSV files."""
    print("\n" + "="*60)
    print("Generating Google Sheets CSV Templates")
    print("="*60 + "\n")

    print("CONFIG LAYER (3 sheets with example data):")
    generate_clients_sheet()
    generate_prompts_sheet()
    generate_section_definitions_sheet()

    print("\nEXECUTION LAYER (11 sheets - empty templates):")
    generate_onboarding_sheet()
    generate_prep_inputs_sheet()
    generate_batch_composer_sheet()
    generate_runs_sheet()
    generate_pipeline_steps_sheet()
    generate_claims_sheet()
    generate_merged_claims_sheet()
    generate_context_packs_sheet()
    generate_contacts_sheet()
    generate_sections_sheet()
    generate_dossiers_sheet()

    print("\n" + "="*60)
    print("✓ All 14 CSV files generated in tmp/sheets_export/")
    print("="*60)
    print("\nNext steps:")
    print("1. Review CSV files in tmp/sheets_export/")
    print("2. Create new Google Sheet")
    print("3. Import each CSV as a separate tab")
    print("4. Share Sheet ID for API integration")
    print()


if __name__ == "__main__":
    main()
