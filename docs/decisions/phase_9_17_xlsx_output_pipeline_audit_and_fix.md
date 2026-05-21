# Fase 9.17 - auditoria de outputs reales XLSX y correccion integral de pipeline

## Objetivo de la fase

Garantizar que toda salida oficial `xlsx_generalization_*_preview.xlsx` pase por un pipeline unico y verificable que aplique, sin excepciones:

1. extraccion semantica corregida;
2. `BUDGET_REVIEW_001`;
3. `BUDGET_REVIEW_TRACE_001`;
4. `INDEX` limpio;
5. formateo global del workbook;
6. validacion programatica post-generacion con fallo explicito.

## Contexto desde Fase 9.16

- Fase 9.16 cerro tecnicamente con fixes de semantica e `INDEX`.
- El usuario reporto discrepancia critica: lo observado manualmente en outputs no coincidia con el reporte tecnico.
- Esta fase se enfoca en auditoria y enforcement de pipeline, no en nuevas funcionalidades.

## Discrepancia reportada por el usuario

Revision humana reportada:

- `xlsx_generalization_001_preview.xlsx`: `Descripcion/Importe` inconsistentes, formulas auxiliares visibles y `INDEX` con `=HYPERLINK(...)`.
- `xlsx_generalization_002_preview.xlsx`: apariencia de workbook antiguo (`README_MASTER phase=9.9`, sin hojas profesionales segun revision manual inicial).

## Archivos exactos auditados

- `outputs/live_excel_master/xlsx_generalization/xlsx_generalization_001_preview.xlsx`
- `outputs/live_excel_master/xlsx_generalization/xlsx_generalization_002_preview.xlsx`

## Diagnostico de pipeline

### Hallazgos de auditoria previa programatica (estado local al inicio de 9.17)

- Ambos archivos existen y ya incluyen `INDEX`, `BUDGET_REVIEW_001` y `BUDGET_REVIEW_TRACE_001`.
- Ambos abren en `INDEX`.
- En ambos, `INDEX` no contiene formula visible `=HYPERLINK(...)` ni texto `HYPERLINK is not implemented`.
- En `001`, el caso critico aparece correcto (`LUV_AP | EQUIPAMIENTO | 37297.09`).
- En ambos, `_review_row_id` esta oculto y `PRES_*.__source_*` ocultas.
- En ambos, no se detectaron formulas auxiliares en `COST_ITEMS` como partidas.
- Inconsistencia real detectada: `README_MASTER.phase` seguia en `9.9` (metadato heredado de plantilla base).

### Diagnostico de por que 001 podia seguir viendose mal

- Riesgo identificado: outputs antiguos coexistiendo con nuevos y falta de validacion post-generacion obligatoria.
- Sin un validador final hard-stop, era posible considerar correcto un output no inspeccionado en disco.
- La correccion semantica estaba implementada, pero faltaba enforcement programatico de contrato final por archivo generado.

### Diagnostico de por que 002 podia parecer antiguo/no actualizado

- El pipeline previo no forzaba una comprobacion estricta de metadatos/version final.
- `README_MASTER.phase=9.9` podia reforzar percepcion de workbook viejo aun cuando la estructura visual ya fuese nueva.
- Faltaba un criterio programatico de rechazo para metadata de fase incoherente.

## Rutas de generacion existentes

1. `scripts/run_xlsx_generalization_dry_run.py`
   - genera `xlsx_generalization_###_preview.xlsx` via `generate_preview_from_real_xlsx(...)`.
2. `scripts/generate_live_excel_master.py::generate_preview_from_real_xlsx`
   - preserva hojas, crea capas tecnicas, construye `BUDGET_REVIEW_*`, aplica formato global y guarda workbook.

No se detectaron rutas paralelas adicionales creando `xlsx_generalization_*_preview.xlsx` fuera del wrapper oficial.

## Ruta oficial decidida (unica)

Ruta oficial consolidada para previews XLSX:

1. leer XLSX;
2. detectar estructura economica;
3. preservar hojas;
4. construir `COST_ITEMS` filtrando auxiliares;
5. construir `BUDGET_REVIEW_001`;
6. construir `BUDGET_REVIEW_TRACE_001`;
7. construir `INDEX` limpio;
8. aplicar formato global;
9. fijar hoja activa `INDEX`;
10. validar workbook generado (post-generacion, obligatoria);
11. guardar/aceptar output.

## Cambios aplicados

### `scripts/generate_live_excel_master.py`

- Se define `PREVIEW_PIPELINE_PHASE = "9.17"`.
- Se agrega `_upsert_readme_field(...)` para actualizar metadata sin duplicados.
- Se actualiza `README_MASTER.phase` durante preview a `9.17`.
- Se implementa `validate_generated_xlsx_preview(...)` con checks hard-stop:
  - existencia de `INDEX`, `BUDGET_REVIEW_*`, `BUDGET_REVIEW_TRACE_*`;
  - hoja activa en `INDEX`;
  - `README_MASTER.phase` coherente;
  - `INDEX` sin formulas visibles `=HYPERLINK(...)` ni texto tecnico;
  - `BUDGET_REVIEW_*` sin `#NAME?`, sin descripciones numericas puras y sin formulas auxiliares en descripcion;
  - `_review_row_id` oculto;
  - `PRES_*.__source_*` ocultas;
  - `COST_ITEMS` sin formulas auxiliares como partidas ni filas vacias+importe cero.
- `generate_preview_from_real_xlsx(...)` ejecuta esta validacion y falla explicitamente si no cumple.

### `scripts/run_xlsx_generalization_dry_run.py`

- Migra a fase `9.17` (metadata y mensajes).
- Revalida cada preview generado con `validate_generated_xlsx_preview(...)`.
- Si falla la validacion, el proceso falla y no reporta output como correcto.

## Verificaciones post-generacion

Se verifico localmente sobre los dos outputs oficiales:

- `xlsx_generalization_001_preview.xlsx`: cumple checks; caso critico correcto.
- `xlsx_generalization_002_preview.xlsx`: cumple estructura/profesionalizacion y ahora con `README_MASTER.phase=9.17`.

## Tests anadidos o modificados

- Nuevo: `tests/scripts/test_xlsx_output_pipeline_audit.py`
  - valida pipeline oficial, fase coherente, `INDEX` limpio, semantica de `BUDGET_REVIEW` y rechazo de formulas auxiliares.
  - valida fallo esperado del validador si hay `=HYPERLINK(...)`, falta hoja review o hay `#NAME?`/formulas auxiliares.
- Modificado: `tests/scripts/test_xlsx_generalization_support.py`
  - ahora valida fase `PREVIEW_PIPELINE_PHASE`.
  - valida limpieza de `INDEX` y coherencia de `README_MASTER.phase`.

## Limitaciones

- La validacion semantica post-generacion es estructural; no sustituye revision humana integral de todo layout.
- Muestra real disponible sigue siendo limitada y puede no cubrir todos los patrones extremos.

## Riesgos

- Criterios demasiado estrictos podrian bloquear layouts no estandar pero validos; se monitoriza en Fase 9.18.
- El metadato de fase se usa como guardrail; cambios futuros deben mantenerlo sincronizado para evitar falsos bloqueos.

## Recomendacion para Fase 9.18

- Ejecutar nueva ronda de generalizacion real ampliada (solo XLSX) con validacion post-generacion activa.
- Catalogar falsos positivos/falsos negativos del validador y ajustar reglas con evidencia.
- Mantener BC3 fuera de alcance hasta cerrar no-regresion XLSX en muestra ampliada.
