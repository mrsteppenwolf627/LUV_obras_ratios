# Fase 9.1: diseno tecnico del generador del Excel maestro vivo

## 1. Objetivo de la fase

Definir el contrato tecnico del generador del Excel maestro vivo como salida operativa principal del sistema, estableciendo estructura minima de hojas, reglas de actualizacion, trazabilidad, versionado/snapshots, validaciones previas y restricciones de uso antes de cualquier implementacion.

## 2. Contexto desde Fase 9.0

- Fase 8 quedo cerrada tecnicamente con estrategia Presto/PZH basada en ruta evidenciada, no parser nativo forzado.
- Fase 9.0 fijo la decision metodologica: el producto operativo final es un Excel maestro vivo (ADR-019).
- Quedaron pendientes de 9.0: contrato tecnico del generador, reglas concretas de actualizacion/snapshots y criterios de bloqueo de escritura.

## 3. Que significa Excel maestro vivo a nivel tecnico

- Es un artefacto Excel unico de salida operativa por iteracion.
- Es regenerable/sobrescribible de forma controlada y auditable.
- Su contenido no sustituye RAW ni logs fuente; consume capas intermedias y validadas.
- Debe conservar trazabilidad fila a fuente, version y estado de validacion.
- Debe separar explicitamente datos usados, excluidos y pendientes.

## 4. Alcance de Fase 9.1

- Definir diseno tecnico de hojas minimas obligatorias y opcionales.
- Definir contrato minimo por hoja (objetivo, columnas, fuente, historico, sobrescritura).
- Definir reglas de actualizacion, snapshot y bloqueo.
- Definir trazabilidad minima obligatoria transversal.
- Definir validaciones previas de escritura y reglas de exclusion.
- Definir que puede/no puede entrar al maestro en fases siguientes.

## 5. Fuera de alcance de Fase 9.1

- Implementacion del generador.
- Creacion de Excel maestro real con datos reales.
- Importacion real al master.
- Calculo de ratios finales.
- Normalizacion final de categorias.
- Consolidacion final de importes.
- Nuevo tratamiento tecnico de Presto/PZH fuera de Fase 8.
- Cualquier modificacion de RAW.

## 6. Estructura minima propuesta del Excel

Se propone estructura por dominios:

- Gobernanza y auditoria: `README_MASTER`, `IMPORT_LOG`, `CHANGELOG`, `SNAPSHOTS`.
- Catastro de fuentes y versiones: `SOURCE_FILES`, `PROJECTS`, `BUDGET_VERSIONS`, `RAW_IMPORTS`.
- Datos de coste y normalizacion: `COST_ITEMS`, `NORMALIZED_COST_ITEMS`, `CATEGORY_MAPPING`.
- Calidad y elegibilidad: `VALIDATION_RESULTS`, `EXCLUSIONS`.
- Preparacion y resultados de ratios: `RATIO_INPUTS`, `RATIOS_CALCULATED`.

## 7. Hojas obligatorias iniciales

Evaluacion para primer diseno:

- `README_MASTER`: SI.
- `IMPORT_LOG`: SI.
- `SOURCE_FILES`: SI.
- `PROJECTS`: SI.
- `BUDGET_VERSIONS`: SI.
- `RAW_IMPORTS`: SI.
- `COST_ITEMS`: SI.
- `NORMALIZED_COST_ITEMS`: SI.
- `CATEGORY_MAPPING`: SI, pero con columnas parcialmente pendientes por decision humana.
- `VALIDATION_RESULTS`: SI.
- `RATIO_INPUTS`: SI.
- `RATIOS_CALCULATED`: SI (puede iniciar vacia hasta fase habilitada).
- `EXCLUSIONS`: SI.
- `SNAPSHOTS`: SI.
- `CHANGELOG`: SI.

## 8. Hojas opcionales futuras

- `MANUAL_REVIEW`.
- `TRACEABILITY_VIEW` (vista de trazabilidad extendida).
- `FORMAT_STATUS`.
- `QUALITY_METRICS`.
- `SUPPLIER_EXPORTS`.

## 9. Contrato de cada hoja

### 9.1 README_MASTER
- Objetivo: describir alcance, restricciones, version del contrato y convenciones del maestro vivo.
- Columnas minimas: `field`, `value`, `updated_at`, `updated_by`.
- Fuente de datos: configuracion de pipeline/documentacion interna.
- Tipo: auditoria/gobernanza.
- Sobrescritura: SI.
- Historico: SI (via `CHANGELOG` y `SNAPSHOTS`).

### 9.2 IMPORT_LOG
- Objetivo: registrar ejecuciones de pipeline y resultado de actualizacion del maestro.
- Columnas minimas: `import_batch_id`, `run_id`, `started_at`, `finished_at`, `status`, `records_written`, `records_skipped`, `error_code`, `error_message`.
- Fuente de datos: ejecucion del pipeline.
- Tipo: auditoria.
- Sobrescritura: NO (append-only).
- Historico: SI.

### 9.3 SOURCE_FILES
- Objetivo: catalogo de archivos origen.
- Columnas minimas: `source_file_id`, `original_filename`, `file_hash`, `file_type_detected`, `source_priority`, `ingested_at`, `import_batch_id`, `sensitivity_flag`.
- Fuente de datos: inventario de ingesta.
- Tipo: intermedia/catalogo.
- Sobrescritura: SI parcial (anotaciones no identitarias).
- Historico: SI.

### 9.4 PROJECTS
- Objetivo: identidad de proyecto y metadatos base para trazabilidad.
- Columnas minimas: `project_id`, `project_code`, `project_name`, `surface_base_value`, `surface_base_unit`, `surface_base_status`, `created_at`, `updated_at`.
- Fuente de datos: capa intermedia consolidada.
- Tipo: intermedia.
- Sobrescritura: SI controlada.
- Historico: SI (snapshot por cambios estructurales).

### 9.5 BUDGET_VERSIONS
- Objetivo: versionado de presupuestos por proyecto.
- Columnas minimas: `budget_version_id`, `project_id`, `source_file_id`, `version_name`, `version_date`, `is_latest_version`, `validation_status`, `import_batch_id`.
- Fuente de datos: capa intermedia de versionado.
- Tipo: intermedia.
- Sobrescritura: SI controlada.
- Historico: SI.

### 9.6 RAW_IMPORTS
- Objetivo: indice de referencia a RAW sin duplicar contenido bruto.
- Columnas minimas: `raw_import_id`, `source_file_id`, `raw_path_ref`, `raw_hash`, `ingested_at`, `import_batch_id`, `raw_access_policy`.
- Fuente de datos: catalogo RAW.
- Tipo: RAW-index (no RAW payload).
- Sobrescritura: NO (append-only).
- Historico: SI.

### 9.7 COST_ITEMS
- Objetivo: partidas/capitulos trazables en forma original utilizable.
- Columnas minimas: `cost_item_id`, `budget_version_id`, `source_file_id`, `origin_record_ref`, `description_raw`, `unit_raw`, `quantity_raw`, `unit_price_raw`, `amount_raw`, `row_hash`, `validation_status`.
- Fuente de datos: parseo/lectura por formato.
- Tipo: intermedia.
- Sobrescritura: NO destructiva (nuevas versiones, no reemplazo silencioso).
- Historico: SI.

### 9.8 NORMALIZED_COST_ITEMS
- Objetivo: capa normalizada intermedia para comparabilidad.
- Columnas minimas: `normalized_cost_item_id`, `cost_item_id`, `normalized_description`, `normalized_unit`, `normalized_quantity`, `normalized_amount`, `normalization_status`, `normalization_rule_ref`, `row_hash`, `validation_status`.
- Fuente de datos: normalizadores intermedios por formato.
- Tipo: intermedia/normalizacion.
- Sobrescritura: SI por version de normalizacion.
- Historico: SI.

### 9.9 CATEGORY_MAPPING
- Objetivo: mapear items normalizados a categorias de negocio.
- Columnas minimas: `mapping_id`, `mapping_key`, `target_category`, `mapping_confidence`, `mapping_status`, `decision_source`, `approved_by`, `approved_at`.
- Fuente de datos: reglas y revision humana.
- Tipo: intermedia de negocio.
- Sobrescritura: SI controlada.
- Historico: SI.
- Pendientes: semantica final de categorias y politica de aprobacion humana.

### 9.10 VALIDATION_RESULTS
- Objetivo: resultados de validacion por entidad/fila/regla.
- Columnas minimas: `validation_result_id`, `entity_type`, `entity_id`, `rule_id`, `severity`, `status`, `message`, `validated_at`, `import_batch_id`.
- Fuente de datos: validadores existentes y futuros.
- Tipo: validacion.
- Sobrescritura: NO (append-only con resoluciones trazadas).
- Historico: SI.

### 9.11 RATIO_INPUTS
- Objetivo: dataset elegible para calculo de ratios cuando fase lo habilite.
- Columnas minimas: `ratio_input_id`, `normalized_cost_item_id`, `project_id`, `budget_version_id`, `eligibility_status`, `exclusion_flag`, `validation_status`, `effective_at`.
- Fuente de datos: normalizados + validacion + exclusiones.
- Tipo: ratios (entrada).
- Sobrescritura: SI regenerable por iteracion.
- Historico: SI (snapshot por corrida).

### 9.12 RATIOS_CALCULATED
- Objetivo: salida de ratios por version de calculo.
- Columnas minimas: `ratio_calc_id`, `ratio_code`, `project_scope`, `input_version_ref`, `calculated_value`, `calculation_status`, `calculated_at`.
- Fuente de datos: motor de calculo (fase futura).
- Tipo: ratios (salida).
- Sobrescritura: SI por version de calculo.
- Historico: SI.
- Nota: puede permanecer vacia hasta habilitacion metodologica.

### 9.13 EXCLUSIONS
- Objetivo: registrar exclusiones sin borrar datos.
- Columnas minimas: `exclusion_id`, `entity_type`, `entity_id`, `reason_code`, `reason_detail`, `is_reversible`, `excluded_at`, `excluded_by`, `import_batch_id`.
- Fuente de datos: validacion y revision humana.
- Tipo: validacion/auditoria.
- Sobrescritura: SI (reversion trazada, no borrado).
- Historico: SI.

### 9.14 SNAPSHOTS
- Objetivo: versionar estados del maestro por iteracion.
- Columnas minimas: `snapshot_id`, `snapshot_ts`, `master_version`, `trigger_reason`, `source_run_id`, `storage_ref`, `checksum`, `created_by`.
- Fuente de datos: pipeline de publicacion del maestro.
- Tipo: auditoria/versionado.
- Sobrescritura: NO (append-only).
- Historico: SI.

### 9.15 CHANGELOG
- Objetivo: bitacora legible de cambios funcionales de estructura/contrato.
- Columnas minimas: `change_id`, `change_ts`, `change_type`, `affected_sheet`, `change_summary`, `decision_ref`, `applied_by`.
- Fuente de datos: proceso de actualizacion del maestro y decisiones documentadas.
- Tipo: auditoria/gobernanza.
- Sobrescritura: NO (append-only).
- Historico: SI.

## 10. Regla de actualizacion del Excel

- Sobrescribir maestro: cuando exista corrida valida completa de pipeline sobre contrato vigente y sin bloqueos criticos.
- Anadir hoja: solo si agrega capacidad operativa no redundante y queda documentada en decision de fase/ADR si aplica.
- Crear snapshot: antes de toda sobrescritura y despues de toda sobrescritura exitosa.
- Bloquear actualizacion: cuando falle validacion critica, falte trazabilidad minima obligatoria o se detecte mezcla de datos no elegibles.

## 11. Reglas de versionado/snapshots

- Version semantica del maestro: `major.minor.patch`.
- `major`: cambio incompatible de contrato de hoja/columnas.
- `minor`: nueva hoja o columnas compatibles.
- `patch`: correcciones sin cambio de contrato.
- Snapshot obligatorio:
  - pre-update (estado anterior),
  - post-update (estado publicado),
  - rollback snapshot si se revierte publicacion.
- Cada snapshot debe tener `checksum` y referencia de ejecucion (`run_id` o equivalente).

## 12. Trazabilidad minima obligatoria

A nivel fila o entidad del maestro vivo debe existir referencia verificable a:

- `source_file_id`.
- `budget_version_id`.
- `import_batch_id`.
- `row_hash` o identificador deterministico equivalente.
- `created_at` y `updated_at` (o `event_ts` en tablas append-only).
- `validation_status`.

Si una hoja no puede portar todos los campos directamente, debe portar claves que permitan resolverlos por join trazable.

## 13. Reglas de validacion antes de escribir en Excel

Validaciones de puerta minima:

- Contrato de hojas: nombres y columnas minimas requeridas.
- Integridad de claves: ids obligatorios no nulos y unicidad donde aplique.
- Integridad referencial minima entre `SOURCE_FILES`, `BUDGET_VERSIONS`, `COST_ITEMS`, `NORMALIZED_COST_ITEMS`.
- Estado de validacion: no promover a `RATIO_INPUTS` entidades con `VALIDATION_BLOCKED`.
- Seguridad de datos: no incluir datos marcados como sensibles fuera de politica permitida.
- Trazabilidad: rechazo si faltan claves minimas de trazabilidad.

## 14. Reglas de exclusion

- Toda exclusion debe quedar en `EXCLUSIONS` con `reason_code` y `reason_detail`.
- Exclusion nunca implica borrado fisico del dato original intermedio.
- `RATIO_INPUTS` debe respetar `exclusion_flag` y `eligibility_status`.
- Reversion de exclusion permitida solo con nuevo evento trazado.

## 15. Que datos pueden entrar al Excel en fases futuras

- Catalogo de fuentes y versiones (`SOURCE_FILES`, `PROJECTS`, `BUDGET_VERSIONS`).
- Datos de coste parseados y normalizados intermedios con trazabilidad.
- Resultados de validacion y exclusiones.
- Entradas elegibles a ratios (`RATIO_INPUTS`) cuando reglas lo permitan.
- Ratios calculados versionados (`RATIOS_CALCULATED`) cuando exista fase habilitada.

## 16. Que datos no pueden entrar todavia

- Datos reales no validados para uso en ratios finales.
- Carga real consolidada al master operativo con datos sensibles.
- Cualquier payload RAW completo (solo indices/referencias).
- Resultados de categorias finales no aprobadas humanamente.
- Ratios finales consolidados mientras superficie base y reglas finales sigan pendientes.

## 17. Riesgos tecnicos

- Sobrescritura sin snapshot utilizable.
- Deriva de esquema entre hojas y pipeline.
- Debilidad de trazabilidad si faltan ids deterministas por fila.
- Inclusion accidental de datos no elegibles/sensibles.
- Complejidad de versionado cuando cambien reglas de normalizacion.

## 18. Decisiones pendientes

- Convencion definitiva de `row_hash` por formato.
- Politica final de `CATEGORY_MAPPING` (estado, aprobacion y taxonomia).
- Umbrales operativos de bloqueo/no bloqueo previos a publicacion.
- Estrategia de particionado temporal del maestro si crece volumen.
- Definicion final de reglas de calculo de ratios (fase posterior).

## 19. Relacion con ADR-019

Fase 9.1 no crea una nueva decision arquitectonica de alto nivel; desarrolla tecnicamente ADR-019 y operacionaliza su alcance. Por tanto, en esta fase no se crea ADR nueva.

## 20. Recomendacion para Fase 9.2

Abrir Fase 9.2 para implementacion controlada del generador del Excel maestro vivo con:

1. creacion de plantilla del maestro segun contrato 9.1;
2. validacion automatica de esquema antes de escritura;
3. escritura en entorno no sensible con fixtures;
4. snapshots pre/post y rollback;
5. pruebas automatizadas de trazabilidad, exclusiones y bloqueo de publicacion.
