# Contacts Sheet

NOTES FROM AUTHOR (MAY OR MAY NOT REFLECT WHATS BELOW): Okay, so I mentioned this in the dossier sections as well, but this is related to what actually gets rendered. Essentially, we're going to render this in the dossier. Each contact gets their own sort of section. It's just how we'll kind of run it. All the code for that is baked into the actual app, so it's fine. We just need to get to the point where we have all this stuff. Anyway, yeah, so what's happening here is there's a key contacts deep research step that happens early on. That generates a few of the contacts, most of them, I'll say. And then there's other deep research steps and agent steps that generate claims, and all these claims are sitting at, you know, we've got a bunch of JSON claims, really. We're going to take all of those claims, and we're going to pass them to the Enrich Contacts step or AI. And it's effectively a really tailor-made claims extractor, but just for the contacts, the contacts that are relevant to the opportunity and the ICP. And then it's going to, you know, for each of those contacts, create a list of, like, all the stuff we got for them. Or, sorry, it's going to pass over this information by returning a JSON object that has an array. And for each item within that array, we will run the Enrich Contact step, and that is an agent that has access to tools like AnyMail Finder and Firecrawl and an Appify LinkedIn scraper. And we're basically asking it to fill out these fields, you know, the bio, the LinkedIn summary, so we'll know if they have one, et cetera, and so on. And, yeah, we will, for each of these, not only will it get that agent that creates much of that information, but within that same step that's being called asynchronously and in parallel, there's a chain, and that is the agent that finds some of the contact information, generates the summaries, et cetera. Then there's also the copy and the copywriting, which is the email and the LinkedIn. And then we have a client-specific version of that copywriting thing, which, you know, will receive its own prompt from somewhere. We just got to pass it there. And all of this stuff is going to be, you know, critical. We're going to probably need to extract some sort of variables or give the agent prompts, you know, something that is actually, you know, at the end of the day, I need to make sure we have the main contact information called out as its own sort of JSON so we can parse it and render it, like the names and the emails and the LinkedIn URLs, the, you know, summary about all this other stuff. I don't know. So, yeah, it will need to be rendered in JSON. We'll have that. Same deal with the email copy. So, like the subject line, whatever, all the new lines got to render, you know, same deal. But overall, this one is relatively straightforward. Lord.

**Source file:** `DOSSIER_FLOW_TEST - Contacts.csv`
**Sheet name in Make.com:** `Contacts`

## Purpose

The **Contacts** sheet stores **enriched contact data** produced by the 06_ENRICH_CONTACTS pipeline. Each row is a contact discovered for a lead.

## Structure

| Column | Field | Description |
|--------|-------|-------------|
| A | RUN_ID | Pipeline run identifier |
| B | DOSSIER_ID | Parent dossier identifier |
| C | FIRST_NAME | Contact first name |
| D | LAST_NAME | Contact last name |
| E | EMAIL | Verified email address |
| F | LINKEDIN_URL | LinkedIn profile URL |
| G | LINKEDIN_SUMMARY | Summary from LinkedIn research |
| H | WEB_SUMMARY | Summary from web research |
| I | SIGNAL_RELEVANCE | Why this contact is relevant to the signal |
| J | INTERESTING_FACTS | Notable facts about the contact |
| K | EMAIL_COPY | Generic outreach email copy |
| L | LINKEDIN_COPY | Generic LinkedIn message copy |
| M | CLIENT_EMAIL_COPY | Client-specific email copy |
| N | CLIENT_LINKEDIN_COPY | Client-specific LinkedIn copy |

## Data Flow

```
06_ENRICH_CONTACTS (parent)
    │
    ├── For each contact from Contact Discovery:
    │   │
    │   └── 06.2_ENRICH_CONTACT_TEMPLATE (child)
    │       │
    │       ├── LinkedIn research
    │       ├── Web research
    │       ├── Email generation
    │       └── Write row to Contacts sheet
    │
    └── Continue to next contact
```

## Copy Generation

Each contact gets 4 types of outreach copy:

### Generic Email (EMAIL_COPY)
Standard outreach without client context.

### Generic LinkedIn (LINKEDIN_COPY)
Short (<250 char) LinkedIn connection message.

### Client Email (CLIENT_EMAIL_COPY)
Personalized with client differentiators and signal context.

### Client LinkedIn (CLIENT_LINKEDIN_COPY)
Shorter personalized message for LinkedIn.

## Migration Notes

1. **Database table** - Create `dossier_contacts_v2` table
2. **Normalized structure** - Link to dossier via foreign key
3. **Copy versioning** - Track changes to outreach copy
4. **Email validation** - Validate email formats
5. **LinkedIn URLs** - Validate URL format and existence

---

## NOTES FROM CURSOR: Understanding Your Requirements

### What You're Describing

**1. Two-Phase Contact Discovery**
Contacts come from two sources: (1) the key contacts deep research step (early in pipeline) finds initial contacts, and (2) the enrich contacts step extracts contacts from ALL claims (not just the key contacts step). The second phase is important because other research steps might have discovered contacts too.

**What this means:** Contact discovery isn't just one step - it's an initial discovery plus a comprehensive extraction from all accumulated claims. The system needs to handle both phases and combine their results.

**2. Enrich Contacts as Specialized Claims Extraction**
The enrich contacts step is "effectively a really tailor-made claims extractor, but just for the contacts." It takes all claims and extracts contact-relevant information, filtering by what's relevant to the opportunity and ICP.

**What this means:** This step is like claims extraction, but specialized for contacts. It looks through all claims and pulls out people who might be decision-makers or relevant contacts.

**3. Parallel Enrichment with Internal Chaining**
For each contact discovered, you run an enrichment process. All contacts are enriched in parallel (async). But within each contact's enrichment, there's a chain: (1) enrich contact (get email, LinkedIn, bio, etc.), (2) generate generic copy, (3) generate client-specific copy.

**What this means:** The system needs to handle parallel execution (all contacts at once) with sequential steps within each contact (enrich → copy → client copy). Each contact goes through the full chain independently.

**4. Copy as Structured JSON**
You need email copy and LinkedIn copy stored in a way that preserves formatting (newlines, structure). The email copy needs subject, body, signature as separate fields so the frontend can render it properly.

**What this means:** Copy should be stored as structured JSON, not plain text. This preserves formatting and makes it easy for the frontend to parse and render.

**5. Two Versions of Copy (Generic + Client-Specific)**
You want one standard copy format that applies to all clients, then clients can modify it (but not create from scratch). You want to see both versions: what your system generated and what the client's version looks like.

**What this means:** Generate generic copy first, then if the client has copy preferences, generate a client-specific version. Store both so you can compare them. The client version is based on the generic version, not created from scratch.

**6. Contact Data as Renderable JSON**
You need contact information (names, emails, LinkedIn URLs, summaries) stored as JSON so the frontend can parse and render it. Each contact gets its own section in the dossier.

**What this means:** Contact data should be structured JSON that matches what the frontend expects. The system needs to ensure all required fields are present and properly formatted.

### Key Insight

The Contacts sheet represents "enriched contacts with outreach copy" - but like everything else, this needs to be per-run and per-dossier. When you run 80 dossiers, each one has its own contacts. The enrichment process is parallel (all contacts at once) but chained (each contact goes through enrich → copy → client copy). The system should track this chain so you can see where any contact is in the process and what went wrong if something fails.

---

## NOTES FROM CLAUDE: Final Schema Design

**After extensive back-and-forth, here's how contacts fit into the final schema:**

### What You Really Needed

1. **BOTH renderable AND processing columns** - You said: "The reason I wanted those columns originally is because they're simple. I can easily run another prompt over it to generate email copy... I want those in addition. Called out explicitly that they are renderable columns."

   Solution: Contacts sheet has TWO column sets:
   - **Columns A-S (RENDERABLE):** For app display - id, dossier_id, name, first_name, last_name, title, email, phone, linkedin_url, linkedin_connections, bio_paragraph, tenure_months, previous_companies, education, skills, recent_post_quote, is_primary, source
   - **Columns T-AF (PROCESSING):** For generating copy - tier, bio_summary, why_they_matter, signal_relevance, interesting_facts, linkedin_summary, web_summary, email_copy, linkedin_copy, client_email_copy, client_linkedin_copy, confidence

2. **Match app's exact field names** - You provided the complete variable reference showing exact fields your app expects (snake_case). The renderable columns match this exactly so you can "just swap sources" in the app without transformation.

3. **Two sources for contacts:**
   - **Key Contacts research** - Research step that finds primary decision-makers
   - **Claims extraction** - Contacts mentioned in claims
   - Both feed into the same enrichment workflow

4. **Chained enrichment:** Each contact goes through:
   - **Enrich step** - Agent with tools (LinkedIn, web search) fills out bio_paragraph, tenure_months, previous_companies, etc.
   - **Copy step** - Generate generic email_copy and linkedin_copy
   - **Client copy step** - Generate client_email_copy and client_linkedin_copy (personalized)

### Final Contacts Sheet Structure

The Contacts sheet (execution layer) now has:

**RENDERABLE columns (A-S)** - Match app expectations:
- `id` (UUID), `dossier_id` (FK), `run_id` (FK)
- `name`, `first_name`, `last_name`, `title`, `email`, `phone`
- `linkedin_url`, `linkedin_connections`, `bio_paragraph`
- `tenure_months`, `previous_companies` (JSON), `education`, `skills` (JSON)
- `recent_post_quote`, `is_primary`, `source`, `created_at`

**PROCESSING columns (T-AF)** - For copy generation:
- `tier`, `bio_summary`, `why_they_matter`, `signal_relevance`
- `interesting_facts` (JSON), `linkedin_summary`, `web_summary`
- `email_copy`, `linkedin_copy`, `client_email_copy`, `client_linkedin_copy`
- `confidence`

### Why Both Sets Are Needed

**Your quote:** "Basically, that's just sort of a stopgap for me so that I can quickly find a path to render this project. But ultimately, you know, I'm going to return more than that in the other columns like I originally had."

**RENDERABLE columns:**
- App can display immediately
- No transformation needed (snake_case field names)
- "Just swap sources" from Sheets → Supabase

**PROCESSING columns:**
- Provide context for generating copy
- Help make decisions about contact priority (tier, confidence)
- Enable iteration on copy generation (can re-run prompts over these fields)
- Capture enrichment results (linkedin_summary, web_summary)

### Parallel Enrichment with Internal Chaining

**How it works:**
1. Contact discovery finds 5 contacts
2. Create 5 rows in Contacts sheet (different contact_ids)
3. Enrich all 5 in parallel:
   - Each contact_id → enrichment agent → fills RENDERABLE columns (bio_paragraph, tenure_months, etc.)
   - Agent output also fills PROCESSING columns (linkedin_summary, web_summary, why_they_matter)
4. Generate copy (chained after enrichment):
   - Each contact_id → copy generation → fills email_copy, linkedin_copy
5. Generate client copy (chained after generic copy):
   - Each contact_id → client copy generation → fills client_email_copy, client_linkedin_copy

**Result:** 5 complete contact rows, ready for rendering and copy generation.

### Two Versions of Copy

**Generic copy (email_copy, linkedin_copy):**
- Standardized outreach templates
- Could work for any client in similar industry
- Good starting point

**Client-specific copy (client_email_copy, client_linkedin_copy):**
- Personalized with client's brand voice
- References client's specific differentiators (ESOP, Butler Builder, etc.)
- Uses client's actual examples and language

Both versions stored, sales team can choose which to use or blend.

### Contact Data as Renderable JSON

You said: "All fields needed for rendering." The RENDERABLE columns match your app's exact expectations:
- Name fields for personalization (first_name, last_name)
- Contact info for outreach (email, phone, linkedin_url)
- Background for context (bio_paragraph, tenure_months, previous_companies, education, skills)
- Activity for relevance (recent_post_quote, linkedin_connections)
- Flags for prioritization (is_primary, source, confidence)

**STATUS:** Schema finalized with Contacts sheet having both renderable columns (for app display) and processing columns (for copy generation). Multiple rows per run, complete contact cards ready for rendering.
