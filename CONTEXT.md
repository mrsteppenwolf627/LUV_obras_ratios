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
| Fase 4.1 - Implementación parser BC3 preliminar | En curso | Implementación de estructura intermedia trazable sin importar al master |
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

