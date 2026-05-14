# Fase 3.4: iteracion diagnostica final BC3

## 1. Objetivo

Robustecer el extractor diagnostico BC3 en sanitizacion, estabilidad y clasificacion de riesgos para decidir con menor incertidumbre si se puede pasar al diseno de parser preliminar (Fase 4), manteniendo alcance estrictamente diagnostico.

## 2. Motivacion desde Fase 3.3

Fase 3.3 amplio cobertura de heuristicas estructurales, pero la revision final requiere:

- reducir riesgo de exposicion de datos sensibles en salidas revisables;
- formalizar severidad de incidencias por archivo;
- incorporar criterio global de readiness basado en riesgos y bloqueadores;
- comparar variabilidad entre archivos BC3 sin depender de nombres reales.

## 3. Alcance

- Reforzar sanitizacion de JSON y Markdown.
- Anadir matriz de riesgos por archivo con severidades estandarizadas.
- Anadir resumen global de readiness del lote BC3.
- Anadir comparativa entre archivos BC3 con identificadores sanitizados.
- Mantener ejecucion no destructiva y salida en `reports/bc3_diagnostics/`.

## 4. Fuera de alcance

- Parser BC3 definitivo.
- Importacion al master.
- Calculo de ratios.
- Consolidacion de importes.
- Normalizacion final de categorias.
- Modificacion de archivos RAW.
- Tratamiento de Presto/PZH.

## 5. Mejoras diagnosticas previstas

1. Sanitizacion reforzada:
- truncado seguro de muestras;
- ocultacion de rutas absolutas;
- limitacion de textos largos y tokens potencialmente sensibles;
- metadata de sensibilidad potencial del reporte.

2. Matriz de riesgos por archivo:
- severidades: `INFO`, `WARNING`, `ERROR`, `MANUAL_REVIEW_REQUIRED`, `BLOCKED`;
- incidencias de encoding, cabecera, relaciones, registros desconocidos, ambiguedad economica y variabilidad de unidades.

3. Readiness global:
- `READY_FOR_PRELIMINARY_PARSER_DESIGN`;
- `NEEDS_MORE_DIAGNOSTIC_HEURISTICS`;
- `BLOCKED_BY_DECODING_OR_STRUCTURE`.

4. Comparativa entre archivos:
- versiones FIEBDC candidatas;
- tipos de registro comunes y exclusivos;
- unidades comunes y exclusivas;
- diferencias de jerarquia, densidad economica y carga textual;
- advertencias de variabilidad.

5. Markdown ejecutivo:
- resumen global;
- readiness;
- matriz de riesgos;
- comparativa;
- hallazgos y limites;
- recomendacion de siguiente fase.

## 6. Criterios de aceptacion

- `scripts/inspect_bc3.py` genera JSON/Markdown con nuevos bloques de sanitizacion, riesgos, readiness y comparativa.
- `tests/scripts/test_inspect_bc3.py` cubre los nuevos comportamientos con fixtures sinteticas.
- Ejecucion sobre BC3 reales locales funciona sin modificar entradas.
- Reports reales permanecen fuera de Git.
- Validaciones de repo y test suite pasan.

## 7. Criterios para pasar a Fase 4

- Sin bloqueadores de decodificacion o estructura critica.
- Cabeceras y tipos principales suficientemente consistentes para diseno preliminar.
- Riesgos remanentes controlados y documentados como no bloqueantes para diseno.
- Aceptacion explicita de que Fase 4 sigue siendo preliminar (no parser definitivo).

## 8. Criterios para abrir Fase 3.5

- Persisten `BLOCKED` en archivos relevantes.
- Persisten `MANUAL_REVIEW_REQUIRED` estructurales severos sin mitigacion.
- Variabilidad de variantes/tipos impide proponer contrato tecnico minimo del parser preliminar.
- Sanitizacion todavia insuficiente para compartir revisiones internas con seguridad.

## 9. Riesgos

- Falsos positivos de sensibilidad por sanitizacion agresiva.
- Falsos negativos de sensibilidad por sanitizacion insuficiente.
- Heuristicas de severidad sobregeneralizadas entre variantes FIEBDC.
- Sobreinterpretacion de senales economicas fuera de contexto semantico.

## 10. Decisiones pendientes

- Contrato final de parser BC3 definitivo.
- Mapeo definitivo de categorias y taxonomia.
- Reglas finales de unidades, moneda e impuestos.
- Politica final de version valida por proyecto.
- Integracion futura con master (fuera de Fase 3).
