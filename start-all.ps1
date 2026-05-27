Write-Host "Iniciando LUV Obras Ratios..." -ForegroundColor Green

$projectRoot = $PSScriptRoot
$dbPath = Join-Path $projectRoot "data/master/ratios.db"

if (-not (Test-Path $dbPath) -or (Get-Item $dbPath).Length -eq 0) {
    Write-Host "Inicializando BD SQLite..." -ForegroundColor Yellow
    python (Join-Path $projectRoot "scripts/init_db.py")
}

Write-Host "Lanzando backend en una nueva ventana..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$projectRoot'; python -m uvicorn app.main:app --reload --port 8000"

Start-Sleep -Seconds 3

$frontendRoot = Join-Path $projectRoot "frontend"
Write-Host "Lanzando frontend en una nueva ventana..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$frontendRoot'; npm run dev"

Start-Sleep -Seconds 5

Write-Host "Abriendo navegador..." -ForegroundColor Green
Start-Process "http://localhost:5173"

Write-Host "Backend: http://localhost:8000/docs" -ForegroundColor Gray
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Gray
Write-Host "BD: data/master/ratios.db" -ForegroundColor Gray
