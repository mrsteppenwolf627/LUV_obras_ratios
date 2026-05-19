# Fase 9.6: contrato de ingesta real controlada al Excel maestro vivo

## 1. Objetivo de la fase

Definir el contrato formal que determine cuando una carga `PREVIEW_ONLY` puede pasar a estado `OPERATIVE` dentro del Excel maestro vivo, sin habilitar todavia promocion automatica ni ingesta masiva real.

## 2. Contexto desde Fase 9.6-preview-fix

- Fase 9.6-preview y 9.6-preview-fix demostraron que la salida puede ser metodologicamente segura y operativamente legible.
- Sigue pendiente la puerta contractual para promocion controlada a estado operativo.
- Fase 9.6 formal cierra esa brecha con criterios explicitos de promocion, bloqueo y revision humana.

## 3. Diferencia entre PREVIEW_ONLY y OPERATIVE

- `PREVIEW_ONLY`: salida local de analisis, no promotable por defecto, sin efecto en ratios operativos.
- `OPERATIVE`: carga aceptada bajo contrato, trazable, versionada y elegible para fases posteriores de consolidacion (sin habilitar aun ratios finales).

## 4. Que significa promover una preview al Excel maestro vivo

Promover implica marcar una corrida/segmento de datos como apta para uso operativo futuro, conservando snapshots, trazabilidad completa, integridad referencial y evidencia de validacion.

## 5. Criterios minimos de promocion (PREVIEW_ONLY -> OPERATIVE)

1. `source_file_id` no vacio.
2. `import_batch_id` no vacio.
3. `budget_version_id` no vacio.
4. `source_sheet_name` presente cuando el input sea XLSX.
5. `source_row_number` presente cuando el input sea tabular.
6. `validation_status` valido segun contrato.
7. Sin estados `BLOCKED`/`ERROR` en filas criticas.
8. Sin `validation_status` desconocidos.
9. Sin IDs duplicados en claves criticas.
10. Sin relaciones rotas entre hojas contractuales.
11. Trazabilidad minima suficiente hacia el input.
12. Separacion minima de `item_description`/`amount` y, cuando sea detectable, `unit`/`quantity`/`unit_price`.
13. Prohibido mezclar importes en `item_description` si existe deteccion clara de columna monetaria.
14. `preview_only = TRUE` antes de promocion.
15. Promocion explicita y manual (nunca automatica por defecto).

## 6. Criterios de bloqueo (PROMOTION_BLOCKED)

- Archivo no interpretable.
- Formato no soportado.
- Falta de trazabilidad minima.
- Importes mezclados en descripcion cuando habia columna clara de importe.
- `amount` ausente en porcentaje alto de filas monetarias detectables (ver umbrales preliminares).
- Relaciones rotas entre hojas.
- Duplicados de IDs criticos.
- Estados `BLOCKED` o `ERROR` en filas criticas.
- Fallo de snapshot pre-promocion.
- Fallo de validacion de integridad.
- Ruta de output no permitida.
- Cualquier intento de modificar RAW.
- Uso de archivo real fuera de zona local controlada.

## 7. Criterios de revision humana (MANUAL_REVIEW_REQUIRED)

- Columnas ambiguas.
- Capitulos detectados sin codigo.
- Partidas detectadas sin unidad.
- Cantidad o precio unitario ausente, con importe presente.
- Importes parciales.
- Posibles totales de capitulo mezclados con partidas.
- Presupuesto parcial.
- Version potencialmente duplicada.
- Hoja no tabular.
- Multiples hojas con estructuras heterogeneas.

## 8. Umbrales minimos de completitud (preliminares)

Estos umbrales son **provisionales** y deben recalibrarse con mas casos reales:

- Trazabilidad completa minima (`source_sheet_name + source_row_number + source_file_id`): >= 95% filas operativas.
- Filas monetarias con `amount` separado cuando existe señal monetaria detectable: >= 85%.
- Filas con ambiguedad estructural: <= 20%.
- Filas que requieren `MANUAL_REVIEW_REQUIRED`: <= 25% para candidatura a promocion; >25% bloquea promocion automatica y fuerza revision.
- Filas criticas con `BLOCKED/ERROR`: 0% para promocion.

## 9. Reglas de calidad de separacion de campos

- `item_description` debe contener texto descriptivo, no valores monetarios separables.
- Si se detecta columna de importe, el valor va a `amount`, no a descripcion.
- `unit`, `quantity`, `unit_price` se pueblan cuando las cabeceras sean detectables con confianza minima.
- Si no hay confianza, dejar vacio y registrar `notes` + `MANUAL_REVIEW_REQUIRED` segun aplique.

## 10. Reglas de trazabilidad obligatoria

Minimo por fila operativa candidata:

- `source_file_id`
- `import_batch_id`
- `budget_version_id`
- `source_sheet_name` (XLSX)
- `source_row_number` (tabular)
- `validation_status`
- Referencia cruzable a `COST_ITEMS.origin_record_ref` y/o equivalente.

## 11. Reglas de idempotencia por run_id

- Cualquier evaluacion/potencial promocion debe asociarse a `run_id` unico.
- Repetir el mismo `run_id` no debe duplicar efectos ni crear doble promocion.
- Si el `run_id` ya existe, debe responder como `idempotent_skip` o estado equivalente.

## 12. Reglas de snapshots antes/despues de promocion

- Snapshot `pre_promotion` obligatorio antes de aplicar cambio de estado.
- Snapshot `post_promotion` obligatorio tras promocion valida.
- Ambos snapshots con checksum SHA-256 y registro en `SNAPSHOTS`.
- Evento de promocion trazado en `CHANGELOG`.

## 13. Reglas de rollback si falla promocion

- Si falla validacion durante promocion, rollback inmediato al snapshot `pre_promotion`.
- Si rollback falla, estado final debe quedar `PROMOTION_BLOCKED` con error trazado.
- Nunca dejar workbook en estado intermedio no validado.

## 14. Hojas que se poblarian al promover

- `IMPORT_LOG`
- `SOURCE_FILES`
- `PROJECTS`
- `BUDGET_VERSIONS`
- `RAW_IMPORTS` (indice, no payload RAW)
- `COST_ITEMS`
- `VALIDATION_RESULTS`
- `EXCLUSIONS` (si aplica)
- `SNAPSHOTS`
- `CHANGELOG`
- `IMPORTED_BUDGET_VIEW` (como vista operativa de entrada)

## 15. Hojas que seguirian vacias o pendientes

- `NORMALIZED_COST_ITEMS` (hasta fase de normalizacion formal habilitada).
- `CATEGORY_MAPPING` (sin decision final de categorias).
- `RATIO_INPUTS` (no alimentar con datos reales en esta fase).
- `RATIOS_CALCULATED` (sin calculo final habilitado).

## 16. Que datos no pueden alimentar ratios todavia

- Cualquier fila en `PREVIEW_ONLY`.
- Cualquier fila con `MANUAL_REVIEW_REQUIRED`, `BLOCKED`, `ERROR` o estado no reconocido.
- Cargas sin trazabilidad minima o con separacion insuficiente de campos economicos.

## 17. Riesgos

- Sobrepromocion de previews con calidad insuficiente.
- Heterogeneidad de estructuras XLSX reales.
- Deriva entre capa operativa y capa tecnica si no se aplica contrato de forma consistente.
- Presion de negocio para saltarse revision humana en casos ambiguos.

## 18. Limitaciones

- Umbrales aun preliminares por baja muestra real controlada.
- No se implementa en esta fase la promocion real completa.
- No se activa normalizacion final ni calculo final de ratios.

## 19. Decisiones pendientes

- Calibracion final de umbrales con corpus real ampliado.
- Definicion de taxonomia final para `CATEGORY_MAPPING`.
- Reglas finales de elegibilidad para alimentar `RATIO_INPUTS`.
- Politica de aprobacion humana (roles, SLA, trazas de aprobacion).

## 20. Recomendacion para Fase 9.7

Implementar evaluador contractual en modo `dry-run` que emita:

- `OPERATIVE_CANDIDATE`
- `PROMOTION_BLOCKED`
- `MANUAL_REVIEW_REQUIRED`

con salida trazable por `run_id`, tests sinteticos y sin habilitar todavia promocion automatica real.
