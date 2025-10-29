#!/usr/bin/env python3
"""
Rules Engine for Energy Sector Security Demo
Detects: Impossible Travel, Patch Drift, Open Port Anomalies
"""

import pandas as pd
import json
from datetime import datetime, timedelta
from geopy.distance import geodesic
import uuid

# Configuration
IMPOSSIBLE_TRAVEL_SPEED_MPH = 500  # Flag travel faster than 500 mph
PATCH_DRIFT_DAYS = 30  # Flag hosts not patched in 30+ days
ALLOWED_PORTS = {22, 80, 443, 53, 5432, 3306, 445}  # Whitelist


def load_data():
    """Load all static data files"""
    print("Loading data files...")
    auth_events = pd.read_csv('/data/auth_events.csv')
    auth_events['timestamp'] = pd.to_datetime(auth_events['timestamp'])
    
    host_inventory = pd.read_csv('/data/host_inventory.csv')
    host_inventory['last_patch_date'] = pd.to_datetime(host_inventory['last_patch_date'])
    
    with open('/data/vuln_scan.json', 'r') as f:
        vuln_data = json.load(f)
    
    firewall_logs = pd.read_csv('/data/firewall_logs.csv')
    
    return auth_events, host_inventory, vuln_data, firewall_logs


def detect_impossible_travel(auth_events):
    """Detect geographically impossible travel between logins"""
    alerts = []
    
    # Sort by user and timestamp
    auth_events = auth_events.sort_values(['user', 'timestamp'])
    
    for user in auth_events['user'].unique():
        user_events = auth_events[auth_events['user'] == user].reset_index(drop=True)
        
        for i in range(1, len(user_events)):
            prev = user_events.iloc[i-1]
            curr = user_events.iloc[i]
            
            # Calculate distance and time
            coord1 = (prev['latitude'], prev['longitude'])
            coord2 = (curr['latitude'], curr['longitude'])
            distance_miles = geodesic(coord1, coord2).miles
            
            time_diff_hours = (curr['timestamp'] - prev['timestamp']).total_seconds() / 3600
            
            if time_diff_hours > 0:
                speed_mph = distance_miles / time_diff_hours
                
                if speed_mph > IMPOSSIBLE_TRAVEL_SPEED_MPH:
                    alerts.append({
                        'id': str(uuid.uuid4()),
                        'type': 'impossible_travel',
                        'severity': 'HIGH',
                        'timestamp': curr['timestamp'].isoformat(),
                        'user': user,
                        'description': f"User '{user}' traveled {distance_miles:.0f} miles in {time_diff_hours:.1f} hours ({speed_mph:.0f} mph)",
                        'evidence': {
                            'previous_location': prev['location'],
                            'previous_ip': prev['source_ip'],
                            'previous_time': prev['timestamp'].isoformat(),
                            'current_location': curr['location'],
                            'current_ip': curr['source_ip'],
                            'current_time': curr['timestamp'].isoformat(),
                            'distance_miles': round(distance_miles, 2),
                            'speed_mph': round(speed_mph, 2)
                        },
                        'suggested_actions': [
                            'Immediately disable user account pending investigation',
                            'Review MFA/authentication logs for compromise indicators',
                            'Contact user to verify recent travel activity'
                        ]
                    })
    
    return alerts


def detect_patch_drift(host_inventory):
    """Detect hosts with outdated patch levels"""
    alerts = []
    current_date = datetime.now()
    threshold_date = current_date - timedelta(days=PATCH_DRIFT_DAYS)
    
    for _, host in host_inventory.iterrows():
        if host['last_patch_date'] < threshold_date:
            days_since_patch = (current_date - host['last_patch_date']).days
            
            # Determine severity based on criticality and days
            if host['criticality'] == 'critical' and days_since_patch > 90:
                severity = 'CRITICAL'
            elif host['criticality'] in ['high', 'critical']:
                severity = 'HIGH'
            elif days_since_patch > 60:
                severity = 'MEDIUM'
            else:
                severity = 'LOW'
            
            alerts.append({
                'id': str(uuid.uuid4()),
                'type': 'patch_drift',
                'severity': severity,
                'timestamp': current_date.isoformat(),
                'host': host['hostname'],
                'description': f"Host '{host['hostname']}' has not been patched in {days_since_patch} days",
                'evidence': {
                    'hostname': host['hostname'],
                    'ip_address': host['ip_address'],
                    'os': host['os'],
                    'last_patch_date': host['last_patch_date'].isoformat(),
                    'days_since_patch': days_since_patch,
                    'criticality': host['criticality'],
                    'installed_apps': host['installed_apps']
                },
                'suggested_actions': [
                    'Schedule emergency patching window',
                    'Review change management policy',
                    'Isolate system if critical vulnerabilities exist'
                ]
            })
    
    return alerts


def detect_open_port_anomalies(firewall_logs):
    """Detect suspicious open ports or connections"""
    alerts = []
    
    # Focus on ALLOW actions to unusual ports
    allowed_traffic = firewall_logs[firewall_logs['action'] == 'ALLOW']
    
    for _, log in allowed_traffic.iterrows():
        port = log['dst_port']
        
        if port not in ALLOWED_PORTS:
            # Determine severity based on known dangerous ports
            if port in [23, 21, 3389, 1433]:  # Telnet, FTP, RDP, MSSQL
                severity = 'HIGH'
            else:
                severity = 'MEDIUM'
            
            alerts.append({
                'id': str(uuid.uuid4()),
                'type': 'open_port_anomaly',
                'severity': severity,
                'timestamp': log['timestamp'],
                'host': log['dst_ip'],
                'description': f"Suspicious traffic allowed to port {port} on {log['dst_ip']}",
                'evidence': {
                    'source_ip': log['src_ip'],
                    'destination_ip': log['dst_ip'],
                    'destination_port': int(port),
                    'protocol': log['protocol'],
                    'bytes': int(log['bytes']),
                    'timestamp': log['timestamp']
                },
                'suggested_actions': [
                    'Review firewall rules for this port',
                    'Investigate if service on this port is necessary',
                    'Consider blocking or restricting access'
                ]
            })
    
    # Remove duplicates (same dst_ip and dst_port)
    seen = set()
    unique_alerts = []
    for alert in alerts:
        key = (alert['host'], alert['evidence']['destination_port'])
        if key not in seen:
            seen.add(key)
            unique_alerts.append(alert)
    
    return unique_alerts


def main():
    """Main execution function"""
    print("=" * 60)
    print("Energy Sector Security Rules Engine")
    print("=" * 60)
    
    # Load data
    auth_events, host_inventory, vuln_data, firewall_logs = load_data()
    
    # Run detection rules
    print("\n[1/3] Detecting impossible travel...")
    travel_alerts = detect_impossible_travel(auth_events)
    print(f"   Found {len(travel_alerts)} impossible travel alert(s)")
    
    print("\n[2/3] Detecting patch drift...")
    patch_alerts = detect_patch_drift(host_inventory)
    print(f"   Found {len(patch_alerts)} patch drift alert(s)")
    
    print("\n[3/3] Detecting open port anomalies...")
    port_alerts = detect_open_port_anomalies(firewall_logs)
    print(f"   Found {len(port_alerts)} open port alert(s)")
    
    # Combine all alerts
    all_alerts = travel_alerts + patch_alerts + port_alerts
    
    # Save to shared volume
    output_file = '/shared/alerts.json'
    with open(output_file, 'w') as f:
        json.dump(all_alerts, f, indent=2)
    
    print(f"\n✓ Generated {len(all_alerts)} total alerts")
    print(f"✓ Saved to {output_file}")
    print("=" * 60)


if __name__ == '__main__':
    main()
