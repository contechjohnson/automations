# Contacts Sheet

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
