#!/bin/bash

echo "======================================================================"
echo "  Energy Sector AI Security Demo - Setup Validation"
echo "======================================================================"
echo ""

ERRORS=0

# Check Docker
echo "Checking Docker..."
if command -v docker &> /dev/null; then
    echo "  ✓ Docker installed: $(docker --version)"
    if docker info > /dev/null 2>&1; then
        echo "  ✓ Docker daemon is running"
    else
        echo "  ✗ Docker daemon is not running"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "  ✗ Docker not found"
    ERRORS=$((ERRORS + 1))
fi

# Check Docker Compose
echo ""
echo "Checking Docker Compose..."
if command -v docker-compose &> /dev/null; then
    echo "  ✓ docker-compose installed: $(docker-compose --version)"
else
    echo "  ✗ docker-compose not found"
    ERRORS=$((ERRORS + 1))
fi

# Check required directories
echo ""
echo "Checking project structure..."
REQUIRED_DIRS=("data" "rules" "agent" "web" "shared" "web/templates")
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "  ✓ Directory exists: $dir"
    else
        echo "  ✗ Missing directory: $dir"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check required files
echo ""
echo "Checking required files..."
REQUIRED_FILES=(
    "docker-compose.yml"
    "data/auth_events.csv"
    "data/host_inventory.csv"
    "data/vuln_scan.json"
    "data/firewall_logs.csv"
    "rules/Dockerfile"
    "rules/requirements.txt"
    "rules/rules_engine.py"
    "agent/Dockerfile"
    "agent/requirements.txt"
    "agent/agent.py"
    "web/Dockerfile"
    "web/requirements.txt"
    "web/app.py"
    "web/templates/dashboard.html"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ File exists: $file"
    else
        echo "  ✗ Missing file: $file"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check port availability
echo ""
echo "Checking port availability..."
if command -v lsof &> /dev/null; then
    if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "  ⚠ Port 8080 is already in use"
        echo "    You may need to change the port in docker-compose.yml"
    else
        echo "  ✓ Port 8080 is available"
    fi
else
    echo "  ⚠ Cannot check port (lsof not installed)"
fi

# Summary
echo ""
echo "======================================================================"
if [ $ERRORS -eq 0 ]; then
    echo "  ✓ All checks passed! Ready to run the demo."
    echo ""
    echo "  Start the demo with:"
    echo "    ./start-demo.sh"
    echo ""
    echo "  Or manually:"
    echo "    docker-compose up --build"
else
    echo "  ✗ Found $ERRORS error(s). Please fix them before running."
fi
echo "======================================================================"
echo ""

exit $ERRORS
