#!/usr/bin/env python3
"""
Automatic Workflow Executor
- Monitors for new workflows
- Maps tasks to services automatically  
- Executes workflows with real-time monitoring
"""

import requests
import json
import time
import sqlite3
from datetime import datetime

BASE_URL = "http://localhost:8001"
DB_PATH = "app/backend/test.db"

# Task name to service mapping
TASK_SERVICE_MAPPING = {
    "Sample Preparation": {
        "service_id": 4,  # Sample Preparation Station
        "endpoint": "http://localhost:5002",
        "action": "prepare",
        "default_params": {
            "volume": 10.0,
            "dilution_factor": 2.0,
            "target_ph": 7.0,
            "timeout": 300
        }
    },
    "HPLC Purity Analysis": {
        "service_id": 5,  # HPLC Analysis System
        "endpoint": "http://localhost:5003", 
        "action": "analyze",
        "default_params": {
            "method": "USP_assay_method",
            "injection_volume": 10.0,
            "runtime_minutes": 20.0,
            "timeout": 1800
        }
    },
    "HPLC Analysis System": {
        "service_id": 5,  # HPLC Analysis System
        "endpoint": "http://localhost:5003",
        "action": "analyze", 
        "default_params": {
            "method": "USP_assay_method",
            "injection_volume": 10.0,
            "runtime_minutes": 20.0,
            "timeout": 1800
        }
    }
}

def fix_workflow_mapping(workflow_id):
    """Fix task-to-service mapping for a workflow"""
    print(f"Fixing workflow {workflow_id} task mappings...")
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Get tasks that need mapping
        cursor.execute("""
            SELECT id, name FROM tasks 
            WHERE workflow_id = ? AND service_id IS NULL
        """, (workflow_id,))
        
        unmapped_tasks = cursor.fetchall()
        
        if not unmapped_tasks:
            print("  No unmapped tasks found")
            return True
        
        print(f"  Found {len(unmapped_tasks)} unmapped tasks")
        
        # Map each task
        for task_id, task_name in unmapped_tasks:
            if task_name in TASK_SERVICE_MAPPING:
                mapping = TASK_SERVICE_MAPPING[task_name]
                service_id = mapping["service_id"]
                
                # Create service parameters with unique sample ID
                params = mapping["default_params"].copy()
                params["sample_id"] = f"AUTO_WF{workflow_id}_TASK{task_id}_{int(time.time())}"
                
                # Update task in database
                cursor.execute("""
                    UPDATE tasks 
                    SET service_id = ?, service_parameters = ?, status = 'pending'
                    WHERE id = ?
                """, (service_id, json.dumps(params), task_id))
                
                print(f"    [OK] Mapped '{task_name}' to service {service_id}")
            else:
                print(f"    [WARN] No mapping for '{task_name}'")
        
        # Reset workflow status
        cursor.execute("UPDATE workflows SET status = 'pending' WHERE id = ?", (workflow_id,))
        
        conn.commit()
        print(f"  Workflow {workflow_id} mapping fixed!")
        return True
        
    except Exception as e:
        print(f"  [ERROR] Failed to fix mapping: {str(e)}")
        return False
    finally:
        conn.close()

def execute_workflow_auto(workflow_id):
    """Automatically execute a workflow"""
    print(f"\n=== Executing Workflow {workflow_id} ===")
    
    # Get workflow details
    response = requests.get(f"{BASE_URL}/api/workflows/{workflow_id}")
    if response.status_code != 200:
        print(f"Failed to get workflow {workflow_id}")
        return False
    
    workflow = response.json()
    tasks = sorted(workflow['tasks'], key=lambda x: x['order_index'])
    
    print(f"Workflow: {workflow['name']}")
    print(f"Tasks: {len(tasks)}")
    
    # Update workflow to running
    requests.put(f"{BASE_URL}/api/workflows/{workflow_id}", json={"status": "running"})
    
    # Execute each task in sequence
    for i, task in enumerate(tasks):
        task_id = task['id']
        task_name = task['name']
        service_id = task['service_id']
        service_parameters = task['service_parameters']
        
        print(f"\n--- Task {i+1}: {task_name} ---")
        
        if not service_id or not service_parameters:
            print(f"[ERROR] Task {task_name} not properly mapped")
            continue
        
        # Parse parameters
        try:
            params = json.loads(service_parameters) if isinstance(service_parameters, str) else service_parameters
        except:
            print(f"[ERROR] Invalid parameters for {task_name}")
            continue
        
        # Get task mapping info
        if task_name not in TASK_SERVICE_MAPPING:
            print(f"[ERROR] No execution mapping for {task_name}")
            continue
        
        mapping = TASK_SERVICE_MAPPING[task_name]
        endpoint = mapping["endpoint"]
        action = mapping["action"]
        
        # Update task to running
        requests.put(f"{BASE_URL}/api/tasks/{task_id}", json={"status": "running"})
        print(f"Starting {task_name}...")
        
        # Execute the task
        success = execute_task(endpoint, action, params, task_id, task_name)
        
        if success:
            print(f"[SUCCESS] {task_name} completed")
        else:
            print(f"[FAILED] {task_name} failed")
            # Mark workflow as failed
            requests.put(f"{BASE_URL}/api/workflows/{workflow_id}", json={"status": "failed"})
            return False
    
    # Mark workflow as completed
    requests.put(f"{BASE_URL}/api/workflows/{workflow_id}", json={"status": "completed"})
    print(f"\n[SUCCESS] Workflow {workflow_id} completed!")
    return True

def execute_task(endpoint, action, params, task_id, task_name):
    """Execute a single task"""
    try:
        # Start the task
        response = requests.post(f"{endpoint}/{action}", json=params)
        if response.status_code != 202:
            print(f"  [ERROR] Failed to start: {response.status_code}")
            if response.status_code == 409:
                # Reset instrument and try again
                print(f"  Resetting instrument...")
                requests.post(f"{endpoint}/reset")
                time.sleep(2)
                response = requests.post(f"{endpoint}/{action}", json=params)
                if response.status_code != 202:
                    return False
        
        print(f"  Task started successfully")
        
        # Monitor progress
        start_time = time.time()
        last_progress = None
        
        while time.time() - start_time < 600:  # 10 minute timeout
            status_response = requests.get(f"{endpoint}/status")
            if status_response.status_code == 200:
                status_data = status_response.json()
                status = status_data.get('status')
                progress = status_data.get('progress_percent')
                
                # Show progress updates
                if progress and progress != last_progress:
                    if progress - (last_progress or 0) >= 20:  # Show every 20%
                        print(f"  Progress: {progress}%")
                        last_progress = progress
                
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
                        requests.put(f"{BASE_URL}/api/tasks/{task_id}", json=task_update)
                        
                        # Show summary
                        if 'results' in results and 'recovery_percent' in results['results']:
                            recovery = results['results']['recovery_percent']
                            print(f"  Completed: {recovery}% recovery")
                        elif 'results' in results and 'summary' in results['results']:
                            purity = results['results']['summary'].get('main_compound_purity', 'N/A')
                            print(f"  Completed: {purity}% purity")
                        else:
                            print(f"  Completed successfully")
                        
                        return True
                
                elif status in ['failed', 'aborted']:
                    requests.put(f"{BASE_URL}/api/tasks/{task_id}", json={"status": "failed"})
                    print(f"  [ERROR] Task {status}")
                    return False
            
            time.sleep(3)
        
        print(f"  [ERROR] Task timeout")
        return False
        
    except Exception as e:
        print(f"  [ERROR] Exception: {str(e)}")
        return False

def process_workflow(workflow_id):
    """Process a workflow: fix mapping and execute"""
    print(f"\n{'='*50}")
    print(f"Processing Workflow {workflow_id}")
    print(f"{'='*50}")
    
    # Fix task mapping
    if not fix_workflow_mapping(workflow_id):
        print(f"Failed to fix workflow {workflow_id}")
        return False
    
    # Execute workflow
    time.sleep(1)  # Brief pause
    return execute_workflow_auto(workflow_id)

def main():
    """Process specific workflow"""
    print("Automatic Workflow Executor")
    print("="*40)
    
    # Process workflow 2 (Test_02)
    success = process_workflow(2)
    
    if success:
        print(f"\n[SUCCESS] Workflow execution completed!")
        print(f"Check the frontend monitor to see real-time updates.")
    else:
        print(f"\n[FAILED] Workflow execution failed!")

if __name__ == "__main__":
    main()