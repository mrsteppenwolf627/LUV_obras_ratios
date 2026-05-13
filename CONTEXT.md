# CONTEXT.md

## Arquitectura

Sistema interno de importaci?n y validaci?n de presupuestos para LUV Studio, orientado a construir un master de ratios econ?micos con trazabilidad completa.

Arquitectura prevista por capas:

1. Ingesta de fuentes: Excel, BC3/Presto y otros formatos auxiliares.
2. Preservaci?n RAW: almacenamiento inmutable del archivo origen y sus metadatos (incluyendo hash).
3. Normalizaci?n: transformaci?n controlada de cap?tulos, partidas, mediciones e importes a un esquema interno.
4. Validaci?n: reglas matem?ticas y de consistencia para aceptar, marcar o excluir datos.
5. C?lculo/Agregaci?n: generaci?n progresiva de ratios ?nicamente con datos validados.
6. Exportaci?n/Integraci?n: actualizaci?n controlada del master y generaci?n de salidas auditables.
7. Interfaz futura: capa de revisi?n/aprobaci?n manual para cargas y excepciones.

## Objetivo del proyecto

Construir un sistema robusto que alimente progresivamente un master de ratios de obra a partir de presupuestos antiguos, con trazabilidad estricta desde cada ratio final hasta su fuente original, sin invenci?n de datos ni estimaciones no soportadas.

## Herramientas operativas

- ChatGPT: razonamiento central, coordinaci?n metodol?gica, arquitectura, decisiones estrat?gicas, mantenimiento conceptual de `CONTEXT.md` y ADRs.
- Codex / Antigravity: backend, parsers, validadores, tests, auditor?a t?cnica, refactors e integraciones.
- Gemini CLI: frontend, UX, prototipado visual e interfaz interna.

## Restricciones cr?ticas

1. No inventar datos.
2. No estimar datos ausentes.
3. No sobrescribir datos brutos.
4. No borrar hist?rico de importaciones.
5. No actualizar ratios con datos no validados.
6. No usar PDF como fuente autom?tica principal si existe Excel o BC3.
7. Conservar siempre la fuente original.
8. Registrar el hash de cada archivo importado.
9. Registrar logs de importaci?n.
10. Separar dato bruto, dato normalizado, validaciones, c?lculos y exportaciones.
11. Cualquier decisi?n arquitect?nica relevante debe documentarse en `ADRs.md`.
12. Cualquier tarea debe reflejarse en `CONTEXT.md`.
13. El sistema debe poder detectar duplicados.
14. El sistema debe poder marcar datos como excluidos sin eliminarlos.
15. Todo c?lculo de ratio debe ser auditable desde resultado final hasta dato de origen.

## Estado actual

| Tarea | Estado | Notas |
|---|---|---|
| Crear estructura base | Completado | Estructura inicial del repositorio creada |
| Crear CONTEXT.md | Completado | Documento de gobernanza inicial creado |
| Crear ADRs.md | Completado | Decisiones arquitect?nicas iniciales documentadas |
| Crear README.md | Completado | Gu?a inicial del proyecto creada |
| Crear scripts iniciales | Completado | `validate_context.py` e `inspect_repo.py` |
| Analizar Excel de ejemplo | Pendiente | Requiere muestras reales controladas |
| Analizar BC3 real | Pendiente | Requiere archivo BC3/Presto real |
| Definir estructura final del master | Pendiente | Depende de an?lisis de fuentes reales |
| Definir categor?as de ratios | Pendiente | No fijar sin evidencia de datos |
| Definir superficie base | Pendiente | Bloqueante para ratios consolidados |
| Crear parser Excel | Pendiente | Se inicia tras an?lisis de variabilidad real |
| Crear parser BC3 | Pendiente | Se inicia tras an?lisis de BC3/Presto real |
| Crear validador matem?tico | Pendiente | Reglas tras definici?n de master y campos cr?ticos |
| Crear exportador al master | Pendiente | Solo con esquema y validaciones cerradas |
| Crear interfaz | Pendiente | Fase posterior (Gemini CLI) |

## Backlog priorizado

### P0

- Gobernanza documental.
- Definici?n del master de ratios.
- Definici?n de reglas de validaci?n.
- An?lisis de archivos reales (Excel y BC3/Presto).
- Decisiones formales sobre prioridad de fuentes.
- Definici?n expl?cita de superficie base.

### P1

- Parser Excel.
- Parser BC3.
- Normalizador de cap?tulos/partidas.
- Validador matem?tico y de consistencia.
- Exportador al master.

### P2

- Interfaz de carga y revisi?n.
- Dashboard de seguimiento de calidad de datos.
- Automatizaciones avanzadas de pipeline.
- Visualizaci?n de ratios y evoluci?n hist?rica.

## Riesgos t?cnicos

- Alta variabilidad de formatos Excel entre estudios/proyectos.
- Variabilidad estructural de archivos BC3 seg?n origen/versiones.
- Archivos Presto nativos potencialmente no legibles de forma directa.
- Fiabilidad limitada de extracci?n autom?tica desde PDF/OCR.
- Riesgo de duplicados entre importaciones o versiones del mismo presupuesto.
- Presupuestos por fases con solape parcial de partidas.
- Diferencias entre presupuesto contratado, mediciones y revisiones posteriores.
- Ausencia o inconsistencia de superficie base para normalizar ratios.
- Cap?tulos sin mapeo claro a taxonom?a interna.
- Cambios futuros en categor?as de ratios y criterios comparativos.

## Reglas de actualizaci?n

- `CONTEXT.md` debe actualizarse despu?s de cada tarea relevante.
- Cada decisi?n arquitect?nica nueva o cambio sustancial debe registrarse en `ADRs.md`.
- El estado y backlog deben reflejar el avance real del repositorio.
- No se deben cerrar tareas sin evidencia verificable (c?digo, tests, o documentaci?n).
