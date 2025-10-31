# Quick Start Guide

## 🚀 Getting Started in 3 Steps

### 1. Ensure Docker is Running
```bash
docker --version
docker-compose --version
```

### 2. Start the Demo
```bash
./start-demo.sh
```

Or manually:
```bash
docker-compose up --build
```

### 3. Open Dashboard
Navigate to: **http://localhost:8080**

---

## 🎯 What You'll See

### Step 1: Rules Engine (30 seconds)
- Analyzes synthetic security data
- Detects impossible travel, patch drift, and open ports
- Generates `shared/alerts.json`

### Step 2: AI Agent (30 seconds)
- Reads alerts and applies mock LLM analysis
- Generates contextual summaries and recommendations
- Creates `shared/triage.json`

### Step 3: Web Dashboard (Continuous)
- Displays interactive security dashboard
- Shows all alerts with AI-generated summaries
- Allows approve/reject actions
- Runs on http://localhost:8080

---

## 📊 Expected Results

You should see approximately **10-15 security alerts**:

### Impossible Travel
- User accounts authenticating from geographically impossible locations
- Example: Alice logs in from New York, then London in 1 hour

### Patch Drift
- Systems not patched in 30+ days
- Critical severity for legacy systems like Windows XP HMI

### Open Port Anomalies
- Non-whitelisted ports accepting traffic
- Telnet (23), RDP (3389), MSSQL (1433) connections

---

## 🔄 Resetting the Demo

To start fresh:
```bash
# Stop services
docker-compose down

# Clear generated data
rm -f shared/*.json

# Restart
./start-demo.sh
```

---

## 🛠️ Troubleshooting

### Port 8080 Already in Use
Edit `docker-compose.yml` and change port mapping:
```yaml
ports:
  - "8081:8080"  # Use 8081 instead
```

### Services Won't Start
```bash
# View logs
docker-compose logs rules
docker-compose logs agent
docker-compose logs web

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

### No Alerts Shown
```bash
# Check if alerts were generated
cat shared/alerts.json

# Check if triage was created
cat shared/triage.json

# Restart web service
docker-compose restart web
```

### Permission Issues
```bash
# Fix shared folder permissions
chmod -R 777 shared/

# Restart services
docker-compose restart
```

---

## 📖 Next Steps

1. **Explore the Dashboard**: Click on alerts to see detailed AI analysis
2. **Review Evidence**: Examine technical data for each alert
3. **Make Decisions**: Use Approve/Reject buttons to provide feedback
4. **Check Feedback**: View stored decisions in `shared/feedback.json`
5. **Customize Data**: Edit files in `/data` to create new scenarios
6. **Add Rules**: Modify `rules/rules_engine.py` to add detection logic

---

## 💡 Demo Scenarios

### Scenario 1: Compromised Account
- Look for the "janitor" user impossible travel alert
- Review AI analysis explaining the credential compromise
- Approve the alert to trigger incident response

### Scenario 2: Legacy System Risk
- Find the "legacy-hmi-1" patch drift alert
- Note the CRITICAL severity for Windows XP system
- Review suggested upgrade recommendations

### Scenario 3: Insecure Protocols
- Examine open port alerts for Telnet and FTP
- See NERC CIP compliance references
- Approve remediation to close insecure ports

---

For detailed information, see [README.md](README.md)
