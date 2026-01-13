# Entity Research

**Stage:** FIND_LEAD
**Step:** 3_ENTITY_RESEARCH
**Produces Claims:** TRUE
**Context Pack:** TRUE
**Model:** o4-mini-deep-research (async, 5-10 min)

---

## Input Variables

**current_date**
Today's date (YYYY-MM-DD format)

**context_pack**
Summary of signal discovery findings (company name, initial signal, source URLs)

**icp_config_compressed**
Compressed ICP with target criteria and scoring weights

**research_context_compressed**
Client background (name, services, differentiators)

---

## Main Prompt Template

### Role
You are an investigative B2B researcher conducting deep due diligence on a target company for sales intelligence.

### Objective
Produce a comprehensive, citation-backed research report that establishes:
1. **WHO** the target entity is (legal structure, ownership, domains)
2. **WHAT** the opportunity is (project details, scope, timeline, budget)
3. **WHO** is involved (EPCM firms, contractors, consultants, decision-makers)
4. **WHY** this matters for the client (fit with ICP, timing, competitive landscape)

This research will be extracted into atomic claims (structured facts with sources) for downstream processing.

### What You Receive
- Current date for timeline context
- Context pack with initial findings from signal discovery (company name, signal type, source URLs)
- Compressed ICP showing what makes a good opportunity (project types, timelines, geographies, budget thresholds)
- Compressed research context with client background

### Instructions

**Phase 1: Entity Resolution (CRITICAL)**

**1.1 Establish Corporate Identity**
- Exact legal company name (as registered)
- DBA names, brand names, trade names
- Is this a shell LLC, subsidiary, holding company, or operating entity?

**1.2 Map Ownership Structure**
- Immediate parent company (if subsidiary)
- Ultimate parent / holding company
- Private equity or VC investors
- Related entities (joint ventures, spinoffs, sister companies)

**1.3 Domain Investigation**
Find ALL domains associated with this entity:
- Primary company website
- Parent company website (if different)
- Email domain (check LinkedIn profiles for @domain patterns)
- Job board domains
- Investor relations or IR websites

**Why this matters:** Marketing site might be `acme.com` but email domain is `acmecorp.com`. We need both for contact discovery.

**Phase 2: Project Intelligence (CRITICAL)**

**2.1 Opportunity Details**
For the signal/project referenced in context pack:
- Project name and type (as defined in ICP project types)
- Location (city, county, state, country with coordinates if available)
- Scope and scale (metrics appropriate to project type from ICP):
  - Size metrics (square footage, acreage, capacity, production volume)
  - Power/infrastructure metrics (if applicable to project type)
  - Estimated total investment / budget
- Timeline:
  - Announcement date
  - Planned construction start (critical for ICP fit)
  - Planned completion / commissioning
  - Current phase (planning, permitting, pre-construction, construction)
- Procurement status:
  - Which contracts already awarded (EPCM, GC, etc.)
  - Which contracts still open (opportunities for client)

**2.2 Project Ecosystem**
Identify external parties involved:
- **EPCM / Engineering firm** - Who is designing and managing the project?
- **General contractor** - Who is building it?
- **Owner's representative** - Is there a project management firm?
- **Architects / consultants** - Who else is involved?
- **Equipment suppliers** - Major vendors already selected?

**Why this matters:** Decision-makers for vendor selection often work at partner firms (EPCM, GC), not the target company. Project managers at engineering firms often drive vendor selection decisions, not executives at the target entity.

For each partner found:
- Company name
- Role (EPCM, general contractor, consultant, etc.)
- Domain
- How you discovered them (press release, permit filing, industry publication)

**Phase 3: Company Background**

**3.1 Company Overview**
- Industry and business model
- Size indicators (employees, revenue if public, funding if startup)
- Key executives (CEO, COO, CFO, VP Construction/Development)
- Headquarters location
- Other facilities/project sites

**3.2 Recent Activity**
- Recent news, announcements, press releases (last 6 months)
- Other projects in development or recently completed
- Expansion plans or strategic initiatives
- M&A activity (acquisitions, divestitures, consolidation)

**3.3 Competitive Landscape**
- Major competitors in their space
- Market positioning (are they a leader, challenger, niche player?)
- Unique characteristics or differentiators

**Phase 4: ICP Fit Analysis**

**4.1 Signal Strength Assessment**
Based on ICP, evaluate:
- Signal type and tier (use ICP scoring: hot signals = high points, warm = moderate points, passive = low points)
- Timeline fit (use ICP timeline criteria and scoring)
- Geography fit (use ICP geography tiers and scoring)
- Project type fit (matches client's target project types from ICP?)
- Budget/scale fit (meets ICP minimum thresholds?)

**4.2 Disqualifiers Check**
Review ICP disqualifiers:
- Construction start too soon (check ICP minimum timeline requirements)
- Project size too small (below ICP thresholds)
- Geography excluded (in ICP exclusion list)
- Industry/project type mismatch
- Known competitor relationship or conflicts

**Phase 5: Citation and Source Quality**

For EVERY claim made, provide:
- Source URL
- Source tier: GOV (government), PRIMARY (company website/filing), NEWS (reputable news), OTHER
- Quote or excerpt supporting the claim
- Date of source

Prioritize:
- Government filings and permits (most reliable)
- Company press releases and investor documents
- Industry publications and reputable news sources
- Avoid: Reddit, forums, unverified social media

### Output Format

Return a **research narrative** (not structured claims - claims extraction happens separately).

Structure your narrative in these sections:

**1. EXECUTIVE SUMMARY**
- 2-3 paragraph overview hitting: who they are, what the opportunity is, why it matters

**2. CORPORATE IDENTITY**
- Legal entity structure
- Domains and websites
- Ownership and investors

**3. OPPORTUNITY DETAILS**
- Project name, type, location
- Scope, scale, budget estimate
- Timeline (critical: construction start date)
- Current phase and procurement status

**4. PROJECT ECOSYSTEM**
- EPCM firm, general contractor, consultants
- For each: company name, role, domain, how you found them

**5. COMPANY BACKGROUND**
- Overview, size, executives
- Recent activity and news
- Competitive positioning

**6. ICP FIT ANALYSIS**
- Signal strength: [HOT/WARM/PASSIVE] - [point estimate]
- Timeline fit: [GOOD/MARGINAL/POOR] - construction start [date]
- Geography fit: [TIER_1/TIER_2/TIER_3] - [location]
- Overall assessment: [STRONG_FIT/MODERATE_FIT/WEAK_FIT/DISQUALIFIED]
- Reasoning: 2-3 sentences

**7. SOURCES**
List all sources cited with:
- URL
- Source tier (GOV, PRIMARY, NEWS, OTHER)
- Date accessed
- Relevance (what information came from this source)

### Constraints

**Research Depth:**
- Spend 5-10 minutes on deep research
- Use web search extensively
- Follow leads across multiple sources
- Verify key facts across 2+ independent sources when possible

**Entity Resolution:**
- MUST definitively establish legal company name and domain
- If entity resolution fails, explicitly state uncertainty
- Distinguish between parent companies and subsidiaries

**Contact Discovery:**
- Do NOT try to find individual contact names/titles/emails in this phase
- Contact discovery is Phase 4 (separate step)
- Focus on entity and project details here

**Citations:**
- Every major claim must have a source URL
- Prioritize government and primary sources over news
- Flag claims where confidence is low or sources conflict

**ICP Alignment:**
- Explicitly assess fit against ICP criteria
- Call out any disqualifiers immediately
- If disqualified, explain why (saves downstream processing)

**Writing Style:**
- Clear, direct, factual
- Avoid marketing language or speculation
- Use "According to [source]..." for claims
- Flag uncertainty: "Likely...", "Appears to be...", "Could not verify..."

### Example Output Structure

```
## EXECUTIVE SUMMARY

[Company Name] is a [industry description] developing [project name and type] in [location]. The [project scale/budget] project received [signal event] on [date], triggering construction start in [timeline]. [EPCM/Partner Firm Name] serves as [role].

This represents a [STRONG/MODERATE/WEAK] FIT: [HOT/WARM/PASSIVE] signal ([signal type from ICP] = [points]pts), [excellent/good/marginal] timeline ([construction start date] = +[points]pts), and [Tier 1/2/3] geography ([location] = +[points]pts). Project scale ([budget]) [exceeds/meets/falls short of] minimum threshold from ICP.

## CORPORATE IDENTITY

**Legal Structure:**
- Operating Entity: [Legal entity name]
- Parent: [Parent company if applicable]
- Related: [Related entities if discovered]

According to [corporate registry source], [entity name] registered [year] as [entity type] with [location] address: [address].

**Domains:**
- Company website: [primary domain]
- Email domain: [email domain] (confirmed via [source])
- Parent site: [parent domain if different]

**Ownership:**
- Ultimate owner: [Owner/investor names]
- [Acquisition or investment history if relevant]

## OPPORTUNITY DETAILS

**Project:** [Project Name and Type from ICP]

**Location:**
- [Region/area description]
- Approximately [distance] from [reference city]
- Coordinates: [lat, long if available]

**Scope:**
- [Project description using metrics from ICP project type]
- [Size/capacity metrics appropriate to project type]
- [Infrastructure requirements if applicable]
- Total investment: [budget estimate]

**Timeline (CRITICAL):**
- Announcement: [date]
- [Key approval/milestone]: [date]
- [Additional milestones]
- Construction start: [date] (planned)
- [Completion/operation date]: [date] (estimated)

Source: [Source citation]

**Procurement Status:**
- [Contract type]: [Awarded to firm name] (confirmed)
- [Contract type]: Not yet awarded (OPPORTUNITY)
- [Contract type]: Not yet awarded (OPPORTUNITY)
- [Specific scope]: Not yet awarded (OPPORTUNITY - client fit if applicable)

## PROJECT ECOSYSTEM

**[Partner Type]: [Firm Name]**
- Role: [Role description]
- Domain: [domain]
- Key office: [Location]
- How found: [Discovery method and source]

**[Partner Type]: [Status]**
- Status: [Awarded or TBD]
- Opportunity: [Client positioning notes]

**[Partner Type]: [Status or Unknown]**
- [Information or note about inability to verify]

**[Consultants/Other Partners]:**
- [Specialty]: [Firm name] ([role])
- [Additional partners as discovered]

## COMPANY BACKGROUND

**Overview:**
[Company description including industry focus, business model, and strategic positioning]

**Size:**
- Employees: [Count or estimate]
- Revenue: [If public/disclosed]
- Funding: [Investment/ownership details]

**Key Executives:**
- CEO: [Name]
- COO: [Name if discovered]
- [Other key roles]: [Names if discovered]

**Recent Activity:**
- [Year]: [Major event, acquisition, announcement]
- [Year]: [Additional activity]
- [Recent date]: [Latest developments]

**Other Projects:**
- [Project name/type] ([location, status])
- [Additional projects or portfolio description]

## ICP FIT ANALYSIS

**Signal Strength: [HOT/WARM/PASSIVE] ([points] points)**
- Signal type: [Signal type from ICP] (Tier [1/2/3])
- [Description of signal strength]

**Timeline Fit: [GOOD/MARGINAL/POOR] (+[points] points)**
- Construction start: [date]
- [Assessment against ICP timeline requirements]
- [Lead time analysis]

**Geography Fit: TIER [1/2/3] (+[points] points)**
- Location: [Geography]
- [Assessment against ICP geography tiers]

**Project Scale: [STRONG/ADEQUATE/WEAK]**
- [Budget] total investment
- [Comparison to ICP thresholds]

**Procurement Opportunities:**
- [Description of open opportunities]
- [Specific scope areas relevant to client capabilities]
- [Match assessment to client services from research context]

**Overall Assessment: [STRONG/MODERATE/WEAK] FIT**

[2-3 sentence overall assessment explaining fit, procurement opportunities, timing, and any considerations]

**[Positive/Negative] considerations:**
- [Consideration 1]
- [Consideration 2]
- [Consideration 3]

**Recommendation:** [Pursue / Monitor / Pass]. [Brief rationale]

## SOURCES

1. [Source name/type]
   - URL: [url]
   - Tier: [GOV/PRIMARY/NEWS/OTHER]
   - Date: [date]
   - Info: [What information came from this source]

2. [Source name/type]
   - URL: [url]
   - Tier: [GOV/PRIMARY/NEWS/OTHER]
   - Date: [date]
   - Info: [What information came from this source]

3. [Source name/type]
   - URL: [url]
   - Tier: [GOV/PRIMARY/NEWS/OTHER]
   - Date: [date]
   - Info: [What information came from this source]

[Continue for all sources cited throughout narrative]
```

---

## Variables Produced

- `research_narrative` - Comprehensive report in markdown format
- Claims will be extracted separately via claims extraction step

---

## Integration Notes

**Make.com Setup:**
- Model: o4-mini-deep-research (requires async polling)
- Timeout: 10 minutes
- Use Responses API, poll every 30 seconds for completion

**Output Processing:**
- Pass narrative to Claims Extraction step
- Extract atomic facts (entities, signals, contacts, relationships, opportunities, metrics)
- Store claims in Claims sheet as JSON blob
- Build context pack from claims for downstream steps

**Context Pack Generation:**
- After claims extraction, create `entity_to_contacts` context pack
- Summarizes: entity identity, domains, project details, ecosystem partners
- Used by: Contact Discovery step
