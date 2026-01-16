# Section Writer - Opportunity Intelligence

**Stage:** ASSEMBLE
**Step:** 10_WRITER_OPPORTUNITY
**Produces Claims:** FALSE
**Context Pack:** FALSE
**Model:** gpt-4.1
**Target Column:** `enrich_lead`

---

## Input Variables

**merged_claims_json**
All claims filtered to OPPORTUNITY type (from 06_ENRICH_OPPORTUNITY step)

---

## Main Prompt Template

### Role
You are a dossier section writer transforming opportunity research into the OPPORTUNITY_DETAILS section for vendor positioning.

### Objective
Parse OPPORTUNITY claims and generate OPPORTUNITY_DETAILS section showing: project scope, budget, timeline, procurement status, technical requirements, vendor opportunities, and project risks. This section gives sales teams deep project intelligence.

### What You Receive
- Merged claims filtered to OPPORTUNITY type (project-specific intelligence)

### Instructions

**Phase 1: Extract Opportunity Elements**

From OPPORTUNITY claims, extract:
- **Project specifications**: Scope, square footage, capacity, technical requirements
- **Budget**: Total project cost, breakdown by phase/component
- **Timeline**: Current phase, key milestones, construction schedule, critical path
- **Procurement status**: Contracts awarded (EPCM, GC), contracts open, bid processes
- **Vendor opportunities**: Where client fits, contract value estimate, competition
- **Technical requirements**: Standards, certifications, specifications
- **Project risks**: Permitting hurdles, budget pressures, timeline challenges

**Phase 2: Organize by Category**

**2.1 PROJECT SPECIFICATIONS**

```
**Scope:**
[Detailed project scope with square footage, capacity, infrastructure details]

**Technical Requirements:**
- [Requirement 1]
- [Requirement 2]
- [Standards/certifications required]

**Quality Standards:**
[Quality requirements, certifications, compliance needs]
```

**2.2 BUDGET & VALUE**

```
**Total Project Cost:** [$ amount if known]

**Budget Breakdown:**
- [Phase 1]: [$ amount]
- [Phase 2]: [$ amount]

**Client's Scope Value (Estimate):**
[Estimated contract value for client's services]

**Budget Status:**
[Funded, financing in progress, budget pressure indicators]
```

**2.3 TIMELINE & MILESTONES**

```
**Current Phase:** [Planning, permitting, pre-construction, construction]

**Key Milestones:**
- ✅ [Completed milestone] - [Date]
- 🔄 [In progress milestone] - [Expected date]
- ⏳ [Upcoming milestone] - [Expected date]

**Construction Schedule:**
[Phase-by-phase timeline]

**Critical Path:**
[Dependencies and timeline-critical items]
```

**2.4 PROCUREMENT STATUS**

```
**Contracts Awarded:**
- EPCM: [Firm name] - [Date awarded]
- General Contractor: [Firm name] - [Date awarded]
- Major Equipment: [Vendor] - [Date awarded]

**Contracts Still Open:**
- [Contract type 1] - [Timeline for selection]
- [Contract type 2] - [Timeline for selection]

**Procurement Timeline:**
[When vendor selection decisions happening]

**Bid Processes:**
[RFP schedules, qualification requirements]
```

**2.5 VENDOR OPPORTUNITIES**

```
**Where Client Fits:**
[Specific scope areas matching client's services]

**Estimated Contract Value:**
[$ range for client's scope]

**Likely Competition:**
- [Competitor 1] - [Why they'll bid]
- [Competitor 2] - [Why they'll bid]

**Differentiation Opportunities:**
[What makes client uniquely positioned for this scope]
```

**2.6 PROJECT RISKS & CHALLENGES**

```
**Permitting/Regulatory:**
[Hurdles, delays, community opposition]

**Budget Pressures:**
[Cost overruns, financing gaps, value engineering]

**Timeline Challenges:**
[Schedule risks, weather, supply chain]

**Mitigation Strategies:**
[How client can address or mitigate risks]
```

**Phase 3: Write OPPORTUNITY_DETAILS Section**

Combine all categories into structured section with narrative flow.

### Output Format

Return valid JSON with two root-level objects:
- `company_snapshot` → Goes to `find_lead` column
- `project_sites` → Goes to `enrich_lead` column

```json
{
  "company_snapshot": {
    "company_name": "[Company Name]",
    "description": "Short description of what the company does (1-2 sentences)",
    "domain": "company-domain.com",
    "hq_city": "[City]",
    "hq_state": "[State/Province]",
    "industry": "[Industry from ICP]"
  },
  "project_sites": [
    {
      "site_name": "[Project Name]",
      "address": "[Full address or location description]",
      "scope": "[Project scope summary]",
      "status": "[Preconstruction|Construction|Operational]",
      "estimated_value": "[Dollar amount if known]",
      "construction_start": "[Date or quarter]"
    }
  ],
  "opportunity_details": {
    "project_specifications": {
      "scope_summary": "[Project Name] is a $1.2B underground nickel-copper-PGM mine in [Geography]'s Ring of Fire, 540km northeast of [Location]. Project includes 3.6km underground decline, 2,000 tpd processing plant, tailings management facility, 300-person camp, and 100km all-season access road.",
      "technical_requirements": [
        "Remote-site construction accessible via ice road (winter) or temporary airstrip",
        "Winter construction capability (-40°C operations)",
        "Modular construction for equipment transport constraints",
        "First Nations workforce integration ([Location], Marten Falls communities)"
      ],
      "capacity": "2,000 tonnes per day processing capacity, 10-year mine life",
      "infrastructure": "100km all-season road, permanent bridge crossings, power transmission line",
      "quality_standards": "ISO 45001 safety, environmental compliance per EA requirements, First Nations consultation protocols"
    },
    "budget": {
      "total_project_cost": "$1.2B",
      "breakdown": {
        "mine_development": "$400M",
        "processing_plant": "$350M",
        "infrastructure": "$300M (includes road, power, camp)",
        "contingency": "$150M"
      },
      "client_scope_estimate": "$40-60M (civil works, steel erection, site preparation)",
      "funding_status": "Fully funded - $500M equity closed June 2025, $700M debt financing expected Q4 2025"
    },
    "timeline": {
      "current_phase": "Pre-construction (detailed engineering in progress)",
      "milestones": [
        {
          "milestone": "Environmental Assessment exemption",
          "status": "completed",
          "date": "2025-07-04",
          "significance": "Cleared major regulatory hurdle, accelerated timeline"
        },
        {
          "milestone": "EPCM contract awarded ([Partner Firm])",
          "status": "completed",
          "date": "2025-07-15",
          "significance": "Engineering phase started, vendor evaluation beginning"
        },
        {
          "milestone": "Detailed engineering completion",
          "status": "in_progress",
          "expected_date": "2026-Q1",
          "significance": "Required before vendor selection finalized"
        },
        {
          "milestone": "Civil works and steel vendor selection",
          "status": "upcoming",
          "expected_date": "2026-Q1 to Q2",
          "significance": "Client's opportunity window"
        },
        {
          "milestone": "Site preparation start",
          "status": "upcoming",
          "expected_date": "2026-Q2",
          "significance": "Construction kickoff"
        },
        {
          "milestone": "First ore production",
          "status": "upcoming",
          "expected_date": "2028-Q3",
          "significance": "Revenue start"
        }
      ],
      "construction_schedule": "Q2 2026 site prep, Q3 2026 underground development, Q4 2026 plant construction, 2027-2028 commissioning",
      "critical_path": "Access road completion before major equipment delivery (Q2 2026), winter weather windows for foundation work (Q4 2026), processing plant steel erection (Q1-Q2 2027)"
    },
    "procurement": {
      "contracts_awarded": [
        {
          "type": "EPCM",
          "vendor": "[Partner Firm Name]",
          "date": "2025-07-15",
          "scope": "Engineering, procurement coordination, construction management"
        }
      ],
      "contracts_open": [
        {
          "type": "Civil works and site preparation",
          "timeline": "Vendor selection Q1 2026",
          "estimated_value": "$25-35M",
          "status": "[Partner Firm] evaluating qualified contractors"
        },
        {
          "type": "Steel erection",
          "timeline": "Vendor selection Q1-Q2 2026",
          "estimated_value": "$15-25M",
          "status": "May be bundled with civil or separate bid"
        },
        {
          "type": "Underground [industry from ICP] contractor",
          "timeline": "Vendor selection Q2 2026",
          "estimated_value": "$300M+",
          "status": "Separate procurement, not client's scope"
        }
      ],
      "procurement_process": "EPCM-led evaluation with [Company] final approval. No formal RFP expected - [Partner Firm] will invite qualified contractors to submit proposals.",
      "qualification_requirements": "Remote-site experience, safety record, First Nations partnerships, winter construction capability"
    },
    "vendor_opportunities": {
      "client_fit": "Civil works (site preparation, foundations, roads, laydown areas) and steel erection (processing plant structural steel). Both scopes align with client's specialized remote-site capabilities.",
      "estimated_contract_value": "$40-60M combined (civil $25-35M + steel $15-25M)",
      "likely_competition": [
        "Aecon Group (national reach, [industry from ICP] experience, low-cost positioning)",
        "Bird Construction ([Geography] presence, government relationships)",
        "Ledcor (remote-site experience, western [Geography] focus)",
        "Local/regional firms (First Nations partnerships, community ties)"
      ],
      "differentiation_opportunities": [
        "Specialized winter construction equipment (national firms rent, client owns)",
        "Proven ice road [industry] expertise (12 remote projects)",
        "Existing First Nations workforce partnerships in Northern [Geography]",
        "Modular construction approach for transport-constrained sites",
        "Schedule acceleration track record (8-week average vs industry standard)"
      ]
    },
    "risks_and_challenges": {
      "permitting": {
        "description": "EA exemption granted, but road permits still require First Nations consultation completion",
        "impact": "Could delay site access (Q2 2026 start at risk)",
        "mitigation": "Client's First Nations partnerships could accelerate consultation process"
      },
      "community_opposition": {
        "description": "Some environmental groups oppose Ring of Fire development",
        "impact": "Potential protests or legal challenges",
        "mitigation": "[Company] has strong community relationships, environmental commitments"
      },
      "supply_chain": {
        "description": "Remote location limits equipment/material transport (ice road only Q1-Q3)",
        "impact": "Missed transport window adds 6-12 month delay",
        "mitigation": "Client's pre-positioning strategy addresses this (core competency)"
      },
      "budget_pressure": {
        "description": "$1.2B budget is tight for remote mine of this scale",
        "impact": "Value engineering likely, cost pressure on vendors",
        "mitigation": "Frame client's premium as schedule acceleration investment (offset by reduced carrying costs)"
      },
      "timeline_pressure": {
        "description": "Ambitious Q2 2026 construction start after 2-year regulatory delay",
        "impact": "Compressed vendor selection and mobilization timeline",
        "mitigation": "Client's rapid mobilization capability (key differentiator)"
      }
    }
  }
}
```

### Constraints

**Do:**
- Provide detailed, specific project information
- Estimate contract values where possible
- Identify specific vendor opportunities for client
- Explain risks with mitigation strategies
- Note what information is missing or uncertain

**Do NOT:**
- Fabricate project details not in claims
- Overstate contract values without evidence
- Ignore competitive reality
- Skip risk assessment
- Provide generic project descriptions

**Quality Standards:**
- Specific numbers (square footage, capacity, budget) when available
- Milestone dates (actual and expected)
- Competitive landscape (who will bid, why)
- Clear vendor opportunity description (scope, value, timing)
- Actionable risk mitigation (not just risk identification)

---

## Variables Produced

Fields added to `find_lead` JSONB column:
- `company_snapshot` - Object with company name, description, domain, HQ location, industry

Fields added to `enrich_lead` JSONB column:
- `project_sites` - Array of project site objects with name, address, scope, status
- `opportunity_details` - Object with project specifications, budget, timeline, procurement, vendor opportunities, risks

---

## Integration Notes

**Model:** gpt-4.1 (sync, 2-3 min)
**Target Column:** `enrich_lead` (JSONB) - OPPORTUNITY_DETAILS section

**Routing:** Generate if OPPORTUNITY claims available (from 06_ENRICH_OPPORTUNITY step)

**Next Steps:**
- Opportunity details inform vendor positioning and approach strategy
- Contract value estimate helps client prioritize pursuit
- Timeline drives outreach urgency
- Risk mitigation becomes selling point in outreach
