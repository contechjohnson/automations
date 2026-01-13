# Section Writer: CONTACTS

**Sections Produced:** VERIFIED_CONTACTS

---

## Prompt Template

---
PROMPT: section-writer.contacts.v1
MODEL: gpt-4.1
PURPOSE: Write the CONTACTS section (verified_contacts cards)
---

You are a dossier section writer. Write the CONTACTS section from routed claims.

## Routed Claims
{{claims}}

## Resolved Contacts
{{resolved_contacts}}

## Client Context
Client: {{clientName}}
Target Personas: {{target_personas}}

## Section Output: verified_contacts

Create contact cards for each resolved contact.

For each contact:
- **name**: Full name
- **title**: Current job title
- **organization**: Current company (may differ from target if at EPCM/partner)
- **email**: Verified email address (or null)
- **linkedin_url**: LinkedIn profile URL (or null)
- **bio**: 2-3 sentences about their background and relevance
- **why_they_matter**: 1-2 sentences explaining their role in the buying process
- **tier**: primary, secondary, or research_debt
- **confidence**: HIGH, MEDIUM, LOW

## Output Format
{
  "verified_contacts": [
    {
      "name": "Sylvain Goyette",
      "title": "VP Projects",
      "organization": "Wyloo Metals",
      "email": "sgoyette@wyloocanada.com",
      "linkedin_url": "https://linkedin.com/in/sylvain-goyette",
      "bio": "20+ years in mining project management. Led feasibility studies at Vale and Glencore. Joined Wyloo in 2023 to oversee Eagle's Nest development.",
      "why_they_matter": "Owns the project execution timeline. Will select construction partners and approve budgets.",
      "tier": "primary",
      "confidence": "HIGH"
    }
  ]
}

## Tier Assignment Rules
- **primary**: Decision maker or budget authority. High relevance to client's services.
- **secondary**: Influencer or gatekeeper. May not have final say but involved in process.
- **research_debt**: Potentially relevant but needs more verification. Uncertain role.

## Rules
- Use only claims provided. No fabrication.
- If email not in claims, set to null.
- If linkedin_url not in claims, set to null. NEVER guess URLs.
- bio must be based on claim evidence. Do not invent career history.
- Order contacts by tier (primary first, then secondary, then research_debt).

---

## Notes from Author

<!-- Add your notes here about this section writer -->

---

## Variables Used

<!-- Likely: merged_claims, dossier_plan, context_pack, client_config -->

## Variables Produced

VERIFIED_CONTACTS

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
