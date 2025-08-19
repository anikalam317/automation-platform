#!/usr/bin/env python3
"""
Process test_03 workflow specifically
"""

import requests
import json
import time
import sqlite3

BASE_URL = "http://localhost:8001"
DB_PATH = "app/backend/test.db"

def fix_workflow_3():
    """Fix workflow 3 task mappings"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Map Sample Preparation (task 6) to service 4
        cursor.execute("""
            UPDATE tasks 
            SET service_id = 4, service_parameters = ?, status = 'pending'
            WHERE id = 6
        """, (json.dumps({
            "sample_id": "TEST03_SAMPLE_001",
            "volume": 10.0,
            "dilution_factor": 2.0,
            "target_ph": 7.0,
            "timeout": 300
        }),))
        
        # Map HPLC Analysis System (task 7) to service 5
        cursor.execute("""
            UPDATE tasks 
            SET service_id = 5, service_parameters = ?, status = 'pending'
            WHERE id = 7
        """, (json.dumps({
            "sample_id": "TEST03_SAMPLE_001",
            "method": "USP_assay_method",
            "injection_volume": 10.0,
            "runtime_minutes": 20.0,
            "timeout": 1800
        }),))
        
        # Reset workflow status
        cursor.execute("UPDATE workflows SET status = 'pending' WHERE id = 3")
        
        conn.commit()
        print("Workflow 3 task mappings fixed!")
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return False
    finally:
        conn.close()

def execute_workflow_3():
    """Execute workflow 3"""
    print("Executing test_03 workflow...")
    
    # Update workflow to running
    requests.put(f"{BASE_URL}/api/workflows/3", json={"status": "running"})
    
    # Task 1: Sample Preparation (task ID 6)
    print("\n1. Sample Preparation...")
    requests.put(f"{BASE_URL}/api/tasks/6", json={"status": "running"})
    
    prep_params = {
        "sample_id": "TEST03_SAMPLE_001",
        "volume": 10.0,
        "dilution_factor": 2.0,
        "target_ph": 7.0
    }
    
    # Reset prep station first
    requests.post("http://localhost:5002/reset")
    time.sleep(1)
    
    response = requests.post("http://localhost:5002/prepare", json=prep_params)
    if response.status_code == 202:
        print("   Sample prep started")
        
        # Monitor until completion
        while True:
            status_response = requests.get("http://localhost:5002/status")
            if status_response.status_code == 200:
                status = status_response.json().get('status')
                if status == 'completed':
                    results_response = requests.get("http://localhost:5002/results")
                    if results_response.status_code == 200:
                        results = results_response.json()
                        requests.put(f"{BASE_URL}/api/tasks/6", json={
                            "status": "completed",
                            "results": results
                        })
                        recovery = results['results']['recovery_percent']
                        print(f"   Sample prep completed: {recovery}% recovery")
                    break
                elif status in ['failed', 'aborted']:
                    print(f"   Sample prep {status}")
                    return False
            time.sleep(3)
    else:
        print(f"   Failed to start prep: {response.status_code}")
        return False
    
    # Task 2: HPLC Analysis (task ID 7)
    print("\n2. HPLC Analysis...")
    requests.put(f"{BASE_URL}/api/tasks/7", json={"status": "running"})
    
    hplc_params = {
        "sample_id": "TEST03_SAMPLE_001",
        "method": "USP_assay_method",
        "injection_volume": 10.0,
        "runtime_minutes": 15.0
    }
    
    # Reset HPLC first
    requests.post("http://localhost:5003/reset")
    time.sleep(1)
    
    response = requests.post("http://localhost:5003/analyze", json=hplc_params)
    if response.status_code == 202:
        print("   HPLC analysis started")
        
        # Monitor until completion
        while True:
            status_response = requests.get("http://localhost:5003/status")
            if status_response.status_code == 200:
                status = status_response.json().get('status')
                if status == 'completed':
                    results_response = requests.get("http://localhost:5003/results")
                    if results_response.status_code == 200:
                        results = results_response.json()
                        requests.put(f"{BASE_URL}/api/tasks/7", json={
                            "status": "completed",
                            "results": results
                        })
                        purity = results['results']['summary']['main_compound_purity']
                        print(f"   HPLC analysis completed: {purity}% purity")
                    break
                elif status in ['failed', 'aborted']:
                    print(f"   HPLC analysis {status}")
                    return False
            time.sleep(5)
    else:
        print(f"   Failed to start HPLC: {response.status_code}")
        return False
    
    # Mark workflow as completed
    requests.put(f"{BASE_URL}/api/workflows/3", json={"status": "completed"})
    print("\ntest_03 workflow completed successfully!")
    return True

def main():
    print("Processing test_03 workflow")
    print("=" * 30)
    
    # Fix mappings
    if not fix_workflow_3():
        return
    
    # Execute workflow
    execute_workflow_3()
    
    print("\nDone! Check the frontend monitor for updates.")

if __name__ == "__main__":
    main()