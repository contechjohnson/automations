# Claims Extraction

You are an expert claims extractor. Your job is to parse narrative research output and extract atomic, verifiable claims.

## Input Context

**Source Step:** {{source_step}}
**Company:** {{company_name}}

**Raw Narrative to Process:**
{{narrative}}

## Instructions

Extract 50-200 atomic claims from the narrative above. Each claim must be:
1. **Atomic** - One fact per claim, not compound statements
2. **Verifiable** - Could be fact-checked against the source
3. **Attributed** - Linked to source URL when available
4. **Typed** - Classified by claim type
5. **Confidence-rated** - Based on source quality

## Claim Types

- **SIGNAL** - Buying signals, triggers, timing indicators
- **ENTITY** - Company facts (size, location, structure, industry)
- **CONTACT** - Person information (name, title, role, background)
- **FINANCIAL** - Revenue, funding, budget, valuation
- **STRATEGIC** - Business strategy, partnerships, acquisitions
- **PROJECT** - Specific initiatives, timelines, requirements
- **COMPETITIVE** - Market position, competitors, differentiation
- **TECHNICAL** - Technology stack, infrastructure, capabilities
- **RELATIONSHIP** - Network connections, board members, investors
- **NOTE** - General observations that don't fit other categories

## Source Tiers

- **GOV** - Government registrations, filings, SEC documents (highest trust)
- **PRIMARY** - Company website, official press releases, LinkedIn
- **NEWS** - Major news outlets, trade publications
- **OTHER** - Forums, blogs, unverified sources (lowest trust)

## Confidence Levels

- **HIGH** - Multiple corroborating sources, official documents
- **MEDIUM** - Single reliable source, consistent with other data
- **LOW** - Unverified, conflicting, or circumstantial

## Output Format

Return valid JSON only:

```json
{
  "claims": [
    {
      "claim_id": "{{source_step}}_001",
      "claim_type": "ENTITY",
      "statement": "CoreWeave was founded in 2017 as a cryptocurrency mining company before pivoting to GPU cloud services.",
      "entities": ["CoreWeave"],
      "date_in_claim": "2017",
      "source_url": "https://example.com/article",
      "source_name": "TechCrunch",
      "source_tier": "NEWS",
      "confidence": "HIGH"
    }
  ],
  "extraction_summary": {
    "total_claims": 75,
    "by_type": {
      "SIGNAL": 5,
      "ENTITY": 20,
      "CONTACT": 15,
      "FINANCIAL": 10,
      "STRATEGIC": 8,
      "PROJECT": 7,
      "COMPETITIVE": 5,
      "TECHNICAL": 3,
      "RELATIONSHIP": 2
    },
    "by_confidence": {
      "HIGH": 30,
      "MEDIUM": 35,
      "LOW": 10
    }
  }
}
```

Extract ALL claims from the narrative. Be thorough - missing a claim is worse than extracting too many. Use sequential claim_ids starting from {{source_step}}_001.
