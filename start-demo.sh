#!/bin/bash

echo "======================================================================"
echo "  Energy Sector AI Security Demo - Starting Services"
echo "======================================================================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "ERROR: Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "ERROR: docker-compose is not installed."
    exit 1
fi

echo "✓ Docker is running"
echo "✓ docker-compose is available"
echo ""

# Clean up any existing containers
echo "Cleaning up previous containers..."
docker-compose down > /dev/null 2>&1

# Build and start services
echo "Building and starting services..."
echo ""
docker-compose up --build

echo ""
echo "======================================================================"
echo "  Demo stopped. Run './start-demo.sh' again to restart."
echo "======================================================================"
