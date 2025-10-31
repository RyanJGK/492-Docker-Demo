#!/usr/bin/env python3
"""
Flask Web UI for AI-Assisted SOC Platform
Provides dashboard for alert triage and feedback collection
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

from flask import Flask, render_template, jsonify, request

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Configuration
TRIAGE_FILE = os.environ.get('TRIAGE_FILE', '/shared/triage.json')
FEEDBACK_FILE = os.environ.get('FEEDBACK_FILE', '/shared/feedback.json')
ALERTS_FILE = os.environ.get('ALERTS_FILE', '/shared/alerts.json')


def load_json_file(filepath: str, default: Any = None) -> Any:
    """
    Load JSON file with error handling
    
    Args:
        filepath: Path to JSON file
        default: Default value if file doesn't exist or is invalid
        
    Returns:
        Parsed JSON data or default value
    """
    try:
        # Wait for file if it doesn't exist yet
        # Increased timeout for AI processing (can take 30-60+ seconds)
        max_retries = 30
        retry_count = 0
        
        while not os.path.exists(filepath) and retry_count < max_retries:
            logger.info(f"Waiting for {filepath}... ({retry_count + 1}/{max_retries})")
            time.sleep(2)
            retry_count += 1
        
        if not os.path.exists(filepath):
            logger.warning(f"File not found after {max_retries * 2} seconds: {filepath}")
            return default if default is not None else []
        
        # Check if file is empty or still being written
        file_size = os.path.getsize(filepath)
        if file_size == 0:
            logger.warning(f"File is empty: {filepath}")
            return default if default is not None else []
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        logger.info(f"Successfully loaded {filepath} ({file_size} bytes)")
        return data
    
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {filepath}: {e}")
        return default if default is not None else []
    except Exception as e:
        logger.error(f"Error loading {filepath}: {e}")
        return default if default is not None else []


def save_json_file(filepath: str, data: Any) -> bool:
    """
    Save data to JSON file
    
    Args:
        filepath: Path to JSON file
        data: Data to save
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving to {filepath}: {e}")
        return False


@app.route('/')
def dashboard():
    """Render main dashboard"""
    return render_template('dashboard.html')


@app.route('/api/alerts')
def get_alerts():
    """
    Get all triaged alerts
    
    Returns:
        JSON response with triaged alerts
    """
    try:
        triaged_alerts = load_json_file(TRIAGE_FILE, [])
        
        # Sort by risk score (descending) and timestamp
        triaged_alerts.sort(
            key=lambda x: (
                -x.get('ai_analysis', {}).get('risk_score', 0),
                x.get('triage_timestamp', '')
            ),
            reverse=False
        )
        
        return jsonify({
            'status': 'success',
            'count': len(triaged_alerts),
            'alerts': triaged_alerts
        })
    
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'alerts': []
        }), 500


@app.route('/api/feedback', methods=['GET'])
def get_feedback():
    """
    Get feedback history
    
    Returns:
        JSON response with feedback entries
    """
    try:
        feedback = load_json_file(FEEDBACK_FILE, [])
        
        # Sort by timestamp (most recent first)
        feedback.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return jsonify({
            'status': 'success',
            'count': len(feedback),
            'feedback': feedback
        })
    
    except Exception as e:
        logger.error(f"Error fetching feedback: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'feedback': []
        }), 500


@app.route('/feedback', methods=['POST'])
def submit_feedback():
    """
    Submit feedback for an alert
    
    Expected JSON payload:
    {
        "alert_id": "uuid",
        "action": "approved" | "rejected",
        "reason": "explanation text",
        "alert_type": "alert type" (optional, will be extracted from triage)
    }
    
    Returns:
        JSON response with status
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400
        
        # Validate required fields
        alert_id = data.get('alert_id')
        action = data.get('action')
        reason = data.get('reason', '').strip()
        
        if not alert_id:
            return jsonify({
                'status': 'error',
                'message': 'alert_id is required'
            }), 400
        
        if action not in ['approved', 'rejected']:
            return jsonify({
                'status': 'error',
                'message': 'action must be "approved" or "rejected"'
            }), 400
        
        if not reason:
            return jsonify({
                'status': 'error',
                'message': 'reason is required'
            }), 400
        
        # Get alert type from triage data
        alert_type = data.get('alert_type')
        if not alert_type:
            triaged_alerts = load_json_file(TRIAGE_FILE, [])
            for alert in triaged_alerts:
                if alert.get('alert_id') == alert_id:
                    alert_type = alert.get('original_alert', {}).get('type', 'unknown')
                    break
        
        # Load existing feedback
        feedback = load_json_file(FEEDBACK_FILE, [])
        
        # Create feedback entry
        feedback_entry = {
            'alert_id': alert_id,
            'action': action,
            'reason': reason,
            'alert_type': alert_type or 'unknown',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'analyst': data.get('analyst', 'anonymous')
        }
        
        # Append and save
        feedback.append(feedback_entry)
        
        if not save_json_file(FEEDBACK_FILE, feedback):
            return jsonify({
                'status': 'error',
                'message': 'Failed to save feedback'
            }), 500
        
        logger.info(
            f"Feedback received: {action} for alert {alert_id} - {reason}"
        )
        
        return jsonify({
            'status': 'success',
            'message': f'Feedback {action} recorded',
            'feedback': feedback_entry
        })
    
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/stats')
def get_stats():
    """
    Get statistics about alerts and feedback
    
    Returns:
        JSON response with statistics
    """
    try:
        triaged_alerts = load_json_file(TRIAGE_FILE, [])
        feedback = load_json_file(FEEDBACK_FILE, [])
        
        # Alert statistics
        alert_counts = {
            'total': len(triaged_alerts),
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0
        }
        
        alert_types = {}
        risk_scores = []
        
        for alert in triaged_alerts:
            severity = alert.get('original_alert', {}).get('severity', 'unknown')
            if severity in alert_counts:
                alert_counts[severity] += 1
            
            alert_type = alert.get('original_alert', {}).get('type', 'unknown')
            alert_types[alert_type] = alert_types.get(alert_type, 0) + 1
            
            risk_score = alert.get('ai_analysis', {}).get('risk_score', 0)
            risk_scores.append(risk_score)
        
        # Feedback statistics
        feedback_counts = {
            'total': len(feedback),
            'approved': sum(1 for f in feedback if f.get('action') == 'approved'),
            'rejected': sum(1 for f in feedback if f.get('action') == 'rejected')
        }
        
        feedback_by_type = {}
        for f in feedback:
            alert_type = f.get('alert_type', 'unknown')
            if alert_type not in feedback_by_type:
                feedback_by_type[alert_type] = {'approved': 0, 'rejected': 0}
            
            action = f.get('action', 'unknown')
            if action in ['approved', 'rejected']:
                feedback_by_type[alert_type][action] += 1
        
        # Calculate average risk score
        avg_risk_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0
        
        return jsonify({
            'status': 'success',
            'alerts': alert_counts,
            'alert_types': alert_types,
            'feedback': feedback_counts,
            'feedback_by_type': feedback_by_type,
            'average_risk_score': round(avg_risk_score, 2),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
    
    except Exception as e:
        logger.error(f"Error generating stats: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })


if __name__ == '__main__':
    logger.info("Starting Flask web application")
    logger.info(f"Triage file: {TRIAGE_FILE}")
    logger.info(f"Feedback file: {FEEDBACK_FILE}")
    
    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 8080)),
        debug=os.environ.get('DEBUG', 'False').lower() == 'true'
    )
