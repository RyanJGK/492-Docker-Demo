"""Detection engine for AI-assisted SOC demo platform."""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd
from geopy.distance import geodesic


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("rules.detect")


WHITELISTED_PORTS = {22, 80, 443, 3389}
IMPOSSIBLE_TRAVEL_THRESHOLD_MPH = 500
CRITICAL_PATCH_DAYS = 60
HIGH_PATCH_DAYS = 30


def load_csv(path: str) -> pd.DataFrame:
    """Load a CSV file into a DataFrame, returning an empty frame if missing."""

    if not os.path.exists(path):
        logger.warning("CSV file not found: %s", path)
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Failed to read CSV %s: %s", path, exc)
        return pd.DataFrame()


def load_json(path: str) -> Any:
    """Load JSON content from a file, returning None if missing or invalid."""

    if not os.path.exists(path):
        logger.warning("JSON file not found: %s", path)
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Failed to read JSON %s: %s", path, exc)
        return None


def build_alert(
    alert_type: str,
    severity: str,
    description: str,
    evidence: Dict[str, Any],
    suggested_actions: Iterable[str],
) -> Dict[str, Any]:
    """Construct an alert record compliant with the shared schema."""

    timestamp = datetime.now(timezone.utc).isoformat()
    alert = {
        "id": str(uuid.uuid4()),
        "type": alert_type,
        "severity": severity,
        "timestamp": timestamp,
        "description": description,
        "evidence": evidence,
        "suggested_actions": list(suggested_actions),
    }
    logger.debug("Generated alert: %s", alert)
    return alert


def detect_impossible_travel(auth_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Detect impossible travel events based on login distances and timing."""

    if auth_df.empty:
        return []

    alerts: List[Dict[str, Any]] = []
    try:
        auth_df = auth_df.copy()
        auth_df["timestamp"] = pd.to_datetime(auth_df["timestamp"], utc=True, errors="coerce")
        auth_df = auth_df.dropna(subset=["timestamp", "lat", "lon", "user"])
        auth_df["lat"] = auth_df["lat"].astype(float)
        auth_df["lon"] = auth_df["lon"].astype(float)
        auth_df["success"] = auth_df["success"].astype(str).str.lower() == "true"
        auth_df = auth_df[auth_df["success"]]

        auth_df = auth_df.sort_values(["user", "timestamp"])

        for user, group in auth_df.groupby("user"):
            group = group.reset_index(drop=True)
            for idx in range(1, len(group)):
                prev = group.loc[idx - 1]
                current = group.loc[idx]
                time_delta = current["timestamp"] - prev["timestamp"]
                hours = time_delta.total_seconds() / 3600
                if hours <= 0:
                    continue

                prev_coord = (prev["lat"], prev["lon"])
                curr_coord = (current["lat"], current["lon"])
                distance_miles = geodesic(prev_coord, curr_coord).miles
                speed = distance_miles / hours if hours else float("inf")

                if speed > IMPOSSIBLE_TRAVEL_THRESHOLD_MPH:
                    severity = "critical" if speed >= IMPOSSIBLE_TRAVEL_THRESHOLD_MPH * 2 else "high"
                    description = (
                        f"User {user} traveled {distance_miles:.0f} miles in {hours:.1f} hours "
                        f"(~{speed:.0f} mph), exceeding policy limits."
                    )
                    evidence = {
                        "user": user,
                        "previous_login": prev["timestamp"].isoformat(),
                        "previous_city": prev.get("city"),
                        "previous_country": prev.get("country"),
                        "current_login": current["timestamp"].isoformat(),
                        "current_city": current.get("city"),
                        "current_country": current.get("country"),
                        "distance_miles": round(distance_miles, 2),
                        "speed_mph": round(speed, 2),
                    }
                    suggested_actions = [
                        "Trigger MFA reset and investigate recent account activity",
                        "Correlate with VPN logs and badge access records",
                        "Temporarily limit remote access until validated",
                    ]
                    alerts.append(
                        build_alert(
                            alert_type="impossible_travel",
                            severity=severity,
                            description=description,
                            evidence=evidence,
                            suggested_actions=suggested_actions,
                        )
                    )
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Impossible travel detection failed: %s", exc)

    return alerts


def detect_patch_drift(host_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Detect hosts that have exceeded acceptable patch windows."""

    if host_df.empty:
        return []

    alerts: List[Dict[str, Any]] = []
    today = datetime.now(timezone.utc).date()
    try:
        for _, row in host_df.iterrows():
            last_patch_raw = str(row.get("last_patch_date", "")).strip()
            if not last_patch_raw:
                continue
            last_patch_dt = pd.to_datetime(last_patch_raw, utc=True, errors="coerce")
            if pd.isna(last_patch_dt):
                continue
            days_outdated = (today - last_patch_dt.date()).days
            if days_outdated <= HIGH_PATCH_DAYS:
                continue

            severity = "critical" if days_outdated > CRITICAL_PATCH_DAYS else "high"
            description = (
                f"Host {row.get('hostname')} last patched {days_outdated} days ago, "
                "exceeding maintenance window."
            )
            evidence = {
                "hostname": row.get("hostname"),
                "ip": row.get("ip"),
                "last_patch_date": last_patch_dt.date().isoformat(),
                "days_since_patch": days_outdated,
                "critical_apps": row.get("critical_apps"),
                "location": row.get("location"),
            }
            suggested_actions = [
                "Coordinate maintenance window with operations team",
                "Prioritize security patch deployment",
                "Verify compensating controls for impacted services",
            ]
            alerts.append(
                build_alert(
                    alert_type="patch_drift",
                    severity=severity,
                    description=description,
                    evidence=evidence,
                    suggested_actions=suggested_actions,
                )
            )
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Patch drift detection failed: %s", exc)

    return alerts


def detect_open_ports(firewall_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Detect allowed firewall traffic to unauthorized destination ports."""

    if firewall_df.empty:
        return []

    alerts: List[Dict[str, Any]] = []
    try:
        firewall_df = firewall_df.copy()
        firewall_df["dest_port"] = pd.to_numeric(firewall_df["dest_port"], errors="coerce")
        firewall_df = firewall_df.dropna(subset=["dest_port"])

        for _, row in firewall_df.iterrows():
            port = int(row["dest_port"])
            if row.get("action", "").lower() != "allowed" or port in WHITELISTED_PORTS:
                continue

            severity = "high" if port < 1024 else "medium"
            description = (
                f"Unauthorized port {port} allowed on host {row.get('hostname')} from "
                f"{row.get('source_ip')}"
            )
            evidence = {
                "timestamp": row.get("timestamp"),
                "source_ip": row.get("source_ip"),
                "dest_ip": row.get("dest_ip"),
                "dest_port": port,
                "protocol": row.get("protocol"),
                "hostname": row.get("hostname"),
            }
            suggested_actions = [
                "Review firewall ACLs for non-standard services",
                "Validate business justification with asset owner",
                "Capture packet trace to identify payload",
            ]
            alerts.append(
                build_alert(
                    alert_type="open_port",
                    severity=severity,
                    description=description,
                    evidence=evidence,
                    suggested_actions=suggested_actions,
                )
            )
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Open port detection failed: %s", exc)

    return alerts


def detect_splunk_anomalies(events: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Detect anomalous activity described in Splunk-derived JSON events."""

    if not events:
        return []

    alerts: List[Dict[str, Any]] = []
    try:
        for event in events:
            event_type = event.get("event_type")
            if event_type == "failed_login":
                count = int(event.get("count", 0))
                window = int(event.get("time_window_minutes", 0))
                if count > 5 and window <= 10:
                    description = (
                        f"{count} failed logins for user {event.get('user')} on "
                        f"{event.get('source')} within {window} minutes."
                    )
                    suggested_actions = [
                        "Lock or monitor affected account in Active Directory",
                        "Correlate with network telemetry for potential brute force",
                        "Initiate password reset if activity persists",
                    ]
                    alerts.append(
                        build_alert(
                            alert_type="splunk_anomaly",
                            severity="high",
                            description=description,
                            evidence={
                                "event_id": event.get("event_id"),
                                "source": event.get("source"),
                                "user": event.get("user"),
                                "count": count,
                                "time_window_minutes": window,
                                "source_ip": event.get("source_ip"),
                            },
                            suggested_actions=suggested_actions,
                        )
                    )
            elif event_type == "privilege_escalation":
                description = (
                    f"Privilege escalation detected on {event.get('source')} via "
                    f"process {event.get('process')}"
                )
                suggested_actions = [
                    "Isolate host from control network pending investigation",
                    "Review recent command history and created accounts",
                    "Coordinate with plant operations before remediation",
                ]
                alerts.append(
                    build_alert(
                        alert_type="splunk_anomaly",
                        severity="critical",
                        description=description,
                        evidence={
                            "event_id": event.get("event_id"),
                            "source": event.get("source"),
                            "process": event.get("process"),
                            "details": event.get("details"),
                        },
                        suggested_actions=suggested_actions,
                    )
                )
            elif event_type in {"unusual_process", "process_anomaly"}:
                description = (
                    f"Unusual process {event.get('process')} executed on {event.get('source')}"
                )
                suggested_actions = [
                    "Capture forensic image before restarting services",
                    "Validate command origin with historian team",
                    "Block outbound connections associated with reverse shell",
                ]
                alerts.append(
                    build_alert(
                        alert_type="splunk_anomaly",
                        severity="high",
                        description=description,
                        evidence={
                            "event_id": event.get("event_id"),
                            "source": event.get("source"),
                            "process": event.get("process"),
                            "command_line": event.get("command_line"),
                        },
                        suggested_actions=suggested_actions,
                    )
                )
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Splunk anomaly detection failed: %s", exc)

    return alerts


def main() -> None:
    """Entry point for detection pipeline."""

    data_dir = os.environ.get("DATA_DIR", "/data")
    output_dir = os.environ.get("OUTPUT_DIR", "/shared")
    os.makedirs(output_dir, exist_ok=True)

    auth_events_path = os.path.join(data_dir, "auth_events.csv")
    host_inventory_path = os.path.join(data_dir, "host_inventory.csv")
    firewall_logs_path = os.path.join(data_dir, "firewall_logs.csv")
    splunk_events_path = os.path.join(data_dir, "splunk_events.json")

    logger.info("Loading data sources from %s", data_dir)
    auth_df = load_csv(auth_events_path)
    hosts_df = load_csv(host_inventory_path)
    firewall_df = load_csv(firewall_logs_path)
    splunk_events = load_json(splunk_events_path) or []

    alerts: List[Dict[str, Any]] = []
    alerts.extend(detect_impossible_travel(auth_df))
    alerts.extend(detect_patch_drift(hosts_df))
    alerts.extend(detect_open_ports(firewall_df))
    alerts.extend(detect_splunk_anomalies(splunk_events))

    alerts_path = os.path.join(output_dir, "alerts.json")
    try:
        with open(alerts_path, "w", encoding="utf-8") as handle:
            json.dump(alerts, handle, indent=2)
        logger.info("Wrote %s alerts to %s", len(alerts), alerts_path)
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Failed to write alerts: %s", exc)
        raise


if __name__ == "__main__":
    main()
