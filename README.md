# AI-Assisted SOC Demo Platform for Energy Sector

A comprehensive demonstration platform for AI-powered Security Operations Center (SOC) capabilities specifically designed for energy sector critical infrastructure. This system uses AI to analyze security alerts with human-in-the-loop feedback to continuously improve detection accuracy.

## 🎯 Overview

This platform demonstrates modern SOC operations with:
- **Automated threat detection** using rule-based engines
- **AI-powered alert triage** using OpenRouter LLM API
- **Human feedback loop** to improve AI analysis over time
- **Energy sector context** for SCADA, EMS, and critical infrastructure
- **Docker-based deployment** for easy local testing and production deployment

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Synthetic │      │   Detection  │      │  AI Agent   │
│    Data     │─────▶│    Rules     │─────▶│  Service    │
│  (CSV/JSON) │      │   Engine     │      │ (OpenRouter)│
└─────────────┘      └──────────────┘      └─────────────┘
                            │                      │
                            ▼                      ▼
                     ┌─────────────┐        ┌─────────────┐
                     │   alerts    │        │   triage    │
                     │    .json    │        │    .json    │
                     └─────────────┘        └─────────────┘
                                                   │
                                                   ▼
                                            ┌─────────────┐
                                            │   Flask     │
                                            │   Web UI    │◀──┐
                                            └─────────────┘   │
                                                   │          │
                                                   ▼          │
                                            ┌─────────────┐   │
                                            │  feedback   │   │
                                            │    .json    │───┘
                                            └─────────────┘
                                              (learning loop)
```

**Workflow:**
1. **Detection Rules Engine** analyzes synthetic data (auth logs, host inventory, firewall logs, Splunk events)
2. Generates security alerts (impossible travel, patch drift, open ports, anomalies)
3. **AI Agent** reads alerts and previous feedback, calls OpenRouter API for analysis
4. Generates risk scores, threat analysis, and remediation recommendations
5. **Web UI** displays alerts to security analysts
6. Analysts approve/reject alerts with reasoning
7. Feedback is stored and used to adjust future AI analysis confidence

## 📋 Prerequisites

- **Docker** and **Docker Compose** (v2.0+)
- **OpenRouter API Key** - Get yours at [https://openrouter.ai/](https://openrouter.ai/)
- **2GB RAM** minimum for running all services
- **Modern web browser** (Chrome, Firefox, Safari, Edge)

## 🚀 Local Setup

### Step 0: Validate Setup (Recommended)

Before starting, run the validation script to ensure all files are in place:

```bash
python3 validate.py
```

This will check:
- Directory structure
- All data files (CSV/JSON)
- Python application files
- Dockerfiles and requirements
- Configuration files
- Documentation

You should see: `✓ ALL CHECKS PASSED!`

### Step 1: Clone and Navigate

```bash
cd /path/to/ai-soc-demo
```

### Step 2: Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your OpenRouter API key
nano .env  # or use your preferred editor
```

Update the `.env` file:
```env
OPENROUTER_API_KEY=sk-or-v1-your-actual-api-key-here
```

**⚠️ SECURITY NOTE:** Never commit your `.env` file to version control. The `.gitignore` file is configured to exclude it.

### Step 3: Build and Run

```bash
# Build all Docker images and start services
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

### Step 4: Access the Dashboard

Open your browser and navigate to:
```
http://localhost:8080
```

You should see the SOC dashboard with security alerts!

### Step 5: Test the Feedback Loop

1. Review an alert on the dashboard
2. Enter your analysis in the feedback text area
3. Click "Approve" or "Reject"
4. Restart the services to see feedback influence new analysis:
   ```bash
   docker-compose restart agent
   ```

## 📊 Data Sources

### Synthetic Data Files (in `data/` directory)

1. **auth_events.csv** - User authentication logs with geolocation
   - Realistic users: Security analysts, plant managers, field engineers, executives
   - Locations: Chicago, Houston, Seattle, NYC, Moscow, Mumbai, Dubai, etc.
   - Includes impossible travel scenarios

2. **host_inventory.csv** - Asset inventory with patch status
   - SCADA gateways, EMS historians, PLCs, RTUs
   - Active Directory, Splunk, backup servers
   - Firewalls, VPN concentrators, HMI workstations

3. **firewall_logs.csv** - Network traffic logs
   - Authorized and unauthorized ports
   - Source/destination IPs and ports
   - Allow/block actions

4. **vuln_scan.json** - Vulnerability scan results
   - CVE identifiers and CVSS scores
   - Exploitability status
   - Patch availability

5. **splunk_events.json** - SIEM correlation events
   - Failed login attempts (brute force)
   - Privilege escalation
   - Unusual process execution
   - Data exfiltration indicators
   - Ransomware indicators

## 🔍 Detection Rules

The detection engine (`rules/detect.py`) implements four rule types:

### 1. Impossible Travel Detection
- Calculates geographic distance between consecutive logins
- Computes travel speed in mph
- Flags if speed > 500 mph
- **Critical** if > 1000 mph, **High** if > 500 mph

### 2. Patch Drift Detection
- Checks days since last patch
- **Critical** if > 60 days
- **High** if > 30 days
- Prioritizes critical infrastructure systems

### 3. Open Port Detection
- Compares against whitelist: [22, 80, 443, 3389]
- Flags unauthorized ports
- **High** severity for risky ports (telnet, VNC, etc.)
- **Medium** for other unauthorized ports

### 4. Splunk Anomaly Correlation
- Failed login thresholds (5+ in 10 minutes)
- Privilege escalation detection
- Unusual process execution (credential dumping tools)
- Data exfiltration patterns
- Configuration changes outside maintenance windows

## 🤖 AI Agent

The AI agent (`agent/agent.py`) uses OpenRouter's API to provide:

### Analysis Components
- **Risk Score (1-10)** with detailed justification
- **Threat Analysis** in energy sector context
- **Operational Impact** assessment
- **Remediation Steps** (2-3 actionable items)
- **Confidence Score** adjusted by historical feedback

### Feedback Learning
The agent incorporates analyst feedback to improve over time:
- Tracks approval/rejection patterns by alert type
- Adjusts confidence scores based on historical accuracy
- Summarizes recent feedback for context
- Marks alerts as "Feedback Adjusted" when applicable

### System Prompt
Specialized for energy sector:
- Prioritizes safety and availability
- Considers SCADA/ICS operational constraints
- Understands critical infrastructure context
- Balances security with operational continuity

## 🌐 Web UI Features

### Dashboard (`web/app.py` + `templates/dashboard.html`)

**Statistics Cards:**
- Critical, High, Medium alert counts
- Average risk score across all alerts

**Alert Display:**
- Color-coded severity badges
- Risk scores and confidence indicators
- Collapsible evidence and remediation sections
- Feedback-adjusted indicators

**Filtering & Search:**
- Filter by severity (Critical, High, Medium, Low)
- Full-text search across all alert fields
- Real-time updates

**Feedback System:**
- Required reason text for all actions
- Approve/Reject buttons
- AJAX submission (no page reload)
- Toast notifications for user actions

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main dashboard UI |
| `/api/alerts` | GET | Get all triaged alerts (JSON) |
| `/api/feedback` | GET | Get feedback history (JSON) |
| `/feedback` | POST | Submit analyst feedback |
| `/api/stats` | GET | Get alert and feedback statistics |
| `/health` | GET | Health check endpoint |

## 🔒 Security Best Practices

### ✅ Implemented Security Features

1. **Environment Variables Only**
   - API keys loaded from environment
   - No hardcoded secrets in code
   - `.env` excluded from git via `.gitignore`

2. **API Key Protection**
   - Never exposed in frontend
   - Not logged in error messages
   - Not included in API responses

3. **Error Handling**
   - Sanitized error messages
   - Structured logging
   - Fallback analysis when LLM unavailable

4. **Docker Security**
   - Read-only volume mounts where appropriate
   - Non-root users (can be added if needed)
   - Network isolation via Docker networks

### ⚠️ For Production Deployment

- Use secrets management (AWS Secrets Manager, HashiCorp Vault)
- Enable HTTPS/TLS
- Implement authentication (OAuth, SAML)
- Add rate limiting
- Enable audit logging
- Use dedicated database instead of JSON files
- Implement backup strategy

## 🌍 Web Deployment

### Deploying to Render

1. **Create a new Web Service** on [render.com](https://render.com)
2. **Connect your GitHub repository**
3. **Configure build settings:**
   - Build Command: `docker-compose -f docker-compose.prod.yml build`
   - Start Command: `docker-compose -f docker-compose.prod.yml up`
4. **Add environment variables:**
   - `OPENROUTER_API_KEY`: Your API key
5. **Deploy!**

### Deploying to Railway

1. **Create a new project** on [railway.app](https://railway.app)
2. **Connect your repository**
3. **Add environment variable:**
   - `OPENROUTER_API_KEY`: Your API key
4. Railway auto-detects Docker Compose
5. **Deploy!**

### Deploying to Fly.io

1. **Install flyctl:** `brew install flyctl` (macOS) or see [fly.io/docs](https://fly.io/docs/getting-started/installing-flyctl/)
2. **Login:** `flyctl auth login`
3. **Launch app:** `flyctl launch`
4. **Set secret:** `flyctl secrets set OPENROUTER_API_KEY=your-key`
5. **Deploy:** `flyctl deploy`

## 🧪 Testing Checklist

- [x] Synthetic data generated with realistic energy sector scenarios
- [x] All 4 detection rules implemented and tested
- [x] AI agent successfully calls OpenRouter API
- [x] Feedback influences subsequent AI analysis
- [x] Web UI displays formatted alerts
- [x] AJAX approve/reject functionality works
- [x] Feedback persists to feedback.json
- [x] Docker builds complete without errors
- [x] `docker-compose up` runs full stack
- [x] `.env.example` provided, `.gitignore` excludes `.env`
- [x] No hardcoded API keys in codebase
- [x] Logs are sanitized (no secrets exposed)
- [x] Mobile responsive design (Bootstrap 5)

## 📝 Example Workflow

### Initial Run

```bash
# Start the stack
docker-compose up

# Output shows:
# 1. Rules engine processing data
# 2. Alerts generated (impossible travel, patch drift, etc.)
# 3. AI agent analyzing alerts with OpenRouter
# 4. Triage results saved
# 5. Web UI ready at http://localhost:8080
```

### Using the Dashboard

1. **View alerts** sorted by risk score
2. **Expand evidence** to see technical details
3. **Review AI analysis** including threat assessment and operational impact
4. **Check remediation steps** provided by AI
5. **Submit feedback:**
   - "Confirmed with Alice - account disabled. Updating travel policy."
   - Click "Approve"
6. **System learns** from your feedback

### Feedback Learning Example

**First Run:**
- Alert: "Impossible travel for frank.patel@energycorp.com (Mumbai → Austin)"
- AI Confidence: 70%
- Analyst: Approves (contractor traveling for work)

**Second Run (after restart):**
- Similar alert for same contractor
- AI Confidence: 85% (adjusted based on previous approval)
- Marked as "Feedback Adjusted"
- Lower risk score or different recommendation

## 🛠️ Troubleshooting

### Service won't start

**Issue:** Container fails to start
```bash
# Check logs
docker-compose logs rules
docker-compose logs agent
docker-compose logs web

# Rebuild without cache
docker-compose build --no-cache
docker-compose up
```

### API key error

**Issue:** "OPENROUTER_API_KEY environment variable not set"
```bash
# Verify .env file exists and contains key
cat .env

# Ensure docker-compose picks up .env
docker-compose config
```

### No alerts displayed

**Issue:** Dashboard shows "Loading alerts..." forever

**Solutions:**
1. Check if all services started:
   ```bash
   docker-compose ps
   ```
2. Verify alerts.json was created:
   ```bash
   ls -la shared/
   ```
3. Wait 30-60 seconds for agent to complete AI analysis
4. Check browser console for JavaScript errors

### LLM API failures

**Issue:** AI analysis using fallback (not calling OpenRouter)

**Solutions:**
1. Verify API key is correct
2. Check OpenRouter API status
3. Ensure internet connectivity from Docker containers
4. Review agent logs:
   ```bash
   docker-compose logs agent
   ```

### Port already in use

**Issue:** "Bind for 0.0.0.0:8080 failed: port is already allocated"

**Solutions:**
```bash
# Find process using port 8080
lsof -i :8080  # macOS/Linux
netstat -ano | findstr :8080  # Windows

# Kill the process or change port in docker-compose.yml
ports:
  - "8081:8080"  # Use 8081 on host instead
```

## 🎓 Educational Use

This platform is designed for:
- **Cybersecurity training** - Learn SOC operations and AI-assisted analysis
- **Demo presentations** - Showcase modern security tools
- **Research projects** - Experiment with AI/ML in cybersecurity
- **Job interviews** - Portfolio project demonstrating full-stack + security skills

**Not intended for:**
- Production security monitoring (use commercial SIEM/SOAR platforms)
- Real-world threat detection (synthetic data only)
- Compliance requirements (not audited or certified)

## 📚 Technology Stack

- **Backend:** Python 3.11, Flask
- **AI/LLM:** OpenRouter API (Hermes 3 Llama 3.1 405B)
- **Data Processing:** Pandas, GeoPy
- **Frontend:** HTML5, Bootstrap 5, Vanilla JavaScript
- **Containerization:** Docker, Docker Compose
- **Data Format:** CSV, JSON

## 🤝 Contributing

This is a demo project, but improvements are welcome:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- **OpenRouter** for AI API access
- **Bootstrap** for UI components
- Energy sector cybersecurity professionals for domain expertise
- Open-source community for tools and libraries

## 📞 Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review logs: `docker-compose logs`
3. Open an issue on GitHub

---

**⚡ Built for the Energy Sector | 🛡️ Securing Critical Infrastructure | 🤖 Powered by AI**
