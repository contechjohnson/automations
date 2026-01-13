#!/usr/bin/env python3
"""
Add v2_ prefix to all Columnline table names
"""

import re

# Read original schema
with open('database/columnline_schema.sql', 'r') as f:
    sql = f.read()

# Table names to prefix
tables = [
    'clients', 'prompts', 'section_definitions',
    'onboarding', 'prep_inputs', 'batch_composer',
    'runs', 'pipeline_steps', 'claims', 'merged_claims',
    'context_packs', 'contacts', 'sections', 'dossiers'
]

# Sort by length (longest first) to avoid partial replacements
tables_sorted = sorted(tables, key=len, reverse=True)

for table in tables_sorted:
    # CREATE TABLE IF NOT EXISTS {table}
    sql = re.sub(
        rf'\bCREATE TABLE IF NOT EXISTS {table}\b',
        f'CREATE TABLE IF NOT EXISTS v2_{table}',
        sql
    )

    # REFERENCES {table}
    sql = re.sub(
        rf'\bREFERENCES {table}\(',
        f'REFERENCES v2_{table}(',
        sql
    )

    # ON {table}(
    sql = re.sub(
        rf'\bON {table}\(',
        f'ON v2_{table}(',
        sql
    )

    # COMMENT ON TABLE {table}
    sql = re.sub(
        rf'\bCOMMENT ON TABLE {table}\b',
        f'COMMENT ON TABLE v2_{table}',
        sql
    )

# Update index names to include v2
sql = re.sub(
    r'CREATE INDEX IF NOT EXISTS idx_',
    'CREATE INDEX IF NOT EXISTS idx_v2_',
    sql
)

# Update comment at top
sql = sql.replace(
    '-- Columnline Dossier Pipeline Schema',
    '-- Columnline V2 Dossier Pipeline Schema'
)

# Write v2 schema
with open('database/columnline_schema_v2.sql', 'w') as f:
    f.write(sql)

print("✅ Created database/columnline_schema_v2.sql with v2_ prefixes")
print("\nTables renamed:")
for table in sorted(tables):
    print(f"  {table} → v2_{table}")
