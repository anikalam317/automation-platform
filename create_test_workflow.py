#!/usr/bin/env python3
import requests
import json

# Create a sequential test workflow
workflow_data = {
    "name": "Powder_13_Service_Integration_Test",
    "author": "Lab User",
    "tasks": [
        {
            "name": "Sample Measurement",
            "service_parameters": {
                "measurement_unit": "g",
                "tolerance": 1
            }
        },
        {
            "name": "Run Weight Balance",
            "service_parameters": {
                "materials_table": [
                    {"run": 1, "material_1": 0.1, "material_2": 0.05}
                ]
            }
        },
        {
            "name": "Weight Balance",
            "service_parameters": {
                "materials_table": [
                    {"run": 1, "material_1": 0.1, "material_2": 0.05}
                ]
            }
        }
    ]
}

# Send request
response = requests.post("http://localhost:8001/api/workflows", json=workflow_data)
print(f"Status: {response.status_code}")
print(json.dumps(response.json(), indent=2))

if response.status_code == 201:
    workflow_id = response.json()["id"]
    print(f"\nWorkflow created with ID: {workflow_id}")
    print(f"Navigate to http://localhost:3005/builder/{workflow_id} to edit")
    print(f"Navigate to http://localhost:3005/monitor/{workflow_id} to monitor")