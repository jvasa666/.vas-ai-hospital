#!/usr/bin/env pwsh
Write-Host "Starting ZFP Hospital Services..." -ForegroundColor Cyan
docker-compose up -d
Write-Host ""
Write-Host "Services started!" -ForegroundColor Green
Write-Host "Clinical Service: http://localhost:8080/api/health" -ForegroundColor Yellow
Write-Host "Admin Service: http://localhost:3000/api/health" -ForegroundColor Yellow
Write-Host ""
Write-Host "View logs: docker-compose logs -f" -ForegroundColor Cyan
Write-Host "Stop services: docker-compose down" -ForegroundColor Cyan
