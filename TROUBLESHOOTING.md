# Troubleshooting Guide - AI-Assisted SOC Platform

## 🚨 Common Issues and Solutions

### Issue 1: "Failed to load alerts" Error

**Symptoms:**
- Dashboard loads but shows "Failed to load alerts" message
- Browser console shows fetch errors
- Spinner keeps loading indefinitely

**Root Causes:**

#### A) Data Pipeline Still Processing (MOST COMMON)
The agent service takes **30-60 seconds** to complete AI analysis.

**Solution:**
```bash
# 1. Wait 60 seconds after starting services
# 2. Check if services completed successfully
docker-compose logs rules
docker-compose logs agent

# 3. Look for these success messages:
#    rules: "Detection engine completed successfully"
#    agent: "AI agent completed successfully"

# 4. If agent is still running, wait more
# 5. Refresh the dashboard
```

#### B) Missing or Invalid API Key
Agent can't connect to OpenRouter API.

**Solution:**
```bash
# 1. Check .env file exists
cat .env

# 2. Verify API key is set correctly
grep OPENROUTER_API_KEY .env

# Should see: OPENROUTER_API_KEY=sk-or-v1-...
# NOT: OPENROUTER_API_KEY=your_openrouter_api_key_here

# 3. If wrong, edit .env
nano .env

# 4. Rebuild and restart
docker-compose down
docker-compose up --build
```

#### C) Services Exited With Errors

**Solution:**
```bash
# Check exit codes and errors
docker-compose ps

# View detailed logs
docker-compose logs rules --tail=50
docker-compose logs agent --tail=50

# Look for ERROR or CRITICAL messages
```

#### D) File Permission Issues

**Solution:**
```bash
# Check shared directory permissions
ls -la shared/

# Make writable (for testing)
chmod -R 777 shared/

# Restart services
docker-compose restart
```

---

### Issue 2: Services Exit Immediately

**Symptoms:**
- `docker-compose ps` shows rules/agent containers as "Exited (0)"
- Services appear to stop right after starting

**This is NORMAL behavior!**

The rules and agent services are designed to:
1. Run once
2. Process data
3. Create output files
4. Exit cleanly

**Verification:**
```bash
# Check if files were created
ls -lh shared/

# You should see:
# alerts.json  (from rules service)
# triage.json  (from agent service)
# feedback.json

# Check logs to verify success
docker-compose logs rules | grep "completed successfully"
docker-compose logs agent | grep "completed successfully"
```

**If files are missing:**
```bash
# Re-run just that service
docker-compose up rules   # for alerts.json
docker-compose up agent   # for triage.json
```

---

### Issue 3: Agent Service Fails

**Symptoms:**
- `triage.json` not created
- Agent logs show errors
- Fallback analysis used

**Common Causes:**

#### A) API Key Issues
```bash
# Check agent logs
docker-compose logs agent | grep -i "api\|key\|error"

# Look for:
# "OPENROUTER_API_KEY environment variable not set"
# "LLM API call failed"
# "401 Unauthorized"
```

**Solution:** Fix API key in .env and rebuild

#### B) Network/Connectivity Issues
```bash
# Check if container can reach internet
docker-compose exec web curl -I https://openrouter.ai

# Should return HTTP 200
```

**Solution:** Check firewall, proxy settings

#### C) API Rate Limits
```bash
# Look for 429 errors in logs
docker-compose logs agent | grep "429\|rate limit"
```

**Solution:** Wait and retry, or check OpenRouter account limits

---

### Issue 4: Port 8080 Already in Use

**Symptoms:**
- Error: "bind: address already in use"
- Can't start web service

**Solution:**
```bash
# Find what's using port 8080
lsof -i :8080   # macOS/Linux
netstat -ano | findstr :8080  # Windows

# Option 1: Stop the other service
# Option 2: Use a different port
```

Edit `docker-compose.yml`:
```yaml
web:
  ports:
    - "8081:8080"  # Use 8081 instead
```

Then access: http://localhost:8081

---

### Issue 5: Empty or Invalid JSON Files

**Symptoms:**
- Dashboard loads but no alerts show
- Logs show "File is empty" warnings

**Diagnosis:**
```bash
# Check file sizes
ls -lh shared/

# Files should be:
# alerts.json:  > 1KB
# triage.json:  > 5KB

# View contents
cat shared/alerts.json | jq .    # Pretty print
cat shared/triage.json | jq .
```

**Solution:**
```bash
# Delete bad files
rm shared/alerts.json shared/triage.json

# Re-run services
docker-compose up rules
docker-compose up agent
```

---

### Issue 6: Dashboard Loads but Shows No Data

**Symptoms:**
- No errors in console
- Empty alert list
- Statistics show "0" for everything

**Diagnosis:**
```bash
# Check API endpoints directly
curl http://localhost:8080/api/alerts
curl http://localhost:8080/api/stats

# Should return JSON with data
```

**Solution:**
```bash
# Check if triage.json has data
cat shared/triage.json | jq '. | length'

# Should show number of alerts (e.g., 15-20)

# If 0, regenerate:
docker-compose up agent --force-recreate
```

---

### Issue 7: Feedback Submission Fails

**Symptoms:**
- Clicking Approve/Reject shows error
- Console shows 500 error
- Logs show permission denied

**Solution:**
```bash
# Check feedback.json permissions
ls -la shared/feedback.json

# Should be writable
# If not:
chmod 666 shared/feedback.json

# Verify volume mount is NOT read-only
grep "shared:/shared:ro" docker-compose.yml

# Should NOT have :ro for web service
```

---

## 🔧 Diagnostic Tools

### Run Automated Diagnostics
```bash
# Run the diagnostic script
bash scripts/diagnose.sh

# This will check:
# - Service status
# - File existence and sizes
# - Environment variables
# - Service logs
# - Web accessibility
```

### Manual Diagnostics

#### Check Service Status
```bash
docker-compose ps

# Healthy status:
# rules:  Exited (0)    ← Normal!
# agent:  Exited (0)    ← Normal!
# web:    Up (healthy)  ← Should stay running
```

#### View Logs
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs web
docker-compose logs agent --follow

# Last N lines
docker-compose logs rules --tail=20
```

#### Check Files
```bash
# List with sizes
ls -lh shared/

# Preview content
head -n 20 shared/alerts.json
head -n 20 shared/triage.json

# Count alerts
cat shared/triage.json | jq '. | length'
```

#### Test API Endpoints
```bash
# Health check
curl http://localhost:8080/health

# Get alerts
curl http://localhost:8080/api/alerts | jq .

# Get stats
curl http://localhost:8080/api/stats | jq .
```

#### Check Network
```bash
# Test from inside container
docker-compose exec web curl -I http://localhost:8080/health

# Check DNS resolution
docker-compose exec web curl -I https://openrouter.ai
```

---

## 🚀 Quick Fixes

### Complete Reset
```bash
# Nuclear option - start fresh
docker-compose down -v
rm -rf shared/*.json
docker-compose up --build
```

### Rebuild Single Service
```bash
# Rebuild just the web service
docker-compose up --build web

# Rebuild everything
docker-compose build --no-cache
docker-compose up
```

### Clear Docker Cache
```bash
# Remove all unused images/containers
docker system prune -a

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up
```

---

## 📊 Expected Timing

Understanding normal operation timing:

```
T+0s:   docker-compose up
T+5s:   All containers start
T+10s:  rules service completes → alerts.json created
T+15s:  agent service starts processing
T+45s:  agent completes AI analysis → triage.json created
T+50s:  web service reads triage.json
T+55s:  Dashboard displays alerts! ✅
```

**If it takes longer than 2 minutes**, check logs for errors.

---

## 🆘 Still Having Issues?

### Collect Debug Information
```bash
# Create a debug bundle
mkdir debug-info
docker-compose ps > debug-info/services.txt
docker-compose logs > debug-info/all-logs.txt
ls -lR shared/ > debug-info/files.txt
cat .env.example > debug-info/env-example.txt
cp shared/*.json debug-info/ 2>/dev/null || true

# Create tarball
tar -czf soc-debug-$(date +%Y%m%d-%H%M%S).tar.gz debug-info/
```

### Check Documentation
- `README.md` - Full setup guide
- `QUICKSTART.md` - Fast start guide
- `ERRORS_FIXED.md` - Known issues and fixes
- `BUGFIX_REPORT.md` - Recent bug fixes

### Common Log Messages Explained

| Message | Meaning | Action |
|---------|---------|--------|
| "Waiting for {file}..." | Normal - waiting for upstream service | Wait |
| "File not found after 60 seconds" | Upstream service failed or slow | Check logs |
| "Using fallback analysis" | AI API unavailable | Check API key |
| "Detection engine completed" | ✅ Rules service success | None |
| "AI agent completed" | ✅ Agent service success | None |
| "Permission denied" | File/volume permissions issue | Fix permissions |
| "Connection refused" | Service not ready yet | Wait or check network |

---

## 💡 Pro Tips

1. **First time setup?** Wait 90 seconds before expecting data
2. **Rebuilding?** Use `--build` flag: `docker-compose up --build`
3. **Testing changes?** Restart specific service: `docker-compose restart agent`
4. **Clear everything?** `docker-compose down -v && rm shared/*.json`
5. **Check health?** `curl localhost:8080/health` or run `scripts/diagnose.sh`

---

## ✅ Success Indicators

You know everything is working when:

- ✅ `docker-compose ps` shows web as "Up (healthy)"
- ✅ Dashboard loads at http://localhost:8080
- ✅ Multiple alerts display with AI analysis
- ✅ Statistics show correct counts
- ✅ Feedback submission works (no errors)
- ✅ `shared/triage.json` has content (>5KB)
- ✅ Browser console has no errors

---

**Last Updated:** 2024-10-31  
**Version:** 1.1 (Post-orchestration fix)
