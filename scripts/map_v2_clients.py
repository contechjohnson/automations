"""
Script to map v2_clients to production clients.

Run this AFTER the migration in database/migrations/004_v2_production_integration.sql

Usage:
    python scripts/map_v2_clients.py

This will:
1. List all v2 clients without production mapping
2. List all production clients
3. Allow manual mapping or auto-match by name similarity
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.environ['SUPABASE_URL'],
    os.environ['SUPABASE_SERVICE_ROLE_KEY']
)

# Known mappings (v2_client_id -> production_client_uuid)
# These mappings have been applied to the database
KNOWN_MAPPINGS = {
    'CLT_ROGER_ACRES_001': 'fb83b832-23db-4ee1-993f-50da8e9fd9bb',  # Span Construction (MAPPED 2026-01-15)
}

# Production clients reference (for future mappings):
# - Aim to Thrive Nutrition: b69f2d69-a1bd-411b-8e57-00369bc58107
# - ARCO Murray: a8fc1197-a601-4f32-a0bf-a67c3bbbcfd7
# - Berg Group: 26404e38-1faf-47e4-9b3e-22245674f08d
# - Columnline AI: 9953f9eb-74e2-4217-b694-81448f6028fb
# - DCI Group: 5b1c547c-4d0a-4d34-b086-240861f63116
# - Gresham Smith (DEMO): 4ec27849-54ab-4d7c-b2c1-946b600e87c2
# - H+O Structural Engineering: 0de65969-b0a9-4fdb-8009-31a2bef0c30e
# - Katz LDE: 1265fd32-8b86-47b7-9178-75c2110e6945
# - Phelan's Interiors: 1df517d7-2ea8-46eb-8731-92c01f8ffbf6
# - SH Commercial Real Estate: 41115775-4bef-4f21-b249-221fb3dbf0f9
# - Span Construction: fb83b832-23db-4ee1-993f-50da8e9fd9bb
# - Studer Education: 3e5cad11-78ad-4155-aae6-35d5ea76385a
# - Workforce Connect: 5246bdce-f137-4ca4-ad94-c063ead511d9

def get_production_clients():
    """Get all production clients."""
    result = supabase.table('clients').select('id, company_name').execute()
    return {c['company_name']: c['id'] for c in result.data}

def get_v2_clients():
    """Get all v2 clients."""
    result = supabase.table('v2_clients').select('client_id, client_name, production_client_id, status').execute()
    return result.data

def map_client(v2_client_id: str, production_client_uuid: str):
    """Map a v2 client to a production client."""
    result = supabase.table('v2_clients').update({
        'production_client_id': production_client_uuid
    }).eq('client_id', v2_client_id).execute()
    return result

def main():
    print("=" * 60)
    print("V2 → Production Client Mapping")
    print("=" * 60)

    # Get all clients
    prod_clients = get_production_clients()
    v2_clients = get_v2_clients()

    print(f"\nProduction Clients ({len(prod_clients)}):")
    for name, uuid in prod_clients.items():
        print(f"  {name}: {uuid}")

    print(f"\nV2 Clients ({len(v2_clients)}):")
    for c in v2_clients:
        mapped = "✓ Mapped" if c.get('production_client_id') else "✗ Not mapped"
        print(f"  {c['client_name']} ({c['client_id']}): {mapped}")
        if c.get('production_client_id'):
            print(f"    → {c['production_client_id']}")

    # Apply known mappings
    print("\n" + "=" * 60)
    print("Applying known mappings...")
    print("=" * 60)

    for v2_id, prod_uuid in KNOWN_MAPPINGS.items():
        print(f"\nMapping {v2_id} → {prod_uuid}")
        try:
            result = map_client(v2_id, prod_uuid)
            if result.data:
                print(f"  ✓ Success")
            else:
                print(f"  ✗ No rows updated (client may not exist)")
        except Exception as e:
            print(f"  ✗ Error: {e}")

    # Verify
    print("\n" + "=" * 60)
    print("Verification")
    print("=" * 60)

    v2_clients = get_v2_clients()
    unmapped = [c for c in v2_clients if not c.get('production_client_id')]

    if unmapped:
        print(f"\n⚠️  {len(unmapped)} unmapped v2 clients:")
        for c in unmapped:
            print(f"  - {c['client_name']} ({c['client_id']})")
    else:
        print("\n✓ All v2 clients are mapped!")

if __name__ == '__main__':
    main()
