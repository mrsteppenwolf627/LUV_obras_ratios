# CONTEXT: LUV Ratios

**Proyecto:** Sistema de consolidacion y validacion de ratios de construccion
**Version:** 1.1.0
**Estado:** FUNCIONAL (en desarrollo activo)
**Fecha actualizacion:** 1 de junio de 2026
**Ultima sesion relevante:** snapshot funcional Backend FASE 1-3 + Frontend FASE 4 verificado localmente, manteniendo la linea canonica del Excel maestro vivo

## Arquitectura

Sistema interno de importacion, validacion y consolidacion para LUV Studio, con dos lineas activas que conviven:

1. Linea canonica del producto: Excel maestro vivo con trazabilidad completa, preservacion del presupuesto origen y salidas auditables.
2. Linea funcional complementaria: backend FastAPI + frontend React para visualizacion, validacion y comparativa de ratios via `/visuales`.

Arquitectura operativa por capas:

1. Ingesta de fuentes: Excel, BC3/Presto exportado y formatos auxiliares.
2. Preservacion RAW: almacenamiento inmutable del archivo origen y sus metadatos.
3. Normalizacion: conversion controlada a esquema interno trazable.
4. Validacion: reglas matematicas y estructurales para aceptar, bloquear o excluir datos.
5. Calculo/agregacion: consolidacion progresiva de ratios solo con datos validados.
6. Exportacion/integracion: actualizacion controlada del Excel maestro y endpoints API para consumo interno.
7. Capa de visuales: frontend React con consumo de `/api/ratios/chapters` y `/api/analyze/comparativa`.

Stack actualmente verificado en repositorio:

- Backend: FastAPI, SQLAlchemy 2, Alembic, SQLite local, Pydantic v2.
- Frontend: React 19, TypeScript, Vite, TailwindCSS 4, React Router 7, Axios.
- Testing: Pytest backend, Vitest + React Testing Library frontend.

## Objetivo del proyecto

Construir un sistema robusto que alimente progresivamente un master de ratios de obra a partir de presupuestos historicos, con trazabilidad estricta desde cada ratio final hasta su fuente original, sin invencion de datos ni estimaciones no soportadas.

Como objetivo complementario ya implementado, el sistema expone visuales internas para:

1. Consultar rangos estadisticos por capitulo.
2. Evaluar la confiabilidad de cada ratio segun numero de muestras.
3. Comparar un presupuesto nuevo frente al historico consolidado.

## Herramientas operativas

- ChatGPT: coordinacion metodologica, arquitectura y mantenimiento conceptual.
- Codex / Antigravity: backend, scripts, validaciones, tests, frontend y documentacion tecnica.
- Frontend local: `frontend/` con Vite para iteracion rapida sobre `/visuales`.

## Restricciones críticas

1. No inventar datos.
2. No estimar datos ausentes.
3. No sobrescribir datos brutos.
4. No borrar historico de importaciones.
5. No actualizar ratios con datos no validados.
6. No usar PDF como fuente automatica principal si existe Excel o BC3.
7. Conservar siempre la fuente original.
8. Registrar el hash de cada archivo importado cuando aplique.
9. Registrar logs de importacion y generacion.
10. Separar dato bruto, dato normalizado, validaciones, calculos y exportaciones.
11. Toda decision arquitectonica relevante debe documentarse en `ADRs.md`.
12. Toda tarea relevante debe reflejarse en `CONTEXT.md` o `PROJECT_STATUS.md`.
13. El sistema debe poder detectar duplicados.
14. El sistema debe poder marcar datos como excluidos sin eliminarlos.
15. Todo calculo de ratio debe ser auditable desde el resultado final hasta el dato de origen.
16. No subir a Git outputs reales, Excels generados ni reportes sensibles.
17. La linea FASE 1-4 de `visuales` no sustituye el roadmap canonico del Excel maestro vivo.

## Estado actual

### Snapshot sesión 1 de junio de 2026 — FASE C + Tab Items × Categorías

- Rama de trabajo actual: `feature/FASE-C-schema`.
- Backend: `pytest` 625 tests pasando (528 previos + 97 nuevos FASE C).
- Frontend: `vitest` 50/50 tests pasando.
- Backend respondiendo en `http://localhost:8000`.
- Frontend Vite respondiendo en `http://localhost:5173`.

#### Nuevas funcionalidades FASE C

- Schema extendido: enums `Categoria` (MEDIUM/PREMIUM/LUXURY/LUXURY_PLUS) y `Confianza`; nueva tabla `item_master_ratios` con constraint único (item_master_id, categoria); columnas `categoria_asignada` y `ratio_comparativa` en `ItemMaster` / `ItemInstance`.
- Migration Alembic `b3c4d5e6f7a8` aplicada y reversible.
- `app/utils/keywords_mapping.py`: clasificación por keywords (4 tiers, 40+ keywords).
- `app/services/clasificacion_service.py`: clasificar por keywords + fallback por precio + nivel de confianza por N.
- `app/crud/item_master_ratios.py`: get/create, actualización incremental (running average), queries, medianas por categoría.
- `GET /api/items/list`: lista de ItemMaster para autocomplete con ratio_actual y confianza via outerjoin.
- `POST /api/items/analisis`: análisis por items con clasificación automática, comparación histórica y actualización incremental de ratios.
- Frontend tab 4 "Items × Categorías": `ItemsAnalisisTab`, `AnalisisForm` con `ItemCombobox` nativo (sin shadcn/ui), `ItemsTable`, `ResumenPorCategoria`, `GraficosAnalisis`, `DetalleItemModal`, `AnalisisHistorico`.

#### Bug fix

- `diff_pct` → `diferencia_pct` en tipos, componentes y fixtures de tests (crash `undefined.toFixed()` al recibir respuesta del API).

### Snapshot funcional verificado el 1 de junio de 2026

- Rama de trabajo actual: `main`.
- `git status --short --branch`: repo limpio y `main` estaba `ahead 6` respecto a `origin/main` antes de este commit.
- Backend y frontend fueron inicializados localmente en esta sesion.
- Backend respondiendo en `http://localhost:8000`.
- Frontend Vite respondiendo en `http://localhost:5173`.
- `pytest`: 528 tests pasando.
- `npm test` en `frontend/`: 6 tests pasando.
- `python scripts/validate_context.py`: OK.
- `python scripts/inspect_repo.py`: OK.

### Linea Backend FASE 1-3 + Frontend FASE 4 (`/visuales`)

- FASE 1: schema y estadisticas ampliadas cerradas para `ratios` con `percentil_25`, `percentil_75` y `std_dev`.
- FASE 2: endpoints `GET /api/ratios/chapters` y `POST /api/analyze/comparativa` operativos.
- FASE 3: indices y optimizaciones aplicados para consultas de visualizacion.
- FASE 4: pagina `/visuales` implementada con tres vistas:
  - Rango de validacion.
  - Solidez/confiabilidad.
  - Comparativa de presupuesto.

Estado de datos de esta linea:

- Presupuestos importados en la BD local: 6.
- Capitulos consolidados reportados por la documentacion vigente: 49.
- Solidez estadistica actual: `N=1` en la mayoria de la linea documentada de visuales, por lo que la confianza sigue siendo debil y depende de ampliar corpus.

Notas de verificacion:

- La API backend esta verificada en esta sesion.
- El frontend Vite responde y los tests frontend pasan.
- La validacion visual final en navegador de `/visuales` sigue siendo una comprobacion manual conveniente cuando se retome UX, aunque la infraestructura local esta levantada.

### Estado canonico del roadmap principal

- Fase 8: cerrada tecnicamente.
- Fase 9.0: iniciada y vigente.
- Fase 9.1: cerrada documentalmente.
- Fase 9.2: cerrada tecnicamente.
- Fase 9.3: cerrada tecnicamente.
- Fase 9.4: cerrada tecnicamente.
- Fase 9.5: cerrada tecnicamente.
- Fase 9.6-preview: ejecutada.
- Fase 9.6-preview-fix: ejecutada.
- Fase 9.6 formal: cerrada documentalmente.
- Fase 9.7: cerrada documentalmente.
- Fase 9.8: cerrada tecnicamente.
- Fase 9.9: cerrada tecnicamente.
- Fase 9.10: cerrada tecnicamente.
- Fase 9.11: cerrada documentalmente.
- Fase 9.12: cerrada tecnicamente.
- Fase 9.13: cerrada tecnicamente.
- Fase 9.14: cerrada tecnicamente.
- Fase 9.15: cerrada tecnicamente.
- Fase 9.16: cerrada tecnicamente.
- Fase 9.17: cerrada tecnicamente.
- Fase 9.18: cerrada tecnicamente.
- Fase 9.19: reportada como complete por Codex.
- Fase 9.20: vigente como fase canonica de auditoria forense de artefactos XLSX y entrega inequivoca para revision humana.

Decisiones vigentes del roadmap principal:

- La salida principal del sistema es un Excel maestro vivo.
- El pipeline debe seguir siendo `PREVIEW_ONLY` para trabajo real controlado mientras no exista promocion explicita.
- BC3 y Presto/PZH siguen en roadmap bajo restricciones documentadas.

## Backlog priorizado

### P0

- Solicitar acceso a presupuestos historicos para ingesta masiva (N > 5 → confianza SOLIDO/MUY_SOLIDO).
- Validar tab "Items × Categorias" en navegador: modal, autocomplete, analisis, graficos.

### P1

- Importar mas presupuestos para elevar la confiabilidad estadistica de la linea de visuales.
- Revisar con negocio si los capitulos consolidados y sus rangos son realistas.
- Mantener no-regresion de endpoints y componentes de visualizacion.

### P2

- Mejorar cobertura E2E de frontend si la linea `/visuales` gana prioridad operativa.
- Consolidar validacion manual de artefactos XLSX de Fase 9.20 y preparar Fase 9.21.

## Riesgos técnicos

- Riesgo documental: confundir el snapshot funcional de `visuales` con el estado canonico del producto principal.
- Variabilidad estructural real de fuentes Excel/BC3 segun origen y version.
- Presto/PZH sin lectura nativa directa confirmada.
- Riesgo de mezclar datos no validados en fases tempranas del maestro vivo.
- Ausencia o inconsistencia de superficie base para normalizacion de ratios.
- Riesgo de baja utilidad estadistica mientras el volumen de presupuestos siga siendo limitado.
- Riesgo de divergencia entre verificacion por tests y validacion UX manual si el navegador conserva cache antigua.

## Reglas de actualización

- `CONTEXT.md` debe actualizarse despues de cada tarea relevante que cambie el estado operativo o documental.
- Cada decision arquitectonica nueva o cambio sustancial debe registrarse en `ADRs.md`.
- `PROJECT_STATUS.md` debe reflejar snapshots operativos concretos con fecha y evidencia.
- No se deben cerrar tareas sin evidencia verificable en codigo, tests, logs o documentacion.
- La linea canonica de Fase 9.x prevalece sobre snapshots auxiliares salvo cambio documentado explicito.
