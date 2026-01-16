"""
Run migration 004: V2 Production Integration

Adds columns needed for v2 → production dossier publishing:
1. production_client_id UUID on v2_clients
2. pipeline_version TEXT on dossiers
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.environ['SUPABASE_URL'],
    os.environ['SUPABASE_SERVICE_ROLE_KEY']
)

def run_migration():
    print("=" * 60)
    print("Running Migration 004: V2 Production Integration")
    print("=" * 60)

    # Migration 1: Add production_client_id to v2_clients
    print("\n1. Adding production_client_id to v2_clients...")
    try:
        result = supabase.rpc('exec_sql', {
            'query': 'ALTER TABLE v2_clients ADD COLUMN IF NOT EXISTS production_client_id UUID;'
        }).execute()
        print("   ✓ Column added (or already exists)")
    except Exception as e:
        # RPC may not exist - try alternative approach
        print(f"   Note: RPC not available, checking column directly...")
        # Check if column exists by querying
        try:
            test = supabase.table('v2_clients').select('production_client_id').limit(1).execute()
            print("   ✓ Column already exists")
        except Exception as e2:
            print(f"   ✗ Column doesn't exist and can't add via API")
            print(f"   → Run this SQL manually in Supabase SQL Editor:")
            print(f"     ALTER TABLE v2_clients ADD COLUMN IF NOT EXISTS production_client_id UUID;")
            return False

    # Migration 2: Add pipeline_version to dossiers
    print("\n2. Adding pipeline_version to dossiers...")
    try:
        # Check if column exists
        test = supabase.table('dossiers').select('pipeline_version').limit(1).execute()
        print("   ✓ Column already exists")
    except Exception as e:
        print(f"   ✗ Column doesn't exist")
        print(f"   → Run this SQL manually in Supabase SQL Editor:")
        print(f"     ALTER TABLE dossiers ADD COLUMN IF NOT EXISTS pipeline_version TEXT DEFAULT 'v1';")
        print(f"     CREATE INDEX IF NOT EXISTS idx_dossiers_pipeline_version ON dossiers(pipeline_version);")
        return False

    print("\n" + "=" * 60)
    print("Migration check complete!")
    print("=" * 60)
    return True

if __name__ == '__main__':
    run_migration()
