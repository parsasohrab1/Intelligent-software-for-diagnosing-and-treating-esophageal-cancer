# Dashboard Troubleshooting Guide

## Quick Start Commands

### Option 1: Use the Batch File
Double-click `start_dashboard.bat` or run:
```cmd
start_dashboard.bat
```

This will open two command windows - one for backend, one for frontend.

### Option 2: Manual Start

**Terminal 1 - Backend:**
```powershell
cd "c:\Users\asus\Documents\companies\ithub\AI\products\clones\cancer diagnosing\Intelligent-software-for-diagnosing-and-treating-esophageal-cancer"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

**Terminal 2 - Frontend:**
```powershell
cd "c:\Users\asus\Documents\companies\ithub\AI\products\clones\cancer diagnosing\Intelligent-software-for-diagnosing-and-treating-esophageal-cancer\frontend"
npm run dev
```

## Common Issues and Solutions

### 1. ERR_CONNECTION_REFUSED

**Check if servers are running:**
```powershell
netstat -ano | findstr "8001 3000"
```

**If nothing is listening:**
- Check the command windows for error messages
- Verify Python is installed: `python --version`
- Verify Node.js is installed: `node --version`
- Install dependencies:
  - Backend: `pip install -r requirements.txt`
  - Frontend: `cd frontend && npm install`

### 2. Port Already in Use

**Free the ports:**
```powershell
# Find process using port 8001
netstat -ano | findstr ":8001"
# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Find process using port 3000
netstat -ano | findstr ":3000"
# Kill the process
taskkill /PID <PID> /F
```

### 3. Backend Won't Start

**Common causes:**
- Missing Python dependencies: `pip install -r requirements.txt`
- Database not running: `docker-compose up -d postgres redis`
- Import errors: Check the backend window for Python errors
- Port conflict: Another service using port 8001

**Test backend import:**
```powershell
python -c "import app.main; print('OK')"
```

### 4. Frontend Won't Start

**Common causes:**
- Missing Node modules: `cd frontend && npm install`
- Port 3000 in use: Another service or previous instance
- Node.js not installed or wrong version

**Test frontend:**
```powershell
cd frontend
npm run dev
```

### 5. Database Connection Errors

**Start required services:**
```powershell
docker-compose up -d postgres redis
```

Wait 30 seconds for services to be ready, then restart backend.

## Verification Steps

1. **Check Backend:**
   - Open: http://127.0.0.1:8001/api/v1/health
   - Should return: `{"status":"healthy",...}`

2. **Check Frontend:**
   - Open: http://localhost:3000
   - Should show the dashboard

3. **Check API Docs:**
   - Open: http://127.0.0.1:8001/docs
   - Should show Swagger UI

## Access URLs

- **Dashboard**: http://localhost:3000/dashboard
- **Frontend**: http://localhost:3000
- **Backend API**: http://127.0.0.1:8001
- **API Docs**: http://127.0.0.1:8001/docs

## Still Having Issues?

1. Check the command windows for error messages
2. Verify all dependencies are installed
3. Ensure Docker services are running (if using database)
4. Check Windows Firewall isn't blocking ports
5. Try restarting your computer if ports seem stuck
