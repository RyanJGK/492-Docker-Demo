#!/usr/bin/env python3
"""
AI Agent for Energy Sector Security Demo
Summarizes alerts and provides triage recommendations
"""

import json
import os
from datetime import datetime


def mock_llm_call(alert):
    """
    Mock LLM function that simulates GPT-4 analysis
    In production, this would call OpenAI API or local LLM
    """
    
    # Build context-aware summaries based on alert type and severity
    alert_type = alert['type']
    severity = alert['severity']
    
    if alert_type == 'impossible_travel':
        user = alert['user']
        evidence = alert['evidence']
        summary = f"""
**Alert Summary:** User account '{user}' shows signs of credential compromise. The account 
authenticated from {evidence['previous_location']} and then from {evidence['current_location']} 
within {evidence['speed_mph']:.0f} mph travel time, which is physically impossible. This pattern 
strongly suggests either credential theft or account sharing.

**Risk Assessment:** This is a HIGH-severity incident typical of credential-based attacks in 
energy sector environments. Attackers often use stolen credentials to move laterally through 
OT/IT networks after initial compromise.

**Recommended Actions:**
1. **Immediate**: Disable user account '{user}' and force password reset with MFA re-enrollment
2. **Investigation**: Review all access logs for this account over past 48 hours; check for 
   data exfiltration or lateral movement attempts
3. **Containment**: If account accessed critical systems (SCADA, EMS), initiate incident 
   response protocol and notify CISO
4. **Long-term**: Implement geo-fencing policies to block logins from unexpected countries
        """
    
    elif alert_type == 'patch_drift':
        host = alert['host']
        evidence = alert['evidence']
        days = evidence['days_since_patch']
        criticality = evidence['criticality']
        
        summary = f"""
**Alert Summary:** Critical infrastructure host '{host}' running {evidence['os']} has not 
received security patches in {days} days. This system is classified as '{criticality}' 
criticality and is at elevated risk of exploitation through known vulnerabilities.

**Risk Assessment:** Unpatched systems in energy environments are prime targets for ransomware 
and APT groups. With {days} days of patch drift, this host is likely vulnerable to multiple 
publicly disclosed exploits. The installed applications ({evidence['installed_apps']}) may 
contain remotely exploitable vulnerabilities.

**Recommended Actions:**
1. **Immediate**: Run targeted vulnerability scan against this host to identify active exposures
2. **Short-term**: Schedule emergency maintenance window to apply critical security patches; 
   coordinate with operations team to minimize downtime
3. **Compensating Controls**: If patching requires extended downtime, implement network 
   segmentation and additional monitoring on this host
4. **Process Improvement**: Review patch management SLAs for {criticality}-criticality systems
        """
    
    elif alert_type == 'open_port_anomaly':
        port = alert['evidence']['destination_port']
        dst_ip = alert['evidence']['destination_ip']
        
        port_descriptions = {
            23: 'Telnet (unencrypted remote access)',
            21: 'FTP (unencrypted file transfer)',
            3389: 'RDP (Windows remote desktop)',
            1433: 'Microsoft SQL Server'
        }
        
        port_desc = port_descriptions.get(port, f'non-standard port {port}')
        
        summary = f"""
**Alert Summary:** Network traffic detected to {port_desc} on host {dst_ip}. This port is 
outside the approved whitelist for energy sector operations and represents an attack surface 
that should be minimized according to NERC CIP standards.

**Risk Assessment:** Unusual open ports in OT/IT environments often indicate either misconfigurations 
or legacy systems that bypass standard hardening procedures. Port {port} is particularly concerning 
as it may allow unencrypted or poorly secured access to critical infrastructure components.

**Recommended Actions:**
1. **Investigation**: Identify what service is running on port {port} and whether it's required 
   for operational needs
2. **Firewall Review**: Update firewall rules to block port {port} if service is unnecessary; 
   if required, restrict access to specific source IPs only
3. **Encryption**: If this port must remain open, ensure all traffic is encrypted (e.g., use 
   SSH instead of Telnet, SFTP instead of FTP)
4. **Compliance**: Document justification for any exceptions to port whitelist per NERC CIP-007
        """
    
    else:
        summary = f"Unknown alert type: {alert_type}"
    
    return summary.strip()


def generate_triage(alerts):
    """Process alerts and generate triage recommendations"""
    triage_results = []
    
    print(f"Processing {len(alerts)} alerts...")
    
    for i, alert in enumerate(alerts, 1):
        print(f"  [{i}/{len(alerts)}] Analyzing {alert['type']} alert (ID: {alert['id'][:8]}...)")
        
        # Get AI summary (mock LLM)
        ai_summary = mock_llm_call(alert)
        
        # Build triage result
        triage = {
            'alert_id': alert['id'],
            'alert_type': alert['type'],
            'severity': alert['severity'],
            'timestamp': alert['timestamp'],
            'original_description': alert['description'],
            'evidence': alert['evidence'],
            'ai_summary': ai_summary,
            'suggested_actions': alert['suggested_actions'],
            'status': 'pending_review',
            'analyst_decision': None,
            'analyst_notes': None,
            'triage_timestamp': datetime.now().isoformat()
        }
        
        triage_results.append(triage)
    
    return triage_results


def main():
    """Main execution function"""
    print("=" * 60)
    print("Energy Sector Security AI Agent")
    print("=" * 60)
    
    # Load alerts
    alerts_file = '/shared/alerts.json'
    print(f"\nLoading alerts from {alerts_file}...")
    
    try:
        with open(alerts_file, 'r') as f:
            alerts = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: {alerts_file} not found. Run rules engine first.")
        return
    
    if not alerts:
        print("No alerts to process.")
        triage_results = []
    else:
        # Generate triage
        print(f"\nFound {len(alerts)} alerts to analyze\n")
        triage_results = generate_triage(alerts)
    
    # Save triage results
    output_file = '/shared/triage.json'
    with open(output_file, 'w') as f:
        json.dump(triage_results, f, indent=2)
    
    print(f"\n✓ Generated {len(triage_results)} triage reports")
    print(f"✓ Saved to {output_file}")
    
    # Print summary
    if triage_results:
        severity_counts = {}
        for t in triage_results:
            sev = t['severity']
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
        
        print("\nSeverity Breakdown:")
        for sev in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            if sev in severity_counts:
                print(f"  {sev}: {severity_counts[sev]}")
    
    print("=" * 60)


if __name__ == '__main__':
    main()
