@echo off
cd /d "%~dp0"

start "Portfolio Static Frontend" cmd /k call "%~dp0run-static.cmd"
start "Portfolio API Backend" cmd /k call "%~dp0run-api.cmd"
start "Medical RAG API Backend" cmd /k call "%~dp0run-rag-api.cmd"

echo Started local project windows.
echo Frontend: http://localhost:5500/
echo Portfolio API docs: http://localhost:8000/docs
echo Medical RAG API health: http://localhost:8002/api/health
