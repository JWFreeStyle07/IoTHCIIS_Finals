@echo off
title BalikBisita Launcher
echo.
echo  ============================================
echo   BalikBisita IoT Dashboard Launcher
echo  ============================================
echo.

echo  Clearing any old processes on ports 1880 and 5000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":1880 "') do (
    taskkill /PID %%a /F >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5000 "') do (
    taskkill /PID %%a /F >nul 2>&1
)
timeout /t 2 /nobreak >nul

echo  Starting Flask prediction service...
start "Flask - predict_service" cmd /k "cd /d C:\Users\Jade Aerron Marges\IoT_FinalProject && venv\Scripts\python src\predict_service.py"

echo  Waiting for Flask to load (5 seconds)...
timeout /t 5 /nobreak >nul

echo  Starting Node-RED...
start "Node-RED" cmd /k "node-red"

echo  Waiting for Node-RED to load (8 seconds)...
timeout /t 8 /nobreak >nul

echo  Opening dashboard in browser...
start "" "http://localhost:1880/ui"

echo.
echo  Both services are running.
echo  Flask:     http://localhost:5000/health
echo  Editor:    http://localhost:1880
echo  Dashboard: http://localhost:1880/ui
echo.
echo  Close the two black windows to stop the services.
pause
