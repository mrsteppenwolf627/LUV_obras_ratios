# Fase 5.0: diseno documental de normalizacion intermedia BC3

## 1. Objetivo

Definir el diseno documental de una capa de normalizacion intermedia BC3 a partir de la salida estricta (`parse_bc3_strict` + `validate_bc3_strict`), sin importar al master ni tomar decisiones economicas finales.

## 2. Contexto heredado de Fase 4

- Fase 4 cerrada tecnicamente como bloque de parsing/validacion estructural BC3.
- Parser estricto implementado y validador estricto implementado.
- Estado de cierre: `validation_readiness.global=VALIDATION_READY_WITH_CONTROLLED_EXCLUSIONS`.
- Estado lote: `full_corpus_status=NOT_BLOCKED`, `valid_subset_status=ADVANCE_ALLOWED`.
- Corpus real analizado: 5 BC3, con 4 elegibles y 1 excluido controladamente.

## 3. Estado del parser estricto

- Script: `scripts/parse_bc3_strict.py`.
- Produce estructura estricta trazable por archivo/linea/registro.
- Separa `parsed`, `unknown`, `unsupported`, `errors`, `warnings`, `manual_review_required`, `controlled_exclusions`.
- Mantiene estados de corpus y subconjunto valido.

## 4. Estado del validador estricto

- Script: `scripts/validate_bc3_strict.py`.
- Valida contrato raiz y coherencia minima `~C/~D`.
- Aplica equivalencia `code/code#`.
- Diferencia manual review no bloqueante vs bloqueo estructural real.
- Conserva exclusiones controladas sin ocultarlas.

## 5. Corpus valido y exclusiones controladas

- Subconjunto valido para trabajo de normalizacion intermedia: 4 BC3.
- Archivo excluido del flujo principal: `BC3_02`.
- Motivo de exclusion: `NOT_ELIGIBLE_AUXILIARY_OR_CORRUPT`.
- Tratamiento de `BC3_02`: referencia tecnica, fuera de procesamiento normalizado principal.

## 6. Alcance de normalizacion intermedia

- Estandarizar una representacion interna intermedia de estructura BC3 valida.
- Mantener trazabilidad completa a origen estricto.
- Preparar datos para fases posteriores de mapping de categorias e importacion.
- Marcar ambiguedades y dependencias de revision humana.

## 7. Fuera de alcance

- Importacion al master.
- Calculo de ratios.
- Consolidacion de importes finales.
- Normalizacion final de categorias.
- Decisiones de superficie base.
- Decisiones de tolerancias definitivas.

## 8. Modelo intermedio propuesto

Modelo documental orientado a entidades con banderas de calidad:

- entidad principal por archivo BC3 elegible;
- colecciones estructuradas por concepto/relacion/senales;
- metadatos de trazabilidad y de estado de validacion;
- capa de excepciones y manual review separada.

## 9. Entidades previstas

- `chapters`
- `cost_items`
- `relations`
- `units`
- `descriptions`
- `measurements_signals`
- `economic_signals`
- `source_trace`
- `validation_flags`
- `manual_review`

## 10. Datos que se pueden estructurar

- Codigos de conceptos y jerarquias basicas.
- Relaciones padre-hijo detectables y trazables.
- Unidades y descripciones cuando existan de forma explicita.
- Senales de medicion/economicas como tokens o campos parciales sin forzar interpretacion final.
- Banderas de calidad y alertas heredadas del validador estricto.

## 11. Datos que deben quedar ambiguos

- Campos economicos con semantica no determinista por variante.
- Unidades con conflicto o multiplicidad no resuelta.
- Textos descriptivos con posible ambiguedad de alcance.
- Relaciones dudosas que no son bloqueo estructural pero requieren criterio de negocio.

## 12. Datos que requieren revision humana futura

- Casos en `manual_review_required` del parse/validador estricto.
- Ambiguedades de unidad con impacto potencial en comparabilidad.
- Senales economicas sin contrato estable entre variantes BC3.
- Excepciones que condicionen `CATEGORY_MAPPING` posterior.

## 13. Relacion futura con CATEGORY_MAPPING

- La normalizacion intermedia prepara datos, no asigna categorias finales.
- `CATEGORY_MAPPING` se ejecutara en fase posterior con reglas explicitas y versionadas.
- La capa intermedia debe exponer suficientes pistas para mapping auditado, sin forzar clasificaciones.

## 14. Relacion futura con master

- El modelo intermedio no escribe en master.
- La importacion al master se habilitara en fase posterior con contrato de aceptacion.
- Solo datos validados y con controles de exclusion/resolucion podran optar a integracion.

## 15. Reglas de trazabilidad

- Conservar `sanitized_id` y `relative_path` de cada archivo.
- Mantener referencia a registro y linea cuando sea posible.
- Preservar origen de cada entidad normalizada (`source_trace`).
- No perder relacion entre flags de validacion y entidad afectada.

## 16. Reglas de exclusion

- Archivos `NOT_ELIGIBLE_AUXILIARY_OR_CORRUPT` no entran al flujo principal.
- Exclusion siempre explicita y reportada.
- Exclusion no implica borrado ni ocultacion del historial.
- Excluidos pueden mantenerse como referencia tecnica fuera de procesamiento principal.

## 17. Riesgos

- Sobre-normalizar ambiguedades y contaminar fases posteriores.
- Infra-normalizar y perder utilidad operativa de la capa intermedia.
- Acoplar prematuramente decisiones de negocio (categorias/master) dentro de normalizacion.
- Tratar exclusiones controladas como invisibles en vez de trazables.

## 18. Decisiones pendientes

- Contrato exacto de schema JSON de normalizacion intermedia.
- Politica de versionado del modelo intermedio.
- Criterios minimos de aceptacion por entidad para fase de mapping.
- Umbrales de calidad para pasar de normalizacion a pre-importacion.

## 19. Criterios para pasar a Fase 5.1

- Diseno documental aprobado y consistente con ADR-015.
- Alcance/fuera de alcance sin ambiguedad.
- Entidades intermedias y trazabilidad definidas.
- Reglas de exclusion y manual review explicitadas.
- Sin cambios que violen restricciones criticas (master/ratios/consolidacion/categorias finales).
