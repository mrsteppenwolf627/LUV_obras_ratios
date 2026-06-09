# Script PowerShell: Importacion masiva de presupuestos (FASE 3 - Parsers mejorados)

param(
    [string]$PresupuestosDir = "C:\Users\a.alarcon\Desktop\Cursor projects\luv _obras_ratios\data\samples\PRESUPUESTOS",
    [string]$ApiUrl = "http://localhost:8000/api/import/budgets"
)

$ErrorActionPreference = "Continue"

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

# Stats
$stats = @{
    total_files = 0
    processed = 0
    failed = 0
    items_created = 0
    items_duplicated = 0
    successful_imports = 0
    time_start = Get-Date
    failed_list = @()
}

Write-Log "========================================" "INFO"
Write-Log "IMPORTACION MASIVA - FASE 3 (Parsers mejorados)" "INFO"
Write-Log "Presupuestos dir: $PresupuestosDir" "INFO"
Write-Log "========================================" "INFO"

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

# PARSER 1: Excel mejorado
function Read-ExcelFileImproved {
    param([string]$FilePath)
    $lineas = @()
    $excel = $null

    try {
        $excel = New-Object -ComObject Excel.Application
        $excel.Visible = $false
        $excel.DisplayAlerts = $false

        $wb = $excel.Workbooks.Open($FilePath)

        # Iterar sobre todas las sheets
        foreach ($ws in $wb.Sheets) {
            $range = $ws.UsedRange
            $rows = $range.Rows.Count
            $cols = $range.Columns.Count

            if ($rows -lt 2) { continue }

            Write-Log "Excel sheet: $($ws.Name) ($rows filas x $cols cols)" "DEBUG"

            # Buscar header en primeras 10 filas
            $header = @{}
            for ($r = 1; $r -le [Math]::Min(10, $rows); $r++) {
                for ($c = 1; $c -le $cols; $c++) {
                    $cell = $ws.Cells($r, $c).Value2
                    if ($cell) {
                        $cellStr = $cell.ToString().ToLower().Trim()

                        if ($cellStr -match "(descripci|description|desc|partida|item|concept)" -and !$header["desc"]) {
                            $header["desc"] = $c
                        }
                        if ($cellStr -match "(cantidad|qty|quantity|units|medida|cant)" -and !$header["cant"]) {
                            $header["cant"] = $c
                        }
                        if ($cellStr -match "(precio|unitario|price|pu|rate|cost|valor)" -and !$header["precio"]) {
                            $header["precio"] = $c
                        }
                        if ($cellStr -match "(unidad|unit|um|ud|u\.)" -and !$header["unit"]) {
                            $header["unit"] = $c
                        }
                        if ($cellStr -match "(cap|chapter|section)" -and !$header["cap"]) {
                            $header["cap"] = $c
                        }
                    }
                }
                if ($header.Count -ge 3) { break }
            }

            # Extraer datos desde header+1 hasta final
            $startRow = $r + 1
            for ($r = $startRow; $r -le $rows; $r++) {
                $desc_val = if ($header["desc"]) { $ws.Cells($r, $header["desc"]).Value2 } else { $null }
                $cant_val = if ($header["cant"]) { $ws.Cells($r, $header["cant"]).Value2 } else { $null }
                $prec_val = if ($header["precio"]) { $ws.Cells($r, $header["precio"]).Value2 } else { $null }
                $unit_val = if ($header["unit"]) { $ws.Cells($r, $header["unit"]).Value2 } else { "u" }
                $cap_val = if ($header["cap"]) { $ws.Cells($r, $header["cap"]).Value2 } else { "00" }

                if ($desc_val) {
                    try {
                        $cant_num = [double]$cant_val
                        $prec_num = [double]$prec_val

                        if ($cant_num -gt 0 -and $prec_num -gt 0) {
                            $lineas += @{
                                numero = $r
                                capitulo = if ($cap_val) { "$cap_val" } else { "00" }
                                descripcion = "$desc_val"
                                cantidad = $cant_num
                                unidad = if ($unit_val) { "$unit_val" } else { "u" }
                                precio_unitario = $prec_num
                            }
                        }
                    } catch {
                        # Skip invalid rows
                    }
                }
            }
        }

        $wb.Close()
    }
    catch {
        Write-Log "Error Excel $FilePath : $_" "WARNING"
    }
    finally {
        if ($excel) {
            $excel.Quit()
            [System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel) | Out-Null
        }
    }

    return $lineas
}

# PARSER 2: BC3/Presupuestos mejorado
function Read-PresupuestoFileImproved {
    param([string]$FilePath)
    $lineas = @()

    try {
        $content = Get-Content -Path $FilePath -Encoding UTF8 -ErrorAction SilentlyContinue
        if (-not $content) { return $lineas }

        $numero = 0
        $items = @{}

        # Detectar si es BC3 (formato propietario)
        $firstLine = if ($content -is [array]) { $content[0] } else { $content }

        if ($firstLine -like "~*") {
            # BC3 Format: Extract ~C lines (concepto)
            # Format: ~C|CODIGO|UNIDAD|DESCRIPCION|PRECIO|FECHA|...
            foreach ($line in $content) {
                if ($line -match '~C\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|') {
                    $numero++
                    $unit = $matches[2]
                    $desc = $matches[3]
                    $precio_str = $matches[4]

                    if ($desc -and $desc.Length -gt 3) {
                        # Extract price, use 100 default if not found
                        $precio = 100
                        if ($precio_str -and $precio_str -match '[\d,\.]+') {
                            try {
                                $precio = [double]($precio_str -replace ',', '.')
                                if ($precio -lt 0.01) { $precio = 100 }
                            } catch {
                                $precio = 100
                            }
                        }

                        $lineas += @{
                            numero = $numero
                            capitulo = "00"
                            descripcion = $desc.Trim()
                            cantidad = 1
                            unidad = if ($unit -and $unit.Length -gt 0) { $unit.Trim() } else { "u" }
                            precio_unitario = $precio
                        }
                    }
                }
            }
        } else {
            # Plain text format: flexible pattern
            $lines = $content -split "`n"
            foreach ($line in $lines) {
                $line = $line.Trim()
                if ([string]::IsNullOrWhiteSpace($line)) { continue }

                # Flexib pattern: num + text + num + unit + num
                if ($line -match '^\s*(\d+)\s+(.+?)\s+([\d,\.]+)\s+(\S+)\s+([\d,\.]+)') {
                    $numero++
                    $desc = $matches[2].Trim()
                    $cant = [double]($matches[3] -replace ',', '.')
                    $unit = $matches[4].Trim()
                    $prec = [double]($matches[5] -replace ',', '.')

                    if ($cant -gt 0 -and $prec -gt 0) {
                        $lineas += @{
                            numero = $numero
                            capitulo = "00"
                            descripcion = $desc
                            cantidad = $cant
                            unidad = $unit
                            precio_unitario = $prec
                        }
                    }
                }
            }
        }
    }
    catch {
        Write-Log "Error reading $FilePath : $_" "WARNING"
    }

    return $lineas
}

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

# Main
Write-Log "Discovering files..." "INFO"
if (-not (Test-Path -Path $PresupuestosDir)) {
    Write-Log "Directory not found: $PresupuestosDir" "ERROR"
    exit 1
}

$files = Get-ChildItem -Path $PresupuestosDir -File
$stats.total_files = $files.Count

Write-Log "Total files: $($stats.total_files)" "INFO"

$toImport = @()
Write-Log "Processing files..." "INFO"

foreach ($file in $files) {
    $fileName = $file.Name
    $filePath = $file.FullName
    $ext = $file.Extension.ToLower()

    $lineas = @()

    if ($ext -eq ".xlsx") {
        $lineas = Read-ExcelFileImproved -FilePath $filePath
    }
    elseif ($ext -in @(".pzh", ".bc3", ".presto")) {
        $lineas = Read-PresupuestoFileImproved -FilePath $filePath
    }
    else {
        continue
    }

    if ($lineas.Count -eq 0) {
        $stats.failed++
        $stats.failed_list += @{ file = $fileName; reason = "No lines extracted" }
        continue
    }

    $json = ConvertTo-BudgetJson -FilePath $filePath -Lineas $lineas
    if (-not $json) {
        $stats.failed++
        continue
    }

    $toImport += @{ fileName = $fileName; json = $json; lineCount = $lineas.Count }
    Write-Log "Ready: $fileName ($($lineas.Count) lines)" "INFO"
    $stats.processed++
}

Write-Log "" "INFO"
Write-Log "Files to import: $($toImport.Count)" "INFO"
Write-Log "" "INFO"

if ($toImport.Count -eq 0) {
    Write-Log "No files to import." "WARNING"
    exit 0
}

# Import
Write-Log "Importing to API..." "INFO"

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

        Write-Log "Imported: $($item.fileName) | Created: $($response.items_creados) | Dup: $($response.items_duplicados)" "INFO"
    }
    catch {
        $stats.failed++
        $stats.failed_list += @{ file = $item.fileName; reason = $_.Exception.Message }
        Write-Log "Error: $($item.fileName) - $_" "ERROR"
    }
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

Write-Log "RESUMEN:" "INFO"
Write-Log "  Total files: $($stats.total_files)" "INFO"
Write-Log "  Processed: $($stats.processed)" "INFO"
Write-Log "  Failed: $($stats.failed)" "INFO"
Write-Log "  Successful imports: $($stats.successful_imports)" "INFO"
Write-Log "" "INFO"

Write-Log "ITEMS:" "INFO"
Write-Log "  Items created: $($stats.items_created)" "INFO"
Write-Log "  Items duplicated: $($stats.items_duplicated)" "INFO"
Write-Log "" "INFO"

if ($stats.failed_list.Count -gt 0) {
    Write-Log "FAILED FILES:" "INFO"
    foreach ($item in $stats.failed_list | Select-Object -First 10) {
        Write-Log "  $($item.file) - $($item.reason)" "ERROR"
    }
}

Write-Log "" "INFO"
Write-Log "LOGS: $logFile" "INFO"
Write-Log "=====================================================" "INFO"

Write-Log "Import completed" "INFO"
