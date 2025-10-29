#!/usr/bin/env python3
"""
Flask Web Dashboard for Energy Sector Security Demo
Displays triage results and enables analyst feedback
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
from datetime import datetime

app = Flask(__name__)

# Paths to shared data
TRIAGE_FILE = '/shared/triage.json'
FEEDBACK_FILE = '/shared/feedback.json'


def load_triage():
    """Load triage results"""
    if not os.path.exists(TRIAGE_FILE):
        return []
    
    with open(TRIAGE_FILE, 'r') as f:
        return json.load(f)


def load_feedback():
    """Load analyst feedback"""
    if not os.path.exists(FEEDBACK_FILE):
        return {}
    
    with open(FEEDBACK_FILE, 'r') as f:
        return json.load(f)


def save_feedback(feedback):
    """Save analyst feedback"""
    with open(FEEDBACK_FILE, 'w') as f:
        json.dump(feedback, f, indent=2)


@app.route('/')
def dashboard():
    """Main dashboard view"""
    triage_data = load_triage()
    feedback_data = load_feedback()
    
    # Merge feedback into triage data
    for item in triage_data:
        alert_id = item['alert_id']
        if alert_id in feedback_data:
            item['analyst_decision'] = feedback_data[alert_id]['decision']
            item['analyst_notes'] = feedback_data[alert_id].get('notes', '')
            item['decision_timestamp'] = feedback_data[alert_id]['timestamp']
    
    # Calculate statistics
    total_alerts = len(triage_data)
    severity_counts = {
        'CRITICAL': 0,
        'HIGH': 0,
        'MEDIUM': 0,
        'LOW': 0
    }
    status_counts = {
        'pending_review': 0,
        'approved': 0,
        'rejected': 0
    }
    
    for item in triage_data:
        severity_counts[item['severity']] = severity_counts.get(item['severity'], 0) + 1
        
        if item.get('analyst_decision') == 'approved':
            status_counts['approved'] += 1
        elif item.get('analyst_decision') == 'rejected':
            status_counts['rejected'] += 1
        else:
            status_counts['pending_review'] += 1
    
    stats = {
        'total': total_alerts,
        'severity': severity_counts,
        'status': status_counts
    }
    
    return render_template('dashboard.html', 
                          triage=triage_data, 
                          stats=stats,
                          current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """Handle analyst feedback (approve/reject)"""
    data = request.json
    alert_id = data.get('alert_id')
    decision = data.get('decision')  # 'approved' or 'rejected'
    notes = data.get('notes', '')
    
    if not alert_id or decision not in ['approved', 'rejected']:
        return jsonify({'error': 'Invalid request'}), 400
    
    # Load existing feedback
    feedback_data = load_feedback()
    
    # Add new feedback
    feedback_data[alert_id] = {
        'decision': decision,
        'notes': notes,
        'timestamp': datetime.now().isoformat()
    }
    
    # Save feedback
    save_feedback(feedback_data)
    
    return jsonify({'success': True, 'alert_id': alert_id, 'decision': decision})


@app.route('/api/stats')
def get_stats():
    """Get current statistics"""
    triage_data = load_triage()
    feedback_data = load_feedback()
    
    stats = {
        'total_alerts': len(triage_data),
        'reviewed': len(feedback_data),
        'pending': len(triage_data) - len(feedback_data)
    }
    
    return jsonify(stats)


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'web-dashboard'})


if __name__ == '__main__':
    print("=" * 60)
    print("Starting Energy Sector Security Dashboard")
    print("=" * 60)
    print("Dashboard available at: http://localhost:8080")
    print("=" * 60)
    app.run(host='0.0.0.0', port=8080, debug=True)
