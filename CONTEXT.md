# CONTEXT: LUV Ratios

**Proyecto:** Sistema de consolidacion y validacion de ratios de construccion
**Version:** 1.2.0
**Estado:** FUNCIONAL (en desarrollo activo)
**Fecha actualizacion:** 2 de junio de 2026
**Ultima sesion relevante:** TASK 5A+5B+5C completado — deduplicación automática + endpoint POST /api/import/budgets + 658/658 tests verdes

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

### Snapshot sesión 2 de junio de 2026 — TASK 5A+5B+5C: Deduplicación + Import

- Rama de trabajo actual: `feature/FASE-C-schema`.
- Backend: `pytest` **658 tests pasando** (625 previos + 33 nuevos TASK 5A+5B+5C).
- Frontend: `vitest` 4/4 tests pasando (RangoValidacion refactor).
- Backend verificado en `http://localhost:8000`.
- Frontend Vite respondiendo en `http://localhost:5173`.

#### Nuevas funcionalidades TASK 5A+5B+5C

- `app/utils/normalize.py`: `normalize_item_key()` — NFKD+lowercase+colapso de espacios+strip+max500, idempotente.
- `src/db/schema.py`: tabla `BudgetImport` (file_hash único, status, items_count, error_message).
- `app/crud/budgets.py`: `create/get/update_budget_import()` para trazabilidad de cada importación API.
- `app/schemas/import_budgets.py`: `BudgetImportRequest` + `BudgetImportResponse` (Pydantic v2).
- `POST /api/import/budgets`: importación JSON con deduplicación automática — 409 si hash existe, skip de líneas inválidas, contadores `items_creados`/`items_duplicados`/`muestras_actualizadas`.
- Migración Alembic `c4d5e6f7a8b9` aplicada y en HEAD.
- `tests/test_normalize.py`: 11 unit tests (normalize puro).
- `tests/test_import.py`: 16 integration tests (5 suites: valid, dedup, 409, inválidas, validación).

#### Refactor UX RangoValidacion (REFACTOR-RANGO-002)

- `RangoValidacion.tsx`: 3 estados según `cantidad_datos` — SIN_DATOS (N=0), MUESTRA_INSUFICIENTE (N<2), VALIDACION_COMPLETA (N≥2).
- Constante `MUESTRAS_MINIMAS_PARA_RANGO=2` centraliza el umbral.

#### Validación manual en vivo (2026-06-02)

```
Test A — Importación válida:
  POST /api/import/budgets → 200 {"items_creados":1,"status":"success"}  ✅

Test B — Re-importar mismo file_hash:
  POST /api/import/budgets (mismo hash) → 409 "Ya importado"  ✅

Test C — 3 variantes del mismo item en un payload:
  POST /api/import/budgets → {"items_creados":1,"items_duplicados":2}  ✅
```

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

| Tarea | Impacto | Dependencia | Riesgo | Esfuerzo | Prioridad |
|---|:---:|:---:|:---:|:---:|:---:|
| ADR-17: Estrategia de deduplicación | Alto | — | Bajo | 1h | ✅ COMPLETADO |
| TASK 5A: Función normalize_item_key() | Alto | ADR-17 | Bajo | 2h | ✅ COMPLETADO |
| TASK 5B: Endpoint POST /api/import/budgets | Alto | TASK 5A | Medio | 3h | ✅ COMPLETADO |
| TASK 5C: Tests unitarios + integración | Alto | TASK 5B | Bajo | 2h | ✅ COMPLETADO |
| TASK 5D: Validación duplicados archivo | Medio | TASK 5B | Bajo | 1h | ⏳ PENDIENTE |
| TASK 6: Refactor ingesta automática | Medio | TASK 5 | Bajo | 3h | ⏳ PENDIENTE |

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

## 🔐 ADRs: Decisiones Arquitectónicas

### ADR-16: Input Autónomo en RangoValidacion

**Status:** ✅ CONGELADA  
**Fecha:** 2026-06-02  
**Propuesto por:** Aitor + Claude  

**Decisión:**
Refactorizar `RangoValidacion.tsx` para incluir input local autónomo. Usuario entra número → valida → ve resultado, todo en el mismo componente.

**Por qué:**
- Componente independiente, reutilizable
- Arquitectura clara (sin acoplamiento padre-hijo)
- UX intuitiva: input + gráfico + validación en mismo lugar
- Fácil para arquitecto/equipo obras

**Alternativa rechazada:**
- Input en página padre = confusión de responsabilidades, acoplamiento innecesario

**Impacto:**
- Afecta: `frontend/src/components/Visuales/RangoValidacion.tsx`
- Props: remover `miValor` si viene del padre
- Riesgo: BAJO (cambio UI puro)
- Sin impacto en: Backend, BD, lógica validación (ya existe)

**Status de cambio:** Congelada. Solo revisar si falla validación manual.

### ADR-17: Estrategia de Deduplicación en Ingesta Masiva

**Status:** ✅ CONGELADA  
**Fecha:** 2026-06-02  
**Propuesto por:** Claude + Aitor  

**Decisión:**
Implementar deduplicación mediante normalización determinística de `item_key` + reutilización de `get_or_create_item_master()` existente.

**Problema:**
Sin normalización, 1000 partidas históricas = 1000 ItemMaster (N=1 cada uno) = sistema permanentemente "MUY_DÉBIL".
Ej: "CARPINTERÍA ALUMINIO" ≠ "Carpintería Aluminio" = duplicación silenciosa.

**Solución:**
1. Función `normalize_item_key(descripcion)` → determinística, idempotente
2. Endpoint `POST /api/import/budgets` que usa `get_or_create_item_master(item_key_normalizado)`
3. Validación de hash para evitar re-importar mismo presupuesto
4. Incremento automático de `muestras_count` en ItemMaster

**Componentes:**
- `app/utils/normalize.py` → función normalización
- `app/routers/import_budgets.py` → endpoint importación
- `app/crud/budgets.py` → CRUD para BudgetImport (metadatos)
- Tests: `tests/test_normalize.py`, `tests/test_import.py`

**Normalización rules:**
- Lowercase
- Remover espacios múltiples
- Remover acentos/diacríticos
- Remover caracteres especiales (excepto guiones/espacios internos)
- Máximo 500 caracteres
- Idempotente: `normalize(normalize(x)) == normalize(x)`

**Validación duplicados:**
- Tabla `budget_import` con (filename_hash, import_date, status)
- Si `filename_hash` existe → rechazar "Ya importado el 2026-06-01"

**Impacto:**
- Nuevos archivos: `normalize.py`, `import_budgets.py`, `budgets.py` (crud)
- Nueva tabla: `budget_import` (metadatos importación)
- Nueva migración Alembic
- Sin cambios en ItemMaster, ItemInstance (compatible)

**Trade-offs:**
- (+) Deduplicación automática, trazabilidad de importaciones
- (-) Normalización es irreversible (item_key normalizado ≠ descripción original)

**Status cambio:** Congelada. Cambios solo con consensus arquitectónico.

---

## 🔐 ÚLTIMA ACTUALIZACIÓN

- **Fecha:** 2026-06-02
- **Modelo:** Claude Code (Sonnet 4.6)
- **Cambios:**
  - ✅ `app/utils/normalize.py` — `normalize_item_key()` determinístico e idempotente
  - ✅ `app/routers/import_budgets.py` — endpoint `POST /api/import/budgets`
  - ✅ `app/crud/budgets.py` — CRUD `BudgetImport` (create/get/update)
  - ✅ `app/schemas/import_budgets.py` — schemas Pydantic v2
  - ✅ `src/db/schema.py` — tabla `budget_imports`
  - ✅ `migrations/versions/c4d5e6f7a8b9` — CREATE TABLE budget_imports (HEAD)
  - ✅ `tests/test_normalize.py` — 11 unit tests normalize
  - ✅ `tests/test_import.py` — 16 integration tests import
  - ✅ `frontend/src/components/Visuales/RangoValidacion.tsx` — 3 estados UX

- **Checklist:**
  - [x] 658/658 tests pasando
  - [x] Endpoint `/api/import/budgets` funcional (validado en vivo)
  - [x] Deduplicación automática por `normalize_item_key()` verificada
  - [x] Prevención de re-importar (`file_hash` único → 409) verificada
  - [x] RangoValidacion 3 estados (N=0 / N<2 / N≥2) funcional
  - [x] Sin breaking changes en tests existentes
  - [x] BD en estado HEAD (Alembic `c4d5e6f7a8b9`)
  - [x] Documentado en CONTEXT.md + ADR-17
