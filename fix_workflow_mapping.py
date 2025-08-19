#!/usr/bin/env python3
"""
Fix the workflow by mapping tasks to the correct services
"""

import requests
import json

BASE_URL = "http://localhost:8001"

def get_workflow():
    """Get the current workflow"""
    response = requests.get(f"{BASE_URL}/api/workflows/1")
    if response.status_code == 200:
        return response.json()
    return None

def update_task_service_mapping():
    """Update tasks to map them to the correct services"""
    
    # First, let's stop the workflow and restart it properly
    try:
        # Stop the workflow
        response = requests.post(f"{BASE_URL}/api/workflows/1/stop")
        print(f"Stopped workflow: {response.status_code}")
    except:
        pass
    
    # Task-to-service mapping based on our registration
    task_service_mapping = {
        "Sample Preparation": {
            "service_id": 4,  # Sample Preparation Station
            "service_parameters": {
                "sample_id": "WORKFLOW_SAMPLE_001",
                "volume": 10.0,
                "dilution_factor": 2.0,
                "target_ph": 7.0,
                "timeout": 300
            }
        },
        "HPLC Purity Analysis": {
            "service_id": 5,  # HPLC Analysis System  
            "service_parameters": {
                "sample_id": "WORKFLOW_SAMPLE_001",
                "method": "USP_assay_method",
                "injection_volume": 10.0,
                "runtime_minutes": 20.0,
                "timeout": 1800
            }
        },
        "HPLC Analysis System": {
            "service_id": 5,  # HPLC Analysis System (duplicate?)
            "service_parameters": {
                "sample_id": "WORKFLOW_SAMPLE_001", 
                "method": "USP_assay_method",
                "injection_volume": 10.0,
                "runtime_minutes": 20.0,
                "timeout": 1800
            }
        }
    }
    
    # Get workflow details
    workflow = get_workflow()
    if not workflow:
        print("Could not get workflow details")
        return False
    
    print(f"Updating workflow: {workflow['name']}")
    print(f"Tasks found: {len(workflow['tasks'])}")
    
    # Update each task with service mapping
    updated_tasks = 0
    for task in workflow['tasks']:
        task_name = task['name']
        task_id = task['id']
        
        if task_name in task_service_mapping:
            mapping = task_service_mapping[task_name]
            
            # Update task in database (we'll use direct database update)
            update_data = {
                "service_id": mapping["service_id"],
                "service_parameters": mapping["service_parameters"],
                "status": "pending"
            }
            
            print(f"Updating task '{task_name}' (ID: {task_id}) with service {mapping['service_id']}")
            # Note: We'd need a direct SQL update or a new API endpoint for this
            updated_tasks += 1
        else:
            print(f"No mapping found for task: {task_name}")
    
    return updated_tasks > 0

def create_new_workflow():
    """Create a new workflow with proper task-service mapping"""
    workflow_data = {
        "name": "Pharmaceutical QC Analysis",
        "author": "Lab Automation System", 
        "tasks": [
            {
                "name": "Sample Preparation",
                "service_id": 4,
                "service_parameters": {
                    "sample_id": "QC_SAMPLE_002",
                    "volume": 10.0,
                    "dilution_factor": 2.0,
                    "target_ph": 7.0,
                    "timeout": 300
                }
            },
            {
                "name": "HPLC Purity Analysis", 
                "service_id": 5,
                "service_parameters": {
                    "sample_id": "QC_SAMPLE_002",
                    "method": "USP_assay_method",
                    "injection_volume": 10.0,
                    "runtime_minutes": 20.0,
                    "timeout": 1800
                }
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/api/workflows/", json=workflow_data)
    if response.status_code == 201:
        workflow = response.json()
        print(f"Created new workflow: {workflow['name']} (ID: {workflow['id']})")
        return workflow
    else:
        print(f"Failed to create workflow: {response.status_code}")
        print(response.text)
        return None

def manual_workflow_execution():
    """Manually trigger workflow execution using the coordinator"""
    
    # First, let's manually trigger the task execution by calling the services directly
    print("\nManually executing workflow tasks...")
    
    # Task 1: Sample Preparation
    print("1. Starting Sample Preparation...")
    prep_params = {
        "sample_id": "MANUAL_QC_001",
        "volume": 10.0,
        "dilution_factor": 2.0,
        "target_ph": 7.0
    }
    
    response = requests.post("http://localhost:5002/prepare", json=prep_params)
    if response.status_code == 202:
        print("   Sample preparation started successfully")
        
        # Wait for completion (polling)
        import time
        while True:
            status_response = requests.get("http://localhost:5002/status")
            if status_response.status_code == 200:
                status = status_response.json().get('status')
                print(f"   Status: {status}")
                if status == 'completed':
                    results_response = requests.get("http://localhost:5002/results")
                    if results_response.status_code == 200:
                        results = results_response.json()
                        print(f"   Sample prep completed: {results['results']['recovery_percent']}% recovery")
                    break
                elif status in ['failed', 'aborted']:
                    print(f"   Sample preparation {status}")
                    break
            time.sleep(5)
    else:
        print(f"   Failed to start sample preparation: {response.status_code}")
        return
    
    # Task 2: HPLC Analysis  
    print("\n2. Starting HPLC Analysis...")
    hplc_params = {
        "sample_id": "MANUAL_QC_001",
        "method": "USP_assay_method",
        "injection_volume": 10.0,
        "runtime_minutes": 15.0
    }
    
    response = requests.post("http://localhost:5003/analyze", json=hplc_params)
    if response.status_code == 202:
        print("   HPLC analysis started successfully")
        
        # Wait for completion (polling)
        while True:
            status_response = requests.get("http://localhost:5003/status")
            if status_response.status_code == 200:
                status = status_response.json().get('status')
                print(f"   Status: {status}")
                if status == 'completed':
                    results_response = requests.get("http://localhost:5003/results")
                    if results_response.status_code == 200:
                        results = results_response.json()
                        purity = results['results']['summary']['main_compound_purity']
                        print(f"   HPLC analysis completed: {purity}% purity")
                    break
                elif status in ['failed', 'aborted']:
                    print(f"   HPLC analysis {status}")
                    break
            time.sleep(10)
    else:
        print(f"   Failed to start HPLC analysis: {response.status_code}")

def main():
    print("Workflow Execution Fix Tool")
    print("=" * 40)
    
    choice = input("\nChoose option:\n1. Manual workflow execution (Direct)\n2. Create new workflow with proper mapping\n3. Both\nEnter choice (1/2/3): ")
    
    if choice in ['1', '3']:
        print("\n=== Manual Workflow Execution ===")
        manual_workflow_execution()
    
    if choice in ['2', '3']:
        print("\n=== Creating New Workflow ===")
        create_new_workflow()
    
    print("\nDone!")

if __name__ == "__main__":
    main()