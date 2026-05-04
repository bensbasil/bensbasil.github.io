@echo off
setlocal
cd /d "%~dp0backend"

set "PY=python"
if exist "venv\Scripts\python.exe" set "PY=venv\Scripts\python.exe"

echo Starting Portfolio FastAPI backend at http://127.0.0.1:8000/
echo API docs: http://127.0.0.1:8000/docs
"%PY%" -m uvicorn main:app --host 127.0.0.1 --port 8000
