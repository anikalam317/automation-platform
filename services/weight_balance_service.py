#!/usr/bin/env python3
"""
Weight Balance Service
Coordinates with weight balance instruments and manages measurement processes
Port: 6001
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import time
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)

# Configuration
WEIGHT_BALANCE_ENDPOINT = "http://localhost:5011"

@app.route('/status', methods=['GET'])
def get_status():
    """Get service status"""
    try:
        # Check if weight balance instrument is available
        balance_response = requests.get(f"{WEIGHT_BALANCE_ENDPOINT}/status", timeout=5)
        balance_available = balance_response.status_code == 200
    except:
        balance_available = False
    
    return jsonify({
        "service": "Weight Balance Service",
        "status": "online",
        "weight_balance_available": balance_available,
        "timestamp": datetime.now().isoformat(),
        "capabilities": ["process_materials", "coordinate_measurements"]
    })

@app.route('/process_materials', methods=['POST'])
def process_materials():
    """Process materials table through weight balance"""
    try:
        data = request.get_json() or {}
        
        # Extract materials table and parameters
        materials_table = data.get('materials_table', [])
        measurement_mode = data.get('measurement_mode', 'automatic')
        stabilization_time = data.get('stabilization_time', 3)
        number_of_readings = data.get('number_of_readings', 3)
        output_format = data.get('output_format', 'json')
        
        if not materials_table:
            return jsonify({"error": "No materials table provided"}), 400
        
        print(f"Processing {len(materials_table)} material rows through weight balance service")
        
        # Prepare request for weight balance instrument
        balance_request = {
            "materials_table": materials_table,
            "unit": "g",
            "tolerance": 1.0,
            "replicates": number_of_readings
        }
        
        # Call weight balance instrument
        balance_response = requests.post(
            f"{WEIGHT_BALANCE_ENDPOINT}/dispense", 
            json=balance_request,
            timeout=60
        )
        
        if balance_response.status_code == 200:
            balance_data = balance_response.json()
            
            # Format response for workflow system
            result = {
                "success": True,
                "service": "Weight Balance Service",
                "processing_mode": measurement_mode,
                "stabilization_time": stabilization_time,
                "measurements_per_sample": number_of_readings,
                "total_runs": balance_data.get("total_runs", 0),
                "total_measurements": balance_data.get("total_measurements", 0),
                "success_rate": balance_data.get("success_rate", 0),
                "results": balance_data.get("results", []),
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"Weight balance processing completed. Success rate: {result['success_rate']}%")
            return jsonify(result)
        else:
            error_msg = f"Weight balance error: HTTP {balance_response.status_code}"
            print(error_msg)
            return jsonify({"error": error_msg}), 500
            
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to communicate with weight balance: {str(e)}"
        print(error_msg)
        return jsonify({"error": error_msg}), 503
    except Exception as e:
        error_msg = f"Service error: {str(e)}"
        print(error_msg)
        return jsonify({"error": error_msg}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "service": "Weight Balance Service",
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/', methods=['GET'])
def home():
    """Service information"""
    return jsonify({
        "service": "Weight Balance Service",
        "version": "1.0.0",
        "description": "Coordinates weight measurements and material processing",
        "endpoints": {
            "GET /status": "Get service status",
            "POST /process_materials": "Process materials table through weight balance",
            "GET /health": "Health check"
        },
        "weight_balance_endpoint": WEIGHT_BALANCE_ENDPOINT
    })

if __name__ == '__main__':
    print("Starting Weight Balance Service on port 6001...")
    print(f"Will coordinate with weight balance at: {WEIGHT_BALANCE_ENDPOINT}")
    app.run(host='127.0.0.1', port=6001, debug=False)