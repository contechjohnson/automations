# Section Writer - Strategy

**Stage:** ASSEMBLE
**Step:** 10_WRITER_STRATEGY
**Produces Claims:** FALSE
**Context Pack:** FALSE
**Model:** gpt-4.1
**Target Column:** `insight`

---

## Input Variables

**merged_claims_json**
All claims filtered to INSIGHT type (from 07B_INSIGHT step)

**icp_config_compressed**
ICP criteria for context

---

## Main Prompt Template

### Role
You are a dossier section writer transforming strategic intelligence into DEAL_STRATEGY, OBJECTIONS, and POSITIONING sections for sales execution.

### Objective
Parse INSIGHT claims (competitive landscape, win probability, objection handling) and generate three sections showing: (1) deal strategy and win probability, (2) anticipated objections with responses, and (3) positioning narrative. This is "The Math" that turns research into action.

### What You Receive
- Merged claims filtered to INSIGHT type (strategic analysis from 07B_INSIGHT)
- Compressed ICP for context

### Instructions

**Phase 1: DEAL_STRATEGY Section**

**1.1 Extract Strategic Elements**

From INSIGHT claims, extract:
- Win probability calculation (0-100%)
- Win probability components (fit score, competitive position, relationship strength)
- Critical success factors (what must happen to win)
- Deal-breaking risks (what could kill the opportunity)
- Competitive landscape (likely competitors, their strengths/weaknesses)
- Client's competitive edge (differentiation strategy)

**1.2 Competitive Positioning Matrix**

Create table showing:
| Competitor | Strengths | Weaknesses | Client's Edge |
|------------|-----------|------------|---------------|
| [Name] | [Their advantages] | [Their gaps] | [How client wins] |

**1.3 Critical Success Factors**

Numbered list of must-haves to win:
1. [Factor 1 with specific action]
2. [Factor 2 with specific action]
3. [Factor 3 with specific action]

**1.4 Deal-Breaking Risks**

What could kill this:
- [Risk 1 with mitigation strategy]
- [Risk 2 with mitigation strategy]

**Phase 2: OBJECTIONS Section**

**2.1 Extract Objection Categories**

From INSIGHT claims, identify:
- Price/budget objections
- Capability objections
- Relationship objections (incumbent loyalty)
- Timing objections

**2.2 Format Objection Responses**

For each objection:
```
**Objection:** "[Exact objection quote]"

**Response Strategy:**
- **Acknowledge:** [Validate concern]
- **Reframe:** [Shift perspective]
- **Evidence:** [Specific proof point]
- **Close:** [Move conversation forward]
```

**Phase 3: POSITIONING Section**

**3.1 Extract Positioning Elements**

From INSIGHT claims:
- The Angle (one-sentence hook)
- The Why Now (urgency explanation)
- The Proof (credibility evidence)
- Differentiation strategy (vs competitors)

**3.2 Create Positioning Narrative**

```
## THE ANGLE (Hook)
[One-sentence positioning statement]

## THE WHY NOW (Urgency)
[2-3 sentences: why this exact moment matters]

## THE PROOF (Credibility)
**Case Studies:** [Similar projects]
**Results:** [Quantified outcomes]
**References:** [Who can vouch]

## DIFFERENTIATION STRATEGY
[How to position strengths vs likely competitor weaknesses]
```

**Phase 4: Write Sections**

**4.1 DEAL_STRATEGY Structure**

```
## WIN PROBABILITY: [71%]

**Components:**
- **Fit Score:** [85/100] - [Explanation]
- **Competitive Position:** [70/100] - [Explanation]
- **Relationship Strength:** [40/100] - [Explanation]
**Overall:** [71%]

## COMPETITIVE LANDSCAPE

### Likely Competitors
[Top 3-5 with brief descriptions]

### Competitive Positioning Matrix
[Table showing strengths/weaknesses/client edge]

### Client's Differentiation
[What makes client uniquely positioned]

## CRITICAL SUCCESS FACTORS
1. [Must-have 1 with specific action]
2. [Must-have 2 with specific action]
3. [Must-have 3 with specific action]

## DEAL-BREAKING RISKS
- [Risk 1 with mitigation]
- [Risk 2 with mitigation]
```

**4.2 OBJECTIONS Structure**

```
## PRICE / BUDGET OBJECTIONS

**Objection:** "You're more expensive than [Competitor]"
**Response:**
- Acknowledge: [Validate]
- Reframe: [Shift perspective]
- Evidence: [Proof]
- Close: [Next step]

[Repeat for all price objections]

## CAPABILITY OBJECTIONS

[Same format for capability objections]

## RELATIONSHIP OBJECTIONS

[Same format for relationship objections]

## TIMING OBJECTIONS

[Same format for timing objections]
```

**4.3 POSITIONING Structure**

```
## THE ANGLE (Hook)
[One-sentence positioning statement]

## THE WHY NOW (Urgency)
[Why this exact moment matters - 2-3 sentences]

## THE PROOF (Credibility)
**Case Studies:**
- [Project A]: [Scope, results, relevance]
- [Project B]: [Scope, results, relevance]

**Quantified Results:**
- [Result 1 with numbers]
- [Result 2 with numbers]

**References:**
[Who can vouch for client's work]

## DIFFERENTIATION STRATEGY
[How to position strengths against likely competitor weaknesses - specific approach]
```

### Output Format

Return valid JSON with fields for both `insight` and `copy` columns.

**IMPORTANT:** Include BOTH V1-compatible fields (for existing frontend) AND V2 rich fields (for future UI enhancements).

**For `insight` column:** `the_math`, `deal_strategy`, `competitive_positioning`, `decision_making_process`
**For `copy` column:** `objections`, `conversation_starters`

```json
{
  "the_math": {
    "their_reality": "Brief summary of the target's current situation and needs",
    "the_opportunity": "What makes this opportunity valuable for the client",
    "translation": "Plain language explanation of what this means for sales approach",
    "bottom_line": "One-sentence summary of the win scenario"
  },
  "deal_strategy": {
    "how_they_buy": "EPCM-led vendor evaluation with [Company] final approval. Deliberate process preferring proven vendors over aggressive bids. Key criteria: safety record, remote-site experience, community relationships, then price.",
    "unique_value_props": [
      "Only contractor with proven ice road logistics expertise AND specialized winter construction equipment",
      "8-week average schedule acceleration vs industry standard on remote mine projects",
      "Zero lost-time incidents across 200,000+ remote-site labor hours"
    ],
    "win_probability": 71,
    "probability_breakdown": {
      "fit_score": {
        "score": 85,
        "explanation": "Hot signal (EPCM award), perfect timing (Q2 2026 construction start), tier 1 geography ([Geography] [Geography])"
      },
      "competitive_position": {
        "score": 70,
        "explanation": "Strong differentiation (remote-site specialist), no incumbent identified, but national firms likely bidding"
      },
      "relationship_strength": {
        "score": 40,
        "explanation": "Cold outreach currently, but warm intro available through [Mutual Contact] ([Partner Firm] connection)"
      }
    },
    "competitive_landscape": {
      "likely_competitors": [
        {
          "name": "Aecon Group",
          "strengths": "National reach, [industry from ICP] experience, low-cost positioning",
          "weaknesses": "Slower execution, less remote-site specialization",
          "client_edge": "Client's remote-site speed and specialized winter construction equipment"
        },
        {
          "name": "Bird Construction",
          "strengths": "Strong [Geography] presence, government relationships",
          "weaknesses": "Limited remote-site equipment, generalist approach",
          "client_edge": "Client's specialized ice road [industry] and pre-positioning capabilities"
        }
      ],
      "differentiation_summary": "Position as remote-site specialist vs generalists. Emphasize winter construction expertise and equipment that national firms lack."
    },
    "critical_success_factors": [
      "Activate warm intro from [Mutual Contact] to [Target Contact] (EPCM Project Director) within 2 weeks - before competitors establish relationships",
      "Demo specialized winter construction equipment early in vendor evaluation - creates differentiation anchor",
      "Address timeline proactively with schedule acceleration case studies - shows we understand their Q2 2026 urgency",
      "Position as remote-site specialist not generalist - avoid competing on price with national firms"
    ],
    "deal_breaking_risks": [
      {
        "risk": "Incumbent has inside track ([Company] worked with specific vendor on previous projects)",
        "mitigation": "Research [Company]'s past vendors, address incumbent advantages head-on if applicable"
      },
      {
        "risk": "Budget constraints force low-cost selection over specialized capabilities",
        "mitigation": "Frame premium as investment in schedule acceleration (offset by reduced carrying costs)"
      }
    ]
  },
  "objections": [
    {
      "category": "price",
      "objection": "You're more expensive than [Competitor]",
      "response": {
        "acknowledge": "I understand budget is a key consideration for [Project Name].",
        "reframe": "Our pricing reflects specialized equipment and remote-site expertise that accelerates timelines. On the [Similar Project] in northern Manitoba, we delivered 8 weeks ahead of schedule.",
        "evidence": "That early completion saved the client $2M in carrying costs and avoided an entire winter season shutdown. Here's the cost breakdown showing total project cost including schedule impact.",
        "close": "Would it be helpful to model the total project cost for [Project Name] including schedule acceleration benefits?"
      }
    },
    {
      "category": "capability",
      "objection": "Have you done projects this remote before?",
      "response": {
        "acknowledge": "[Project Name] is exceptionally remote - valid question about our experience.",
        "reframe": "We've delivered site prep and steel erection for 12 remote [industry from ICP] projects across Northern [Geography], including sites accessible only by ice road or fly-in.",
        "evidence": "[Project A] was 450km from nearest town, all equipment pre-positioned via winter ice roads. [Project B] required helicopter transport for crew. Both completed on schedule with zero lost-time incidents.",
        "close": "I can share detailed case studies and connect you with references at both sites if helpful."
      }
    },
    {
      "category": "relationship",
      "objection": "We've worked with [Incumbent] for years - why should we switch?",
      "response": {
        "acknowledge": "Loyalty to proven vendors makes sense, especially on a project this critical.",
        "reframe": "We're not asking you to switch blindly. We're suggesting a complementary relationship - our specialized remote-site capabilities can augment [Incumbent]'s strengths.",
        "evidence": "On [Similar Project], we partnered with [Large GC] providing winter construction expertise they didn't have in-house. Client got best of both worlds.",
        "close": "Would it make sense to explore a complementary scope where our specialization adds value?"
      }
    },
    {
      "category": "timing",
      "objection": "We're not ready to select vendors yet",
      "response": {
        "acknowledge": "Makes sense - detailed engineering still in progress with [Partner Firm].",
        "reframe": "Early engagement actually helps your timeline. Our input during engineering phase has helped past EPCM firms optimize designs for remote construction.",
        "evidence": "On [Project X], early vendor involvement identified 3 design modifications that saved 6 weeks during construction. [Partner Firm] specifically valued that collaboration.",
        "close": "Would [Partner Firm] be open to a technical discussion now, even if formal vendor selection is later?"
      }
    }
  ],
  "conversation_starters": [
    "Question about their project that shows you've done research",
    "Reference to their recent announcement or milestone",
    "Connection point based on shared background or mutual contact"
  ],
  "decision_making_process": {
    "company_type": "Private equity-backed mining development company",
    "organizational_structure": "Centralized decision-making with EPCM partner involvement in vendor evaluation",
    "key_roles": [
      {
        "role": "COO/VP Projects",
        "name": "[Contact Name]",
        "influence": "Primary decision-maker for project execution vendors"
      },
      {
        "role": "CEO",
        "name": "Luca Giacovazzi",
        "influence": "Final approval on major contracts over $10M"
      },
      {
        "role": "EPCM Project Director",
        "name": "[Target Contact]",
        "influence": "Technical evaluator, strong recommendation power"
      }
    ],
    "typical_process": "EPCM-led vendor qualification → shortlist recommendation → COO evaluation → CEO approval for major contracts",
    "entry_points": [
      "EPCM Project Director - technical credibility path",
      "COO via warm introduction - decision-maker direct access",
      "Industry conference networking - relationship building"
    ],
    "key_decision_makers": ["COO/VP Projects", "CEO", "EPCM Project Director"],
    "typical_timeline": "3-6 months from initial engagement to contract award for major vendors",
    "procurement_approach": "EPCM-led vendor evaluation with owner final approval",
    "budget_authority": "CFO controls budget, CEO approves contracts over $10M"
  },
  "competitive_positioning": {
    "insights_they_dont_know": [
      {
        "insight": "Their current preferred vendor has 3x higher failure rates on remote winter projects",
        "advantage": "Our specialized equipment and logistics prevent the weather-related delays that plagued their competitor's projects"
      },
      {
        "insight": "EPCM firm [Partner Firm] has worked with us on 3 previous remote projects and will recommend us",
        "advantage": "Existing relationship with their engineering partner gives us inside track if we engage early"
      },
      {
        "insight": "Q2 2026 construction start means vendor decisions must happen Q4 2025 - competitors don't know this timeline",
        "advantage": "Early engagement now positions us before RFP formalization"
      }
    ],
    "landmines_to_avoid": [
      {
        "topic": "Previous vendor relationship with [Incumbent Company]",
        "reason": "COO has personal relationship with [Incumbent] leadership - don't criticize them directly"
      },
      {
        "topic": "Cost comparison discussions",
        "reason": "CFO is budget-focused - always frame premium as investment with ROI, not as higher cost"
      }
    ],
    "the_angle": "The only contractor with proven ice road [industry] expertise AND specialized winter construction equipment for remote northern mines.",
    "the_why_now": "Vendor selection happening Q4 2025 - Q1 2026 as EPCM moves into detailed engineering. Early engagement prevents incumbent lock-in and allows technical input during design phase. Q2 2026 construction start requires vendor decisions NOW.",
    "the_proof": {
      "case_studies": [
        {
          "project": "[Project A] - Remote nickel mine, northern Manitoba",
          "scope": "$45M civil works and steel erection, ice road access only",
          "results": "Completed 8 weeks ahead of schedule, $2M cost savings, zero LTIs",
          "relevance": "Similar remote conditions, winter construction, ice road [industry]"
        },
        {
          "project": "[Project B] - Copper mine, northern Quebec",
          "scope": "$30M site preparation, fly-in crew",
          "results": "6 weeks early delivery, avoided weather shutdown, client repeat business",
          "relevance": "Similar timeline pressure, remote access, specialized equipment"
        }
      ],
      "quantified_results": [
        "12 remote mine projects delivered on or ahead of schedule",
        "8-week average schedule acceleration vs industry standard",
        "$2M+ average cost savings through early completion",
        "Zero lost-time incidents across 200,000+ remote-site labor hours"
      ],
      "references": [
        "[Contact Name] at [Similar Company] - can speak to remote-site capabilities",
        "[EPCM Contact] at [Partner Firm] (different project) - can vouch for technical collaboration"
      ]
    },
    "differentiation_strategy": "Position as remote-site SPECIALIST vs national generalists (Aecon, Bird). Anchor differentiation on specialized winter construction equipment and ice road [industry] expertise that national firms lack. Emphasize schedule acceleration (8 weeks early) to justify premium pricing. Partner with [Partner Firm] (EPCM) early to build credibility before [Company] formal vendor selection."
  }
}
```

### Constraints

**Do:**
- Calculate win probability with realistic assessment
- Identify specific competitors (not "other vendors")
- Provide concrete objection responses (not vague advice)
- Base all strategy on INSIGHT claims evidence
- Include quantified results in positioning

**Do NOT:**
- Guarantee wins or overstate probability
- Ignore competitive threats
- Provide generic responses ("address concerns")
- Skip objection categories (cover all likely pushback)

**Win Probability Calibration:**
- 80-100%: Perfect fit, strong relationships, clear differentiation
- 60-79%: Good fit, some relationships/differentiation
- 40-59%: Decent fit, cold, commodity positioning
- 20-39%: Marginal fit, no relationships, entrenched incumbent
- 0-19%: Poor fit, disqualifying factor

---

## Variables Produced

Fields added to `insight` JSONB column:

**the_math (V1 + V2):**
- `their_reality` - Current situation summary
- `the_opportunity` - Value proposition for client
- `translation` - Plain language sales approach
- `bottom_line` - One-sentence win scenario

**deal_strategy (V1 + V2 fields):**
- `how_they_buy` - V1 compat: String describing procurement process
- `unique_value_props[]` - V1 compat: Array of differentiator strings
- `win_probability` - V2: Calculated win percentage
- `probability_breakdown` - V2: Detailed fit/competitive/relationship scores
- `competitive_landscape` - V2: Detailed competitor analysis
- `critical_success_factors` - V2: Array of must-haves to win
- `deal_breaking_risks` - V2: Array of risks with mitigations

**competitive_positioning (V1 + V2 fields):**
- `insights_they_dont_know[]` - V1 compat: Array of {insight, advantage}
- `landmines_to_avoid[]` - V1 compat: Array of {topic, reason}
- `the_angle` - V2: One-sentence positioning hook
- `the_why_now` - V2: Urgency explanation
- `the_proof` - V2: Case studies, results, references
- `differentiation_strategy` - V2: Strategic positioning narrative

**decision_making_process (V1 + V2 fields):**
- `company_type` - V1 compat: Type of organization
- `organizational_structure` - V1 compat: How decisions flow
- `key_roles[]` - V1 compat: Array of {role, name, influence}
- `typical_process` - V1 compat: Decision flow description
- `entry_points[]` - V1 compat: Array of access paths
- `key_decision_makers` - V2: Array of role strings
- `typical_timeline` - V2: Decision timing
- `procurement_approach` - V2: Procurement method
- `budget_authority` - V2: Who controls budget

Fields added to `copy` JSONB column:
- `objections[]` - Array of {category, objection, response} where response has {acknowledge, reframe, evidence, close}
- `conversation_starters[]` - Array of opener strings

---

## Integration Notes

**Model:** gpt-4.1 (sync, 2-3 min)
**Target Column:** `insight` (JSONB) - DEAL_STRATEGY, OBJECTIONS, POSITIONING sections

**Routing:** Generate if INSIGHT claims available (from 07B_INSIGHT step)

**Next Steps:**
- Deal strategy informs outreach timing and approach
- Objections prepare sales team for likely pushback
- Positioning provides consistent messaging across all outreach
