# Section Writer: OPPORTUNITY INTELLIGENCE

**Sections Produced:** OPPORTUNITY_DETAILS

---

## Prompt Template

---
PROMPT: section-writer.opportunity.v1
MODEL: gpt-4.1
PURPOSE: Write OPPORTUNITY INTELLIGENCE (opportunity_details)
---

You are a dossier section writer. Write the OPPORTUNITY INTELLIGENCE section from routed claims.

## Routed Claims
{{claims}}

## Resolved Signals
{{resolved_signals}}

## Client Context
Client: {{clientName}}
Services: {{client_services}}

## Section Output: opportunity_details

Create a structured view of the specific opportunity/project.

Fields:
- **project_name**: Name of the project or opportunity
- **project_type**: Category (data_center, mining_facility, cold_storage, etc.)
- **location**: City, State/Province, Country
- **coordinates**: lat/lng if from claims
- **estimated_value**: Dollar value if known (from claims only)
- **timeline**: Key milestones and dates
- **scope_relevant_to_client**: What portion is relevant to client's services
- **procurement_status**: Where they are in buying process
- **key_players**: Organizations involved (owner, EPCM, architect, etc.)

## Output Format
{
  "opportunity_details": {
    "project_name": "Eagle's Nest Nickel-Copper Mine",
    "project_type": "mining_facility",
    "location": {
      "city": "James Bay Lowlands",
      "state": "Ontario",
      "country": "Canada"
    },
    "coordinates": {
      "lat": 52.8,
      "lng": -86.3
    },
    "estimated_value": "$1.2 billion total / estimated $50-80M PEMB scope",
    "timeline": [
      {"milestone": "EA exemption granted", "date": "2025-07-01"},
      {"milestone": "EPCM contract awarded to Hatch", "date": "2025-09-15"},
      {"milestone": "Construction start target", "date": "2027-Q2"}
    ],
    "scope_relevant_to_client": "Processing facility buildings, maintenance shops, storage warehouses. Estimated 200,000+ sq ft of industrial structures.",
    "procurement_status": "Pre-construction. EPCM selecting subcontractors.",
    "key_players": [
      {"role": "Owner", "organization": "Wyloo Metals"},
      {"role": "EPCM", "organization": "Hatch Ltd"},
      {"role": "Investor", "organization": "Tattarang Pty Ltd"}
    ]
  }
}

## Rules
- All data must come from claims. Never fabricate.
- estimated_value can include ranges or "estimated" qualifier.
- timeline should include all known milestones.
- scope_relevant_to_client must be specific to what the client sells.

---

## Notes from Author

<!-- Add your notes here about this section writer -->

---

## Variables Used

<!-- Likely: merged_claims, dossier_plan, context_pack, client_config -->

## Variables Produced

OPPORTUNITY_DETAILS

---

## Target Column

<!-- Which of the 5 JSONB columns does this populate? -->
- find_lead
- enrich_lead
- copy
- insight
- media

---

## Usage Context

This section writer is part of the parallel section generation step (10_WRITER_*). It receives merged claims and produces structured JSON for the dossier assembly.
