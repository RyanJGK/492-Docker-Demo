#!/usr/bin/env python3
"""
AI Agent Service for SOC Alert Triage
Uses OpenRouter API to analyze security alerts with feedback learning
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AIAgent:
    """AI agent for security alert triage and analysis"""
    
    def __init__(self, api_key: str, alerts_file: str, triage_file: str, feedback_file: str):
        """
        Initialize AI agent
        
        Args:
            api_key: OpenRouter API key
            alerts_file: Path to alerts.json
            triage_file: Path to output triage.json
            feedback_file: Path to feedback.json
        """
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable not set")
        
        self.api_key = api_key
        self.alerts_file = alerts_file
        self.triage_file = triage_file
        self.feedback_file = feedback_file
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "nousresearch/hermes-3-llama-3.1-405b"
    
    def load_alerts(self) -> List[Dict[str, Any]]:
        """Load alerts from JSON file"""
        try:
            # Wait for alerts file to be created
            max_retries = 10
            retry_count = 0
            
            while not os.path.exists(self.alerts_file) and retry_count < max_retries:
                logger.info(f"Waiting for alerts file... ({retry_count + 1}/{max_retries})")
                time.sleep(2)
                retry_count += 1
            
            if not os.path.exists(self.alerts_file):
                logger.warning(f"Alerts file not found: {self.alerts_file}")
                return []
            
            with open(self.alerts_file, 'r') as f:
                alerts = json.load(f)
            
            logger.info(f"Loaded {len(alerts)} alerts")
            return alerts
        
        except Exception as e:
            logger.error(f"Error loading alerts: {e}")
            return []
    
    def load_feedback(self) -> List[Dict[str, Any]]:
        """Load feedback history from JSON file"""
        try:
            if not os.path.exists(self.feedback_file):
                # Initialize empty feedback file
                with open(self.feedback_file, 'w') as f:
                    json.dump([], f, indent=2)
                logger.info("Initialized empty feedback file")
                return []
            
            with open(self.feedback_file, 'r') as f:
                feedback = json.load(f)
            
            logger.info(f"Loaded {len(feedback)} feedback entries")
            return feedback
        
        except Exception as e:
            logger.error(f"Error loading feedback: {e}")
            return []
    
    def build_feedback_context(self, feedback: List[Dict[str, Any]]) -> str:
        """
        Build context string from feedback history
        
        Args:
            feedback: List of feedback entries
            
        Returns:
            Formatted feedback context string
        """
        if not feedback:
            return "No previous feedback available."
        
        # Take last 20 feedback entries
        recent_feedback = feedback[-20:]
        
        approved = [f for f in recent_feedback if f.get('action') == 'approved']
        rejected = [f for f in recent_feedback if f.get('action') == 'rejected']
        
        context_parts = [
            f"Previous feedback summary: {len(approved)} approved, {len(rejected)} rejected alerts.",
            "\nRecent approved patterns:"
        ]
        
        for entry in approved[-5:]:
            context_parts.append(
                f"  - Alert type: {entry.get('alert_type', 'unknown')}, "
                f"Reason: {entry.get('reason', 'N/A')}"
            )
        
        context_parts.append("\nRecent rejected patterns:")
        for entry in rejected[-5:]:
            context_parts.append(
                f"  - Alert type: {entry.get('alert_type', 'unknown')}, "
                f"Reason: {entry.get('reason', 'N/A')}"
            )
        
        return "\n".join(context_parts)
    
    def call_llm(self, prompt: str, system_prompt: str) -> Optional[str]:
        """
        Call OpenRouter LLM API
        
        Args:
            prompt: User prompt
            system_prompt: System prompt
            
        Returns:
            LLM response or None on error
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        try:
            logger.info("Calling OpenRouter API")
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            logger.info("LLM response received successfully")
            return content
        
        except requests.exceptions.RequestException as e:
            logger.error(f"LLM API call failed: {str(e)}")
            return None
        except KeyError as e:
            logger.error(f"Unexpected API response format: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during LLM call: {str(e)}")
            return None
    
    def analyze_alert(self, alert: Dict[str, Any], feedback_context: str) -> Dict[str, Any]:
        """
        Analyze a single alert using AI
        
        Args:
            alert: Alert dictionary
            feedback_context: Feedback context string
            
        Returns:
            Analysis dictionary
        """
        system_prompt = f"""You are an expert cybersecurity analyst for an energy sector company managing critical infrastructure (SCADA, EMS, power generation/distribution systems).

Your responsibilities:
1. Provide a risk score (1-10) with clear justification
2. Analyze threats in the context of energy sector operations and safety
3. Provide 2-3 specific, actionable remediation steps
4. Consider operational impact (availability is critical for utilities)
5. Prioritize safety and reliability alongside security

{feedback_context}

When similar alert patterns have been approved/rejected previously, adjust your confidence and recommendations accordingly.

Respond in JSON format with the following structure:
{{
  "risk_score": <1-10>,
  "risk_justification": "<explanation>",
  "threat_analysis": "<detailed analysis in energy context>",
  "operational_impact": "<potential impact on operations>",
  "remediation_steps": ["<step1>", "<step2>", "<step3>"],
  "confidence": <0.0-1.0>,
  "feedback_adjusted": <true/false>
}}"""
        
        # Build alert prompt
        prompt = f"""Analyze this security alert:

Alert Type: {alert.get('type')}
Severity: {alert.get('severity')}
Description: {alert.get('description')}

Evidence:
{json.dumps(alert.get('evidence', {}), indent=2)}

Suggested Actions:
{json.dumps(alert.get('suggested_actions', []), indent=2)}

Provide your analysis in JSON format."""
        
        # Call LLM
        response = self.call_llm(prompt, system_prompt)
        
        if not response:
            # Fallback analysis
            logger.warning(f"Using fallback analysis for alert {alert.get('id')}")
            return self._fallback_analysis(alert)
        
        # Parse JSON response
        try:
            # Extract JSON from response (handle markdown code blocks)
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0].strip()
            elif '```' in response:
                response = response.split('```')[1].split('```')[0].strip()
            
            analysis = json.loads(response)
            logger.info(f"Successfully analyzed alert {alert.get('id')}")
            return analysis
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Response was: {response}")
            return self._fallback_analysis(alert)
    
    def _fallback_analysis(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Provide fallback analysis when LLM is unavailable
        
        Args:
            alert: Alert dictionary
            
        Returns:
            Fallback analysis dictionary
        """
        severity_scores = {
            'critical': 9,
            'high': 7,
            'medium': 5,
            'low': 3
        }
        
        risk_score = severity_scores.get(alert.get('severity', 'medium'), 5)
        
        return {
            "risk_score": risk_score,
            "risk_justification": f"{alert.get('severity', 'medium').capitalize()} severity alert detected by rules engine",
            "threat_analysis": f"Alert type: {alert.get('type')}. {alert.get('description', 'Security event detected')}",
            "operational_impact": "Potential impact on critical infrastructure operations",
            "remediation_steps": alert.get('suggested_actions', [])[:3],
            "confidence": 0.6,
            "feedback_adjusted": False
        }
    
    def adjust_confidence_with_feedback(
        self, 
        alert: Dict[str, Any], 
        analysis: Dict[str, Any], 
        feedback: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Adjust confidence based on historical feedback
        
        Args:
            alert: Alert dictionary
            analysis: AI analysis dictionary
            feedback: List of feedback entries
            
        Returns:
            Updated analysis with adjusted confidence
        """
        if not feedback:
            return analysis
        
        alert_type = alert.get('type')
        similar_feedback = [
            f for f in feedback 
            if f.get('alert_type') == alert_type
        ]
        
        if not similar_feedback:
            return analysis
        
        # Calculate approval rate
        approved_count = sum(1 for f in similar_feedback if f.get('action') == 'approved')
        approval_rate = approved_count / len(similar_feedback)
        
        # Adjust confidence based on historical approval rate
        original_confidence = analysis.get('confidence', 0.7)
        adjusted_confidence = (original_confidence + approval_rate) / 2
        
        analysis['confidence'] = round(adjusted_confidence, 2)
        analysis['feedback_adjusted'] = True
        
        logger.info(
            f"Adjusted confidence for {alert_type}: "
            f"{original_confidence:.2f} -> {adjusted_confidence:.2f} "
            f"(approval rate: {approval_rate:.2%})"
        )
        
        return analysis
    
    def triage_alerts(self) -> List[Dict[str, Any]]:
        """
        Triage all alerts with AI analysis
        
        Returns:
            List of triaged alerts
        """
        alerts = self.load_alerts()
        feedback = self.load_feedback()
        
        if not alerts:
            logger.warning("No alerts to triage")
            return []
        
        feedback_context = self.build_feedback_context(feedback)
        triaged_alerts = []
        
        for alert in alerts:
            logger.info(f"Analyzing alert {alert.get('id')} ({alert.get('type')})")
            
            # Analyze with AI
            analysis = self.analyze_alert(alert, feedback_context)
            
            # Adjust confidence based on feedback
            analysis = self.adjust_confidence_with_feedback(alert, analysis, feedback)
            
            # Build triaged alert
            triaged_alert = {
                "alert_id": alert.get('id'),
                "ai_analysis": analysis,
                "original_alert": alert,
                "triage_timestamp": datetime.utcnow().isoformat() + "Z"
            }
            
            triaged_alerts.append(triaged_alert)
        
        logger.info(f"Successfully triaged {len(triaged_alerts)} alerts")
        return triaged_alerts
    
    def save_triage(self, triaged_alerts: List[Dict[str, Any]]) -> None:
        """
        Save triaged alerts to JSON file
        
        Args:
            triaged_alerts: List of triaged alert dictionaries
        """
        try:
            with open(self.triage_file, 'w') as f:
                json.dump(triaged_alerts, f, indent=2)
            
            logger.info(f"Saved {len(triaged_alerts)} triaged alerts to {self.triage_file}")
        
        except Exception as e:
            logger.error(f"Error saving triage results: {e}")
            raise


def main():
    """Main entry point"""
    api_key = os.environ.get('OPENROUTER_API_KEY')
    alerts_file = os.environ.get('ALERTS_FILE', '/shared/alerts.json')
    triage_file = os.environ.get('TRIAGE_FILE', '/shared/triage.json')
    feedback_file = os.environ.get('FEEDBACK_FILE', '/shared/feedback.json')
    
    logger.info("Initializing AI agent")
    logger.info(f"Alerts file: {alerts_file}")
    logger.info(f"Triage file: {triage_file}")
    logger.info(f"Feedback file: {feedback_file}")
    
    try:
        agent = AIAgent(api_key, alerts_file, triage_file, feedback_file)
        triaged_alerts = agent.triage_alerts()
        agent.save_triage(triaged_alerts)
        
        logger.info("AI agent completed successfully")
    
    except Exception as e:
        logger.critical(f"AI agent failed: {e}")
        raise


if __name__ == '__main__':
    main()
