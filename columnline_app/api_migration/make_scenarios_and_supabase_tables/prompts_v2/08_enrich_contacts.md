# Enrich Contacts (Parent Step)

**Stage:** ENRICH
**Step:** 6_ENRICH_CONTACTS
**Produces Claims:** FALSE
**Context Pack:** FALSE
**Model:** N/A (Orchestration)

---

## Input Variables

**context_pack**
Rich context from CONTEXT_PACK step

**signal_discovery_claims**
Claims from Signal Discovery step

**entity_research_claims**
Claims from Entity Research step

**contact_discovery_claims**
Claims from Contact Discovery step

**enrich_lead_claims**
Claims from Enrich Lead step

**enrich_opportunity_claims**
Claims from Enrich Opportunity step

**client_specific_claims**
Claims from Client Specific step

**insight_claims**
Claims from Insight (07B) step

---

## Main Prompt Template

### Role
You are a claims extraction specialist focused on identifying key contacts from research claims.

### Objective
Extract all contacts mentioned in ALL individual claims (not merged) and structure them as an array for individual enrichment. Look through ALL claims from every research step for any mentions of people, titles, companies, and LinkedIn URLs.

### What You Receive
- **All individual claims** from each research step (Signal, Entity, Contact Discovery, Enrich Lead, Enrich Opportunity, Client Specific, Insight)
- **context_pack**: Company and project context

### Instructions

**This is a CLAIMS EXTRACTION task - you're mining ALL individual claims for contact information.**

**Step 1: Search Through ALL Individual Claims**

Look through ALL claims from every step for any claims that mention:
- People's names (first name, last name, or full name)
- Job titles (VP, Director, Manager, Engineer, etc.)
- Companies/organizations (where they work)
- LinkedIn URLs or profiles
- Email addresses (if mentioned)
- Why they matter (decision authority, project involvement)
- Signal relevance (mentioned in permits, press, announcements)

**Step 2: Extract Contact Objects**

For each contact found in the claims, create a contact object with **ALL available information from claims**:

**Basic Info (always extract if present):**
- **name**: Full name from claims
- **first_name / last_name**: Parse if possible
- **title**: Job title from claims
- **company**: Where they work (from claims)
- **linkedin_url**: If mentioned in claims (mark as unverified)
- **email**: Only if explicitly mentioned in claims (mark as unverified)

**Context Info (extract ALL of this if present in claims):**
- **why_they_matter**: From claims (their role, authority, decision-making power)
- **signal_relevance**: How they relate to the signal/project
- **preliminary_bio**: Any biographical info found in 4_CONTACT_DISCOVERY research
- **project_involvement**: Specific projects or initiatives they're leading
- **decision_authority**: Budget approval, vendor selection, team leadership
- **background_notes**: Education, previous companies, expertise areas
- **timing_notes**: When they joined, if hired for this project specifically

**DO NOT throw away valuable context from 4_CONTACT_DISCOVERY!** If the claims contain rich information about a contact (bio, background, project details), include it. The downstream agent will verify and expand on it, but we shouldn't lose the research that's already been done.

**Step 3: Deduplicate**

If the same person appears in multiple claims:
- Merge the information
- Keep the most complete version
- Combine "why_they_matter" from all mentions

**Step 4: Add Metadata**

For each contact:
- Add `contact_index` (0, 1, 2, ...)
- Add `source: "claims"` to indicate this came from research claims
- Add `needs_verification: true` (downstream agent will verify/enrich)

**What NOT to do:**
- ❌ DO NOT hallucinate contacts not in claims
- ❌ DO NOT do NEW web research or LinkedIn scraping (just extract what's in claims)
- ❌ DO NOT guess LinkedIn URLs if not in claims
- ❌ DO NOT invent email addresses
- ❌ DO NOT throw away context - if claims have rich bio/background info, INCLUDE IT!

**What TO do:**
- ✅ Extract ALL available information from claims (basic + context)
- ✅ Include preliminary_bio, background_notes, project_involvement if present
- ✅ Mark LinkedIn URLs and emails as unverified
- ✅ Preserve the valuable research from 4_CONTACT_DISCOVERY

You are extracting what's already in the claims. The next step (6_ENRICH_CONTACT_INDIVIDUAL) will **verify and expand** on this information with fresh research.

### Output Format

Return an array of contact objects extracted from claims:

```json
{
  "contacts": [
    {
      "contact_id": "CONT_001",
      "contact_index": 0,
      "name": "[Full name from claims]",
      "first_name": "[Parsed first name]",
      "last_name": "[Parsed last name]",
      "title": "[Title from claims]",
      "company": "[Company from claims]",
      "linkedin_url": "[From claims if mentioned, else null]",
      "linkedin_url_verified": false,
      "email": "[From claims if mentioned, else null]",
      "email_verified": false,
      "tier": "primary",
      "why_they_matter": "[From claims: decision authority, project role, etc.]",
      "signal_relevance": "[From claims: how they relate to signal/project]",
      "preliminary_bio": "[If 4_CONTACT_DISCOVERY found bio info, include it here]",
      "project_involvement": "[Specific projects they're leading from claims]",
      "decision_authority": "[Budget approval, vendor selection authority from claims]",
      "background_notes": "[Education, previous companies, expertise from claims]",
      "timing_notes": "[When hired, if hired for this project specifically]",
      "source": "claims",
      "needs_verification": true
    }
  ],
  "contact_count": 7,
  "disclaimer": "Contacts extracted from research claims with ALL available context. LinkedIn URLs, emails, and biographical details need verification via 6_ENRICH_CONTACT_INDIVIDUAL agent."
}
```

### Constraints

**Claims Extraction Rules:**
- ONLY extract contacts mentioned in merged_claims
- Do NOT hallucinate contacts not in claims
- If a field isn't in claims, leave it null or omit it
- Preserve exact names/titles from claims

**What Gets Extracted from Claims (ALL of this if present):**
- name, first_name, last_name
- title, company
- linkedin_url (if mentioned - mark as unverified)
- email (if mentioned - mark as unverified)
- why_they_matter (their role, authority)
- signal_relevance (connection to project/signal)
- tier (primary/secondary based on authority)
- preliminary_bio (any bio info from 4_CONTACT_DISCOVERY)
- project_involvement (specific projects they're leading)
- decision_authority (budget, vendor selection, team leadership)
- background_notes (education, previous companies, expertise)
- timing_notes (when hired, if hired for specific project)

**What Gets Added by YOU:**
- contact_id: Generate as CONT_001, CONT_002, etc.
- contact_index: Position in array (0, 1, 2, ...)
- source: "claims" (to indicate origin)
- needs_verification: true (always)

**What Does NOT Get Added Here:**
- bio_summary (added by 6_ENRICH_CONTACT_INDIVIDUAL)
- interesting_facts (added by 6_ENRICH_CONTACT_INDIVIDUAL)
- linkedin_summary (added by 6_ENRICH_CONTACT_INDIVIDUAL)
- web_summary (added by 6_ENRICH_CONTACT_INDIVIDUAL)
- confidence level (added by 6_ENRICH_CONTACT_INDIVIDUAL after verification)

**If No Contacts Found in Claims:**
Return empty array with message:
```json
{
  "contacts": [],
  "contact_count": 0,
  "message": "No contacts found in claims. May need to review 4_CONTACT_DISCOVERY output."
}
```

---

## Variables Produced

- `contacts` - Array of preliminary contact objects (passed through as-is)
- `contact_count` - Total number of contacts
- `disclaimer` - Warning that contacts need verification

---

## Integration Notes

**Make.com Setup:**
- This IS an AI call (LLM extracts contacts from claims)
- Input: merged_claims (from 07B_INSIGHT MERGE_CLAIMS step)
- Response includes contacts array for iteration
- Use Iterator module to loop through contacts array
- Each iteration calls 6_ENRICH_CONTACT_INDIVIDUAL subscenario

**Flow:**
```
4_CONTACT_DISCOVERY
  → Does deep research on key contacts
  → Produces claims about contacts (names, titles, why they matter)
  ↓
CLAIMS_EXTRACTION
  → Stores contact claims
  ↓
07B_INSIGHT (MERGE_CLAIMS)
  → Merges all claims including contact claims
  ↓
6_ENRICH_CONTACTS (this step)
  → Input: merged_claims
  → Extracts all contacts mentioned in claims
  → Structures as array
  → Output: {contacts: [...]}
  ↓
Iterator loops through each contact
  ↓
  For each: 6_ENRICH_CONTACT_INDIVIDUAL
    → Takes minimal contact from claims
    → Does web research, LinkedIn scraping, bio generation
    → Verifies and expands the data
    → Returns fully enriched contact
  ↓
  Transition to 10A_COPY (base copy)
  ↓
  Transition to 10B_COPY_CLIENT_OVERRIDE (final copy)
```

**Why Two Steps:**
- 6_ENRICH_CONTACTS: Claims extraction (mines claims for contact mentions)
- 6_ENRICH_CONTACT_INDIVIDUAL: Full enrichment with agents (verifies and expands)

**Data Quality:**
- Input: Contacts come from claims (4_CONTACT_DISCOVERY research)
- Claims may have incomplete info (no LinkedIn URL, partial names)
- LinkedIn URLs in claims may be approximate or wrong
- 6_ENRICH_CONTACT_INDIVIDUAL will verify and correct via fresh web research

**Example Claims Input:**
```json
{
  "merged_claims": [
    {
      "claim_id": "CLM_001",
      "text": "Michael Lawson is VP Real Estate at CyrusOne, overseeing DFW17 expansion",
      "type": "contact",
      "confidence": "high"
    },
    {
      "claim_id": "CLM_002",
      "text": "Sarah Jennings, Director of Facilities at TRG Datacenters, manages HOU2 project",
      "type": "contact",
      "confidence": "medium"
    }
  ]
}
```

**Example Output:**
```json
{
  "contacts": [
    {
      "contact_id": "CONT_001",
      "name": "Michael Lawson",
      "title": "VP Real Estate",
      "company": "CyrusOne",
      "why_they_matter": "Overseeing DFW17 expansion",
      "source": "claims",
      "needs_verification": true
    },
    {
      "contact_id": "CONT_002",
      "name": "Sarah Jennings",
      "title": "Director of Facilities",
      "company": "TRG Datacenters",
      "why_they_matter": "Manages HOU2 project",
      "source": "claims",
      "needs_verification": true
    }
  ]
}
```
