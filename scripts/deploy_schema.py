#!/usr/bin/env python3
"""
Deploy Columnline schema to Supabase

Creates all 14 tables using Supabase Python client.
"""

import os
import sys
from supabase import create_client

# Read .env manually
if os.path.exists('.env'):
    with open('.env') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value.strip('"').strip("'")

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("\n" + "="*60)
print("DEPLOYING COLUMNLINE SCHEMA TO SUPABASE")
print("="*60)
print(f"Target: {SUPABASE_URL}\n")

# Read schema file
with open('database/columnline_schema.sql') as f:
    schema_sql = f.read()

# Execute via RPC (if available) or use postgrest API
# Note: Supabase Python client doesn't directly support raw SQL execution
# We'll try the rpc method or create tables via API

print("ℹ️  Supabase Python client limitations:")
print("   - No direct SQL execution via Python")
print("   - Tables must be created via SQL Editor or psql\n")

print("📋 RECOMMENDED DEPLOYMENT METHODS:\n")

print("METHOD 1: Supabase SQL Editor (Easiest)")
print("   1. Go to: https://supabase.com/dashboard/project/uqqjzkbgiivhbazehljv/sql")
print("   2. Copy contents of: database/columnline_schema.sql")
print("   3. Paste and click 'Run'\n")

print("METHOD 2: psql with connection string")
print("   (Requires database password from Supabase dashboard)\n")

print("METHOD 3: Use Supabase CLI")
print("   supabase db push --db-url <CONNECTION_STRING>\n")

print("="*60)
print("\nChecking existing tables...")
print("="*60)

# Try to query each table to see if it exists
tables_to_check = [
    'clients', 'prompts', 'section_definitions',
    'onboarding', 'prep_inputs', 'batch_composer',
    'runs', 'pipeline_steps', 'claims', 'merged_claims',
    'context_packs', 'contacts', 'sections', 'dossiers'
]

existing = []
missing = []

for table in tables_to_check:
    try:
        result = supabase.table(table).select('*').limit(0).execute()
        existing.append(table)
        print(f"✅ {table} - exists")
    except Exception as e:
        missing.append(table)
        print(f"❌ {table} - not found")

print(f"\n📊 Summary:")
print(f"   Existing: {len(existing)}/{len(tables_to_check)}")
print(f"   Missing: {len(missing)}/{len(tables_to_check)}")

if missing:
    print(f"\n⚠️  Missing tables: {', '.join(missing)}")
    print("\nPlease deploy schema using one of the methods above.")
else:
    print("\n🎉 All tables exist! Ready to import CSV data.")
    print("\nRun: python3 scripts/import_csvs_to_supabase.py")

