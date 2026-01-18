# Columnline V2 Integration Roadmap

This document tracks features that are not fully supported in the initial v2 pipeline integration and the planned approach to address them.

## Status Key
- `deferred` - Not supported in initial release, planned for future
- `partial` - Works with limitations, see notes
- `planned` - Actively being worked on
- `complete` - Fully implemented

---

## Initial Integration (Current Scope)

**Goal:** V2 dossiers render in production app alongside V1 dossiers.

**Approach:** Writers output production-compatible JSON → Publish endpoint assembles → Write to existing `dossiers` + `contacts` tables.

---

## Feature Status

### 1. Batch System

**Status:** `partial`

**Current Behavior:**
- V1 uses batches for grouping dossiers by generation date
- App groups by `batch_date` (from `batches.created_at`)
- Batch status shows pipeline progress

**V2 Approach (Initial):**
- Create a single daily batch per client: `V2_YYYYMMDD`
- All V2 dossiers for a client on that day share the batch
- Batch status set to `complete` immediately (V2 dossiers arrive ready)

**Limitations:**
- No in-progress batch visibility (V2 dossiers appear all at once when published)
- Batch counts may be inconsistent with V1 patterns

**Future Enhancement:**
- Option A: Create batch at run start, update count as dossiers complete
- Option B: Generate batch ID in Make.com, pass through entire pipeline
- Option C: Skip batches for V2, group by `created_at` date instead

---

### 2. Supersedes / Updated Badge

**Status:** `deferred`

**Current Behavior (V1):**
- When a dossier is regenerated, new dossier gets `supersedes_dossier_id`
- Old dossier gets `superseded_by_dossier_id`
- UI shows "Updated" badge on superseded dossiers

**V2 Approach (Initial):**
- V2 reruns create new dossiers (no automatic linking)
- No "Updated" badge functionality

**Future Enhancement:**
- Add `supersedes_run_id` to V2 publish request
- Lookup previous dossier for same company + client
- Automatically set supersedes relationship
- May need deduplication by company domain

**Implementation Notes:**
```python
# Future: in publish endpoint
previous_dossier = find_previous_dossier(
    client_id=production_client_id,
    company_domain=seed_data['domain']
)
if previous_dossier:
    # Mark old as superseded
    update_dossier(previous_dossier['id'], {
        'superseded_by_dossier_id': new_dossier_id,
        'status': 'superseded'
    })
    # Mark new as superseding
    update_dossier(new_dossier_id, {
        'supersedes_dossier_id': previous_dossier['id']
    })
```

---

### 3. Client Mapping

**Status:** `partial`

**Current Behavior:**
- V1 has `clients` table with UUID primary keys
- V2 has `v2_clients` table with different schema
- Production app uses `clients.id` for RLS and relationships

**V2 Approach (Initial):**
- Add `production_client_id UUID` column to `v2_clients`
- Manually map each active client once
- Publish endpoint looks up production UUID from v2 client

**Limitations:**
- Manual setup required for each client
- Two places to maintain client config (v2_clients for pipeline, clients for app)

**Future Enhancement Options:**

**Option A: Unified Clients Table**
- Migrate v2 config fields into production `clients` table
- Add: `icp_config`, `industry_research`, `research_context` JSONB columns
- Single source of truth

**Option B: Foreign Key Relationship**
- Keep both tables
- Add proper FK constraint: `v2_clients.production_client_id REFERENCES clients(id)`
- Sync script to keep in alignment

**Option C: Slug-Based Lookup**
- Use `slug` as shared identifier across both tables
- Add `slug` column to production `clients` if not present
- Lookup by slug instead of UUID mapping

**Recommendation:** Option B for now (least invasive), migrate to Option A when v2 is stable.

---

### 4. CSV Export

**Status:** `deferred`

**Current Behavior:**
- App has CSV export for dossiers
- Export relies on specific JSONB field structure
- Used for batch download of contacts, signals, etc.

**V2 Approach (Initial):**
- V2 dossiers use same JSONB structure (after prompt updates)
- Export should work for basic fields

**Potential Issues:**
- Some fields may be named differently
- Nested structure might vary
- May need conditional handling based on `pipeline_version`

**Future Enhancement:**
```typescript
// In export logic
function getDossierForExport(dossier: Dossier) {
  if (dossier.pipeline_version === 'v2') {
    // V2-specific field mapping if needed
    return transformV2ForExport(dossier);
  }
  return dossier; // V1 unchanged
}
```

---

### 5. Release Scheduling

**Status:** `planned`

**Current Behavior:**
- `release_date` sets when dossier becomes visible
- `released_at` is set when actually released
- RLS filters by `released_at <= NOW()`

**V2 Approach:**
- Publish endpoint accepts `release_date` parameter
- If provided: set `release_date`, leave `released_at` null
- If not provided: set `released_at = NOW()` for immediate visibility

**Implementation:**
```python
@router.post("/columnline/publish/{run_id}")
async def publish_to_production(
    run_id: str,
    release_date: Optional[date] = None
):
    # ...
    dossier_data = {
        # ... other fields
        'release_date': release_date,
        'released_at': None if release_date else datetime.utcnow()
    }
```

---

### 6. Multi-List Support

**Status:** `partial`

**Current Behavior:**
- Dossiers can be on multiple lists via `dossier_lists` junction table
- Default list is "Inbox"

**V2 Approach (Initial):**
- V2 dossiers created without list assignment
- Users manually add to lists via UI

**Future Enhancement:**
- Add `default_list_id` parameter to publish endpoint
- Auto-assign to "Inbox" or specified list on creation

---

### 7. Rerun / Refresh

**Status:** `deferred`

**Current Behavior:**
- UI has "Rerun" button to regenerate specific agents
- Creates new execution with same seed

**V2 Approach (Initial):**
- Not supported - reruns must be triggered from Make.com
- Creates new dossier (see Supersedes)

**Future Enhancement:**
- Add `/columnline/rerun/{dossier_id}` endpoint
- Lookup original seed from V2 run
- Trigger new Make.com execution
- Auto-link as supersedes

---

### 8. Pipeline Version Tracking

**Status:** `planned`

**V2 Approach:**
- Add `pipeline_version TEXT DEFAULT 'v1'` to dossiers table
- V2 dossiers get `pipeline_version = 'v2'`
- Enables filtering, metrics, and conditional logic

**Benefits:**
- Debug: "Show me all V2 dossiers"
- Metrics: "V2 vs V1 success rates"
- Conditional: Different export/render logic if needed

---

## Implementation Priority

### Phase 1: MVP (Current)
1. Schema updates (production_client_id, pipeline_version)
2. Writer prompt updates for production-compatible JSON
3. Publish endpoint with basic assembly
4. Single daily batch per client
5. Manual client mapping

### Phase 2: Polish
1. Release scheduling support
2. CSV export compatibility
3. Default list assignment
4. Improved batch handling

### Phase 3: Parity
1. Supersedes / Updated badge
2. Rerun capability from UI
3. Unified clients table
4. Full batch lifecycle tracking

---

## Migration Considerations

### Existing V1 Dossiers
- ~734 dossiers remain unchanged
- `pipeline_version` defaults to 'v1'
- No migration needed

### New V2 Dossiers
- Created via publish endpoint
- `pipeline_version = 'v2'`
- Use production client UUIDs
- Same contacts table structure

### Coexistence
- Both pipeline versions render in same UI
- Transform layer handles both formats
- Gradual migration possible (keep V1 for existing clients, V2 for new)

---

## Questions / Open Items

1. **Batch ID Strategy:** Should V2 batches be created:
   - Per day per client? (current plan)
   - Per run?
   - Not at all (use created_at for grouping)?

2. **Supersedes Trigger:** Should supersedes be:
   - Automatic (by company domain match)?
   - Manual (pass previous dossier ID)?
   - Opt-in via publish parameter?

3. **Client Sync:** If we update ICP config in v2_clients, should it:
   - Auto-sync to production clients?
   - Remain separate (v2 for pipeline only)?

4. **Error Handling:** If publish fails partially (dossier created, contacts fail):
   - Rollback entire transaction?
   - Mark dossier as `error` status?
   - Retry endpoint?

---

*Last updated: 2026-01-15*
