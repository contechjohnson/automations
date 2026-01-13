#!/usr/bin/env python3
"""
Parse all prompts from prompts_v2 folder and update 02_prompts.csv
"""

import os
import re
import csv
from datetime import datetime
from pathlib import Path

PROMPTS_DIR = Path("columnline_app/api_migration/make_scenarios_and_csvs/prompts_v2")
OUTPUT_CSV = Path("tmp/sheets_export/02_prompts.csv")

def parse_metadata(content):
    """Extract metadata from prompt file (Stage, Step, Produces Claims, etc.)"""
    metadata = {}

    # Extract title
    title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
    metadata['title'] = title_match.group(1).strip() if title_match else 'Unknown'

    # Extract metadata fields
    metadata['stage'] = extract_field(content, r'\*\*Stage:\*\*\s*(.+)')
    metadata['step'] = extract_field(content, r'\*\*Step:\*\*\s*(.+)')
    metadata['produces_claims'] = extract_field(content, r'\*\*Produces Claims:\*\*\s*(TRUE|FALSE)', default='FALSE')
    metadata['context_pack'] = extract_field(content, r'\*\*Context Pack:\*\*\s*(TRUE|FALSE)', default='FALSE')
    metadata['model'] = extract_field(content, r'\*\*Model:\*\*\s*(.+)', default='gpt-4.1')

    return metadata

def extract_field(content, pattern, default=''):
    """Extract a single field using regex"""
    match = re.search(pattern, content)
    return match.group(1).strip() if match else default

def extract_section(content, section_name):
    """Extract content of a markdown section"""
    # Match section header and capture everything until next ## header or end
    pattern = rf'^## {section_name}\s*\n(.*?)(?=\n##|\Z)'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    return match.group(1).strip() if match else ''

def extract_input_variables(content):
    """Extract input variables from ## Input Variables section"""
    section = extract_section(content, 'Input Variables')
    if not section:
        return []

    variables = []
    # Match **variable_name** or **variable_name** *(optional)*
    for line in section.split('\n'):
        match = re.match(r'\*\*([a-z_]+)\*\*', line)
        if match:
            var_name = match.group(1)
            variables.append(var_name)

    return variables

def extract_output_variables(content):
    """Extract output variables from ## Variables Produced section"""
    section = extract_section(content, 'Variables Produced')
    if not section:
        return []

    variables = []
    # Match - `variable_name`
    for line in section.split('\n'):
        match = re.match(r'-\s*`([a-z_]+)`', line)
        if match:
            var_name = match.group(1)
            variables.append(var_name)

    return variables

def extract_full_prompt(content):
    """Extract the full prompt template section"""
    return extract_section(content, 'Main Prompt Template')

def generate_slug(filename):
    """Convert filename to slug (e.g., 01_search_builder.md -> search-builder)"""
    # Remove number prefix and .md extension
    slug = re.sub(r'^\d+_', '', filename)
    slug = slug.replace('.md', '')
    slug = slug.replace('_', '-')
    return slug

def parse_prompt_file(filepath):
    """Parse a single prompt file and return row data"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    filename = filepath.name

    # Skip STATUS.md and backup files
    if filename == 'STATUS.md' or '.bak' in filename:
        return None

    # Extract all data
    metadata = parse_metadata(content)
    input_vars = extract_input_variables(content)
    output_vars = extract_output_variables(content)
    prompt_template = extract_full_prompt(content)

    # Generate prompt_id based on filename number
    number_match = re.match(r'^(\d+)_', filename)
    if number_match:
        prompt_num = int(number_match.group(1))
        prompt_id = f"PRM_{prompt_num:03d}"
    else:
        # For 99_claims_merge.md
        if filename.startswith('99_'):
            prompt_id = "PRM_099"
        else:
            prompt_id = "PRM_999"

    slug = generate_slug(filename)

    # Format variables as JSON arrays
    input_vars_json = str(input_vars).replace("'", '"')
    output_vars_json = str(output_vars).replace("'", '"')

    return {
        'prompt_id': prompt_id,
        'prompt_slug': slug,
        'stage': metadata['stage'],
        'step': metadata['step'],
        'prompt_template': prompt_template,
        'model': metadata['model'],
        'produce_claims': metadata['produces_claims'],
        'context_pack_produced': metadata['context_pack'],
        'variables_used': input_vars_json,
        'variables_produced': output_vars_json,
        'version': 'v2.0',
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def main():
    print(f"Parsing prompts from: {PROMPTS_DIR}")

    # Get all prompt files sorted by filename
    prompt_files = sorted([
        f for f in PROMPTS_DIR.glob('*.md')
        if f.name != 'STATUS.md' and '.bak' not in f.name
    ])

    print(f"Found {len(prompt_files)} prompt files")

    # Parse all files
    rows = []
    for filepath in prompt_files:
        print(f"  Parsing: {filepath.name}")
        row = parse_prompt_file(filepath)
        if row:
            rows.append(row)

    # Sort by prompt_id
    rows.sort(key=lambda x: x['prompt_id'])

    print(f"\nParsed {len(rows)} prompts successfully")
    print(f"Writing to: {OUTPUT_CSV}")

    # Write CSV
    fieldnames = [
        'prompt_id', 'prompt_slug', 'stage', 'step', 'prompt_template',
        'model', 'produce_claims', 'context_pack_produced',
        'variables_used', 'variables_produced', 'version', 'created_at'
    ]

    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✅ Successfully updated {OUTPUT_CSV}")
    print(f"   Total prompts: {len(rows)}")

    # Show sample
    print("\nSample (first 3 rows):")
    for row in rows[:3]:
        print(f"  {row['prompt_id']} - {row['prompt_slug']} - {row['stage']}")

if __name__ == '__main__':
    main()
