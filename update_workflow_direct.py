#!/usr/bin/env python3
"""
Directly update the workflow in the database to map tasks to services
"""

import sqlite3
import json

# Connect to the database
db_path = "app/backend/test.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def update_workflow_tasks():
    """Update the existing workflow tasks with proper service mappings"""
    
    # Task to service mapping
    task_mappings = {
        "Sample Preparation": {
            "service_id": 4,  # Sample Preparation Station
            "service_parameters": {
                "sample_id": "WORKFLOW_QC_001",
                "volume": 10.0,
                "dilution_factor": 2.0,
                "target_ph": 7.0,
                "timeout": 300
            }
        },
        "HPLC Purity Analysis": {
            "service_id": 5,  # HPLC Analysis System
            "service_parameters": {
                "sample_id": "WORKFLOW_QC_001",
                "method": "USP_assay_method",
                "injection_volume": 10.0,
                "runtime_minutes": 20.0,
                "timeout": 1800
            }
        },
        "HPLC Analysis System": {
            "service_id": 5,  # HPLC Analysis System (duplicate)
            "service_parameters": {
                "sample_id": "WORKFLOW_QC_001",
                "method": "USP_assay_method",
                "injection_volume": 10.0,
                "runtime_minutes": 20.0,
                "timeout": 1800
            }
        }
    }
    
    # Get all tasks from workflow 1
    cursor.execute("SELECT id, name, workflow_id FROM tasks WHERE workflow_id = 1")
    tasks = cursor.fetchall()
    
    print(f"Found {len(tasks)} tasks in workflow 1:")
    
    for task_id, task_name, workflow_id in tasks:
        print(f"  Task {task_id}: {task_name}")
        
        if task_name in task_mappings:
            mapping = task_mappings[task_name]
            service_id = mapping["service_id"]
            service_parameters = json.dumps(mapping["service_parameters"])
            
            # Update the task
            cursor.execute("""
                UPDATE tasks 
                SET service_id = ?, service_parameters = ?, status = 'pending'
                WHERE id = ?
            """, (service_id, service_parameters, task_id))
            
            print(f"    [OK] Mapped to service {service_id}")
        else:
            print(f"    [ERROR] No mapping found")
    
    # Reset workflow status to pending
    cursor.execute("UPDATE workflows SET status = 'pending' WHERE id = 1")
    
    # Commit changes
    conn.commit()
    print(f"\nWorkflow updated successfully!")

def show_current_state():
    """Show the current state of the workflow"""
    cursor.execute("""
        SELECT w.id, w.name, w.status, t.id, t.name, t.service_id, t.status 
        FROM workflows w 
        LEFT JOIN tasks t ON w.id = t.workflow_id 
        WHERE w.id = 1
        ORDER BY t.order_index
    """)
    
    results = cursor.fetchall()
    if not results:
        print("No workflow found with ID 1")
        return
    
    workflow_id, workflow_name, workflow_status = results[0][:3]
    print(f"\nWorkflow: {workflow_name} (ID: {workflow_id}, Status: {workflow_status})")
    print("Tasks:")
    
    for row in results:
        task_id, task_name, service_id, task_status = row[3:]
        if task_id:  # Task exists
            print(f"  - {task_name} (ID: {task_id}, Service: {service_id}, Status: {task_status})")

def main():
    print("Workflow Database Update Tool")
    print("=" * 40)
    
    print("\nCurrent state:")
    show_current_state()
    
    print("\nUpdating task mappings...")
    update_workflow_tasks()
    
    print("\nNew state:")
    show_current_state()
    
    conn.close()
    print("\nDone! The workflow should now be ready for execution.")

if __name__ == "__main__":
    main()