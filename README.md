# LUV Obras Ratios

Sistema interno para importacion, parsing, validacion estructural y futura normalizacion de presupuestos, con trazabilidad completa desde BC3 fuente hasta capas intermedias.

## Estado actual

- Fase 4 completada como bloque BC3 de parsing/validacion estructural.
- Parser estricto BC3 implementado: `scripts/parse_bc3_strict.py`.
- Validador estricto BC3 implementado: `scripts/validate_bc3_strict.py`.
- Normalizador intermedio BC3 implementado: `scripts/normalize_bc3_intermediate.py`.
- Validador de contrato de normalizacion intermedia implementado: `scripts/validate_bc3_intermediate_normalization.py`.
- Estado consolidado BC3:
  - `validation_readiness.global=VALIDATION_READY_WITH_CONTROLLED_EXCLUSIONS`
  - `full_corpus_status=NOT_BLOCKED`
  - `valid_subset_status=ADVANCE_ALLOWED`
  - `eligible_files_count=4`
  - `excluded_files_count=1`
- Decision humana vigente: `BC3_02` queda excluido del flujo principal como `NOT_ELIGIBLE_AUXILIARY_OR_CORRUPT` y se mantiene solo como referencia tecnica.
- Reorientacion vigente: estrategia multi-formato con prioridad alta en Excel y Presto/PZH; BC3 queda como modulo disponible, no como unica prioridad.

## Fase actual

- Fase 5.3 iniciada: replanteamiento multi-formato y priorizacion Excel/Presto.
- No se lanza por ahora un endurecimiento adicional de schema BC3.
- Siguiente bloque previsto: diagnostico Excel/Presto antes de extractores definitivos por formato.

## Restricciones criticas activas

- No importar al master.
- No calcular ratios.
- No consolidar importes finales.
- No normalizar categorias finales.
- No UX todavia.
- No modificar RAW.
- No subir muestras reales ni reports reales sensibles.

## Flujo por capas (resumen)

1. Ingesta y preservacion de fuente.
2. Diagnostico por formato (Excel, Presto/PZH, BC3 segun aplique).
3. Parseo/validacion por formato con contratos trazables.
4. Modelo intermedio comun multi-formato.
5. Mapping de categorias y decisiones de negocio (fase posterior).
6. Importacion al master (fase posterior).
7. Calculo de ratios (fase posterior).

## Comandos base

```bash
python scripts/validate_context.py
python scripts/inspect_repo.py
pytest
```
