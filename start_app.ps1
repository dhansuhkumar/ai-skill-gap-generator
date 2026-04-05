# Startup script for AI Skill Gap Generator

Write-Host "Starting AI Skill Gap Generator..." -ForegroundColor Cyan

# 1. Start Backend
Write-Host "Starting Backend on Port 8080..." -ForegroundColor Green
$backendProcess = Start-Process -FilePath "python" -ArgumentList "-m backend.run" -WorkingDirectory "$PSScriptRoot" -PassThru -NoNewWindow

# 2. Start Frontend
Write-Host "Starting Frontend..." -ForegroundColor Green
$frontendProcess = Start-Process -FilePath "npm.cmd" -ArgumentList "run dev" -WorkingDirectory "$PSScriptRoot\frontend" -PassThru -NoNewWindow

Write-Host "Application started!" -ForegroundColor Yellow
Write-Host "Backend: http://localhost:8080"
Write-Host "Frontend: http://localhost:5173"
Write-Host "Press any key to stop servers..."

$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Cleanup
Stop-Process -Id $backendProcess.Id -ErrorAction SilentlyContinue
Stop-Process -Id $frontendProcess.Id -ErrorAction SilentlyContinue
Write-Host "Servers stopped." -ForegroundColor Red
