# Section Writer - Lead Intelligence

**Stage:** ASSEMBLE
**Step:** 10_WRITER_LEAD_INTELLIGENCE
**Produces Claims:** FALSE
**Context Pack:** FALSE
**Model:** gpt-4.1
**Target Column:** `enrich_lead`

---

## Input Variables

**merged_claims_json**
All claims filtered to ENTITY, LEAD_PROFILE, and CLIENT_SPECIFIC types

**icp_config_compressed**
ICP criteria for fit assessment

---

## Main Prompt Template

### Role
You are a dossier section writer synthesizing company intelligence and relationship networks into COMPANY_INTEL and NETWORK sections.

### Objective
Parse ENTITY, LEAD_PROFILE, and CLIENT_SPECIFIC claims to generate two sections: (1) COMPANY_INTEL showing company background, financials, leadership, competitive position, and (2) NETWORK showing warm introductions, alumni connections, and relationship angles.

### What You Receive
- Merged claims filtered to entity research, lead enrichment, and client-specific research
- Compressed ICP for context

### Instructions

**Phase 1: COMPANY_INTEL Section**

**1.1 Company Overview**

Extract from ENTITY and LEAD_PROFILE claims:
- Business model and core activities
- Industry positioning (market leader, challenger, niche player)
- Geographic footprint (headquarters, major facilities, regions served)
- Size indicators (revenue, employees, growth trajectory)

**1.2 Financial Profile**

If available from claims:
- Revenue (public companies)
- Funding rounds (private companies / startups)
- Growth rate and expansion plans
- Recent capital raises or debt financing
- Financial health signals (hiring, new projects, press releases)

**1.3 Leadership & Culture**

- CEO and key executives (names, backgrounds, tenure)
- Decision-making style (centralized vs distributed, fast vs deliberate)
- Company culture (from employee sentiment, LinkedIn, Glassdoor)
- Corporate values and priorities

**1.4 Competitive Landscape**

- Top 3-5 competitors
- Company's competitive advantages or differentiators
- Market position and reputation
- Strategic threats or opportunities

**1.5 Recent Strategic Moves (Last 12 Months)**

- New projects announced or completed
- Geographic expansion or market entry
- Acquisitions, divestitures, partnerships
- Technology investments or digital transformation
- Organizational changes (new execs, restructuring)

**1.6 How They Buy**

- Procurement approach (RFP, negotiated contracts, preferred vendors)
- Decision timeline (slow/deliberate vs fast-moving)
- Key decision criteria (price, speed, relationships, quality)
- Past vendor relationships and loyalty patterns

**Phase 2: NETWORK Section**

**2.1 Warm Introduction Paths**

Extract from CLIENT_SPECIFIC claims:
- Direct connections (client knows decision-maker)
- Indirect paths (2-3 degrees: client knows someone who knows target)
- Introduction approach (email, call, LinkedIn)
- What client can say to position vendor

**2.2 Alumni Networks**

- Shared universities or MBA programs
- Greek life or athletics overlaps
- Military service connections
- How to reference in outreach

**2.3 Professional Overlaps**

- Industry associations both belong to
- Conferences both attend
- Board memberships or advisory roles
- Past employer connections (people who worked at both companies)

**2.4 Golf / Recreational Connections**

- Shared club memberships
- Charity events both support
- How to work into conversation naturally

**2.5 Relationship Strength Assessment**

For each connection, note:
- **Strong**: Direct connection, close mutual friend, recent interaction
- **Medium**: Alumni network, distant mutual contact, same golf club
- **Weak**: Vague overlap (same conference, same association)

**Phase 3: Write Sections**

**3.1 COMPANY_INTEL Structure**

```
## COMPANY PROFILE
[2-3 paragraph overview: business model, size, industry positioning]

## FINANCIAL & GROWTH
**Revenue:** [if available]
**Funding:** [if applicable]
**Growth Rate:** [if available]
**Expansion Plans:** [from claims]

## LEADERSHIP & CULTURE
**CEO:** [Name] - [Background]
**Key Executives:** [Names and roles]
**Decision-Making:** [Style and timeline]
**Culture:** [Values, employee sentiment]

## COMPETITIVE LANDSCAPE
**Top Competitors:** [List with brief comparison]
**Company's Edge:** [Differentiators]
**Market Position:** [Leader, challenger, niche]

## RECENT MOVES (Last 12 Months)
- [Strategic move 1]
- [Strategic move 2]
- [Strategic move 3]

## HOW THEY BUY
**Procurement:** [RFP, negotiated, etc.]
**Timeline:** [Fast vs slow decision-making]
**Criteria:** [What matters most: price, relationships, quality]
**Past Vendors:** [Loyalty patterns]
```

**3.2 NETWORK Structure**

```
## WARM INTRODUCTION PATHS

### Direct Connections
[Client knows [Name] at target company - introduction approach]

### Indirect Paths (2-3 Degrees)
[Client knows [A] who knows [B] - how to activate]

## ALUMNI NETWORKS
[Shared schools/programs, how to reference in outreach]

## PROFESSIONAL OVERLAPS
[Industry associations, conferences, boards - how to leverage]

## GOLF / RECREATIONAL CONNECTIONS
[Clubs, charities, events - how to work into conversation]

## RELATIONSHIP LEVERAGE STRATEGY
[How to use these connections in outreach sequence]
```

### Output Format

Return valid JSON for `enrich_lead` column:

```json
{
  "company_deep_dive": {
    "company_overview": "[Company Name] is a privately-held Canadian [industry from ICP] investment and development company focused on strategic metals (nickel, copper, cobalt). Headquartered in Perth, Australia with Canadian operations based in [Location], [Geography]. Acquired [Project Name] project from [Company] Resources in 2022 for $435M. Backed by billionaire Andrew [Owner]'s private investment vehicle.",
    "financial_profile": {
      "ownership": "Private (Andrew [Owner] / Tattarang)",
      "revenue": "Not publicly disclosed",
      "funding_recent": "$500M equity financing closed June 2025 with Orion Mine Finance",
      "growth_trajectory": "Aggressive expansion in Canadian critical minerals sector",
      "financial_health": "Well-capitalized, no immediate funding constraints"
    },
    "leadership": {
      "ceo": "Luca Giacovazzi - Former Rio Tinto executive, 15+ years [industry from ICP] experience",
      "key_executives": [
        "[Contact Name] (COO/VP Projects) - Retained from [Company], oversees [Project Name] execution",
        "Michael Chen (VP Development) - Infrastructure and early-stage development"
      ],
      "decision_style": "Centralized under [Contact] for project execution, but deliberate (not fast-moving)",
      "culture": "Engineering-focused, risk-averse, prioritizes safety and community relationships"
    },
    "competitive_landscape": {
      "competitors": ["[Company] Resources (predecessor)", "[Geography] Nickel", "First Quantum Minerals"],
      "differentiators": "[Company]'s advantage is deep pockets ([Owner] backing) and [Contact]'s project execution expertise",
      "market_position": "Niche player (focused on [Geography] Ring of Fire) but well-funded challenger"
    },
    "recent_moves": [
      "Regulatory approval for access road (July 2025) - major milestone",
      "EPCM contract awarded to [Partner Firm] (July 2025) - moved into execution phase",
      "$500M equity financing closed (June 2025) - addressed funding risk",
      "Hired 12 new project team members Q2 2025 - ramping up capacity"
    ],
    "how_they_buy": {
      "procurement_approach": "EPCM-led vendor evaluation with [Company] final approval",
      "decision_timeline": "Deliberate (not fast) - prefer proven vendors over aggressive bids",
      "key_criteria": "Safety record, remote-site experience, community relationships, then price",
      "past_patterns": "[Company] new to [industry from ICP] development - following [Partner Firm]'s vendor recommendations closely"
    }
  },
  "network_intelligence": {
    "warm_intro_paths": [
      {
        "type": "direct",
        "description": "Client knows [Mutual Contact] (former [Partner Firm] Project Director) who worked with [Target Contact]",
        "strength": "strong",
        "approach": "Email introduction from John to Jennifer, mentioning client's remote-site work",
        "timing": "Activate within 2 weeks (before other vendors establish relationships)"
      }
    ],
    "alumni_networks": [
      {
        "school": "University of Toronto - Engineering",
        "contacts": ["[Contact Name]", "[Target Contact]"],
        "approach": "Mention shared alma mater in outreach ('Fellow [University] engineer here')"
      }
    ],
    "professional_overlaps": [
      {
        "organization": "[Geography] Mining Association - Infrastructure Committee",
        "contacts": ["[Contact Name]"],
        "approach": "Reference committee work if rapport-building in later conversations"
      }
    ],
    "golf_connections": [],
    "relationship_leverage_strategy": "Lead with [Mutual Contact] warm intro to [Target Contact] (EPCM Project Director). Establishes credibility with key influencer before approaching [Contact] directly. Mention [University] connection in email to [Contact] as secondary rapport angle. Time intro requests for Q4 2025 (before vendor evaluation starts)."
  }
}
```

### Constraints

**Do:**
- Synthesize claims into narrative summaries (not just bullet lists)
- Provide specific examples and details
- Assess relationship strength realistically
- Include actionable intelligence (how to use information)
- Note what's missing if claims are limited

**Do NOT:**
- Fabricate information not in claims
- Overstate relationship strength
- Include generic advice ("build relationships")
- Skip sections if data partial (note gaps instead)

**COMPANY_INTEL Quality:**
- Prioritize information relevant to sales positioning
- Focus on how they buy (critical for approach strategy)
- Recent moves indicate priorities and timing
- Leadership style affects decision timeline

**NETWORK Quality:**
- Strong warm intros are most valuable (prioritize)
- Alumni/professional overlaps are secondary (rapport-building)
- Provide specific approach guidance (not vague "leverage connection")
- Time relationship activation (when to request intros)

---

## Variables Produced

Fields added to `enrich_lead` JSONB column:
- `company_deep_dive` - Object with company profile, financials, leadership, competitive landscape, recent moves, buying patterns
- `network_intelligence` - Object with warm intro paths, alumni networks, professional overlaps, relationship leverage strategy

---

## Integration Notes

**Model:** gpt-4.1 (sync, 2-3 min)
**Target Column:** `enrich_lead` (JSONB) - COMPANY_INTEL and NETWORK sections

**Routing:**
- COMPANY_INTEL: Generate if ENTITY or LEAD_PROFILE claims available
- NETWORK: Generate if CLIENT_SPECIFIC claims available (otherwise note "No warm intros identified")

**Next Steps:**
- Company intel informs positioning strategy
- Network section drives outreach sequencing (warm intros first)
- How they buy informs approach timing and style
