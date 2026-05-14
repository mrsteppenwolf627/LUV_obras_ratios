# Fase 4.3.1: ajuste menor de readiness y umbrales de relaciones BC3

## 1. Objetivo

Recalibrar de forma acotada el readiness del validador intermedio BC3 para evitar bloqueos excesivos cuando la evidencia t?cnica apunta a revisi?n manual no bloqueante.

## 2. Contexto desde Fase 4.3

- Fase 4.3 qued? implementada con contrato de readiness por archivo y por lote.
- Resultado real heredado: `ERROR` en lote real.
- Recomendaci?n heredada: abrir ajuste menor 4.3.1.

## 3. Estado real actual

- Estado heredado al inicio de 4.3.1: `ERROR`.
- Bloqueos activos heredados (sanitizado):
  - `ORPHAN_RELATIONS_BLOCKING` en un archivo.
  - `UNKNOWN_RECORDS_OVER_THRESHOLD` en un archivo.
  - `MISSING_MANUAL_REASONS` como ajuste t?cnico menor en ambos archivos.

## 4. Motivos concretos del ERROR (sanitizado)

1. Relaciones `~D` con hijos no presentes en `concepts` parseados en volumen relevante.
2. Unknown record types por encima de umbral inicial de tipos (no de peso estructural).
3. `manual_review_required` vac?o en parse preliminar pese a se?ales de revisi?n manual.

## 5. An?lisis de relaciones hu?rfanas

- Cantidad observada (sanitizada): un archivo por encima del umbral absoluto previo, otro por debajo.
- Proporci?n observada: no necesariamente mayoritaria respecto del total de relaciones.
- Impacto en estructura m?nima: en el lote real sigue existiendo `~V`, volumen de `~C` y relaciones v?lidas.
- Conclusi?n 4.3.1: la orfandad no debe bloquear solo por conteo absoluto; debe bloquear cuando sea masiva y con impacto estructural.
- Regla recalibrada:
  - `validation_blocker` solo si `orphan_count >= 15` y `orphan_ratio >= 0.40`.
  - En otros casos, `non_blocking_manual_review` con trazabilidad expl?cita.

## 6. An?lisis de unknown records sobre umbral

- Tipos observados (sanitizado): variantes preservadas como unsupported.
- Preservaci?n: se mantienen en `unknown_record_types` / `unsupported_records`.
- Impacto estructural: no impiden detectar `~V`, `~C`, `~D` en el lote real.
- Conclusi?n 4.3.1: superar umbral por cantidad de tipos no implica bloqueo si su peso real en el archivo es bajo.
- Regla recalibrada:
  - `UNKNOWN_RECORDS_PREDOMINANT` bloqueante cuando adem?s la presencia desconocida es estructuralmente predominante.
  - `UNKNOWN_RECORDS_OVER_THRESHOLD` no bloqueante cuando el peso relativo es bajo y la estructura m?nima existe.

## 7. An?lisis de MISSING_MANUAL_REASONS

- Diagn?stico: el origen del problema estaba en parser preliminar y en el control del validador.
- En parser preliminar se a?adieron razones expl?citas para se?ales manuales diagn?sticas:
  - `ENCODING_REVIEW_RECOMMENDED`
  - `UNKNOWN_RECORD_TYPES_REVIEW`
  - `AMBIGUOUS_ECONOMIC_SIGNALS_REVIEW`
  - `MULTIPLE_UNITS_REVIEW`
- El validador mantiene la detecci?n de inconsistencia si en futuros casos vuelve a faltar justificaci?n.

## 8. Decisi?n de recalibraci?n

Se aprueba ajuste menor acotado en validador y parser preliminar para:

1. distinguir bloqueos estructurales reales de revisi?n manual no bloqueante;
2. usar criterio relativo (proporcional) adem?s de umbral absoluto;
3. garantizar razones expl?citas en `manual_review_required` desde origen cuando aplica.

## 9. Criterios actualizados de readiness

- `VALIDATION_BLOCKED`:
  - falta estructura m?nima, decodificaci?n fallida, ausencia cr?tica (`~V`/`~C`) o relaciones hu?rfanas masivas con ratio alto.
- `VALIDATION_READY_WITH_NON_BLOCKING_MANUAL_REVIEW`:
  - hay revisi?n manual, pero no compromete estructura m?nima.
- `VALIDATION_NEEDS_MINOR_ADJUSTMENTS`:
  - no hay bloqueos de datos, pero hay ajustes t?cnicos de clasificaci?n/explicaci?n.
- `VALIDATION_READY_FOR_STRICTER_PARSER_DESIGN`:
  - sin bloqueadores ni ajustes menores pendientes.

## 10. Riesgos

- Umbral de orfandad puede requerir recalibraci?n por lote.
- Variantes FIEBDC futuras pueden elevar unknowns con impacto real.
- Exceso de tolerancia puede ocultar bloqueos si no se monitoriza ratio de unknowns y consistencia de relaciones.

## 11. Decisiones pendientes

- Umbral definitivo por tipolog?a de presupuesto/BC3.
- Pol?tica final de normalizaci?n de unidades.
- Pol?tica final de interpretaci?n econ?mica previa a fases de importaci?n.

## 12. Recomendaci?n final

- Ejecutar nuevamente parser+validador sobre lote real local.
- Si el estado pasa a `VALIDATION_READY_WITH_NON_BLOCKING_MANUAL_REVIEW`, avanzar a fase siguiente de parser m?s estricto con trazabilidad de riesgos.
- Si persiste `VALIDATION_BLOCKED` por razones estructurales reales, abrir ajuste acotado adicional en lugar de avanzar de fase.
