#!/usr/bin/env python3
"""
Start all PAT workflow instrument simulators
"""

import subprocess
import time
import sys
import os
from pathlib import Path
import requests
import threading

# Instrument configurations
INSTRUMENTS = [
    {
        "name": "Weight Balance",
        "script": "instruments/weight_balance_simulator.py", 
        "port": 5011,
        "endpoint": "http://localhost:5011"
    },
    {
        "name": "Mixer",
        "script": "instruments/mixer_simulator.py",
        "port": 5012, 
        "endpoint": "http://localhost:5012"
    },
    {
        "name": "NIR Spectrometer",
        "script": "instruments/nir_simulator.py",
        "port": 5013,
        "endpoint": "http://localhost:5013"
    }
]

def check_port_available(port):
    """Check if port is available"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    return result != 0

def start_instrument(instrument):
    """Start a single instrument simulator"""
    script_path = Path(instrument["script"])
    
    if not script_path.exists():
        print(f"ERROR: Script not found: {script_path}")
        return None
    
    if not check_port_available(instrument["port"]):
        print(f"WARNING: Port {instrument['port']} already in use for {instrument['name']}")
        return None
    
    try:
        print(f"Starting {instrument['name']} on port {instrument['port']}...")
        
        # Start the instrument simulator
        process = subprocess.Popen(
            [sys.executable, str(script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        return process
        
    except Exception as e:
        print(f"ERROR: Failed to start {instrument['name']}: {e}")
        return None

def wait_for_instrument(instrument, timeout=30):
    """Wait for instrument to be ready"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{instrument['endpoint']}/status", timeout=2)
            if response.status_code == 200:
                print(f"SUCCESS: {instrument['name']} is ready!")
                return True
        except:
            pass
        time.sleep(1)
    
    print(f"ERROR: {instrument['name']} failed to start within {timeout}s")
    return False

def test_instruments():
    """Test all instrument endpoints"""
    print("\n" + "="*50)
    print("Testing instrument endpoints...")
    print("="*50)
    
    all_healthy = True
    
    for instrument in INSTRUMENTS:
        try:
            print(f"\nTesting {instrument['name']}...")
            
            # Test status endpoint
            response = requests.get(f"{instrument['endpoint']}/status", timeout=5)
            if response.status_code == 200:
                status = response.json()
                print(f"  Status: {status.get('status', 'unknown')}")
                print(f"  Connected: {status.get('connected', 'unknown')}")
                print(f"  Model: {status.get('model', 'unknown')}")
                
                # Test home endpoint
                home_response = requests.get(instrument['endpoint'], timeout=5)
                if home_response.status_code == 200:
                    print("  SUCCESS: All endpoints responding")
                else:
                    print("  WARNING: Home endpoint not responding")
                    all_healthy = False
            else:
                print(f"  ERROR: Status endpoint returned {response.status_code}")
                all_healthy = False
                
        except Exception as e:
            print(f"  ERROR: Error testing {instrument['name']}: {e}")
            all_healthy = False
    
    print(f"\n{'SUCCESS: All instruments healthy!' if all_healthy else 'WARNING: Some instruments have issues'}")
    return all_healthy

def main():
    """Main function to start all simulators"""
    print("PAT Workflow Instrument Simulators")
    print("="*50)
    
    # Check Python dependencies
    required_modules = ['flask', 'flask_cors', 'numpy', 'requests']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print(f"ERROR: Missing required modules: {', '.join(missing_modules)}")
        print("Install with: pip install flask flask-cors numpy requests")
        sys.exit(1)
    
    processes = []
    
    try:
        # Start all instruments
        for instrument in INSTRUMENTS:
            process = start_instrument(instrument)
            if process:
                processes.append((instrument, process))
        
        if not processes:
            print("ERROR: No instruments started successfully")
            sys.exit(1)
        
        # Wait for all instruments to be ready
        print(f"\nWaiting for {len(processes)} instruments to start...")
        time.sleep(3)  # Give processes time to start
        
        ready_count = 0
        for instrument, process in processes:
            if wait_for_instrument(instrument):
                ready_count += 1
        
        print(f"\nSUCCESS: {ready_count}/{len(processes)} instruments started successfully!")
        
        if ready_count > 0:
            # Test all instruments
            test_instruments()
            
            # Keep running
            print(f"\nInstrument simulators running...")
            print("Available endpoints:")
            for instrument in INSTRUMENTS:
                if any(i['name'] == instrument['name'] for i, p in processes):
                    print(f"  {instrument['name']}: {instrument['endpoint']}")
            
            print("\nPress Ctrl+C to stop all simulators")
            
            # Monitor processes
            while True:
                time.sleep(10)
                
                # Check if any process died
                for i, (instrument, process) in enumerate(processes):
                    if process.poll() is not None:
                        print(f"WARNING: {instrument['name']} simulator stopped unexpectedly")
                        # Could restart here if needed
                
        else:
            print("ERROR: No instruments are ready")
            
    except KeyboardInterrupt:
        print("\nStopping all instrument simulators...")
        
        for instrument, process in processes:
            print(f"  Stopping {instrument['name']}...")
            process.terminate()
            try:
                process.wait(timeout=5)
                print(f"  SUCCESS: {instrument['name']} stopped")
            except subprocess.TimeoutExpired:
                print(f"  Force killing {instrument['name']}...")
                process.kill()
                process.wait()
        
        print("SUCCESS: All simulators stopped")
    
    except Exception as e:
        print(f"ERROR: {e}")
        
        # Clean up processes
        for instrument, process in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()

if __name__ == "__main__":
    main()