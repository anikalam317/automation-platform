#!/usr/bin/env python3
"""
Laboratory Instrument Initialization Script

This script initializes laboratory instruments by:
1. Loading instrument definitions from instrument_definitions/
2. Synchronizing them with the database
3. Setting up initial instrument configurations
4. Validating instrument connections

Usage:
    python initialize_instruments.py
    python initialize_instruments.py --sync-only  # Only sync to database
    python initialize_instruments.py --check-connections  # Check instrument connectivity
"""

import json
import os
import sys
import argparse
import requests
from pathlib import Path
from typing import Dict, List, Any
import time

def load_instrument_definitions() -> List[Dict[str, Any]]:
    """Load all instrument definitions from the instrument_definitions directory"""
    definitions_path = Path("instrument_definitions")
    instruments = []
    
    if not definitions_path.exists():
        print(f"ERROR: {definitions_path} directory not found!")
        print("Please make sure you're running this script from the project root directory.")
        return []
    
    print(f"Loading instrument definitions from {definitions_path}/")
    
    for file_path in definitions_path.glob("*.json"):
        # Skip task definitions
        if file_path.name.startswith("task_"):
            continue
            
        try:
            with open(file_path, 'r') as f:
                instrument = json.load(f)
                instruments.append(instrument)
                print(f"  [OK] Loaded: {instrument['name']} ({instrument['id']})")
        except Exception as e:
            print(f"  [ERROR] Error loading {file_path}: {e}")
    
    return instruments

def load_task_definitions() -> List[Dict[str, Any]]:
    """Load all task definitions from the instrument_definitions directory"""
    definitions_path = Path("instrument_definitions")
    tasks = []
    
    print(f"🔍 Loading task definitions from {definitions_path}/")
    
    for file_path in definitions_path.glob("task_*.json"):
        try:
            with open(file_path, 'r') as f:
                task = json.load(f)
                tasks.append(task)
                print(f"  ✅ Loaded: {task['name']} ({task['id']})")
        except Exception as e:
            print(f"  ❌ Error loading {file_path}: {e}")
    
    return tasks

def sync_to_database(api_url: str = "http://localhost:8001") -> bool:
    """Sync instrument and task definitions to the database"""
    print(f"🔄 Synchronizing definitions to database at {api_url}")
    
    try:
        # Check if API is available
        health_response = requests.get(f"{api_url}", timeout=5)
        if health_response.status_code != 200:
            print(f"❌ Backend API not available at {api_url}")
            return False
        
        # Sync definitions
        sync_response = requests.post(f"{api_url}/api/instrument-management/sync-to-database", timeout=10)
        if sync_response.status_code == 200:
            result = sync_response.json()
            print(f"  ✅ {result['message']}")
            return True
        else:
            error_data = sync_response.json() if sync_response.headers.get('content-type', '').startswith('application/json') else {}
            print(f"  ❌ Sync failed: {error_data.get('detail', 'Unknown error')}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Connection error: {e}")
        return False

def check_instrument_connections(instruments: List[Dict[str, Any]]) -> Dict[str, bool]:
    """Check connectivity to instrument simulation endpoints"""
    print("🔗 Checking instrument connections...")
    
    connection_status = {}
    
    for instrument in instruments:
        instrument_id = instrument['id']
        connection = instrument.get('connection', {})
        endpoint = connection.get('simulation_endpoint')
        
        if not endpoint:
            print(f"  ⚠️  {instrument['name']}: No simulation endpoint configured")
            connection_status[instrument_id] = False
            continue
        
        try:
            # Try to connect to the status endpoint
            status_endpoint = endpoint + connection.get('status_endpoint', '/status')
            response = requests.get(status_endpoint, timeout=3)
            
            if response.status_code == 200:
                print(f"  ✅ {instrument['name']}: Connected ({endpoint})")
                connection_status[instrument_id] = True
            else:
                print(f"  ❌ {instrument['name']}: HTTP {response.status_code} ({endpoint})")
                connection_status[instrument_id] = False
                
        except requests.exceptions.RequestException as e:
            print(f"  ❌ {instrument['name']}: Connection failed - {e}")
            connection_status[instrument_id] = False
    
    return connection_status

def create_sample_instrument() -> None:
    """Create a sample instrument definition for demonstration"""
    definitions_path = Path("instrument_definitions")
    sample_path = definitions_path / "sample_instrument.json"
    
    if sample_path.exists():
        print("  ℹ️  Sample instrument already exists")
        return
    
    sample_instrument = {
        "id": "sample-instrument",
        "name": "Sample Lab Instrument",
        "category": "analytical",
        "manufacturer": "Example Corp",
        "model": "Model X1000",
        "description": "Sample laboratory instrument for demonstration purposes",
        "capabilities": [
            "Basic analysis",
            "Quality control",
            "Data collection"
        ],
        "parameters": {
            "sample_id": {
                "type": "string",
                "label": "Sample ID",
                "default": "auto-generated",
                "required": True
            },
            "analysis_type": {
                "type": "select",
                "label": "Analysis Type",
                "options": ["standard", "detailed", "quick"],
                "default": "standard",
                "required": True
            },
            "timeout": {
                "type": "number",
                "label": "Timeout (seconds)",
                "min": 60,
                "max": 600,
                "default": 300,
                "required": False
            }
        },
        "connection": {
            "type": "http",
            "simulation_endpoint": "http://sample-instrument:5010",
            "real_endpoint": None,
            "status_endpoint": "/status",
            "execute_endpoint": "/analyze",
            "results_endpoint": "/results",
            "reset_endpoint": "/reset"
        },
        "validation": {
            "calibration_required": True,
            "maintenance_schedule": "monthly"
        },
        "outputs": {
            "analysis_results": True,
            "quality_metrics": True,
            "raw_data": True
        },
        "typical_runtime_seconds": 120,
        "status": "active",
        "created_by": "system",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z"
    }
    
    with open(sample_path, 'w') as f:
        json.dump(sample_instrument, f, indent=2)
    
    print(f"  ✅ Created sample instrument: {sample_path}")

def display_summary(instruments: List[Dict[str, Any]], tasks: List[Dict[str, Any]], 
                   connection_status: Dict[str, bool] = None) -> None:
    """Display a summary of loaded instruments and tasks"""
    print("\n" + "="*60)
    print("🧪 LABORATORY AUTOMATION FRAMEWORK - INSTRUMENT SUMMARY")
    print("="*60)
    
    print(f"\n📋 INSTRUMENTS LOADED: {len(instruments)}")
    for instrument in instruments:
        status_icon = "🟢" if connection_status and connection_status.get(instrument['id']) else "🔴" if connection_status else "⚪"
        print(f"  {status_icon} {instrument['name']} ({instrument['category']})")
        print(f"     ID: {instrument['id']}")
        print(f"     Capabilities: {len(instrument.get('capabilities', []))}")
        if instrument.get('connection', {}).get('simulation_endpoint'):
            print(f"     Endpoint: {instrument['connection']['simulation_endpoint']}")
        print()
    
    print(f"\n📝 TASKS LOADED: {len(tasks)}")
    for task in tasks:
        print(f"  📌 {task['name']} ({task['category']})")
        print(f"     ID: {task['id']}")
        print(f"     Compatible Instruments: {len(task.get('compatible_instruments', []))}")
        print(f"     Estimated Duration: {task.get('estimated_duration_seconds', 0)}s")
        print()
    
    if connection_status:
        connected = sum(1 for status in connection_status.values() if status)
        total = len(connection_status)
        print(f"\n🔗 CONNECTION STATUS: {connected}/{total} instruments connected")
    
    print("\n" + "="*60)
    print("🚀 Ready for laboratory automation!")
    print("   • Manage instruments: http://localhost:3005/manage-instruments")
    print("   • Manage tasks: http://localhost:3005/manage-tasks") 
    print("   • Build workflows: http://localhost:3005/builder")
    print("="*60)

def main():
    parser = argparse.ArgumentParser(description='Initialize Laboratory Instruments')
    parser.add_argument('--sync-only', action='store_true', 
                       help='Only sync definitions to database')
    parser.add_argument('--check-connections', action='store_true',
                       help='Check instrument connectivity')
    parser.add_argument('--api-url', default='http://localhost:8001',
                       help='Backend API URL (default: http://localhost:8001)')
    parser.add_argument('--create-sample', action='store_true',
                       help='Create a sample instrument definition')
    
    args = parser.parse_args()
    
    print("*** Laboratory Automation Framework - Instrument Initialization ***")
    print("=" * 60)
    
    # Create sample instrument if requested
    if args.create_sample:
        print("📝 Creating sample instrument definition...")
        create_sample_instrument()
        print()
    
    # Load definitions
    instruments = load_instrument_definitions()
    tasks = load_task_definitions()
    
    if not instruments and not tasks:
        print("❌ No instrument or task definitions found!")
        sys.exit(1)
    
    print(f"\n✅ Loaded {len(instruments)} instruments and {len(tasks)} tasks")
    
    connection_status = None
    
    # Check connections if requested
    if args.check_connections:
        connection_status = check_instrument_connections(instruments)
        print()
    
    # Sync to database unless sync-only is specified
    if not args.sync_only or True:  # Always try to sync
        success = sync_to_database(args.api_url)
        if success:
            print("✅ Database synchronization completed")
        else:
            print("⚠️  Database synchronization failed - check if backend is running")
        print()
    
    # Display summary
    display_summary(instruments, tasks, connection_status)
    
    print("\n🎯 Next Steps:")
    print("1. Start the system: docker compose -f compose_v1.yml up -d")
    print("2. Open frontend: http://localhost:3005")
    print("3. Manage instruments: /manage-instruments")
    print("4. Create workflows: /builder")

if __name__ == "__main__":
    main()