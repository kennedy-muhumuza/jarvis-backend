# deactivate
# http://localhost:5000/docs
# bash run_backend.sh
# ---clean restart in bash
# taskkill //F //IM "uvicorn.exe" 2>nul; source venv/Scripts/activate; uvicorn main:app --reload
# Check running Uvicorn processes
# tasklist | find "uvicorn"

# Kill specific process
# taskkill /F /PID <PID>

# Kill all Uvicorn processes
# taskkill /F /IM "uvicorn.exe"

#!/bin/bash
# chmod +x run_backend.sh

taskkill /F /IM "uvicorn.exe" 2>/dev/null


# Start FastAPI server with auto-reload
# uvicorn main:app --host 0.0.0.0 --port 5000 --reload

#!/bin/bash

#!/bin/bash
echo "🔪 Killing any running uvicorn processes..."
taskkill /F /IM "uvicorn.exe" 2>/dev/null

echo "🚀 Starting Jarvis backend..."
source venv/Scripts/activate
uvicorn main:app --host 0.0.0.0 --port 5000 --reload --ws websockets

# Test websocket
# wscat -c ws://127.0.0.1:5000/ws





# ::CMD/Powershell

# @echo off
# call venv\Scripts\activate
# uvicorn main:app --host 0.0.0.0 --port 5000 --reload
# pause

