#!/usr/bin/env python3
"""
Simple workflow execution - execute the mapped workflow tasks
"""

import requests
import json
import time

BASE_URL = "http://localhost:8001"

def execute_workflow():
    """Execute the workflow by calling services directly"""
    
    print("Executing Workflow: Pharmaceutical QC Analysis")
    print("=" * 50)
    
    # Get the workflow
    response = requests.get(f"{BASE_URL}/api/workflows/1")
    if response.status_code != 200:
        print("Failed to get workflow")
        return
    
    workflow = response.json()
    tasks = sorted(workflow['tasks'], key=lambda x: x['order_index'])
    
    print(f"Workflow: {workflow['name']}")
    print(f"Status: {workflow['status']}")
    print(f"Tasks: {len(tasks)}")
    
    # Update workflow to running
    requests.put(f"{BASE_URL}/api/workflows/1", json={"status": "running"})
    
    # Execute each task
    for i, task in enumerate(tasks):
        task_id = task['id']
        task_name = task['name']
        service_id = task['service_id']
        service_parameters = task['service_parameters']
        
        print(f"\n--- Task {i+1}: {task_name} ---")
        
        if not service_id:
            print(f"❌ No service mapping for {task_name}")
            continue
        
        # Get service details
        service_response = requests.get(f"{BASE_URL}/api/services/{service_id}")
        if service_response.status_code != 200:
            print(f"❌ Failed to get service {service_id}")
            continue
        
        service = service_response.json()
        endpoint = service['endpoint']
        
        print(f"Service: {service['name']}")
        print(f"Endpoint: {endpoint}")
        
        # Update task to running
        requests.put(f"{BASE_URL}/api/tasks/{task_id}", json={"status": "running"})
        
        # Execute based on service type
        success = False
        if service_id == 4:  # Sample Prep
            success = execute_sample_prep(endpoint, service_parameters, task_id)
        elif service_id == 5:  # HPLC
            success = execute_hplc_analysis(endpoint, service_parameters, task_id)
        
        if not success:
            print(f"❌ Task {task_name} failed")
            # Update workflow to failed
            requests.put(f"{BASE_URL}/api/workflows/1", json={"status": "failed"})
            return
        
        print(f"✅ Task {task_name} completed")
    
    # Mark workflow as completed
    requests.put(f"{BASE_URL}/api/workflows/1", json={"status": "completed"})
    print(f"\n🎉 Workflow completed successfully!")

def execute_sample_prep(endpoint, parameters, task_id):
    """Execute sample preparation"""
    try:
        params = json.loads(parameters) if isinstance(parameters, str) else parameters
        
        # Start preparation
        response = requests.post(f"{endpoint}/prepare", json=params)
        if response.status_code != 202:
            print(f"Failed to start preparation: {response.status_code}")
            return False
        
        print("Sample preparation started...")
        
        # Monitor progress
        start_time = time.time()
        while time.time() - start_time < 300:  # 5 minute timeout
            status_response = requests.get(f"{endpoint}/status")
            if status_response.status_code == 200:
                status_data = status_response.json()
                status = status_data.get('status')
                
                if 'progress_percent' in status_data:
                    progress = status_data['progress_percent']
                    print(f"  Progress: {progress}%")
                
                if status == 'completed':
                    # Get results
                    results_response = requests.get(f"{endpoint}/results")
                    if results_response.status_code == 200:
                        results = results_response.json()
                        
                        # Update task
                        task_update = {
                            "status": "completed",
                            "results": results
                        }
                        requests.put(f"http://localhost:8001/api/tasks/{task_id}", json=task_update)
                        
                        recovery = results['results']['recovery_percent']
                        print(f"  ✅ Sample prep completed: {recovery}% recovery")
                        return True
                
                elif status in ['failed', 'aborted']:
                    requests.put(f"http://localhost:8001/api/tasks/{task_id}", json={"status": "failed"})
                    print(f"  ❌ Sample preparation {status}")
                    return False
            
            time.sleep(3)
        
        print("  ❌ Sample preparation timeout")
        return False
        
    except Exception as e:
        print(f"  ❌ Error in sample prep: {str(e)}")
        return False

def execute_hplc_analysis(endpoint, parameters, task_id):
    """Execute HPLC analysis"""
    try:
        params = json.loads(parameters) if isinstance(parameters, str) else parameters
        
        # Start analysis
        response = requests.post(f"{endpoint}/analyze", json=params)
        if response.status_code != 202:
            print(f"Failed to start analysis: {response.status_code}")
            return False
        
        print("HPLC analysis started...")
        
        # Monitor progress
        start_time = time.time()
        while time.time() - start_time < 600:  # 10 minute timeout
            status_response = requests.get(f"{endpoint}/status")
            if status_response.status_code == 200:
                status_data = status_response.json()
                status = status_data.get('status')
                
                if 'progress_percent' in status_data:
                    progress = status_data['progress_percent']
                    print(f"  Progress: {progress}%")
                
                if status == 'completed':
                    # Get results
                    results_response = requests.get(f"{endpoint}/results")
                    if results_response.status_code == 200:
                        results = results_response.json()
                        
                        # Update task
                        task_update = {
                            "status": "completed", 
                            "results": results
                        }
                        requests.put(f"http://localhost:8001/api/tasks/{task_id}", json=task_update)
                        
                        purity = results['results']['summary']['main_compound_purity']
                        print(f"  ✅ HPLC analysis completed: {purity}% purity")
                        return True
                
                elif status in ['failed', 'aborted']:
                    requests.put(f"http://localhost:8001/api/tasks/{task_id}", json={"status": "failed"})
                    print(f"  ❌ HPLC analysis {status}")
                    return False
            
            time.sleep(5)
        
        print("  ❌ HPLC analysis timeout")
        return False
        
    except Exception as e:
        print(f"  ❌ Error in HPLC analysis: {str(e)}")
        return False

if __name__ == "__main__":
    execute_workflow()