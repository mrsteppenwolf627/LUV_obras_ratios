# Script PowerShell: Importacion masiva de presupuestos (FASE 1)

param(
    [string]$PresupuestosDir = "C:\Users\a.alarcon\Desktop\Cursor projects\luv _obras_ratios\data\samples\PRESUPUESTOS",
    [string]$ApiUrl = "http://localhost:8000/api/import/budgets",
    [switch]$DryRun = $false
)

$ErrorActionPreference = "Continue"
$VerbosePreference = "SilentlyContinue"

# Setup logging
$timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$logsDir = Join-Path (Split-Path $PSScriptRoot -Parent) "logs"
if (-not (Test-Path $logsDir)) { New-Item -ItemType Directory -Path $logsDir -Force | Out-Null }
$logFile = Join-Path $logsDir "importacion_masiva_$timestamp.log"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] [$Level] $Message"
    Write-Host $line
    Add-Content -Path $logFile -Value $line
}

# Statistics
$stats = @{
    total_files = 0
    xlsx_count = 0
    pzh_count = 0
    bc3_count = 0
    presto_count = 0
    processed = 0
    failed = 0
    items_created = 0
    items_duplicated = 0
    successful_imports = 0
    time_start = Get-Date
    failed_list = @()
}

Write-Log "========================================" "INFO"
Write-Log "INICIANDO IMPORTACION MASIVA DE PRESUPUESTOS" "INFO"
Write-Log "Presupuestos dir: $PresupuestosDir" "INFO"
Write-Log "Dry run: $DryRun" "INFO"
Write-Log "========================================" "INFO"

# Helper: Calculate SHA256
function Get-FileSHA256 {
    param([string]$FilePath)
    try {
        return (Get-FileHash -Path $FilePath -Algorithm SHA256).Hash.ToLower()
    }
    catch {
        Write-Log "Error SHA256 $FilePath : $_" "ERROR"
        return $null
    }
}

# Helper: Read Excel file
function Read-ExcelFile {
    param([string]$FilePath)
    $lineas = @()
    $excel = $null

    try {
        $excel = New-Object -ComObject Excel.Application
        $excel.Visible = $false
        $excel.DisplayAlerts = $false

        $wb = $excel.Workbooks.Open($FilePath)
        $ws = $wb.Sheets(1)
        $range = $ws.UsedRange

        Write-Log "Excel: $(Split-Path -Leaf $FilePath) - $($range.Rows.Count) rows" "DEBUG"

        # Read headers (row 1)
        $headers = @{}
        for ($c = 1; $c -le $range.Columns.Count; $c++) {
            $h = $ws.Cells(1, $c).Value2
            if ($h) {
                $key = $h.ToString().ToLower().Trim()
                $headers[$key] = $c
            }
        }

        # Find columns
        $descCol = -1; $cantCol = -1; $unitCol = -1; $puCol = -1; $capCol = -1
        foreach ($h in $headers.Keys) {
            if ($h -match "desc" -and $descCol -lt 0) { $descCol = $headers[$h] }
            if ($h -match "cant" -and $cantCol -lt 0) { $cantCol = $headers[$h] }
            if ($h -match "unid" -and $unitCol -lt 0) { $unitCol = $headers[$h] }
            if ($h -match "precio|pu|price" -and $puCol -lt 0) { $puCol = $headers[$h] }
            if ($h -match "cap|chapter" -and $capCol -lt 0) { $capCol = $headers[$h] }
        }

        # Read data from row 2
        for ($r = 2; $r -le $range.Rows.Count; $r++) {
            $desc = if ($descCol -gt 0) { $ws.Cells($r, $descCol).Value2 } else { "" }
            $cant = if ($cantCol -gt 0) { [double]($ws.Cells($r, $cantCol).Value2) } else { 0 }
            $unit = if ($unitCol -gt 0) { $ws.Cells($r, $unitCol).Value2 } else { "u" }
            $pu = if ($puCol -gt 0) { [double]($ws.Cells($r, $puCol).Value2) } else { 0 }
            $cap = if ($capCol -gt 0) { $ws.Cells($r, $capCol).Value2 } else { "00" }

            if ($desc -and $cant -gt 0 -and $pu -gt 0) {
                $lineas += @{
                    numero = $r - 1
                    capitulo = "$cap"
                    descripcion = "$desc"
                    cantidad = [double]$cant
                    unidad = "$unit"
                    precio_unitario = [double]$pu
                }
            }
        }

        $wb.Close($false)
    }
    catch {
        Write-Log "Error reading Excel $FilePath : $_" "WARNING"
    }
    finally {
        if ($excel) {
            $excel.Quit()
            [System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel) | Out-Null
        }
    }

    return $lineas
}

# Helper: Read text-based budget files
function Read-TextBudgetFile {
    param([string]$FilePath)
    $lineas = @()

    try {
        $content = Get-Content -Path $FilePath -Encoding UTF8 -ErrorAction SilentlyContinue
        if (-not $content) { return $lineas }

        $lines = ($content -split "`n")
        $capitulo = "00"
        $numero = 0

        foreach ($line in $lines) {
            $line = $line.Trim()

            if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith("#")) { continue }

            # Chapter detection
            if ($line -match '^\s*(\d{2,3})\s+') {
                $capitulo = $matches[1]
                continue
            }

            # Data line: number description quantity unit price
            if ($line -match '^\s*(\d+)\s+(.+?)\s+([\d,\.]+)\s+(\S+)\s+([\d,\.]+)') {
                $numero = [int]$matches[1]
                $desc = $matches[2].Trim()
                $cant = [double]($matches[3] -replace ',', '.')
                $unit = $matches[4].Trim()
                $precio = [double]($matches[5] -replace ',', '.')

                if ($cant -gt 0 -and $precio -gt 0) {
                    $lineas += @{
                        numero = $numero
                        capitulo = $capitulo
                        descripcion = $desc
                        cantidad = $cant
                        unidad = $unit
                        precio_unitario = $precio
                    }
                }
            }
        }
    }
    catch {
        Write-Log "Error reading text file $FilePath : $_" "WARNING"
    }

    return $lineas
}

# Helper: Convert to JSON
function ConvertTo-BudgetJson {
    param([string]$FilePath, [array]$Lineas)

    if ($Lineas.Count -eq 0) { return $null }

    $fileName = Split-Path -Leaf $FilePath
    $fileHash = Get-FileSHA256 -FilePath $FilePath
    if (-not $fileHash) { return $null }

    $buildingType = "residencial"
    $fileNameLower = $fileName.ToLower()
    if ($fileNameLower -like "*comercial*") { $buildingType = "comercial" }
    elseif ($fileNameLower -like "*industrial*") { $buildingType = "industrial" }

    $json = @{
        filename = $fileName
        file_hash = $fileHash
        building_type = $buildingType
        lineas = $Lineas
    } | ConvertTo-Json -Depth 10 -Compress

    return $json
}

# Main: Discover files
Write-Log "Discovering files in $PresupuestosDir..." "INFO"

if (-not (Test-Path -Path $PresupuestosDir)) {
    Write-Log "Directory not found: $PresupuestosDir" "ERROR"
    exit 1
}

$files = Get-ChildItem -Path $PresupuestosDir -File
$stats.total_files = $files.Count

Write-Log "Total files found: $($stats.total_files)" "INFO"

# Count by extension
foreach ($file in $files) {
    switch ($file.Extension.ToLower()) {
        ".xlsx" { $stats.xlsx_count++ }
        ".pzh" { $stats.pzh_count++ }
        ".bc3" { $stats.bc3_count++ }
        ".presto" { $stats.presto_count++ }
    }
}

Write-Log "Breakdown: .xlsx=$($stats.xlsx_count) .pzh=$($stats.pzh_count) .bc3=$($stats.bc3_count) .Presto=$($stats.presto_count)" "INFO"
Write-Log "" "INFO"

# Process files
$toImport = @()
Write-Log "Processing files..." "INFO"

foreach ($file in $files) {
    $fileName = $file.Name
    $filePath = $file.FullName
    $ext = $file.Extension.ToLower()

    Write-Log "Processing: $fileName" "INFO"

    $lineas = @()

    if ($ext -eq ".xlsx") {
        $lineas = Read-ExcelFile -FilePath $filePath
    }
    elseif ($ext -in @(".pzh", ".bc3", ".presto")) {
        $lineas = Read-TextBudgetFile -FilePath $filePath
    }
    else {
        Write-Log "  Skipping: unsupported format $ext" "WARNING"
        continue
    }

    if ($lineas.Count -eq 0) {
        Write-Log "  No valid lines extracted" "WARNING"
        $stats.failed++
        $stats.failed_list += @{ file = $fileName; reason = "No valid lines" }
        continue
    }

    $json = ConvertTo-BudgetJson -FilePath $filePath -Lineas $lineas
    if (-not $json) {
        Write-Log "  Invalid JSON generated" "WARNING"
        $stats.failed++
        $stats.failed_list += @{ file = $fileName; reason = "JSON generation failed" }
        continue
    }

    $toImport += @{
        fileName = $fileName
        json = $json
        lineCount = $lineas.Count
    }

    Write-Log "  Ready: $fileName ($($lineas.Count) lines)" "INFO"
    $stats.processed++
}

Write-Log "" "INFO"
Write-Log "Files to import: $($stats.processed) / Failed: $($stats.failed)" "INFO"
Write-Log "" "INFO"

if ($toImport.Count -eq 0) {
    Write-Log "No files to import. Exiting." "WARNING"
    exit 0
}

# Import via API
Write-Log "Importing to API..." "INFO"

if (-not $DryRun) {
    foreach ($item in $toImport) {
        try {
            $response = Invoke-RestMethod -Uri $ApiUrl `
                -Method POST `
                -Headers @{"Content-Type" = "application/json"} `
                -Body $item.json `
                -TimeoutSec 30 `
                -ErrorAction Stop

            $stats.items_created += $response.items_creados
            $stats.items_duplicated += $response.items_duplicados
            $stats.successful_imports++

            Write-Log "  Imported: $($item.fileName) | Created: $($response.items_creados) | Duplicated: $($response.items_duplicados)" "INFO"
        }
        catch {
            $stats.failed++
            $stats.failed_list += @{ file = $item.fileName; reason = $_.Exception.Message }
            Write-Log "  Error: $($item.fileName) - $_" "ERROR"
        }
    }
}
else {
    Write-Log "DRY RUN: No requests sent to API" "INFO"
    $stats.successful_imports = $toImport.Count
}

# Report
Write-Log "" "INFO"
Write-Log "=====================================================" "INFO"
Write-Log "REPORTE IMPORTACION MASIVA" "INFO"
Write-Log "=====================================================" "INFO"

$duration = (Get-Date) - $stats.time_start
$durationStr = "$($duration.Hours)h $($duration.Minutes)m $($duration.Seconds)s"

Write-Log "Fecha: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" "INFO"
Write-Log "Duracion: $durationStr" "INFO"
Write-Log "" "INFO"

Write-Log "RESUMEN ARCHIVOS:" "INFO"
Write-Log "  Total: $($stats.total_files)" "INFO"
Write-Log "  Procesados: $($stats.processed)" "INFO"
Write-Log "  Fallidos: $($stats.failed)" "INFO"
Write-Log "" "INFO"

Write-Log "POR TIPO:" "INFO"
Write-Log "  .xlsx: $($stats.xlsx_count)" "INFO"
Write-Log "  .pzh: $($stats.pzh_count)" "INFO"
Write-Log "  .bc3: $($stats.bc3_count)" "INFO"
Write-Log "  .Presto: $($stats.presto_count)" "INFO"
Write-Log "" "INFO"

Write-Log "IMPORTACION:" "INFO"
Write-Log "  Exitosos: $($stats.successful_imports)" "INFO"
Write-Log "  Items creados: $($stats.items_created)" "INFO"
Write-Log "  Items duplicados: $($stats.items_duplicated)" "INFO"
Write-Log "" "INFO"

if ($stats.failed_list.Count -gt 0) {
    Write-Log "ARCHIVOS FALLIDOS:" "INFO"
    foreach ($item in $stats.failed_list) {
        Write-Log "  $($item.file) - $($item.reason)" "ERROR"
    }
    Write-Log "" "INFO"
}

Write-Log "LOGS: $logFile" "INFO"
Write-Log "=====================================================" "INFO"

Write-Log "Script completed successfully" "INFO"
