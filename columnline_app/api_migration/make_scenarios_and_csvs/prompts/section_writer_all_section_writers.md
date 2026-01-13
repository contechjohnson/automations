# Section Writer: ALL SECTION WRITERS

**Sections Produced:** SOURCES_AND_REFERENCES

---

## Prompt Template

// Pseudocode for sources aggregation
const sources = [];
const seenUrls = new Set();

for (const section of Object.values(section_routing)) {
  for (const claimId of section.claim_ids) {
    const claim = claims.find(c => c.claim_id === claimId);
    if (claim.source_url && !seenUrls.has(claim.source_url)) {
      sources.push({
        url: claim.source_url,
        name: claim.source_name,
        used_in: [section.name]
      });
      seenUrls.add(claim.source_url);
    }
  }
}

return { sources_and_references: sources };

---

## Notes from Author

<!-- Add your notes here about this section writer -->

---

## Variables Used

<!-- Likely: merged_claims, dossier_plan, context_pack, client_config -->

## Variables Produced

SOURCES_AND_REFERENCES

---

## Target Column

<!-- Which of the 5 JSONB columns does this populate? -->
- find_lead
- enrich_lead
- copy
- insight
- media

---

## Usage Context

This section writer is part of the parallel section generation step (10_WRITER_*). It receives merged claims and produces structured JSON for the dossier assembly.
