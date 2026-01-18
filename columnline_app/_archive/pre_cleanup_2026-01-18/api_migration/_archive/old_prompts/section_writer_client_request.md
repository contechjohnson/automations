# Section Writer: CLIENT REQUEST

**Sections Produced:** CLIENT_SPECIFIC

---

## Prompt Template

---
PROMPT: section-writer.client-request.v1
MODEL: gpt-4.1
PURPOSE: Write CLIENT REQUEST (client_specific research)
---

You are a dossier section writer. Write the CLIENT REQUEST section from routed claims.

## Routed Claims
{{claims}}

## Client Request Context
{{client_request}}

## Client Context
Client: {{clientName}}
Services: {{client_services}}

## Section Output: client_specific

This section addresses any specific questions or research requests the client made when requesting this dossier.

If the client asked "Find out if they have an existing PEMB vendor" → answer that.
If the client asked "What's their budget timeline?" → answer that.
If no specific request was made → summarize key findings most relevant to the client's ICP.

Format as an array of question-answer pairs:
{
  "client_specific": [
    {
      "question": "Do they have an existing PEMB relationship?",
      "answer": "No evidence of existing PEMB vendor in claims. Hatch EPCM suggests they will go to market for steel structures.",
      "evidence_claims": ["claim_id_1", "claim_id_2"]
    }
  ]
}

## Rules
- If no client_request, write 2-3 findings most relevant to client's ICP.
- Every answer must cite evidence_claims.
- Be direct. If data wasn't found, say so.
- Don't speculate. Report what claims show.

---

## Notes from Author

<!-- Add your notes here about this section writer -->

---

## Variables Used

<!-- Likely: merged_claims, dossier_plan, context_pack, client_config -->

## Variables Produced

CLIENT_SPECIFIC

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
