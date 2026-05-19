# Fase 9.4: refactor controlado de validaciones de integridad y resiliencia

## 1. Objetivo de la fase

Separar las validaciones de integridad del Excel maestro vivo a un modulo dedicado, reforzar resiliencia operativa y mantener compatibilidad funcional con Fase 9.1, 9.2 y 9.3 usando solo datos sinteticos.

## 2. Contexto desde Fase 9.3

- Fase 9.3 dejo operativo el generador con carga sintetica incremental, validaciones referenciales basicas, snapshots, rollback inicial y retencion simple.
- La logica de integridad estaba acoplada al CLI principal, reduciendo mantenibilidad y testabilidad aislada.

## 3. Problema tecnico detectado

- Validaciones de esquema, estados, referencias y rutas estaban en un unico script CLI.
- El acoplamiento dificultaba pruebas unitarias de integridad sin recorrer siempre flujos de ejecucion completos.
- Faltaban bloqueos explicitos para `MANUAL_REVIEW_REQUIRED`, estados desconocidos y rollback desde rutas externas.

## 4. Alcance del refactor

- Extraer validaciones a `scripts/live_excel_integrity.py`.
- Mantener `scripts/generate_live_excel_master.py` como punto de entrada CLI.
- Endurecer reglas de estados, relaciones y rutas permitidas.
- Añadir tests sinteticos de resiliencia enfocados en fallos controlados.

## 5. Fuera de alcance

- Rediseño amplio del generador.
- Uso de datos reales.
- Importacion real al master.
- Calculo de ratios finales.
- Normalizacion final de categorias.
- Consolidacion final de importes.
- Interfaz, dashboard o flujo UX.

## 6. Modulos creados o modificados

- Creado: `scripts/live_excel_integrity.py`.
- Modificado: `scripts/generate_live_excel_master.py`.
- Modificados/creados tests:
  - `tests/scripts/test_generate_live_excel_master.py` (compatibilidad mantenida, sin cambios de contrato).
  - `tests/scripts/test_live_excel_master_hardening.py` (compatibilidad mantenida).
  - `tests/scripts/test_live_excel_integrity.py` (nuevo).

## 7. Validaciones extraidas

- Existencia de hojas obligatorias.
- Existencia de columnas minimas.
- IDs minimos no vacios.
- Duplicados en claves sinteticas obligatorias.
- Relaciones:
  - `BUDGET_VERSIONS.source_file_id -> SOURCE_FILES.source_file_id`.
  - `COST_ITEMS.budget_version_id -> BUDGET_VERSIONS.budget_version_id`.
  - `COST_ITEMS.source_file_id -> SOURCE_FILES.source_file_id`.
  - `RAW_IMPORTS.source_file_id -> SOURCE_FILES.source_file_id`.
  - `VALIDATION_RESULTS.import_batch_id -> IMPORT_LOG.import_batch_id`.
  - `EXCLUSIONS` compatible con contrato actual (`SOURCE_FILE` via `entity_id`).
- Bloqueo en `RATIO_INPUTS` para estados no elegibles.
- Validacion de rutas permitidas para output y snapshots.

## 8. Validaciones nuevas añadidas

- Bloqueo de promocion a `RATIO_INPUTS` con `MANUAL_REVIEW_REQUIRED`.
- Rechazo de `validation_status` desconocidos/no reconocidos.
- Validacion de `NORMALIZED_COST_ITEMS.cost_item_id -> COST_ITEMS.cost_item_id`.
- Bloqueo de `NORMALIZED_COST_ITEMS` cuando referencia `COST_ITEMS` con estado bloqueado/error/manual review.
- Rechazo de rollback desde snapshot fuera de `outputs/live_excel_master/snapshots/`.

## 9. Tests de resiliencia añadidos

- `test_misspelled_required_column_fails`.
- `test_column_order_change_is_allowed_when_headers_exist`.
- `test_unknown_validation_status_fails`.
- `test_manual_review_required_cannot_promote_to_ratio_inputs`.
- `test_normalized_cost_item_requires_existing_cost_item`.
- `test_rollback_from_snapshot_outside_allowed_path_fails`.

## 10. Riesgos

- Las reglas de estados validos podrian requerir ampliacion controlada en fases futuras.
- Mantener checksum por tamano (`size:<bytes>`) sigue siendo una señal debil para integridad criptografica.
- La retencion simple por archivo local no cubre escenarios avanzados de backup distribuido.

## 11. Limitaciones

- `CATEGORY_MAPPING` no fuerza categoria final definitiva porque el contrato aun la mantiene pendiente.
- No se introduce rollback transaccional multi-fichero.
- No se añade logica de datos reales ni validacion semantica final de negocio.

## 12. Compatibilidad con Fase 9.1, 9.2 y 9.3

- Se mantiene el contrato de hojas/columnas definido en Fase 9.1.
- Se mantiene el CLI principal y flujo base de Fase 9.2.
- Se mantienen snapshots/rollback/retencion y carga sintetica incremental de Fase 9.3.
- El refactor es interno y no cambia la superficie funcional comprometida.

## 13. Decisiones que siguen pendientes

- Definir checksum fuerte (ej. SHA-256) para snapshots.
- Definir elegibilidad final de ratios en fase con datos reales validados.
- Definir politica avanzada de retencion por workbook y ventana temporal.
- Definir reglas finales de normalizacion y categoria definitiva.

## 14. Recomendacion para Fase 9.5

- Ampliar cargas sinteticas multi-lote con controles de idempotencia por `run_id`.
- Fortalecer rollback seguro ante corrupcion parcial (ensayos negativos adicionales).
- Preparar contrato de entrada pre-real sin habilitar datos reales ni romper restricciones activas.
