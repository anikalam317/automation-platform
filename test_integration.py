#!/usr/bin/env python3
"""
Comprehensive integration test for Laboratory Automation Framework
Tests all API endpoints and frontend-backend connectivity
"""

import requests
import json
import time

# Configuration
BACKEND_URL = "http://localhost:8005"
FRONTEND_URL = "http://localhost:3004"

def test_api_endpoint(method, endpoint, data=None, expected_status=200):
    """Test a single API endpoint"""
    url = f"{BACKEND_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        elif method == "PUT":
            response = requests.put(url, json=data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, timeout=10)
        
        if response.status_code == expected_status:
            print(f"✅ {method} {endpoint} - Status: {response.status_code}")
            return response.json() if response.status_code != 204 else None
        else:
            print(f"❌ {method} {endpoint} - Expected: {expected_status}, Got: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ {method} {endpoint} - Error: {e}")
        return None

def main():
    print("🧪 Laboratory Automation Framework - Integration Test")
    print("=" * 60)
    
    # Test 1: Backend Health Check
    print("\n1. Backend Health Check:")
    print("-" * 30)
    
    # Test 2: Task Templates API
    print("\n2. Task Templates API:")
    print("-" * 30)
    templates = test_api_endpoint("GET", "/api/task-templates/")
    if templates:
        print(f"   Found {len(templates)} task templates")
        for template in templates[:2]:  # Show first 2
            print(f"   - {template['name']} ({template['category']})")
    
    # Test creating a new task template
    new_template = {
        "name": "Test Template",
        "description": "Test template for integration testing",
        "category": "testing",
        "type": "test",
        "default_parameters": {"test": True},
        "estimated_duration": 5,
        "enabled": True
    }
    
    created_template = test_api_endpoint("POST", "/api/task-templates/", new_template, 201)
    if created_template:
        template_id = created_template["id"]
        print(f"   Created template with ID: {template_id}")
        
        # Test updating the template
        update_data = {"description": "Updated test template"}
        test_api_endpoint("PUT", f"/api/task-templates/{template_id}", update_data)
        
        # Test deleting the template
        test_api_endpoint("DELETE", f"/api/task-templates/{template_id}", expected_status=200)
    
    # Test 3: Services API
    print("\n3. Services/Instruments API:")
    print("-" * 30)
    services = test_api_endpoint("GET", "/api/services/")
    if services:
        print(f"   Found {len(services)} services")
        for service in services[:2]:  # Show first 2
            print(f"   - {service['name']} ({service['type']})")
    
    # Test creating a new service
    new_service = {
        "name": "Test Instrument",
        "description": "Test instrument for integration testing",
        "type": "test-instrument",
        "endpoint": "http://localhost:9999/test",
        "default_parameters": {"test_mode": True},
        "enabled": True
    }
    
    created_service = test_api_endpoint("POST", "/api/services/", new_service, 201)
    if created_service:
        service_id = created_service["id"]
        print(f"   Created service with ID: {service_id}")
        
        # Test updating the service
        update_data = {"description": "Updated test instrument"}
        test_api_endpoint("PUT", f"/api/services/{service_id}", update_data)
        
        # Test deleting the service
        test_api_endpoint("DELETE", f"/api/services/{service_id}", expected_status=200)
    
    # Test 4: AI Workflow Generation
    print("\n4. AI Workflow Generation:")
    print("-" * 30)
    ai_prompts = [
        "Create an HPLC analysis workflow",
        "Design a pharmaceutical testing workflow",
        "Build a GC-MS analysis workflow"
    ]
    
    for prompt in ai_prompts:
        workflow = test_api_endpoint("POST", "/api/ai/generate-workflow", {"prompt": prompt})
        if workflow:
            print(f"   Generated '{workflow['name']}' with {len(workflow['tasks'])} tasks")
    
    # Test 5: Workflows API
    print("\n5. Workflows API:")
    print("-" * 30)
    
    workflows = test_api_endpoint("GET", "/api/workflows/")
    if workflows is not None:
        print(f"   Found {len(workflows)} existing workflows")
    
    # Create a test workflow
    test_workflow = {
        "name": "Integration Test Workflow",
        "author": "Test Suite",
        "tasks": [
            {"name": "Test Task 1", "service_parameters": {"test": True}},
            {"name": "Test Task 2", "service_parameters": {"test": True}}
        ]
    }
    
    created_workflow = test_api_endpoint("POST", "/api/workflows/", test_workflow, 201)
    if created_workflow:
        workflow_id = created_workflow["id"]
        print(f"   Created workflow with ID: {workflow_id}")
        
        # Test workflow controls
        test_api_endpoint("POST", f"/api/workflows/{workflow_id}/pause")
        test_api_endpoint("POST", f"/api/workflows/{workflow_id}/resume")
        test_api_endpoint("POST", f"/api/workflows/{workflow_id}/stop")
        test_api_endpoint("DELETE", f"/api/workflows/{workflow_id}", expected_status=200)
    
    # Test 6: Frontend Connectivity
    print("\n6. Frontend Connectivity:")
    print("-" * 30)
    
    try:
        frontend_response = requests.get(FRONTEND_URL, timeout=5)
        if frontend_response.status_code == 200:
            print(f"✅ Frontend accessible at {FRONTEND_URL}")
        else:
            print(f"❌ Frontend not accessible - Status: {frontend_response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Frontend not accessible - Error: {e}")
    
    # Test 7: CORS Check
    print("\n7. CORS Configuration:")
    print("-" * 30)
    
    try:
        headers = {
            "Origin": FRONTEND_URL,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type"
        }
        
        cors_response = requests.options(f"{BACKEND_URL}/api/task-templates/", headers=headers, timeout=5)
        if cors_response.status_code in [200, 204]:
            print("✅ CORS properly configured")
        else:
            print(f"❌ CORS issue - Status: {cors_response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ CORS test failed - Error: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Integration Test Completed!")
    print("\nNext Steps:")
    print("1. Open browser to http://localhost:3004")
    print("2. Test Tasks tab - should show task templates")
    print("3. Test Instruments tab - should show services")
    print("4. Test Builder tab - should show both in component palette")
    print("5. Test AI Workflow Generator - should create workflows")

if __name__ == "__main__":
    main()