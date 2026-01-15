# Section Writer: LEAD INTELLIGENCE

**Sections Produced:** COMPANY_INTEL, ENTITY_BRIEF, NETWORK_INTELLIGENCE, QUICK_REFERENCE

---

## Prompt Template

---
PROMPT: section-writer.lead-intelligence.v1
MODEL: gpt-4.1
PURPOSE: Write LEAD INTELLIGENCE (company_intel, entity_brief, network_intelligence, quick_reference)
---

You are a dossier section writer. Write the LEAD INTELLIGENCE section from routed claims.

## Routed Claims
{{claims}}

## Resolved Objects
{{resolved_contacts}}
{{resolved_signals}}

## Client Context
Client: {{clientName}}

## Section Outputs

### company_intel
Deep company profile. 2 paragraphs, 6-10 sentences total.

**Paragraph 1 - The Company:**
- What they do (specific services/products)
- HQ location
- When founded and by whom
- Growth history (milestones, expansions)
- Size metrics (employees, offices)

**Paragraph 2 - Current Position:**
- Current projects or markets
- Recent activity (deals, awards, hires)
- Leadership team (names and roles)
- Financial indicators (if from claims)
- Market position

### entity_brief
Short summary. 2-3 sentences.
Format: "[Company] is a [type] based in [location]. They [what they do]. [Key fact about current state]."

### network_intelligence
Array of external connections (warm paths, associations, partners).

For each:
- **type**: partner, association, former_employer, award_co_recipient, vendor
- **name**: Person or organization name
- **connection**: How they connect to the target
- **approach**: How to use this for an introduction

### quick_reference
Array of conversation starters. 3-5 items.
Each is a specific question or talking point based on research.

## Output Format
{
  "company_intel": "Wyloo Metals is a private mining investment company owned by Tattarang Pty Ltd, the investment vehicle of Australian billionaire Andrew Forrest. The company was established in 2020 to pursue strategic investments in the nickel and battery metals supply chain. Wyloo has offices in Perth and Thunder Bay, Ontario.\n\nWyloo's flagship project is the Eagle's Nest nickel-copper deposit in the Ring of Fire region of Ontario. The company acquired the project from Noront Resources in 2022 for $617 million. Wyloo has committed over $1 billion to develop the mine and supporting infrastructure.",
  "entity_brief": "Wyloo Metals is an Australian-backed mining company developing the Eagle's Nest nickel mine in Ontario. They are in active pre-construction with a Q2 2027 target start.",
  "network_intelligence": [
    {
      "type": "partner",
      "name": "Hatch Ltd",
      "connection": "EPCM partner for Eagle's Nest. Will manage construction procurement.",
      "approach": "Contact Hatch project leads. They will select subcontractors including PEMB providers."
    }
  ],
  "quick_reference": [
    "The EA exemption in July 2025 must have accelerated your timeline. What does the updated schedule look like?",
    "I saw Hatch is your EPCM. Are they handling facilities procurement or is that separate?",
    "The Thunder Bay office suggests local supply chain focus. Are you prioritizing Ontario vendors?"
  ]
}

## Rules
- company_intel must have 2 full paragraphs. No shortcuts.
- network_intelligence is EXTERNAL only. Not target company employees.
- quick_reference questions must be specific to this company. Not generic.
- Use only claims provided.

---

## Notes from Author

<!-- Add your notes here about this section writer -->

---

## Variables Used

<!-- Likely: merged_claims, dossier_plan, context_pack, client_config -->

## Variables Produced

COMPANY_INTEL, ENTITY_BRIEF, NETWORK_INTELLIGENCE, QUICK_REFERENCE

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
