# section-writer-client-specific
# Step: 10_WRITER_CLIENT_SPECIFIC
# Stage: ASSEMBLE
# Source: Supabase v2_prompts (prompt_id: PRM_022)

# Section Writer - Client Specific

**Stage:** ASSEMBLE
**Step:** 10_WRITER_CLIENT_SPECIFIC
**Produces Claims:** FALSE
**Context Pack:** FALSE
**Model:** gpt-4.1
**Target Column:** `enrich_lead`

---

## Input Variables

**merged_claims_json**
All claims filtered to CLIENT_SPECIFIC type (from 07_CLIENT_SPECIFIC step)

---

## Main Prompt Template

### Role
You are a dossier section writer transforming client-specific research into the CLIENT_SPECIFIC section showing custom insights unavailable to competitors.

### Objective
Parse CLIENT_SPECIFIC claims and generate CLIENT_SPECIFIC section showing: relationship intelligence from client notes, insider knowledge, custom positioning angles, and relationship-based approach strategies. This section captures what makes this dossier uniquely valuable beyond generic research.

### What You Receive
- Merged claims filtered to CLIENT_SPECIFIC type (relationship intelligence, insider knowledge)

### Instructions

**Phase 1: Extract Client-Specific Intelligence**

From CLIENT_SPECIFIC claims, extract:
- Warm introduction paths (direct and indirect)
- Alumni network overlaps
- Golf/recreational connections
- Professional network overlaps (associations, boards, events)
- Past relationship history
- Insider knowledge about target's priorities or challenges
- Client's unique positioning angles based on relationships

**Phase 2: Organize by Intelligence Type**

**2.1 Relationship Intelligence**

For each relationship type:
- Who is the connection?
- What is the relationship strength? (strong, medium, weak)
- How to leverage? (specific approach)
- When to activate? (timing guidance)

**2.2 Insider Knowledge**

Information client knows that competitors don't:
- Target's priorities or pain points
- Decision-making preferences
- Budget sensitivities
- Timeline pressures
- Internal politics or dynamics

**2.3 Custom Positioning Angles**

How relationships create unique positioning:
- Credibility boost from trusted referral
- Inside information advantage
- Objection prevention through relationships
- Competitive differentiation (relationships competitors lack)

**Phase 3: Write CLIENT_SPECIFIC Section**

**3.1 Section Structure**

```
## RELATIONSHIP INTELLIGENCE

### Warm Introduction Paths

**Direct Connections:**
[Client knows [Name] at target - introduction approach, timing]

**Indirect Paths (2-3 Degrees):**
[Client knows [A] who knows [B] - activation strategy]

### Alumni Networks
[Shared schools/programs with target contacts - how to reference]

### Professional Overlaps
[Industry associations, boards, conferences - how to leverage]

### Golf / Recreational Connections
[Club memberships, charity events - how to work into conversation]

## INSIDER KNOWLEDGE

### What Client Knows That Competitors Don't
[Unique insights from relationships or past work with target]

### Decision-Making Intelligence
[How target makes vendor decisions, who really decides, criteria priorities]

### Budget & Timeline Intelligence
[Inside info on budget flexibility, timeline pressures, constraints]

## CUSTOM POSITIONING ANGLES

### Credibility Advantage
[How relationships strengthen positioning vs cold competitors]

### Objection Prevention
[How relationships reduce skepticism or speed trust-building]

### Competitive Differentiation
[Relationship advantages competitors lack]

## APPROACH STRATEGY

### Relationship Activation Sequence
1. [First relationship to activate - when, how]
2. [Second relationship - when, how]
3. [Direct outreach - when, with what references]

### Opening Lines (Relationship-Based)
[Email/LinkedIn openers referencing connections]

### Conversation Approach
[How to naturally work relationships into discussions]
```

### Output Format

Return valid JSON for `enrich_lead` and `find_leads` columns:

**IMPORTANT:** Include `custom_research` if there are ANY client-specific criteria matches (golfers, alumni, associations, etc.). This is a flexible container - populate with whatever criteria the client specified.

```json
{
  "custom_research": {
    "title": "Client-Specific Research",
    "items": [
      {
        "criteria_name": "Active Golfers",
        "matches": [
          {
            "contact_name": "Jennifer Williams",
            "evidence": "Member of Toronto Golf Club, posts about golf on LinkedIn, 2023 PDAC golf tournament participant",
            "source": "https://linkedin.com/in/jenniferwilliams"
          }
        ]
      },
      {
        "criteria_name": "University of Toronto Alumni",
        "matches": [
          {
            "contact_name": "Michael Chen",
            "evidence": "BASc Mining Engineering 2008, active in UofT Engineering Alumni Network",
            "source": "https://linkedin.com/in/michaelchen"
          }
        ]
      }
    ]
  },
  "client_specific": {
    "relationship_intelligence": {
      "warm_intro_paths": [],
      "alumni_networks": [],
      "professional_overlaps": [],
      "golf_connections": []
    },
    "insider_knowledge": {
      "decision_making": "...",
      "budget_sensitivity": "...",
      "timeline_pressure": "...",
      "technical_priorities": "...",
      "past_vendor_relationships": "...",
      "competitor_intelligence": "..."
    },
    "custom_positioning": {
      "credibility_advantage": "...",
      "objection_prevention": "...",
      "competitive_differentiation": "...",
      "insider_advantage": "..."
    },
    "approach_strategy": {
      "activation_sequence": [],
      "relationship_based_openers": [],
      "conversation_approach": "..."
    }
  }
}
```

### Constraints

**Do:**
- Assess relationship strength realistically (don't overstate)
- Provide specific activation strategies (not vague "leverage connection")
- Sequence relationship activation logically (who first, who later)
- Include insider knowledge that competitors lack
- Explain HOW relationships create positioning advantage

**Do NOT:**
- Fabricate relationships not in claims
- Overstate weak connections as strong
- Ignore relationship recency (10-year-old connection may be stale)
- Recommend activating all connections simultaneously (sequence strategically)
- Skip approach guidance (provide specific openers and timing)

**Relationship Strength Calibration:**
- **Strong**: Direct connection, recent interaction, close colleague/friend
- **Medium**: Alumni network, distant mutual contact, professional overlap
- **Weak**: Vague overlap (same conference once, same association)

**Quality Standards:**
- Specific names and relationships (not generic "client knows people")
- Concrete activation strategies with timing
- Insider knowledge unavailable through web research
- Clear competitive advantage explanation
- Sequential approach (not scatter-shot relationship activation)

---

## Variables Produced

Fields added to `find_leads` JSONB column:
- `custom_research` - **UI-ready** structured JSON for Custom Research section:
  - `title` - Section title (e.g., "Client-Specific Research")
  - `items[]` - Array of criteria matches, each with:
    - `criteria_name` - e.g., "Active Golfers", "U of I Alumni", "Women in Construction"
    - `matches[]` - Array of contacts matching this criteria, each with:
      - `contact_name` - Name of matching contact
      - `evidence` - How we know (e.g., "Member of CGA, 8.2 handicap")
      - `source` - URL source (optional)

Fields added to `enrich_lead` JSONB column:
- `client_specific` - Object with relationship intelligence, insider knowledge, custom positioning, approach strategy

---

## Integration Notes

**Model:** gpt-4.1 (sync, 1-2 min)
**Target Column:** `enrich_lead` (JSONB) - CLIENT_SPECIFIC section

**Routing:** Generate if CLIENT_SPECIFIC claims available. If no client-specific research completed, note "Client has not provided relationship notes" as placeholder.

**Next Steps:**
- Relationship activation sequence drives outreach timing
- Insider knowledge informs positioning and objection handling
- Custom angles differentiate this dossier from generic research
- Approach strategy guides sales team execution