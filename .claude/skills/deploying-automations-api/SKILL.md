# Deploying Automations API

**Type:** Deployment Pattern Skill
**Status:** Active
**Created:** 2026-01-13

---

## When to Use This Skill

Activate when:
- User asks to "deploy the API" or "push changes to production"
- You've made changes to `api/` directory
- You've added new endpoints or routes
- User says "it's not working" after code changes
- Testing endpoints that return 404 or old responses

**Keywords:** "deploy", "push to production", "API not working", "changes not live", "restart API"

---

## The Deployment Pattern

The automations API uses **GitHub Actions for auto-deployment**:

1. **Commit & Push** → Triggers deployment
2. **GitHub Actions** → Pulls code on droplet & restarts services
3. **Test endpoint** → Verify deployment worked

**NO SSH needed!** Don't try to manually SSH into the droplet.

---

## Step-by-Step Deployment

### 1. Commit Changes

```bash
git add -A
git commit -m "Descriptive message about changes"
```

### 2. Push to GitHub (Triggers Auto-Deploy)

```bash
git push
```

**What happens automatically:**
- GitHub Actions workflow runs
- Droplet pulls latest code
- Services restart (automations-api, automations-worker)
- API is live with new changes

### 3. Verify Deployment

**Wait 30-60 seconds**, then test:

```bash
# Test health endpoint
curl https://api.columnline.dev/health

# Test specific endpoint you changed
curl https://api.columnline.dev/your-new-endpoint
```

**Expected:** Status 200 with correct response

---

## API URLs

| URL | Use Case |
|-----|----------|
| `https://api.columnline.dev` | **Production (use this!)** |
| `http://64.225.120.95:8000` | Direct IP (debugging only) |
| `https://lazy-bella-unevolutional.ngrok-free.dev` | Legacy (avoid) |

**Always use `api.columnline.dev` in Make.com and documentation.**

---

## Common Issues

### Issue: "404 Not Found" after pushing

**Cause:** Deployment hasn't completed yet
**Fix:** Wait 60 seconds, test again

### Issue: "Old response" still returned

**Cause:** Deployment succeeded but services didn't restart
**Fix:** Contact user to manually restart:
```bash
ssh root@64.225.120.95
systemctl restart automations-api
```

### Issue: "Changes not reflected"

**Checklist:**
1. ✅ Did you commit? `git status`
2. ✅ Did you push? Check GitHub repo
3. ✅ Did you wait 60 seconds?
4. ✅ Are you testing the right URL? (api.columnline.dev)

---

## GitHub Actions Workflow

**Location:** `.github/workflows/deploy.yml` (assumed)

**What it does:**
1. Triggered on push to `main` branch
2. SSHs into droplet
3. Runs: `cd /opt/automations && git pull`
4. Runs: `systemctl restart automations-api automations-worker`

---

## Manual Deployment (Fallback)

**Only use if GitHub Actions fails:**

```bash
ssh root@64.225.120.95
# Password in 1Password

cd /opt/automations
git pull
systemctl restart automations-api automations-worker
systemctl status automations-api
```

---

## Testing Endpoints in Make.com

After deployment, test in Make.com:

```
Module: HTTP > Make a Request

URL: https://api.columnline.dev/your-endpoint
Method: GET (or POST/PUT)
Headers: (usually none needed)
```

**Access response:**
- `{{1.field}}` - Direct field access
- `{{1.nested.field}}` - Nested field
- `{{1.array[0]}}` - Array element

**No JavaScript parsing needed!**

---

## Deployment Checklist

Before telling user "it's deployed":

- [ ] Changes committed (`git status` clean)
- [ ] Changes pushed (`git push` successful)
- [ ] Waited 60 seconds for auto-deploy
- [ ] Tested endpoint with curl
- [ ] Got 200 response with expected data
- [ ] Provided Make.com-ready URL to user

---

## Remember

✅ **DO:** Commit → Push → Wait → Test
❌ **DON'T:** Try to SSH manually (auto-deploy handles it)
✅ **DO:** Use `api.columnline.dev` in all examples
❌ **DON'T:** Give users raw IP or ngrok URLs

---

**Status:** This is the canonical deployment pattern for the automations API.
