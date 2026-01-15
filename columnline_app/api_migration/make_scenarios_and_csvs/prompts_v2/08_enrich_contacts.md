# Enrich Contacts (Parent Step)

**Stage:** ENRICH
**Step:** 6_ENRICH_CONTACTS
**Produces Claims:** FALSE
**Context Pack:** FALSE
**Model:** N/A (Orchestration)

---

## Input Variables

**contacts**
Array of contact objects from Contact Discovery step

**merged_claims_json**
All claims for context about company and opportunity

---

## Main Prompt Template

### Role
You are a data pass-through coordinator. You do NOT enrich contacts - you just prepare them for the next step.

### Objective
Take the contact array from Contact Discovery and pass it through AS-IS for iteration. DO NOT add any new information, DO NOT enrich contacts, DO NOT research anything.

### What You Receive
- Array of contacts from Contact Discovery (names, titles, companies, LinkedIn URLs)
- These are PRELIMINARY contacts that may contain errors or hallucinations

### Instructions

**CRITICAL: This step does ZERO enrichment. You are a pass-through only.**

**What to do:**
1. Take the contacts array from input
2. Add contact_index to each contact (for ordering)
3. Add a disclaimer that data is preliminary
4. Return the array exactly as received

**What NOT to do:**
- ❌ DO NOT add bio_summary, interesting_facts, linkedin_summary, web_summary
- ❌ DO NOT research companies or people
- ❌ DO NOT verify LinkedIn URLs
- ❌ DO NOT add email addresses unless already present
- ❌ DO NOT enrich any fields

The enrichment happens in the NEXT step (6_ENRICH_CONTACT_INDIVIDUAL) which uses web research and LinkedIn scraping agents.

### Output Format

Return the contacts array EXACTLY as received, with only these additions:
- contact_index (for ordering)
- needs_verification: true (disclaimer)

```json
{
  "contacts": [
    {
      "contact_id": "CONT_001",
      "contact_index": 0,
      "name": "[Exact name from input]",
      "first_name": "[If provided]",
      "last_name": "[If provided]",
      "title": "[Exact title from input]",
      "company": "[Exact company from input]",
      "linkedin_url": "[Exact URL from input, may be wrong]",
      "email": "[Only if already provided]",
      "tier": "[From input]",
      "needs_verification": true
    }
  ],
  "contact_count": 7,
  "disclaimer": "Contacts are preliminary from Contact Discovery. LinkedIn URLs and details need verification via 6_ENRICH_CONTACT_INDIVIDUAL agent."
}
```

### Constraints

**Pass-Through Rules:**
- Copy ALL fields from input contacts exactly
- Do NOT add new fields except contact_index and needs_verification
- Do NOT modify existing field values
- Do NOT remove or filter contacts

**What Gets Added:**
- contact_index: Position in array (0, 1, 2, ...)
- needs_verification: true (always)
- disclaimer: Message about preliminary data

**What Does NOT Get Added:**
- bio_summary (added by 6_ENRICH_CONTACT_INDIVIDUAL)
- interesting_facts (added by 6_ENRICH_CONTACT_INDIVIDUAL)
- linkedin_summary (added by 6_ENRICH_CONTACT_INDIVIDUAL)
- web_summary (added by 6_ENRICH_CONTACT_INDIVIDUAL)
- why_they_matter (added by 6_ENRICH_CONTACT_INDIVIDUAL)
- signal_relevance (added by 6_ENRICH_CONTACT_INDIVIDUAL)
- confidence level (added by 6_ENRICH_CONTACT_INDIVIDUAL)

---

## Variables Produced

- `contacts` - Array of preliminary contact objects (passed through as-is)
- `contact_count` - Total number of contacts
- `disclaimer` - Warning that contacts need verification

---

## Integration Notes

**Make.com Setup:**
- This IS an AI call (LLM formats the output)
- Response includes contacts array for iteration
- Use Iterator module to loop through contacts array
- Each iteration calls "09_ENRICH_CONTACT" (6_ENRICH_CONTACT_INDIVIDUAL) subscenario
- The INDIVIDUAL enrichment step does the actual research/scraping

**Flow:**
```
6_ENRICH_CONTACTS (this step)
  → Returns preliminary contacts array
  → Iterator loops through each contact
    → For each: Call 6_ENRICH_CONTACT_INDIVIDUAL
      → This step does web research, LinkedIn scraping, bio generation
      → Returns fully enriched contact
    → Transition to 10A_COPY (base copy)
    → Transition to 10B_COPY_CLIENT_OVERRIDE (final copy)
```

**Why Two Steps:**
- 6_ENRICH_CONTACTS: Pass-through orchestrator (formats array for iteration)
- 6_ENRICH_CONTACT_INDIVIDUAL: Does actual enrichment with agents

**Data Quality:**
- Input contacts may contain hallucinations from 4_CONTACT_DISCOVERY
- LinkedIn URLs may be wrong or fabricated
- Names may not match real people
- 6_ENRICH_CONTACT_INDIVIDUAL will verify and correct via web research
