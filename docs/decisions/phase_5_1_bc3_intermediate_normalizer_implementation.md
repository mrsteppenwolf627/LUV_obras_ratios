# Fase 5.1: implementacion inicial del normalizador intermedio BC3

## Objetivo

Implementar `scripts/normalize_bc3_intermediate.py` para transformar la salida estricta BC3 en una estructura intermedia normalizada, trazable y util para fases posteriores de validacion/mapping, sin importar al master.

## Entrada

- Principal: `reports/bc3_strict_parse/bc3_strict_parse_inventory.json`
- Complementaria: `reports/bc3_strict_validation/bc3_strict_validation_report.json` (si existe)

## Salida

- JSON: `reports/bc3_intermediate_normalization/bc3_intermediate_normalization_report.json`
- Markdown: `reports/bc3_intermediate_normalization/bc3_intermediate_normalization_report.md`

## Alcance implementado

- Normalizacion por archivo elegible con entidades intermedias:
  - `chapters`
  - `cost_items`
  - `relations`
  - `units`
  - `descriptions`
  - `measurement_signals`
  - `economic_signals`
  - `validation_flags`
  - `manual_review`
  - `unknown_or_unsupported`
  - `source_trace`
- Preservacion de `controlled_exclusions`.
- Preservacion de estados de corpus (`full_corpus_status`, `valid_subset_status`).

## Reglas aplicadas

1. No destructivo sobre input.
2. Trazabilidad por `sanitized_id`, `relative_path`, linea y origen de registro cuando aplique.
3. Separacion de candidatos:
   - `chapters` para codigos con sufijo `#`;
   - `cost_items` para el resto.
4. Relaciones `~D` preservadas sin inferencia adicional.
5. Unidades preservadas como set observado, sin normalizacion final.
6. Descripciones preservadas con truncado defensivo para reporte intermedio.
7. Senales de medicion/economicas extraidas como tokens, sin consolidacion de magnitudes/importes.
8. `unknown`/`unsupported` preservados.
9. `manual_review` preservado y enriquecido con salida de validacion estricta cuando esta disponible.

## Fuera de alcance

- Importacion al master.
- Calculo de ratios.
- Consolidacion de importes finales.
- Normalizacion final de categorias.
- Alimentar `CATEGORY_MAPPING`.

## Riesgos y limites conocidos

- Extraccion de senales economicas/medicion es intencionalmente conservadora en esta fase.
- Clasificacion `chapter`/`cost_item` por sufijo de codigo es heuristica intermedia, no taxonomia final.
- Casos ambiguos permanecen para revision humana y/o fases posteriores.

## Validacion de fase

- Tests sinteticos especificos del normalizador.
- Ejecucion integrada con `parse_bc3_strict` y `validate_bc3_strict` antes de `normalize_bc3_intermediate`.
- Politica de seguridad: sin subida de reports reales ni muestras.

## Siguiente paso recomendado (Fase 5.2)

- Implementar validador de contrato de la estructura intermedia normalizada (schema + reglas minimas de coherencia por entidad), manteniendo las mismas restricciones de ADR-015.
