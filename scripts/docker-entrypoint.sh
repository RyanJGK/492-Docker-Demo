#!/bin/bash
# Entrypoint script for web service with data pipeline wait logic

set -e

echo "🚀 Starting AI-Assisted SOC Web Service"
echo "=========================================="

# Wait for alerts.json (created by rules service)
ALERTS_FILE="${ALERTS_FILE:-/shared/alerts.json}"
TRIAGE_FILE="${TRIAGE_FILE:-/shared/triage.json}"
FEEDBACK_FILE="${FEEDBACK_FILE:-/shared/feedback.json}"
MAX_WAIT=120  # 2 minutes max wait

echo "📁 Checking data files..."

# Initialize feedback.json if it doesn't exist
if [ ! -f "$FEEDBACK_FILE" ]; then
    echo "[]" > "$FEEDBACK_FILE"
    echo "✓ Initialized $FEEDBACK_FILE"
fi

# Wait for alerts.json
echo "⏳ Waiting for alerts.json (rules service output)..."
WAITED=0
while [ ! -f "$ALERTS_FILE" ] && [ $WAITED -lt $MAX_WAIT ]; do
    if [ $((WAITED % 10)) -eq 0 ]; then
        echo "   Waited ${WAITED}s for $ALERTS_FILE..."
    fi
    sleep 2
    WAITED=$((WAITED + 2))
done

if [ ! -f "$ALERTS_FILE" ]; then
    echo "⚠️  WARNING: $ALERTS_FILE not found after ${MAX_WAIT}s"
    echo "   Rules service may still be running. Web UI will retry automatically."
    echo "   Check logs: docker-compose logs rules"
else
    ALERTS_SIZE=$(stat -c%s "$ALERTS_FILE" 2>/dev/null || stat -f%z "$ALERTS_FILE" 2>/dev/null || echo "0")
    echo "✓ alerts.json found (${ALERTS_SIZE} bytes)"
fi

# Wait for triage.json
echo "⏳ Waiting for triage.json (agent service output)..."
WAITED=0
while [ ! -f "$TRIAGE_FILE" ] && [ $WAITED -lt $MAX_WAIT ]; do
    if [ $((WAITED % 10)) -eq 0 ]; then
        echo "   Waited ${WAITED}s for $TRIAGE_FILE..."
    fi
    sleep 2
    WAITED=$((WAITED + 2))
done

if [ ! -f "$TRIAGE_FILE" ]; then
    echo "⚠️  WARNING: $TRIAGE_FILE not found after ${MAX_WAIT}s"
    echo "   Agent service may still be processing (AI calls can take time)."
    echo "   Web UI will retry automatically."
    echo "   Check logs: docker-compose logs agent"
    echo ""
    echo "   Common causes:"
    echo "   - Missing OPENROUTER_API_KEY in .env"
    echo "   - API rate limits or network issues"
    echo "   - Agent still processing (wait 1-2 minutes total)"
else
    TRIAGE_SIZE=$(stat -c%s "$TRIAGE_FILE" 2>/dev/null || stat -f%z "$TRIAGE_FILE" 2>/dev/null || echo "0")
    echo "✓ triage.json found (${TRIAGE_SIZE} bytes)"
fi

echo ""
echo "✅ Starting Flask web application..."
echo "   Dashboard will be available at: http://localhost:8080"
echo "   If you see 'Failed to load alerts', wait 30-60s and refresh"
echo ""

# Execute the main command (python app.py)
exec "$@"
