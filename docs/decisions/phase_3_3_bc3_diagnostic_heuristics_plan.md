# Fase 3.3: plan de ampliacion de heuristicas diagnosticas BC3

## 1. Objetivo

Ampliar el extractor diagnostico BC3 para capturar mas señales estructurales y de riesgo, manteniendo alcance estrictamente diagnostico y sin convertirlo en parser definitivo.

## 2. Motivacion desde Fase 3.2

La revision 3.2 confirma:

- coexistencia de variantes FIEBDC;
- diferencias de tipos de registro entre archivos;
- jerarquias no triviales;
- alta densidad numerica sin semantica consolidada.

Esto justifica ampliar heuristicas antes de pasar a parser preliminar.

## 3. Alcance

- Clasificacion diagnostica de codigos `~C` (capitulo/partida/otro candidato).
- Profundidad jerarquica aproximada a partir de `~D`.
- Estadisticas por tipo de registro (conteo, porcentaje, longitud media, muestras sanitizadas cortas).
- Deteccion diagnostica de campos economicos por tipo sin consolidar.
- Deteccion diagnostica de carga textual por tipo sin extraer contenido extenso.
- Señales de variante FIEBDC y diferencias entre archivos del lote.
- Resumen de warnings para revision humana.

## 4. Fuera de alcance

- Parser BC3 definitivo.
- Importacion al master.
- Calculo de ratios.
- Consolidacion economica.
- Normalizacion final de categorias o unidades.
- Tratamiento de Presto/PZH.

## 5. Heuristicas a ampliar

1. Clasificacion diagnostica de `~C`:
   - `chapter_candidates`;
   - `item_candidates`;
   - `other_candidates`.
2. Jerarquia aproximada:
   - total relaciones;
   - padres unicos;
   - hijos unicos;
   - profundidad maxima aproximada;
   - relaciones incompletas.
3. Estadisticas por tipo:
   - conteo;
   - porcentaje sobre total;
   - longitud media aproximada;
   - muestras cortas sanitizadas.
4. Señales economicas:
   - tokens numericos;
   - tokens tipo importe;
   - presencia por tipo;
   - ambiguedad economica.
5. Señales textuales:
   - longitud media textual por tipo;
   - tipos con mayor carga textual.
6. Señales de variante:
   - version FIEBDC candidata;
   - tipos no comunes;
   - warnings comparativos del lote.
7. Warnings:
   - encoding de confianza media;
   - tipos no comunes;
   - relaciones incompletas;
   - economia ambigua;
   - diversidad de unidades.

## 6. Estructura esperada del JSON actualizado

- `files[].inspection` añade:
  - `c_code_classification`;
  - `hierarchy_summary`;
  - `record_type_stats`;
  - `economic_field_diagnostics`;
  - `text_field_diagnostics`;
  - `fiebdc_variant_signals`;
  - `warnings`.
- nivel global añade:
  - `variant_warnings`.

## 7. Estructura esperada del Markdown actualizado

- Resumen global con warnings de variante.
- Seccion por archivo con:
  - codificacion y version candidata;
  - clasificacion de codigos;
  - resumen jerarquico;
  - estadisticas por tipo;
  - señales economicas y textuales;
  - warnings.

## 8. Criterios de aceptacion

- `scripts/inspect_bc3.py` genera JSON y Markdown con campos nuevos.
- Tests cubren nuevas heuristicas con fixtures sinteticas.
- Persisten restricciones: no parser, no master, no ratios, no consolidacion.
- Ejecucion real sobre `data/samples` completa sin errores destructivos.
- Reports reales siguen fuera de Git.

## 9. Riesgos

- Heuristicas pueden sobregeneralizar entre variantes FIEBDC.
- Posibles falsos positivos en clasificacion de codigos.
- Tokens numericos ambiguos sin contexto semantico.
- Riesgo de exponer metadatos sensibles si se versionan reports reales.

## 10. Decisiones pendientes

- Reglas semanticas definitivas de parser BC3.
- Politica final de codigos y taxonomia.
- Normalizacion final de unidades/importes.
- Estrategia de validacion economica consolidada.
- Criterio formal para salto a parser preliminar.

## 11. Condicion para pasar a Fase 4 o abrir Fase 3.4

- Pasar a Fase 4 (parser preliminar) si:
  - variantes FIEBDC relevantes quedan cubiertas diagnosticamente;
  - jerarquia y tipos principales quedan estables en muestras reales;
  - warnings criticos no bloquean interpretacion base.
- Abrir Fase 3.4 si:
  - persisten diferencias estructurales altas entre BC3;
  - hay ambiguedad critica en codigos/relaciones;
  - aparecen nuevos tipos de registro no cubiertos.
