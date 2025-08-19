#!/usr/bin/env python3
"""
Workflow Execution Daemon
Continuously monitors for new workflows and executes them automatically
"""

import requests
import json
import time
import sqlite3
import threading
from datetime import datetime

BASE_URL = "http://backend:8001"
DB_PATH = "app/backend/test.db"

# Task name to service mapping
TASK_SERVICE_MAPPING = {
    "Sample Preparation": {
        "service_id": 4,
        "endpoint": "http://sample-prep-station:5002",
        "action": "prepare",
        "default_params": {
            "volume": 10.0,
            "dilution_factor": 2.0,
            "target_ph": 7.0,
            "timeout": 300
        }
    },
    "HPLC Purity Analysis": {
        "service_id": 5,
        "endpoint": "http://hplc-system:5003",
        "action": "analyze",
        "default_params": {
            "method": "USP_assay_method",
            "injection_volume": 10.0,
            "runtime_minutes": 20.0,
            "timeout": 1800
        }
    },
    "HPLC Analysis System": {
        "service_id": 5,
        "endpoint": "http://hplc-system:5003",
        "action": "analyze",
        "default_params": {
            "method": "USP_assay_method",
            "injection_volume": 10.0,
            "runtime_minutes": 20.0,
            "timeout": 1800
        }
    }
}

class WorkflowExecutionDaemon:
    def __init__(self):
        self.running = False
        self.processed_workflows = set()
        
    def start(self):
        """Start the daemon"""
        self.running = True
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Workflow Execution Daemon started")
        print("Monitoring for new workflows to execute...")
        
        while self.running:
            try:
                self.check_and_process_workflows()
                time.sleep(5)  # Check every 5 seconds
            except KeyboardInterrupt:
                print("\nShutting down daemon...")
                break
            except Exception as e:
                print(f"[ERROR] Daemon error: {str(e)}")
                time.sleep(10)
    
    def check_and_process_workflows(self):
        """Check for workflows that need processing"""
        try:
            # Get all workflows
            response = requests.get(f"{BASE_URL}/api/workflows/", timeout=5)
            if response.status_code != 200:
                return
            
            workflows = response.json()
            
            for workflow in workflows:
                workflow_id = workflow['id']
                workflow_status = workflow['status']
                
                # Skip if already processed
                if workflow_id in self.processed_workflows:
                    continue
                
                # Only process running workflows 
                if workflow_status == 'running':
                    if self.has_unmapped_tasks(workflow):
                        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Found new workflow with unmapped tasks: {workflow['name']} (ID: {workflow_id})")
                        self.process_workflow(workflow_id)
                        self.processed_workflows.add(workflow_id)
                    elif self.has_pending_tasks(workflow):
                        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Found running workflow with pending tasks: {workflow['name']} (ID: {workflow_id})")
                        self.execute_workflow_direct(workflow_id)
                        self.processed_workflows.add(workflow_id)
                
        except requests.exceptions.RequestException:
            # Silently ignore connection errors
            pass
    
    def has_unmapped_tasks(self, workflow):
        """Check if workflow has tasks without service mapping"""
        for task in workflow.get('tasks', []):
            if not task.get('service_id'):
                return True
        return False
    
    def has_pending_tasks(self, workflow):
        """Check if workflow has tasks that are pending execution"""
        for task in workflow.get('tasks', []):
            if task.get('service_id') and task.get('status') == 'pending':
                return True
        return False
    
    def execute_workflow_direct(self, workflow_id):
        """Execute workflow directly without mapping (tasks already mapped)"""
        thread = threading.Thread(target=self.execute_workflow_async, args=(workflow_id,))
        thread.daemon = True
        thread.start()
    
    def process_workflow(self, workflow_id):
        """Process a workflow: map tasks and execute"""
        print(f"Processing workflow {workflow_id}...")
        
        # Fix task mapping
        if not self.fix_workflow_mapping(workflow_id):
            print(f"  [ERROR] Failed to fix mapping for workflow {workflow_id}")
            return
        
        # Execute workflow in background thread
        thread = threading.Thread(target=self.execute_workflow_async, args=(workflow_id,))
        thread.daemon = True
        thread.start()
    
    def fix_workflow_mapping(self, workflow_id):
        """Fix task-to-service mapping for a workflow"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Get unmapped tasks
            cursor.execute("""
                SELECT id, name FROM tasks 
                WHERE workflow_id = ? AND service_id IS NULL
            """, (workflow_id,))
            
            unmapped_tasks = cursor.fetchall()
            
            if not unmapped_tasks:
                return True
            
            print(f"  Mapping {len(unmapped_tasks)} tasks...")
            
            # Map each task
            for task_id, task_name in unmapped_tasks:
                if task_name in TASK_SERVICE_MAPPING:
                    mapping = TASK_SERVICE_MAPPING[task_name]
                    service_id = mapping["service_id"]
                    
                    # Create service parameters
                    params = mapping["default_params"].copy()
                    params["sample_id"] = f"AUTO_WF{workflow_id}_T{task_id}_{int(time.time())}"
                    
                    # Update task
                    cursor.execute("""
                        UPDATE tasks 
                        SET service_id = ?, service_parameters = ?, status = 'pending'
                        WHERE id = ?
                    """, (service_id, json.dumps(params), task_id))
                    
                    print(f"    Mapped '{task_name}' to service {service_id}")
            
            conn.commit()
            conn.close()
            print(f"  Task mapping completed for workflow {workflow_id}")
            return True
            
        except Exception as e:
            print(f"  [ERROR] Mapping failed: {str(e)}")
            return False
    
    def execute_workflow_async(self, workflow_id):
        """Execute workflow asynchronously"""
        try:
            print(f"  Starting execution of workflow {workflow_id}...")
            
            # Get workflow details
            response = requests.get(f"{BASE_URL}/api/workflows/{workflow_id}")
            if response.status_code != 200:
                return
            
            workflow = response.json()
            tasks = sorted(workflow['tasks'], key=lambda x: x['order_index'])
            
            # Execute each task
            for i, task in enumerate(tasks):
                task_id = task['id']
                task_name = task['name']
                service_id = task['service_id']
                service_parameters = task['service_parameters']
                
                if not service_id or not service_parameters:
                    continue
                
                print(f"    Executing: {task_name}")
                
                # Parse parameters
                try:
                    params = json.loads(service_parameters) if isinstance(service_parameters, str) else service_parameters
                except:
                    continue
                
                # Get task mapping
                if task_name not in TASK_SERVICE_MAPPING:
                    continue
                
                mapping = TASK_SERVICE_MAPPING[task_name]
                endpoint = mapping["endpoint"]
                action = mapping["action"]
                
                # Update task to running
                requests.put(f"{BASE_URL}/api/tasks/{task_id}", json={"status": "running"})
                
                # Execute task
                success = self.execute_task(endpoint, action, params, task_id, task_name)
                
                if not success:
                    print(f"    [FAILED] {task_name}")
                    requests.put(f"{BASE_URL}/api/workflows/{workflow_id}", json={"status": "failed"})
                    return
                
                print(f"    [SUCCESS] {task_name}")
            
            # Mark workflow as completed
            requests.put(f"{BASE_URL}/api/workflows/{workflow_id}", json={"status": "completed"})
            print(f"  [COMPLETED] Workflow {workflow_id}: {workflow['name']}")
            
        except Exception as e:
            print(f"  [ERROR] Execution failed: {str(e)}")
    
    def execute_task(self, endpoint, action, params, task_id, task_name):
        """Execute a single task"""
        try:
            # Start the task
            response = requests.post(f"{endpoint}/{action}", json=params, timeout=10)
            if response.status_code != 202:
                # Try resetting instrument if busy
                if response.status_code == 409:
                    requests.post(f"{endpoint}/reset")
                    time.sleep(2)
                    response = requests.post(f"{endpoint}/{action}", json=params, timeout=10)
                    if response.status_code != 202:
                        return False
                else:
                    return False
            
            # Monitor until completion
            start_time = time.time()
            while time.time() - start_time < 300:  # 5 minute timeout
                try:
                    status_response = requests.get(f"{endpoint}/status", timeout=5)
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get('status')
                        
                        if status == 'completed':
                            # Get results
                            results_response = requests.get(f"{endpoint}/results", timeout=5)
                            if results_response.status_code == 200:
                                results = results_response.json()
                                
                                # Update task
                                task_update = {"status": "completed", "results": results}
                                requests.put(f"{BASE_URL}/api/tasks/{task_id}", json=task_update, timeout=5)
                                return True
                        
                        elif status in ['failed', 'aborted']:
                            requests.put(f"{BASE_URL}/api/tasks/{task_id}", json={"status": "failed"}, timeout=5)
                            return False
                    
                    time.sleep(3)
                except requests.exceptions.RequestException:
                    time.sleep(5)
            
            return False
            
        except Exception as e:
            print(f"      Task error: {str(e)}")
            return False

def main():
    print("=" * 60)
    print("WORKFLOW EXECUTION DAEMON")
    print("=" * 60)
    print("This service will automatically:")
    print("• Monitor for new workflows") 
    print("• Map tasks to services")
    print("• Execute workflows in real-time")
    print("• Update status in the database")
    print()
    print("Now any workflow you create in the frontend will")
    print("automatically execute within seconds!")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    daemon = WorkflowExecutionDaemon()
    daemon.start()

if __name__ == "__main__":
    main()