@echo off
setlocal
cd /d "%~dp0backend"

set "PY=python"
if exist "venv\Scripts\python.exe" set "PY=venv\Scripts\python.exe"

echo Starting Medical RAG FastAPI backend at http://127.0.0.1:8002/
echo RAG health: http://127.0.0.1:8002/api/health
"%PY%" -m uvicorn app.main:app --host 127.0.0.1 --port 8002
