# Automations Project Instructions

You help build and manage automations (scrapers, research workers, enrichment pipelines) that run on a DigitalOcean droplet.

## Key Files
- `SKILL.md` - Full reference guide with patterns and examples
- `workers/` - Where worker code lives
- `database/schema.sql` - Supabase registry schema

## Quick Reference

### Scraper Patterns
| Pattern | Use When | Template |
|---------|----------|----------|
| ArcGIS | URL has `FeatureServer` or `arcgis` | `permits.py` |
| State Portal | HTML tables, state gov sites | `portals.py` |
| Public API | Has documented API, returns JSON | `apis.py` |
| Browser | JavaScript-heavy, needs login | `browser.py` |
| Google Maps | Business discovery by location | `maps.py` |

### Naming Convention
`{geography}-{source-type}`
- `va-loudoun-permits`
- `ferc-pjm-interconnections`
- `gmaps-ia-behavioral-health`

### Creating New Automation
1. Identify which pattern applies
2. Check if template exists in `workers/scrapers/`
3. If template exists: just add config to Supabase registry
4. If new pattern: create worker file, then register
5. Test via API: `POST /run {"slug": "..."}`

### Registry Queries (Supabase)
```sql
-- By state
SELECT * FROM automations WHERE geography->>'state' = 'VA';

-- By category  
SELECT * FROM automations WHERE category = 'permits';

-- Failed ones
SELECT * FROM automations WHERE last_run_status = 'failed';
```

### Deployment
```bash
ssh root@DROPLET_IP
cd /opt/automations && git pull
systemctl restart automations-api automations-worker
```

## When User Asks To...

**"Build a scraper for X County permits"**
→ Find their GIS portal, identify pattern, get endpoint, add to registry, test

**"This scraper is broken"**
→ Check dashboard (:9181), find error, usually endpoint changed

**"What do we have for Virginia?"**
→ Query registry by state

**"Add new client"**
→ INSERT into clients table with their ICP info

Always read `SKILL.md` for detailed patterns and config schemas.
