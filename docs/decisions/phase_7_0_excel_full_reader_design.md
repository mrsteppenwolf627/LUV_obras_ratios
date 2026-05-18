# Fase 7.0: diseno documental del lector integral Excel

## 1. Objetivo

Definir documentalmente el contrato de un lector integral Excel capaz de leer, perfilar y describir workbooks completos de forma trazable, segura y no destructiva antes de cualquier normalizacion, importacion al master o calculo de ratios.

## 2. Contexto heredado de Fase 6 y 6.1

- Fase 6 identifico 3 archivos Excel reales, 7 hojas totales, 2 chartsheets y presencia de formulas.
- Fase 6.1 amplio el perfilado y encontro 5/5 worksheets con used_range util, candidate_header_rows y candidate_columns.
- La evidencia real confirma que Excel requiere un lector integral, no un extractor parcial basado en supuestos de cabecera plana.

## 3. Por que Excel es formato prioritario

- Es uno de los formatos mas frecuentes en la operativa real.
- La variabilidad estructural es alta y requiere lectura defensiva.
- Las hojas pueden mezclar datos, presentacion, formulas, tablas y contexto humano.
- Un lector completo reduce el riesgo de normalizar de forma prematura o perder trazabilidad.

## 4. Alcance del lector integral Excel

El lector debe:

- Inventariar archivos Excel soportados.
- Diferenciar hojas `WORKSHEET`, `CHARTSHEET` y hojas no tabulares.
- Detectar rangos usados, densidad, formulas, celdas combinadas, comentarios, estilos utiles y bloques tabulares.
- Identificar cabeceras y columnas candidatas sin forzar interpretaciones finales.
- Preservar trazabilidad por archivo, hoja, fila, columna y coordenada.
- Producir salida apta para validacion y normalizacion posterior, pero sin ejecutar esas capas.

## 5. Fuera de alcance

- Importacion al master.
- Calculo de ratios.
- Consolidacion final de importes.
- Normalizacion final de categorias.
- Alimentar `CATEGORY_MAPPING`.
- Modificar archivos RAW.
- Reescritura de formulas o valores originales.

## 6. Tipos de archivo soportados inicialmente

- `.xlsx`
- `.xlsm`

Tratamiento explicito:

- `.xls` y `.xlsb` deben quedar como legacy/no soportados o referencia tecnica, segun contrato.
- Otras extensiones deben registrarse como no aptas sin romper el lote.

## 7. Tratamiento de `WORKSHEET`

Para cada hoja tabular:

- Calcular dimensiones y `used_range`.
- Detectar filas y columnas no vacias.
- Detectar bloques tabulares candidatos.
- Identificar cabeceras candidatas.
- Identificar columnas candidatas.
- Registrar formulas, comentarios, estilos y celdas combinadas.
- Generar muestras sanitizadas de filas y bloques relevantes.

## 8. Tratamiento de `CHARTSHEET`

Las `CHARTSHEET` no deben tratarse como `WORKSHEET`.

- Deben registrarse como contexto del workbook.
- Deben quedar marcadas como no tabulares.
- Deben alimentar `manual_review` o `warnings` si aportan senal de estructura no tabular.

## 9. Tratamiento de hojas vacias

- Deben conservarse en el inventario.
- No deben forzarse a tabla.
- Deben generar `manual_review` o warning de hoja vacia, no error automatica salvo contrato explicito.

## 10. Tratamiento de hojas visuales o no tabulares

- Deben mantenerse como contexto.
- No deben forzarse a estructura tabular.
- Deben registrarse como hojas no tabulares con trazabilidad y muestras sanitizadas limitadas.

## 11. Tratamiento de formulas

- Deben registrarse como senal estructural.
- Debe conservarse la coordenada y el valor de formula.
- Si existen valores cacheados, pueden registrarse como informacion auxiliar, sin sustituir la formula.

## 12. Tratamiento de valores cacheados

- Si el archivo expone valor cacheado, puede registrarse como senal auxiliar.
- El valor cacheado no sustituye al valor original de formula.
- No debe usarse para consolidacion final ni para ratios en esta fase.

## 13. Tratamiento de celdas combinadas

- Deben preservarse como contexto estructural.
- Deben registrarse con conteo y rango.
- No deben romper la trazabilidad de celda.

## 14. Tratamiento de filas y columnas ocultas

- Deben registrarse si aportan contexto.
- Deben considerarse en el perfil de densidad y riesgo.
- No deben descartarse silenciosamente.

## 15. Tratamiento de estilos utiles

- Los estilos pueden ser una senal auxiliar de estructura.
- Deben registrarse de forma agregada, no como volcado masivo.
- No deben reinterpretarse como contenido de negocio.

## 16. Tratamiento de comentarios

- Deben registrarse si existen.
- Deben mantenerse sanitizados.
- No deben usarse como unica fuente semantica.

## 17. Deteccion de rangos usados

El lector debe detectar:

- `min_row`
- `max_row`
- `min_column`
- `max_column`
- filas no vacias
- columnas no vacias

## 18. Deteccion de bloques tabulares

- Debe detectar bloques candidatos sin asumir un unico bloque por hoja.
- Debe aceptar hojas con multiples bloques o con contexto no tabular.
- Debe conservar incertidumbre en `manual_review`.

## 19. Deteccion de cabeceras candidatas

Debe identificar filas candidatas por:

- texto predominante;
- palabras clave parciales y variantes;
- combinacion de texto y numericos;
- cabeceras multi-fila.

## 20. Deteccion de columnas candidatas

Debe inferir columnas candidatas para:

- codigo;
- descripcion;
- unidad;
- cantidad;
- medicion;
- precio;
- importe;
- total;
- capitulo;
- partida.

## 21. Deteccion de senales presupuestarias

El lector puede identificar senales, no decisiones finales:

- codigo;
- descripcion;
- unidad;
- cantidad;
- medicion;
- precio;
- importe;
- total;
- capitulo;
- partida.

## 22. Estructura JSON propuesta

Salida minima propuesta:

- `reader_metadata`
- `source_files`
- `workbook_summaries`
- `sheets[]`
- `global_summary`
- `risks`
- `warnings`
- `manual_review`
- `controlled_exclusions`

## 23. Estructura Markdown propuesta

Debe incluir:

- resumen global;
- inventario de archivos;
- resumen por workbook;
- resumen por hoja;
- riesgos;
- warnings;
- manual review;
- recomendaciones.

## 24. Reglas de trazabilidad

Cada item relevante debe conservar:

- archivo;
- hoja;
- tipo de hoja;
- fila;
- columna;
- coordenada;
- valor;
- formula;
- tipo de dato.

## 25. Reglas de sanitizacion

- No volcar contenido sensible extenso.
- Truncar muestras largas.
- Omitir valores no necesarios para diagnostico.
- Mantener identificadores de celda y hoja cuando aporten trazabilidad.

## 26. Reglas de `manual_review`

Debe marcar:

- hojas vacias;
- hojas no tabulares;
- chartsheets;
- formulas relevantes;
- bloques ambiguos;
- cabeceras poco claras;
- columnas inciertas.

## 27. Reglas de warnings

Warnings tipicos:

- chartsheets presentes;
- formulas presentes;
- estilos excesivos con baja densidad;
- celdas combinadas relevantes;
- estructuras ocultas.

## 28. Reglas de errores bloqueantes

Solo deben bloquear:

- archivo no legible;
- archivo corrupto;
- extension incompatible en contexto no soportado;
- perdida de trazabilidad basica;
- imposibilidad de generar salida minima.

## 29. Criterios de aceptacion

- Inventario reproducible.
- Trazabilidad por celda y hoja.
- Distincion entre hojas tabulares y no tabulares.
- Salida JSON y Markdown locales.
- Tests sinteticos en verde.
- No modificacion de RAW.

## 30. Riesgos

- Exceso de heuristica en hojas complejas.
- Sobreinterpretacion de formatos visuales.
- Columnas semanticamente ambiguas.
- Tablas partidas en varios bloques.
- Chartsheets confundidas con hojas de datos.

## 31. Decisiones pendientes

- Contrato minimo de tolerancia para hojas no tabulares.
- Umbral de severidad para cabeceras ambiguas.
- Estrategia final para `.xls` y `.xlsb`.
- Profundidad exacta de valores cacheados.
- Relacion futura con normalizacion Excel.

## 32. Plan de implementacion para Fase 7.1

1. Crear el lector integral Excel con salida contractual.
2. Mantener lectura no destructiva y trazabilidad por celda.
3. Producir JSON y Markdown sanitizados.
4. Cubrir con fixtures sinteticas.
5. Validar sobre corpus real sin subir outputs sensibles.
6. Preparar la capa de normalizacion Excel como fase posterior.
