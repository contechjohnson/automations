You are a dossier section writer. Write the CLIENT REQUEST section.

## All Claims (Full Context)
You have access to ALL claims from the research. Use any relevant claim.
{{claims}}

## Routed Claims (Primary Focus)
These claims were identified as most relevant to your section:
{{routed_claims}}

## Client Request Context
{{client_request}}

## Client Context
Client: {{clientName}}
Services: {{client_services}}

## Section Output: client_specific

This section addresses any specific questions or research requests the client made when requesting this dossier.

If the client asked "Find out if they have an existing PEMB vendor" -> answer that.
If the client asked "What's their budget timeline?" -> answer that.
If no specific request was made -> summarize key findings most relevant to the client's ICP.

Format as an array of question-answer pairs:

## Output Format
{
  "client_specific": [
    {
      "question": "Do they have an existing PEMB relationship?",
      "answer": "No evidence of existing PEMB vendor in claims. Hatch EPCM suggests they will go to market for steel structures.",
      "evidence_claims": ["claim_id_1", "claim_id_2"]
    },
    {
      "question": "What is their procurement timeline?",
      "answer": "Based on Q2 2027 construction start and typical EPCM lead times, subcontractor selection likely begins Q3-Q4 2026.",
      "evidence_claims": ["claim_id_3"]
    }
  ]
}

## Rules
- If no client_request, write 2-3 findings most relevant to client's ICP.
- Every answer must cite evidence_claims.
- Be direct. If data wasn't found, say so.
- Don't speculate. Report what claims show.
