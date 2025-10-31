#!/usr/bin/env python3
"""
Generate static HTML version of the dashboard for GitHub Pages
"""

import json
import os
from datetime import datetime
from jinja2 import Template

# Paths
DASHBOARD_TEMPLATE = 'web/templates/dashboard.html'
OUTPUT_FILE = 'docs/index.html'
TRIAGE_FILE = 'triage_sample.json'

# Sample triage data for static demo
SAMPLE_TRIAGE = [
    {
        "alert_id": "ALERT-001",
        "timestamp": "2025-10-29 11:00:00",
        "severity": "CRITICAL",
        "alert_type": "IMPOSSIBLE_TRAVEL",
        "original_description": "User robert.johnson logged in from Moscow Russia after previous login from Austin USA within impossible timeframe",
        "ai_summary": "This alert indicates a potential account compromise. The user 'robert.johnson' authenticated successfully from Moscow, Russia just 15 minutes after logging in from Austin, Texas. This is physically impossible and suggests either credential theft or simultaneous use of compromised credentials.\n\nRisk Factors:\n- Geographic distance: ~8,500 km\n- Time between logins: 15 minutes\n- Previous failed login attempt from Moscow\n- User has legitimate Austin-based access history\n\nRecommendation: HIGH PRIORITY - Suspend account immediately and initiate incident response.",
        "evidence": {
            "user": "robert.johnson",
            "login_1": {
                "timestamp": "2025-10-29 11:00:00",
                "location": "Moscow Russia",
                "ip": "192.168.100.5",
                "success": False
            },
            "login_2": {
                "timestamp": "2025-10-29 11:15:00",
                "location": "Austin USA",
                "ip": "10.0.3.200",
                "success": True
            },
            "distance_km": 8500,
            "time_diff_minutes": 15
        },
        "suggested_actions": [
            "Immediately suspend user account robert.johnson",
            "Force password reset on all enterprise systems",
            "Review all recent activities for this user",
            "Check for any data exfiltration attempts",
            "Notify user via out-of-band communication"
        ],
        "analyst_decision": None
    },
    {
        "alert_id": "ALERT-002",
        "timestamp": "2025-10-29 08:10:00",
        "severity": "HIGH",
        "alert_type": "BLOCKED_THREAT",
        "original_description": "Multiple blocked connection attempts to critical server from external IP 203.0.113.100",
        "ai_summary": "External IP address 203.0.113.100 attempted to establish RDP (Remote Desktop Protocol) connections to critical infrastructure server ems-server-1. The firewall successfully blocked these attempts.\n\nConcerns:\n- Target: High-criticality SCADA monitoring system\n- Protocol: RDP (port 3389) - commonly targeted for ransomware\n- Source: External internet IP\n- Pattern suggests automated scanning or targeted attack\n\nRecommendation: MEDIUM PRIORITY - Monitor for continued attempts, verify firewall rules are optimal.",
        "evidence": {
            "src_ip": "203.0.113.100",
            "dst_ip": "10.0.1.10",
            "dst_port": 3389,
            "protocol": "TCP",
            "action": "BLOCK",
            "target_system": "ems-server-1 (SCADA Monitor)",
            "criticality": "high"
        },
        "suggested_actions": [
            "Add source IP to threat intelligence feeds",
            "Review RDP exposure on external networks",
            "Verify MFA is enabled for all remote access",
            "Consider implementing VPN-only access to critical systems"
        ],
        "analyst_decision": None
    },
    {
        "alert_id": "ALERT-003",
        "timestamp": "2025-10-29 09:00:00",
        "severity": "HIGH",
        "alert_type": "UNPATCHED_CRITICAL",
        "original_description": "Critical system ops-server-2 running outdated software (last patched 2025-09-10)",
        "ai_summary": "High-criticality server 'ops-server-2' has not received security patches in over 50 days. This Ubuntu system runs critical infrastructure including PostgreSQL database and Apache web services.\n\nVulnerabilities:\n- Multiple CVEs likely unpatched\n- Running Apache and PostgreSQL with known vulnerabilities\n- Exposes attack surface to both internal and external threats\n\nRecommendation: HIGH PRIORITY - Schedule maintenance window for patching within 48 hours.",
        "evidence": {
            "hostname": "ops-server-2",
            "ip_address": "10.0.1.11",
            "os": "Ubuntu 20.04",
            "last_patch_date": "2025-09-10",
            "days_since_patch": 50,
            "criticality": "high",
            "installed_apps": ["Apache", "PostgreSQL", "Python"]
        },
        "suggested_actions": [
            "Schedule emergency patching maintenance window",
            "Perform full vulnerability scan after patching",
            "Review patch management policy and automation",
            "Consider implementing automated security updates for critical systems"
        ],
        "analyst_decision": None
    },
    {
        "alert_id": "ALERT-004",
        "timestamp": "2025-10-29 14:00:00",
        "severity": "MEDIUM",
        "alert_type": "ANOMALOUS_LOGIN",
        "original_description": "User michael.rodriguez accessed system from unusual location Sydney Australia",
        "ai_summary": "User 'michael.rodriguez' successfully authenticated from Sydney, Australia. While this is unusual given their typical Houston, Texas location, there are several factors to consider:\n\nNormal Indicators:\n- Successful authentication (credentials valid)\n- No failed attempts preceding this login\n- User has history of legitimate access\n\nUnusual Indicators:\n- Significant geographic distance from normal location\n- No travel notification on file\n\nRecommendation: LOW-MEDIUM PRIORITY - Contact user to verify legitimate travel. If not traveling, escalate to HIGH priority.",
        "evidence": {
            "user": "michael.rodriguez",
            "location": "Sydney Australia",
            "ip": "203.0.113.50",
            "timestamp": "2025-10-29 14:00:00",
            "success": True,
            "typical_locations": ["Houston USA"]
        },
        "suggested_actions": [
            "Contact michael.rodriguez to verify travel to Australia",
            "If legitimate, update user profile with travel dates",
            "If not legitimate, immediately suspend account and investigate",
            "Review all activities during this session"
        ],
        "analyst_decision": None
    },
    {
        "alert_id": "ALERT-005",
        "timestamp": "2025-10-29 09:30:00",
        "severity": "CRITICAL",
        "alert_type": "LEGACY_SYSTEM_ALERT",
        "original_description": "Critical legacy system legacy-hmi-1 running Windows XP detected with active network connections",
        "ai_summary": "CRITICAL: A legacy Windows XP system (legacy-hmi-1) is actively running and connected to the network. This system:\n\n- Runs unsupported Windows XP (end-of-life since 2014)\n- Contains legacy SCADA client software\n- Has not received security patches since 2024-05-15\n- Marked as CRITICAL infrastructure component\n- Vulnerable to all Windows XP exploits (1000+ known CVEs)\n\nImmediate Risks:\n- Easy target for ransomware (e.g., WannaCry, NotPetya)\n- Potential pivot point for network intrusion\n- Cannot be patched against modern threats\n- Likely fails compliance requirements\n\nRecommendation: CRITICAL PRIORITY - Immediately isolate from network or implement strict network segmentation.",
        "evidence": {
            "hostname": "legacy-hmi-1",
            "ip_address": "192.168.100.10",
            "os": "Windows XP",
            "last_patch_date": "2024-05-15",
            "days_since_patch": 565,
            "criticality": "critical",
            "installed_apps": ["Legacy SCADA Client"],
            "network_activity": True
        },
        "suggested_actions": [
            "URGENT: Isolate system to dedicated VLAN with strict firewall rules",
            "Implement application whitelisting if system must remain operational",
            "Develop migration plan to modern OS within 90 days",
            "Implement enhanced monitoring and IDS/IPS rules",
            "Document business justification for continued operation",
            "Ensure air-gapped backup of critical SCADA configurations"
        ],
        "analyst_decision": None
    },
    {
        "alert_id": "ALERT-006",
        "timestamp": "2025-10-29 09:15:00",
        "severity": "LOW",
        "alert_type": "ALLOWED_TRAFFIC",
        "original_description": "Database connection from trusted internal host to ops-server-2",
        "ai_summary": "Normal database traffic detected between internal systems. Server 10.0.1.10 connected to PostgreSQL database on ops-server-2 (10.0.1.11) via standard port 3306.\n\nNormal Indicators:\n- Source and destination are both internal trusted hosts\n- Using standard database port\n- Traffic was allowed by firewall policy\n- Consistent with expected application architecture\n\nRecommendation: LOW PRIORITY - Normal operations, no action required. Log retained for audit purposes.",
        "evidence": {
            "timestamp": "2025-10-29 09:15:00",
            "src_ip": "10.0.1.10",
            "dst_ip": "10.0.2.20",
            "dst_port": 3306,
            "protocol": "TCP",
            "action": "ALLOW",
            "bytes": 2048
        },
        "suggested_actions": [
            "Continue monitoring database access patterns",
            "Ensure database credentials are rotated regularly",
            "Verify encryption in transit for database connections"
        ],
        "analyst_decision": None
    }
]

# Calculate statistics
def calculate_stats(triage_data):
    total = len(triage_data)
    severity_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
    status_counts = {'pending_review': 0, 'approved': 0, 'rejected': 0}
    
    for item in triage_data:
        severity_counts[item['severity']] = severity_counts.get(item['severity'], 0) + 1
        
        if item.get('analyst_decision') == 'approved':
            status_counts['approved'] += 1
        elif item.get('analyst_decision') == 'rejected':
            status_counts['rejected'] += 1
        else:
            status_counts['pending_review'] += 1
    
    return {
        'total': total,
        'severity': severity_counts,
        'status': status_counts
    }

def generate_static_site():
    """Generate static HTML for GitHub Pages"""
    
    # Read template
    with open(DASHBOARD_TEMPLATE, 'r') as f:
        template_content = f.read()
    
    # Create Jinja2 template
    template = Template(template_content)
    
    # Calculate stats
    stats = calculate_stats(SAMPLE_TRIAGE)
    
    # Render template
    html_content = template.render(
        triage=SAMPLE_TRIAGE,
        stats=stats,
        current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        static_mode=True
    )
    
    # Create docs directory if it doesn't exist
    os.makedirs('docs', exist_ok=True)
    
    # Write output
    with open(OUTPUT_FILE, 'w') as f:
        f.write(html_content)
    
    print(f"? Static site generated: {OUTPUT_FILE}")
    print(f"  - Total alerts: {stats['total']}")
    print(f"  - Critical: {stats['severity']['CRITICAL']}")
    print(f"  - High: {stats['severity']['HIGH']}")
    print(f"  - Medium: {stats['severity']['MEDIUM']}")
    print(f"  - Low: {stats['severity']['LOW']}")

if __name__ == '__main__':
    generate_static_site()
