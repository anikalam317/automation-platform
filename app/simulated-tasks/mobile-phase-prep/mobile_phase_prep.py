"""
This module provides a simulated laboratory environment for preparing a mobile
phase. It includes things like:
- Preparing a mobile phase with specified components and concentrations. To do
  this it will mock turn on pumps and valves and monitor the volume of each
  mobilie phase being pumped into a container.
- Using a liquid handler to pipet smaller portions of liquids needed for the
  mobile phase mixture.
- Using a power dispenser to add solid components to the mobile phase.
- Using a robotic arm to transfer the prepared mobile phase to a heated
  stirring plate for mixing.
- Operating the stir plate and heating it to the desired temperature
- Sending a notification to a scientist that the mobile phase is ready for use.
- Sending a notification back to the Laboratory Automation Framework (LAF) that
  the mobile phase preparation is complete.
"""

import time
import threading
import requests
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

SIM_SPEED = float(os.environ.get("SIM_SPEED", "1.0"))
MAIN_PLATFORM_URL = os.environ.get(
    "MAIN_PLATFORM_URL", "http://web:5000/api/task/progress"
)

# Lock to ensure only one simulation runs at a time
task_lock = threading.Lock()
current_task_id = None


def notify_platform(task_id, status, step, message=None):
    payload = {
        "task_id": task_id,
        "status": status,
        "step": step,
        "message": message,
    }
    try:
        requests.post(MAIN_PLATFORM_URL, json=payload, timeout=5)
    except Exception as e:
        print(f"Failed to notify platform: {e}")


def simulate_mobile_phase_prep(task_id, params):
    global current_task_id
    steps = [
        ("prepare_components", "Preparing mobile phase components"),
        ("pump_liquids", "Pumping liquids into container"),
        ("pipet_liquids", "Pipetting small portions"),
        ("add_solids", "Adding solid components"),
        ("transfer_to_stir_plate", "Transferring to heated stir plate"),
        ("stir_and_heat", "Stirring and heating"),
        ("notify_scientist", "Notifying scientist mobile phase is ready"),
        ("notify_laf", "Notifying LAF preparation is complete"),
    ]
    try:
        for step_code, step_desc in steps:
            notify_platform(task_id, "in_progress", step_code, step_desc)
            time.sleep(2 * SIM_SPEED)
        notify_platform(
            task_id, "completed", "all", "Mobile phase preparation complete"
        )
    except Exception as e:
        notify_platform(task_id, "error", "exception", f"Error: {e}")
    finally:
        with task_lock:
            current_task_id = None


@app.route("/simulate/mobile-phase-prep", methods=["POST"])
def start_simulation():
    global current_task_id
    data = request.json
    task_id = data.get("task_id")
    params = data.get("params", {})
    if not task_id:
        return jsonify({"error": "Missing task_id"}), 400
    with task_lock:
        if current_task_id is not None:
            return jsonify(
                {"error": "Instrument busy", "current_task_id": current_task_id}
            ), 409
        current_task_id = task_id
        threading.Thread(
            target=simulate_mobile_phase_prep, args=(task_id, params)
        ).start()
    return jsonify({"status": "started", "task_id": task_id})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
