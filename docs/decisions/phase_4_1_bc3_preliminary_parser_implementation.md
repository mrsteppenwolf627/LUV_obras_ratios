# Fase 4.1: implementacion del parser BC3 preliminar

## 1. Objetivo

Implementar un parser BC3 preliminar que produzca estructura intermedia trazable, sin alimentar el master y sin invadir fases de validacion, normalizacion o calculo de ratios.

## 2. Alcance

- Script `scripts/parse_bc3_preliminary.py`.
- Soporte preliminar para `~V`, `~C`, `~D`, `~K`, `~M`, `~T`.
- Mantenimiento de registros no soportados en `unknown_record_types` y `unsupported_records`.
- Salida JSON y Markdown en `reports/bc3_preliminary_parse/`.

## 3. Fuera de alcance

- Parser definitivo BC3.
- Importacion al master.
- Calculo de ratios.
- Consolidacion de importes.
- Normalizacion final de categorias.
- Decisiones de superficie base o tolerancias definitivas.

## 4. Contrato seguido desde Fase 4.0

- Lectura no destructiva.
- Deteccion de encoding alineada con diagnostico (`utf-8`, fallback `cp1252`).
- Separacion entre parseado, ambiguedades y unknowns.
- Estructura intermedia con trazabilidad por archivo/linea/registro.
- Errores, warnings y manual review explicitos.

## 5. Estructura de salida implementada

- `metadata`: fecha UTC, version parser, politica de seguridad y alcance.
- `files[]`: por cada BC3:
  - `file_ref`: id sanitizado, ruta relativa, extension, tamano.
  - `decode`: encoding, confianza, estrategia.
  - `header`: presencia de `~V`, linea de cabecera, version FIEBDC candidata.
  - `records`: conteos por tipo, `supported_record_types`, `unknown_record_types`.
  - `concepts`: conceptos preliminares de `~C`.
  - `relations`: relaciones preliminares de `~D` + incompletas.
  - `units`: unidades detectadas.
  - `economic_signals`: tokens numericos y de importe en modo diagnostico.
  - `raw_records`: muestra truncada de registros parseados.
  - `unsupported_records`: registros no soportados conservados como contexto.
  - `risk_flags`, `errors`, `warnings`, `manual_review_required`.
- `global_summary`: conteos globales de archivos, estados y riesgos.

## 6. Limitaciones conocidas

- Parseo semantico parcial, no definitivo.
- Clasificacion `~C` heuristica.
- Relaciones `~D` sin validacion estructural completa de dominio.
- Tokens economicos no se consolidan ni se interpretan como precio final.

## 7. Criterios de aceptacion

1. Script ejecutable y no destructivo.
2. JSON y Markdown generados correctamente.
3. Trazabilidad por archivo/linea/registro disponible.
4. Unknowns y registros soportados/no soportados separados.
5. Sin importacion al master, sin ratios y sin consolidacion.
6. Tests sinteticos de cobertura minima en verde.

## 8. Riesgos

- Variabilidad real de variantes FIEBDC.
- Ambiguedad de codigos y unidades.
- Riesgo de sobreinterpretacion economica fuera de alcance.
- Riesgo de exponer datos sensibles en outputs reales si se versionan.

## 9. Siguientes pasos

1. Ejecutar parser preliminar sobre muestras locales bajo control.
2. Revisar outputs sanitizados y riesgos.
3. Definir Fase 4.2 para robustecer contrato de parsing preliminar antes de parser definitivo.
