# CONTEXT.md

## Arquitectura

Sistema interno de importación y validación de presupuestos para LUV Studio, orientado a construir un master de ratios económicos con trazabilidad completa.

Arquitectura prevista por capas:

1. Ingesta de fuentes: Excel, BC3/Presto y otros formatos auxiliares.
2. Preservación RAW: almacenamiento inmutable del archivo origen y sus metadatos (incluyendo hash).
3. Normalización: transformación controlada de capítulos, partidas, mediciones e importes a un esquema interno.
4. Validación: reglas matemáticas y de consistencia para aceptar, marcar o excluir datos.
5. Cálculo/Agregación: generación progresiva de ratios únicamente con datos validados.
6. Exportación/Integración: actualización controlada del master y generación de salidas auditables.
7. Interfaz futura: capa de revisión/aprobación manual para cargas y excepciones.

## Objetivo del proyecto

Construir un sistema robusto que alimente progresivamente un master de ratios de obra a partir de presupuestos antiguos, con trazabilidad estricta desde cada ratio final hasta su fuente original, sin invención de datos ni estimaciones no soportadas.

## Herramientas operativas

- ChatGPT: razonamiento central, coordinación metodológica, arquitectura, decisiones estratégicas, mantenimiento conceptual de `CONTEXT.md` y ADRs.
- Codex / Antigravity: backend, parsers, validadores, tests, auditoría técnica, refactors e integraciones.
- Gemini CLI: frontend, UX, prototipado visual e interfaz interna.

## Restricciones críticas

1. No inventar datos.
2. No estimar datos ausentes.
3. No sobrescribir datos brutos.
4. No borrar histórico de importaciones.
5. No actualizar ratios con datos no validados.
6. No usar PDF como fuente automática principal si existe Excel o BC3.
7. Conservar siempre la fuente original.
8. Registrar el hash de cada archivo importado.
9. Registrar logs de importación.
10. Separar dato bruto, dato normalizado, validaciones, cálculos y exportaciones.
11. Cualquier decisión arquitectónica relevante debe documentarse en `ADRs.md`.
12. Cualquier tarea debe reflejarse en `CONTEXT.md`.
13. El sistema debe poder detectar duplicados.
14. El sistema debe poder marcar datos como excluidos sin eliminarlos.
15. Todo cálculo de ratio debe ser auditable desde resultado final hasta dato de origen.

## Estado actual

| Tarea | Estado | Notas |
|---|---|---|
| Fase 2 - Diagnóstico real de muestras | Completado | Base diagnóstica ejecutada sobre `data/samples` sin importación al master |
| Fase 2.1 - Endurecimiento diagnóstico | Completado | Soporte Chartsheet y reportes sanitizados implementados |
| Fase 2.2 - Revisión técnica del diagnóstico real | Completado (documental) | Revisión técnica formal documentada en `docs/decisions/phase_2_2_real_sample_diagnostic_review.md` |
| Fase 3 - Extractor diagnóstico BC3 | Completado (técnico) | Readiness cerrado en Fase 3.5 con estado `READY_FOR_PRELIMINARY_PARSER_DESIGN` |
| Fase 3.1 - Implementación extractor BC3 | Completado (técnico) | Plan, ADR-013, script, tests y validaciones cerradas |
| Fase 3.2 - Revisión diagnóstica BC3 real | Completado (documental) | Revisión cerrada en `docs/decisions/phase_3_2_bc3_diagnostic_review.md` |
| Fase 3.3 - Heurísticas diagnósticas BC3 | Completado (técnico) | Heurísticas ampliadas, validaciones y ejecución real cerradas |
| Fase 3.4 - Iteración diagnóstica final BC3 | Completado (técnico) | Sanitización reforzada, matriz de riesgos, readiness y comparativa BC3 implementadas |
| Fase 3.5 - Cierre de readiness BC3 | Completado (técnico) | Bloqueadores tipados, warnings no bloqueantes explicitados y criterio de paso cerrado |
| Fase 4.0 - Diseño documental parser BC3 preliminar | Completado (documental) | Diseño cerrado en `docs/decisions/phase_4_0_bc3_preliminary_parser_design.md` y ADR-014 |
| Fase 4.1 - Implementación parser BC3 preliminar | Completado (técnico) | Parser preliminar implementado, validado y ejecutado localmente |
| Fase 4.2 - Validación estructura intermedia BC3 | Completado (técnico) | Validador implementado, pruebas en verde y ejecución real con estado `MANUAL_REVIEW_REQUIRED` |
| Fase 4.3 - Readiness de validación BC3 | En curso | Contrato de resolución de manual review y readiness por archivo/lote |
| Fase 1.1 - Inicialización base | Completado | Repositorio, validaciones, commit inicial y push cerrados |
| Fase 1.2 - Diseño preliminar del master | Completado | Documento preliminar creado y ADR-009 propuesta |
| Fase 1.3 - Política de duplicados y versionado | Completado (documental) | Política preliminar creada y ADR-010 propuesta |
| Fase 1.4 - Reglas de validación matemática y consistencia | Completado (documental) | Política preliminar creada y ADR-011 propuesta |
| Fase 1.5 - Revisión humana y congelación parcial | Completado (documental) | Revisión formal creada y ADR-012 propuesta |
| Crear estructura base | Completado | Estructura inicial del repositorio creada |
| Crear CONTEXT.md | Completado | Documento de gobernanza inicial creado |
| Crear ADRs.md | Completado | Decisiones arquitectónicas iniciales documentadas |
| Crear README.md | Completado | Guía inicial del proyecto creada |
| Crear scripts iniciales | Completado | `validate_context.py` e `inspect_repo.py` |
| Revisión humana de diseño preliminar del master | Pendiente | Gate obligatorio antes de Fase 2 |
| Revisión humana de política de duplicados y versionado | Pendiente | Gate obligatorio antes de Fase 2 |
| Revisión humana de reglas de validación | Pendiente | Gate obligatorio antes de Fase 2 |
| Revisión humana de congelación parcial metodológica | Pendiente | Gate obligatorio antes de Fase 2 |
| Analizar Excel de ejemplo | En curso (diagnóstico) | Fase 2: inspección controlada sin importación |
| Analizar BC3 real | En curso (diagnóstico) | Fase 2: inspección superficial sin parser definitivo |
| Definir estructura final del master | En curso | Basado en `docs/decisions/master_schema_preliminar.md` |
| Definir categorías de ratios | Pendiente | No fijar sin evidencia de datos |
| Definir superficie base | Pendiente | Bloqueante para ratios consolidados |
| Crear parser Excel | Pendiente | No iniciar antes de revisión humana Fases 1.2-1.5 |
| Crear parser BC3 | Pendiente | No iniciar antes de revisión humana Fases 1.2-1.5 |
| Crear validador matemático | Pendiente | Reglas tras definición final de master |
| Crear exportador al master | Pendiente | Solo con esquema y validaciones cerradas |
| Crear interfaz | Pendiente | Fase posterior (Gemini CLI) |

## Estado Fase 2 (real samples)

- Muestras detectadas: 7 archivos totales en `data/samples`, de los cuales 6 son muestras operativas y 1 es archivo de soporte ignorado (`.gitkeep`).
- Los reportes completos locales pueden contener información sensible y deben permanecer fuera de Git.
- Los reportes sanitizados son la base para revisión humana de diagnóstico.
- Sigue bloqueado avanzar a parsers definitivos, importación al master o cálculo de ratios.
- Recomendación para Fase 3: iniciar extractor diagnóstico BC3 (sin parser definitivo, sin actualización de master).

## Estado Fase 3 (BC3 diagnóstico)

- Objetivo: construir extractor diagnóstico BC3 no destructivo para entender encoding, cabecera/FIEBDC, tipos de registro, relaciones básicas y riesgos de estructura.
- Objetivo Fase 3.3: ampliar heurísticas diagnósticas BC3 para reducir riesgo antes de diseño de parser preliminar (cerrado técnicamente).
- Objetivo Fase 3.4: iteración diagnóstica final BC3 para reforzar sanitización, clasificación de riesgos y criterio de readiness (cerrado técnicamente).
- Objetivo Fase 3.5: revisar bloqueadores manuales y cerrar readiness BC3 con criterios explícitos de paso/no paso a Fase 4.
- Restricciones activas:
  - No crear parser definitivo.
  - No diseñar todavía parser preliminar salvo recomendación final documentada.
  - No importar al master.
  - No calcular ratios.
  - No normalizar categorías finales.
  - No consolidar importes.
  - No modificar RAW.
- Seguridad de reportes: los reportes completos con datos reales pueden contener información sensible y no deben subirse a Git.

## Estado Fase 4.0 (diseño parser BC3 preliminar)

- Objetivo: definir documentalmente la arquitectura, estructura intermedia, trazabilidad, errores, warnings y criterios de aceptación del parser BC3 preliminar antes de implementarlo.
- Decisión de entrada: Fase 3 cerrada técnicamente con readiness `READY_FOR_PRELIMINARY_PARSER_DESIGN`.
- Restricciones activas:
  - No implementar parser definitivo.
  - No importar al master.
  - No calcular ratios.
  - No consolidar importes finales.
  - No normalizar categorías finales.
  - No modificar RAW.
- Seguridad de reportes: los reports reales completos pueden contener información sensible y deben permanecer fuera de Git.

## Estado Fase 4.1 (implementación parser BC3 preliminar)

- Objetivo: implementar `scripts/parse_bc3_preliminary.py` siguiendo el contrato de Fase 4.0 y ADR-014.
- Alcance: parser preliminar para estructura intermedia, con trazabilidad por archivo/registro/línea.
- Restricciones activas:
  - Parser preliminar, no parser definitivo.
  - Generar estructura intermedia, no master.
  - No importar al master.
  - No calcular ratios.
  - No consolidar importes.
  - No normalizar categorías finales.
  - No modificar RAW.
- Seguridad de outputs: salidas sobre datos reales pueden ser sensibles y no deben subirse a Git.

## Estado Fase 4.2 (validación estructura intermedia BC3)

- Objetivo: validar coherencia estructural y completitud mínima del JSON intermedio generado por `scripts/parse_bc3_preliminary.py`.
- Alcance: separación explícita de `errors`, `warnings`, `manual_review_required` y bloqueos metodológicos.
- Restricciones activas:
  - No importar al master.
  - No calcular ratios.
  - No consolidar importes.
  - No normalizar categorías finales.
  - No modificar RAW.
- Seguridad de outputs: resultados de validación sobre datos reales pueden ser sensibles y no deben subirse a Git.

## Estado Fase 4.3 (readiness de validación BC3)

- Objetivo: distinguir `validation_blocker`, `manual_review` bloqueante/no bloqueante y condiciones mínimas para avanzar con parser más estricto.
- Resultado heredado de Fase 4.2: estado real `MANUAL_REVIEW_REQUIRED` en lote local.
- Restricciones activas:
  - No importar al master.
  - No calcular ratios.
  - No consolidar importes.
  - No normalizar categorías finales.
  - No modificar RAW.
- Seguridad de outputs: reports de validación sobre datos reales pueden ser sensibles y no deben subirse a Git.

## Backlog priorizado

### P0

- Gobernanza documental.
- Definición del master de ratios.
- Definición de reglas de validación.
- Análisis de archivos reales (Excel y BC3/Presto).
- Decisiones formales sobre prioridad de fuentes.
- Definición explícita de superficie base.
- Revisión humana del diseño preliminar del master (gate).
- Revisión humana de política de duplicados y versionado (gate).
- Revisión humana de reglas de validación matemática y consistencia (gate).
- Revisión humana de congelación parcial metodológica (gate).

### P1

- Parser Excel.
- Parser BC3.
- Normalizador de capítulos/partidas.
- Validador matemático y de consistencia.
- Exportador al master.

### P2

- Interfaz de carga y revisión.
- Dashboard de seguimiento de calidad de datos.
- Automatizaciones avanzadas de pipeline.
- Visualización de ratios y evolución histórica.

## Riesgos técnicos

- Alta variabilidad de formatos Excel entre estudios/proyectos.
- Variabilidad estructural de archivos BC3 según origen/versiones.
- Archivos Presto nativos potencialmente no legibles de forma directa.
- Fiabilidad limitada de extracción automática desde PDF/OCR.
- Riesgo de duplicados entre importaciones o versiones del mismo presupuesto.
- Presupuestos por fases con solape parcial de partidas.
- Diferencias entre presupuesto contratado, mediciones y revisiones posteriores.
- Ausencia o inconsistencia de superficie base para normalizar ratios.
- Capítulos sin mapeo claro a taxonomía interna.
- Cambios futuros en categorías de ratios y criterios comparativos.

## Reglas de actualización

- `CONTEXT.md` debe actualizarse después de cada tarea relevante.
- Cada decisión arquitectónica nueva o cambio sustancial debe registrarse en `ADRs.md`.
- El estado y backlog deben reflejar el avance real del repositorio.
- No se deben cerrar tareas sin evidencia verificable (código, tests, o documentación).
- No se puede avanzar a parsers definitivos, importación al master ni cálculo de ratios hasta completar las revisiones humanas pendientes.
- Fase 2 solo puede ejecutarse como análisis diagnóstico de muestras; no permite importación definitiva ni actualización del master.
- En Fase 2, los reportes completos que incluyan contenido potencialmente sensible deben mantenerse fuera de Git; solo se comparte reporte sanitizado.
- Fase 3 BC3 se limita a extracción diagnóstica y no puede alimentar el master ni consolidar importes.



## Estado Fase 4.3.1 (ajuste menor de readiness BC3)

- Objetivo: recalibrar reglas de readiness y umbrales de relaciones/unknown records para distinguir bloqueos estructurales reales de revisi?n manual no bloqueante.
- Restricciones activas:
  - No importar al master.
  - No calcular ratios.
  - No consolidar importes.
  - No normalizar categor?as finales.
  - No modificar RAW.
- Seguridad de outputs: resultados reales pueden ser sensibles y no deben subirse a Git.

## Estado Fase 4.3.2 (cierre de ajustes menores de readiness BC3)

- Fase 4.3.1 implementada técnicamente.
- Estado real heredado al inicio: `validation_metadata.status=WARNING` y `validation_readiness.global=VALIDATION_NEEDS_MINOR_ADJUSTMENTS`.
- Objetivo: cerrar ajustes menores de clasificación/readiness para pasar a estado de avance sin forzar resultados.
- Restricciones activas:
  - No importar al master.
  - No calcular ratios.
  - No consolidar importes.
  - No normalizar categorías finales.
  - No modificar RAW.
  - No subir outputs reales sensibles.

## Estado Fase 4.4 (validación ampliada con corpus BC3 real)

- Fase 4.3.2 cerrada técnicamente.
- Fase 4.4 iniciada para validar robustez y estabilidad sobre corpus BC3 real ampliado.
- Objetivo: evaluar parser preliminar + validador intermedio con mayor variabilidad FIEBDC antes de diseñar parser más estricto.
- Restricciones activas:
  - Solo analizar BC3 en esta fase.
  - Ignorar Excel, PDF, Presto, PrestoBackup, PrestoRecord, PZH y otros formatos no BC3.
  - No importar al master.
  - No calcular ratios.
  - No consolidar importes.
  - No normalizar categorías finales.
  - No modificar RAW.
  - No subir muestras reales.
  - No subir outputs reales sensibles.

## Estado Fase 4.4.1 (análisis acotado de BC3 bloqueados)

- Fase 4.4 ejecutada sobre corpus ampliado local.
- Resultado heredado: estado global bloqueado por 2 BC3 (`validation_readiness.global=VALIDATION_BLOCKED`).
- Fase 4.4.1 iniciada para análisis acotado de archivos bloqueados.
- Objetivo: determinar si los bloqueos provienen de archivo no válido/auxiliar, variante BC3 no cubierta, fallo de detección preliminar o estructura realmente incompleta.
- Restricciones activas:
  - No importar al master.
  - No calcular ratios.
  - No consolidar importes.
  - No normalizar categorías finales.
  - No modificar RAW.
  - No subir muestras reales.
  - No subir outputs reales sensibles.

## Estado Fase 4.4.2 (tipificación de aptitud BC3 y exclusión controlada)

- Fase 4.4.1 cerrada documentalmente.
- Fase 4.4.2 iniciada para tipificar explícitamente aptitud de archivos BC3 y habilitar avance controlado por subconjunto válido.
- Objetivo: distinguir archivos elegibles, elegibles con revisión no bloqueante, no aptos/auxiliares/corruptos y bloqueados estructurales.
- Restricciones activas:
  - No importar al master.
  - No calcular ratios.
  - No consolidar importes.
  - No normalizar categorías finales.
  - No modificar RAW.
  - No subir muestras reales.
  - No subir outputs reales sensibles.

## Estado Fase 4.4.3 (análisis y regresión sintética del bloqueo estructural BC3_03)

- Fase 4.4.2 cerrada técnicamente con tipificación de aptitud por archivo y avance permitido por subconjunto válido.
- Fase 4.4.3 iniciada para analizar de forma acotada el bloqueo estructural de `BC3_03` (`ORPHAN_RELATIONS_BLOCKING`).
- Objetivo: discriminar si el bloqueo proviene de parser preliminar, validador, variante BC3/FIEBDC no cubierta o inconsistencia real de archivo.
- Restricciones activas:
  - No importar al master.
  - No calcular ratios.
  - No consolidar importes.
  - No normalizar categorías finales.
  - No modificar RAW.
  - No subir muestras reales.
  - No subir outputs reales sensibles.

## Estado Fase 4.4.4 (alineación de readiness global con exclusión controlada)

- Fase 4.4.3 cerrada técnicamente.
- BC3_03 desbloqueado tras cubrir equivalencia code/code# en validación.
- Fase 4.4.4 iniciada para alinear readiness global con exclusión controlada de archivos no aptos.
- Objetivo: permitir avance del corpus cuando solo existan exclusiones explícitas NOT_ELIGIBLE_AUXILIARY_OR_CORRUPT y haya subconjunto válido suficiente.
- Restricciones activas:
  - No importar al master.
  - No calcular ratios.
  - No consolidar importes.
  - No normalizar categorías finales.
  - No modificar RAW.
  - No subir muestras reales.
  - No subir outputs reales sensibles.


## Estado Fase 4.5 (diseño parser BC3 estricto sobre subconjunto válido)

- Fase 4.4.4 cerrada técnicamente.
- Decisión humana: no bloquear el proyecto por BC3_02 y avanzar con subconjunto válido.
- BC3_02 queda excluido del flujo principal como NOT_ELIGIBLE_AUXILIARY_OR_CORRUPT y se mantiene solo como referencia técnica.
- Fase 4.5 iniciada para diseñar documentalmente el parser BC3 más estricto sobre 4 BC3 válidos.
- Restricciones activas:
  - No importar al master.
  - No calcular ratios.
  - No consolidar importes.
  - No normalizar categorías finales.
  - No modificar RAW.
  - No subir muestras reales ni reports reales sensibles.


## Estado Fase 4.6 (implementación parser BC3 estricto sobre subconjunto válido)

- Fase 4.5 cerrada documentalmente.
- Fase 4.6 iniciada para implementar `scripts/parse_bc3_strict.py` sobre el subconjunto válido.
- Decisión humana vigente: `BC3_02` permanece excluido del flujo principal como `NOT_ELIGIBLE_AUXILIARY_OR_CORRUPT`.
- Objetivo: parser BC3 estricto con trazabilidad por archivo/línea/registro y exclusión controlada explícita.
- Restricciones activas:
  - No importar al master.
  - No calcular ratios.
  - No consolidar importes.
  - No normalizar categorías finales.
  - No modificar RAW.
  - No subir muestras reales ni outputs/reportes reales sensibles.

## Estado Fase 4.7 (validación cruzada estricta de coherencia ~C/~D)

- Fase 4.6 cerrada técnicamente.
- Fase 4.7 iniciada para implementar validación cruzada estricta mínima sobre salida de parser BC3 estricto.
- Objetivo: validar coherencia entre conceptos `~C` y relaciones `~D` en subconjunto válido, preservando exclusiones controladas.
- Restricciones activas:
  - No importar al master.
  - No calcular ratios.
  - No consolidar importes.
  - No normalizar categorías finales.
  - No modificar RAW.
  - No subir muestras reales ni reports reales sensibles.

## Estado Fase 5.0 (diseno documental de normalizacion intermedia BC3)

- Fase 4 queda cerrada como bloque BC3 de parsing estricto y validacion estructural.
- Fase 4.7 cerrada tecnicamente.
- Decision humana vigente: avanzar a Fase 5 sin seguir bloqueando por `BC3_02`, salvo nueva evidencia estructural.
- `BC3_02` permanece excluido controladamente del flujo principal como `NOT_ELIGIBLE_AUXILIARY_OR_CORRUPT` y se mantiene como referencia tecnica.
- Subconjunto valido actual: 4 BC3 elegibles.
- Fase 5.0 iniciada con objetivo documental: disenar normalizacion intermedia BC3 sobre salida estricta.
- Restricciones activas:
  - No importar al master.
  - No calcular ratios.
  - No consolidar importes finales.
  - No normalizar categorias finales.
  - No modificar RAW.
  - No subir muestras reales ni reports reales sensibles.

## Estado Fase 5.1 (implementacion inicial del normalizador intermedio BC3)

- Fase 4 cerrada documentalmente como bloque BC3 de parsing/validacion estructural.
- Fase 5.0 documentada como diseno de normalizacion intermedia BC3.
- Fase 5.1 iniciada para implementar el primer normalizador intermedio BC3.
- Fase 5 sigue abierta.
- Objetivo: transformar salida estricta BC3 a estructura intermedia normalizada y trazable para validaciones futuras.
- Restricciones activas:
  - No importar al master.
  - No calcular ratios.
  - No consolidacion final de importes.
  - No normalizacion final de categorias.
  - No modificar RAW.
  - No subir samples ni reports reales sensibles.

## Estado Fase 5.2 (validador de contrato de normalizacion intermedia BC3)

- Fase 5.1 cerrada tecnicamente.
- Fase 5.2 iniciada para validar contrato de normalizacion intermedia BC3 antes de mapping o integracion posterior.
- Objetivo: verificar estructura minima, trazabilidad y coherencia basica de la salida de normalizacion intermedia.
- Restricciones activas:
  - No importar al master.
  - No calcular ratios.
  - No consolidacion final de importes.
  - No normalizacion final de categorias.
  - No CATEGORY_MAPPING todavia.
  - No modificar RAW.
  - No subir samples ni reports reales sensibles.

## Estado Fase 5.3 (replanteamiento multi-formato y prioridad Excel/Presto)

- Fase 5.2 cerrada tecnicamente con validador de contrato de normalizacion intermedia BC3 operativo.
- Decision humana vigente: no lanzar endurecimiento adicional BC3 en esta etapa.
- BC3 queda disponible como modulo avanzado (parseo estricto, validacion estricta, normalizacion intermedia y validacion de contrato), pero deja de ser prioridad unica.
- Estrategia activa: enfoque multi-formato con prioridad alta para Excel y Presto/PZH.
- Siguiente bloque recomendado: diagnostico tecnico acotado de Excel y Presto/PZH antes de nuevos extractores/normalizadores por formato.
- Restricciones activas:
  - No importar al master.
  - No calcular ratios.
  - No consolidacion final de importes.
  - No normalizacion final de categorias.
  - No UX todavia.
  - No CATEGORY_MAPPING todavia.
  - No modificar RAW.
  - No subir samples ni reports reales sensibles.

## Estado Fase 6 (diagnostico real Excel)

- Fase 5.3 cerrada documentalmente con estrategia multi-formato activa.
- Fase 6 iniciada para diagnostico real Excel previo a extractor definitivo.
- Objetivo: caracterizar estructura real de workbooks Excel (tipos de hoja, dimensiones, cabeceras, columnas candidatas, tablas, formulas y riesgos) sin integracion a master.
- Restricciones activas:
  - No importar al master.
  - No calcular ratios.
  - No consolidar importes.
  - No normalizar categorias finales.
  - No modificar RAW.
  - No subir muestras reales ni reports sensibles.

## Estado Fase 6.1 (perfilado profundo de hojas Excel reales)

- Fase 6 cerrada tecnicamente con diagnostico Excel operativo.
- Fase 6.1 iniciada para perfilado profundo de hojas `WORKSHEET` reales.
- Objetivo: entender por que no se detectaron tablas/cabeceras/columnas candidatas en Fase 6 y ampliar heuristicas de deteccion estructural.
- Restricciones activas:
  - No importar al master.
  - No calcular ratios.
  - No consolidacion final.
  - No normalizacion final.
  - No modificar RAW.
  - No subir muestras ni reports reales.
