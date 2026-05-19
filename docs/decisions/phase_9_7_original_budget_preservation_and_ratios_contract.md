# Fase 9.7: contrato de preservacion del presupuesto original y enlace con ratios progresivos

## 1. Objetivo de la fase

Definir el contrato formal para que cada presupuesto importado pueda conservarse dentro del Excel maestro vivo con una logica equivalente al input cuando sea posible, coexistiendo con la capa tecnica que alimenta normalizacion y ratios progresivos.

## 2. Contexto desde Fase 9.6

- Fase 9.6 formal cerro el contrato `PREVIEW_ONLY -> OPERATIVE` (promocion, bloqueo y revision humana).
- La preview 9.6-preview-fix incorporo `IMPORTED_BUDGET_VIEW`, pero aun no fijaba una estrategia completa de preservacion multi-hoja del presupuesto original.
- Se confirma direccion de producto: el master no puede degradar el presupuesto a una tabla tecnica incomprensible.

## 3. Problema detectado

La salida previa fue segura y trazable, pero insuficiente en preservacion operativa del formato/logica de entrada para revisores humanos.

## 4. Decision de producto

Se adopta como regla de producto que el presupuesto importado debe preservarse en el master con estructura util equivalente al input cuando sea posible, sin sustituir la capa tecnica normalizada.

## 5. Capa preservada vs capa tecnica

- Capa preservada/operativa: representacion legible del presupuesto (hojas, filas, columnas, capitulos, partidas, unidades, cantidades, precios e importes cuando sea detectable).
- Capa tecnica/normalizada: `SOURCE_FILES`, `IMPORT_LOG`, `BUDGET_VERSIONS`, `RAW_IMPORTS`, `COST_ITEMS`, `NORMALIZED_COST_ITEMS`, `CATEGORY_MAPPING`, `VALIDATION_RESULTS`, `RATIO_INPUTS`, `RATIOS_CALCULATED`, `EXCLUSIONS`, `SNAPSHOTS`, `CHANGELOG`.

## 6. Regla de coexistencia obligatoria

Ambas capas deben coexistir y estar trazadas. La capa tecnica no reemplaza la capa preservada; la capa preservada no omite los controles tecnicos.

## 7. Estrategia elegida

Se adopta **Opcion C**:

- hojas visibles preservadas por presupuesto (lectura humana);
- indice y mapeo tecnico de trazabilidad (lectura de sistema/auditoria).

## 8. Estrategia de nombres de hojas preservadas

Se define una estrategia estable y sanitizada por bloque de presupuesto:

- `PRESERVED_###_INDEX`
- `PRESERVED_###_SHEET_###`
- `PRESERVED_###_MAPPING`

Reglas:

- `###` secuencial por presupuesto/version dentro del master.
- nombres originales de hoja siempre guardados en metadatos aunque el nombre visible se sanitize.
- nunca sobrescribir hojas preservadas de presupuestos anteriores.

## 9. Estrategia para inputs XLSX multi-hoja

- Cada hoja importable del XLSX debe preservarse como hoja visible equivalente (`PRESERVED_###_SHEET_###`) o vista equivalente documentada.
- Conservar `source_sheet_name` original.
- Conservar `source_row_number` y, si es viable, `source_column_number`.
- Mantener valores originales cuando sea posible, anadiendo columnas de trazabilidad sin destruir contenido util.

## 10. Estrategia para inputs BC3

- Preservacion en vista operativa equivalente por estructura BC3 (capitulos/partidas/mediciones/precios/importes).
- Mantener referencia a registro/linea origen BC3 en metadatos de trazabilidad.
- Evitar volcado plano que pierda jerarquia funcional del presupuesto.

## 11. Estrategia futura para Presto/PZH

- Se mantiene el compromiso de Fase 8: via export/herramienta evidenciada.
- No se implementa parser nativo nuevo en 9.7.
- Cuando exista ruta valida por caso, la preservacion debe seguir el mismo contrato de capa visible + mapeo tecnico.

## 12. Que significa mantener formato y sus limites

- Mantener formato significa conservar estructura de lectura util y equivalencia operativa, no clonar pixel-perfect del archivo original.
- Limites: heterogeneidad de layouts, celdas fusionadas, formulas complejas y hojas no tabulares.
- Si un campo no se detecta con fiabilidad, se deja vacio y se marca para revision humana.

## 13. Enlace entre fila preservada y fila tecnica

Toda fila preservada debe poder enlazarse por clave trazable minima:

- `source_file_id`
- `budget_version_id`
- `import_batch_id`
- `source_sheet_name`
- `source_row_number`
- `preserved_row_id` (o equivalente deterministico)

## 14. Enlace de partida preservada con COST_ITEMS

- `COST_ITEMS.origin_record_ref` debe apuntar a referencia preservada (`sheet!row` o equivalente estable).
- Cada `cost_item_id` debe poder resolverse hacia su fila preservada origen.

## 15. Enlace COST_ITEMS -> NORMALIZED_COST_ITEMS

- `NORMALIZED_COST_ITEMS.cost_item_id` es el puente obligatorio.
- No normalizar items bloqueados/error/manual review no resuelto.

## 16. Enlace NORMALIZED_COST_ITEMS -> RATIO_INPUTS

- `RATIO_INPUTS.normalized_cost_item_id` solo recibe items validados y elegibles.
- Items pendientes o bloqueados no pasan a entrada de ratios.

## 17. Actualizacion progresiva de ratios (fases posteriores)

- Los ratios no se calculan desde hojas preservadas directas.
- Los ratios se alimentan desde `RATIO_INPUTS`.
- `RATIOS_CALCULATED` se actualiza progresivamente conforme crece historico validado.
- Sin superficie base definida no se consolida ratio final.

## 18. Que datos pueden alimentar ratios

- Datos con trazabilidad completa y estado elegible tras validacion.
- Items normalizados con mapeo de categoria aprobado cuando aplique.

## 19. Que datos no pueden alimentar ratios todavia

- Filas `PREVIEW_ONLY`.
- Filas con `BLOCKED`, `ERROR`, `MANUAL_REVIEW_REQUIRED` o estado desconocido.
- Datos sin separacion minima de campos economicos cuando era detectable.
- Datos sin trazabilidad minima.

## 20. Criterios para crear hojas nuevas

- Mejora claridad operativa del presupuesto preservado.
- Mejora trazabilidad entre capa visible y tecnica.
- Evita mezclar presupuestos distintos sin contexto.
- Mantiene compatibilidad de integridad y validacion existentes.

## 21. Criterios para no crear hojas nuevas

- Si la nueva hoja duplica informacion sin valor funcional.
- Si rompe legibilidad o trazabilidad.
- Si introduce estructura incompatible con contrato actual.

## 22. Hojas nuevas evaluadas

Se propone incluir en el contrato (implementacion futura incremental):

- `PRESERVED_BUDGETS_INDEX`
- `PRESERVED_BUDGET_SHEETS`
- `PRESERVED_BUDGET_ROWS`
- `PRESERVED_BUDGET_CELLS` (opcional segun coste/beneficio y volumen)
- `PRESERVED_TO_COST_ITEMS_MAP`

Nota: la fase 9.7 no obliga a implementar todas; fija el contrato y prioridad.

## 23. Riesgos

- Crecimiento alto de hojas/volumen en el master.
- Dificultad de estandarizar layouts heterogeneos.
- Riesgo de desalineacion entre capa preservada y tecnica si falla mapeo.
- Presion por promover sin revision humana suficiente.

## 24. Limitaciones

- No hay ingesta real operativa masiva en esta fase.
- No hay normalizacion final ni calculo final de ratios.
- Umbrales finales de calidad deben recalibrarse con mas casos reales controlados.

## 25. Decisiones pendientes

- Nivel final de granularidad de preservacion (fila vs celda para todos los casos).
- Politica de versionado de bloques preservados por presupuesto.
- Umbrales definitivos para promocion OPERATIVE con multiples formatos reales.

## 26. Recomendacion para Fase 9.8

Implementar en modo incremental y seguro:

1. scaffolding de hojas de preservacion (`INDEX`, `SHEETS`, `MAP`);
2. estrategia de nombres sanitizados y secuenciales testeada;
3. mapeo trazable `preserved_row -> cost_item_id`;
4. pruebas sinteticas de no colision entre presupuestos;
5. evaluador dry-run conjunto (contrato 9.6 + contrato 9.7) sin promocion automatica.
