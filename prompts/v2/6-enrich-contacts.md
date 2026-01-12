## EXTRACT KEY CONTACTS FROM RESEARCH CLAIMS

You are analyzing research claims to identify key contacts for sales outreach.

### INPUT

**All Research Claims:**
{{all_claims}}

**Target Company:**
{{company_name}} ({{domain}})

**ICP Titles:**
{{target_titles}}

### TASK

Scan ALL claims and extract every person who could be a relevant contact.

**Where to find people:**
- `claim_type: "CONTACT"` - Direct contact mentions
- `claim_type: "RELATIONSHIP"` - People mentioned in relationships
- `claim_type: "ATTRIBUTE"` - May contain emails, LinkedIn URLs

**For each person, extract:**
- Name
- Title
- Organization
- Domain (for email lookup)
- Email (if found in claims - check ATTRIBUTE claims!)
- LinkedIn URL (if found in claims)
- Signal relevance (which SIGNAL claims connect to this person)
- Evidence claim IDs

### CRITICAL

Some claims already have emails! For example:
- "Jennifer Schumacher's email is jschumacher@ndep.nv.gov" (ATTRIBUTE claim)
- "Mark Talavera's email is mtalavera@ndep.nv.gov" (ATTRIBUTE claim)

**Do NOT miss these** - they save enrichment API calls.

### OUTPUT FORMAT
```json
{
  "contacts": [
    {
      "name": "Jennifer Schumacher",
      "title": "Chief of Bureau of Air Pollution Control",
      "organization": "Nevada Department of Environmental Protection",
      "domain": "ndep.nv.gov",
      "email_from_claims": "jschumacher@ndep.nv.gov",
      "linkedin_from_claims": null,
      "signal_relevance": "Manages air permitting for Goldfield Project",
      "evidence_claim_ids": ["claim_014", "claim_015", "claim_018"],
      "needs_enrichment": {
        "email": false,
        "linkedin": true
      }
    },
    {
      "name": "Paul Tomory",
      "title": "President and CEO",
      "organization": "Centerra Gold Inc.",
      "domain": "centerragold.com",
      "email_from_claims": null,
      "linkedin_from_claims": null,
      "signal_relevance": "CEO of company proceeding with Goldfield construction",
      "evidence_claim_ids": ["claim_012"],
      "needs_enrichment": {
        "email": true,
        "linkedin": true
      }
    }
  ],
  "excluded": [
    {
      "name": "Andy Tonsing",
      "reason": "Not at target company - wrote article about IREN, works at Stand Together"
    }
  ]
}
```

### RULES

1. **Check ATTRIBUTE claims for existing emails/LinkedIn** - don't miss free data
2. **Set needs_enrichment flags** - skip API calls for data we already have
3. **Exclude tangential mentions** - journalists, analysts who wrote about company
4. **Include partner org contacts** - if relevant to the opportunity
5. **Domain must match their org** - NDEP person uses ndep.nv.gov, not target domain
