# Fase 9.10: piloto dry-run real con varios presupuestos aislados

## Objetivo de la fase

Ejecutar una prueba real controlada (local, reversible y sin promocion automatica) para validar la combinacion:

- preview preservada;
- capa visible preservada;
- mapeo a `COST_ITEMS`;
- evaluador dry-run combinado.

## Contexto desde Fase 9.9

- Fase 9.9 cerro el evaluador dry-run con estados:
  - `OPERATIVE_CANDIDATE`
  - `PROMOTION_BLOCKED`
  - `MANUAL_REVIEW_REQUIRED`
  - `PRESERVATION_INCOMPLETE`
- Quedaba pendiente contrastar esos estados con varios casos reales aislados.

## Alcance de la prueba real controlada

- Ejecucion local sobre un conjunto pequeno de archivos reales aislados.
- Generacion de preview por archivo en ruta ignorada por Git.
- Evaluacion dry-run por `run_id` sanitizado.
- Registro de metricas, estado y motivos por archivo.

## Fuera de alcance

- Promocion operativa real.
- Actualizacion del master operativo.
- Calculo final de ratios.
- Normalizacion final de categorias.
- Consolidacion definitiva de importes.

## Archivos reales usados (IDs sanitizados)

- `REAL_DRY_RUN_001`
- `REAL_DRY_RUN_002`
- `REAL_DRY_RUN_003`

## Formato de cada archivo

- `REAL_DRY_RUN_001`: `xlsx`
- `REAL_DRY_RUN_002`: `xlsx`
- `REAL_DRY_RUN_003`: `xlsx`

## Flujo ejecutado por archivo

1. Generacion preview local preservada (`PREVIEW_ONLY`).
2. Creacion de hojas preservadas visibles (`PRES_*`) + hojas indice/mapa.
3. Generacion/actualizacion de `PRESERVED_TO_COST_ITEMS_MAP`.
4. Evaluacion dry-run combinada sin promocion automatica.

## Resultado de preview preservada por archivo

- `REAL_DRY_RUN_001`: preview generado; hojas preservadas visibles y operativa presentes.
- `REAL_DRY_RUN_002`: preview generado; hojas preservadas visibles y operativa presentes.
- `REAL_DRY_RUN_003`: preview generado; hojas preservadas visibles y operativa presentes.

## Resultado del evaluador dry-run por archivo

- `REAL_DRY_RUN_001`: `OPERATIVE_CANDIDATE`
- `REAL_DRY_RUN_002`: `PROMOTION_BLOCKED`
- `REAL_DRY_RUN_003`: `OPERATIVE_CANDIDATE`

## Metricas por archivo

### REAL_DRY_RUN_001
- `mapping_rate`: `0.7938144329896907`
- `traceability_rate`: `1.0`
- `manual_review_rate`: `0.0`
- `blocked_rate`: `0.0`
- `amount_separation_rate`: `1.0`
- `ratio_input_rows`: `0.0`
- `ratio_calculated_rows`: `0.0`

### REAL_DRY_RUN_002
- `mapping_rate`: `0.9`
- `traceability_rate`: `1.0`
- `manual_review_rate`: `0.0`
- `blocked_rate`: `0.0`
- `amount_separation_rate`: `0.0`
- `ratio_input_rows`: `0.0`
- `ratio_calculated_rows`: `0.0`

### REAL_DRY_RUN_003
- `mapping_rate`: `0.7590361445783133`
- `traceability_rate`: `1.0`
- `manual_review_rate`: `0.0`
- `blocked_rate`: `0.0`
- `amount_separation_rate`: `1.0`
- `ratio_input_rows`: `0.0`
- `ratio_calculated_rows`: `0.0`

## Estado final por archivo

- `REAL_DRY_RUN_001`: `OPERATIVE_CANDIDATE`
- `REAL_DRY_RUN_002`: `PROMOTION_BLOCKED`
- `REAL_DRY_RUN_003`: `OPERATIVE_CANDIDATE`

## Motivos explicitos por archivo

- `REAL_DRY_RUN_001`: sin motivos de bloqueo/revision.
- `REAL_DRY_RUN_002`:
  - `amount_mixed_in_description`
  - `insufficient_amount_separation`
- `REAL_DRY_RUN_003`: sin motivos de bloqueo/revision.

## Evaluacion visual resumida por archivo

- `REAL_DRY_RUN_001`:
  - Se preservan hojas del input (2 hojas visibles preservadas).
  - Se reconoce estructura tabular.
  - No se detectaron importes separados en la vista operativa (limitacion de deteccion para este layout).
- `REAL_DRY_RUN_002`:
  - Se preserva hoja visible del input.
  - Se detectan importes en `amount`, pero siguen mezclados en descripcion en filas monetarias detectadas.
  - El estado `PROMOTION_BLOCKED` es coherente con el contrato.
- `REAL_DRY_RUN_003`:
  - Se preservan hojas del input (2 hojas visibles preservadas).
  - Estructura legible y trazable.
  - Igual que en `REAL_DRY_RUN_001`, la separacion de importes no siempre aplica por layout detectado.

## Limitaciones detectadas

- Heuristica de separacion `description/amount` dependiente de cabeceras y layout real.
- En algunos XLSX, `amount` no se detecta/puebla aunque la preservacion visible sea correcta.
- `mapping_rate` aun heterogeneo entre ficheros (rango observado aproximado: 0.75-0.90).

## Ajustes recomendados

1. Mejorar heuristicas de deteccion de columnas monetarias para layouts heterogeneos.
2. Aumentar precision de `PRESERVED_TO_COST_ITEMS_MAP` en filas no tabulares o mixtas.
3. Anadir diagnostico explicito por archivo sobre por que `amount` no fue separable.

## Umbrales preliminares: evaluacion de adecuacion

Umbrales usados (preliminares):

- `traceability_rate >= 0.95`
- `amount_separation_rate >= 0.85` (cuando aplique)
- `manual_review_rate <= 0.25`
- `blocked_rate = 0`

Evidencia del piloto:

- `traceability_rate` y `blocked_rate` se comportan bien en los 3 casos.
- `amount_separation_rate` discrimina correctamente un caso problematico (`REAL_DRY_RUN_002`), pero necesita mejorar cobertura en layouts donde no se detecta `amount`.

Conclusion: los umbrales son utiles como gate preliminar, pero requieren recalibracion y mejor observabilidad antes de fijarlos como definitivos.

## Confirmaciones metodologicas

- No hubo promocion automatica.
- No se actualizo master operativo.
- No se subieron outputs sensibles.
- No se modifico RAW.
- No se subieron archivos reales ni Excels generados.

## Recomendacion para Fase 9.11

Abrir fase de ajustes post-piloto enfocada en:

1. mejora de separacion de campos monetarios en preview operativa;
2. mejora de cobertura/precision de mapping preservado -> `COST_ITEMS`;
3. recalibracion controlada de umbrales preliminares con mas casos reales aislados;
4. mantener estrictamente `no promotion by default`.
