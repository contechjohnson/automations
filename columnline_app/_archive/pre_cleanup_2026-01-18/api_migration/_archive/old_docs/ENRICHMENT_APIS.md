# Enrichment APIs Reference

This document covers external APIs used for contact enrichment in the dossier pipeline.

---

## Overview

| API | Purpose | Cost |
|-----|---------|------|
| **AnyMailFinder** | Email lookup by name/domain/LinkedIn | 1 credit per valid email |
| **Apify LinkedIn Scraper** | Full LinkedIn profile data | $10 per 1,000 profiles |

---

## 1. AnyMailFinder

**Purpose:** Find and verify email addresses for decision-makers.

### Quick Reference

| Property | Value |
|----------|-------|
| **Base URL** | `https://api.anymailfinder.com/v5.1/` |
| **Auth** | `Authorization: YOUR_API_KEY` header |
| **Timeout** | 180 seconds (real-time SMTP verification) |
| **Pricing** | 1 credit = 1 valid email; risky/not_found = free |

### Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/find-email/person` | POST | Find email by name + domain |
| `/find-email/company` | POST | All emails at a domain |
| `/find-email/decision-maker` | POST | Find CEO/CTO/CFO etc. by role |
| `/find-email/linkedin` | POST | LinkedIn URL to email |
| `/verify-email` | POST | Verify existing email |
| `/bulk` | POST | Batch operations |
| `/account` | GET | Check remaining credits |

### Email Status Levels

| Status | Meaning | Cost |
|--------|---------|------|
| `valid` | Deliverable, SMTP verified | 1 credit |
| `risky` | May exist, inconclusive | FREE |
| `not_found` | No email found | FREE |
| `blacklisted` | Blocked by policy | FREE |

**Important:** Always use `valid_email` field (not `email`) to get verified-only emails.

### Find Email by Name + Domain

```python
import requests

def find_email(name: str, domain: str, api_key: str) -> dict:
    """
    Find email for a person at a company.

    Args:
        name: Full name (e.g., "John Smith")
        domain: Company domain (e.g., "acmecorp.com")
        api_key: AnyMailFinder API key

    Returns:
        dict with email, status, valid_email
    """
    response = requests.post(
        "https://api.anymailfinder.com/v5.1/find-email/person",
        headers={
            "Authorization": api_key,
            "Content-Type": "application/json"
        },
        json={
            "full_name": name,
            "domain": domain
        },
        timeout=180  # Real-time SMTP verification can take time
    )

    data = response.json()
    return {
        "email": data.get("valid_email"),  # Only verified emails
        "status": data.get("email_status"),
        "raw_email": data.get("email")
    }

# Usage
result = find_email("John Smith", "acmecorp.com", "YOUR_API_KEY")
if result["email"]:
    print(f"Found verified email: {result['email']}")
```

### Find Email by LinkedIn URL

```python
def find_email_by_linkedin(linkedin_url: str, api_key: str) -> dict:
    """
    Find email from LinkedIn profile URL.

    Args:
        linkedin_url: LinkedIn profile URL
        api_key: AnyMailFinder API key

    Returns:
        dict with email, status
    """
    response = requests.post(
        "https://api.anymailfinder.com/v5.1/find-email/linkedin",
        headers={
            "Authorization": api_key,
            "Content-Type": "application/json"
        },
        json={"linkedin_url": linkedin_url},
        timeout=180
    )

    data = response.json()
    return {
        "email": data.get("valid_email"),
        "status": data.get("email_status")
    }

# Usage
result = find_email_by_linkedin("https://www.linkedin.com/in/johnsmith", "YOUR_API_KEY")
```

### Find Decision Maker

```python
def find_decision_maker(domain: str, role: str, api_key: str) -> dict:
    """
    Find email for a specific role at a company.

    Args:
        domain: Company domain
        role: Role category (cto, cfo, ceo, vp-sales, vp-marketing, hr-head, etc.)
        api_key: AnyMailFinder API key

    Returns:
        dict with email, status
    """
    response = requests.post(
        "https://api.anymailfinder.com/v5.1/find-email/decision-maker",
        headers={
            "Authorization": api_key,
            "Content-Type": "application/json"
        },
        json={
            "domain": domain,
            "category": role
        },
        timeout=180
    )

    data = response.json()
    return {
        "email": data.get("valid_email"),
        "status": data.get("email_status"),
        "category": role
    }

# Usage
cto = find_decision_maker("techcorp.com", "cto", "YOUR_API_KEY")
```

### Bulk Search

```python
def bulk_find_emails(searches: list, api_key: str) -> list:
    """
    Find emails for multiple people in one request.

    Args:
        searches: List of {"full_name": str, "domain": str} dicts
        api_key: AnyMailFinder API key

    Returns:
        List of results
    """
    response = requests.post(
        "https://api.anymailfinder.com/v5.1/bulk",
        headers={
            "Authorization": api_key,
            "Content-Type": "application/json"
        },
        json={"searches": searches},
        timeout=300
    )

    return response.json().get("results", [])

# Usage
searches = [
    {"full_name": "John Smith", "domain": "acmecorp.com"},
    {"full_name": "Jane Doe", "domain": "techcorp.com"}
]
results = bulk_find_emails(searches, "YOUR_API_KEY")
```

### Check Account Credits

```python
def get_credits(api_key: str) -> int:
    """Get remaining API credits."""
    response = requests.get(
        "https://api.anymailfinder.com/v5.1/account",
        headers={"Authorization": api_key}
    )
    return response.json().get("credits_left", 0)
```

### Webhook Support

For async processing, add `x-webhook-url` header:

```python
response = requests.post(
    "https://api.anymailfinder.com/v5.1/find-email/person",
    headers={
        "Authorization": api_key,
        "Content-Type": "application/json",
        "x-webhook-url": "https://your-server.com/webhook"
    },
    json={"full_name": name, "domain": domain}
)
# Returns immediately; result POSTed to webhook when complete
```

---

## 2. Apify LinkedIn Scraper

**Purpose:** Extract full LinkedIn profile data including work history, skills, and contact info.

### Quick Reference

| Property | Value |
|----------|-------|
| **Actor** | `dev_fusion/linkedin-profile-scraper` |
| **Actor ID** | `2SyF0bVxmgGr8IVCZ` |
| **Store URL** | https://apify.com/dev_fusion/linkedin-profile-scraper |
| **Auth** | Apify API token |
| **Pricing** | $10 per 1,000 profiles |
| **Rating** | 4.6/5 (110 reviews, 34K+ users) |

### Key Features

- **No LinkedIn cookies required** - Works without authentication
- **Automatic email discovery** - Built-in email finding
- **Phone number lookup** - Available for paid users
- **Bulk processing** - Concurrent profile scraping
- **Complete profile data** - Work history, education, skills, etc.

### Installation

```bash
pip install apify-client
```

### Basic Usage

```python
from apify_client import ApifyClient

def scrape_linkedin_profiles(profile_urls: list, api_token: str) -> list:
    """
    Scrape LinkedIn profiles for detailed information.

    Args:
        profile_urls: List of LinkedIn profile URLs
        api_token: Apify API token

    Returns:
        List of profile data dicts
    """
    client = ApifyClient(api_token)

    run_input = {
        "profileUrls": profile_urls
    }

    # Run the actor and wait for completion
    run = client.actor("dev_fusion/linkedin-profile-scraper").call(run_input=run_input)

    # Collect results
    results = []
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        results.append(item)

    return results

# Usage
profiles = scrape_linkedin_profiles(
    ["https://www.linkedin.com/in/williamhgates"],
    "YOUR_APIFY_TOKEN"
)
```

### Output Fields

The scraper returns comprehensive profile data:

```python
{
    # Basic Info
    "linkedinUrl": "https://www.linkedin.com/in/williamhgates",
    "firstName": "Bill",
    "lastName": "Gates",
    "fullName": "Bill Gates",
    "headline": "Co-chair, Bill & Melinda Gates Foundation",
    "connections": 500,
    "followers": 15000,

    # Contact (auto-discovered)
    "email": "found@example.com",
    "mobileNumber": "+1234567890",  # Paid users only

    # Current Job
    "jobTitle": "Co-chair",
    "companyName": "Bill & Melinda Gates Foundation",
    "companyIndustry": "Non-profit Organizations",
    "companyWebsite": "https://www.gatesfoundation.org",
    "companyLinkedin": "https://www.linkedin.com/company/gatesfoundation",
    "companySize": "1001-5000",
    "jobLocation": "Seattle, Washington, United States",
    "jobStartedOn": "2021-01",
    "jobStillWorking": True,
    "currentJobDuration": "3 yrs 6 mos",

    # Work History (array)
    "experiences": [
        {
            "companyName": "Bill & Melinda Gates Foundation",
            "title": "Co-chair",
            "jobDescription": "Leading foundation initiatives...",
            "jobStartedOn": "2021-01",
            "jobEndedOn": None,
            "jobStillWorking": True,
            "jobLocation": "Seattle, Washington, United States",
            "companyWebsite": "https://www.gatesfoundation.org",
            "companyIndustry": "Non-profit Organizations",
            "companySize": "1001-5000"
        }
    ],

    # Education (array)
    "educations": [
        {
            "schoolName": "Harvard University",
            "degree": "Bachelor of Arts",
            "fieldOfStudy": "Computer Science",
            "startYear": 1973,
            "endYear": 1975
        }
    ],

    # Skills (array)
    "skills": ["Software Development", "Strategy", "Leadership"],

    # Languages (array)
    "languages": ["English"],

    # Additional arrays
    "certifications": [...],
    "publications": [...],
    "recommendations": [...],
    "volunteerExperiences": [...],
    "patents": [...]
}
```

### Advanced Usage with Error Handling

```python
from apify_client import ApifyClient
import json

def enrich_contacts_from_linkedin(
    linkedin_urls: list,
    api_token: str
) -> tuple[list, list]:
    """
    Enrich contacts with LinkedIn data.

    Args:
        linkedin_urls: List of LinkedIn profile URLs
        api_token: Apify API token

    Returns:
        Tuple of (successful_profiles, failed_urls)
    """
    client = ApifyClient(api_token)

    run_input = {"profileUrls": linkedin_urls}

    try:
        run = client.actor("dev_fusion/linkedin-profile-scraper").call(
            run_input=run_input,
            timeout_secs=3600  # 1 hour max
        )

        successful = []
        failed = []

        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            if item.get("succeeded", True) and not item.get("error"):
                # Extract key fields for contact enrichment
                successful.append({
                    "linkedin_url": item.get("linkedinUrl"),
                    "name": item.get("fullName"),
                    "first_name": item.get("firstName"),
                    "last_name": item.get("lastName"),
                    "email": item.get("email"),
                    "phone": item.get("mobileNumber"),
                    "headline": item.get("headline"),
                    "title": item.get("jobTitle"),
                    "company": item.get("companyName"),
                    "company_website": item.get("companyWebsite"),
                    "company_industry": item.get("companyIndustry"),
                    "company_size": item.get("companySize"),
                    "location": item.get("jobLocation"),
                    "connections": item.get("connections"),
                    "experiences": item.get("experiences", []),
                    "skills": item.get("skills", []),
                    "educations": item.get("educations", [])
                })
            else:
                failed.append({
                    "url": item.get("inputUrl") or item.get("linkedinUrl"),
                    "error": item.get("error", "Unknown error")
                })

        return successful, failed

    except Exception as e:
        return [], [{"url": url, "error": str(e)} for url in linkedin_urls]

# Usage
profiles, errors = enrich_contacts_from_linkedin(
    [
        "https://www.linkedin.com/in/williamhgates",
        "https://www.linkedin.com/in/satya-nadella-4b0ad62b"
    ],
    "YOUR_APIFY_TOKEN"
)

print(f"Successfully enriched: {len(profiles)}")
print(f"Failed: {len(errors)}")
```

### Rate Limits

| Plan | Daily Runs | Profiles per Run | API Access |
|------|------------|------------------|------------|
| **Free** | 10 | 10 | UI only |
| **Paid** | 10,000,000 | Unlimited | API + CLI |

### Cost Calculation

```
Cost = (Number of profiles / 1000) × $10

Examples:
- 100 profiles = $1.00
- 500 profiles = $5.00
- 1,000 profiles = $10.00
```

---

## 3. Integration in Pipeline

### Contact Enrichment Flow (Step 06)

```
Contact Discovery (Agent SDK)
    │
    │  Names + LinkedIn URLs
    │
    ▼
┌─────────────────────────────────────┐
│  Apify LinkedIn Scraper             │
│  - Full profile data                │
│  - Work history                     │
│  - Company info                     │
│  - Auto-discovered email            │
└─────────────────────────────────────┘
    │
    │  If email not found
    │
    ▼
┌─────────────────────────────────────┐
│  AnyMailFinder                      │
│  - SMTP-verified email              │
│  - Decision-maker lookup            │
└─────────────────────────────────────┘
    │
    │  Combined enriched data
    │
    ▼
v2_contacts table
```

### Combined Enrichment Function

```python
from apify_client import ApifyClient
import requests

def enrich_contact(
    linkedin_url: str,
    name: str,
    company_domain: str,
    apify_token: str,
    anymailfinder_key: str
) -> dict:
    """
    Full contact enrichment: LinkedIn + Email verification.

    Args:
        linkedin_url: LinkedIn profile URL
        name: Contact full name (fallback for email lookup)
        company_domain: Company domain (fallback for email lookup)
        apify_token: Apify API token
        anymailfinder_key: AnyMailFinder API key

    Returns:
        Enriched contact dict
    """
    result = {
        "linkedin_url": linkedin_url,
        "name": name,
        "email": None,
        "email_status": None,
        "phone": None,
        "title": None,
        "company": None,
        "headline": None,
        "experiences": [],
        "skills": [],
        "source": "linkedin"
    }

    # Step 1: LinkedIn scrape
    try:
        client = ApifyClient(apify_token)
        run = client.actor("dev_fusion/linkedin-profile-scraper").call(
            run_input={"profileUrls": [linkedin_url]},
            timeout_secs=300
        )

        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            result["name"] = item.get("fullName") or name
            result["title"] = item.get("jobTitle")
            result["company"] = item.get("companyName")
            result["headline"] = item.get("headline")
            result["phone"] = item.get("mobileNumber")
            result["experiences"] = item.get("experiences", [])
            result["skills"] = item.get("skills", [])

            # Check if LinkedIn found email
            if item.get("email"):
                result["email"] = item.get("email")
                result["email_status"] = "linkedin_discovered"
                result["source"] = "linkedin"
    except Exception as e:
        print(f"LinkedIn scrape failed: {e}")

    # Step 2: If no email, try AnyMailFinder
    if not result["email"]:
        try:
            # Try LinkedIn URL lookup first
            response = requests.post(
                "https://api.anymailfinder.com/v5.1/find-email/linkedin",
                headers={
                    "Authorization": anymailfinder_key,
                    "Content-Type": "application/json"
                },
                json={"linkedin_url": linkedin_url},
                timeout=180
            )
            data = response.json()

            if data.get("valid_email"):
                result["email"] = data["valid_email"]
                result["email_status"] = data.get("email_status")
                result["source"] = "anymailfinder_linkedin"

            # Fallback to name + domain if LinkedIn lookup failed
            elif company_domain:
                response = requests.post(
                    "https://api.anymailfinder.com/v5.1/find-email/person",
                    headers={
                        "Authorization": anymailfinder_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "full_name": result["name"],
                        "domain": company_domain
                    },
                    timeout=180
                )
                data = response.json()

                if data.get("valid_email"):
                    result["email"] = data["valid_email"]
                    result["email_status"] = data.get("email_status")
                    result["source"] = "anymailfinder_domain"

        except Exception as e:
            print(f"AnyMailFinder lookup failed: {e}")

    return result
```

---

## Environment Variables

```bash
# Add to .env
ANYMAILFINDER_API_KEY=your_anymailfinder_key
APIFY_API_KEY=your_apify_token
```

```python
import os

ANYMAILFINDER_KEY = os.environ.get("ANYMAILFINDER_API_KEY")
APIFY_TOKEN = os.environ.get("APIFY_API_KEY")
```

---

## Error Handling Best Practices

### AnyMailFinder

```python
# Handle rate limits and errors
response = requests.post(url, headers=headers, json=payload, timeout=180)

if response.status_code == 401:
    raise ValueError("Invalid API key")
elif response.status_code == 402:
    raise ValueError("Insufficient credits")
elif response.status_code != 200:
    raise Exception(f"API error: {response.status_code}")
```

### Apify

```python
from apify_client import ApifyClient
from apify_client.clients.resource_clients import ActorClientListRunsAsync

try:
    run = client.actor("dev_fusion/linkedin-profile-scraper").call(
        run_input=run_input,
        timeout_secs=3600
    )

    if run.get("status") == "FAILED":
        raise Exception(f"Actor failed: {run.get('statusMessage')}")

except Exception as e:
    # Handle timeout, network errors, etc.
    print(f"Apify error: {e}")
```

---

## Links

| Resource | URL |
|----------|-----|
| AnyMailFinder API Docs | https://anymailfinder.com/api |
| AnyMailFinder Console | https://newapp.anymailfinder.com |
| Apify Actor Store | https://apify.com/dev_fusion/linkedin-profile-scraper |
| Apify Console | https://console.apify.com |
| Apify Python Client | https://docs.apify.com/api/client/python |

---

## Related Documents

- [OPENAI_REFERENCE.md](./OPENAI_REFERENCE.md) - OpenAI API patterns
- [CLAIMS_SYSTEM.md](./CLAIMS_SYSTEM.md) - How claims work
- [06-ENRICH_CONTACTS.md](./blueprints/06-ENRICH_CONTACTS.md) - Pipeline step documentation
