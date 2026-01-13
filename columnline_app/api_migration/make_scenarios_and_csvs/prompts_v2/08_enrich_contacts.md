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
You are an orchestration coordinator preparing contact enrichment tasks for parallel execution.

### Objective
Initialize parallel contact enrichment by preparing individual enrichment tasks. Each contact gets enriched separately (LinkedIn scraping, web research, bio generation) then reassembled.

### What You Receive
- Array of contacts from Contact Discovery (names, titles, LinkedIn URLs, basic info)
- Merged claims providing context about company, project, and opportunity

### Instructions

**This is NOT an AI prompt - it's an orchestration step.**

The 6_ENRICH_CONTACTS step does the following:

**Step 1: Validate Contact Array**
- Ensure contacts array is not empty
- Check that each contact has minimum required fields:
  - name (or first_name + last_name)
  - title
  - company
  - linkedin_url (preferred) or email

**Step 2: Prepare Enrichment Tasks**
For each contact in the array:
- Create a task payload containing:
  - contact_data (the contact object)
  - merged_claims (for context)
  - contact_index (position in array)

**Step 3: Launch Parallel Enrichment**
- Call subscenario "09_ENRICH_CONTACT" for each contact
- Pass individual task payload to each subscenario
- Execute in parallel (all contacts enriched simultaneously)

**Step 4: Collect Results**
- Wait for all subscenarios to complete
- Collect enriched contact objects
- Preserve order (contact_index ensures correct sequencing)

**Step 5: Return Enriched Contacts**
- Return array of fully enriched contacts
- Each contact now has: bio, interesting facts, signal relevance, research summaries

### Output Format

```json
{
  "enriched_contacts": [
    {
      "contact_id": "CONT_001",
      "name": "[Contact Name]",
      "title": "[Title from ICP]",
      "company": "[Company Name]",
      "linkedin_url": "[LinkedIn URL]",
      "email": "[email address]",
      "bio_summary": "[Bio summary text]",
      "interesting_facts": ["[fact 1]", "[fact 2]"],
      "linkedin_summary": "[LinkedIn research summary]",
      "web_summary": "[Web research summary]",
      "why_they_matter": "[Relevance description]",
      "signal_relevance": "[How they relate to signal]",
      "tier": "primary",
      "confidence": "HIGH"
    }
  ],
  "contacts_enriched_count": 7,
  "failed_count": 0
}
```

### Constraints

**Orchestration Logic:**
- Launch all enrichment tasks in parallel (not sequential)
- Handle failures gracefully (one failed contact shouldn't stop others)
- Preserve contact order for reassembly
- Pass sufficient context to each enrichment task

**Error Handling:**
- If a contact lacks LinkedIn URL, enrichment still attempts with web search
- If enrichment fails for a contact, mark as "LOW" confidence but include
- If ALL contacts fail, propagate error to parent pipeline

---

## Variables Produced

- `enriched_contacts` - Array of fully enriched contact objects
- `contacts_enriched_count` - Number successfully enriched
- `failed_count` - Number that failed enrichment

---

## Integration Notes

**Make.com Setup:**
- This is a "Call Subscenario" step, not an AI call
- Use Iterator module to loop through contacts array
- Each iteration calls "09_ENRICH_CONTACT" subscenario in parallel
- Use Array Aggregator to reassemble results

**Parallel Execution:**
- Make.com allows parallel subscenario calls via Iterator
- All enrichments happen simultaneously (faster than sequential)
- Order preserved via contact_index field

**Next Steps:**
- Enriched contacts flow to Copy generation (generic + client-specific)
- Also included in Contacts section writer for dossier
