"""AI agent service for triaging alerts with LLM assistance."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("agent.service")


OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY environment variable not set")

ALERTS_FILE = os.environ.get("ALERTS_FILE", "/shared/alerts.json")
TRIAGE_FILE = os.environ.get("TRIAGE_FILE", "/shared/triage.json")
FEEDBACK_FILE = os.environ.get("FEEDBACK_FILE", "/shared/feedback.json")


SYSTEM_PROMPT_TEMPLATE = (
    "You are a cybersecurity analyst for an energy sector company (SCADA, EMS systems).\n"
    "Provide: 1) Risk score (1-10) with justification, 2) Threat analysis in energy context,\n"
    "3) 2-3 actionable remediation steps, 4) Consider operational impact.\n"
    "Previous feedback: {feedback_context}\n"
    "Prioritize critical infrastructure availability and safety."
)


@dataclass
class FeedbackStats:
    """Aggregated feedback metrics for an alert type."""

    approvals: int = 0
    rejections: int = 0

    @property
    def total(self) -> int:
        """Total feedback count."""

        return self.approvals + self.rejections

    def adjust_confidence(self, base_confidence: float) -> Tuple[float, bool]:
        """Adjust confidence based on feedback trends."""

        if self.total == 0:
            return base_confidence, False

        adjustment = 0.0
        if self.approvals > self.rejections:
            adjustment = min(0.15, self.approvals * 0.03)
        elif self.rejections > self.approvals:
            adjustment = -min(0.20, self.rejections * 0.04)

        adjusted = max(0.05, min(0.99, base_confidence + adjustment))
        return adjusted, True


def call_llm(prompt: str, system_prompt: str) -> str:
    """Invoke the OpenRouter API with the provided prompts."""

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "nousresearch/hermes-3-llama-3.1-405b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=60,
    )
    if response.status_code != 200:
        logger.error(
            "LLM call failed with status %s: %s",
            response.status_code,
            response.text,
        )
        response.raise_for_status()

    body = response.json()
    try:
        return body["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        logger.error("Unexpected LLM response format: %s", body)
        raise RuntimeError("Invalid LLM response structure") from exc


def load_json_list(path: str) -> List[Dict[str, Any]]:
    """Load a JSON list file, returning an empty list if missing or invalid."""

    if not os.path.exists(path):
        logger.warning("JSON list file not found: %s", path)
        return []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
            if isinstance(data, list):
                return data
            logger.warning("Expected list in %s but found %s", path, type(data))
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse JSON list %s: %s", path, exc)
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("Unexpected error reading %s: %s", path, exc)
    return []


def aggregate_feedback(feedback: List[Dict[str, Any]]) -> Dict[str, FeedbackStats]:
    """Aggregate feedback counts per alert type."""

    stats: Dict[str, FeedbackStats] = {}
    for entry in feedback:
        alert_type = entry.get("type") or entry.get("alert_type")
        if not alert_type:
            continue
        if alert_type not in stats:
            stats[alert_type] = FeedbackStats()
        action = str(entry.get("action", "")).lower()
        if action == "approved":
            stats[alert_type].approvals += 1
        elif action == "rejected":
            stats[alert_type].rejections += 1
    return stats


def build_feedback_context(stats: Dict[str, FeedbackStats]) -> str:
    """Convert feedback stats into a textual context for the LLM."""

    if not stats:
        return "No prior analyst feedback on record."

    parts: List[str] = []
    for alert_type, metric in stats.items():
        parts.append(
            f"{alert_type}: {metric.approvals} approved / {metric.rejections} rejected"
        )
    return "; ".join(parts)


def base_risk_and_confidence(alert: Dict[str, Any]) -> Tuple[int, float]:
    """Derive base risk score and confidence from alert severity."""

    severity = str(alert.get("severity", "medium")).lower()
    mapping = {
        "critical": (9, 0.8),
        "high": (8, 0.7),
        "medium": (6, 0.6),
        "low": (4, 0.5),
    }
    return mapping.get(severity, (5, 0.5))


def fallback_summary(alert: Dict[str, Any]) -> str:
    """Generate a deterministic fallback summary when LLM calls fail."""

    return (
        f"Risk Assessment for alert {alert.get('id')}: {alert.get('description')}\n"
        f"Evidence: {json.dumps(alert.get('evidence', {}), indent=2)}"
    )


def create_triage_entry(
    alert: Dict[str, Any],
    feedback_stats: Dict[str, FeedbackStats],
    feedback_context: str,
) -> Dict[str, Any]:
    """Build triage entry for a single alert."""

    alert_type = alert.get("type", "unknown")
    risk_score, base_confidence = base_risk_and_confidence(alert)
    stats = feedback_stats.get(alert_type, FeedbackStats())
    adjusted_confidence, feedback_adjusted = stats.adjust_confidence(base_confidence)

    prompt = (
        "Analyze the following alert and provide a JSON response with keys "
        "risk_score (int 1-10), summary (string), remediation_steps (list of 2-3 strings), "
        "and operational_impact (string).\n"
        f"Alert JSON: {json.dumps(alert, indent=2)}\n"
        f"Current base risk score: {risk_score}\n"
        f"Base confidence: {base_confidence:.2f}\n"
        f"Feedback-adjusted confidence: {adjusted_confidence:.2f}\n"
    )
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(feedback_context=feedback_context)

    try:
        llm_raw = call_llm(prompt=prompt, system_prompt=system_prompt)
        logger.info("LLM responded for alert %s", alert.get("id"))
    except Exception as exc:  # pylint: disable=broad-except
        logger.error("LLM call failed: %s", exc)
        llm_raw = fallback_summary(alert)

    llm_risk_score, summary, remediation_steps = parse_llm_response(llm_raw)
    risk_score_output = llm_risk_score if llm_risk_score is not None else risk_score

    triage_record = {
        "alert_id": alert.get("id"),
        "ai_analysis": {
            "risk_score": int(risk_score_output),
            "summary": summary,
            "remediation_steps": remediation_steps,
            "confidence": round(adjusted_confidence, 2),
            "feedback_adjusted": feedback_adjusted,
            "llm_context": llm_raw,
        },
        "original_alert": alert,
    }
    return triage_record


def parse_llm_response(llm_output: str) -> Tuple[Optional[int], str, List[str]]:
    """Parse LLM output, tolerating JSON or free-form responses."""

    if not llm_output:
        return None, "No analysis provided.", []

    llm_output = llm_output.strip()
    if llm_output.startswith("{"):
        try:
            payload = json.loads(llm_output)
            summary = payload.get("summary") or payload.get("analysis")
            steps = payload.get("remediation_steps") or []
            risk_score = payload.get("risk_score")
            if isinstance(steps, str):
                steps = [steps]
            if isinstance(risk_score, str) and risk_score.isdigit():
                risk_score = int(risk_score)
            return (
                risk_score if isinstance(risk_score, int) else None,
                summary or llm_output,
                list(steps),
            )
        except json.JSONDecodeError:
            logger.warning("LLM output was not valid JSON, falling back to text parse.")

    lines = [line.strip("- ") for line in llm_output.splitlines() if line.strip()]
    summary_lines: List[str] = []
    remediation_steps: List[str] = []

    in_steps = False
    risk_score: Optional[int] = None
    for line in lines:
        lower = line.lower()
        if lower.startswith("risk score"):
            digits = "".join(ch for ch in lower if ch.isdigit())
            if digits:
                risk_score = int(digits)
            summary_lines.append(line)
            continue
        if "remediation" in lower or lower.startswith("1.") or lower.startswith("step"):
            in_steps = True
        if in_steps and lower and lower[0].isdigit():
            remediation_steps.append(line)
        elif in_steps and (line.startswith("-") or line.startswith("•")):
            remediation_steps.append(line.lstrip("-• "))
        else:
            summary_lines.append(line)

    summary = " ".join(summary_lines[:3]) if summary_lines else llm_output
    return risk_score, summary, remediation_steps[:3]


def persist_triage(triage: List[Dict[str, Any]]) -> None:
    """Persist triage data to the configured JSON file."""

    os.makedirs(os.path.dirname(TRIAGE_FILE), exist_ok=True)
    with open(TRIAGE_FILE, "w", encoding="utf-8") as handle:
        json.dump(triage, handle, indent=2)
    logger.info("Wrote %s triage records to %s", len(triage), TRIAGE_FILE)


def main() -> None:
    """Entry point for the agent service."""

    logger.info("Loading alerts from %s", ALERTS_FILE)
    alerts = load_json_list(ALERTS_FILE)
    feedback = load_json_list(FEEDBACK_FILE)
    feedback_stats = aggregate_feedback(feedback)
    feedback_context = build_feedback_context(feedback_stats)

    triage_records: List[Dict[str, Any]] = []
    for alert in alerts:
        triage_records.append(create_triage_entry(alert, feedback_stats, feedback_context))

    persist_triage(triage_records)


if __name__ == "__main__":
    main()
