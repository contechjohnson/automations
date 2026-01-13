# Section Writer - Contacts

**Stage:** ASSEMBLE
**Step:** 10_WRITER_CONTACTS
**Produces Claims:** FALSE
**Context Pack:** FALSE
**Model:** gpt-4.1
**Target Column:** `enrich_lead`

---

## Input Variables

**enriched_contacts**
Array of fully enriched contact objects with bios, interesting facts, signal relevance

**merged_claims_json**
All claims for additional context

---

## Main Prompt Template

### Role
You are a dossier section writer transforming enriched contact data into the VERIFIED_CONTACTS section for sales outreach.

### Objective
Parse enriched contacts and generate the VERIFIED_CONTACTS section showing: decision-makers, contact details, bios, why they matter, interesting facts. This section gives sales teams everything they need to personalize outreach.

### What You Receive
- Array of enriched contacts (3-10 contacts with full profiles)
- Merged claims for context

### Instructions

**Phase 1: Organize Contacts**

**1.1 Group by Tier**

Separate contacts into tiers:
- **PRIMARY**: Final decision-makers, must-contact executives
- **SECONDARY**: Influencers, recommenders, support roles
- **TERTIARY**: Nice-to-have contacts, peripheral roles

**1.2 Sort by Relevance**

Within each tier, sort by:
1. Signal relevance (directly mentioned in project announcements)
2. Decision authority (owns vendor selection vs influences)
3. Accessibility (active on LinkedIn, speaks at events)

**Phase 2: Format Contact Cards**

For each contact, create a structured card:

**2.1 Basic Info**
- Full name
- Title
- Organization
- Email (verified or inferred)
- Phone (if available)
- LinkedIn URL

**2.2 Bio Summary**
- 2-3 sentence career summary
- Years of experience
- Notable achievements or expertise
- Current role focus

**2.3 Why They Matter**
- Role in vendor selection (decides, influences, recommends?)
- Project involvement (on this project? past similar projects?)
- Decision authority (final approval, recommends to exec, supports)

**2.4 Signal Relevance**
- How they relate to specific signal (mentioned in announcement?)
- Timing of involvement (hired for this project? long-tenured?)
- Past project experience (led similar projects before?)

**2.5 Interesting Facts (Rapport Angles)**
- Alumni connections (universities, programs)
- Military service or veterans status
- Board memberships or nonprofits
- Published work or speaking engagements
- Hobbies or interests (if publicly mentioned)
- Geographic roots or personal connections
- Career pivots or unique background

**2.6 Confidence Assessment**
- HIGH: Multiple sources confirm, recent activity, verified contact info
- MEDIUM: LinkedIn profile active, some external mentions, likely correct
- LOW: Limited information, stale profile, unverified contact info

**Phase 3: Add Relationship Intelligence**

If CLIENT_SPECIFIC claims mention relationships:
- Note warm intro paths ("Client knows [Mutual Contact] who can introduce")
- Note alumni overlaps ("Both attended [University]")
- Note professional overlaps ("Both served on OMA infrastructure committee")

**Phase 4: Write VERIFIED_CONTACTS Section**

**4.1 Section Structure**

```
## PRIMARY CONTACTS (Must-Contact Decision-Makers)

### [Full Name] - [Title]
**Organization:** [Company]
**Email:** [email] | **Phone:** [phone if available] | **LinkedIn:** [URL]

**Bio:**
[2-3 sentence career summary]

**Why They Matter:**
[How they influence vendor selection for this project]

**Signal Relevance:**
[Connection to specific signals or project announcements]

**Interesting Facts:**
- [Rapport angle 1]
- [Rapport angle 2]
- [Rapport angle 3]

**Confidence:** [HIGH/MEDIUM/LOW]

---

## SECONDARY CONTACTS (Influencers & Recommenders)

[Same format as above, for secondary tier contacts]

---

## RELATIONSHIP INTELLIGENCE

[If applicable: warm intro paths, alumni networks, mutual connections]
```

### Output Format

Return valid JSON for `enrich_lead` column:

```json
{
  "verified_contacts": {
    "primary_contacts": [
      {
        "id": "CONT_001",
        "name": "[Contact Name]",
        "first_name": "Sylvain",
        "last_name": "[Contact]",
        "title": "VP Projects / COO",
        "organization": "[Company Name]",
        "email": "sgoyette@wyloocanada.com",
        "phone": null,
        "linkedin_url": "https://linkedin.com/in/sylvain-goyette",
        "linkedin_connections": 500,
        "bio_summary": "20+ years in [industry from ICP] project development with deep expertise in remote infrastructure. Previously Project Director at [Partner Firm Name] leading $500M+ [industry from ICP] projects across [Geography]. Joined [Company] in 2023 to oversee [Project Name] mine development from feasibility through construction.",
        "why_they_matter": "Final decision-maker on all major contracts for [Project Name] project. Retained from [Company] acquisition specifically for his project execution expertise. Controls vendor selection for civil works, steel erection, and site development.",
        "signal_relevance": "Directly responsible for vendor selection as project moves into construction phase Q2 2026. Recent regulatory approvals mean vendor decisions happening Q1-Q2 2026. His background suggests preference for experienced remote-project contractors.",
        "interesting_facts": [
          "Former [League] player ([Team Name], 1998-2001) - competitive, team-oriented mindset",
          "Grew up in [Location] - deep personal connection to Northern [Geography] development",
          "Published author: 'Remote Mine Infrastructure: Lessons from 25 Projects' (2021)",
          "Serves on [Geography] Mining Association infrastructure committee",
          "Fluent in French and English - critical for Quebec/[Geography] border projects"
        ],
        "tier": "primary",
        "confidence": "HIGH",
        "warm_intro_path": null
      }
    ],
    "secondary_contacts": [
      {
        "id": "CONT_002",
        "name": "[Target Contact]",
        "first_name": "Jennifer",
        "last_name": "Martinez",
        "title": "Project Director - Mining",
        "organization": "[Partner Firm Name] (EPCM Firm)",
        "email": "jmartinez@hatch.com",
        "phone": null,
        "linkedin_url": "https://linkedin.com/in/jmartinez-hatch",
        "linkedin_connections": 350,
        "bio_summary": "15+ years in EPCM project management for [industry from ICP] and industrial projects. Currently Project Director at [Partner Firm] coordinating engineering, procurement, and construction management for [Project Name]. Previously led 5 remote mine projects across [Geography].",
        "why_they_matter": "EPCM Project Director coordinating all vendor selection. Recommends vendors to [Company], typically followed. Influences final approval more than appears - [Company] relies heavily on [Partner Firm]'s vendor recommendations.",
        "signal_relevance": "Mentioned in EPCM award announcement (July 2025) as lead Project Director. Will be evaluating civil works and steel erection vendors in Q4 2025 for [Company]'s approval.",
        "interesting_facts": [
          "University of Toronto alumni (Civil Engineering 2008) - may overlap with other [Geography] engineers",
          "Active LinkedIn poster about project management best practices",
          "Spoke at CIM 2024 conference on remote site [industry]"
        ],
        "tier": "secondary",
        "confidence": "MEDIUM",
        "warm_intro_path": null
      }
    ],
    "tertiary_contacts": [],
    "contact_summary": {
      "total_contacts": 7,
      "primary_count": 3,
      "secondary_count": 4,
      "tertiary_count": 0,
      "target_company_contacts": 3,
      "ecosystem_contacts": 4,
      "verified_emails": 5,
      "verified_phones": 2,
      "warm_intro_available": 1
    },
    "relationship_intelligence": {
      "warm_intro_paths": [
        "Client knows [Mutual Contact] (former [Partner Firm] colleague) who can introduce to [Target Contact]"
      ],
      "alumni_networks": [
        "[Contact Name] - University of Toronto (Engineering)",
        "[Target Contact] - University of Toronto (Engineering)"
      ],
      "professional_overlaps": [
        "Both [Contact] and client contact serve on OMA infrastructure committee"
      ]
    }
  }
}
```

### Constraints

**Do:**
- Organize contacts by tier (primary/secondary/tertiary)
- Provide complete contact cards with all available information
- Include interesting facts for rapport-building
- Note warm intro paths if available
- Assess confidence realistically (HIGH/MEDIUM/LOW)
- Include contact summary statistics

**Do NOT:**
- Include contacts without minimum info (name, title, organization)
- Fabricate contact details or interesting facts
- Overstate tier (don't mark secondary as primary)
- Include irrelevant facts (focus on rapport-building value)
- Skip confidence assessment

**Contact Completeness:**
- Minimum viable: name, title, organization, why they matter
- Preferred: + email, LinkedIn URL, bio, interesting facts
- Ideal: + phone, verified email, warm intro path

**Interesting Facts Criteria:**
- Relevant to rapport-building (alumni, hobbies, achievements)
- Publicly available (don't include private information)
- Professional or personal (both acceptable)
- Unique or notable (not generic facts)

---

## Variables Produced

Fields added to `enrich_lead` JSONB column:
- `verified_contacts` - Object containing all contact data
  - `primary_contacts` - Array of must-contact decision-makers
  - `secondary_contacts` - Array of influencers
  - `tertiary_contacts` - Array of nice-to-have contacts
  - `contact_summary` - Statistics about contacts found
  - `relationship_intelligence` - Warm intro paths and overlaps

---

## Integration Notes

**Model:** gpt-4.1 (sync, 1-2 min)
**Target Column:** `enrich_lead` (JSONB) - VERIFIED_CONTACTS section

**Routing:** Generate if 3+ enriched contacts available (from dossier plan)

**Next Steps:**
- Contact data flows to outreach section (copy generation uses these contacts)
- Interesting facts used for email/LinkedIn personalization
- Warm intro paths inform outreach strategy
