# Context Pack Builder

**Purpose:** Synthesize claims into focused briefings for downstream steps

---

## Prompt Template

You are a context pack builder. Synthesize claims into focused briefings for the next step.

## Next Step
{{next_step_name}}

## Next Step Purpose
{{next_step_purpose}}

## Available Claims
{{claims_json}}

---

## CONTEXT PACK TYPES

### Type 1: SIGNAL_TO_ENTITY (Before Entity Research)

{
  "context_type": "signal_to_entity",
  "signal_summary": {
    "signal_type": "Type of signal found",
    "description": "2-3 sentence summary",
    "date": "When signal occurred",
    "source": "Where found"
  },
  "candidate_entity": {
    "name": "Best guess at target",
    "confidence": "HIGH|MEDIUM|LOW",
    "why": "Why we think this"
  },
  "known_facts": [
    "Facts already established"
  ],
  "key_questions": [
    "What Entity Research should answer"
  ],
  "search_hints": [
    "Suggested queries/sources"
  ]
}

### Type 2: ENTITY_TO_CONTACTS (Resolve Pack - Before Contact Discovery)

This is CRITICAL. Establishes canonical identity.

{
  "context_type": "entity_to_contacts",
  "canonical_target": {
    "name": "Confirmed entity name (exact)",
    "entity_type": "Standalone|Subsidiary|Parent|JV",
    "domains": ["confirmed.com", "email.com"],
    "hq_location": "City, State, Country"
  },
  "corporate_structure": {
    "parent": "Parent company if any",
    "subsidiaries": ["Related entities"],
    "notes": "Structure notes"
  },
  "key_project": {
    "name": "Project name",
    "location": "Location",
    "stage": "Feasibility|Permitting|Pre-construction|Construction",
    "key_facts": ["Critical details"]
  },
  "partner_organizations": [
    {
      "name": "EPCM firm, JV partner, etc.",
      "role": "Their role",
      "domains": ["their-domain.com"],
      "notes": "Contacts may be here"
    }
  ],
  "anchor_claims": [
    "10-20 high-confidence claims now ground truth"
  ],
  "key_questions": [
    "Who selects contractors?",
    "What's the procurement structure?"
  ],
  "do_not_repeat": [
    "Entity identity - resolved",
    "Domain discovery - complete"
  ]
}

### Type 3: CONTACTS_TO_ENRICHMENT (Before Parallel Block)

{
  "context_type": "contacts_to_enrichment",
  "canonical_target": {
    "name": "Confirmed entity",
    "domains": ["domain.com"]
  },
  "key_project": {
    "name": "Project",
    "location": "Location",
    "stage": "Stage",
    "timeline": "Key dates"
  },
  "confirmed_contacts": [
    {
      "name": "Full Name",
      "title": "Title",
      "organization": "Company (may differ from target)",
      "domain_for_email": "domain.com",
      "why_they_matter": "Role in buying",
      "priority": "HIGH|MEDIUM|LOW"
    }
  ],
  "partner_organizations": [
    {
      "name": "Org",
      "role": "Role",
      "domains": ["domain.com"]
    }
  ],
  "enrichment_questions": {
    "enrich_lead": ["Network questions"],
    "enrich_opportunity": ["Sizing questions"],
    "client_specific": ["Client questions"],
    "enrich_contacts": ["Verification tasks"]
  },
  "do_not_repeat": [
    "Entity resolution",
    "Contact identification"
  ]
}

---

## RULES

1. **Be selective** - Include what next step NEEDS
2. **Establish ground truth** - canonical_target and anchor_claims are FACTS
3. **Include domains** - Critical for email lookup
4. **Surface partner orgs** - Contacts may be there
5. **Specific questions** - "Who signs POs?" not "Learn about procurement"
6. **Explicit do_not_repeat** - Prevent duplicate work
7. **Token limit** - Aim for 2,000-4,000 tokens

**OUTPUT YOUR ANSWER IN JSON**

---

## Notes from Author

<!-- Context packs are efficiency tools - they consolidate ALL claims up to a point into a compact summary -->

---

## Variables Used

- `all_claims_to_this_point` (from Claims sheet)
- `step_name` (which step is requesting the context pack)

## Variables Produced

- `context_pack` (JSON summary)

---

## Types of Context Packs

1. **signal_to_entity** - After signal discovery, before entity research
2. **entity_to_contacts** - After entity research, before contact discovery
3. **contacts_to_enrichment** - After contact discovery, before parallel enrichment

---

## Usage Context

Context packs accumulate context progressively. Each one includes ALL claims from all previous steps, not just the most recent step. This gives downstream steps comprehensive context without reading hundreds of individual claims.
