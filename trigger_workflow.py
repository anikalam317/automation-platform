#!/usr/bin/env python3
"""
Manually trigger workflow execution by calling the workflow coordinator
"""

import sys
import os
sys.path.append('app/backend/src')

from laf.workflows.coordinator import WorkflowCoordinator
import time

def trigger_workflow_execution():
    """Manually trigger the workflow execution"""
    
    print("Triggering workflow execution...")
    
    # Create coordinator instance
    coordinator = WorkflowCoordinator()
    
    # Simulate workflow insertion event for workflow ID 1
    workflow_data = {
        "workflow_id": 1,
        "operation": "INSERT"
    }
    
    print("Calling coordinator.handle_workflow_change()...")
    coordinator.handle_workflow_change(workflow_data)
    
    print("Workflow execution triggered!")

def mock_celery_task_execution():
    """Mock the Celery task execution without Redis"""
    
    print("Starting mock task execution (no Celery/Redis)...")
    
    # We'll directly call the launch_service function logic
    import requests
    import json
    
    # Get the workflow tasks
    response = requests.get("http://localhost:8001/api/workflows/1")
    if response.status_code == 200:
        workflow = response.json()
        tasks = workflow['tasks']
        
        print(f"Workflow: {workflow['name']}")
        print(f"Tasks: {len(tasks)}")
        
        # Execute tasks in order
        for i, task in enumerate(sorted(tasks, key=lambda x: x['order_index'])):
            task_id = task['id']
            task_name = task['name']
            service_id = task['service_id']
            service_parameters = task['service_parameters']
            
            if not service_id:
                print(f"Task {task_name} has no service mapping")
                continue
            
            print(f"\nExecuting Task {i+1}: {task_name}")
            print(f"Service ID: {service_id}")
            
            # Get service details
            service_response = requests.get(f"http://localhost:8001/api/services/{service_id}")
            if service_response.status_code == 200:
                service = service_response.json()
                endpoint = service['endpoint']
                
                print(f"Service: {service['name']} ({endpoint})")
                
                # Update task status to running
                task_update = {"status": "running"}
                requests.put(f"http://localhost:8001/api/tasks/{task_id}", json=task_update)
                
                # Execute the service call
                if service_id == 4:  # Sample Prep Station
                    execute_sample_prep(endpoint, service_parameters, task_id)
                elif service_id == 5:  # HPLC System
                    execute_hplc_analysis(endpoint, service_parameters, task_id)
                
                time.sleep(2)  # Brief pause between tasks
            else:
                print(f"Failed to get service details for service {service_id}")

def execute_sample_prep(endpoint, parameters, task_id):
    """Execute sample preparation task"""
    print("  Starting sample preparation...")
    
    prep_params = json.loads(parameters) if isinstance(parameters, str) else parameters
    
    # Start preparation
    response = requests.post(f"{endpoint}/prepare", json=prep_params)
    if response.status_code == 202:
        print("  Sample preparation started")
        
        # Monitor until completion
        while True:
            status_response = requests.get(f"{endpoint}/status")
            if status_response.status_code == 200:
                status = status_response.json().get('status')
                if status == 'completed':
                    # Get results
                    results_response = requests.get(f"{endpoint}/results")
                    if results_response.status_code == 200:
                        results = results_response.json()
                        
                        # Update task with results
                        task_update = {
                            "status": "completed",
                            "results": results
                        }
                        requests.put(f"http://localhost:8001/api/tasks/{task_id}", json=task_update)
                        print(f"  Sample prep completed: {results['results']['recovery_percent']}% recovery")
                    break
                elif status in ['failed', 'aborted']:
                    task_update = {"status": "failed"}
                    requests.put(f"http://localhost:8001/api/tasks/{task_id}", json=task_update)
                    print(f"  Sample preparation {status}")
                    break
            time.sleep(3)
    else:
        print(f"  Failed to start sample preparation: {response.status_code}")

def execute_hplc_analysis(endpoint, parameters, task_id):
    """Execute HPLC analysis task"""
    print("  Starting HPLC analysis...")
    
    hplc_params = json.loads(parameters) if isinstance(parameters, str) else parameters
    
    # Start analysis
    response = requests.post(f"{endpoint}/analyze", json=hplc_params)
    if response.status_code == 202:
        print("  HPLC analysis started")
        
        # Monitor until completion
        while True:
            status_response = requests.get(f"{endpoint}/status")
            if status_response.status_code == 200:
                status = status_response.json().get('status')
                if status == 'completed':
                    # Get results
                    results_response = requests.get(f"{endpoint}/results")
                    if results_response.status_code == 200:
                        results = results_response.json()
                        
                        # Update task with results
                        task_update = {
                            "status": "completed",
                            "results": results
                        }
                        requests.put(f"http://localhost:8001/api/tasks/{task_id}", json=task_update)
                        purity = results['results']['summary']['main_compound_purity']
                        print(f"  HPLC analysis completed: {purity}% purity")
                    break
                elif status in ['failed', 'aborted']:
                    task_update = {"status": "failed"}
                    requests.put(f"http://localhost:8001/api/tasks/{task_id}", json=task_update)
                    print(f"  HPLC analysis {status}")
                    break
            time.sleep(5)
    else:
        print(f"  Failed to start HPLC analysis: {response.status_code}")

def update_workflow_status():
    """Update workflow status to completed"""
    workflow_update = {"status": "completed"}
    response = requests.put("http://localhost:8001/api/workflows/1", json=workflow_update)
    if response.status_code == 200:
        print("\nWorkflow marked as completed!")

def main():
    print("Workflow Execution Trigger")
    print("=" * 30)
    
    # Execute the workflow
    mock_celery_task_execution()
    
    # Update workflow status
    update_workflow_status()
    
    print("\nWorkflow execution completed!")
    print("Check the frontend monitor to see the results.")

if __name__ == "__main__":
    main()