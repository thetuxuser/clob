$ErrorActionPreference = 'Stop'

Write-Host "Uninstalling clob..." -ForegroundColor Cyan
& python -m pip uninstall clob -y --quiet
Write-Host "clob uninstalled." -ForegroundColor Green
Write-Host "Config files remain at: $env:USERPROFILE\.config\clob\" -ForegroundColor Yellow
Write-Host "Remove them manually if desired."
