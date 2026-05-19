# Fase 9.3: hardening del generador del Excel maestro vivo

## 1. Objetivo de la fase

Endurecer el generador del Excel maestro vivo con carga sintetica incremental, validaciones referenciales minimas y politica inicial de snapshots/rollback/retencion sin uso de datos reales.

## 2. Contexto desde Fase 9.2

- Fase 9.2 ya implemento plantilla base, esquema minimo y snapshots pre/post.
- Fase 9.3 extiende ese baseline para validar integridad de datos entre hojas y soportar corridas sinteticas incrementales repetibles.

## 3. Alcance

- Carga sintetica incremental en hojas clave (`SOURCE_FILES`, `PROJECTS`, `BUDGET_VERSIONS`, `IMPORT_LOG`, `RAW_IMPORTS`, `COST_ITEMS`, `VALIDATION_RESULTS`, `EXCLUSIONS`, `CHANGELOG`).
- Validaciones referenciales compatibles con contrato 9.1/9.2.
- Bloqueo de promocion a `RATIO_INPUTS` cuando `validation_status` bloquea.
- Snapshot pre/post reforzado en cargas incrementales.
- Retencion inicial simple por numero maximo de snapshots.
- Rollback inicial desde snapshot existente.
- Pruebas sinteticas de hardening.

## 4. Fuera de alcance

- Uso de datos reales.
- Importacion real de BC3/Excel/PDF/Presto-PZH al master.
- Calculo de ratios finales.
- Normalizacion final de categorias.
- Consolidacion de importes reales.
- Cambios sobre RAW.

## 5. Datos sintéticos usados

- IDs sinteticos con prefijos (`sf_`, `prj_`, `bv_`, `imp_`, `raw_`, `ci_`, `vr_`, `ex_`, `ri_`).
- Valores sinteticos no operativos en descripciones, hashes y metadatos.
- `RATIO_INPUTS` solo con placeholders sinteticos y `validation_status=VALIDATED`.
- `RATIOS_CALCULATED` permanece sin calculo operativo.

## 6. Validaciones referenciales implementadas

- `BUDGET_VERSIONS.source_file_id` debe existir en `SOURCE_FILES.source_file_id`.
- `COST_ITEMS.budget_version_id` debe existir en `BUDGET_VERSIONS.budget_version_id`.
- `COST_ITEMS.source_file_id` debe existir en `SOURCE_FILES.source_file_id`.
- `RAW_IMPORTS.source_file_id` debe existir en `SOURCE_FILES.source_file_id`.
- `VALIDATION_RESULTS.import_batch_id` debe existir en `IMPORT_LOG.import_batch_id`.
- `EXCLUSIONS` limitacion de contrato: no tiene `source_file_id`; validacion compatible cuando `entity_type=SOURCE_FILE`, `entity_id` debe existir en `SOURCE_FILES`.
- Bloqueo de promocion en `RATIO_INPUTS` si `validation_status` esta en `BLOCKED/ERROR/VALIDATION_BLOCKED`.
- IDs minimos no vacios y sin duplicados en claves sinteticas principales.
- Campos `validation_status` obligatorios no vacios en hojas que lo exigen.

## 7. Política inicial de snapshots

- Snapshot `pre_update` obligatorio antes de modificar workbook existente.
- Snapshot `post_update` obligatorio tras escritura/validacion correcta.
- Registro en hoja `SNAPSHOTS` con:
  - `snapshot_id`;
  - `source_run_id` (run_id);
  - `trigger_reason` (`pre_update`, `post_update`, `rollback`);
  - `snapshot_ts`;
  - `checksum` simple (`size:<bytes>`);
  - `storage_ref` (ruta segura).

## 8. Política inicial de rollback

- Se implementa rollback inicial via `--rollback-from <snapshot>`.
- Flujo:
  - snapshot pre-rollback del estado actual;
  - restauracion desde snapshot indicado;
  - validacion de esquema + referencial;
  - registro `rollback` en `SNAPSHOTS` y `CHANGELOG`;
  - snapshot post-update del estado restaurado.

## 9. Política inicial de retención de snapshots

- Parametro `--snapshot-retention-max N` (default 5).
- Se conservan los ultimos `N` snapshots en `outputs/live_excel_master/snapshots`.
- Snapshots excedentes se eliminan por antiguedad y se registra evento en `CHANGELOG`.
- Politica simple intencional, sin backup distribuido en esta fase.

## 10. Tests añadidos o modificados

- Nuevo archivo: `tests/scripts/test_live_excel_master_hardening.py`.
- Cobertura:
  - carga sintetica incremental valida;
  - relaciones validas y fallos controlados por referencias rotas;
  - bloqueo de `RATIO_INPUTS` con estados bloqueados;
  - deteccion de IDs vacios y duplicados;
  - snapshots pre/post en carga incremental;
  - repetibilidad;
  - retencion de snapshots;
  - rollback inicial;
  - bloqueo fuera de `outputs/live_excel_master`.

## 11. Riesgos detectados

- Crecimiento de complejidad si se amplian relaciones sin modularizar validadores.
- `checksum` por tamano es basico y no criptografico.
- Rollback depende de integridad del snapshot en filesystem local.

## 12. Limitaciones

- No hay carga real ni validacion semantica de negocio final.
- `EXCLUSIONS` no permite validacion directa por `source_file_id` por limitacion de contrato actual.
- No hay politica avanzada de ciclo de vida de backups/snapshots.

## 13. Decisiones pendientes

- Definir checksum fuerte (ej. SHA-256) para snapshots.
- Definir reglas finales de elegibilidad de `RATIO_INPUTS` ligadas a normalizacion real.
- Definir alcance de rollback automatico transaccional.
- Definir limites de crecimiento de workbook y estrategia de particionado.

## 14. Recomendación para Fase 9.4

- Consolidar validadores en modulo dedicado de integridad.
- Endurecer validaciones cruzadas con `NORMALIZED_COST_ITEMS` y `CATEGORY_MAPPING` sin romper contrato.
- Introducir pruebas de resiliencia (corrupcion parcial, rollback negativo, stress sintetico).
