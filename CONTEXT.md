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

- Fecha de consolidacion documental: 2026-05-19.
- Fase 8: cerrada tecnicamente.
- Fase 9.0: iniciada y vigente.
- Fase 9.1: cerrada documentalmente.
- Fase 9.2: cerrada tecnicamente.
- Fase 9.3: cerrada tecnicamente.
- Fase 9.4: cerrada tecnicamente.
- Fase 9.5: iniciada (idempotencia por run_id, checksum SHA-256 y rollback negativo).
- Decision vigente: la salida principal del sistema es un Excel maestro vivo, iterativo y actualizable (ADR-019 y `docs/decisions/phase_9_0_live_excel_master_output_definition.md`).
- BC3: modulo avanzado operativo, no prioridad unica.
- Excel: lector integral operativo y contrato multi-formato vigente.
- Presto/PZH: obligatorio en roadmap mediante ruta tecnica evidenciada (export/herramienta equivalente), sin lectura nativa directa confirmada.

## Fase vigente

- Fase vigente: 9.5 - idempotencia, checksum fuerte y rollback negativo del Excel maestro vivo.
- Estado: iniciada y activa.
- Objetivo: endurecer cargas sinteticas multi-lote con idempotencia explicita por run_id, registrar checksum fuerte SHA-256 en snapshots y bloquear rollback negativo ante snapshots inexistentes/corruptos/fuera de ruta/esquema invalido.
- Restriccion metodologica: solo datos sinteticos y sin rediseño funcional fuera del contrato 9.1/9.2/9.3/9.4.

## Proxima fase recomendada

- Proxima fase: 9.6 - preparacion de contrato pre-real y controles de entrada sintetica ampliados.
- Condicion: mantener restricciones activas y no habilitar datos reales hasta validacion explicita.

## Restricciones activas (fase 9.5)

- Endurecimiento controlado: idempotencia run_id, checksum SHA-256 y rollback negativo sin rediseño amplio.
- Mantener compatibilidad con contrato 9.1/9.2/9.3/9.4.
- Solo datos sinteticos y pruebas de integridad/resiliencia.
- No usar datos reales.
- No importar presupuestos reales al master.
- No calcular ratios finales.
- No consolidar importes reales.
- No normalizar categorias finales.
- No romper trazabilidad ni validaciones previas ya consolidadas.
- No subir Excels generados.
- No diseñar interfaz, dashboard ni flujo UX en esta fase.
- Respetar contrato documental definido en Fase 9.1, Fase 9.2, Fase 9.3 y Fase 9.4.
- No modificar RAW.
- No subir muestras reales ni reports/outputs sensibles.

## Resumen de fases cerradas (alto nivel)

- Fase 1.x: base de gobernanza documental y restricciones iniciales cerrada.
- Fase 2.x: diagnostico real de muestras (no destructivo) cerrado.
- Fase 3.x: extractor diagnostico BC3 y readiness preliminar cerrados.
- Fase 4.x: parser BC3 preliminar/estricto y validacion estructural cerrados.
- Fase 5.x: normalizacion intermedia BC3 y validacion de contrato cerradas.
- Fase 6.x: diagnostico real Excel y perfilado profundo cerrados.
- Fase 7.x: lector integral Excel y contrato comun multi-formato cerrados.
- Fase 8: estrategia tecnica obligatoria Presto/PZH cerrada tecnicamente.

## Backlog priorizado

### P0

- Implementar idempotencia explicita por run_id en carga sintetica incremental.
- Sustituir checksum de snapshots por SHA-256.
- Endurecer rollback negativo y asegurar restauracion segura ante fallo.

### P1

- Cerrar Fase 9.5 con evidencia de resiliencia y no-regresion.
- Preparar Fase 9.6 para contrato pre-real sin habilitar datos reales.

### P2

- UX/interfaz de carga y revision.
- Automatizaciones avanzadas de pipeline.
- Visualizacion de ratios y evolucion historica.

## Riesgos técnicos

- Variabilidad estructural real de fuentes Excel/BC3 segun origen/versiones.
- Presto/PZH sin lectura nativa directa confirmada.
- Riesgo de mezclar datos no validados en fases tempranas del maestro vivo.
- Ausencia o inconsistencia de superficie base para normalizacion de ratios.
- Riesgo de perder trazabilidad en futuras sobrescrituras si no se disena historial explicito.

## Historico de fases (referencial, no estado vigente)

Este bloque conserva hitos para trazabilidad historica. No sustituye el estado canonico anterior.

- Fase 4.3.1: ajuste menor de readiness BC3.
- Fase 4.3.2: cierre de ajustes menores de readiness BC3.
- Fase 4.4 a 4.4.4: validacion ampliada y exclusion controlada de BC3 no aptos.
- Fase 4.5 a 4.7: parser BC3 estricto y validacion cruzada estricta.
- Fase 5.0 a 5.3: normalizacion intermedia BC3 y giro multi-formato.
- Fase 6 y 6.1: diagnostico y perfilado Excel.
- Fase 7.0 a 7.2: lector integral Excel y contrato comun multi-formato.
- Fase 8: estrategia obligatoria Presto/PZH basada en evidencia.
- Fase 9.0: definicion del Excel maestro vivo como salida principal.
- Fase 9.1: diseno tecnico del generador del Excel maestro vivo.
- Fase 9.2: implementacion controlada del generador del Excel maestro vivo.
- Fase 9.3: hardening con carga sintetica incremental, validaciones referenciales y snapshots/rollback/retencion iniciales.
- Fase 9.4: refactor controlado de validaciones de integridad en modulo dedicado.

## Fuentes canonicas de estado actual

- `ADRs.md` (ADR-019).
- `docs/decisions/phase_8_presto_pzh_support_strategy.md`.
- `docs/decisions/phase_9_0_live_excel_master_output_definition.md`.
- `docs/decisions/phase_9_1_live_excel_master_generator_design.md`.
- `docs/decisions/phase_9_2_live_excel_master_generator_implementation.md`.
- `docs/decisions/phase_9_3_live_excel_master_hardening.md`.
- `docs/decisions/phase_9_4_live_excel_integrity_validation_refactor.md`.
- `README.md` (resumen operativo).

## Reglas de actualización

- `CONTEXT.md` debe actualizarse despues de cada tarea relevante.
- Cada decision arquitectonica nueva o cambio sustancial debe registrarse en `ADRs.md`.
- El estado y backlog deben reflejar el avance real del repositorio.
- No se deben cerrar tareas sin evidencia verificable (codigo, tests, o documentacion).
- La seccion "Estado operativo vigente (canonico)" prevalece sobre bloques historicos.
