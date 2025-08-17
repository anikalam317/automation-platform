@echo off
echo ========================================
echo Laboratory Automation Framework Demo
echo ========================================
echo.
echo Starting all services...
echo.

echo [1/3] Starting Backend API...
start "Backend API" cmd /k "python demo_backend.py"
timeout /t 3 /nobreak >nul

echo [2/3] Starting Instrument Simulators...
start "Instrument Simulators" cmd /k "cd scripts && npm start"
timeout /t 3 /nobreak >nul

echo [3/3] Starting Frontend...
start "Frontend" cmd /k "npm run dev"
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo All services started!
echo ========================================
echo.
echo Frontend:              http://localhost:3000
echo Backend API:           http://localhost:8000
echo API Documentation:     http://localhost:8000/docs
echo.
echo Instrument Simulators:
echo - HPLC System:         http://localhost:8001
echo - GC-MS System:        http://localhost:8002
echo - Liquid Handler:      http://localhost:8003
echo - Analytical Balance:  http://localhost:8004
echo - Sample Storage:      http://localhost:8005
echo.
echo Press any key to open the frontend application...
pause >nul
start http://localhost:3000