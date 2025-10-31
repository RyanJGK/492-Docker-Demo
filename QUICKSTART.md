# Quick Start Guide

Get the AI-Assisted SOC Demo Platform running in under 5 minutes!

## Prerequisites Check

```bash
# Verify Docker is installed
docker --version
docker-compose --version

# Should show Docker version 20.10+ and Compose version 2.0+
```

## Step 1: Validate Setup

Run the validation script to ensure everything is in place:

```bash
python3 validate.py
```

You should see: `✓ ALL CHECKS PASSED!`

## Step 2: Configure API Key

```bash
# Copy the example environment file
cp .env.example .env

# Edit and add your OpenRouter API key
nano .env
```

Update this line:
```env
OPENROUTER_API_KEY=sk-or-v1-YOUR-ACTUAL-KEY-HERE
```

**Get your API key:** https://openrouter.ai/keys

## Step 3: Run the Platform

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

**⏰ Important - Wait Time:**
- **First run** takes 2-3 minutes to build Docker images
- **Data processing** takes 30-60 seconds (AI calls are slow)
- **Wait 60 seconds** after services start before accessing dashboard
- Watch logs: `docker-compose logs -f web` to see progress

**What's happening:**
1. Rules engine analyzes data → creates `alerts.json` (~10s)
2. AI agent processes alerts with OpenRouter → creates `triage.json` (~30-60s)
3. Web UI loads and displays triaged alerts ✅

## Step 4: Access Dashboard

**After waiting 60 seconds**, open your browser:
```
http://localhost:8080
```

You should see security alerts with AI analysis!

**If you see "Failed to load alerts":**
- Wait another 30 seconds (AI processing takes time)
- Check logs: `docker-compose logs agent`
- Run diagnostics: `bash scripts/diagnose.sh`
- See `TROUBLESHOOTING.md` for detailed help

## Step 5: Test Feedback Loop

1. **Review an alert** on the dashboard
2. **Enter your reasoning** in the text area
3. **Click Approve or Reject**
4. **Restart agent** to see feedback applied:
   ```bash
   docker-compose restart agent
   ```
5. **Refresh dashboard** - alerts now show "Feedback Adjusted" badge

## Troubleshooting

### No alerts showing?
```bash
# Check all services are running
docker-compose ps

# View logs
docker-compose logs

# Wait 60 seconds after startup for AI analysis to complete
```

### API key error?
```bash
# Verify .env file
cat .env

# Make sure key starts with: sk-or-v1-
```

### Port already in use?
```bash
# Edit docker-compose.yml, change port:
ports:
  - "8081:8080"  # Use 8081 instead
```

## Stopping the Platform

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## What's Happening Behind the Scenes?

1. **Rules Engine** (`rules/detect.py`):
   - Reads CSV/JSON files from `data/`
   - Detects: impossible travel, patch drift, open ports, anomalies
   - Writes alerts to `shared/alerts.json`

2. **AI Agent** (`agent/agent.py`):
   - Reads `shared/alerts.json`
   - Reads `shared/feedback.json` for learning
   - Calls OpenRouter API for analysis
   - Writes triage to `shared/triage.json`

3. **Web UI** (`web/app.py`):
   - Reads `shared/triage.json`
   - Displays dashboard at http://localhost:8080
   - Collects feedback to `shared/feedback.json`

4. **Feedback Loop**:
   - Analyst feedback influences future AI analysis
   - Confidence scores adjust based on approval patterns
   - System learns which alerts are true positives

## Example Alerts You'll See

- **Impossible Travel**: User in Chicago then Moscow in 2 hours
- **Patch Drift**: SCADA gateway not patched in 78 days
- **Open Ports**: Unauthorized port 8080 on production system
- **Splunk Anomalies**: Brute force, privilege escalation, mimikatz

## Next Steps

- Explore the alerts and AI analysis
- Submit feedback on multiple alerts
- Restart agent to see learning in action
- Review `README.md` for detailed documentation
- Customize detection rules in `rules/detect.py`
- Add your own synthetic data to `data/`

## Need Help?

See full documentation in `README.md`, especially:
- Architecture diagram
- API endpoints
- Security best practices
- Deployment guides

---

**Ready to secure critical infrastructure with AI? Let's go! 🛡️⚡**
