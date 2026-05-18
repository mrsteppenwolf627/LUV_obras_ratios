# Fase 5.2: contrato de validacion de normalizacion intermedia BC3

## Objetivo

Definir e implementar un validador de contrato para la salida de `scripts/normalize_bc3_intermediate.py`, asegurando estructura minima, trazabilidad y coherencia basica antes de cualquier mapping de categorias, importacion al master o calculo de ratios.

## Contexto de entrada

- Fase 4 cerrada tecnicamente con parser y validador estrictos.
- Fase 5.1 implementada con `scripts/normalize_bc3_intermediate.py`.
- Subconjunto valido habilitado para avance controlado.
- Exclusiones controladas preservadas explicitamente.

## Restricciones congeladas

- No importar al master.
- No calcular ratios.
- No consolidar importes finales.
- No normalizar categorias finales.
- No alimentar `CATEGORY_MAPPING`.
- No modificar RAW.

## Contrato a validar

### Raiz obligatoria

- `normalization_metadata`
- `source_reports`
- `corpus_status`
- `files`
- `global_summary`
- `controlled_exclusions`

### Por archivo elegible

- `file_ref`
- `source_trace`
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

### Coherencia minima

1. `source_trace` existe y no es vacio.
2. `chapters` y `cost_items` son listas.
3. Las relaciones preservan trazabilidad minima (`line_number` o equivalente de origen).
4. Unidades observadas, sin marca de normalizacion final.
5. Senales economicas preservadas sin consolidacion final.
6. Senales de medicion preservadas sin consolidacion final.
7. `manual_review` preservado.
8. `controlled_exclusions` preservado.
9. No aparecen campos de master.
10. No aparecen campos de ratios calculados.
11. No aparece consolidacion final de importes.
12. No aparecen categorias finales asignadas.
13. No se alimenta `CATEGORY_MAPPING`.

## Severidades

- `INFO`
- `WARNING`
- `ERROR`
- `MANUAL_REVIEW_REQUIRED`
- `BLOCKED`

## Salidas del validador

- JSON en `reports/bc3_intermediate_normalization_validation/` con:
  - `validation_metadata`
  - `source_normalization_report`
  - `corpus_status`
  - `files`
  - `global_validation_summary`
  - `blocking_errors`
  - `manual_review_items`
  - `warnings`
  - `info`
- Markdown en la misma carpeta con resumen de contrato, bloqueos, manual review, warnings y tabla por archivo.

## Decision de fase

Se implementa un validador dedicado de contrato para desacoplar la validez estructural intermedia de las futuras decisiones de negocio (mapping, master, ratios), manteniendo control de alcance y trazabilidad segun ADR-015.

## Riesgos

- Falsos positivos por contratos demasiado estrictos en esta fase temprana.
- Falsos negativos si no se validan invariantes anti-master/anti-ratios.

## Mitigacion

- Tests sinteticos por invariantes clave.
- Separacion explicita de severidades.
- Recomendaciones de salida para ajustes menores sin forzar integraciones.

## Siguiente paso previsto (Fase 5.3)

Usar este validador como gate previo para endurecer esquema intermedio por entidad (sin mapping final) y preparar contrato de pre-mapping controlado.
