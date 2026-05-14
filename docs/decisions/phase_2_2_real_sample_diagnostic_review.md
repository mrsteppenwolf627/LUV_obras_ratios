# Fase 2.2: Revisión técnica del diagnóstico real

## 1. Propósito

Esta revisión documenta lo aprendido del primer lote real de muestras y propone la siguiente secuencia técnica antes de construir extractores diagnósticos o parsers definitivos.

## 2. Fuentes revisadas

- `reports/sample_inspections/sample_inventory_sanitized.json`
- `reports/sample_inspections/sample_inventory_sanitized_report.md`
- `reports/sample_inspections/file_hashes.json` (duplicados exactos por hash)
- `reports/sample_inspections/sample_inventory.json` solo como reporte local sensible, cuando aplique

Nota de seguridad: los reportes completos pueden contener información sensible y no deben subirse a Git.

## 3. Inventario operativo

- Total de archivos detectados: 7
- Muestras operativas (excluyendo `.gitkeep`): 6
- Archivos ignorados: 1 (`.gitkeep`)
- Conteo por formato operativo:
  - Excel: 1
  - BC3: 2
  - Presto: 2
  - PZH: 1
  - PDF: 0
  - Otros: 0 (operativo)
- Duplicados exactos por hash: 0 grupos

## 4. Observaciones sobre Excel

- Excel detectados: 1
- Hojas detectadas: 3 (`Datos`, `Representación`, `Hoja1`)
- Presencia de Chartsheet: sí (`Representación`)
- Hojas tabulares (WORKSHEET): `Datos`, `Hoja1`
- Dimensiones básicas:
  - `Datos`: 63 x 4
  - `Representación` (CHARTSHEET): sin `max_row`/`max_column` aplicables
  - `Hoja1`: 23 x 3

Implicaciones para futuro extractor Excel:

- No puede asumir que todas las hojas sean tabulares.
- Debe distinguir explícitamente `WORKSHEET` de `CHARTSHEET`.
- Debe detectar hojas candidatas antes de intentar extraer estructuras.
- No debe interpretar ratios en esta etapa.

## 5. Observaciones sobre BC3

- BC3 detectados: 2
- Encoding detectado: `cp1252` en ambos
- Señal de texto: ambos aparecen como `is_text_like = true`
- Señal de versión/estándar: en esta fase queda como observación diagnóstica; no se fija interpretación semántica definitiva

Implicaciones para futuro extractor BC3:

- Debe soportar `cp1252`.
- Debe contemplar variantes de FIEBDC/Presto.
- Debe empezar como extractor diagnóstico, no parser definitivo.
- Debe listar estructura, tipos de registro, capítulos y relaciones antes de cualquier integración con master.
- No debe interpretar importes todavía.

## 6. Observaciones sobre Presto/PZH

- Presto detectados: 2
- PZH detectados: 1
- Estado actual: `NEEDS_FORMAT_RESEARCH`
- Decisión actual: no intentar interpretación en esta fase
- Posible relación: coexistencia con BC3/Excel sugiere pertenencia a los mismos proyectos, pendiente de verificación posterior

Conclusión: Presto/PZH quedan en línea de investigación de formato futura.

## 7. Observaciones sobre duplicados/versiones/fases

- Duplicados exactos: no se detectaron grupos duplicados por hash.
- Señales de versión/fase: existe al menos un archivo con `version_or_phase_hint = true` (`22_10_SCE_Presupuesto final.Presto`).
- No se debe tomar ninguna decisión automática sobre versión válida por nombre de archivo.
- Se mantiene la política vigente de revisión humana para duplicados/versionado.

## 8. Riesgos detectados

- Variabilidad de formatos entre fuentes.
- Excel con hojas no tabulares (chartsheets).
- BC3 en `cp1252` y posible variación de variantes FIEBDC.
- Presto/PZH sin interpretación aún.
- Reportes completos potencialmente sensibles.
- Riesgo de asumir validez por nombre (`final`, `v1`, etc.).
- Necesidad de mantener muestras reales y outputs sensibles fuera de Git.

## 9. Recomendación técnica

Orden recomendado:

1. Extractor diagnóstico BC3.
2. Extractor diagnóstico Excel.
3. Investigación de Presto/PZH.
4. Diseño posterior de parser normalizador.

Justificación: BC3 parece actualmente la fuente más estructurada y prometedora para iniciar extracción diagnóstica, sin convertirla aún en parser definitivo.

## 10. Alcance recomendado para el extractor diagnóstico BC3

El primer extractor BC3 debe:

- Leer archivos BC3 de forma no destructiva.
- Detectar encoding.
- Detectar cabecera y versión FIEBDC.
- Contar registros por tipo.
- Listar códigos de capítulos candidatos.
- Listar relaciones jerárquicas básicas.
- Detectar unidades presentes.
- Detectar importes aparentes sin consolidarlos.
- Generar salidas diagnósticas JSON/Markdown.
- No alimentar master.
- No calcular ratios.
- No decidir categorías definitivas.

## 11. Criterios para pasar a Fase 3

Antes de construir el extractor diagnóstico BC3:

- Revisar y aprobar este documento.
- Confirmar BC3 como primera línea de trabajo.
- Mantener Excel como segunda línea.
- Mantener Presto/PZH como investigación.
- Confirmar que el extractor será diagnóstico, no definitivo.
- Confirmar que no actualizará master.

## 12. Decisiones pendientes

- Superficie base oficial.
- Categorías definitivas.
- Tolerancias.
- IVA/impuestos.
- Moneda.
- Inflación/año.
- Criterios de versión válida.
- Tratamiento de Presto/PZH.
- Parser Excel definitivo.
- Parser BC3 definitivo.
- Estructura física final del master.
