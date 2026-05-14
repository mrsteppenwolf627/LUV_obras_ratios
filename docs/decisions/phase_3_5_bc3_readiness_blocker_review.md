# Fase 3.5: cierre de readiness BC3 y revision de bloqueadores manuales

## 1. Objetivo

Cerrar el diagnostico BC3 identificando por que el readiness no avanzaba a Fase 4 y separar de forma explicita:

- riesgos asumibles para diseno preliminar;
- riesgos que requieren ajuste diagnostico menor;
- riesgos que requieren decision humana;
- riesgos que bloquean realmente el paso.

## 2. Contexto desde Fase 3.4

Fase 3.4 introdujo sanitizacion reforzada, matriz de riesgos por archivo, comparativa y estado global de readiness. El lote real analizado contiene 2 BC3 sanitizados (`BC3_01`, `BC3_02`) con variantes FIEBDC distintas y diferencias de tipos de registro.

## 3. Readiness obtenido antes del ajuste 3.5

- Estado: `NEEDS_MORE_DIAGNOSTIC_HEURISTICS`
- Bloqueador reportado: `MANUAL_REVIEW_REQUIRED`
- Severidades globales: `WARNING` + `MANUAL_REVIEW_REQUIRED`

Motivo observado: la logica trataba parte de la variabilidad de tipos de registro entre variantes como posible bloqueo manual en lugar de warning no bloqueante.

## 4. Bloqueadores detectados

### 4.1 Bloqueadores reales (estructurales)

- `DECODE_OR_READ_BLOCKED`
- `MISSING_V_HEADER`
- `INCOMPLETE_RELATIONS`

### 4.2 Riesgos no bloqueantes (diagnosticos)

- `ENCODING_MEDIUM_CONFIDENCE`
- `VARIANT_RECORD_TYPES_DIFFERENCE`
- `AMBIGUOUS_ECONOMIC_TOKENS`
- `MULTIPLE_UNITS`
- `NO_D_RELATIONS` (warning de cobertura; no bloqueo automatico)

## 5. Tabla de riesgos (sanitizada)

| ID | Severidad | Tipo | Estado 3.5 | Nota |
|---|---|---|---|---|
| DECODE_OR_READ_BLOCKED | BLOCKED | parser_design_blocker | Bloqueante | Impide lectura/decodificacion usable |
| MISSING_V_HEADER | ERROR | parser_design_blocker | Bloqueante | Falta cabecera minima para contrato preliminar |
| INCOMPLETE_RELATIONS | MANUAL_REVIEW_REQUIRED | parser_design_blocker | Bloqueante condicional | Requiere revisar estructura jerarquica |
| ENCODING_MEDIUM_CONFIDENCE | WARNING | diagnostic_warning | Asumible | Esperable en cp1252; no invalida inspeccion |
| VARIANT_RECORD_TYPES_DIFFERENCE | WARNING | diagnostic_warning | Asumible con control | Variabilidad normal entre variantes FIEBDC |
| AMBIGUOUS_ECONOMIC_TOKENS | WARNING | diagnostic_warning | Ajuste menor | Sirve de alerta, no decide precio ni importes |
| MULTIPLE_UNITS | INFO/WARNING | diagnostic_warning | Decision humana posterior | Normalizacion de unidades queda fuera de Fase 3 |

## 6. Tabla de warnings observados en lote real

| Archivo sanitizado | Warnings | Clasificacion |
|---|---|---|
| BC3_01 | ENCODING_MEDIUM_CONFIDENCE, VARIANT_RECORD_TYPES_DIFFERENCE, AMBIGUOUS_ECONOMIC_TOKENS, MULTIPLE_UNITS | No bloqueante |
| BC3_02 | ENCODING_MEDIUM_CONFIDENCE, AMBIGUOUS_ECONOMIC_TOKENS, MULTIPLE_UNITS | No bloqueante |

No se observaron en el lote real actual: `DECODE_OR_READ_BLOCKED`, `MISSING_V_HEADER`, `INCOMPLETE_RELATIONS`.

## 7. Clasificacion final por categoria

### 7.1 Asumible para parser preliminar

- Encoding `cp1252` con confianza media, cuando la lectura diagnostica es estable.
- Variabilidad de tipos de registro compatible con variantes FIEBDC (`~G/~L/~X` en un archivo y ausencia en otro).

### 7.2 Requiere ajuste menor del diagnostico

- Explicar explicitamente warnings no bloqueantes en `readiness_summary`.
- Separar `diagnostic_warning` de `parser_design_blocker`.

### 7.3 Requiere decision humana

- Politica definitiva de normalizacion de unidades.
- Politica final de interpretacion economica (fuera de fase diagnostica).

### 7.4 Bloquea Fase 4

- Fallo de lectura/decodificacion.
- Ausencia de cabecera `~V`.
- Relaciones incompletas relevantes en estructura jerarquica.

## 8. Analisis de severidad del readiness

Conclusion: la logica previa era **demasiado estricta** para el caso de variabilidad normal entre variantes FIEBDC. En 3.5 se ajusta para que solo riesgos tipados como `parser_design_blocker` frenen el readiness.

## 9. Criterios minimos para pasar a Fase 4

1. Sin `DECODE_OR_READ_BLOCKED`.
2. Sin `MISSING_V_HEADER`.
3. Sin `INCOMPLETE_RELATIONS` relevantes.
4. Readiness global en `READY_FOR_PRELIMINARY_PARSER_DESIGN`.
5. Mantener limites: sin parser definitivo, sin master, sin ratios.

## 10. Criterios para bloquear Fase 4

1. Cualquier `BLOCKED` por lectura/decodificacion.
2. `ERROR` estructural en cabecera o formato minimo.
3. `MANUAL_REVIEW_REQUIRED` por estructura jerarquica inconsistente.

## 11. Recomendacion final

**Recomendacion:** pasar a Fase 4 (diseno de parser BC3 preliminar) con alcance acotado, porque tras el ajuste menor de 3.5 los riesgos activos del lote real quedan clasificados como no bloqueantes para diseno preliminar.

Condiciones:

- mantener la separacion estricta entre diagnostico y parser definitivo;
- no importar al master;
- no calcular ratios;
- mantener reports reales fuera de Git.
