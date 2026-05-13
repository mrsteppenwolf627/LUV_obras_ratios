# CONTEXT.md

## Arquitectura

Sistema interno de importacion y validacion de presupuestos para LUV Studio, orientado a construir un master de ratios economicos con trazabilidad completa.

Arquitectura prevista por capas:

1. Ingesta de fuentes: Excel, BC3/Presto y otros formatos auxiliares.
2. Preservacion RAW: almacenamiento inmutable del archivo origen y sus metadatos (incluyendo hash).
3. Normalizacion: transformacion controlada de capitulos, partidas, mediciones e importes a un esquema interno.
4. Validacion: reglas matematicas y de consistencia para aceptar, marcar o excluir datos.
5. Calculo/Agregacion: generacion progresiva de ratios unicamente con datos validados.
6. Exportacion/Integracion: actualizacion controlada del master y generacion de salidas auditables.
7. Interfaz futura: capa de revision/aprobacion manual para cargas y excepciones.

## Objetivo del proyecto

Construir un sistema robusto que alimente progresivamente un master de ratios de obra a partir de presupuestos antiguos, con trazabilidad estricta desde cada ratio final hasta su fuente original, sin invencion de datos ni estimaciones no soportadas.

## Herramientas operativas

- ChatGPT: razonamiento central, coordinacion metodologica, arquitectura, decisiones estrategicas, mantenimiento conceptual de `CONTEXT.md` y ADRs.
- Codex / Antigravity: backend, parsers, validadores, tests, auditoria tecnica, refactors e integraciones.
- Gemini CLI: frontend, UX, prototipado visual e interfaz interna.

## Restricciones críticas

1. No inventar datos.
2. No estimar datos ausentes.
3. No sobrescribir datos brutos.
4. No borrar historico de importaciones.
5. No actualizar ratios con datos no validados.
6. No usar PDF como fuente automatica principal si existe Excel o BC3.
7. Conservar siempre la fuente original.
8. Registrar el hash de cada archivo importado.
9. Registrar logs de importacion.
10. Separar dato bruto, dato normalizado, validaciones, calculos y exportaciones.
11. Cualquier decision arquitectonica relevante debe documentarse en `ADRs.md`.
12. Cualquier tarea debe reflejarse en `CONTEXT.md`.
13. El sistema debe poder detectar duplicados.
14. El sistema debe poder marcar datos como excluidos sin eliminarlos.
15. Todo calculo de ratio debe ser auditable desde resultado final hasta dato de origen.

## Estado actual

| Tarea | Estado | Notas |
|---|---|---|
| Fase 1.1 - Inicializacion base | Completado | Repositorio, validaciones, commit inicial y push cerrados |
| Fase 1.2 - Diseno preliminar del master | Completado | Documento preliminar creado y ADR-009 propuesta |
| Fase 1.3 - Politica de duplicados y versionado | Completado (documental) | Politica preliminar creada y ADR-010 propuesta |
| Crear estructura base | Completado | Estructura inicial del repositorio creada |
| Crear CONTEXT.md | Completado | Documento de gobernanza inicial creado |
| Crear ADRs.md | Completado | Decisiones arquitectonicas iniciales documentadas |
| Crear README.md | Completado | Guia inicial del proyecto creada |
| Crear scripts iniciales | Completado | `validate_context.py` e `inspect_repo.py` |
| Revision humana de diseno preliminar del master | Pendiente | Gate obligatorio antes de parsers |
| Revision humana de politica de duplicados y versionado | Pendiente | Gate obligatorio antes de analisis real |
| Analizar Excel de ejemplo | Pendiente | Requiere muestras reales controladas |
| Analizar BC3 real | Pendiente | Requiere archivo BC3/Presto real |
| Definir estructura final del master | En curso | Basado en `docs/decisions/master_schema_preliminar.md` |
| Definir categorias de ratios | Pendiente | No fijar sin evidencia de datos |
| Definir superficie base | Pendiente | Bloqueante para ratios consolidados |
| Crear parser Excel | Pendiente | No iniciar antes de revision de Fase 1.2 |
| Crear parser BC3 | Pendiente | No iniciar antes de revision de Fase 1.2 |
| Crear validador matematico | Pendiente | Reglas tras definicion final de master |
| Crear exportador al master | Pendiente | Solo con esquema y validaciones cerradas |
| Crear interfaz | Pendiente | Fase posterior (Gemini CLI) |

## Backlog priorizado

### P0

- Gobernanza documental.
- Definicion del master de ratios.
- Definicion de reglas de validacion.
- Analisis de archivos reales (Excel y BC3/Presto).
- Decisiones formales sobre prioridad de fuentes.
- Definicion explicita de superficie base.
- Revision humana del diseno preliminar del master (gate).
- Revision humana de politica de duplicados y versionado (gate).

### P1

- Parser Excel.
- Parser BC3.
- Normalizador de capitulos/partidas.
- Validador matematico y de consistencia.
- Exportador al master.

### P2

- Interfaz de carga y revision.
- Dashboard de seguimiento de calidad de datos.
- Automatizaciones avanzadas de pipeline.
- Visualizacion de ratios y evolucion historica.

## Riesgos técnicos

- Alta variabilidad de formatos Excel entre estudios/proyectos.
- Variabilidad estructural de archivos BC3 segun origen/versiones.
- Archivos Presto nativos potencialmente no legibles de forma directa.
- Fiabilidad limitada de extraccion automatica desde PDF/OCR.
- Riesgo de duplicados entre importaciones o versiones del mismo presupuesto.
- Presupuestos por fases con solape parcial de partidas.
- Diferencias entre presupuesto contratado, mediciones y revisiones posteriores.
- Ausencia o inconsistencia de superficie base para normalizar ratios.
- Capitulos sin mapeo claro a taxonomia interna.
- Cambios futuros en categorias de ratios y criterios comparativos.

## Reglas de actualización

- `CONTEXT.md` debe actualizarse despues de cada tarea relevante.
- Cada decision arquitectonica nueva o cambio sustancial debe registrarse en `ADRs.md`.
- El estado y backlog deben reflejar el avance real del repositorio.
- No se deben cerrar tareas sin evidencia verificable (codigo, tests, o documentacion).
- No avanzar a implementacion de parsers ni al analisis de archivos reales hasta validar documentalmente Fase 1.2 y Fase 1.3.
