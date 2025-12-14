@echo off
echo ==========================================
echo Starting INEsCape Dashboard
echo ==========================================
echo.

cd /d "c:\Users\asus\Documents\companies\ithub\AI\products\clones\cancer diagnosing\Intelligent-software-for-diagnosing-and-treating-esophageal-cancer"

echo Stopping existing processes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *" 2>nul
taskkill /F /IM node.exe /FI "WINDOWTITLE eq *" 2>nul
timeout /t 2 /nobreak >nul

echo.
echo Starting Backend Server on http://127.0.0.1:8001
start "INEsCape Backend" cmd /k "cd /d %CD% && python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload"

timeout /t 10 /nobreak >nul

echo.
echo Starting Frontend Server on http://localhost:3000
start "INEsCape Frontend" cmd /k "cd /d %CD%\frontend && npm run dev"

timeout /t 15 /nobreak >nul

echo.
echo ==========================================
echo Server Status
echo ==========================================
echo.
netstat -ano | findstr ":8001" | findstr "LISTENING" >nul
if %errorlevel% == 0 (
    echo [OK] Backend is listening on port 8001
) else (
    echo [ERROR] Backend is NOT running on port 8001
)

netstat -ano | findstr ":3000" | findstr "LISTENING" >nul
if %errorlevel% == 0 (
    echo [OK] Frontend is listening on port 3000
) else (
    echo [ERROR] Frontend is NOT running on port 3000
)

echo.
echo ==========================================
echo Access URLs
echo ==========================================
echo Dashboard:    http://localhost:3000/dashboard
echo Frontend:     http://localhost:3000
echo Backend API:  http://127.0.0.1:8001
echo API Docs:     http://127.0.0.1:8001/docs
echo.
echo Two command windows have been opened.
echo Check those windows for any error messages.
echo.
pause
