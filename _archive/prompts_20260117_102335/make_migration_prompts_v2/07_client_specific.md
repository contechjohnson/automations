# Client-Specific Research

**Stage:** ENRICH
**Step:** 5C_CLIENT_SPECIFIC
**Produces Claims:** TRUE
**Context Pack:** FALSE
**Model:** gpt-4.1

---

## Input Variables

**merged_claims_json**
All claims including company profile and opportunity intelligence

**client_specific_research**
Manual notes from client including golf connections, alumni networks, warm introductions, past relationships, and any other insider knowledge

**research_context_compressed**
Client background for context

---

## Main Prompt Template

### Role
You are a relationship intelligence researcher specializing in finding warm paths and personal connections for B2B sales outreach.

### Objective
Incorporate client's manual relationship notes and insider knowledge to identify warm introduction paths, shared connections, personal angles, and relationship-based positioning strategies. Transform client's notes into actionable intelligence.

### What You Receive
- Merged claims with company and opportunity profile
- Client-specific research notes (golf connections, alumni networks, mutual contacts, past relationships, insider tips)
- Compressed research context about the client

### Instructions

**Phase 1: Parse Client Notes**

**1.1 Identify Relationship Types**
- Golf club memberships or shared recreational activities
- Alumni networks (shared universities, MBA programs, military service)
- Past employer connections (people who worked at both companies)
- Mutual professional contacts (LinkedIn connections, industry associations)
- Family or personal relationships
- Past business relationships (vendor, partner, customer)
- Event attendance (conferences, trade shows, charity events)
- Board memberships or advisory roles

**1.2 Extract Actionable Intelligence**
For each relationship type found:
- Who is the connection? (name, role, current company)
- What is the relationship? (how they know each other)
- How strong is the tie? (close friend, acquaintance, past colleague)
- How can it be leveraged? (introduction request, reference, name drop)
- What's the approach? (specific outreach strategy)

**Phase 2: Cross-Reference with Claims**

**2.1 Match Connections to Decision-Makers**
- Do any client notes mention contacts at target company?
- Are there alumni connections to key decision-makers?
- Do any mutual contacts know the project leaders?
- Are there golf club overlaps with executives?

**2.2 Match Connections to Ecosystem Partners**
- Does client know anyone at EPCM firm working on project?
- Any relationships with GC or major subcontractors?
- Connections to consultants or owner's rep?
- Relationships with investors or lenders?

**Phase 3: Develop Warm Path Strategies**

**3.1 Direct Warm Introductions**
If client knows decision-maker directly:
- Introduction approach (email intro, call, LinkedIn message)
- Talking points to include
- Timing (now vs wait for milestone)
- What client can say to position vendor

**3.2 Indirect Warm Paths**
If connection is 2-3 degrees away:
- Path to decision-maker (A knows B, B knows target)
- How to activate connection (ask A for intro to B)
- Credibility bridges (what shared context to reference)
- Approach sequence

**3.3 Relationship-Based Positioning**
Even if no direct connection:
- Alumni angle ("I see you went to [University] - Go [Mascot]!")
- Shared interests (golf, industry association, charity work)
- Mutual contacts to reference ("I know Jane Doe mentioned...")
- Common ground to establish rapport

**Phase 4: Integration with Sales Strategy**

**4.1 Timing and Sequencing**
- Which connections to activate first?
- What's the ideal approach sequence?
- When to mention relationships (immediately vs after rapport)?
- How to layer multiple connections for credibility?

**4.2 Positioning Leverage**
How do these relationships strengthen positioning:
- Credibility boost (trusted referral vs cold outreach)
- Inside information (what client knows about needs/priorities)
- Competitive advantage (relationships competitors don't have)
- Objection prevention (trust reduces skepticism)

**4.3 Approach Customization**
Adjust outreach based on relationships:
- Opening lines that reference connection
- Subject lines for emails
- LinkedIn connection request messages
- Phone call talking points

### Output Format

Return BOTH:
1. A **research narrative** (for human review)
2. A **structured JSON object** at the end (for frontend rendering)

**Narrative Sections:**

```
## WARM INTRODUCTION PATHS

### Direct Connections
[Name at target company, relationship strength, introduction approach, what client can say]

### Indirect Paths (2-3 Degrees)
[Connection chain, how to activate, credibility bridges]

### Alumni Networks
[Shared schools/programs, how to reference, rapport-building opportunities]

## RELATIONSHIP-BASED POSITIONING

### Golf/Recreational Overlaps
[Clubs, activities, how to work into conversation]

### Professional Network Overlaps
[Industry associations, conferences, boards, how to leverage]

### Past Employer Connections
[People who worked at both companies, how to reference]

## INSIDER INTELLIGENCE

### What Client Knows That Others Don't
[Unique insights from client's relationships or past work with target]

### Competitive Advantages from Relationships
[Why client's connections give them edge over competitors]

### Objection Prevention
[How relationships reduce skepticism or speed trust-building]

## OUTREACH STRATEGY ADJUSTMENTS

### Opening Lines (Relationship-Based)
[Email/LinkedIn openers that reference connections]

### Talking Points
[What to mention, when to mention, how to position]

### Sequencing
[Order of contact activation, timing, follow-up approach]

## SOURCES
[Client notes referenced, LinkedIn profiles checked, any external sources]
```

---

## STRUCTURED OUTPUT (Required)

After the narrative, include a JSON code block with `custom_research` matching any client-specific criteria found:

```json
{
  "custom_research": {
    "title": "Client-Specific Research",
    "items": [
      {
        "criteria_name": "Active Golfers",
        "matches": [
          {
            "contact_name": "John Smith",
            "evidence": "Member of Colorado Golf Association, 8.2 handicap, plays Arrowhead GC regularly",
            "source": "https://cga.org/profile/123"
          },
          {
            "contact_name": "Sarah Johnson",
            "evidence": "Posts about golf on LinkedIn, recent Pebble Beach trip photos",
            "source": "https://linkedin.com/in/sarahjohnson"
          }
        ]
      },
      {
        "criteria_name": "University of Illinois Alumni",
        "matches": [
          {
            "contact_name": "Mike Chen",
            "evidence": "BS Civil Engineering, U of I 2005. Active in Chicago Illini Club.",
            "source": "https://linkedin.com/in/mikechen"
          }
        ]
      },
      {
        "criteria_name": "Women in Construction Network",
        "matches": [
          {
            "contact_name": "Lisa Martinez",
            "evidence": "Board member of NAWIC Dallas chapter, speaker at 2024 WIC Summit",
            "source": "https://nawic.org/chapters/dallas"
          }
        ]
      }
    ]
  }
}
```

**Custom Research Criteria Types (examples):**
- Golf connections (club memberships, handicaps, courses played)
- Alumni networks (shared universities, Greek life, athletics)
- Military/veterans (branch, service dates, veteran organizations)
- Professional associations (NAWIC, SMPS, AGC memberships)
- Geographic roots (hometown connections, where they started career)
- Past employer overlaps (people who worked at both companies)
- Board/nonprofit involvement (charity boards, advisory roles)
- Hobbies/interests (pilots, marathoners, etc.)

**Only include criteria that have actual matches.** If no golfers found, don't include "Active Golfers" with empty matches.

**If NO client-specific criteria matches found:**
```json
{
  "custom_research": null
}
```

### Constraints

**Do:**
- Prioritize warm introductions over cold outreach where possible
- Cross-reference client notes with claims data (validate connections still current)
- Assess relationship strength realistically (don't overstate weak ties)
- Provide specific, actionable outreach strategies
- Consider timing (when to activate which connections)

**Do NOT:**
- Assume relationships without evidence from client notes
- Fabricate connections or exaggerate relationship strength
- Ignore relationship recency (10-year-old connection may be stale)
- Recommend activating all connections at once (sequence strategically)
- Miss opportunities to layer multiple connections for credibility

**Quality Standards:**
- Every relationship mentioned must be grounded in client notes or claims
- Provide specific names, companies, and relationship types
- Include concrete approach strategies (not vague "reach out")
- Consider both immediate and future relationship leverage
- Balance enthusiasm with realistic assessment of tie strength

---

## Variables Produced

- `research_narrative` - Client-specific relationship intelligence (gets extracted to claims)
- `custom_research` - **UI-ready** structured JSON for Custom Research section:
  - `title` - Section title (e.g., "Client-Specific Research")
  - `items[]` - Array of criteria matches, each with:
    - `criteria_name` - e.g., "Active Golfers", "U of I Alumni", "Women in Construction"
    - `matches[]` - Array of contacts matching this criteria, each with:
      - `contact_name` - Name of matching contact
      - `evidence` - How we know (e.g., "Member of CGA, 8.2 handicap")
      - `source` - URL source (optional)

---

## Integration Notes

**Model:** gpt-4.1 (sync, 2-3 min)
**Next Steps:** Claims extraction → MergedClaims update → Section writers incorporate relationship angles
**Key Value:** Transforms generic dossier into personalized outreach with warm paths
