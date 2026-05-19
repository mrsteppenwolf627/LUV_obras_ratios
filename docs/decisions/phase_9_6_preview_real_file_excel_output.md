# Fase 9.6-preview: vista previa local de salida Excel con archivo real aislado

## Objetivo de la prueba

Generar una salida Excel local de inspeccion visual usando un unico archivo real aislado, sin promocion al master operativo.

## Contexto desde Fase 9.5

- Fase 9.5 quedo cerrada tecnicamente con idempotencia por `run_id`, checksum SHA-256 y rollback negativo.
- El generador del Excel maestro vivo ya tiene estructura, validaciones, snapshots y controles de ruta.
- Antes de abrir ingesta real formal al master, se ejecuta una preview local controlada.

## Por que se hace una preview antes de ingesta real formal

- Reducir riesgo de promocion prematura de datos reales al master operativo.
- Verificar visualmente estructura, trazabilidad y marcadores `PREVIEW_ONLY`.
- Identificar limitaciones de mapeo sin activar calculo de ratios finales.

## Archivo real usado (identificador sanitizado)

- Identificador sanitizado: `REAL_SAMPLE_001`.
- Tipo detectado: `XLSX`.
- Origen local: archivo real aislado ya existente en `data/samples/` (no copiado al repositorio).

## Flujo ejecutado

1. Creacion/actualizacion de workbook preview en ruta segura ignorada por Git.
2. Lectura aislada del workbook real (solo primera hoja, primeras filas no vacias).
3. Poblado controlado con IDs sanitizados y etiquetas `PREVIEW_ONLY` en hojas del maestro.
4. Sin importacion formal al master operativo.
5. Sin calculo de ratios finales ni consolidacion definitiva.

## Que datos se pudieron trasladar al Excel preview

- `SOURCE_FILES`: una entrada sintetizada con `source_file_id` sanitizado.
- `IMPORT_LOG`: lote de preview (`PREVIEW_ONLY`).
- `PROJECTS`: proyecto placeholder de preview.
- `BUDGET_VERSIONS`: version placeholder ligada al archivo sanitizado.
- `RAW_IMPORTS`: referencia local sanitizada (`preview://...`).
- `COST_ITEMS`: filas derivadas de muestra de filas reales, sin importes consolidados.
- `VALIDATION_RESULTS`: resultado informativo de ejecucion preview.
- `EXCLUSIONS`: exclusion de ejemplo no operativa.
- `CHANGELOG`: evento de preview local.

## Que datos quedaron vacios o pendientes

- `NORMALIZED_COST_ITEMS`: vacio.
- `CATEGORY_MAPPING`: vacio.
- `RATIO_INPUTS`: vacio.
- `RATIOS_CALCULATED`: vacio.
- Sin normalizacion final de categorias.
- Sin consolidacion definitiva de importes.

## Limitaciones de la salida

- No representa importacion real formal al master.
- No incluye pipeline completo de validacion semantica por categoria.
- Solo muestra una porcion de filas para inspeccion visual.
- No habilita decisiones finales de ratios ni superficie base.

## Riesgos detectados

- Riesgo de interpretar la preview como salida operativa final si no se etiqueta correctamente.
- Riesgo de sobrelectura de campos economicos sin contrato de ingesta formal 9.6.
- Riesgo de extrapolar mapeos no validados desde una unica muestra real.

## Confirmaciones metodologicas

- Esta salida **no** es master operativo.
- No hubo promocion a master vivo formal.
- No se modifico RAW.
- No se suben outputs reales ni sensibles.
- El Excel generado de preview queda en ruta local ignorada por Git.

## Recomendacion para Fase 9.6 formal

- Definir contrato de ingesta real controlada al master (criterios de entrada, bloqueos, promocion y auditoria).
- Mantener `PREVIEW_ONLY` separado de `OPERATIVE`.
- Habilitar paso de promocion solo con validaciones de integridad + reglas de negocio aprobadas.
