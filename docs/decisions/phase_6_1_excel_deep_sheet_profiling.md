# Fase 6.1: perfilado profundo de hojas Excel reales

## Objetivo

Ampliar el diagnostico Excel para perfilar en profundidad hojas `WORKSHEET` reales y explicar la ausencia inicial de tablas/cabeceras/columnas candidatas observada en Fase 6.

## Contexto heredado

- Fase 6 detecto 3 Excel y 7 hojas totales.
- Se detectaron formulas y chartsheets, pero no cabeceras/columnas candidatas con heuristica basica.
- Se requiere diagnostico mas granular antes de implementar extractor/normalizador Excel de Fase 7.

## Alcance tecnico de Fase 6.1

1. Rango usado real por hoja:
- `min_row`, `max_row`, `min_column`, `max_column`.
- filas/columnas no vacias.

2. Perfil de densidad:
- celdas no vacias / celdas del rango usado.
- filas mas densas.
- columnas mas densas.

3. Cabeceras con heuristica ampliada:
- texto + palabras clave (codigo, cod, partida, descripcion, unidad, ud, cantidad, medicion, precio, importe, total, presupuesto).
- variantes de mayusculas/minusculas y acentos.
- candidatos en varias filas.

4. Columnas candidatas sin cabecera clara:
- patrones por tipo de dato (texto, numerico, formula, unidad, importe aparente).
- inferencia prudente por comportamiento de columna, no por normalizacion final.

5. Estructura visual:
- celdas combinadas.
- formulas.
- filas/columnas ocultas (si aplica).
- anchos de columna de muestra.
- relacion formato vs datos (hojas con mucho estilo y pocos datos).

6. Muestras sanitizadas:
- primeras filas no vacias.
- filas densas.
- posibles filas de cabecera.
- truncado defensivo y sin volcado extenso sensible.

## Salidas

- `reports/excel_diagnostics/excel_diagnostics_inventory.json`
- `reports/excel_diagnostics/excel_diagnostics_inventory_report.md`

## Riesgos y lectura esperada

- Estructuras reales con cabecera desplazada o multi-fila.
- Hojas tabulares con etiquetas poco estandarizadas.
- Dependencia de formulas y formatos visuales como senal estructural.
- Mezcla de hojas tecnicas/tabulares y hojas de presentacion.

## Restricciones activas

- No master.
- No ratios.
- No consolidacion final.
- No normalizacion final.
- No modificar RAW.
- No subir muestras ni reports reales.

## Criterio de salida de Fase 6.1

- Heuristica de perfilado profundo disponible y validada por tests sinteticos.
- Evidencia diagnostica adicional para definir reglas de extractor/normalizador en Fase 7.
