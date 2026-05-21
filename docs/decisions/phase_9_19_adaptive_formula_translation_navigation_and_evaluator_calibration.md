# Fase 9.19 - Formulas adaptativas, navegacion profesional y evaluador semantico

## Objetivo de la fase

Cerrar tres huecos de calidad detectados tras 9.18:

1. Traducir formulas de forma segura en vistas profesionales adaptativas.
2. Mejorar navegacion INDEX/HOME para orientar revision humana.
3. Recalibrar el evaluador dry-run por tipo semantico de hoja XLSX.

## Contexto desde Fase 9.18

- 9.18 separo vistas por tipo semantico y evito mezcla de hojas incompatibles.
- Persistia riesgo de formulas heredadas no coherentes con la vista nueva.
- Persistia riesgo de formulas con nombres definidos no presentes en el workbook generado.
- El evaluador seguia aplicando bloqueos de presupuesto clasico a filas no clasicas.

## Problemas detectados tras revision humana

- En `REAL_XLSX_GENERALIZATION_002` la columna `Diferencia` podia conservar formula heredada (`=+H4-F4`) no coherente con la vista comparativa.
- En `REAL_XLSX_GENERALIZATION_001` la columna `Formula / Ratio` podia mantener formulas activas con nombres definidos no preservados (`PEM`, `PorGasGen`, etc.).
- INDEX/HOME necesitaban orientacion mas directa hacia vistas profesionales por tipo.
- El evaluador bloqueaba por `amount_mixed_in_description` y `description_amount_split_failed` en filas no clasicas.

## Reglas de formulas adaptativas

### Politica general

- No copiar formulas a ciegas.
- Toda formula visible debe ser valida en la hoja donde aparece.
- Si la traduccion no es segura: preservar valor, o preservar formula como texto controlado, y registrar trazabilidad.

### Politica formulas copiadas vs traducidas

- `COMPARISON_TABLE`: no se reutiliza formula heredada.
  - Se traduce a formula de vista: `Diferencia = Importe equivalente - Importe (€)`.
  - En layout actual: `=E{row}-C{row}`.
- `BUDGET_SUMMARY` / `FORMULA_CALCULATION_SHEET`:
  - Si formula referencia nombres definidos no disponibles o contexto no preservable: se guarda como texto controlado (`formula_preserved_as_text: ...`).
  - No se deja formula activa rota.

### Politica de nombres definidos

- Se inspeccionan nombres definidos del workbook final.
- Si una formula activa referencia nombres no existentes, se bloquea como formula insegura en validacion post-generacion.
- Si no se puede preservar de forma fiable, la formula pasa a texto/trace y se conserva el importe como valor.

### Politica para formulas no traducibles

- Estados de traduccion soportados:
  - `TRANSLATED_FORMULA`
  - `PRESERVED_FORMULA`
  - `PRESERVED_AS_TEXT`
  - `VALUE_ONLY`
  - `MOVED_TO_TRACE`
  - `UNSUPPORTED_FORMULA`
- Se registra estado en `BUDGET_REVIEW_TRACE_*`.

## Reglas de navegacion INDEX/HOME

- INDEX se refuerza como tabla de navegacion de vistas adaptativas:
  - `Vista principal`, `Tipo semantico`, `Hoja origen`, `Estado`, `Descripcion`, `Abrir`.
- HOME (`BUDGET_REVIEW_001`) incluye:
  - `Hoja origen`, `Tipo semantico`, `Confianza`, `Vista profesional`, `Estado`, `Advertencias`, `Accion recomendada`.
- Se mantiene sin formulas `=HYPERLINK(...)`; se usan valores limpios y hyperlink de celda.

## Reglas de evaluacion por tipo semantico

- El evaluador extrae `sheet_type` desde HOME y desde notas por fila.
- `amount_mixed_in_description` y `description_amount_split_failed` solo bloquean filas `BUDGET_CLASSIC` o sin tipo.
- Mapeo ambiguo de `PRESERVED_TO_COST_ITEMS_MAP` solo penaliza como manual-reason si existe `BUDGET_CLASSIC`.
- `UNKNOWN` fuerza `MANUAL_REVIEW_REQUIRED`.

## Cambios tecnicos realizados

- Nuevo modulo `scripts/xlsx_formula_translation.py`.
- `scripts/live_excel_professional_output.py`:
  - traduccion/formateo de formulas por tipo,
  - traduccion explicita de `Diferencia` en comparativas (`=Erow-Crow`),
  - trazabilidad de estado de traduccion,
  - columna `Accion recomendada` en HOME.
- `scripts/live_excel_workbook_formatting.py`:
  - INDEX con navegacion semantica de vistas.
- `scripts/live_excel_dry_run_evaluator.py`:
  - calibracion de bloqueos/manual-reasons por `sheet_type`.
- `scripts/generate_live_excel_master.py`:
  - `PREVIEW_PIPELINE_PHASE=9.19`,
  - validaciones nuevas:
    - columnas de navegacion en INDEX/HOME,
    - formulas inseguras por nombres definidos inexistentes en vistas profesionales,
    - mismatch de formula de diferencia en comparativas.

## Tests añadidos o modificados

- Nuevos:
  - `tests/scripts/test_xlsx_formula_translation.py`
  - `tests/scripts/test_xlsx_semantic_evaluator_calibration.py`
  - `tests/scripts/test_xlsx_review_navigation.py`
- Modificados:
  - `tests/scripts/test_xlsx_output_pipeline_audit.py`
  - `tests/scripts/test_live_excel_professional_output.py`

## Resultado de regeneracion local 001/002

- Se regenera en `outputs/live_excel_master/xlsx_generalization/`.
- Verificacion obligatoria post-regeneracion:
  - 001: HOME/INDEX navegables, formulas seguras en `BUDGET_REVIEW_001_Datos`.
  - 002: `BUDGET_REVIEW_001_Hoja1` con diferencia coherente en coordenadas de su vista.

## Limitaciones

- Traduccion de formulas complejas con rangos multi-hoja y nombres definidos avanzados sigue siendo conservadora.
- Si el contexto formula no es fiable, se prioriza seguridad (texto/valor) frente a formula activa.

## Riesgos

- Algunos workbooks reales pueden depender de nombres definidos externos no portables.
- Cambios futuros de layout en vistas comparativas requieren mantener la regla de traduccion de `Diferencia`.

## Recomendacion para Fase 9.20

- Endurecer traduccion de formulas avanzadas (nombres definidos/rangos cruzados) con matriz de compatibilidad por tipo semantico.
- Ampliar no-regresion real en muestra XLSX antes de reabrir BC3 preservado.
