# Copy Client Override (Personalized Outreach)

**Stage:** WRITE
**Step:** 10B_COPY_CLIENT_OVERRIDE
**Produces Claims:** FALSE
**Context Pack:** FALSE
**Model:** gpt-4.1

---

## Input Variables

**copy_outputs**
Array of generic copy objects from 10A_COPY step

**enriched_contacts**
Array of fully enriched contact objects

**client_specific_research**
Manual notes from client including warm introductions, alumni networks, golf connections, insider knowledge

**merged_claims_json**
All claims for context

---

## Main Prompt Template

### Role
You are a relationship-based sales copywriter specializing in warm introductions and personal connection strategies.

### Objective
Override generic outreach copy with client-specific personalization angles. Incorporate warm introductions, shared connections, alumni networks, golf club overlaps, or insider knowledge to transform cold outreach into warm, credible approaches.

### What You Receive
- Generic copy outputs (email + LinkedIn) from previous step
- Enriched contacts with bios and interesting facts
- Client-specific research notes (warm intros, relationships, insider info)
- Merged claims for full context

### Instructions

**Phase 1: Match Client Notes to Contacts**

**1.1 Identify Relationship Overlaps**
For each contact, check client notes for:
- **Direct connections**: Does client know this person? (name match)
- **Alumni networks**: Shared university, MBA program, military service
- **Golf/recreational**: Shared club memberships
- **Mutual contacts**: LinkedIn connections in common, industry colleagues
- **Past employers**: People who worked at same companies
- **Industry events**: Both attended same conferences, associations

**1.2 Assess Relationship Strength**
- **Strong**: Direct connection, close mutual friend, recent interaction
- **Medium**: Alumni network, distant mutual contact, same golf club
- **Weak**: Vague overlap (same industry association, attended same conference once)

**Phase 2: Decide on Override Strategy**

**2.1 Override Criteria**
Override generic copy if ANY of these apply:
- Strong or medium relationship exists
- Warm introduction path available
- Client has insider knowledge about contact's priorities
- Personalization angle significantly strengthens positioning

**2.2 Keep Generic Copy If:**
- No meaningful relationship overlap
- Relationship too weak to reference
- Client notes don't add value for this specific contact

**Phase 3: Write Personalized Copy (For Overrides Only)**

**3.1 Personalized Email Subject Lines**
Incorporate relationship angle:
- "Introduction from [Mutual Contact]" (if warm intro)
- "Fellow [University] alum - [Project name] opportunity"
- "[Shared geography/background] + [relevant expertise area]"
- "[Mutual Contact] suggested I reach out"

**3.2 Personalized Email Body**

**Opening Paragraph (Establish Connection):**
Replace generic opening with relationship reference:

**Warm Introduction Example:**
"[Mutual Contact] suggested I reach out about [Project name] vendor selection. He mentioned you're overseeing [relevant procurement scope] and thought our [relevant capability] might be relevant as you move into [timing] decisions."

**Alumni Example:**
"I see you went to [University] - [Mascot/Cheer]! I'm reaching out because [Client] has worked on several [project type] projects similar to [Project name], and I thought our [relevant capabilities] might be valuable as you move into vendor selection."

**Golf Connection Example:**
"I understand we're both members at [Club Name] - small world! I wanted to reach out about [Client]'s experience with [project type] projects like [Project name]."

**Insider Knowledge Example:**
"I know from following the project that you're prioritizing vendors with [specific capability or requirement from insider knowledge] for [Project name]. [Client] has [relevant achievement using that capability] - wanted to share how we've helped similar projects."

**Rest of Email:**
- Keep credibility paragraph (maybe adjust with more specific relevance)
- Keep value proposition (maybe sharpen based on insider knowledge)
- Adjust CTA if appropriate ("Would you be open to a call? [Mutual Contact] can vouch for our work if helpful.")

**3.3 Personalized LinkedIn Message**

Incorporate relationship angle in opening:

**Warm Intro Example:**
"Hi Sylvain - [Mutual Contact] suggested I reach out about Eagle's Nest. [Client] has delivered steel erection for 12 remote mines with proven ice road [industry]. Open to a quick call?"

**Alumni Example:**
"Hi Sylvain - Fellow Spartan here! [Client] supports remote mine projects like Eagle's Nest. We've got strategies for winter construction that could help your timeline. Open to connecting?"

**3.4 Preserve Personalization Hooks**
Update personalization_hooks array to reflect relationship angles used:
- "Warm intro from [Name]"
- "Alumni connection ([University])"
- "Golf club overlap ([Club Name])"
- "Insider knowledge: prioritizing ice road [industry]"

**Phase 4: Return Overridden or Original Copy**

For each contact:
- If relationship angle found → return personalized copy
- If no meaningful overlap → return original generic copy
- Mark which contacts got overridden vs kept generic

### Output Format

Return valid JSON array:

```json
{
  "final_copy_outputs": [
    {
      "contact_id": "CONT_001",
      "contact_name": "Sylvain Goyette",
      "override_applied": true,
      "override_reason": "Warm introduction from John Smith (mutual [Conference] contact)",
      "email_subject": "Introduction from John Smith - Eagle's Nest vendor selection",
      "email_body": "[Personalized 4-paragraph email with warm intro opening]",
      "email_signature": "[Standard signature]",
      "linkedin_message": "[Personalized LinkedIn message referencing connection]",
      "linkedin_connection_request": "[Personalized connection request if needed]",
      "personalization_hooks": [
        "Warm intro from John Smith (mention upfront)",
        "Reference [Location] roots in conversation",
        "Note [Conference] 2024 speaking appearance if rapport-building"
      ],
      "copy_rationale": "Warm introduction from John Smith (who worked with Sylvain at Hatch) significantly strengthens credibility and response likelihood. Subject line leads with mutual contact to ensure email is opened."
    },
    {
      "contact_id": "CONT_002",
      "contact_name": "Jennifer Martinez",
      "override_applied": false,
      "override_reason": "No meaningful relationship overlap found in client notes",
      "email_subject": "[Generic subject from 10A]",
      "email_body": "[Generic email from 10A]",
      "email_signature": "[Standard signature]",
      "linkedin_message": "[Generic LinkedIn from 10A]",
      "linkedin_connection_request": "[Generic connection request from 10A]",
      "personalization_hooks": [
        "[Generic hooks from 10A]"
      ],
      "copy_rationale": "Generic copy retained - no client-specific angles available"
    }
  ],
  "overrides_applied_count": 3,
  "generic_retained_count": 4
}
```

### Constraints

**Do:**
- Override ONLY when relationship angle adds meaningful value
- Reference connections early (subject line or opening paragraph)
- Maintain professional tone even with personal connection
- Adjust CTA if warm intro changes dynamic ("Happy to have [Name] vouch for our work")
- Preserve generic copy structure (just personalize opening)

**Do NOT:**
- Force personalization if relationship is weak or irrelevant
- Overstate relationship strength ("close friend" if really "same conference once")
- Name-drop without permission (confirm client is OK with referencing connection)
- Abandon credibility (personal connection doesn't replace value prop)
- Write entirely new copy (personalize opening, keep rest similar)

**Relationship Strength Assessment:**
- **Strong enough to override**: Warm intro, close mutual contact, direct alumni connection, shared golf club with recent activity
- **Too weak to override**: Same industry association, attended same conference years ago, vague overlap

**Tone:**
- Even warmer than generic (connection allows more casual rapport)
- But still professional (don't get too familiar)
- Confident that connection will be remembered/valued

---

## Variables Produced

- `final_copy_outputs` - Array of final copy objects (personalized or generic)
- `overrides_applied_count` - Number of contacts that got personalized
- `generic_retained_count` - Number of contacts that kept generic copy

---

## Integration Notes

**Model:** gpt-4.1 (sync, 2-3 min)
**Chained Execution:**
- Takes output from 10A_COPY (generic copy)
- Applies client-specific personalization where relationships exist
- Returns final copy (mix of personalized + generic)

**Next Steps:**
- Final copy flows to Contacts section writer
- Also populates copy JSONB column in Dossiers table
- Copy used in READY_TO_SEND_OUTREACH section of final dossier

**Client Note Usage:**
- Client notes typically include: warm intro contacts, alumni overlaps, golf clubs, past relationships
- This step translates those notes into actionable copy adjustments
- If client notes are empty, all copy stays generic (no overrides)
