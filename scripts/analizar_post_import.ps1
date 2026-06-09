# Script PowerShell: Auditoria post-importacion (FASE 2)
# Analiza resultados en BD SQLite

param(
    [string]$DbPath = "data/master/ratios.db",
    [string]$LogsDir = "logs"
)

$ErrorActionPreference = "Continue"

# Setup
$timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$auditLogFile = Join-Path $LogsDir "auditoria_$timestamp.log"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] [$Level] $Message"
    Write-Host $line
    Add-Content -Path $auditLogFile -Value $line
}

Write-Log "========================================" "INFO"
Write-Log "INICIANDO AUDITORIA POST-IMPORTACION" "INFO"
Write-Log "BD: $DbPath" "INFO"
Write-Log "========================================" "INFO"

# Check database exists
if (-not (Test-Path $DbPath)) {
    Write-Log "Base de datos no encontrada: $DbPath" "ERROR"
    Write-Log "Probablemente no se han importado datos aun" "WARNING"
    exit 1
}

# Load SQLite
try {
    Add-Type -Path "app/lib/System.Data.SQLite.dll" -EA SilentlyContinue
    Write-Log "SQLite library loaded" "DEBUG"
}
catch {
    Write-Log "SQLite assembly not available" "WARNING"
    Write-Log "Ejecuta: python scripts/analyze_imports.py" "INFO"
    exit 1
}

# Connect
$connStr = "Data Source=$DbPath;Version=3;"
$conn = $null

try {
    $conn = New-Object System.Data.SQLite.SQLiteConnection($connStr)
    $conn.Open()
    Write-Log "Conexion a BD establecida" "INFO"
}
catch {
    Write-Log "Error conectando a BD: $_" "ERROR"
    exit 1
}

# Query: Total items
$cmd = $conn.CreateCommand()
$cmd.CommandText = "SELECT COUNT(*) FROM item_master"

try {
    $totalItems = $cmd.ExecuteScalar()
    Write-Log "Total items en BD: $totalItems" "INFO"
}
catch {
    Write-Log "Error consultando BD: $_" "ERROR"
    Write-Log "Verificar si las tablas existen" "WARNING"
    $conn.Close()
    exit 1
}

# Query: Distribution by confidence
Write-Log "Consultando distribucion por confianza..." "INFO"
$cmd.CommandText = @"
SELECT
  estado_confiabilidad,
  COUNT(*) as cantidad
FROM item_master
GROUP BY estado_confiabilidad
ORDER BY cantidad DESC
"@

$confDist = @{}
$reader = $cmd.ExecuteReader()
while ($reader.Read()) {
    $estado = $reader["estado_confiabilidad"]
    $cant = $reader["cantidad"]
    $confDist[$estado] = $cant
}
$reader.Close()

# Query: Top 10 chapters
Write-Log "Consultando capitulos..." "INFO"
$cmd.CommandText = @"
SELECT
  COALESCE(capitulo, 'SIN_CAPITULO') as cap,
  COUNT(*) as items,
  ROUND(AVG(muestras_count), 1) as prom_muestras
FROM item_master
GROUP BY capitulo
ORDER BY prom_muestras DESC
LIMIT 10
"@

$topChapters = @()
$reader = $cmd.ExecuteReader()
while ($reader.Read()) {
    $topChapters += @{
        cap = $reader["cap"]
        items = $reader["items"]
        prom = $reader["prom_muestras"]
    }
}
$reader.Close()

$conn.Close()

# Report
Write-Log "" "INFO"
Write-Log "" "INFO"
Write-Log "=====================================================" "INFO"
Write-Log "REPORTE AUDITORIA POST-IMPORTACION" "INFO"
Write-Log "=====================================================" "INFO"
Write-Log "" "INFO"

Write-Log "FECHA: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" "INFO"
Write-Log "" "INFO"

Write-Log "RESUMEN GENERAL" "INFO"
Write-Log "=====================================================" "INFO"
Write-Log "Total items (ItemMaster): $totalItems" "INFO"

if ($totalItems -eq 0) {
    Write-Log "No se encontraron items en la BD" "WARNING"
    Write-Log "Ejecuta la importacion primero" "INFO"
    Write-Log "" "INFO"
    exit 0
}

Write-Log "" "INFO"

Write-Log "DISTRIBUCION POR CONFIANZA" "INFO"
Write-Log "=====================================================" "INFO"

foreach ($estado in $confDist.Keys) {
    $cant = $confDist[$estado]
    $pct = [Math]::Round(($cant / $totalItems) * 100, 1)
    Write-Log "$estado : $cant items ($pct%)" "INFO"
}

Write-Log "" "INFO"

if ($topChapters.Count -gt 0) {
    Write-Log "TOP CAPITULOS POR MUESTRAS" "INFO"
    Write-Log "=====================================================" "INFO"

    foreach ($cap in $topChapters) {
        Write-Log "$($cap.cap) : N=$($cap.prom) items=$($cap.items)" "INFO"
    }
} else {
    Write-Log "No hay datos de capitulos" "WARNING"
}

Write-Log "" "INFO"
Write-Log "LOGS: $auditLogFile" "INFO"
Write-Log "=====================================================" "INFO"

Write-Log "Auditoria completada" "INFO"
