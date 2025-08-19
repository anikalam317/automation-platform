#!/usr/bin/env python3
"""
Register new lab instruments and task templates in the automation platform
"""

import requests
import json
import time

BASE_URL = "http://localhost:8001"

def register_services():
    """Register the new instrument services"""
    
    services = [
        {
            "name": "Sample Preparation Station",
            "description": "Automated sample preparation system for pharmaceutical analysis including dilution, pH adjustment, and filtration",
            "type": "http",
            "endpoint": "http://localhost:5002",
            "default_parameters": {
                "volume": 10.0,
                "dilution_factor": 2.0,
                "target_ph": 7.0,
                "timeout": 300
            },
            "enabled": True
        },
        {
            "name": "HPLC Analysis System", 
            "description": "High-Performance Liquid Chromatography system for pharmaceutical compound analysis and purity testing",
            "type": "http",
            "endpoint": "http://localhost:5003",
            "default_parameters": {
                "method": "USP_assay_method",
                "injection_volume": 10.0,
                "runtime_minutes": 20.0,
                "timeout": 1800
            },
            "enabled": True
        }
    ]
    
    registered_services = []
    
    for service in services:
        try:
            response = requests.post(f"{BASE_URL}/api/services/", json=service, timeout=10)
            if response.status_code == 201:
                service_data = response.json()
                print(f"[OK] Registered service: {service['name']} (ID: {service_data['id']})")
                registered_services.append(service_data)
            else:
                print(f"[ERROR] Failed to register {service['name']}: {response.status_code}")
                print(f"   Error: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Connection error registering {service['name']}: {str(e)}")
    
    return registered_services

def register_task_templates():
    """Register task templates for the new instruments"""
    
    task_templates = [
        {
            "name": "Sample Preparation",
            "description": "Automated sample preparation including dilution, pH adjustment, and filtration for analytical testing",
            "category": "preparative",
            "type": "sample_prep",
            "required_service_type": "http",
            "default_parameters": {
                "sample_id": "SAMPLE_001",
                "volume": 10.0,
                "dilution_factor": 2.0,
                "target_ph": 7.0,
                "timeout": 300
            },
            "estimated_duration": 60,
            "enabled": True
        },
        {
            "name": "HPLC Purity Analysis",
            "description": "High-Performance Liquid Chromatography analysis for compound identification and purity determination",
            "category": "analytical", 
            "type": "hplc_analysis",
            "required_service_type": "http",
            "default_parameters": {
                "sample_id": "SAMPLE_001",
                "method": "USP_assay_method",
                "injection_volume": 10.0,
                "runtime_minutes": 20.0,
                "timeout": 1800
            },
            "estimated_duration": 90,
            "enabled": True
        }
    ]
    
    registered_templates = []
    
    for template in task_templates:
        try:
            response = requests.post(f"{BASE_URL}/api/task-templates/", json=template, timeout=10)
            if response.status_code == 201:
                template_data = response.json()
                print(f"[OK] Registered task template: {template['name']} (ID: {template_data['id']})")
                registered_templates.append(template_data)
            else:
                print(f"[ERROR] Failed to register {template['name']}: {response.status_code}")
                print(f"   Error: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Connection error registering {template['name']}: {str(e)}")
    
    return registered_templates

def test_instrument_connections():
    """Test connections to the new instruments"""
    
    instruments = [
        ("Sample Prep Station", "http://localhost:5002/status"),
        ("HPLC System", "http://localhost:5003/status")
    ]
    
    print("\nTesting instrument connections...")
    
    for name, url in instruments:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                status_data = response.json()
                instrument_status = status_data.get('status', 'unknown')
                print(f"[OK] {name}: {instrument_status} (Response: {response.status_code})")
            else:
                print(f"[WARN] {name}: HTTP {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] {name}: Connection failed - {str(e)}")

def verify_backend_connection():
    """Verify backend API is accessible"""
    try:
        response = requests.get(f"{BASE_URL}/api/services/", timeout=5)
        if response.status_code == 200:
            print(f"[OK] Backend API accessible at {BASE_URL}")
            return True
        else:
            print(f"[ERROR] Backend API returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Cannot connect to backend API: {str(e)}")
        return False

def main():
    print("Lab Automation Platform - Instrument Registration")
    print("=" * 55)
    
    # Check backend connection
    if not verify_backend_connection():
        print("\n[ERROR] Cannot proceed without backend connection. Make sure the FastAPI server is running.")
        return
    
    # Test instrument connections
    test_instrument_connections()
    
    print(f"\nRegistering services and task templates...")
    
    # Register services (instruments)
    print(f"\n1. Registering instrument services...")
    services = register_services()
    
    # Register task templates
    print(f"\n2. Registering task templates...")
    templates = register_task_templates()
    
    # Summary
    print(f"\nRegistration Summary:")
    print(f"   Services registered: {len(services)}")
    print(f"   Task templates registered: {len(templates)}")
    
    if services and templates:
        print(f"\n[SUCCESS] Registration completed successfully!")
        print(f"\nNext steps:")
        print(f"   1. Open frontend at http://localhost:3005")
        print(f"   2. Check 'Instruments' tab to see registered instruments")
        print(f"   3. Check 'Builder' tab to see available task templates")
        print(f"   4. Create a workflow: Sample Prep -> HPLC Analysis")
        print(f"   5. Execute and monitor the workflow")
    else:
        print(f"\n[WARN] Some registrations failed. Check the errors above.")

if __name__ == "__main__":
    main()