#!/bin/bash
# Diagnostic script to troubleshoot deployment issues

echo "🔍 AI-Assisted SOC Platform Diagnostics"
echo "========================================"
echo ""

# Check if docker-compose is running
echo "1. Checking Docker Compose services..."
if docker-compose ps > /dev/null 2>&1; then
    docker-compose ps
else
    echo "❌ Docker Compose not running or not in project directory"
    exit 1
fi
echo ""

# Check shared directory
echo "2. Checking shared directory files..."
if [ -d "./shared" ]; then
    echo "✓ shared/ directory exists"
    ls -lh ./shared/
    echo ""
    
    # Check each file
    if [ -f "./shared/alerts.json" ]; then
        ALERTS_SIZE=$(stat -f%z "./shared/alerts.json" 2>/dev/null || stat -c%s "./shared/alerts.json" 2>/dev/null || echo "0")
        echo "✓ alerts.json exists (${ALERTS_SIZE} bytes)"
        if [ "$ALERTS_SIZE" -gt 0 ]; then
            echo "  Preview: $(head -c 200 ./shared/alerts.json)..."
        else
            echo "  ⚠️  File is empty!"
        fi
    else
        echo "❌ alerts.json NOT FOUND"
        echo "   Rules service may have failed. Check: docker-compose logs rules"
    fi
    echo ""
    
    if [ -f "./shared/triage.json" ]; then
        TRIAGE_SIZE=$(stat -f%z "./shared/triage.json" 2>/dev/null || stat -c%s "./shared/triage.json" 2>/dev/null || echo "0")
        echo "✓ triage.json exists (${TRIAGE_SIZE} bytes)"
        if [ "$TRIAGE_SIZE" -gt 0 ]; then
            echo "  Preview: $(head -c 200 ./shared/triage.json)..."
        else
            echo "  ⚠️  File is empty!"
        fi
    else
        echo "❌ triage.json NOT FOUND"
        echo "   Agent service may have failed. Check: docker-compose logs agent"
    fi
    echo ""
    
    if [ -f "./shared/feedback.json" ]; then
        echo "✓ feedback.json exists"
    else
        echo "⚠️  feedback.json NOT FOUND (will be created on first feedback)"
    fi
else
    echo "❌ shared/ directory not found!"
fi
echo ""

# Check environment variables
echo "3. Checking environment configuration..."
if [ -f ".env" ]; then
    echo "✓ .env file exists"
    if grep -q "OPENROUTER_API_KEY=your_openrouter_api_key_here" .env 2>/dev/null; then
        echo "❌ API key not configured! Edit .env file."
    elif grep -q "OPENROUTER_API_KEY=sk-or-" .env 2>/dev/null; then
        echo "✓ API key appears to be configured"
    else
        echo "⚠️  API key may not be set correctly"
    fi
else
    echo "❌ .env file not found! Copy .env.example to .env"
fi
echo ""

# Check service logs for errors
echo "4. Checking service logs for errors..."
echo ""
echo "--- Rules Service (last 10 lines) ---"
docker-compose logs --tail=10 rules 2>/dev/null || echo "Cannot get rules logs"
echo ""
echo "--- Agent Service (last 10 lines) ---"
docker-compose logs --tail=10 agent 2>/dev/null || echo "Cannot get agent logs"
echo ""
echo "--- Web Service (last 10 lines) ---"
docker-compose logs --tail=10 web 2>/dev/null || echo "Cannot get web logs"
echo ""

# Check if web service is accessible
echo "5. Checking web service accessibility..."
if curl -s http://localhost:8080/health > /dev/null 2>&1; then
    echo "✓ Web service is responding at http://localhost:8080"
    HEALTH=$(curl -s http://localhost:8080/health)
    echo "  Health check: $HEALTH"
else
    echo "❌ Web service not accessible at http://localhost:8080"
    echo "   Check if port 8080 is already in use"
fi
echo ""

# Summary
echo "========================================"
echo "📋 Diagnostic Summary"
echo "========================================"
echo ""
echo "Common Issues & Solutions:"
echo ""
echo "1. 'Failed to load alerts' error:"
echo "   → Wait 30-60 seconds after starting services"
echo "   → Check: docker-compose logs agent"
echo "   → Verify API key in .env file"
echo ""
echo "2. Services exit immediately:"
echo "   → This is normal! Rules and agent run once then exit"
echo "   → Check logs to verify they completed successfully"
echo ""
echo "3. API key errors:"
echo "   → Copy .env.example to .env"
echo "   → Add your OpenRouter API key"
echo "   → Rebuild: docker-compose up --build"
echo ""
echo "4. Permission errors:"
echo "   → Check shared/ directory is writable"
echo "   → Run: chmod -R 777 shared/ (for testing)"
echo ""
echo "Need more help? Check README.md or ERRORS_FIXED.md"
