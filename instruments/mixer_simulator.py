#!/usr/bin/env python3
"""
Mixer Simulator
Simulates an IKA RW20 overhead stirrer for mixing operations
Port: 5002
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
    "name": "Mixer",
    "model": "IKA RW20",
    "status": "ready",
    "connected": True,
    "mixing": False,
    "current_speed": 0,
    "target_speed": 0,
    "current_temperature": 23.5,
    "target_temperature": 25.0,
    "torque": 0.0,
    "viscosity": 0.0,
    "mixing_time": 0,
    "total_mixing_time": 0,
    "error_message": None,
    "safety_status": "ok",
    "motor_load": 0,
    "speed_accuracy": 1.0,
    "temperature_accuracy": 0.5,
    "settings": {
        "max_speed": 2000,
        "min_speed": 10,
        "speed_ramp_rate": 50,  # rpm/second
        "temperature_control": True,
        "safety_limits": True,
        "auto_stop": True
    },
    "mixing_profiles": {
        "gentle": {"speed": 100, "time": 300},
        "standard": {"speed": 500, "time": 600}, 
        "vigorous": {"speed": 1000, "time": 900}
    },
    "session_data": []
}

def mixing_controller():
    """Background thread to control mixing operations"""
    while True:
        if instrument_state["mixing"] and instrument_state["connected"]:
            # Simulate speed ramping
            if instrument_state["current_speed"] < instrument_state["target_speed"]:
                ramp_rate = instrument_state["settings"]["speed_ramp_rate"]
                instrument_state["current_speed"] = min(
                    instrument_state["target_speed"],
                    instrument_state["current_speed"] + ramp_rate
                )
            elif instrument_state["current_speed"] > instrument_state["target_speed"]:
                ramp_rate = instrument_state["settings"]["speed_ramp_rate"]
                instrument_state["current_speed"] = max(
                    instrument_state["target_speed"],
                    instrument_state["current_speed"] - ramp_rate
                )
            
            # Simulate motor load and torque based on speed and viscosity
            base_torque = (instrument_state["current_speed"] / 2000) * 50  # Max 50 Ncm
            viscosity_factor = 1 + (instrument_state["viscosity"] / 10000)
            instrument_state["torque"] = round(base_torque * viscosity_factor, 2)
            instrument_state["motor_load"] = min(100, instrument_state["torque"] * 2)
            
            # Simulate temperature changes during mixing
            if instrument_state["mixing"]:
                heat_generation = instrument_state["current_speed"] * 0.001
                temp_change = heat_generation + random.gauss(0, 0.1)
                instrument_state["current_temperature"] = round(
                    instrument_state["current_temperature"] + temp_change, 1
                )
                
                # Temperature control
                if instrument_state["settings"]["temperature_control"]:
                    temp_diff = instrument_state["target_temperature"] - instrument_state["current_temperature"]
                    if abs(temp_diff) > 1.0:
                        control_adjustment = temp_diff * 0.1
                        instrument_state["current_temperature"] += control_adjustment
                
                instrument_state["mixing_time"] += 1
                instrument_state["total_mixing_time"] += 1
        
        time.sleep(1)  # Update every second

# Start mixing controller thread
mixing_thread = threading.Thread(target=mixing_controller, daemon=True)
mixing_thread.start()

@app.route('/status', methods=['GET'])
def get_status():
    """Get current instrument status"""
    return jsonify({
        "instrument": instrument_state["name"],
        "model": instrument_state["model"], 
        "status": instrument_state["status"],
        "connected": instrument_state["connected"],
        "mixing": instrument_state["mixing"],
        "current_speed": instrument_state["current_speed"],
        "target_speed": instrument_state["target_speed"],
        "current_temperature": instrument_state["current_temperature"],
        "target_temperature": instrument_state["target_temperature"],
        "torque": instrument_state["torque"],
        "motor_load": instrument_state["motor_load"],
        "mixing_time": instrument_state["mixing_time"],
        "safety_status": instrument_state["safety_status"],
        "timestamp": datetime.now().isoformat(),
        "capabilities": ["mixing", "motor_control", "temperature_control"],
        "specifications": {
            "speed_range": "10-2000 rpm",
            "torque": "50 Ncm",
            "viscosity_max": "10000 mPas",
            "temperature_range": "-10 to 300°C"
        }
    })

@app.route('/start', methods=['POST'])
def start_mixing():
    """Start mixing operation"""
    if not instrument_state["connected"]:
        return jsonify({"error": "Instrument not connected"}), 503
    
    if instrument_state["mixing"]:
        return jsonify({"error": "Already mixing"}), 400
    
    data = request.get_json() or {}
    
    # Parse parameters
    speed = data.get("speed", 500)
    temperature = data.get("temperature", 25.0)
    duration = data.get("duration", 600)
    profile = data.get("profile", None)
    
    # Apply mixing profile if specified
    if profile and profile in instrument_state["mixing_profiles"]:
        profile_data = instrument_state["mixing_profiles"][profile]
        speed = profile_data.get("speed", speed)
        duration = profile_data.get("time", duration)
    
    # Validate parameters
    if speed < instrument_state["settings"]["min_speed"]:
        speed = instrument_state["settings"]["min_speed"]
    elif speed > instrument_state["settings"]["max_speed"]:
        speed = instrument_state["settings"]["max_speed"]
    
    # Start mixing
    instrument_state["target_speed"] = speed
    instrument_state["target_temperature"] = temperature
    instrument_state["mixing"] = True
    instrument_state["status"] = "mixing"
    instrument_state["mixing_time"] = 0
    instrument_state["viscosity"] = data.get("viscosity", 1000)  # mPas
    
    # Store session data
    session_data = {
        "start_time": datetime.now().isoformat(),
        "target_speed": speed,
        "target_temperature": temperature,
        "duration": duration,
        "profile": profile,
        "parameters": data
    }
    instrument_state["session_data"].append(session_data)
    
    # Auto-stop timer if duration specified
    if duration > 0 and instrument_state["settings"]["auto_stop"]:
        def auto_stop():
            time.sleep(duration)
            if instrument_state["mixing"]:
                stop_mixing_internal()
        
        auto_stop_thread = threading.Thread(target=auto_stop, daemon=True)
        auto_stop_thread.start()
    
    return jsonify({
        "success": True,
        "message": "Mixing started",
        "parameters": {
            "speed": speed,
            "temperature": temperature,
            "duration": duration,
            "profile": profile
        },
        "status": instrument_state["status"]
    })

def stop_mixing_internal():
    """Internal function to stop mixing"""
    instrument_state["mixing"] = False
    instrument_state["target_speed"] = 0
    instrument_state["status"] = "ready"
    
    # Update last session data
    if instrument_state["session_data"]:
        instrument_state["session_data"][-1]["end_time"] = datetime.now().isoformat()
        instrument_state["session_data"][-1]["actual_mixing_time"] = instrument_state["mixing_time"]

@app.route('/stop', methods=['POST'])
def stop_mixing():
    """Stop mixing operation"""
    if not instrument_state["connected"]:
        return jsonify({"error": "Instrument not connected"}), 503
    
    if not instrument_state["mixing"]:
        return jsonify({"error": "Not currently mixing"}), 400
    
    stop_mixing_internal()
    
    return jsonify({
        "success": True,
        "message": "Mixing stopped",
        "mixing_time": instrument_state["mixing_time"],
        "status": instrument_state["status"]
    })

@app.route('/emergency_stop', methods=['POST'])
def emergency_stop():
    """Emergency stop - immediate shutdown"""
    instrument_state["mixing"] = False
    instrument_state["target_speed"] = 0
    instrument_state["current_speed"] = 0
    instrument_state["status"] = "emergency_stopped"
    
    return jsonify({
        "success": True,
        "message": "Emergency stop activated",
        "status": instrument_state["status"]
    })

@app.route('/set_speed', methods=['POST'])
def set_speed():
    """Change mixing speed during operation"""
    if not instrument_state["connected"]:
        return jsonify({"error": "Instrument not connected"}), 503
    
    data = request.get_json() or {}
    new_speed = data.get("speed", 0)
    
    # Validate speed
    if new_speed < 0:
        new_speed = 0
    elif new_speed > instrument_state["settings"]["max_speed"]:
        new_speed = instrument_state["settings"]["max_speed"]
    
    instrument_state["target_speed"] = new_speed
    
    return jsonify({
        "success": True,
        "message": f"Target speed set to {new_speed} rpm",
        "target_speed": new_speed,
        "current_speed": instrument_state["current_speed"]
    })

@app.route('/set_temperature', methods=['POST'])
def set_temperature():
    """Set target temperature"""
    if not instrument_state["connected"]:
        return jsonify({"error": "Instrument not connected"}), 503
    
    data = request.get_json() or {}
    temperature = data.get("temperature", 25.0)
    
    instrument_state["target_temperature"] = temperature
    
    return jsonify({
        "success": True,
        "message": f"Target temperature set to {temperature}°C",
        "target_temperature": temperature,
        "current_temperature": instrument_state["current_temperature"]
    })

@app.route('/profiles', methods=['GET'])
def get_profiles():
    """Get available mixing profiles"""
    return jsonify({
        "profiles": instrument_state["mixing_profiles"],
        "current_profile": None
    })

@app.route('/session_data', methods=['GET'])
def get_session_data():
    """Get session data and mixing history"""
    return jsonify({
        "current_session": {
            "mixing": instrument_state["mixing"],
            "mixing_time": instrument_state["mixing_time"],
            "total_mixing_time": instrument_state["total_mixing_time"],
            "current_speed": instrument_state["current_speed"],
            "current_temperature": instrument_state["current_temperature"]
        },
        "session_history": instrument_state["session_data"]
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

@app.route('/connect', methods=['POST'])
def connect():
    """Connect to instrument"""
    instrument_state["connected"] = True
    instrument_state["status"] = "ready"
    
    return jsonify({
        "success": True,
        "message": "Connected to mixer",
        "status": instrument_state["status"]
    })

@app.route('/disconnect', methods=['POST'])
def disconnect():
    """Disconnect from instrument"""
    if instrument_state["mixing"]:
        stop_mixing_internal()
    
    instrument_state["connected"] = False
    instrument_state["status"] = "offline"
    
    return jsonify({
        "success": True,
        "message": "Disconnected from mixer",
        "status": instrument_state["status"]
    })

@app.route('/', methods=['GET'])
def home():
    """Home page with API documentation"""
    return jsonify({
        "instrument": "Mixer Simulator",
        "model": "IKA RW20",
        "version": "1.0.0",
        "endpoints": {
            "GET /status": "Get instrument status",
            "POST /start": "Start mixing operation",
            "POST /stop": "Stop mixing operation",
            "POST /emergency_stop": "Emergency stop",
            "POST /set_speed": "Change mixing speed",
            "POST /set_temperature": "Set target temperature",
            "GET /profiles": "Get mixing profiles",
            "GET /session_data": "Get session data",
            "GET /settings": "Get current settings",
            "POST /settings": "Update settings",
            "POST /connect": "Connect to instrument",
            "POST /disconnect": "Disconnect from instrument"
        }
    })

if __name__ == '__main__':
    print(f"Starting {instrument_state['name']} Simulator on port 5012...")
    print(f"Model: {instrument_state['model']}")
    print("Available endpoints:")
    print("  GET  /status - Instrument status")
    print("  POST /start - Start mixing")
    print("  POST /stop - Stop mixing")
    print("  POST /set_speed - Change speed")
    
    app.run(host='0.0.0.0', port=5012, debug=True)