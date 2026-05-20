# Fase 9.10: piloto dry-run real con varios presupuestos aislados

## 1. Objetivo de la fase

Ejecutar una prueba real controlada en local sobre varios presupuestos aislados para validar preview preservada, trazabilidad, mapeo hacia `COST_ITEMS` y clasificacion dry-run por archivo, sin promocion automatica ni actualizacion del master operativo.

## 2. Contexto desde Fase 9.9

- Fase 9.9 dejo operativo el evaluador combinado (`OPERATIVE_CANDIDATE`, `PROMOTION_BLOCKED`, `MANUAL_REVIEW_REQUIRED`, `PRESERVATION_INCOMPLETE`).
- Se mantenian umbrales preliminares:
  - `traceability_rate >= 0.95`
  - `amount_separation_rate >= 0.85` (cuando aplica)
  - `manual_review_rate <= 0.25`
  - `blocked_rate = 0`
  - `critical_errors = 0`
- No existia todavia evidencia con lote multi-archivo real aislado.

## 3. Alcance de la prueba real controlada

- Ejecucion local en seco (`dry-run`) sobre muestra pequena y representativa.
- IDs sanitizados obligatorios por archivo.
- Generacion de previews solo en rutas ignoradas por Git.
- Evaluacion combinada por archivo y reporte sanitizado.

## 4. Fuera de alcance

- Promocion automatica a operativo.
- Actualizacion del master operativo.
- Calculo final de ratios.
- Normalizacion final de categorias.
- Consolidacion definitiva de importes.
- Modificacion de RAW.
- Interfaz, dashboard o flujo UX.
- Subida de archivos reales, Excels generados o reportes sensibles.

## 5. Seleccion de archivos reales (solo IDs sanitizados)

- `REAL_DRY_RUN_001` -> formato `XLSX`.
- `REAL_DRY_RUN_002` -> formato `BC3` (caso esperado no soportado en preview XLSX directa de esta fase).
- `REAL_DRY_RUN_003` -> formato `XLSX` con estructura distinta.

## 6. Flujo ejecutado por archivo

1. Verificacion de ruta permitida en `data/samples`.
2. Generacion de preview preservada local (solo en `XLSX`).
3. Creacion de hojas visibles preservadas `PRES_*`.
4. Creacion de `PRESERVED_TO_COST_ITEMS_MAP`.
5. Evaluacion dry-run combinada.
6. Registro de estado, motivos y metricas.

## 7. Resultados por archivo

### REAL_DRY_RUN_001

- Estado final: `OPERATIVE_CANDIDATE`.
- Motivos: ninguno bloqueante.
- Preview local: `outputs/live_excel_master/real_dry_run/real_dry_run_001_preview.xlsx`.
- Metricas:
  - `mapping_rate`: `0.7938144329896907`
  - `traceability_rate`: `1.0`
  - `manual_review_rate`: `0.0`
  - `blocked_rate`: `0.0`
  - `amount_separation_rate`: `1.0` (sin amount aplicable detectado en filas evaluadas)
  - `ratio_input_rows`: `0.0`
  - `ratio_calculated_rows`: `0.0`
- Evaluacion visual resumida:
  - Hojas preservadas visibles presentes.
  - Presupuesto reconocible por estructura y orden de filas.
  - Trazabilidad hoja/fila presente.
  - Deteccion automatica de cabeceras economicas limitada en varias filas (`NO_HEADER_DETECTION`).

### REAL_DRY_RUN_002

- Estado final: `PROMOTION_BLOCKED`.
- Motivo explicito: `format_not_supported_for_preview_phase_9_10`.
- Preview local: no aplica (sin preview XLSX en esta fase para BC3).
- Metricas:
  - `mapping_rate`: `0.0`
  - `traceability_rate`: `0.0`
  - `manual_review_rate`: `0.0`
  - `blocked_rate`: `1.0`
  - `amount_separation_rate`: `0.0`
  - `ratio_input_rows`: `0.0`
  - `ratio_calculated_rows`: `0.0`
- Evaluacion visual resumida:
  - No aplica por no existir salida preview en esta fase para ese formato.

### REAL_DRY_RUN_003

- Estado final: `PROMOTION_BLOCKED`.
- Motivos explicitos:
  - `amount_mixed_in_description`
  - `insufficient_amount_separation`
- Preview local: `outputs/live_excel_master/real_dry_run/real_dry_run_003_preview.xlsx`.
- Metricas:
  - `mapping_rate`: `0.8048780487804879`
  - `traceability_rate`: `1.0`
  - `manual_review_rate`: `0.0`
  - `blocked_rate`: `0.0`
  - `amount_separation_rate`: `0.0`
  - `ratio_input_rows`: `0.0`
  - `ratio_calculated_rows`: `0.0`
- Evaluacion visual resumida:
  - Preservacion de hojas y trazabilidad correcta.
  - Reconocimiento economico insuficiente para separacion robusta importe/descripcion.
  - Utilidad operativa parcial; requiere mejora de deteccion/mapeo.

## 8. Limitaciones detectadas

- El flujo de preview actual cubre `XLSX` de forma directa; `BC3` queda bloqueado en este piloto.
- La deteccion de cabeceras en estructuras heterogeneas sigue siendo fragil.
- `mapping_rate` aceptable, pero con volumen relevante de filas `UNMAPPED`.
- En ciertos XLSX reales, la separacion de importes es insuficiente para candidatura robusta.

## 9. Ajustes recomendados

- Endurecer deteccion de cabeceras y columnas economicas multi-layout.
- Introducir heuristicas de separacion descripcion/importe menos sensibles a ruido.
- Mejorar estrategia de mapping para reducir `UNMAPPED`.
- Definir ruta de preview preservada especifica para BC3 dentro del contrato 9.x.

## 10. Adecuacion de umbrales preliminares

- `traceability_rate` y `blocked_rate` se comportaron de forma consistente.
- `amount_separation_rate` mostro capacidad discriminante real en al menos un caso bloqueado.
- Con esta muestra pequena, los umbrales se mantienen preliminares y no se recomiendan cambios definitivos aun.

## 11. Confirmaciones de seguridad y alcance

- No hubo promocion automatica.
- No se actualizo el master operativo.
- No se alimentaron `RATIO_INPUTS` ni `RATIOS_CALCULATED`.
- No se modifico RAW.
- No se subieron archivos reales, Excels generados ni reportes sensibles.
- Todos los outputs del piloto quedaron en ruta local ignorada por Git:
  - `outputs/live_excel_master/real_dry_run/`

## 12. Implementacion de soporte 9.10

- Nuevo wrapper seguro:
  - `scripts/run_real_dry_run_pilot.py`
- Cobertura sintetica:
  - `tests/scripts/test_real_dry_run_pilot_support.py`

## 13. Recomendacion para Fase 9.11

Abrir Fase 9.11 para endurecimiento post-piloto con foco en:

1. mejoras de parsing/mapeo para layouts reales heterogeneos;
2. ruta BC3 preservada bajo contrato 9.x;
3. recalibracion de umbrales con muestra real ampliada;
4. mantenimiento estricto de `PREVIEW_ONLY` sin promocion automatica.
