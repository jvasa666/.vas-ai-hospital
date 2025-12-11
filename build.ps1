#!/usr/bin/env pwsh
Write-Host "Building ZFP Hospital Services..." -ForegroundColor Cyan
docker-compose build --no-cache
Write-Host "Build complete!" -ForegroundColor Green
