# Plan de Fase 2: análisis controlado de muestras

## 1. Propósito de Fase 2

Realizar un diagnóstico controlado de archivos reales de muestra antes de diseñar parsers definitivos, sin importar datos al master y sin calcular ratios.

## 2. Alcance

- Inventario de archivos en `data/samples`.
- Cálculo de hashes SHA256 por archivo.
- Detección preliminar de duplicados exactos por hash.
- Detección y clasificación preliminar de formatos.
- Detección de posibles copias de seguridad por nombre/ruta.
- Detección de posibles versiones y fases por nombre/ruta.
- Inspección básica no destructiva de Excel cuando sea posible.
- Inspección superficial de BC3 (muestra inicial y señal de encoding).
- Registro de PDF como fuente de referencia diagnóstica.
- Registro de Presto/PZH como pendiente de investigación de formato.

## 3. Fuera de alcance

- Importar al master.
- Calcular ratios.
- Crear parser definitivo.
- Modificar archivos originales.
- OCR.
- Extraer importes de PDF.
- Decidir versión válida.
- Decidir superficie base.
- Decidir categorías definitivas.

## 4. Relación con decisiones previas

Este plan se alinea con:

- `docs/decisions/master_schema_preliminar.md`
- `docs/decisions/duplicates_and_budget_versions_policy.md`
- `docs/decisions/validation_rules_policy.md`
- `docs/decisions/human_review_phase_1_5.md`

En particular, mantiene RAW inmutable, trazabilidad por archivo/hash y separación entre diagnóstico y consolidación de ratios.

## 5. Salidas esperadas

- `reports/sample_inspections/file_hashes.json`
- `reports/sample_inspections/sample_inventory.json`
- `reports/sample_inspections/sample_inventory_report.md`

## 6. Criterios de éxito

- Los archivos quedan inventariados.
- Los hashes quedan calculados.
- Los duplicados exactos quedan detectados preliminarmente.
- Los tipos de archivo quedan clasificados.
- Los Excel quedan inspeccionados de forma no destructiva si es posible.
- Los BC3 quedan detectados superficialmente.
- Los PDF quedan marcados como referencia.
- No se importa nada al master.
