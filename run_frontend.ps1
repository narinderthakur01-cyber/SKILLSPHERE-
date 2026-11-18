Write-Host "========================================================" -ForegroundColor Green
Write-Host " Starting SkillSphere Frontend Web App (React + Vite)   " -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
Set-Location -Path "$PSScriptRoot\frontend"
npm run dev
