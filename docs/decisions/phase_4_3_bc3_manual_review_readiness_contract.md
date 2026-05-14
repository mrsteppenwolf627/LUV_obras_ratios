# Fase 4.3: contrato de resolucion de manual_review y readiness de validacion BC3

## 1. Objetivo

Definir un contrato de readiness de validacion para clasificar hallazgos estructurales BC3 y separar:

- bloqueadores reales de validacion;
- manual review bloqueante;
- manual review asumible;
- decisiones humanas futuras;
- ajustes tecnicos menores.

## 2. Contexto heredado de Fase 4.2

- El validador preliminar existe y valida estructura intermedia.
- El lote real evaluado devuelve `MANUAL_REVIEW_REQUIRED`.
- No hay errores bloqueantes globales de parseo/decodificacion en ese lote.

## 3. Resultado real actual

- Estado global observado: `MANUAL_REVIEW_REQUIRED`.
- Causas principales observadas (sanitizado): relaciones `~D` con hijos no presentes en conceptos parseados y ausencia de razones explicitas en `manual_review_required` del parse preliminar.

## 4. Motivos detectados del manual_review real (sanitizado)

1. `RELATION_ORPHAN_CHILD` repetido en `BC3_01` y `BC3_02`.
2. `UNKNOWN_RECORDS_OVER_THRESHOLD` en `BC3_01`.
3. `MISSING_MANUAL_REASONS` en ambos archivos.

Interpretacion de Fase 4.3:

- `MISSING_MANUAL_REASONS` se clasifica como ajuste tecnico menor del flujo, no como bloqueo de datos.
- Relaciones huerfanas deben diferenciar entre volumen asumible y volumen bloqueante.

## 5. Clasificacion de manual_review

- `validation_blocker`:
  - JSON ilegible o estructura raiz ausente.
  - Falta `~V`.
  - Falta `~C` en archivo de presupuesto.
  - Decodificacion fallida.
  - Relaciones huerfanas masivas (sobre umbral bloqueante).
- `non_blocking_manual_review`:
  - Unknown records bajo umbral.
  - Variantes preservadas en `unsupported`.
  - Multiples unidades mientras no se normaliza.
  - Ambiguedad economica mientras no se consolidan importes.
- `future_policy_decision`:
  - Normalizacion de unidades.
  - Interpretacion economica final.
  - Normalizacion de categorias.
- `minor_adjustment_item`:
  - Warning sin clasificacion clara.
  - Falta de explicacion de manual review en campos esperados.

## 6. Tabla de severidades

| Severidad | Uso |
|---|---|
| INFO | Señales correctas o riesgo bajo |
| WARNING | Riesgo no bloqueante |
| ERROR | Error estructural por archivo |
| MANUAL_REVIEW_REQUIRED | Revisión humana requerida |
| BLOCKED | Bloqueo de validación |

## 7. Criterios de readiness por archivo

- `VALIDATION_READY_FOR_STRICTER_PARSER_DESIGN`:
  - sin blockers y sin manual review bloqueante.
- `VALIDATION_READY_WITH_NON_BLOCKING_MANUAL_REVIEW`:
  - manual review clasificado como no bloqueante + warnings controlados.
- `VALIDATION_NEEDS_MINOR_ADJUSTMENTS`:
  - sin bloqueadores de datos, pero con items técnicos menores.
- `VALIDATION_BLOCKED`:
  - cualquier blocker estructural.

## 8. Criterios de readiness por lote

- `VALIDATION_BLOCKED` si existe al menos un archivo bloqueado.
- `VALIDATION_NEEDS_MINOR_ADJUSTMENTS` si no hay bloqueos pero sí ajustes menores pendientes.
- `VALIDATION_READY_WITH_NON_BLOCKING_MANUAL_REVIEW` si hay manual review no bloqueante en uno o más archivos.
- `VALIDATION_READY_FOR_STRICTER_PARSER_DESIGN` si no hay bloqueos ni ajustes menores.

## 9. Criterios para pasar a la siguiente fase

1. Sin `validation_blocker`.
2. Manual review clasificado en su mayoría como no bloqueante o decisión futura.
3. Ajustes menores identificados y acotados.

## 10. Criterios para bloquear avance

1. JSON intermedio inválido o ilegible.
2. Falta de `metadata` o `files`.
3. Falta `~V` o `~C` en archivos clave.
4. Decodificación fallida.
5. Relaciones huerfanas masivas que impiden estructura mínima.

## 11. Criterios para abrir ajuste menor 4.3.1

- Predominio de `minor_adjustment_items` sin bloqueadores estructurales.
- Clasificaciones ambiguas de warning/manual review.
- Necesidad de umbrales más precisos por lote.

## 12. Riesgos

- Umbrales demasiado estrictos pueden bloquear sin necesidad.
- Umbrales laxos pueden ocultar riesgo estructural.
- Variabilidad real BC3 entre lotes puede exigir recalibración.

## 13. Decisiones pendientes

- Umbral definitivo de orfandad de relaciones por tipo de BC3.
- Contrato final de normalización de unidades.
- Criterios finales de interpretación económica.

## 14. Recomendación final

Implementar capa de readiness en `validate_bc3_intermediate.py` con:

- readiness por archivo y global;
- separación de `blocking_items`, `non_blocking_manual_review_items`, `future_human_decisions`, `minor_adjustment_items`;
- recomendación de siguiente fase basada en clasificación, no en nombres de archivo.
