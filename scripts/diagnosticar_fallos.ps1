# Script diagnostico: Por que fallaron los parsers

$dir = "C:\Users\a.alarcon\Desktop\Cursor projects\luv _obras_ratios\data\samples\PRESUPUESTOS"
$files = Get-ChildItem $dir -File

Write-Host "DIAGNOSTICO DE FALLOS DE PARSEO"
Write-Host "======================================`n"

$diagnostics = @()

foreach ($file in $files | Sort-Object Name) {
    $name = $file.Name
    $ext = $file.Extension.ToLower()
    $result = @{
        file = $name
        ext = $ext
        status = "unknown"
        reason = ""
        lines_found = 0
    }

    Write-Host -NoNewline "[$($file.Basename)]... "

    if ($ext -eq ".xlsx") {
        try {
            $excel = New-Object -ComObject Excel.Application
            $excel.Visible = $false
            $excel.DisplayAlerts = $false

            $wb = $excel.Workbooks.Open($file.FullName)
            $ws = $wb.ActiveSheet
            $range = $ws.UsedRange

            $rows = $range.Rows.Count
            $cols = $range.Columns.Count

            # Buscar patron simple: detectar si hay datos numericos en la primera columna
            $numeric_count = 0
            for ($r = 1; $r -le [Math]::Min(10, $rows); $r++) {
                $val = $ws.Cells($r, 1).Value2
                if ($val -match '^\d+$') { $numeric_count++ }
            }

            $wb.Close()

            if ($numeric_count -ge 2) {
                $result.status = "OK_STRUCTURE"
                $result.reason = "Estructura OK (nums en col1)"
                $result.lines_found = $rows - 1
                Write-Host "OK (estructura valida)"
            } else {
                $result.status = "INVALID_STRUCTURE"
                $result.reason = "No hay estructura numerada"
                Write-Host "FAIL (sin estructura)"
            }
        } catch {
            $result.status = "ERROR"
            $result.reason = "Error Excel: $($_.Exception.Message)"
            Write-Host "ERROR"
        } finally {
            if ($excel) { $excel.Quit(); [System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel) | Out-Null }
        }
    }
    elseif ($ext -in @(".bc3", ".pzh", ".presto")) {
        try {
            $content = Get-Content $file.FullName -Encoding UTF8 -ErrorAction Stop
            $lines = $content.Count

            # Buscar lineas con patron numerico (flexibilizado)
            $pattern_matches = 0
            $sample_lines = @()

            $content_lines = $content -split "`n"
            foreach ($line in $content_lines | Select-Object -First 100) {
                $line = $line.Trim()

                # Patron relajado: numero al inicio + texto + numeros
                if ($line -match '^\s*\d+\s+.+\s+[\d,\.]+') {
                    $pattern_matches++
                    if ($sample_lines.Count -lt 3) { $sample_lines += $line }
                }
            }

            if ($pattern_matches -ge 2) {
                $result.status = "OK_FORMAT"
                $result.reason = "Formato valido (patrones numericos encontrados)"
                $result.lines_found = $pattern_matches
                Write-Host "OK (patron encontrado)"
            } else {
                $result.status = "INVALID_FORMAT"
                $result.reason = "No hay patron numerico esperado"
                Write-Host "FAIL (sin patron numerico)"
            }
        } catch {
            $result.status = "ERROR"
            $result.reason = "Error lectura: $($_.Exception.Message)"
            Write-Host "ERROR"
        }
    }
    else {
        $result.status = "UNSUPPORTED"
        $result.reason = "Extension no soportada"
        Write-Host "SKIP (no soportado)"
    }

    $diagnostics += $result
}

Write-Host "`n======================================`n"
Write-Host "RESUMEN DIAGNOSTICO`n"

$by_status = $diagnostics | Group-Object -Property status

foreach ($group in $by_status) {
    Write-Host "$($group.Name): $($group.Count) archivos"
    foreach ($item in $group.Group) {
        Write-Host "  - $($item.file) ($($item.reason))"
    }
    Write-Host ""
}

# Estadisticas
$ok_count = @($diagnostics | Where-Object { $_.status -like "OK*" }).Count
$fail_count = @($diagnostics | Where-Object { $_.status -eq "INVALID_STRUCTURE" -or $_.status -eq "INVALID_FORMAT" }).Count
$error_count = @($diagnostics | Where-Object { $_.status -eq "ERROR" }).Count
$skip_count = @($diagnostics | Where-Object { $_.status -eq "UNSUPPORTED" }).Count

Write-Host "TOTALES:`n"
Write-Host "  Potencialmente importables: $ok_count"
Write-Host "  Estructura invalida: $fail_count"
Write-Host "  Errores de lectura: $error_count"
Write-Host "  No soportados: $skip_count"
Write-Host "  Total archivos: $($diagnostics.Count)`n"
