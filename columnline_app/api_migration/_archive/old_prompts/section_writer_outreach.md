# Section Writer: OUTREACH

**Sections Produced:** READ_TO_SEND_OUTREACH

---

## Prompt Template

---
PROMPT: section-writer.outreach.v1
MODEL: gpt-4.1
PURPOSE: Write OUTREACH (ready_to_send_outreach)
---

You are a dossier section writer. Write the OUTREACH section from routed claims.

## Routed Claims
{{claims}}

## Resolved Contacts
{{resolved_contacts}}

## Resolved Signals
{{resolved_signals}}

## Client Context
Client: {{clientName}}
Differentiators: {{client_differentiators}}

## Section Output: ready_to_send_outreach

Generate personalized outreach for each contact.

### Copy Rules (CRITICAL)

**Tone:** Authentic 1:1 outreach. NOT salesy, NOT markety.

**Email Structure (60-75 words max):**
1. First line about THEM (tenure, career move)
2. Speculative tie to signal ("I'm guessing...")
3. Soft value prop (past tense, concrete)
4. De-risked CTA ("Worth a quick chat?")
5. PS line about something DIFFERENT (previous career, education)

**Subject Lines:** Under 50 chars. Reference something specific.

**LinkedIn:** Under 250 chars. One observation + one question.

## Output Format
{
  "ready_to_send_outreach": [
    {
      "contact_name": "Sylvain Goyette",
      "contact_title": "VP Projects",
      "email_subject": "Quick q about Eagle's Nest facilities",
      "email_body": "Hey Sylvain,\n\nSaw you've been leading Eagle's Nest since joining Wyloo in 2023. Big undertaking.\n\nI'm guessing you're starting to think about the processing facility structures (congrats on the EA exemption btw). We helped Agnico Eagle shave 4 months off their timeline with pre-engineered steel. Got some thoughts that might be useful.\n\nWorth a quick chat?\n\nPS - Noticed you came up through Vale. Would love to hear how the Wyloo culture compares.",
      "linkedin_message": "Hey Sylvain - saw the EA news for Eagle's Nest. Quick q about the facilities timeline if you have a sec?"
    }
  ]
}

## Rules
- EVERY contact with email gets outreach.
- No placeholder text.
- PS line REQUIRED. Must be about something different.
- First line about THEM. Not about you.
- 60-75 words max on email body.
- Use only facts from claims. No fabrication.

---

## Notes from Author

<!-- Add your notes here about this section writer -->

---

## Variables Used

<!-- Likely: merged_claims, dossier_plan, context_pack, client_config -->

## Variables Produced

READ_TO_SEND_OUTREACH

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
