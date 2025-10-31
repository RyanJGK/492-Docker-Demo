"""Flask web interface for the AI-assisted SOC demo platform."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from flask import Flask, abort, jsonify, render_template, request
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("web.app")


TRIAGE_FILE = os.environ.get("TRIAGE_FILE", "/shared/triage.json")
FEEDBACK_FILE = os.environ.get("FEEDBACK_FILE", "/shared/feedback.json")


def create_app() -> Flask:
    """Application factory for the SOC demo dashboard."""

    app = Flask(__name__)

    @app.route("/")
    def index() -> str:
        """Render the dashboard with triaged alerts."""

        triage_data = load_json_list(TRIAGE_FILE)
        feedback_history = load_json_list(FEEDBACK_FILE)
        stats = compute_stats(triage_data, feedback_history)
        return render_template(
            "dashboard.html",
            triage=triage_data,
            feedback=feedback_history,
            stats=stats,
        )

    @app.route("/api/alerts", methods=["GET"])
    def api_alerts() -> Any:
        """Return triaged alerts as JSON."""

        return jsonify(load_json_list(TRIAGE_FILE))

    @app.route("/api/feedback", methods=["GET"])
    def api_feedback() -> Any:
        """Return analyst feedback history."""

        return jsonify(load_json_list(FEEDBACK_FILE))

    @app.route("/api/stats", methods=["GET"])
    def api_stats() -> Any:
        """Return dashboard statistics."""

        triage_data = load_json_list(TRIAGE_FILE)
        feedback_history = load_json_list(FEEDBACK_FILE)
        return jsonify(compute_stats(triage_data, feedback_history))

    @app.route("/feedback", methods=["POST"])
    def submit_feedback() -> Any:
        """Persist analyst feedback for a specific alert."""

        payload = request.get_json(silent=True) or {}
        alert_id = payload.get("alert_id")
        action = (payload.get("action") or "").lower()
        reason = (payload.get("reason") or "").strip()

        if not alert_id or action not in {"approved", "rejected"} or not reason:
            abort(400, description="Invalid feedback payload")

        triage_data = load_json_list(TRIAGE_FILE)
        alert_record = next((item for item in triage_data if item.get("alert_id") == alert_id), None)
        if not alert_record:
            abort(404, description="Alert not found")

        feedback_entry = {
            "alert_id": alert_id,
            "type": (alert_record.get("original_alert") or {}).get("type"),
            "action": action,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        feedback_history = load_json_list(FEEDBACK_FILE)
        feedback_history.append(feedback_entry)
        persist_json_list(FEEDBACK_FILE, feedback_history)
        return jsonify({"status": "success", "feedback": feedback_entry})

    return app


def load_json_list(path: str) -> List[Dict[str, Any]]:
    """Load JSON list data from disk, returning an empty list if missing."""

    if not os.path.exists(path):
        logger.info("JSON file not found, returning empty list: %s", path)
        return []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
            if isinstance(data, list):
                return data
            logger.warning("Expected list in %s but found %s", path, type(data))
    except json.JSONDecodeError as exc:
        logger.error("Failed to decode JSON from %s: %s", path, exc)
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Unexpected error reading %s: %s", path, exc)
    return []


def persist_json_list(path: str, data: List[Dict[str, Any]]) -> None:
    """Persist list data to disk as JSON."""

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
    logger.info("Persisted %s entries to %s", len(data), path)


def compute_stats(triage: List[Dict[str, Any]], feedback: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute summary statistics for dashboard display."""

    severity_counts: Dict[str, int] = {}
    type_counts: Dict[str, int] = {}
    for record in triage:
        severity = str((record.get("original_alert") or {}).get("severity") or "unknown").lower()
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
        alert_type = (record.get("original_alert") or {}).get("type") or "unknown"
        type_counts[alert_type] = type_counts.get(alert_type, 0) + 1

    feedback_totals = {
        "approved": sum(1 for item in feedback if item.get("action") == "approved"),
        "rejected": sum(1 for item in feedback if item.get("action") == "rejected"),
    }

    return {
        "alerts_total": len(triage),
        "feedback_total": len(feedback),
        "severity_counts": severity_counts,
        "type_counts": type_counts,
        "feedback_totals": feedback_totals,
    }


def run() -> None:
    """Run the Flask development server."""

    app = create_app()
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    run()
