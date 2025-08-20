#!/usr/bin/env python3
"""
HPLC Analysis System Instrument
Simulates a High-Performance Liquid Chromatography system for pharmaceutical analysis
"""

import time
import json
import random
import math
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
import threading
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HPLCSystem:
    def __init__(self):
        self.status = "idle"
        self.current_analysis = None
        self.results = {}
        self.run_time = 0
        self.start_time = None
        self.column_temperature = 25.0
        self.flow_rate = 1.0
        self.pressure = 0.0
        
    def run_analysis(self, sample_id, method, injection_volume, runtime_minutes):
        """Simulate HPLC analysis process"""
        self.status = "equilibrating"
        self.start_time = datetime.now()
        self.run_time = runtime_minutes * 60  # Convert to seconds
        self.current_analysis = {
            "sample_id": sample_id,
            "method": method,
            "injection_volume": injection_volume,
            "runtime_minutes": runtime_minutes
        }
        
        logger.info(f"Starting HPLC analysis for {sample_id} using method {method}")
        
        # Simulate HPLC run phases with fast timing for testing  
        phases = [
            ("System equilibration", 10, "equilibrating"),
            ("Sample injection", 5, "injecting"),
            ("Chromatographic separation", 45, "running"),  # Fixed 45 seconds instead of runtime_minutes * 60
            ("Data processing", 10, "processing"),
            ("System flush", 10, "flushing")
        ]
        
        total_time = sum(phase[1] for phase in phases)
        
        for phase_name, duration, status in phases:
            self.status = status
            logger.info(f"Phase: {phase_name} (duration: {duration}s)")
            
            # Simulate real-time parameter updates during run
            if status == "running":
                self._simulate_chromatography_run(duration)
            else:
                time.sleep(duration)
            
            # Simulate pressure fluctuations
            if status in ["running", "equilibrating"]:
                self.pressure = random.uniform(150, 200)  # bar
                self.flow_rate = random.uniform(0.98, 1.02)  # mL/min
        
        # Generate realistic chromatographic results
        self.results = self._generate_analysis_results(sample_id, method, injection_volume)
        
        self.status = "completed"
        logger.info(f"HPLC analysis completed for {sample_id}")
        return self.results
    
    def _simulate_chromatography_run(self, duration):
        """Simulate the actual chromatographic separation with real-time updates"""
        steps = max(10, duration // 30)  # Update every 30 seconds or 10 steps minimum
        step_time = duration / steps
        
        for step in range(steps):
            time.sleep(step_time)
            
            # Simulate detector signal changes
            progress = (step + 1) / steps
            self.pressure = 150 + 50 * math.sin(progress * math.pi) + random.uniform(-5, 5)
            
            # Log significant events during run
            if progress > 0.3 and progress < 0.35:
                logger.info("Peak detected at 5.2 min - Main compound")
            elif progress > 0.7 and progress < 0.75:
                logger.info("Peak detected at 12.8 min - Impurity A")
    
    def _generate_analysis_results(self, sample_id, method, injection_volume):
        """Generate realistic HPLC analysis results"""
        
        # Simulate peak data
        peaks = [
            {
                "retention_time": 5.23 + random.uniform(-0.1, 0.1),
                "area": random.uniform(950000, 1050000),
                "height": random.uniform(45000, 55000),
                "compound": "Main Active Ingredient",
                "purity_percent": random.uniform(98.5, 99.8)
            },
            {
                "retention_time": 12.84 + random.uniform(-0.2, 0.2),
                "area": random.uniform(15000, 25000),
                "height": random.uniform(2000, 3500),
                "compound": "Impurity A",
                "purity_percent": random.uniform(0.5, 1.2)
            },
            {
                "retention_time": 18.91 + random.uniform(-0.15, 0.15),
                "area": random.uniform(5000, 12000),
                "height": random.uniform(800, 1500),
                "compound": "Impurity B",
                "purity_percent": random.uniform(0.1, 0.8)
            }
        ]
        
        # Calculate total purity
        total_purity = sum(peak["purity_percent"] for peak in peaks)
        main_compound_purity = peaks[0]["purity_percent"]
        
        # System performance metrics
        theoretical_plates = random.randint(8000, 12000)
        resolution = random.uniform(2.1, 4.5)
        baseline_noise = random.uniform(0.5, 2.0)
        
        return {
            "sample_id": sample_id,
            "analysis_completed": datetime.now().isoformat(),
            "method": method,
            "injection_volume_ul": injection_volume,
            "actual_runtime_minutes": self.run_time / 60,
            "column_temperature_c": 30.0,
            "flow_rate_ml_min": 1.0,
            "max_pressure_bar": max(180, self.pressure),
            "peaks": peaks,
            "summary": {
                "main_compound_purity": round(main_compound_purity, 2),
                "total_impurities": round(100 - main_compound_purity, 2),
                "number_of_peaks": len(peaks),
                "theoretical_plates": theoretical_plates,
                "resolution": round(resolution, 2),
                "baseline_noise": round(baseline_noise, 2)
            },
            "quality_assessment": {
                "passes_specification": main_compound_purity >= 98.0,
                "specification_limit": 98.0,
                "system_suitability": "passed" if resolution > 2.0 else "failed",
                "data_quality": "good" if baseline_noise < 2.0 else "acceptable"
            },
            "chromatogram_file": f"chromatogram_{sample_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        }

# Global instrument instance
hplc = HPLCSystem()

@app.route('/status', methods=['GET'])
def get_status():
    """Get current HPLC system status"""
    response = {
        "instrument": "HPLC System",
        "model": "Agilent 1260 Infinity II",
        "status": hplc.status,
        "current_analysis": hplc.current_analysis,
        "column_temperature_c": hplc.column_temperature,
        "flow_rate_ml_min": hplc.flow_rate,
        "pressure_bar": round(hplc.pressure, 1),
        "lamp_status": "on",
        "autosampler_ready": True,
        "available_methods": [
            "USP_assay_method",
            "related_substances",
            "dissolution_profile",
            "stability_indicating"
        ]
    }
    
    if hplc.status in ["equilibrating", "injecting", "running", "processing", "flushing"] and hplc.start_time:
        elapsed = (datetime.now() - hplc.start_time).total_seconds()
        total_estimated = hplc.run_time + 70  # Add overhead time
        response["elapsed_time_seconds"] = round(elapsed, 1)
        response["estimated_total_time"] = total_estimated
        response["progress_percent"] = min(100, round((elapsed / total_estimated) * 100, 1))
    
    return jsonify(response)

@app.route('/analyze', methods=['POST'])
def run_analysis():
    """Execute HPLC analysis"""
    try:
        data = request.get_json()
        
        # Validate required parameters
        required_params = ['sample_id', 'method', 'injection_volume', 'runtime_minutes']
        for param in required_params:
            if param not in data:
                return jsonify({"error": f"Missing required parameter: {param}"}), 400
        
        if hplc.status != "idle":
            return jsonify({"error": "HPLC system is currently busy"}), 409
        
        sample_id = data['sample_id']
        method = data['method']
        injection_volume = float(data['injection_volume'])
        runtime_minutes = float(data['runtime_minutes'])
        
        # Validate parameters
        if injection_volume <= 0 or injection_volume > 100:
            return jsonify({"error": "Injection volume must be between 0 and 100 µL"}), 400
        if runtime_minutes < 5 or runtime_minutes > 60:
            return jsonify({"error": "Runtime must be between 5 and 60 minutes"}), 400
        
        # Start analysis in background thread
        def run_hplc_analysis():
            hplc.run_analysis(sample_id, method, injection_volume, runtime_minutes)
        
        thread = threading.Thread(target=run_hplc_analysis)
        thread.daemon = True
        thread.start()
        
        estimated_total_time = (runtime_minutes * 60) + 70  # Add overhead
        
        return jsonify({
            "message": "HPLC analysis started",
            "sample_id": sample_id,
            "method": method,
            "estimated_total_time_seconds": estimated_total_time,
            "status": "equilibrating"
        }), 202
        
    except Exception as e:
        logger.error(f"Error starting HPLC analysis: {str(e)}")
        return jsonify({"error": f"Analysis failed to start: {str(e)}"}), 500

@app.route('/results', methods=['GET'])
def get_results():
    """Get analysis results"""
    if not hplc.results:
        return jsonify({"error": "No analysis results available"}), 404
    
    return jsonify({
        "results": hplc.results,
        "instrument_status": hplc.status
    })

@app.route('/abort', methods=['POST'])
def abort_analysis():
    """Abort current analysis"""
    if hplc.status in ["equilibrating", "injecting", "running", "processing"]:
        hplc.status = "aborted"
        logger.info("HPLC analysis aborted by user")
        return jsonify({"message": "Analysis aborted"})
    else:
        return jsonify({"error": "No active analysis to abort"}), 400

@app.route('/reset', methods=['POST'])
def reset_system():
    """Reset HPLC system to idle state"""
    hplc.status = "idle"
    hplc.current_analysis = None
    hplc.results = {}
    hplc.start_time = None
    hplc.pressure = 0.0
    logger.info("HPLC system reset to idle state")
    return jsonify({"message": "System reset successful"})

@app.route('/maintenance', methods=['GET'])
def maintenance_status():
    """Get maintenance information"""
    return jsonify({
        "last_maintenance": "2024-01-10",
        "next_maintenance_due": "2024-04-10",
        "column_usage_hours": 245,
        "column_max_hours": 1000,
        "lamp_hours": 1250,
        "lamp_max_hours": 2000,
        "pump_seal_replacements": 3,
        "system_uptime_percent": 98.5
    })

if __name__ == '__main__':
    logger.info("Starting HPLC System on port 5003")
    app.run(host='0.0.0.0', port=5003, debug=False)