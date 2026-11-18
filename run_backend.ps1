Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " Starting SkillSphere Backend API Server (FastAPI)       " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Set-Location -Path "$PSScriptRoot\backend"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
