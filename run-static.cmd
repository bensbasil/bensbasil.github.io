@echo off
cd /d "%~dp0"
echo Starting static GitHub Pages frontend at http://127.0.0.1:5500/
python -m http.server 5500 --bind 127.0.0.1
