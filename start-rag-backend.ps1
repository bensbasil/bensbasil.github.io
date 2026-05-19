Set-Location -LiteralPath $PSScriptRoot
Set-Location -LiteralPath ".\backend"

$python = ".\venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    $python = "python"
}

& $python -m uvicorn app.main:app --host 127.0.0.1 --port 8002
