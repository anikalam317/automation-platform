#!/usr/bin/env python3
"""
NIR Spectrometer Simulator
Simulates a Bruker MPA II NIR spectrometer for process monitoring
Port: 5003
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import random
import time
import numpy as np
from datetime import datetime
import threading
import json

app = Flask(__name__)
CORS(app)

# Instrument state
instrument_state = {
    "name": "NIR",
    "model": "Bruker MPA II",
    "status": "ready",
    "connected": True,
    "measuring": False,
    "temperature": 25.0,
    "lamp_hours": 2847,
    "detector_temperature": -25.3,
    "last_reference": "2025-08-20T08:00:00Z",
    "scan_count": 0,
    "error_message": None,
    "settings": {
        "wavelength_start": 1000,  # nm
        "wavelength_end": 2500,    # nm
        "resolution": 2,           # nm
        "scans_to_average": 32,
        "integration_time": 100,   # ms
        "auto_reference": True,
        "background_correction": True
    },
    "calibration_models": {
        "moisture": {"active": True, "r2": 0.987, "rmse": 0.12},
        "protein": {"active": True, "r2": 0.952, "rmse": 0.34},
        "fat": {"active": False, "r2": 0.943, "rmse": 0.28}
    },
    "measurement_history": []
}

def generate_nir_spectrum():
    """Generate a realistic NIR spectrum with peaks and noise"""
    wavelengths = np.arange(
        instrument_state["settings"]["wavelength_start"],
        instrument_state["settings"]["wavelength_end"],
        instrument_state["settings"]["resolution"]
    )
    
    # Generate baseline
    baseline = np.exp(-0.0005 * wavelengths) + 0.1
    
    # Add characteristic peaks for organic materials
    peaks = [
        {"center": 1200, "width": 20, "intensity": 0.15},  # C-H stretch overtone
        {"center": 1450, "width": 30, "intensity": 0.25},  # O-H stretch first overtone
        {"center": 1650, "width": 25, "intensity": 0.12},  # C=O stretch overtone
        {"center": 1940, "width": 35, "intensity": 0.18},  # O-H + C-C combination
        {"center": 2100, "width": 40, "intensity": 0.22},  # C-H stretch combination
        {"center": 2300, "width": 30, "intensity": 0.14}   # C-H deformation combination
    ]
    
    spectrum = baseline.copy()
    for peak in peaks:
        gaussian = peak["intensity"] * np.exp(
            -0.5 * ((wavelengths - peak["center"]) / peak["width"]) ** 2
        )
        spectrum += gaussian
    
    # Add noise based on detector performance
    noise_level = 0.005 * (1 + wavelengths / 10000)  # Wavelength-dependent noise
    noise = np.random.normal(0, noise_level, len(wavelengths))
    spectrum += noise
    
    # Add random variations for different samples
    variation = random.uniform(0.95, 1.05)
    spectrum *= variation
    
    return wavelengths.tolist(), spectrum.tolist()

def apply_preprocessing(spectrum):
    """Apply standard preprocessing to spectrum"""
    spectrum = np.array(spectrum)
    
    # Standard Normal Variate (SNV)
    if instrument_state["settings"]["background_correction"]:
        mean_spectrum = np.mean(spectrum)
        std_spectrum = np.std(spectrum)
        if std_spectrum > 0:
            spectrum = (spectrum - mean_spectrum) / std_spectrum
    
    return spectrum.tolist()

def predict_composition(spectrum):
    """Apply calibration models to predict composition"""
    predictions = {}
    
    for component, model in instrument_state["calibration_models"].items():
        if model["active"]:
            # Simulate model predictions with some realistic noise
            base_values = {
                "moisture": 12.5,
                "protein": 15.8,
                "fat": 3.2
            }
            
            # Add some spectral correlation and noise
            spectral_factor = np.mean(spectrum) * 10 + random.gauss(0, model["rmse"])
            predicted_value = base_values[component] + spectral_factor
            
            # Add realistic constraints
            if component == "moisture":
                predicted_value = max(0, min(25, predicted_value))
            elif component == "protein":
                predicted_value = max(0, min(30, predicted_value))
            elif component == "fat":
                predicted_value = max(0, min(15, predicted_value))
            
            predictions[component] = {
                "value": round(predicted_value, 2),
                "units": "%",
                "confidence": round(model["r2"], 3),
                "model_rmse": model["rmse"]
            }
    
    return predictions

@app.route('/status', methods=['GET'])
def get_status():
    """Get current instrument status"""
    return jsonify({
        "instrument": instrument_state["name"],
        "model": instrument_state["model"],
        "status": instrument_state["status"],
        "connected": instrument_state["connected"],
        "measuring": instrument_state["measuring"],
        "temperature": instrument_state["temperature"],
        "detector_temperature": instrument_state["detector_temperature"],
        "lamp_hours": instrument_state["lamp_hours"],
        "last_reference": instrument_state["last_reference"],
        "scan_count": instrument_state["scan_count"],
        "timestamp": datetime.now().isoformat(),
        "capabilities": ["spectroscopy", "nir", "multivariate_analysis"],
        "specifications": {
            "wavelength_range": "1000-2500 nm",
            "resolution": "≤2 nm",
            "scan_time": "0.1-10 seconds",
            "detector": "InGaAs"
        }
    })

@app.route('/measure', methods=['POST'])
def measure_spectrum():
    """Acquire NIR spectrum"""
    if not instrument_state["connected"]:
        return jsonify({"error": "Instrument not connected"}), 503
    
    if instrument_state["measuring"]:
        return jsonify({"error": "Already measuring"}), 400
    
    data = request.get_json() or {}
    sample_id = data.get("sample_id", f"NIR_{instrument_state['scan_count'] + 1}")
    scans = data.get("scans", instrument_state["settings"]["scans_to_average"])
    apply_models = data.get("apply_models", True)
    
    # Start measurement
    instrument_state["measuring"] = True
    instrument_state["status"] = "measuring"
    
    # Simulate measurement time
    measurement_time = scans * 0.1 + instrument_state["settings"]["integration_time"] / 1000
    time.sleep(min(measurement_time, 3))  # Cap at 3 seconds for demo
    
    # Generate spectrum
    wavelengths, raw_spectrum = generate_nir_spectrum()
    processed_spectrum = apply_preprocessing(raw_spectrum)
    
    measurement_result = {
        "sample_id": sample_id,
        "wavelengths": wavelengths,
        "raw_spectrum": raw_spectrum,
        "processed_spectrum": processed_spectrum,
        "measurement_parameters": {
            "scans_averaged": scans,
            "resolution": instrument_state["settings"]["resolution"],
            "integration_time": instrument_state["settings"]["integration_time"],
            "temperature": instrument_state["temperature"]
        },
        "timestamp": datetime.now().isoformat(),
        "measurement_id": instrument_state["scan_count"] + 1
    }
    
    # Apply calibration models if requested
    if apply_models:
        predictions = predict_composition(processed_spectrum)
        measurement_result["predictions"] = predictions
    
    # Update state
    instrument_state["measuring"] = False
    instrument_state["status"] = "ready"
    instrument_state["scan_count"] += 1
    instrument_state["measurement_history"].append(measurement_result)
    
    # Keep only last 100 measurements in memory
    if len(instrument_state["measurement_history"]) > 100:
        instrument_state["measurement_history"] = instrument_state["measurement_history"][-100:]
    
    return jsonify({
        "success": True,
        "measurement": measurement_result,
        "instrument_status": instrument_state["status"]
    })

@app.route('/reference', methods=['POST'])
def collect_reference():
    """Collect background reference spectrum"""
    if not instrument_state["connected"]:
        return jsonify({"error": "Instrument not connected"}), 503
    
    instrument_state["status"] = "collecting_reference"
    
    # Simulate reference collection
    time.sleep(2)
    
    instrument_state["last_reference"] = datetime.now().isoformat()
    instrument_state["status"] = "ready"
    
    return jsonify({
        "success": True,
        "message": "Reference spectrum collected",
        "reference_time": instrument_state["last_reference"]
    })

@app.route('/models', methods=['GET', 'POST'])
def manage_models():
    """Get or update calibration models"""
    if request.method == 'GET':
        return jsonify({
            "models": instrument_state["calibration_models"],
            "active_models": [name for name, model in instrument_state["calibration_models"].items() if model["active"]]
        })
    
    elif request.method == 'POST':
        if not instrument_state["connected"]:
            return jsonify({"error": "Instrument not connected"}), 503
        
        data = request.get_json() or {}
        model_name = data.get("model_name")
        action = data.get("action", "activate")  # activate, deactivate, update
        
        if model_name not in instrument_state["calibration_models"]:
            return jsonify({"error": "Model not found"}), 404
        
        if action == "activate":
            instrument_state["calibration_models"][model_name]["active"] = True
        elif action == "deactivate":
            instrument_state["calibration_models"][model_name]["active"] = False
        elif action == "update" and "model_data" in data:
            instrument_state["calibration_models"][model_name].update(data["model_data"])
        
        return jsonify({
            "success": True,
            "message": f"Model {model_name} {action}d successfully",
            "models": instrument_state["calibration_models"]
        })

@app.route('/history', methods=['GET'])
def get_measurement_history():
    """Get measurement history"""
    limit = request.args.get('limit', 50, type=int)
    
    history = instrument_state["measurement_history"][-limit:]
    
    return jsonify({
        "history": history,
        "total_measurements": instrument_state["scan_count"],
        "returned_count": len(history)
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
                if key == "wavelength_start" and 800 <= value <= 1500:
                    instrument_state["settings"][key] = value
                elif key == "wavelength_end" and 1500 <= value <= 2700:
                    instrument_state["settings"][key] = value
                elif key == "resolution" and 1 <= value <= 16:
                    instrument_state["settings"][key] = value
                elif key == "scans_to_average" and 1 <= value <= 256:
                    instrument_state["settings"][key] = value
                elif key in ["auto_reference", "background_correction"]:
                    instrument_state["settings"][key] = bool(value)
                else:
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
        "message": "Connected to NIR spectrometer",
        "status": instrument_state["status"]
    })

@app.route('/disconnect', methods=['POST'])
def disconnect():
    """Disconnect from instrument"""
    instrument_state["connected"] = False
    instrument_state["status"] = "offline"
    instrument_state["measuring"] = False
    
    return jsonify({
        "success": True,
        "message": "Disconnected from NIR spectrometer",
        "status": instrument_state["status"]
    })

@app.route('/', methods=['GET'])
def home():
    """Home page with API documentation"""
    return jsonify({
        "instrument": "NIR Spectrometer Simulator",
        "model": "Bruker MPA II",
        "version": "1.0.0",
        "endpoints": {
            "GET /status": "Get instrument status",
            "POST /measure": "Acquire NIR spectrum",
            "POST /reference": "Collect reference spectrum",
            "GET /models": "Get calibration models",
            "POST /models": "Update calibration models",
            "GET /history": "Get measurement history",
            "GET /settings": "Get current settings",
            "POST /settings": "Update settings",
            "POST /connect": "Connect to instrument",
            "POST /disconnect": "Disconnect from instrument"
        }
    })

if __name__ == '__main__':
    print(f"Starting {instrument_state['name']} Simulator on port 5013...")
    print(f"Model: {instrument_state['model']}")
    print("Available endpoints:")
    print("  GET  /status - Instrument status")
    print("  POST /measure - Acquire spectrum")
    print("  POST /reference - Collect reference")
    print("  GET  /models - Calibration models")
    
    app.run(host='0.0.0.0', port=5013, debug=True)