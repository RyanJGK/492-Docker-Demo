#!/usr/bin/env python3
"""
Validation script to verify the AI-Assisted SOC Demo Platform setup
Tests all components without requiring Docker or API keys
"""

import json
import os
import sys
from pathlib import Path

def check_file_exists(filepath: str, description: str) -> bool:
    """Check if a file exists"""
    if Path(filepath).exists():
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description} MISSING: {filepath}")
        return False

def check_directory_exists(dirpath: str, description: str) -> bool:
    """Check if a directory exists"""
    if Path(dirpath).is_dir():
        print(f"✓ {description}: {dirpath}")
        return True
    else:
        print(f"✗ {description} MISSING: {dirpath}")
        return False

def validate_json_file(filepath: str) -> bool:
    """Validate JSON file can be parsed"""
    try:
        with open(filepath, 'r') as f:
            json.load(f)
        return True
    except Exception as e:
        print(f"  ⚠ Error parsing {filepath}: {e}")
        return False

def main():
    print("=" * 60)
    print("AI-Assisted SOC Demo Platform - Validation Script")
    print("=" * 60)
    print()
    
    results = []
    
    # Check directory structure
    print("Checking directory structure...")
    results.append(check_directory_exists("data", "Data directory"))
    results.append(check_directory_exists("rules", "Rules directory"))
    results.append(check_directory_exists("agent", "Agent directory"))
    results.append(check_directory_exists("web", "Web directory"))
    results.append(check_directory_exists("web/templates", "Templates directory"))
    results.append(check_directory_exists("shared", "Shared directory"))
    print()
    
    # Check data files
    print("Checking data files...")
    data_files = [
        ("data/auth_events.csv", "Authentication events"),
        ("data/host_inventory.csv", "Host inventory"),
        ("data/firewall_logs.csv", "Firewall logs"),
        ("data/vuln_scan.json", "Vulnerability scans"),
        ("data/splunk_events.json", "Splunk events")
    ]
    for filepath, desc in data_files:
        exists = check_file_exists(filepath, desc)
        results.append(exists)
        if exists and filepath.endswith('.json'):
            validate_json_file(filepath)
    print()
    
    # Check Python files
    print("Checking Python application files...")
    results.append(check_file_exists("rules/detect.py", "Detection rules engine"))
    results.append(check_file_exists("agent/agent.py", "AI agent service"))
    results.append(check_file_exists("web/app.py", "Flask web application"))
    print()
    
    # Check requirements files
    print("Checking requirements files...")
    results.append(check_file_exists("rules/requirements.txt", "Rules requirements"))
    results.append(check_file_exists("agent/requirements.txt", "Agent requirements"))
    results.append(check_file_exists("web/requirements.txt", "Web requirements"))
    print()
    
    # Check Dockerfiles
    print("Checking Dockerfiles...")
    results.append(check_file_exists("rules/Dockerfile", "Rules Dockerfile"))
    results.append(check_file_exists("agent/Dockerfile", "Agent Dockerfile"))
    results.append(check_file_exists("web/Dockerfile", "Web Dockerfile"))
    print()
    
    # Check Docker Compose files
    print("Checking Docker Compose configuration...")
    results.append(check_file_exists("docker-compose.yml", "Docker Compose (dev)"))
    results.append(check_file_exists("docker-compose.prod.yml", "Docker Compose (prod)"))
    print()
    
    # Check configuration files
    print("Checking configuration files...")
    results.append(check_file_exists(".env.example", "Environment example"))
    results.append(check_file_exists(".gitignore", "Git ignore"))
    print()
    
    # Check web templates
    print("Checking web templates...")
    results.append(check_file_exists("web/templates/dashboard.html", "Dashboard template"))
    print()
    
    # Check documentation
    print("Checking documentation...")
    results.append(check_file_exists("README.md", "README documentation"))
    print()
    
    # Check shared directory initialized
    print("Checking shared directory...")
    results.append(check_file_exists("shared/feedback.json", "Feedback file"))
    if Path("shared/feedback.json").exists():
        validate_json_file("shared/feedback.json")
    print()
    
    # Summary
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    percentage = (passed / total) * 100
    
    print(f"Validation Results: {passed}/{total} checks passed ({percentage:.1f}%)")
    print("=" * 60)
    
    if passed == total:
        print()
        print("✓ ALL CHECKS PASSED!")
        print()
        print("Your AI-Assisted SOC Demo Platform is ready to run.")
        print()
        print("Next steps:")
        print("1. Copy .env.example to .env and add your OpenRouter API key")
        print("2. Run: docker-compose up --build")
        print("3. Open: http://localhost:8080")
        print()
        return 0
    else:
        print()
        print("⚠ Some checks failed. Please review the errors above.")
        print()
        return 1

if __name__ == '__main__':
    sys.exit(main())
