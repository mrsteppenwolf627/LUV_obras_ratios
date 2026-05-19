# Fase 9.8: implementacion incremental de preservacion del presupuesto original y mapeo hacia COST_ITEMS

## 1. Objetivo de la fase

Implementar scaffolding inicial para conservar presupuestos importados dentro del Excel maestro vivo de forma reconocible, con trazabilidad hacia la capa tecnica `COST_ITEMS`, sin promocion automatica ni calculo final de ratios.

## 2. Contexto desde Fase 9.7

- Fase 9.7 cerro contrato de preservacion con estrategia Opcion C.
- Se definio coexistencia obligatoria de capa preservada y capa tecnica.
- Quedaba pendiente implementacion incremental segura.

## 3. Alcance de implementacion

- Ampliacion de esquema minimo del master con hojas indice/mapa de preservacion.
- Generacion de hojas visibles preservadas sanitizadas en flujo preview.
- Trazabilidad `preserved_row -> cost_item_id` en hoja de mapeo.
- Tests sinteticos de nombres, no colision y trazabilidad.

## 4. Fuera de alcance

- Promocion automatica a master operativo.
- Ingesta real operativa masiva.
- Calculo de ratios finales.
- Normalizacion final de categorias.
- Consolidacion definitiva de importes.
- Implementacion completa de evaluador dry-run combinado.

## 5. Hojas preservadas implementadas

- `PRESERVED_BUDGETS_INDEX`
- `PRESERVED_BUDGET_SHEETS`
- `PRESERVED_TO_COST_ITEMS_MAP`

## 6. Hojas indice/mapa implementadas

- `PRESERVED_BUDGETS_INDEX`: indice por presupuesto preservado.
- `PRESERVED_BUDGET_SHEETS`: inventario por hoja preservada.
- `PRESERVED_TO_COST_ITEMS_MAP`: enlace por fila preservada a `COST_ITEMS`.

## 7. Estrategia de nombres de hojas

- Convencion visible: `PRES_<budget_seq>_<sheet_seq>_<source_sanitized>`.
- Secuencial por presupuesto (`001`, `002`, ...).
- Secuencial por hoja dentro del presupuesto (`001`, `002`, ...).
- Colisiones resueltas con sufijo incremental.

## 8. Reglas de sanitizacion de nombres

- Sustitucion de caracteres invalidos de Excel (`[]:*?/\\`) por `_`.
- Normalizacion de espacios.
- Longitud maxima 31 caracteres.
- Fallback estable si nombre original no es usable.

## 9. Como se preserva la logica/formato del input

- Se mantiene orden de filas por hoja.
- Se mantienen valores originales de celdas como texto legible.
- Se preserva separacion por hoja del input.
- Metadatos tecnicos se agregan al final con columnas de trazabilidad.

## 10. Como se conserva trazabilidad hoja/fila/columna origen

En hojas preservadas visibles se anaden:

- `__source_sheet_name`
- `__source_row_number`
- `__source_column_number` (inicialmente vacio en este scaffolding)

Adicionalmente se registra:

- `source_sheet_name`
- `source_row_number`
- `preserved_sheet_id`
- `preserved_row_id`

en hojas indice/mapa.

## 11. Como se enlaza capa preservada con COST_ITEMS

`PRESERVED_TO_COST_ITEMS_MAP` registra:

- claves de fuente (`source_file_id`, `import_batch_id`, `budget_version_id`);
- identificadores preservados (`preserved_sheet_id`, `preserved_row_id`);
- referencia origen (`source_sheet_name`, `source_row_number`);
- `cost_item_id`;
- estado de mapping (`MAPPED` / `UNMAPPED`);
- confianza y estado de validacion.

## 12. Como se evita duplicar datos por run_id

- Se mantiene control existente de idempotencia por `run_id` en carga sintetica.
- En preview se anade bloque preservado nuevo por corrida, sin sobrescribir bloques previos.
- Nombres visibles y IDs preservados usan secuencia incremental y UUID parcial para evitar colision.

## 13. Compatibilidad con Fases 9.1 a 9.7

- Se mantiene CLI principal `generate_live_excel_master.py`.
- Se mantiene contrato base y validaciones de integridad previas.
- No se alteran reglas de bloqueo de `RATIO_INPUTS`.
- No se habilita promocion automatica.

## 14. Tests anadidos o modificados

- Nuevo: `tests/scripts/test_live_excel_budget_preservation.py`.
- Cobertura:
  - creacion de hojas indice/mapa;
  - sanitizacion y unicidad de nombres preservados;
  - trazabilidad base en hojas visibles;
  - presencia de estados de mapping (`MAPPED`/`UNMAPPED`).

## 15. Riesgos

- Crecimiento del workbook por preservacion multi-hoja.
- Variabilidad de inputs no tabulares.
- Mapping parcial en fases tempranas.

## 16. Limitaciones

- `PRESERVED_BUDGET_ROWS` y `PRESERVED_BUDGET_CELLS` no se implementan en 9.8.
- `__source_column_number` queda reservado (sin poblado completo aun).
- Evaluador dry-run combinado no se implementa en esta fase para evitar refactor amplio.

## 17. Confirmacion metodologica

- No se habilita promocion automatica.
- No se habilita ingesta real operativa masiva.
- No se habilita calculo de ratios finales.

## 18. Recomendacion para Fase 9.9

- Implementar evaluador dry-run combinado (contrato 9.6 + 9.7) con estado adicional `PRESERVATION_INCOMPLETE`.
- Endurecer reglas de mapping ambiguo/no tabular.
- Evaluar implementacion de `PRESERVED_BUDGET_ROWS` como capa intermedia antes de granularidad por celda.
