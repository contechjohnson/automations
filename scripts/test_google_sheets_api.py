#!/usr/bin/env python3
"""
Quick test of Google Sheets API connectivity

Before running:
1. Set up service account credentials (see docs/google-sheets-implementation/README.md)
2. Share the Google Sheet with your service account email
3. Set GOOGLE_SHEETS_CREDENTIALS_PATH in .env (or create credentials.json)

Usage:
    python3 scripts/test_google_sheets_api.py
"""

import os
import sys
import json
from pathlib import Path

# Try to import gspread
try:
    import gspread
    from google.oauth2.service_account import Credentials
except ImportError:
    print("❌ Error: gspread not installed")
    print("\nInstall with:")
    print("  pip install gspread google-auth")
    sys.exit(1)

# Sheet ID from user's URL
SHEET_ID = "1G70bxnt_P_2_qAqssrjnzkhBCPUa7gVAKMmc_mTn9fQ"

# Expected sheet names (matching CSV titles)
EXPECTED_SHEETS = [
    "Clients",
    "Prompts",
    "SectionDefinitions",
    "Onboarding",
    "PrepInputs",
    "BatchComposer",
    "Runs",
    "PipelineSteps",
    "Claims",
    "MergedClaims",
    "ContextPacks",
    "Contacts",
    "Sections",
    "Dossiers"
]

def get_credentials():
    """Get service account credentials"""
    # Try environment variable first
    creds_path = os.environ.get('GOOGLE_SHEETS_CREDENTIALS_PATH')

    if not creds_path:
        # Try default location
        creds_path = 'credentials.json'

    if not os.path.exists(creds_path):
        print("❌ Error: credentials.json not found")
        print("\nYou need to:")
        print("1. Create a service account in Google Cloud Console")
        print("2. Download the JSON key file")
        print("3. Save it as 'credentials.json' in this directory")
        print("   OR set GOOGLE_SHEETS_CREDENTIALS_PATH environment variable")
        print("\nSee: docs/google-sheets-implementation/README.md for setup guide")
        return None

    try:
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        credentials = Credentials.from_service_account_file(creds_path, scopes=scopes)
        return credentials
    except Exception as e:
        print(f"❌ Error loading credentials: {e}")
        return None

def test_connection():
    """Test Google Sheets API connection"""
    print("=" * 60)
    print("Google Sheets API Test")
    print("=" * 60)
    print()

    # Get credentials
    print("1. Loading credentials...")
    credentials = get_credentials()
    if not credentials:
        return False
    print("   ✅ Credentials loaded")
    print()

    # Connect to Google Sheets
    print("2. Connecting to Google Sheets API...")
    try:
        client = gspread.authorize(credentials)
        print("   ✅ Connected to Google Sheets API")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False
    print()

    # Open the specific sheet
    print(f"3. Opening sheet: {SHEET_ID}")
    try:
        spreadsheet = client.open_by_key(SHEET_ID)
        print(f"   ✅ Opened sheet: {spreadsheet.title}")
    except gspread.exceptions.APIError as e:
        if "PERMISSION_DENIED" in str(e):
            print("   ❌ Permission denied")
            print("\nYou need to share the Google Sheet with your service account:")
            print("   1. Open the sheet in your browser")
            print("   2. Click 'Share'")
            print("   3. Add your service account email (from credentials.json)")
            print("   4. Give it 'Editor' access")
            return False
        else:
            print(f"   ❌ API Error: {e}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    print()

    # List all worksheets
    print("4. Checking worksheets...")
    worksheets = spreadsheet.worksheets()
    worksheet_titles = [ws.title for ws in worksheets]
    print(f"   Found {len(worksheets)} worksheets:")
    for title in worksheet_titles:
        if title in EXPECTED_SHEETS:
            print(f"     ✅ {title}")
        else:
            print(f"     ⚠️  {title} (not in expected list)")
    print()

    # Check for missing sheets
    missing = set(EXPECTED_SHEETS) - set(worksheet_titles)
    if missing:
        print("   ⚠️  Missing expected sheets:")
        for title in missing:
            print(f"     - {title}")
        print()

    # Test reading from Clients sheet
    print("5. Testing read from Clients sheet...")
    try:
        clients_sheet = spreadsheet.worksheet("Clients")
        # Get first row (headers)
        headers = clients_sheet.row_values(1)
        print(f"   ✅ Read {len(headers)} columns from Clients sheet")
        print(f"   Headers: {', '.join(headers[:5])}...")

        # Get row count
        all_values = clients_sheet.get_all_values()
        print(f"   Total rows: {len(all_values)}")
    except Exception as e:
        print(f"   ❌ Read failed: {e}")
        return False
    print()

    # Test reading from Prompts sheet
    print("6. Testing read from Prompts sheet...")
    try:
        prompts_sheet = spreadsheet.worksheet("Prompts")
        headers = prompts_sheet.row_values(1)
        print(f"   ✅ Read {len(headers)} columns from Prompts sheet")
        all_values = prompts_sheet.get_all_values()
        print(f"   Total rows: {len(all_values)}")

        # Show first prompt if exists
        if len(all_values) > 1:
            first_prompt = all_values[1]
            print(f"   First prompt ID: {first_prompt[0]}")
            print(f"   First prompt slug: {first_prompt[1]}")
    except Exception as e:
        print(f"   ❌ Read failed: {e}")
        return False
    print()

    # Test write to Runs sheet (append a test row)
    print("7. Testing write to Runs sheet...")
    try:
        runs_sheet = spreadsheet.worksheet("Runs")
        test_row = [
            "TEST_RUN_001",  # run_id
            "TEST_CLIENT",   # client_id
            "testing",       # status
            "{}",            # seed_data
            "",              # dossier_id
            "2026-01-12 10:00:00",  # started_at
            "",              # completed_at
            "",              # error_message
            "api",           # triggered_by
            "{}"             # config_snapshot
        ]
        runs_sheet.append_row(test_row)
        print("   ✅ Successfully wrote test row to Runs sheet")
        print("   You can delete this test row from the sheet")
    except Exception as e:
        print(f"   ❌ Write failed: {e}")
        return False
    print()

    print("=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    print("\nYour Google Sheets API setup is working correctly.")
    print("You can now use this sheet with Make.com.")
    print()
    print("Next steps:")
    print("1. Delete the test row from Runs sheet (run_id: TEST_RUN_001)")
    print("2. Use the sheet ID in Make.com: " + SHEET_ID)
    print("3. See docs/google-sheets-implementation/09-paste-ready-api-calls.md")
    print("   for exact API calls to paste into Make.com modules")
    print()

    return True

if __name__ == '__main__':
    success = test_connection()
    sys.exit(0 if success else 1)
