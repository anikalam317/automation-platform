#!/usr/bin/env python3
"""
Sample Preparation Station Instrument
Simulates an automated sample preparation system for pharmaceutical analysis
"""

import time
import json
import random
from datetime import datetime
from flask import Flask, request, jsonify
import threading
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SamplePrepStation:
    def __init__(self):
        self.status = "idle"
        self.current_task = None
        self.results = {}
        self.prep_time = 0
        self.start_time = None
        
    def prepare_sample(self, sample_id, volume, dilution_factor, target_ph):
        """Simulate sample preparation process"""
        self.status = "preparing"
        self.start_time = datetime.now()
        self.current_task = {
            "sample_id": sample_id,
            "volume": volume,
            "dilution_factor": dilution_factor,
            "target_ph": target_ph
        }
        
        logger.info(f"Starting sample prep for {sample_id}")
        
        # Simulate preparation steps with fast timing for testing
        steps = [
            ("Aspirating sample", 5),
            ("Adding diluent", 8),
            ("Mixing solution", 12),
            ("Adjusting pH", 15),
            ("Filtering sample", 10),
            ("Transferring to vial", 10)
        ]
        
        total_time = sum(step[1] for step in steps)
        self.prep_time = total_time
        
        for step_name, duration in steps:
            logger.info(f"Step: {step_name} (estimated {duration}s)")
            time.sleep(duration)
            
            # Simulate occasional minor delays
            if random.random() < 0.3:
                delay = random.uniform(1, 3)
                logger.info(f"Minor delay of {delay:.1f}s")
                time.sleep(delay)
        
        # Generate realistic results
        actual_volume = volume * dilution_factor * random.uniform(0.98, 1.02)
        actual_ph = target_ph + random.uniform(-0.1, 0.1)
        recovery = random.uniform(95, 99)
        
        self.results = {
            "sample_id": sample_id,
            "prepared_at": datetime.now().isoformat(),
            "actual_volume_ml": round(actual_volume, 2),
            "actual_ph": round(actual_ph, 2),
            "target_ph": target_ph,
            "recovery_percent": round(recovery, 1),
            "preparation_time_seconds": total_time + random.randint(-5, 10),
            "dilution_factor": dilution_factor,
            "filtered": True,
            "quality_check": "passed" if recovery > 90 else "warning"
        }
        
        self.status = "completed"
        logger.info(f"Sample prep completed for {sample_id}: {recovery:.1f}% recovery")
        return self.results

# Global instrument instance
prep_station = SamplePrepStation()

@app.route('/status', methods=['GET'])
def get_status():
    """Get current instrument status"""
    response = {
        "instrument": "Sample Preparation Station",
        "model": "AutoPrep-3000",
        "status": prep_station.status,
        "current_task": prep_station.current_task,
        "uptime_hours": 24.5,
        "last_maintenance": "2024-01-15",
        "available_methods": [
            "standard_dilution",
            "ph_adjustment", 
            "filtration",
            "buffer_exchange"
        ]
    }
    
    if prep_station.status == "preparing" and prep_station.start_time:
        elapsed = (datetime.now() - prep_station.start_time).total_seconds()
        response["elapsed_time_seconds"] = round(elapsed, 1)
        response["estimated_completion"] = prep_station.prep_time
        response["progress_percent"] = min(100, round((elapsed / prep_station.prep_time) * 100, 1))
    
    return jsonify(response)

@app.route('/prepare', methods=['POST'])
def prepare_sample():
    """Execute sample preparation"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        required_params = ['sample_id', 'volume', 'dilution_factor', 'target_ph']
        for param in required_params:
            if param not in data:
                return jsonify({"error": f"Missing required parameter: {param}"}), 400
        
        if prep_station.status == "preparing":
            return jsonify({"error": "Instrument is currently busy"}), 409
        
        sample_id = data['sample_id']
        volume = float(data['volume'])
        dilution_factor = float(data['dilution_factor'])
        target_ph = float(data['target_ph'])
        
        # Validate parameters
        if volume <= 0 or volume > 50:
            return jsonify({"error": "Volume must be between 0 and 50 mL"}), 400
        if dilution_factor < 1 or dilution_factor > 100:
            return jsonify({"error": "Dilution factor must be between 1 and 100"}), 400
        if target_ph < 1 or target_ph > 14:
            return jsonify({"error": "pH must be between 1 and 14"}), 400
        
        # Start preparation in background thread
        def run_preparation():
            prep_station.prepare_sample(sample_id, volume, dilution_factor, target_ph)
        
        thread = threading.Thread(target=run_preparation)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "message": "Sample preparation started",
            "sample_id": sample_id,
            "estimated_time_seconds": prep_station.prep_time or 55,
            "status": "preparing"
        }), 202
        
    except Exception as e:
        logger.error(f"Error in sample preparation: {str(e)}")
        return jsonify({"error": f"Preparation failed: {str(e)}"}), 500

@app.route('/results', methods=['GET'])
def get_results():
    """Get preparation results"""
    if not prep_station.results:
        return jsonify({"error": "No results available"}), 404
    
    return jsonify({
        "results": prep_station.results,
        "instrument_status": prep_station.status
    })

@app.route('/abort', methods=['POST'])
def abort_preparation():
    """Abort current preparation"""
    if prep_station.status == "preparing":
        prep_station.status = "aborted"
        logger.info("Sample preparation aborted by user")
        return jsonify({"message": "Preparation aborted"})
    else:
        return jsonify({"error": "No active preparation to abort"}), 400

@app.route('/reset', methods=['POST'])
def reset_instrument():
    """Reset instrument to idle state"""
    prep_station.status = "idle"
    prep_station.current_task = None
    prep_station.results = {}
    prep_station.start_time = None
    logger.info("Instrument reset to idle state")
    return jsonify({"message": "Instrument reset successful"})

if __name__ == '__main__':
    logger.info("Starting Sample Preparation Station on port 5002")
    app.run(host='0.0.0.0', port=5002, debug=False)