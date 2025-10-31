#!/usr/bin/env python3
"""
Detection Rules Engine for Energy Sector SOC
Analyzes synthetic data to detect security threats and anomalies
"""

import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any

import pandas as pd
from geopy.distance import geodesic

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DetectionEngine:
    """Main detection engine for processing security events"""
    
    def __init__(self, data_dir: str, output_dir: str):
        """
        Initialize detection engine
        
        Args:
            data_dir: Directory containing input data files
            output_dir: Directory for output alerts
        """
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.alerts: List[Dict[str, Any]] = []
        
        # Whitelist for authorized ports
        self.authorized_ports = [22, 80, 443, 3389]
        
        # Thresholds
        self.impossible_travel_mph = 500
        self.patch_drift_critical_days = 60
        self.patch_drift_high_days = 30
        self.failed_login_threshold = 5
        self.failed_login_window_minutes = 10
    
    def load_auth_events(self) -> pd.DataFrame:
        """Load authentication events from CSV"""
        try:
            df = pd.read_csv(os.path.join(self.data_dir, 'auth_events.csv'))
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            logger.info(f"Loaded {len(df)} authentication events")
            return df
        except Exception as e:
            logger.error(f"Error loading auth_events.csv: {e}")
            return pd.DataFrame()
    
    def load_host_inventory(self) -> pd.DataFrame:
        """Load host inventory from CSV"""
        try:
            df = pd.read_csv(os.path.join(self.data_dir, 'host_inventory.csv'))
            df['last_patch_date'] = pd.to_datetime(df['last_patch_date'])
            logger.info(f"Loaded {len(df)} hosts")
            return df
        except Exception as e:
            logger.error(f"Error loading host_inventory.csv: {e}")
            return pd.DataFrame()
    
    def load_firewall_logs(self) -> pd.DataFrame:
        """Load firewall logs from CSV"""
        try:
            df = pd.read_csv(os.path.join(self.data_dir, 'firewall_logs.csv'))
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            logger.info(f"Loaded {len(df)} firewall log entries")
            return df
        except Exception as e:
            logger.error(f"Error loading firewall_logs.csv: {e}")
            return pd.DataFrame()
    
    def load_splunk_events(self) -> List[Dict[str, Any]]:
        """Load Splunk events from JSON"""
        try:
            with open(os.path.join(self.data_dir, 'splunk_events.json'), 'r') as f:
                events = json.load(f)
            logger.info(f"Loaded {len(events)} Splunk events")
            return events
        except Exception as e:
            logger.error(f"Error loading splunk_events.json: {e}")
            return []
    
    def load_vuln_scan(self) -> List[Dict[str, Any]]:
        """Load vulnerability scan results from JSON"""
        try:
            with open(os.path.join(self.data_dir, 'vuln_scan.json'), 'r') as f:
                scans = json.load(f)
            logger.info(f"Loaded {len(scans)} vulnerability scan results")
            return scans
        except Exception as e:
            logger.error(f"Error loading vuln_scan.json: {e}")
            return []
    
    def detect_impossible_travel(self, auth_df: pd.DataFrame) -> None:
        """
        Detect impossible travel based on geographic distance and time
        
        Args:
            auth_df: DataFrame containing authentication events
        """
        if auth_df.empty:
            return
        
        # Sort by user and timestamp
        auth_df = auth_df.sort_values(['user', 'timestamp'])
        
        # Group by user
        for user, group in auth_df.groupby('user'):
            events = group.reset_index(drop=True)
            
            for i in range(len(events) - 1):
                curr_event = events.iloc[i]
                next_event = events.iloc[i + 1]
                
                # Calculate distance in miles
                try:
                    coord1 = (curr_event['lat'], curr_event['lon'])
                    coord2 = (next_event['lat'], next_event['lon'])
                    distance_miles = geodesic(coord1, coord2).miles
                    
                    # Calculate time difference in hours
                    time_diff = (next_event['timestamp'] - curr_event['timestamp']).total_seconds() / 3600
                    
                    if time_diff > 0:
                        speed_mph = distance_miles / time_diff
                        
                        # Flag if speed exceeds threshold
                        if speed_mph > self.impossible_travel_mph:
                            severity = "critical" if speed_mph > 1000 else "high"
                            
                            alert = {
                                "id": str(uuid.uuid4()),
                                "type": "impossible_travel",
                                "severity": severity,
                                "timestamp": datetime.utcnow().isoformat() + "Z",
                                "description": f"Impossible travel detected for {user}",
                                "evidence": {
                                    "user": user,
                                    "location1": f"{curr_event['city']}, {curr_event['country']}",
                                    "location2": f"{next_event['city']}, {next_event['country']}",
                                    "timestamp1": curr_event['timestamp'].isoformat(),
                                    "timestamp2": next_event['timestamp'].isoformat(),
                                    "distance_miles": round(distance_miles, 2),
                                    "time_hours": round(time_diff, 2),
                                    "speed_mph": round(speed_mph, 2),
                                    "ip1": curr_event['source_ip'],
                                    "ip2": next_event['source_ip']
                                },
                                "suggested_actions": [
                                    f"Immediately contact {user} to verify recent login activity",
                                    "Reset user credentials and force password change",
                                    f"Block suspicious IP address: {next_event['source_ip']}",
                                    "Review all recent activity from this account",
                                    "Enable MFA if not already active"
                                ]
                            }
                            
                            self.alerts.append(alert)
                            logger.warning(f"Impossible travel detected: {user} - {speed_mph:.2f} mph")
                
                except Exception as e:
                    logger.error(f"Error calculating distance for {user}: {e}")
    
    def detect_patch_drift(self, host_df: pd.DataFrame) -> None:
        """
        Detect systems with outdated patches
        
        Args:
            host_df: DataFrame containing host inventory
        """
        if host_df.empty:
            return
        
        current_time = datetime.utcnow()
        
        for _, host in host_df.iterrows():
            days_since_patch = (current_time - host['last_patch_date']).days
            
            if days_since_patch > self.patch_drift_critical_days:
                severity = "critical"
            elif days_since_patch > self.patch_drift_high_days:
                severity = "high"
            else:
                continue
            
            alert = {
                "id": str(uuid.uuid4()),
                "type": "patch_drift",
                "severity": severity,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "description": f"Critical patch drift detected on {host['hostname']}",
                "evidence": {
                    "hostname": host['hostname'],
                    "ip": host['ip'],
                    "os": host['os'],
                    "last_patch_date": host['last_patch_date'].isoformat(),
                    "days_since_patch": days_since_patch,
                    "critical_apps": host['critical_apps'],
                    "location": host['location']
                },
                "suggested_actions": [
                    f"Schedule emergency patching for {host['hostname']}",
                    "Verify system availability for maintenance window",
                    "Review change management process for critical infrastructure",
                    f"Isolate {host['hostname']} if patch cannot be applied immediately",
                    "Document exception if patching not feasible (e.g., legacy SCADA systems)"
                ]
            }
            
            self.alerts.append(alert)
            logger.warning(f"Patch drift detected: {host['hostname']} - {days_since_patch} days")
    
    def detect_open_ports(self, firewall_df: pd.DataFrame) -> None:
        """
        Detect unauthorized open ports
        
        Args:
            firewall_df: DataFrame containing firewall logs
        """
        if firewall_df.empty:
            return
        
        # Filter for ALLOW actions
        allowed = firewall_df[firewall_df['action'] == 'ALLOW']
        
        # Group by hostname and destination port
        port_summary = allowed.groupby(['hostname', 'dest_port']).agg({
            'source_ip': 'first',
            'timestamp': 'first'
        }).reset_index()
        
        for _, entry in port_summary.iterrows():
            port = entry['dest_port']
            
            if port not in self.authorized_ports:
                # Determine severity based on port
                if port in [23, 5900, 8080, 8888, 9999]:  # Known risky ports
                    severity = "high"
                else:
                    severity = "medium"
                
                alert = {
                    "id": str(uuid.uuid4()),
                    "type": "open_port",
                    "severity": severity,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "description": f"Unauthorized port {port} open on {entry['hostname']}",
                    "evidence": {
                        "hostname": entry['hostname'],
                        "port": int(port),
                        "source_ip": entry['source_ip'],
                        "last_seen": entry['timestamp'].isoformat(),
                        "authorized_ports": self.authorized_ports
                    },
                    "suggested_actions": [
                        f"Investigate why port {port} is open on {entry['hostname']}",
                        "Verify if service on this port is required for operations",
                        f"Block port {port} at firewall if unauthorized",
                        "Review firewall rules for compliance with security policy",
                        "Check for backdoors or unauthorized services"
                    ]
                }
                
                self.alerts.append(alert)
                logger.warning(f"Unauthorized port detected: {entry['hostname']} - port {port}")
    
    def detect_splunk_anomalies(self, splunk_events: List[Dict[str, Any]]) -> None:
        """
        Analyze Splunk events for security anomalies
        
        Args:
            splunk_events: List of Splunk event dictionaries
        """
        if not splunk_events:
            return
        
        for event in splunk_events:
            event_type = event.get('event_type', 'unknown')
            severity = event.get('severity', 'medium')
            
            # Map Splunk severity to our severity levels
            if severity == 'critical':
                alert_severity = 'critical'
            elif severity == 'high':
                alert_severity = 'high'
            elif severity == 'medium':
                alert_severity = 'medium'
            else:
                alert_severity = 'low'
            
            # Generate suggested actions based on event type
            suggested_actions = self._get_splunk_actions(event_type, event)
            
            alert = {
                "id": str(uuid.uuid4()),
                "type": "splunk_anomaly",
                "severity": alert_severity,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "description": f"Splunk alert: {event.get('details', 'Security event detected')}",
                "evidence": {
                    "event_id": event.get('event_id'),
                    "event_type": event_type,
                    "source": event.get('source'),
                    "timestamp": event.get('timestamp'),
                    "user": event.get('user'),
                    "details": event.get('details'),
                    **{k: v for k, v in event.items() if k not in ['event_id', 'event_type', 'source', 'timestamp', 'user', 'details', 'severity']}
                },
                "suggested_actions": suggested_actions
            }
            
            self.alerts.append(alert)
            logger.warning(f"Splunk anomaly detected: {event_type} on {event.get('source')}")
    
    def _get_splunk_actions(self, event_type: str, event: Dict[str, Any]) -> List[str]:
        """
        Generate suggested actions based on Splunk event type
        
        Args:
            event_type: Type of Splunk event
            event: Event dictionary
            
        Returns:
            List of suggested actions
        """
        actions_map = {
            'failed_login': [
                f"Block source IP {event.get('source_ip')} at firewall",
                f"Lock account {event.get('user')} temporarily",
                "Review authentication logs for pattern analysis",
                "Enable account lockout policy if not configured",
                "Consider implementing rate limiting on authentication service"
            ],
            'privilege_escalation': [
                f"Immediately isolate {event.get('source')} from network",
                f"Remove newly created account: {event.get('user')}",
                "Conduct forensic analysis on affected system",
                "Reset credentials for all administrative accounts",
                "Review sudo/admin access logs for unauthorized changes"
            ],
            'unusual_process': [
                f"Terminate process {event.get('process')} immediately",
                "Run full antivirus/EDR scan on affected system",
                f"Quarantine {event.get('source')} for investigation",
                "Analyze process memory dump for IOCs",
                "Check for lateral movement from this system"
            ],
            'data_exfiltration': [
                f"Block outbound traffic to {event.get('destination_ip')}",
                "Identify what data was transferred",
                f"Isolate {event.get('source')} immediately",
                "Review DLP policies and logs",
                "Initiate incident response procedures for data breach"
            ],
            'config_change': [
                "Restore configuration from last known good backup",
                "Identify who made the unauthorized change",
                f"Lock down {event.get('source')} for investigation",
                "Review change management logs",
                "Verify integrity of SCADA/ICS systems"
            ],
            'ransomware_indicator': [
                "IMMEDIATELY disconnect affected systems from network",
                "DO NOT pay ransom - contact law enforcement",
                "Restore from offline backups",
                "Run ransomware decryption tools if available",
                "Initiate full incident response and disaster recovery plan"
            ],
            'backup_deletion': [
                "Stop backup deletion process immediately",
                "Verify integrity of remaining backups",
                "Disable administrative credentials used for deletion",
                "Create offline backup copies immediately",
                "Investigate for ransomware attack preparation"
            ]
        }
        
        return actions_map.get(event_type, [
            f"Investigate event on {event.get('source')}",
            "Review relevant logs for additional context",
            "Document findings in incident tracking system"
        ])
    
    def run_all_detections(self) -> None:
        """Run all detection rules"""
        logger.info("Starting detection engine")
        
        # Load data
        auth_df = self.load_auth_events()
        host_df = self.load_host_inventory()
        firewall_df = self.load_firewall_logs()
        splunk_events = self.load_splunk_events()
        
        # Run detections
        logger.info("Running impossible travel detection")
        self.detect_impossible_travel(auth_df)
        
        logger.info("Running patch drift detection")
        self.detect_patch_drift(host_df)
        
        logger.info("Running open port detection")
        self.detect_open_ports(firewall_df)
        
        logger.info("Running Splunk anomaly detection")
        self.detect_splunk_anomalies(splunk_events)
        
        logger.info(f"Detection complete: {len(self.alerts)} alerts generated")
    
    def save_alerts(self) -> None:
        """Save alerts to JSON file"""
        output_file = os.path.join(self.output_dir, 'alerts.json')
        
        try:
            with open(output_file, 'w') as f:
                json.dump(self.alerts, f, indent=2)
            logger.info(f"Alerts saved to {output_file}")
        except Exception as e:
            logger.error(f"Error saving alerts: {e}")
            raise


def main():
    """Main entry point"""
    data_dir = os.environ.get('DATA_DIR', '/data')
    output_dir = os.environ.get('OUTPUT_DIR', '/shared')
    
    logger.info(f"Initializing detection engine (data_dir={data_dir}, output_dir={output_dir})")
    
    engine = DetectionEngine(data_dir, output_dir)
    engine.run_all_detections()
    engine.save_alerts()
    
    logger.info("Detection engine completed successfully")


if __name__ == '__main__':
    main()
