# Energy Sector AI Security Demo

A self-contained, Dockerized demo application that simulates an AI-assisted Security Operations Center (SOC) for energy sector infrastructure. This demo analyzes static cybersecurity data and provides AI-generated threat insights, trend summaries, and response recommendations.

## 🎯 Overview

This application demonstrates how an integrated AI assistant can analyze security events in an energy company environment:

- **Static Data Analysis**: Processes synthetic CSV/JSON files containing auth events, host inventories, vulnerability scans, and firewall logs
- **Rule-Based Detection**: Implements detection rules for impossible travel, patch drift, and open port anomalies
- **AI-Assisted Triage**: Uses a mock LLM service to generate contextual summaries and remediation recommendations
- **Human-in-the-Loop**: Provides a web dashboard where analysts can review, approve, or reject alerts

## 🏗️ Architecture

The demo consists of four main components:

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌──────────────┐
│   Static    │────▶│    Rules     │────▶│  AI Agent   │────▶│     Web      │
│    Data     │     │   Engine     │     │   Service   │     │  Dashboard   │
└─────────────┘     └──────────────┘     └─────────────┘     └──────────────┘
  CSV/JSON           alerts.json         triage.json        HTTP :8080
```

1. **Data Layer** (`/data`): Static synthetic datasets
   - `auth_events.csv` - User authentication logs
   - `host_inventory.csv` - System patch levels and configurations
   - `vuln_scan.json` - Vulnerability scan results
   - `firewall_logs.csv` - Network traffic logs

2. **Rules Engine** (`/rules`): Python-based detection rules
   - Impossible travel detection (>500 mph)
   - Patch drift detection (>30 days)
   - Open port anomaly detection (non-whitelisted ports)
   - Outputs: `alerts.json`

3. **AI Agent** (`/agent`): Mock LLM service
   - Reads alerts and generates contextual summaries
   - Provides energy-sector-specific remediation guidance
   - References NERC CIP compliance standards
   - Outputs: `triage.json`

4. **Web Dashboard** (`/web`): Flask-based UI
   - Displays alerts with AI-generated summaries
   - Approve/Reject buttons for analyst feedback
   - Real-time statistics and severity breakdowns
   - Serves on `http://localhost:8080`

## 🚀 Quick Start

### Prerequisites

- Docker (20.10+)
- Docker Compose (2.0+)
- 2GB free disk space

### Running the Demo

1. **Clone or navigate to the project directory:**
   ```bash
   cd /path/to/energy-sector-ai-security-demo
   ```

2. **Start all services:**
   ```bash
   docker-compose up --build
   ```

   This will:
   - Build Docker images for all services
   - Run the rules engine to analyze data and generate alerts
   - Run the AI agent to create triage summaries
   - Start the web dashboard

3. **Access the dashboard:**
   Open your browser to: **http://localhost:8080**

4. **Stop the demo:**
   ```bash
   docker-compose down
   ```

### Resetting the Demo

To clear all generated data and start fresh:

```bash
rm -f shared/alerts.json shared/triage.json shared/feedback.json
docker-compose up --build
```

## 📊 Demo Data

The demo includes realistic synthetic data for an energy company:

### Users
- `alice` - Legitimate user with suspicious travel patterns
- `bob` - User with international travel
- `charlie` - Regular domestic user
- `janitor` - Compromised account example

### Hosts
- `ems-server-1` - Energy Management System (Windows)
- `ops-server-2` - Operations server (Ubuntu)
- `legacy-hmi-1` - Human-Machine Interface (Windows XP, severely outdated)
- `backup-server-3` - Backup system (CentOS)
- Various workstations and file servers

### Detection Rules

1. **Impossible Travel**
   - Calculates geographic distance between consecutive logins
   - Flags travel speeds exceeding 500 mph
   - Example: Alice logs in from New York, then London within 1 hour

2. **Patch Drift**
   - Identifies systems not patched in 30+ days
   - Severity based on system criticality and drift duration
   - Example: `legacy-hmi-1` hasn't been patched in 500+ days

3. **Open Port Anomalies**
   - Compares allowed network traffic against port whitelist
   - Flags dangerous ports (Telnet 23, FTP 21, RDP 3389)
   - Example: Telnet connection to legacy HMI system

## 🖥️ Dashboard Features

### Statistics Panel
- Total alerts count
- Pending review count
- Approved/rejected counts
- Severity breakdown (Critical/High/Medium/Low)

### Alert Cards
Each alert displays:
- **Severity Badge**: Color-coded (Critical=Red, High=Orange, Medium=Yellow, Low=Green)
- **Alert Type**: impossible_travel, patch_drift, open_port_anomaly
- **Description**: Human-readable summary
- **AI Analysis**: Contextual summary with risk assessment
- **Technical Evidence**: Raw data in JSON format
- **Suggested Actions**: Remediation steps
- **Approve/Reject Buttons**: Human-in-the-loop feedback

### Analyst Workflow
1. Review AI-generated summary
2. Examine technical evidence
3. Approve (true positive) or Reject (false positive)
4. Add optional notes
5. Feedback stored in `shared/feedback.json`

## 🔧 Technical Details

### Technology Stack
- **Backend**: Python 3.11, Flask
- **Data Processing**: pandas, geopy
- **Frontend**: Bootstrap 5, Bootstrap Icons
- **Containerization**: Docker, Docker Compose

### File Structure
```
energy-sector-ai-security-demo/
├── data/                       # Static data files
│   ├── auth_events.csv
│   ├── host_inventory.csv
│   ├── vuln_scan.json
│   └── firewall_logs.csv
├── rules/                      # Rules engine service
│   ├── Dockerfile
│   ├── requirements.txt
│   └── rules_engine.py
├── agent/                      # AI agent service
│   ├── Dockerfile
│   ├── requirements.txt
│   └── agent.py
├── web/                        # Web dashboard service
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app.py
│   └── templates/
│       └── dashboard.html
├── shared/                     # Shared data volume
│   ├── alerts.json            # Generated by rules engine
│   ├── triage.json            # Generated by AI agent
│   └── feedback.json          # Generated by web dashboard
├── docker-compose.yml         # Service orchestration
├── README.md                  # This file
└── LICENSE
```

### Dependencies

**Rules Engine:**
- pandas==2.1.3
- geopy==2.4.0

**AI Agent:**
- openai==1.3.0 (used for future LLM integration)

**Web Dashboard:**
- flask==3.0.0

### Service Execution Order

1. **rules** (run once, exits on completion)
   - Reads static data files
   - Applies detection logic
   - Writes `alerts.json`

2. **agent** (run once, exits on completion)
   - Reads `alerts.json`
   - Generates AI summaries
   - Writes `triage.json`

3. **web** (continuous service)
   - Reads `triage.json`
   - Serves HTTP dashboard
   - Manages `feedback.json`

## 🔒 Security Considerations

This is a **demonstration environment only**:

- No external network connections required
- All data is synthetic and static
- No real credentials or sensitive information
- Mock LLM service (no API keys needed)
- Not intended for production use

## 🎓 Educational Use Cases

This demo is designed for:

- Training SOC analysts on AI-assisted workflows
- Demonstrating energy sector cybersecurity scenarios
- Prototyping human-in-the-loop security systems
- Teaching Docker-based microservices architecture
- Showcasing NERC CIP compliance concepts

## 🔮 Future Enhancements

Potential additions for extended demos:

1. **Real LLM Integration**: Replace mock with OpenAI GPT-4 or local Llama models
2. **Time-Series Analysis**: Add trending and anomaly detection over time
3. **MITRE ATT&CK Mapping**: Link alerts to ATT&CK framework tactics
4. **Automated Response**: Implement scripted remediation actions
5. **Multi-User Support**: Add authentication and role-based access
6. **Export Functionality**: Generate PDF reports and CSV exports
7. **Integration APIs**: Connect to real SIEM/SOAR platforms

## 📝 Customization

### Adding New Detection Rules

Edit `rules/rules_engine.py`:

```python
def detect_custom_rule(data):
    alerts = []
    # Your detection logic here
    return alerts
```

Add to main():

```python
custom_alerts = detect_custom_rule(data)
all_alerts.extend(custom_alerts)
```

### Modifying Synthetic Data

Edit files in `/data` directory to create different scenarios:
- Add more users to `auth_events.csv`
- Update host configurations in `host_inventory.csv`
- Add vulnerabilities to `vuln_scan.json`
- Create new firewall patterns in `firewall_logs.csv`

### Customizing UI

Edit `web/templates/dashboard.html`:
- Modify Bootstrap styling
- Add new data visualizations
- Change color schemes in `<style>` section

## 🤝 Contributing

This is a demo project. Contributions welcome:
- Add new detection rules
- Improve AI summaries
- Enhance UI/UX
- Add documentation
- Report bugs

## 📄 License

See LICENSE file for details.

## 🆘 Troubleshooting

### Issue: Services fail to start
```bash
# Check Docker is running
docker --version
docker-compose --version

# View logs
docker-compose logs rules
docker-compose logs agent
docker-compose logs web
```

### Issue: Dashboard shows no alerts
```bash
# Verify alerts were generated
cat shared/alerts.json

# Verify triage was created
cat shared/triage.json

# Restart services
docker-compose restart
```

### Issue: Port 8080 already in use
Edit `docker-compose.yml`:
```yaml
ports:
  - "8081:8080"  # Change 8080 to any available port
```

### Issue: Permission denied on shared/ folder
```bash
# Fix permissions
chmod -R 777 shared/
```

## 📧 Support

For questions or issues:
- Open a GitHub issue
- Review Docker Compose logs
- Check README troubleshooting section

---

**Note**: This is a local demonstration environment. It does not connect to external services, require internet access (after initial Docker image pull), or process real security data.
