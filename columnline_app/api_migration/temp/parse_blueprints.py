#!/usr/bin/env python3
"""Parse Make.com blueprint JSONs and extract key information."""

import json
import os
from pathlib import Path

BLUEPRINTS_DIR = Path("columnline_app/api_migration/make_scenarios_and_csvs")

def parse_blueprint(filepath: Path) -> dict:
    """Extract key info from a Make.com blueprint JSON."""
    with open(filepath) as f:
        data = json.load(f)

    flow = data.get("flow", [])

    # Categorize modules
    module_types = {}
    llm_calls = []
    sheets_ops = []
    http_calls = []
    subscenarios = []
    variables = []

    for module in flow:
        mod_type = module.get("module", "unknown")
        module_types[mod_type] = module_types.get(mod_type, 0) + 1

        # Get designer name if available
        name = module.get("metadata", {}).get("designer", {}).get("name", "")

        if "openrouter" in mod_type.lower() or "openai" in mod_type.lower():
            llm_calls.append({
                "id": module.get("id"),
                "name": name,
                "type": mod_type
            })
        elif "google-sheets" in mod_type:
            mapper = module.get("mapper", {})
            sheets_ops.append({
                "id": module.get("id"),
                "name": name,
                "cell": mapper.get("cell", ""),
                "sheet": mapper.get("sheetId", ""),
                "op": mod_type.split(":")[-1]
            })
        elif "http:" in mod_type:
            mapper = module.get("mapper", {})
            http_calls.append({
                "id": module.get("id"),
                "name": name,
                "url": mapper.get("url", "")[:100] if mapper.get("url") else ""
            })
        elif "CallSubscenario" in mod_type or "StartSubscenario" in mod_type:
            subscenarios.append({
                "id": module.get("id"),
                "name": name,
                "type": mod_type
            })
        elif "SetVariable" in mod_type or "GetVariable" in mod_type:
            variables.append({
                "id": module.get("id"),
                "name": name,
                "type": mod_type
            })

    return {
        "name": data.get("name", filepath.stem),
        "total_modules": len(flow),
        "module_types": module_types,
        "llm_calls": llm_calls,
        "sheets_ops": sheets_ops,
        "http_calls": http_calls,
        "subscenarios": subscenarios,
        "variables": variables
    }

def main():
    results = {}

    for filepath in sorted(BLUEPRINTS_DIR.glob("*.json")):
        print(f"\n=== {filepath.name} ===")
        info = parse_blueprint(filepath)
        results[filepath.name] = info

        print(f"Name: {info['name']}")
        print(f"Total modules: {info['total_modules']}")
        print(f"Module types: {info['module_types']}")

        if info['llm_calls']:
            print(f"LLM calls ({len(info['llm_calls'])}):")
            for c in info['llm_calls']:
                print(f"  - {c['name'] or c['id']}: {c['type']}")

        if info['sheets_ops']:
            print(f"Sheets ops ({len(info['sheets_ops'])}):")
            for s in info['sheets_ops'][:5]:  # First 5 only
                print(f"  - {s['name'] or s['id']}: {s['op']} {s['sheet']}!{s['cell']}")
            if len(info['sheets_ops']) > 5:
                print(f"  ... and {len(info['sheets_ops']) - 5} more")

        if info['subscenarios']:
            print(f"Subscenarios ({len(info['subscenarios'])}):")
            for s in info['subscenarios']:
                print(f"  - {s['name'] or s['id']}: {s['type']}")

    # Save summary
    with open("columnline_app/api_migration/temp/blueprint_summary.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n\nSummary saved to columnline_app/api_migration/temp/blueprint_summary.json")

if __name__ == "__main__":
    main()
