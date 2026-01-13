#!/usr/bin/env python3
"""
Import Columnline CSVs to Supabase

Imports the 3 config layer tables:
- clients (1 row)
- prompts (31 rows - model and version excluded)
- section_definitions (2 rows)

V2 Execution layer tables (4-14) remain empty as templates.
"""

import csv
import json
import os
import sys
from pathlib import Path
from supabase import create_client

# Read .env file
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value.strip('"').strip("'")

# Config
CSV_DIR = Path('tmp/sheets_export')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def parse_json_field(value):
    """Parse a JSON string field to actual JSON, or return None"""
    if not value or value.strip() == '':
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        # If not valid JSON, return as-is (might be a simple string)
        return value

def parse_json_fields(row, json_fields):
    """Parse specified fields as JSON"""
    for field in json_fields:
        if field in row:
            row[field] = parse_json_field(row[field])
    return row

def clean_empty_strings(row):
    """Convert empty strings to None for cleaner data"""
    return {k: (None if v == '' else v) for k, v in row.items()}

def import_csv(filename, table_name, json_fields=[], exclude_fields=[]):
    """
    Import CSV to Supabase table

    Args:
        filename: CSV file name
        table_name: Supabase table name
        json_fields: List of field names to parse as JSON
        exclude_fields: List of field names to exclude from import
    """
    csv_path = CSV_DIR / filename
    print(f"\n{'='*60}")
    print(f"Importing {filename} → {table_name}")
    print(f"{'='*60}")

    if not csv_path.exists():
        print(f"  ⚠️  File not found: {csv_path}")
        return

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = []

        for row in reader:
            # Skip empty rows
            if not any(row.values()):
                continue

            # Exclude specified fields
            for field in exclude_fields:
                row.pop(field, None)

            # Parse JSON fields
            row = parse_json_fields(row, json_fields)

            # Clean empty strings
            row = clean_empty_strings(row)

            rows.append(row)

        if not rows:
            print(f"  ⚠️  No data to import (file is empty or header-only)")
            return

        print(f"  📊 Found {len(rows)} row(s)")

        try:
            result = supabase.table(table_name).insert(rows).execute()
            print(f"  ✅ Successfully imported {len(rows)} row(s)")

            # Show first row as sample
            if rows:
                first = rows[0]
                print(f"  📝 Sample row:")
                for key in list(first.keys())[:5]:  # Show first 5 fields
                    value = first[key]
                    if isinstance(value, dict) or isinstance(value, list):
                        print(f"     {key}: <JSON>")
                    else:
                        preview = str(value)[:50]
                        if len(str(value)) > 50:
                            preview += "..."
                        print(f"     {key}: {preview}")

        except Exception as e:
            print(f"  ❌ Error importing to {table_name}: {e}")
            print(f"  💡 First row data: {rows[0]}")
            sys.exit(1)

# ============================================================================
# MAIN IMPORT
# ============================================================================

print("\n" + "="*60)
print("COLUMNLINE CSV → SUPABASE IMPORT")
print("="*60)
print(f"Target: {SUPABASE_URL}")
print(f"Source: {CSV_DIR}")

# 1. CLIENTS
import_csv(
    '01_clients.csv',
    'v2_clients',
    json_fields=[
        'icp_config',
        'icp_config_compressed',
        'industry_research',
        'industry_research_compressed',
        'research_context',
        'research_context_compressed',
        'client_specific_research',
        'drip_schedule'
    ]
)

# 2. PROMPTS
# EXCLUDE: model, version (per user request - Make.com handles model selection)
import_csv(
    '02_prompts.csv',
    'v2_prompts',
    json_fields=[
        'variables_used',
        'variables_produced'
    ],
    exclude_fields=[
        'model',
        'version'
    ]
)

# 3. SECTION DEFINITIONS
import_csv(
    '03_section_definitions.csv',
    'v2_section_definitions',
    json_fields=[
        'expected_variables',
        'variable_types',
        'validation_rules',
        'example_output'
    ]
)

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*60)
print("IMPORT COMPLETE")
print("="*60)
print("\n✅ V2 Config layer imported:")
print("   - clients (1 row)")
print("   - prompts (31 rows - model & version excluded)")
print("   - section_definitions (2 rows)")
print("\n📋 V2 Execution layer tables (4-14) remain empty")
print("   These will be populated during dossier runs\n")

# Verify imports
print("="*60)
print("VERIFICATION")
print("="*60)

try:
    clients_count = len(supabase.table('v2_clients').select('client_id').execute().data)
    prompts_count = len(supabase.table('v2_prompts').select('prompt_id').execute().data)
    sections_count = len(supabase.table('v2_section_definitions').select('section_name').execute().data)

    print(f"✅ clients: {clients_count} row(s)")
    print(f"✅ prompts: {prompts_count} row(s)")
    print(f"✅ section_definitions: {sections_count} row(s)")

    if clients_count == 1 and prompts_count == 31 and sections_count == 2:
        print("\n🎉 All verifications passed!")
    else:
        print("\n⚠️  Counts don't match expected values")
        print("   Expected: clients=1, prompts=31, section_definitions=2")

except Exception as e:
    print(f"❌ Error verifying imports: {e}")

print("\n" + "="*60)
print("Ready for API endpoints!")
print("="*60 + "\n")
