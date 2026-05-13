# Master Schema Preliminar

## 1. Proposito del master

El master de ratios no se define como un unico Excel final. Se define como una estructura de datos trazable y auditable para consolidar presupuestos historicos, normalizar informacion, validar coherencia matematica y calcular ratios de forma progresiva y reproducible.

## 2. Principios de diseno

- RAW inmutable.
- Separacion de capas.
- Validacion antes de calculo.
- Calculo reproducible.
- Trazabilidad hasta origen.
- Exclusion sin borrado.
- No estimacion automatica de datos ausentes.
- No dependencia de PDFs salvo revision manual.
- Capacidad de auditoria tecnica y funcional.

## 3. Capas del master

### 1. RAW_IMPORTS
- Objetivo: conservar la carga original sin transformaciones.
- Datos: blobs/metadata de ingesta por lote.
- Editable: no (solo append).
- Afecta ratios: indirectamente.
- Relacion: base para SOURCE_FILES e IMPORT_BATCH.

### 2. PROJECTS
- Objetivo: representar proyectos de obra.
- Datos: identificacion, contexto, superficie base y estado.
- Editable: si, con control de cambios.
- Afecta ratios: si.
- Relacion: padre de BUDGET_VERSIONS y RATIO_INPUTS.

### 3. BUDGET_VERSIONS
- Objetivo: gestionar versiones de presupuesto por proyecto.
- Datos: version, moneda, totales, flags de vigencia.
- Editable: si, bajo reglas.
- Afecta ratios: si.
- Relacion: conecta PROJECT y SOURCE_FILE con COST_ITEM.

### 4. COST_ITEMS
- Objetivo: conservar partidas/capitulos originales.
- Datos: codigo, descripcion, unidad, medicion, precio, importe y referencia fuente.
- Editable: no (solo correcciones por capas nuevas, no sobreescritura).
- Afecta ratios: indirectamente.
- Relacion: origen de NORMALIZED_COST_ITEMS.

### 5. NORMALIZED_COST_ITEMS
- Objetivo: estandarizar partidas para comparabilidad.
- Datos: categoria normalizada, unidad/importe normalizados, estado de revision.
- Editable: si, con versionado y trazabilidad.
- Afecta ratios: si.
- Relacion: depende de COST_ITEMS y CATEGORY_MAPPING.

### 6. CATEGORY_MAPPING
- Objetivo: definir reglas de mapeo de origen a categoria normalizada.
- Datos: patrones, prioridad, estado activo, autores/revisores.
- Editable: si, controlado.
- Afecta ratios: si.
- Relacion: alimenta NORMALIZED_COST_ITEMS.

### 7. VALIDATION_RESULTS
- Objetivo: registrar resultados de validaciones.
- Datos: regla, severidad, esperado/actual, estado, resolucion.
- Editable: no en historico; solo nuevos eventos o resoluciones trazadas.
- Afecta ratios: si (bloquea/incluye).
- Relacion: aplica a cualquier entidad validable.

### 8. RATIO_INPUTS
- Objetivo: fijar dataset aprobado para calculo.
- Datos: importes validados, superficie base, elegibilidad.
- Editable: no destructivo; regenerable por version.
- Afecta ratios: directo.
- Relacion: deriva de NORMALIZED_COST_ITEMS y VALIDATION_RESULTS.

### 9. RATIOS_CALCULATED
- Objetivo: almacenar resultados de calculo agregados.
- Datos: metricas de ratio, alcance, muestra y version de calculo.
- Editable: no; se recalcula con nueva version.
- Afecta ratios: es la salida principal.
- Relacion: deriva de RATIO_INPUTS.

### 10. IMPORT_LOG
- Objetivo: bitacora de procesos de importacion.
- Datos: eventos, errores, advertencias, tiempos, operador.
- Editable: append-only.
- Afecta ratios: indirectamente.
- Relacion: conecta con IMPORT_BATCH y SOURCE_FILE.

### 11. EXCLUSIONS
- Objetivo: excluir datos sin eliminarlos.
- Datos: motivo, alcance, reversibilidad, autor y fecha.
- Editable: si, con historial.
- Afecta ratios: si.
- Relacion: aplica a cualquier entidad excluible.

### 12. SOURCE_FILES
- Objetivo: catalogar cada archivo importado.
- Datos: hash, extension, tipo detectado, prioridad, metadatos.
- Editable: no para identidad; si para anotaciones.
- Afecta ratios: indirectamente.
- Relacion: referencia clave para BUDGET_VERSION y COST_ITEM.

## 4. Entidades principales

### SOURCE_FILE

- source_file_id
- original_filename
- file_extension
- file_type_detected
- file_hash
- file_size_bytes
- source_path
- import_batch_id
- imported_at
- imported_by
- is_primary_source
- source_priority
- notes

### IMPORT_BATCH

- import_batch_id
- imported_at
- imported_by
- import_status
- source_folder
- files_detected_count
- files_imported_count
- files_rejected_count
- validation_status
- notes

### PROJECT

- project_id
- project_code
- project_name
- location
- province
- country
- client_type
- project_type
- work_type
- status
- surface_base_value
- surface_base_unit
- surface_base_type
- surface_base_source
- surface_base_validation_status
- category_current
- category_source
- notes

Nota: la superficie base queda pendiente de decision metodologica definitiva.

### BUDGET_VERSION

- budget_version_id
- project_id
- source_file_id
- version_name
- version_date
- version_type
- is_contract_version
- is_latest_version
- currency
- tax_included
- total_amount_declared
- total_amount_calculated
- total_difference
- validation_status
- notes

### COST_ITEM

- cost_item_id
- budget_version_id
- source_file_id
- source_sheet
- source_row
- original_code
- original_parent_code
- original_level
- original_description
- original_unit
- original_quantity
- original_unit_price
- original_amount
- original_chapter
- raw_text
- extraction_confidence
- notes

### NORMALIZED_COST_ITEM

- normalized_item_id
- cost_item_id
- project_id
- budget_version_id
- normalized_category_id
- normalized_category_name
- normalized_description
- normalized_unit
- normalized_quantity
- normalized_unit_price
- normalized_amount
- normalization_method
- mapping_confidence
- requires_manual_review
- validation_status
- excluded_from_ratios
- exclusion_reason_id

### CATEGORY_MAPPING

- mapping_id
- original_text_pattern
- original_code_pattern
- normalized_category_id
- normalized_category_name
- mapping_rule_type
- priority
- active
- created_at
- created_by
- reviewed_by
- notes

### VALIDATION_RESULT

- validation_result_id
- entity_type
- entity_id
- validation_rule_id
- severity
- validation_status
- message
- expected_value
- actual_value
- difference_value
- created_at
- resolved_at
- resolved_by
- notes

### RATIO_INPUT

- ratio_input_id
- project_id
- budget_version_id
- normalized_item_id
- normalized_category_id
- amount_for_ratio
- surface_base_value
- surface_base_type
- include_in_ratio
- inclusion_reason
- validation_snapshot_id
- created_at

### RATIO_CALCULATED

- ratio_id
- calculation_date
- ratio_scope
- normalized_category_id
- category_name
- project_type
- work_type
- location_scope
- sample_count
- total_amount
- total_surface
- weighted_ratio_eur_m2
- simple_average_ratio_eur_m2
- min_ratio_eur_m2
- max_ratio_eur_m2
- median_ratio_eur_m2
- excluded_count
- calculation_version
- notes

### EXCLUSION

- exclusion_reason_id
- entity_type
- entity_id
- reason_code
- reason_description
- excluded_by
- excluded_at
- reversible
- notes

## 5. Estados normalizados

### import_status
- DETECTED
- IMPORTED_RAW
- PARSED
- NORMALIZED
- VALIDATED
- REJECTED
- FAILED
- PARTIAL

### validation_status
- NOT_VALIDATED
- VALID
- WARNING
- ERROR
- BLOCKED
- MANUAL_REVIEW_REQUIRED

### ratio_eligibility
- ELIGIBLE
- NOT_ELIGIBLE
- PENDING_REVIEW
- EXCLUDED
- SUPERSEDED

### source_priority
- PRIMARY
- SECONDARY
- REFERENCE_ONLY
- MANUAL_ONLY

## 6. Reglas preliminares de validacion

- No calcular ratios si falta superficie base.
- No calcular ratios si el importe es nulo o negativo sin justificacion.
- No consolidar presupuesto si la suma de partidas no cuadra con total declarado dentro de tolerancia definida.
- No actualizar ratios si hay capitulos sin mapear y el umbral de capitulos no mapeados supera el limite permitido.
- No importar dos veces el mismo archivo con el mismo hash sin marcarlo como duplicado.
- No usar PDF como fuente automatica primaria si hay BC3 o Excel.
- No considerar definitiva una version de presupuesto si no esta marcada como contrato, ultima version o version aprobada.
- No mezclar superficies de tipos distintos en el mismo calculo.
- No borrar datos rechazados; deben quedar con estado REJECTED, EXCLUDED o BLOCKED.

Nota: tolerancias numericas exactas quedan pendientes de decision.

## 7. Claves y trazabilidad

```text
SOURCE_FILE
  -> IMPORT_BATCH
  -> BUDGET_VERSION
  -> COST_ITEM
  -> NORMALIZED_COST_ITEM
  -> RATIO_INPUT
  -> RATIO_CALCULATED

PROJECT
  -> BUDGET_VERSION
  -> RATIO_INPUT
  -> RATIO_CALCULATED

CATEGORY_MAPPING
  -> NORMALIZED_COST_ITEM

VALIDATION_RESULT
  -> cualquier entidad validable

EXCLUSION
  -> cualquier entidad excluible
```

## 8. Campos pendientes de decision

- Superficie base oficial.
- Categorias definitivas.
- Umbrales de categorias.
- Tolerancia aceptable entre total declarado y total calculado.
- Tratamiento de IVA/impuestos.
- Tratamiento de honorarios.
- Tratamiento de paisajismo, piscina, urbanizacion y exteriores.
- Tratamiento de versiones de presupuesto.
- Tratamiento de presupuestos parciales.
- Tratamiento de duplicados por nombre distinto pero mismo contenido.
- Tratamiento de archivos Presto nativos no BC3.
- Moneda e inflacion/actualizacion temporal.
- Si se ajustaran ratios por ano o no.

## 9. Criterios para pasar a implementacion

Antes de implementar parsers se debe:

- Revisar este documento.
- Confirmar superficie base.
- Confirmar categorias iniciales.
- Confirmar estructura minima del master.
- Analizar al menos 2-3 archivos reales controlados.
- Crear politica de duplicados.
- Crear politica de versionado de presupuesto.
