#!/usr/bin/env python3
"""
Simple Laboratory Setup Script

This script initializes the laboratory automation system by:
1. Loading instrument and task definitions
2. Synchronizing with the database
3. Checking connections

Usage: python setup_lab.py
"""

import json
import requests
from pathlib import Path

def main():
    print("Laboratory Automation Framework - Setup")
    print("=" * 50)
    
    # Check if definitions exist
    definitions_path = Path("instrument_definitions")
    if not definitions_path.exists():
        print("ERROR: instrument_definitions directory not found!")
        return
    
    # Count definitions
    instruments = list(definitions_path.glob("[!task_]*.json"))
    tasks = list(definitions_path.glob("task_*.json"))
    
    print(f"Found {len(instruments)} instrument definitions")
    print(f"Found {len(tasks)} task definitions")
    
    # Try to sync with database
    try:
        response = requests.get("http://localhost:8001", timeout=3)
        print("Backend API is running")
        
        # Sync to database
        sync_response = requests.post(
            "http://localhost:8001/api/instrument-management/sync-to-database",
            timeout=10
        )
        
        if sync_response.status_code == 200:
            print("Successfully synced definitions to database")
        else:
            print("Sync to database failed")
            
    except requests.exceptions.RequestException:
        print("Backend API not available - start with 'docker compose up'")
    
    print("\nSetup complete!")
    print("Next steps:")
    print("1. Start system: docker compose -f compose_v1.yml up -d")
    print("2. Open frontend: http://localhost:3005")
    print("3. Manage instruments: http://localhost:3005/manage-instruments")

if __name__ == "__main__":
    main()