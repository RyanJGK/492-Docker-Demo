#!/bin/bash
# Wait for data pipeline to complete before starting web service

set -e

echo "🔍 Waiting for data pipeline to complete..."

# Wait for alerts.json (created by rules service)
ALERTS_FILE="${ALERTS_FILE:-/shared/alerts.json}"
TRIAGE_FILE="${TRIAGE_FILE:-/shared/triage.json}"
MAX_WAIT=120  # 2 minutes max wait
WAITED=0

echo "⏳ Waiting for alerts.json..."
while [ ! -f "$ALERTS_FILE" ] && [ $WAITED -lt $MAX_WAIT ]; do
    sleep 2
    WAITED=$((WAITED + 2))
    echo "   Waited ${WAITED}s for $ALERTS_FILE..."
done

if [ ! -f "$ALERTS_FILE" ]; then
    echo "❌ ERROR: $ALERTS_FILE not found after ${MAX_WAIT}s"
    echo "   The rules service may have failed. Check logs: docker-compose logs rules"
    exit 1
fi

echo "✓ alerts.json found!"

echo "⏳ Waiting for triage.json..."
WAITED=0
while [ ! -f "$TRIAGE_FILE" ] && [ $WAITED -lt $MAX_WAIT ]; do
    sleep 2
    WAITED=$((WAITED + 2))
    echo "   Waited ${WAITED}s for $TRIAGE_FILE..."
done

if [ ! -f "$TRIAGE_FILE" ]; then
    echo "❌ ERROR: $TRIAGE_FILE not found after ${MAX_WAIT}s"
    echo "   The agent service may have failed. Check logs: docker-compose logs agent"
    echo "   Common causes:"
    echo "   - Missing or invalid OPENROUTER_API_KEY"
    echo "   - Network connectivity issues"
    echo "   - API rate limits"
    exit 1
fi

echo "✓ triage.json found!"

# Verify files are not empty
ALERTS_SIZE=$(stat -f%z "$ALERTS_FILE" 2>/dev/null || stat -c%s "$ALERTS_FILE" 2>/dev/null || echo "0")
TRIAGE_SIZE=$(stat -f%z "$TRIAGE_FILE" 2>/dev/null || stat -c%s "$TRIAGE_FILE" 2>/dev/null || echo "0")

echo "📊 File sizes:"
echo "   alerts.json: ${ALERTS_SIZE} bytes"
echo "   triage.json: ${TRIAGE_SIZE} bytes"

if [ "$ALERTS_SIZE" -lt 10 ]; then
    echo "⚠️  WARNING: alerts.json is very small or empty"
fi

if [ "$TRIAGE_SIZE" -lt 10 ]; then
    echo "⚠️  WARNING: triage.json is very small or empty"
fi

echo "✅ Data pipeline complete! Starting web service..."
exec "$@"
