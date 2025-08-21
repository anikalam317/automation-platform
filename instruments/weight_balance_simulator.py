#!/usr/bin/env python3
"""
Weight Balance Simulator
Simulates a Mettler Toledo XPE205 analytical balance
Port: 5001
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import random
import time
from datetime import datetime
import threading
import json

app = Flask(__name__)
CORS(app)

# Instrument state
instrument_state = {
    "name": "Weight Balance",
    "model": "Mettler Toledo XPE205",
    "status": "online",
    "connected": True,
    "last_measurement": None,
    "current_weight": 0.0,
    "tare_weight": 0.0,
    "stability": "stable",
    "door_open": False,
    "temperature": 21.5,
    "humidity": 45.2,
    "calibration_status": "valid",
    "last_calibration": "2025-08-15T10:30:00Z",
    "measurement_count": 0,
    "error_message": None,
    "settings": {
        "precision": 0.01,
        "units": "mg", 
        "stability_time": 3,
        "auto_tare": True,
        "environmental_monitoring": True
    }
}

def simulate_measurement():
    """Simulate a realistic weight measurement with noise"""
    # Add some realistic noise to the measurement
    base_weight = 125.67  # Sample weight in mg
    noise = random.gauss(0, 0.05)  # Gaussian noise ±0.05mg
    environmental_drift = random.uniform(-0.02, 0.02)  # Environmental drift
    
    return round(base_weight + noise + environmental_drift, 3)

def update_environmental_conditions():
    """Periodically update temperature and humidity"""
    while True:
        if instrument_state["connected"]:
            # Simulate small environmental changes
            temp_change = random.gauss(0, 0.1)
            humidity_change = random.gauss(0, 0.5)
            
            instrument_state["temperature"] = round(
                max(18.0, min(25.0, instrument_state["temperature"] + temp_change)), 1
            )
            instrument_state["humidity"] = round(
                max(40.0, min(60.0, instrument_state["humidity"] + humidity_change)), 1
            )
        
        time.sleep(30)  # Update every 30 seconds

# Start environmental monitoring thread
env_thread = threading.Thread(target=update_environmental_conditions, daemon=True)
env_thread.start()

@app.route('/status', methods=['GET'])
def get_status():
    """Get current instrument status"""
    return jsonify({
        "instrument": instrument_state["name"],
        "model": instrument_state["model"],
        "status": instrument_state["status"],
        "connected": instrument_state["connected"],
        "timestamp": datetime.now().isoformat(),
        "uptime": "operational",
        "capabilities": ["balance", "measurement", "precision_weighing"],
        "specifications": {
            "max_weight": "220g",
            "readability": "0.01mg",
            "linearity": "0.02mg",
            "interface": "RS232/USB"
        }
    })

@app.route('/measure', methods=['POST'])
def measure_weight():
    """Perform weight measurement"""
    if not instrument_state["connected"]:
        return jsonify({"error": "Instrument not connected"}), 503
    
    data = request.get_json() or {}
    sample_id = data.get("sample_id", f"SAMPLE_{instrument_state['measurement_count'] + 1}")
    
    # Simulate measurement process
    instrument_state["status"] = "measuring"
    instrument_state["stability"] = "stabilizing"
    
    # Wait for stabilization (simulate)
    time.sleep(instrument_state["settings"]["stability_time"])
    
    # Perform measurement
    weight = simulate_measurement()
    net_weight = weight - instrument_state["tare_weight"]
    
    measurement_result = {
        "sample_id": sample_id,
        "gross_weight": weight,
        "net_weight": round(net_weight, 3),
        "tare_weight": instrument_state["tare_weight"],
        "units": instrument_state["settings"]["units"],
        "precision": instrument_state["settings"]["precision"],
        "stability": "stable",
        "temperature": instrument_state["temperature"],
        "humidity": instrument_state["humidity"],
        "timestamp": datetime.now().isoformat(),
        "measurement_id": instrument_state["measurement_count"] + 1
    }
    
    # Update state
    instrument_state["last_measurement"] = measurement_result
    instrument_state["current_weight"] = weight
    instrument_state["status"] = "ready"
    instrument_state["stability"] = "stable"
    instrument_state["measurement_count"] += 1
    
    return jsonify({
        "success": True,
        "measurement": measurement_result,
        "instrument_status": instrument_state["status"]
    })

@app.route('/tare', methods=['POST'])
def tare_balance():
    """Tare the balance (set current weight as zero)"""
    if not instrument_state["connected"]:
        return jsonify({"error": "Instrument not connected"}), 503
    
    instrument_state["tare_weight"] = instrument_state["current_weight"]
    
    return jsonify({
        "success": True,
        "message": "Balance tared successfully",
        "tare_weight": instrument_state["tare_weight"],
        "units": instrument_state["settings"]["units"]
    })

@app.route('/calibrate', methods=['POST'])
def calibrate():
    """Perform calibration with reference weights"""
    if not instrument_state["connected"]:
        return jsonify({"error": "Instrument not connected"}), 503
    
    data = request.get_json() or {}
    reference_weights = data.get("reference_weights", [100.0, 200.0])
    
    instrument_state["status"] = "calibrating"
    
    # Simulate calibration process
    calibration_results = []
    for ref_weight in reference_weights:
        time.sleep(2)  # Simulate calibration time
        measured = ref_weight + random.gauss(0, 0.01)  # Small error
        calibration_results.append({
            "reference": ref_weight,
            "measured": round(measured, 3),
            "deviation": round(measured - ref_weight, 3)
        })
    
    instrument_state["calibration_status"] = "valid"
    instrument_state["last_calibration"] = datetime.now().isoformat()
    instrument_state["status"] = "ready"
    
    return jsonify({
        "success": True,
        "calibration_results": calibration_results,
        "calibration_date": instrument_state["last_calibration"],
        "status": instrument_state["calibration_status"]
    })

@app.route('/settings', methods=['GET', 'POST'])
def manage_settings():
    """Get or update instrument settings"""
    if request.method == 'GET':
        return jsonify(instrument_state["settings"])
    
    elif request.method == 'POST':
        if not instrument_state["connected"]:
            return jsonify({"error": "Instrument not connected"}), 503
        
        new_settings = request.get_json() or {}
        
        # Update settings with validation
        for key, value in new_settings.items():
            if key in instrument_state["settings"]:
                instrument_state["settings"][key] = value
        
        return jsonify({
            "success": True,
            "message": "Settings updated successfully",
            "settings": instrument_state["settings"]
        })

@app.route('/dispense', methods=['POST'])
def dispense_and_measure():
    """Dispense and measure materials from a table (main workflow endpoint)"""
    if not instrument_state["connected"]:
        return jsonify({"error": "Instrument not connected"}), 503
    
    data = request.get_json() or {}
    materials_table = data.get('materials_table', [])
    unit = data.get('unit', 'g')
    tolerance = data.get('tolerance', 1.0)
    replicates = data.get('replicates', 1)
    
    if not materials_table:
        return jsonify({"error": "No materials table provided"}), 400
    
    print(f"Processing materials table with {len(materials_table)} rows")
    
    instrument_state["status"] = "processing"
    
    results = []
    total_measurements = 0
    successful_measurements = 0
    
    # Conversion factors
    conversion_factors = {"g": 1.0, "mg": 0.001, "kg": 1000.0, "µg": 0.000001}
    unit_factor = conversion_factors.get(unit, 1.0)
    
    for row in materials_table:
        run_number = row.get("run", len(results) + 1)
        row_results = {
            "run": run_number,
            "measurements": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Process each material in the row
        for key, target_weight in row.items():
            if key == "run" or target_weight is None or target_weight == 0:
                continue
            
            for replicate in range(replicates):
                total_measurements += 1
                
                # Simulate dispensing and measurement
                time.sleep(1)  # Simulate dispensing time
                
                # Convert target weight to grams for simulation
                target_in_grams = target_weight * unit_factor
                
                # Simulate dispensing accuracy (99.5% typical)
                dispensing_accuracy = random.uniform(0.995, 1.005)
                actual_in_grams = target_in_grams * dispensing_accuracy
                
                # Add measurement noise
                noise = random.gauss(0, 0.001)  # ±0.001g noise
                actual_in_grams += noise
                
                # Convert back to requested unit
                actual_weight = actual_in_grams / unit_factor
                
                deviation_percent = ((actual_weight - target_weight) / target_weight) * 100 if target_weight > 0 else 0
                within_tolerance = abs(deviation_percent) <= tolerance
                
                if within_tolerance:
                    successful_measurements += 1
                
                measurement = {
                    "material": key,
                    "replicate": replicate + 1,
                    "target_weight": target_weight,
                    "actual_weight": round(actual_weight, 6),
                    "unit": unit,
                    "deviation_percent": round(deviation_percent, 3),
                    "within_tolerance": within_tolerance,
                    "temperature": instrument_state["temperature"],
                    "humidity": instrument_state["humidity"],
                    "timestamp": datetime.now().isoformat()
                }
                
                row_results["measurements"].append(measurement)
                instrument_state["measurement_count"] += 1
        
        results.append(row_results)
    
    instrument_state["status"] = "ready"
    success_rate = (successful_measurements / total_measurements * 100) if total_measurements > 0 else 0
    
    summary = {
        "success": True,
        "total_runs": len(results),
        "total_measurements": total_measurements,
        "successful_measurements": successful_measurements,
        "success_rate": round(success_rate, 1),
        "results": results,
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"Completed processing. Success rate: {success_rate:.1f}%")
    
    return jsonify(summary)

@app.route('/results', methods=['GET'])
def get_results():
    """Get the latest measurement results"""
    return jsonify({
        "last_measurement": instrument_state.get("last_measurement"),
        "measurement_count": instrument_state["measurement_count"],
        "timestamp": datetime.now().isoformat()
    })

@app.route('/initialize', methods=['POST'])
def initialize():
    """Initialize the weight balance"""
    instrument_state["status"] = "initializing"
    time.sleep(2)  # Simulate initialization time
    
    instrument_state["status"] = "ready"
    instrument_state["connected"] = True
    
    return jsonify({
        "success": True,
        "message": "Weight balance initialized",
        "status": "ready",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/reset', methods=['POST'])
def reset_instrument():
    """Reset instrument to default state"""
    global instrument_state
    
    instrument_state.update({
        "status": "online",
        "connected": True,
        "current_weight": 0.0,
        "tare_weight": 0.0,
        "stability": "stable",
        "error_message": None,
        "measurement_count": 0
    })
    
    return jsonify({
        "success": True,
        "message": "Instrument reset successfully",
        "status": instrument_state["status"]
    })

@app.route('/connect', methods=['POST'])
def connect():
    """Connect to instrument"""
    instrument_state["connected"] = True
    instrument_state["status"] = "online"
    
    return jsonify({
        "success": True,
        "message": "Connected to weight balance",
        "status": instrument_state["status"]
    })

@app.route('/disconnect', methods=['POST'])
def disconnect():
    """Disconnect from instrument"""
    instrument_state["connected"] = False
    instrument_state["status"] = "offline"
    
    return jsonify({
        "success": True,
        "message": "Disconnected from weight balance",
        "status": instrument_state["status"]
    })

@app.route('/', methods=['GET'])
def home():
    """Home page with API documentation"""
    return jsonify({
        "instrument": "Weight Balance Simulator",
        "model": "Mettler Toledo XPE205",
        "version": "1.0.0",
        "endpoints": {
            "GET /status": "Get instrument status",
            "POST /measure": "Perform weight measurement",
            "POST /tare": "Tare the balance",
            "POST /calibrate": "Calibrate with reference weights",
            "POST /dispense": "Process materials table (main workflow endpoint)",
            "GET /results": "Get latest measurement results",
            "POST /initialize": "Initialize the weight balance",
            "GET /settings": "Get current settings",
            "POST /settings": "Update settings",
            "POST /reset": "Reset instrument",
            "POST /connect": "Connect to instrument",
            "POST /disconnect": "Disconnect from instrument"
        }
    })

if __name__ == '__main__':
    print(f"Starting {instrument_state['name']} Simulator on port 5011...")
    print(f"Model: {instrument_state['model']}")
    print("Available endpoints:")
    print("  GET  /status - Instrument status")
    print("  POST /measure - Perform measurement")
    print("  POST /tare - Tare balance")
    print("  POST /calibrate - Calibrate instrument")
    
    app.run(host='0.0.0.0', port=5011, debug=True)