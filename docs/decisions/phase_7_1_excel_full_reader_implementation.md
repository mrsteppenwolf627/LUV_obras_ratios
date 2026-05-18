# Fase 7.1: implementacion del lector integral Excel

## Objetivo

Implementar un lector integral Excel no destructivo, trazable por archivo, hoja y celda, basado en el contrato documental de Fase 7.0.

## Contexto heredado

- Fase 6 y 6.1 demostraron que Excel real presenta variabilidad estructural significativa.
- Fase 7.0 definio el contrato documental para un lector integral y no parcial.
- El sistema debe conservar trazabilidad, no forzar hojas no tabulares y no confundir chartsheets con worksheets.

## Alcance

- Leer workbooks Excel de `data/samples/` de forma recursiva.
- Soportar `.xlsx` y `.xlsm`.
- Ignorar otros formatos no Excel.
- Generar inventario, perfil por workbook y perfil por hoja.
- Preservar trazabilidad por celda.
- Emitir JSON y Markdown locales.

## Fuera de alcance

- Importacion al master.
- Calculo de ratios.
- Consolidacion final de importes.
- Normalizacion final de categorias.
- Alimentar `CATEGORY_MAPPING`.
- Modificar archivos RAW.

## Contrato de salida

El lector implementa, como minimo:

- `reader_metadata`
- `source_files`
- `workbook_summaries`
- `sheets`
- `global_summary`
- `risks`
- `warnings`
- `manual_review`
- `controlled_exclusions`

## Reglas funcionales

- Lectura no destructiva.
- Distincion entre `WORKSHEET` y `CHARTSHEET`.
- Registro explicito de hojas vacias y no tabulares.
- Deteccion de `used_range`, densidad, formulas, comentarios, estilos utiles y celdas combinadas.
- Reutilizacion de heuristicas de cabeceras, columnas candidatas y senales presupuestarias.
- Trazabilidad por celda con valor sanitizado, formula y flags.

## Reglas de sanitizacion

- No volcar contenido sensible extenso.
- Truncar muestras largas.
- Mantener coordenadas y contexto suficiente para auditar.

## Reglas de exclusion controlada

- Archivos no Excel y extensiones no soportadas se registran como excluidos.
- Archivos con error de lectura se registran con error y no rompen el lote.
- Las `CHARTSHEET` se conservan como contexto no tabular.

## Criterios de aceptacion

- JSON y Markdown generados localmente.
- Trazabilidad por archivo, hoja y celda.
- Compatibilidad con chartsheets y hojas vacias.
- No modificacion de RAW.
- Tests sinteticos en verde.

## Riesgos

- Workbook muy grande con alto volumen de celdas no vacias.
- Sobreinterpretacion de estructura visual.
- Ambiguedad de columnas semanticas.
- Mezcla de hojas tabulares y presentacion en un mismo archivo.

## Siguiente paso

Fase 7.2: validar el lector integral Excel sobre corpus real local y decidir si hace falta una capa intermedia de normalizacion por archivo u hoja antes de diseñar el modelo comun multi-formato.

