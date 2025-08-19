#!/bin/bash

echo "========================================"
echo "Laboratory Automation Framework Demo"
echo "========================================"
echo ""
echo "Starting all services..."
echo ""

# Check if ports are available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "Warning: Port $port is already in use"
        return 1
    fi
    return 0
}

# Start Backend API
echo "[1/3] Starting Backend API..."
if check_port 8000; then
    python3 demo_backend.py &
    BACKEND_PID=$!
    echo "Backend API started (PID: $BACKEND_PID)"
else
    echo "Port 8000 is in use. Backend may already be running."
fi

sleep 3

# Start Instrument Simulators
echo "[2/3] Starting Instrument Simulators..."
cd scripts
if check_port 8001; then
    npm start &
    SIMULATORS_PID=$!
    echo "Instrument Simulators started (PID: $SIMULATORS_PID)"
else
    echo "Simulator ports (8001-8005) may be in use."
fi
cd ..

sleep 3

# Start Frontend
echo "[3/3] Starting Frontend..."
if check_port 3000; then
    npm run dev &
    FRONTEND_PID=$!
    echo "Frontend started (PID: $FRONTEND_PID)"
else
    echo "Port 3000 is in use. Frontend may already be running."
fi

sleep 5

echo ""
echo "========================================"
echo "All services started!"
echo "========================================"
echo ""
echo "Frontend:              http://localhost:3000"
echo "Backend API:           http://localhost:8000"
echo "API Documentation:     http://localhost:8000/docs"
echo ""
echo "Instrument Simulators:"
echo "- HPLC System:         http://localhost:8001"
echo "- GC-MS System:        http://localhost:8002"
echo "- Liquid Handler:      http://localhost:8003"
echo "- Analytical Balance:  http://localhost:8004"
echo "- Sample Storage:      http://localhost:8005"
echo ""
echo "Opening frontend application..."

# Try to open browser (cross-platform)
if command -v xdg-open > /dev/null; then
    xdg-open http://localhost:3000
elif command -v open > /dev/null; then
    open http://localhost:3000
elif command -v start > /dev/null; then
    start http://localhost:3000
fi

echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap 'echo ""; echo "Stopping services..."; kill $BACKEND_PID $SIMULATORS_PID $FRONTEND_PID 2>/dev/null; exit' INT
wait