# Fase 6: plan de diagnostico real Excel

## Objetivo

Analizar archivos Excel reales para entender su estructura operativa antes de construir un extractor/normalizador definitivo por formato.

## Alcance

- Deteccion recursiva de archivos Excel en `data/samples`.
- Inventario por archivo y por hoja.
- Identificacion de tipologia de hoja (`WORKSHEET`, `CHARTSHEET`, `UNKNOWN`).
- Deteccion de dimensiones y densidad de contenido.
- Deteccion de posibles tablas, cabeceras y columnas candidatas de presupuesto.
- Deteccion de celdas combinadas, formulas y formatos numericos.
- Registro de riesgos y `manual_review` por archivo.

## Fuera de alcance

- Importacion al master.
- Calculo de ratios.
- Consolidacion de importes.
- Normalizacion final de categorias.
- Decisiones de negocio final sobre mapeo.

## Restricciones activas

- No modificar RAW.
- No subir muestras reales ni reports sensibles.
- No inferir datos ausentes.
- No forzar interpretaciones economicas finales.

## Contrato minimo del diagnostico Excel

Salida JSON por archivo:

- `file_ref`
- `workbook_status`
- `supported_extension`
- `sheets`
- `summary`
- `risks`
- `manual_review`

Por hoja `WORKSHEET`:

- `sheet_name`
- `sheet_type`
- `dimensions`
- `non_empty_rows`
- `non_empty_columns`
- `possible_tables`
- `candidate_headers`
- `candidate_columns`
- `merged_cells_count`
- `formula_cells_count`
- `numeric_format_samples`
- `is_empty_sheet`
- `is_likely_tabular`

## Estrategia tecnica

1. Reutilizar `openpyxl` en modo no destructivo.
2. Soportar extensiones comunes (`.xlsx`, `.xlsm`) y marcar `legacy/unsupported` (`.xls`, `.xlsb`) sin fallo global.
3. Aplicar heuristicas de cabecera/columnas candidatas con palabras clave (codigo, descripcion, unidad, cantidad, precio, importe).
4. Separar `risks` vs `manual_review` para no bloquear en exceso.

## Outputs

- `reports/excel_diagnostics/excel_diagnostics_inventory.json`
- `reports/excel_diagnostics/excel_diagnostics_inventory_report.md`

## Tests

- Fixtures sinteticas unicamente.
- Cobertura minima:
  - workbook con worksheet;
  - workbook con chartsheet;
  - hoja vacia;
  - tabla simple;
  - cabeceras candidatas;
  - columnas candidatas de cantidad/precio/importe;
  - formulas;
  - celdas combinadas;
  - input no modificado.

## Riesgos esperados

- Hojas no tabulares mezcladas con hojas de datos.
- Encabezados no estandarizados.
- Uso extensivo de formulas y celdas combinadas.
- Multiples tablas en una misma hoja.

## Criterio de salida de Fase 6

- Diagnostico Excel reproducible, con reportes JSON/Markdown locales.
- Heuristicas basicas validadas por tests sinteticos.
- Evidencia suficiente para definir alcance tecnico de Fase 7 (extractor/normalizador Excel).
