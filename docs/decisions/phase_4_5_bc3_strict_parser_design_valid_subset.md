# Fase 4.5: diseño del parser BC3 estricto sobre subconjunto válido

## 1. Objetivo

Definir documentalmente el diseño de un parser BC3 más estricto, limitado al subconjunto válido de 4 archivos BC3, manteniendo `BC3_02` fuera del flujo principal como no apto.

## 2. Decisión humana de avance

- Decisión explícita: no bloquear el proyecto por `BC3_02`.
- Política aplicada: `BC3_02` permanece en estado `NOT_ELIGIBLE_AUXILIARY_OR_CORRUPT`.
- Consecuencia operativa: el diseño estricto se basa solo en el subconjunto válido (`eligible_files_count=4`).

## 3. Corpus válido usado en esta fase

- Universo evaluado en fase previa: 5 BC3 reales locales.
- Subconjunto válido para diseño estricto: 4 BC3.
- Estado base de entrada: `validation_readiness.global=VALIDATION_READY_WITH_CONTROLLED_EXCLUSIONS`, `valid_subset_status=ADVANCE_ALLOWED`.

## 4. Archivo excluido y motivo

- Archivo excluido: `BC3_02` (ID sanitizado).
- Clasificación: `NOT_ELIGIBLE_AUXILIARY_OR_CORRUPT`.
- Motivo: fallo de decodificación sin estructura útil parseable (`~V`, `~C`, `~D`).
- Tratamiento: referencia técnica únicamente; fuera del flujo principal del parser estricto.

## 5. Alcance del parser estricto

El parser estricto de Fase 4.6 deberá:

- Parsear archivos BC3 del subconjunto válido con reglas más deterministas para `~V`, `~C` y `~D`.
- Endurecer validación de integridad estructural mínima por archivo.
- Emitir errores/warnings/manual review con tipología estable y trazable.
- Conservar salida intermedia separada de cualquier capa de master.
- Preservar la política de exclusión explícita para archivos no aptos.

## 6. Fuera de alcance

- Importación al master.
- Cálculo de ratios.
- Consolidación de importes.
- Normalización final de categorías o unidades.
- Decisiones finales de política económica.
- Reprocesado de `BC3_02` como archivo apto.

## 7. Diferencias frente al parser preliminar

- De heurística amplia a reglas más estrictas sobre registros nucleares (`~V`, `~C`, `~D`).
- Mayor exigencia de completitud de estructura mínima por archivo apto.
- Menor tolerancia a ambigüedad de cabecera/conceptos/relaciones en archivos elegibles.
- Contrato explícito de exclusión: no aptos quedan fuera sin bloquear el avance del subconjunto válido.

## 8. Campos que pasan a ser obligatorios (salida intermedia estricta)

Por archivo apto:

- `file_ref.sanitized_id`
- `file_ref.relative_path`
- `decode.encoding`
- `header.has_v`
- `records.total_records`
- `records.record_type_counts`
- `concepts` (lista no vacía para archivo apto)
- `relations.links` (presente, aunque pueda ser vacía en casos justificados)
- `risk_flags`
- `errors`
- `warnings`
- `manual_review_required`

En resumen de validación:

- `file_eligibility_status`
- `file_eligibility_reason`
- `valid_subset_status`
- `full_corpus_status`
- `excluded_files_count`
- `controlled_exclusions`

## 9. Errores bloqueantes esperados

Para archivos en flujo estricto:

- `MISSING_V_HEADER`
- `CONCEPTS_ABSENT_REVIEW` cuando implique ausencia estructural real
- `ORPHAN_RELATIONS_BLOCKING` cuando supere umbral bloqueante
- `UNKNOWN_RECORDS_PREDOMINANT` cuando la estructura soportada no sea dominante

A nivel de lote:

- bloqueo solo por `BLOCKED_STRUCTURAL_ISSUE` en archivos elegibles o por error global de contrato.
- exclusiones `NOT_ELIGIBLE_AUXILIARY_OR_CORRUPT` se reportan, no bloquean por sí mismas.

## 10. Warnings no bloqueantes esperados

- `RELATION_PARENT_NOT_IN_CONCEPTS`
- `RELATION_CHILD_NOT_IN_CONCEPTS`
- `ENCODING_MEDIUM_CONFIDENCE`
- `MULTIPLE_UNITS_DETECTED`
- `AMBIGUOUS_ECONOMIC_TOKENS`
- `UNKNOWN_RECORD_TYPES_PRESENT` (si no es predominante)

## 11. Manual review esperado

- `MULTIPLE_UNITS_NON_BLOCKING`
- `AMBIGUOUS_ECONOMIC_TOKENS_NON_BLOCKING`
- `RELATION_ORPHAN_CHILD_NON_BLOCKING`
- `UNKNOWN_RECORDS_UNDER_THRESHOLD` / `UNKNOWN_RECORDS_OVER_THRESHOLD`
- decisiones humanas futuras asociadas (`UNITS_POLICY_PENDING`, `ECONOMIC_POLICY_PENDING`)

## 12. Trazabilidad

- Mantener IDs sanitizados por archivo (`BC3_01`, `BC3_03`, `BC3_04`, `BC3_05`) en el subconjunto válido.
- Mantener `BC3_02` explícito en exclusiones controladas.
- Mantener separación entre:
  - parse preliminar/estricto,
  - validación intermedia,
  - decisiones de readiness,
  - futuras fases de normalización y cálculo.

## 13. Criterios de aceptación de diseño (Fase 4.5)

- Documento de diseño estricto aprobado y consistente con Fase 4.4.4.
- Decisión humana de exclusión de `BC3_02` reflejada explícitamente.
- Alcance y fuera de alcance fijados sin ambigüedad.
- Contrato de errores/warnings/manual review definido.
- Restricciones críticas preservadas (sin master, sin ratios, sin consolidación, sin normalización final).

## 14. Riesgos

- Sobrerrestringir reglas y perder tolerancia útil para variantes BC3 válidas.
- Infrarrestringir y reintroducir ambigüedad del parser preliminar.
- Confundir exclusión controlada con ocultación de problemas: mitigado mediante reporte explícito de exclusiones.

## 15. Siguientes pasos

1. Fase 4.6: implementar parser BC3 estricto siguiendo este diseño sobre subconjunto válido.
2. Mantener validación dual de lote completo y subconjunto válido.
3. Conservar `BC3_02` como referencia técnica fuera del flujo principal, sin promoverlo a apto.
