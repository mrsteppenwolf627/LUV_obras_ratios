# Fase 4.4.1: análisis acotado de BC3 bloqueados del corpus ampliado

## 1. Objetivo

Analizar de forma acotada los BC3 bloqueados detectados en Fase 4.4 para clasificar su naturaleza y proponer la siguiente acción mínima, sin ampliar de forma general el parser preliminar.

## 2. Contexto heredado de Fase 4.4

- Corpus local ampliado evaluado: 24 archivos totales en `data/samples/`.
- BC3 detectados y analizados: 5.
- Resultado de readiness por archivo:
  - 3 en `VALIDATION_READY_WITH_NON_BLOCKING_MANUAL_REVIEW`.
  - 2 en `VALIDATION_BLOCKED`.
- Resultado global: `validation_metadata.status=ERROR` y `validation_readiness.global=VALIDATION_BLOCKED`.
- Bloqueadores observados en el lote: `MISSING_V_HEADER`, `CONCEPTS_ABSENT_REVIEW`, `ORPHAN_RELATIONS_BLOCKING`.

## 3. Resumen del corpus para esta fase

- BC3 bloqueados a analizar: 2.
- Identificadores sanitizados: `BC3_02` y `BC3_03`.
- Fuente de análisis: reportes locales existentes de parse preliminar y validación intermedia.

## 4. Tabla sanitizada de archivos bloqueados

| ID sanitizado | Parse status | Validation status | Readiness | Bloqueadores principales |
|---|---|---|---|---|
| BC3_02 | Error de decodificación preliminar | ERROR | VALIDATION_BLOCKED | MISSING_V_HEADER, CONCEPTS_ABSENT_REVIEW |
| BC3_03 | Parse preliminar completado | ERROR | VALIDATION_BLOCKED | ORPHAN_RELATIONS_BLOCKING |

## 5. Análisis por archivo bloqueado

### 5.1 BC3_02

1. Estado de parse:
- El parser preliminar devuelve error de decodificación (`Could not decode file using utf-8 or cp1252.`).
- `header.has_v=false` en salida parseada.

2. Estado de validación:
- `validation_status=ERROR`.
- `validation_readiness=VALIDATION_BLOCKED`.
- Bloqueadores reportados por el validador: `MISSING_V_HEADER` y `CONCEPTS_ABSENT_REVIEW`.

3. Evidencia estructural:
- `~V`: no detectado en parse (coherente con fallo de decodificación).
- `~C`: no detectados.
- `~D`: no detectados.

4. Diagnóstico técnico acotado:
- La causa primaria observada es fallo de lectura/decodificación en parser preliminar.
- El bloqueo reportado como `MISSING_V_HEADER` / `CONCEPTS_ABSENT_REVIEW` parece derivado de ausencia total de estructura parseada tras ese fallo.

5. Naturaleza probable del archivo:
- Candidato a archivo auxiliar, exportación no BC3 legible o contenido corrupto bajo extensión `.bc3`.
- No hay evidencia suficiente para considerarlo presupuesto BC3 parseable en el estado actual.

6. Clasificación recomendada:
- `excluir del flujo principal` (hasta tipificar explícitamente la clase de fallo).
- `mantener como referencia` para robustez diagnóstica.
- Posible ajuste menor futuro: tipificar `DECODE_FAILED` como bloqueador explícito de validación para mayor precisión semántica.

### 5.2 BC3_03

1. Estado de parse:
- Parse preliminar completado.
- `header.has_v=true` y registro `~V` detectado.
- `~C` detectados (517 conceptos).
- `~D` detectados (52 relaciones).

2. Estado de validación:
- `validation_status=ERROR`.
- `validation_readiness=VALIDATION_BLOCKED`.
- Bloqueador principal: `ORPHAN_RELATIONS_BLOCKING` con `37/52` (ratio `0.71`).

3. Evidencia estructural:
- `~V`: presente.
- `~C`: presentes.
- `~D`: presentes.
- Orfandad de relaciones: masiva en términos del umbral vigente (`>=15` y `>=0.40`).

4. Diagnóstico técnico acotado:
- No apunta a ausencia de estructura mínima (sí hay cabecera y conceptos).
- El bloqueo proviene de inconsistencia estructural fuerte entre relaciones y conceptos parseados.

5. Naturaleza probable del archivo:
- BC3 presupuestario con variante estructural no totalmente cubierta por heurística preliminar de códigos o relaciones.
- Alternativamente, estructura incompleta real de origen; requiere inspección acotada adicional para discriminar entre ambos casos.

6. Clasificación recomendada:
- `crear fixture sintética de regresión` (patrón de relaciones con alta orfandad).
- `ajustar parser` solo si se confirma un patrón mínimo y reproducible de tokenización/códigos en `~D` o `~C`.
- Mantener bloqueado para avance global mientras persista la orfandad masiva.

## 6. Hipótesis técnica consolidada

1. `BC3_02` no bloquea por una variante BC3 menor sino por falta de decodificación útil; se comporta como archivo no apto para flujo principal en esta fase.
2. `BC3_03` sí es BC3 estructurado, pero presenta ruptura significativa entre árbol de relaciones y universo de conceptos parseados.
3. El estado global bloqueado está justificado con el contrato vigente de readiness.

## 7. Clasificación del bloqueo (por tipología solicitada)

- Tipo 1 (archivo no válido/no presupuestario): aplicable a `BC3_02` como hipótesis principal.
- Tipo 2 (variante BC3/FIEBDC no cubierta): posible en `BC3_03`, pendiente de confirmación mínima.
- Tipo 3 (fallo de detección parser preliminar): plausible en `BC3_02` (detección condicionada por decodificación fallida).
- Tipo 4 (ausencia real de cabecera/conceptos): no concluyente en `BC3_02` por imposibilidad de parseo; no aplica a `BC3_03`.
- Tipo 5 (relaciones huérfanas estructuralmente bloqueantes): confirmado en `BC3_03`.
- Tipo 6 (archivo auxiliar/referencia): probable para `BC3_02` hasta clasificación final.

## 8. Riesgos

- Tratar `BC3_02` como presupuesto principal puede contaminar métricas de robustez del parser preliminar.
- Relajar umbral de orfandad para `BC3_03` sin evidencia técnica puede ocultar incoherencia estructural real.
- Ajustes amplios en parser en esta fase romperían la restricción de alcance acotado.

## 9. Decisiones pendientes

1. Confirmar política explícita para archivos `.bc3` no decodificables en flujo principal (exclusión vs cola de revisión técnica).
2. Definir si `DECODE_FAILED` debe emerger como código bloqueante explícito en validador intermedio.
3. Diseñar fixture sintética mínima que reproduzca patrón de orfandad masiva sin usar datos reales.

## 10. Recomendación final

- No avanzar con lote completo a parser más estricto.
- Operar con subconjunto válido (`3/5` BC3 en readiness no bloqueante) para pruebas de robustez incremental.
- Abrir ajuste menor posterior, acotado, con dos frentes:
  1. Clasificación explícita de archivos no decodificables/no aptos.
  2. Regresión sintética para orfandad masiva y revisión mínima de detección de relaciones/conceptos.
