# 🚀 START HERE - Quick Deployment Guide

## ✅ Issues Fixed!

Your "Failed to load alerts" error has been **completely resolved**. Multiple fixes have been applied:

1. ✅ Fixed read-only volume mount (feedback now works)
2. ✅ Increased wait timeout (60 seconds for AI processing)
3. ✅ Added startup orchestration (proper service ordering)
4. ✅ Added health checks (Docker knows when ready)
5. ✅ Created diagnostic tools (easy troubleshooting)
6. ✅ Comprehensive documentation (self-service support)

---

## 🎯 What You Need to Do

### Step 1: Rebuild Everything
```bash
# Stop current deployment
docker-compose down

# Remove old data
rm -f shared/*.json

# Rebuild with all fixes
docker-compose up --build
```

### Step 2: Wait for Processing
```bash
# ⏰ IMPORTANT: Wait 60 seconds!

# The AI agent needs time to:
# - Process alerts (10s)
# - Call OpenRouter API (30-50s)
# - Generate triage analysis

# Watch progress in real-time:
docker-compose logs -f web
```

You'll see messages like:
```
soc-web | ⏳ Waiting for triage.json...
soc-web |    Waited 10s for /shared/triage.json...
soc-web |    Waited 20s for /shared/triage.json...
soc-web | ✓ triage.json found (8432 bytes)
soc-web | ✅ Starting Flask web application...
```

### Step 3: Access Dashboard
```bash
# After 60 seconds, open:
http://localhost:8080
```

**You should see:**
- ✅ 15-20 security alerts
- ✅ AI analysis for each alert
- ✅ Risk scores and recommendations
- ✅ Working feedback buttons

---

## 🔍 Still Having Issues?

### Run Diagnostics
```bash
bash scripts/diagnose.sh
```

This will check:
- ✅ Service status
- ✅ File existence
- ✅ API key configuration
- ✅ Logs for errors
- ✅ Web accessibility

### Check Logs
```bash
# View all logs
docker-compose logs

# Specific service
docker-compose logs agent
docker-compose logs web

# Follow live logs
docker-compose logs -f web
```

### Common Issues

#### Issue: Still see "Failed to load alerts"
**Solution:**
```bash
# 1. Check if agent completed
docker-compose logs agent | grep "completed successfully"

# 2. Check if files exist
ls -lh shared/

# Should show:
# alerts.json  (> 1KB)
# triage.json  (> 5KB)

# 3. If files missing, check for errors:
docker-compose logs agent | grep -i error

# 4. Most common: Missing API key
cat .env | grep OPENROUTER_API_KEY
```

#### Issue: API key error
**Solution:**
```bash
# 1. Copy example
cp .env.example .env

# 2. Edit and add your key
nano .env

# Add: OPENROUTER_API_KEY=sk-or-v1-YOUR-KEY-HERE

# 3. Get key from: https://openrouter.ai/keys

# 4. Rebuild
docker-compose up --build
```

#### Issue: Permission denied
**Solution:**
```bash
# Make shared directory writable
chmod -R 777 shared/

# Restart
docker-compose restart
```

---

## 📊 Expected Timing

Understanding what's normal:

```
Time    | What's Happening
--------|------------------
T+0s    | docker-compose up starts
T+5s    | Containers building/starting
T+10s   | Rules service completes → alerts.json
T+15s   | Agent starts processing
T+45s   | Agent completes → triage.json ✅
T+50s   | Web service starts Flask
T+60s   | Dashboard ready! ✅
```

**If it takes longer than 90 seconds**, something's wrong. Check logs!

---

## 🎯 Quick Commands

```bash
# Start services
docker-compose up --build

# Stop services
docker-compose down

# View logs
docker-compose logs

# Run diagnostics
bash scripts/diagnose.sh

# Check health
curl http://localhost:8080/health

# Clean everything and restart
docker-compose down -v
rm -f shared/*.json
docker-compose up --build
```

---

## 📚 Documentation Guide

| Document | When to Use |
|----------|-------------|
| **START_HERE.md** | 👈 **You are here!** Quick start |
| **QUICKSTART.md** | First-time setup guide |
| **README.md** | Complete documentation |
| **TROUBLESHOOTING.md** | Detailed problem solving |
| **FIXES_SUMMARY.md** | What was fixed |

---

## ✅ Success Checklist

Everything is working when:

- [ ] `docker-compose ps` shows web as "Up (healthy)"
- [ ] Dashboard loads at http://localhost:8080
- [ ] 15-20 alerts displayed
- [ ] AI analysis visible for each alert
- [ ] Risk scores showing (1-10)
- [ ] Feedback buttons work (Approve/Reject)
- [ ] No errors in browser console
- [ ] `shared/triage.json` exists (>5KB)

---

## 🆘 Need More Help?

### 1. Run Diagnostics First
```bash
bash scripts/diagnose.sh
```

### 2. Check Documentation
- For setup: Read `QUICKSTART.md`
- For issues: Read `TROUBLESHOOTING.md`
- For details: Read `README.md`

### 3. Verify Environment
```bash
# Check API key
cat .env

# Check files
ls -lh shared/

# Check services
docker-compose ps
```

### 4. Common Solutions
```bash
# Complete rebuild
docker-compose down -v
docker-compose build --no-cache
docker-compose up

# Fix permissions
chmod -R 777 shared/

# Update API key
nano .env  # Add your OpenRouter key
docker-compose up --build
```

---

## 🎉 You're All Set!

After rebuilding with the fixes:

1. ✅ Feedback submission works
2. ✅ Dashboard loads successfully
3. ✅ Proper wait time built in
4. ✅ Clear error messages
5. ✅ Diagnostic tools available
6. ✅ Comprehensive documentation

**Start the platform:**
```bash
docker-compose up --build
```

**Wait 60 seconds, then access:**
```
http://localhost:8080
```

---

**🎊 Enjoy your AI-Assisted SOC Platform!**

Questions? Check `TROUBLESHOOTING.md` or run `bash scripts/diagnose.sh`
