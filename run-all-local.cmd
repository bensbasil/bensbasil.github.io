@echo off
cd /d "%~dp0"

start "Portfolio Static Frontend" cmd /k call "%~dp0run-static.cmd"
start "Portfolio API Backend" cmd /k call "%~dp0run-api.cmd"
start "Medical RAG API Backend" cmd /k call "%~dp0run-rag-api.cmd"
start "Medical RAG Frontend (Vite)" cmd /k "cd /d "%~dp0medical-rag-app" && npm run dev"

echo Started local project windows.
echo Static Frontend (Portfolio and Quiz): http://localhost:5500/
echo Medical RAG Frontend (React): http://localhost:5173/
echo Portfolio API docs: http://localhost:8000/docs
echo Medical RAG API health: http://localhost:8002/api/health
