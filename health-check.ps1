Write-Host "Health Check - LUV Obras Ratios" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

function Test-HttpEndpoint {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Url
    )

    try {
        $status = & curl.exe -sS -o NUL -w "%{http_code}" $Url
        return $status -match "^(200|301|302)$"
    } catch {
        return $false
    }
}

Write-Host "`nBackend (puerto 8000):" -ForegroundColor Cyan
if (Test-HttpEndpoint -Url "http://localhost:8000/docs") {
    Write-Host "  Respondiendo" -ForegroundColor Green
} else {
    Write-Host "  No responde" -ForegroundColor Red
}

Write-Host "`nFrontend (puerto 5173):" -ForegroundColor Cyan
if (Test-HttpEndpoint -Url "http://localhost:5173") {
    Write-Host "  Respondiendo" -ForegroundColor Green
} else {
    Write-Host "  No responde" -ForegroundColor Red
}

Write-Host "`nBase de Datos:" -ForegroundColor Cyan
$dbPath = "data/master/ratios.db"
if (Test-Path $dbPath) {
    $sizeKb = (Get-Item $dbPath).Length / 1KB
    Write-Host ("  Existe ({0} KB)" -f [math]::Round($sizeKb, 2)) -ForegroundColor Green
} else {
    Write-Host "  No existe" -ForegroundColor Red
}

Write-Host "`nAPI Test:" -ForegroundColor Cyan
try {
    $jsonText = & curl.exe -sS "http://localhost:8000/api/master"
    $data = $jsonText | ConvertFrom-Json
    Write-Host "  /api/master responde" -ForegroundColor Green
    Write-Host "  Presupuestos: $($data.metadata.total_budgets)" -ForegroundColor Gray
    Write-Host "  Ratios: $($data.metadata.total_ratios)" -ForegroundColor Gray
} catch {
    Write-Host "  API no responde" -ForegroundColor Red
}

Write-Host "`n=================================" -ForegroundColor Green
