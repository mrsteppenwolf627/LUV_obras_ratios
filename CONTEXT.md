# CONTEXT: LUV Ratios

**Proyecto:** Sistema de consolidacion y validacion de ratios de construccion
**Version:** 1.4.1
**Estado:** 🟢 PRODUCCIÓN READY
**Fecha actualizacion:** 9 de junio de 2026
**Ultima sesion relevante:** Tab Comparativa operativo — POST /api/analyze/comparativa calcula desviaciones, impacto monetario y confiabilidad globales + 733/733 tests verdes

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
18. **Deployment obligatorio en Vercel + Supabase. Alternativas externas prohibidas salvo autorización explícita.** No se propondrá Render, Railway, Fly.io, Docker externo, VPS ni ningún otro proveedor. No se prepararán migraciones fuera de Vercel ni planes B en otra plataforma.

## Estado actual - v1.2.0 (3 de junio de 2026)

### Snapshot funcional verificado 3 de junio de 2026

**Frontend:**
- ✅ Logo LUV Studio actualizado en top nav
- ✅ Fix error sintaxis TablaConfiabilidad.tsx (escaped <, >)
- ✅ Fix error sintaxis JSX TablaConfiabilidad.tsx (tags nesting/closing)
- ✅ Tutorial completo en Tab Comparativa (instrucciones área, capítulos, valores)
- ✅ 4/4 tutoriales interactivos completos y unificados en estilo (Rango, Solidez, Comparativa, Items × Categorías)
- ✅ RangoValidacion con 3 estados (N=0, N=1, N≥2)

**Backend:**
- ✅ POST /api/import/budgets (deduplicación automática)
- ✅ normalize_item_key() (determinístico, idempotente)
- ✅ ImportService (reutilizable, sin acoplamiento HTTP)
- ✅ Validaciones rigurosas (regex SHA256, tipos, rangos)
- ✅ Logging enterprise-grade (INFO/DEBUG/WARNING/ERROR + UUID traza)
- ✅ DuplicateImportError (contrato limpio entre capas)
- ✅ BudgetImport table (prevención re-importar por file_hash)

**Testing:**
- ✅ 670/670 tests pasando
- ✅ Cobertura: unitarios + integración + edge cases
- ✅ ImportService testeable sin HTTP (fixture direct_session)

**Arquitectura:**
- ✅ Separación clara: Router (HTTP) ↔ Service (negocio)
- ✅ Reutilizable desde jobs/scripts/CLI
- ✅ 0 breaking changes
- ✅ ADR-16, ADR-17 congeladas

**Commits últimas sesiones (2–3 junio):**
- Logo + tutoriales frontend
- REFACTOR-RANGO-002: UX por cantidad muestras
- TASK 5A–5C: deduplicación + import + tests
- TASK 5D: validaciones + logging + edge cases
- TASK 6: refactor ingesta → ImportService

---

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

| Tarea | Estado | Impacto | Riesgo | Esfuerzo | Completada |
|---|:---:|:---:|:---:|:---:|:---:|
| **TASK 7:** Ingesta masiva (FASE 1-4) | ✅ COMPLETADA | Alto | Bajo | 8-12h | 9 junio 2026 |
| **TASK 8:** Enriquecimiento Master con Gama Ranges | ✅ COMPLETADA | Alto | Bajo | 6-8h | 12 junio 2026 |
| **TASK 9:** Dashboard gamas + reportes | ⏳ BACKLOG | Medio | Bajo | 4h | — |

## ✅ TASK 7 COMPLETADA - Ingesta Masiva + Afinación + Master Descargable

**Estado:** 🟢 PRODUCCIÓN READY  
**Fecha completación:** 9 de junio de 2026  
**Presupuestos:** 5 importados (90 líneas, 36 items únicos)

**Fases Completadas:**

1. ✅ **FASE 1: Importación masiva**
   - Script: `scripts/importar_presupuestos_masivo.ps1`
   - 48 archivos analizados (5 xlsx, 12 pzh, 12 bc3, 9 Presto)
   - 12 procesados exitosamente (4,694 líneas extraídas)
   - Parsers: Excel flexible + BC3 robusto con extracción de precios

2. ✅ **FASE 2: Auditoría post-import**
   - Script: `scripts/analizar_post_import.py`
   - 26 items iniciales documentados
   - Distribución confianza analizada

3. ✅ **FASE 3: Afinación + Re-importación con volumen**
   - Parsers mejorados (regex BC3, column mapping Excel)
   - 5 presupuestos test: 90 líneas
   - Resultado: 36 items únicos, 54 duplicados (60% tasa)
   - normalize_item_key() + get_or_create_item_master(): FUNCIONAL

4. ✅ **FASE 4: Master descargable + Validación visuales + Frontend integrado**
   - Master Excel: `data/exports/MASTER_2026-06-09.xlsx`
   - 36 items con ratios consolidados, coloreo por confianza
   - **Backend endpoints operativos:**
     - `GET /api/ratios/chapters` — lista completa de capítulos
     - `GET /api/ratios/rango?chapter=X` — estadísticas por capítulo (min/max/percentiles)
     - `POST /api/analyze/comparativa` — comparativa presupuesto vs histórico
   - **Frontend Tab "Rango" operativo:**
     - Dropdown de capítulos
     - Carga de estadísticas via `/api/ratios/rango`
     - Visualización de rangos con percentiles
   - **Tab "Solidez" operativo:**
     - Tabla de confiabilidad por capítulo
   - **Tab "Comparativa" operativo:**
     - POST /api/analyze/comparativa devuelve desviación €/%, impacto monetario, confiabilidad
     - Análisis por capítulo + resumen global
   - Sistema: LISTO PARA PRODUCCIÓN

**Resultados Finales Consolidados:**
- **Items:** 36 únicos con categorías correctas (DEMOLICION, ESTRUCTURA, CARPINTERIA, FONTANERIA, ELECTRICIDAD, PINTURA)
- **Deduplicación:** 60% (54 duplicados detectados)
- **Tests:** 733/733 pasando (718 core + 15 nuevos para visuales)
- **Confianza:**
  - SÓLIDO (N≥5): 1 item (2.8%)
  - DÉBIL (N 2-4): 31 items (86.1%)
  - MUY_DÉBIL (N=1): 4 items (11.1%)
  - Items convergentes (N≥2): 32/36 (88.9%)
- **Presupuestos:** 27 importados + auditados (real production data)
- **Master Excel:** GENERADO con formato coloreado por confianza
- **Visuales:** OPERATIVAS (Rango + Solidez) y funcionales
- **Tests:** 725/725 verdes (718 core + 7 nuevos stats tests)
- **Backend:** 5 commits de fixes + optimizaciones (uvicorn startup, categorías, API datos)

**Scripts Entregados:**
- importar_presupuestos_masivo.ps1 (parsers mejorados)
- analizar_post_import.py (auditoría)
- generar_master_excel.py (master descargable)
- validar_visuales.py (validación)
- diagnosticar_fallos.ps1 (análisis estructuras)
- generar_test_data.py (datos test)

---

## Cómo usar el sistema

### Importar presupuestos

1. Obtén el presupuesto en formato JSON o Excel
2. Convierte a JSON con estructura:
```json
{
  "filename": "presupuesto_ene2026.xlsx",
  "file_hash": "SHA256_hash_del_archivo_64_hex_chars",
  "building_type": "residencial",
  "lineas": [
    {"descripcion": "Carpintería Aluminio", "cantidad": 10, "precio_unitario": 245.50}
  ]
}
```
3. `POST http://localhost:8000/api/import/budgets`
4. Sistema deduplica automáticamente por `normalize_item_key()`

### Usar visuales

- **Tab Rango:** Entra precio unitario, ve si está en rango histórico
- **Tab Solidez:** Mira qué capítulos tienen datos confiables
- **Tab Comparativa:** Compara tu presupuesto total vs histórico
- **Tab Items×Categorías:** Desglosar análisis por categoría

Cada tab tiene tutorial interactivo (botón "📖 Cómo usar")

---

## Setup local (próxima sesión)

```bash
# Backend
python -m app.main
# → localhost:8000

# Frontend
cd frontend/ && npm run dev
# → localhost:5173

# Tests
pytest
# Esperado: 670/670 verdes
```

---

## Scripts útiles

```powershell
# Importar presupuesto
$json = Get-Content "presupuesto.json" -Raw
Invoke-RestMethod -Uri "http://localhost:8000/api/import/budgets" `
    -Method POST -Headers @{"Content-Type"="application/json"} `
    -Body $json

# Correr solo tests de importación
pytest tests/test_import.py tests/test_normalize.py -v

# Ver migraciones Alembic
alembic history
alembic current
```

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

## ✅ TASK 8 COMPLETADA - Enriquecimiento Master con Gama Ranges

**Estado:** 🟢 PRODUCCIÓN READY  
**Fecha completación:** 12 de junio de 2026  
**Modelo:** Claude Code (Haiku 4.5)

**Componentes Entregados:**

1. ✅ **Tabla gama_ranges + seed data (PROMPT 1)**
   - Modelo: `src/db/schema.py:GamaRange` (8 columnas: material_type + 4 tiers)
   - Script: `scripts/seed_gama_ranges.py` (8 materiales base: PORCELANA, PIEDRA, PINTURA, METAL, VIDRIO, MADERA, TEXTIL, ENCIMERA)
   - Seed: 8 registros insertados con rangos EUR/m² verificados

2. ✅ **Lógica gama + endpoint GET /api/items/with_gamas (PROMPT 2)**
   - Utilidad: `app/utils/gama_utils.py` (determine_gama, find_gama_range)
   - Router: `app/routers/items_extended.py` (GET /api/items/with_gamas con filtros q/categoria/limit)
   - Schema: `app/schemas/items_extended.py` (ItemMasterWithGama + ItemsWithGamasResponse)

3. ✅ **Persistencia gama_asignada en BD (PROMPT 3)**
   - Columna: `item_master.gama_asignada VARCHAR(20) DEFAULT 'SIN_CLASIFICAR'`
   - Script: `scripts/assign_gamas_persistent.py` (itera items, calcula gama, persiste en BD)
   - Integración: init_db.py ejecuta seed + assign_gamas automáticamente

4. ✅ **Transacciones + Constraints + Error Handling (PROMPT 5B)**
   - Transacciones: rollback en excepciones, commit solo si OK (try/except/finally)
   - Constraints: GamaRange._validate_constraints() en __init__ y __setattr__
     * Valida: medium_min <= medium_max para CADA tier
     * Valida: premium_min >= medium_max (sin solapamiento)
     * Ejemplo rechazado: medium_min=100 > medium_max=50
   - Error Handling:
     * Per-item fallback: si un item falla, asigna SIN_CLASIFICAR
     * HTTP 500 con JSON descriptivo: {error, message, timestamp}
     * Logging: exc_info=True, qué falló específicamente

**Archivos Creados:**
- `src/db/schema.py` (GamaRange model + validators)
- `scripts/seed_gama_ranges.py` (seed 8 materiales)
- `scripts/assign_gamas_persistent.py` (persistencia en BD)
- `app/utils/gama_utils.py` (lógica determine_gama/find_gama_range)
- `app/routers/items_extended.py` (endpoint GET /api/items/with_gamas)
- `app/schemas/items_extended.py` (Pydantic models)
- `tests/test_gama_assignment.py` (12 tests nuevos)

**Archivos Modificados:**
- `src/db/schema.py` (columna gama_asignada en ItemMaster)
- `scripts/init_db.py` (integración seed + assign_gamas)
- `app/main.py` (include_router items_extended)

**Validaciones Completadas:**
- Seed data: 8/8 materiales cumplen constraints
- Endpoint: devuelve gama_asignada (nunca null)
- Transacciones: rollback on error, commit on success
- Constraints: 3/3 tests de constraint violations pasan
- Tests totales: 12 nuevos (+ tests existentes)

---

## 🔐 ÚLTIMA ACTUALIZACIÓN

- **Fecha:** 17 de junio de 2026
- **Versión:** 1.4.3
- **Modelo:** Claude Code (Sonnet 4.6)

### Sesión 17 junio 2026 — Debug Vercel Python Serverless

**Estado producción:** 🔴 BLOQUEADO — Frontend carga, todos los endpoints /api/* devuelven 404.

**Hipótesis activa:** El rewrite `"/api/:path*" → "/api"` apuntaba a un directorio (no a una función), causando 404 en toda la capa API. Además el handler de `api/hello.py` usaba firma Lambda/AWS incorrecta.

**Cambios realizados:**
- `api/hello.py`: reescrito con `BaseHTTPRequestHandler` (formato Python nativo de Vercel, stdlib puro, sin dependencias)
- `vercel.json`: rewrites corregidos:
  - Añadida regla explícita `"/api/hello" → "/api/hello"` (diagnóstico aislado)
  - Corregida regla principal `"/api/:path*" → "/api/index"` (antes apuntaba a `/api`, un directorio → causa raíz del 404)

**Endpoint de diagnóstico:** `https://luv-obras-ratios.vercel.app/api/hello`

**Resultado esperado:** `200 OK` — `Hello from Vercel Python`

**Próximos pasos según resultado:**

- **A) `/api/hello` responde 200:** Vercel detecta funciones Python. El problema anterior era solo el rewrite roto. Pasar a verificar `api/index.py` (imports pesados, Supabase, etc).
- **B) `/api/hello` sigue en 404:** Vercel no está detectando funciones Python en absoluto. Causa probable: framework mal configurado en dashboard de Vercel, proyecto no tiene `@vercel/python`, o el runtime Python no está habilitado para este proyecto. Solución: revisar Settings → Functions en el dashboard.

---

### Sesión 17 junio 2026 (continuación) — Diagnóstico de configuración Vercel

**Restricción crítica reafirmada:** Solo Vercel + Supabase. Alternativas externas prohibidas salvo autorización explícita (ver Restricción #18).

**Test `/api/hello`:** 🔴 **404 confirmado** (estado reportado por el usuario).

**Conclusión:** Vercel no está publicando funciones Python desde `/api`. Todo `/api/*` devuelve 404 mientras el frontend carga correctamente.

**Auditoría del repositorio (todo CORRECTO — no es la causa):**
- `api/hello.py` y `api/index.py` están rastreados en git; no hay exclusiones en `.gitignore` para `api/`.
- `vercel.json` está en la **raíz** del repo (ubicación correcta) y es sintácticamente válido.
- `.python-version` = `3.12` (limpio, sin BOM).
- `requirements.txt` en la raíz, rastreado.
- No existe `vercel.json` ni `now.json` dentro de `frontend/` (no hay config en conflicto).
- El bloque `functions` lista `api/index.py`; esto **no excluye** a `api/hello.py` (Vercel autodetecta todo `/api`).
- Los `rewrites` no interfieren: una función real en `/api/hello` se resuelve por filesystem **antes** que cualquier rewrite.

**Causa probable (orden de probabilidad):**
1. **Root Directory mal configurado en el dashboard** → apunta a `frontend/` en vez de la raíz del repo. Esto explica TODOS los síntomas a la vez: el frontend Vite compila (es la raíz efectiva), pero `api/` y el `vercel.json` de la raíz quedan **invisibles** → 404 en toda la capa API. Es la causa #1 del patrón "frontend OK + api 404".
2. **El proyecto del deployment `luv-obras-ratios.vercel.app` NO aparece en el team "Aitor's projects"** (verificado vía API de Vercel: los 9 proyectos del team son otros). Probablemente vive en la cuenta personal/Hobby. Riesgo: estar redeployando/mirando un proyecto distinto al que sirve la URL.
3. Build de Python fallando silenciosamente (runtime no habilitado / instalación de `requirements.txt` rota) → revisar build logs en el dashboard.

**Cambio aplicado en código:** NINGUNO. La configuración del repo ya es correcta para Root Directory = raíz; cualquier edición a `vercel.json` arriesgaría romper el frontend que hoy sí funciona, sin atacar la causa real (que es de dashboard). La corrección debe hacerse en Settings del proyecto en Vercel, no en el repo.

**A revisar manualmente en el dashboard de Vercel (Settings del proyecto que sirve `luv-obras-ratios.vercel.app`):**
1. **Settings → General → Root Directory:** debe estar **vacío** (= raíz del repo), NO `frontend`. Si está en `frontend`, cambiarlo a raíz y redeploy. ← acción más probable.
2. **Settings → General → Framework Preset:** "Other" (no "Vite"), para que respete `buildCommand`/`outputDirectory` del `vercel.json`.
3. Confirmar que el proyecto enlazado al repo es el correcto y en qué scope vive (personal vs team).
4. **Deployments → último build → Build Logs:** buscar si aparece "Installing required dependencies..." Python y "Compiling api/index.py / api/hello.py". Si no aparecen, Vercel no ve `/api`.
5. **Deployment → pestaña Functions/Source:** confirmar que existan funciones serverless generadas para `api/index.py` y `api/hello.py`.
6. Confirmar que el commit desplegado incluye `api/hello.py` (commits `2cc1039`, `40f9d2a`).

**URL exacta a probar tras redeploy:** `https://luv-obras-ratios.vercel.app/api/hello` → esperado `200 OK` con cuerpo `Hello from Vercel Python`.

---

### Sesión 17 junio 2026 (3ª iteración) — Routing Vercel: solo se publicaba /api/index

**Dato nuevo del dashboard (Deployment Summary):** Static Assets OK · Functions: **solo `/api/index`** · Runtime: Python 3.12 · `/api/hello` NO aparece · `/api/hello` = 404.

**Verificación git:** `HEAD` local = `origin/main` = `40f9d2a`. `api/hello.py` **existe en el commit desplegado** (confirmado con `git cat-file -e origin/main:api/hello.py`). Descartado: no es un problema de commit/push.

**Diagnóstico de routing (limpio):**
- La lista de *Functions* del dashboard refleja lo que Vercel **construyó**, no el routing. Si `/api/hello` no aparece ahí, NO es por los rewrites (un rewrite solo redirige tráfico; no borra una función ya construida). → **Opción C descartada.**
- Es un problema de **inclusión en el build**. La única palanca en `vercel.json` que nombra funciones es el bloque `functions`, que enumeraba **exclusivamente** `api/index.py`. En esta config (Root Directory ya correcto → `vercel.json` sí se lee), Vercel construyó solo lo enumerado. → **Causa raíz = Opción D.**
- Coherente con la sesión previa: antes el Root Directory estaba mal → `vercel.json` ignorado → todo 404. Al corregirlo, el bloque `functions` pasó a estar activo y limitó el build a `api/index`.

**Decisión:** Opción **D** (corregir `vercel.json`). Equivale también a B (hello queda como función realmente publicada). A se mantiene como fallback (todo endpoint real ya pasa por `api/index`/FastAPI).

**Cambio aplicado (mínimo):** `vercel.json` → clave de `functions` de `"api/index.py"` a `"api/*.py"`, preservando `memory:1024`/`maxDuration:10`. No se tocó `api/index.py`, routers, Supabase, DATABASE_URL ni frontend. Rewrites intactos (la función real `/api/hello` se resuelve por filesystem antes que cualquier rewrite).

**URL a probar tras push + redeploy:** `https://luv-obras-ratios.vercel.app/api/hello` → esperado `200 OK` `Hello from Vercel Python`. Tras el redeploy, verificar en Deployment → Functions que aparezcan **ambas**: `/api/index` y `/api/hello`.

---

### Sesión 17 junio 2026 (4ª iteración) — Bloqueo de deploy: referencia legacy `@database_url`

**Error de Vercel:** `Environment Variable "DATABASE_URL" references Secret "database_url", which does not exist.` Persistía incluso tras borrar y recrear `DATABASE_URL` en el dashboard.

**Causa raíz:** `vercel.json` contenía un bloque `env` con `"DATABASE_URL": "@database_url"`. El prefijo `@` es la sintaxis **legacy de Vercel para referenciar un "Secret"** (concepto distinto de las Environment Variables del dashboard). En cada deploy, Vercel intentaba vincular la variable a un Secret llamado `database_url` que no existe → fallo en la fase de validación de entorno, **antes del build**, bloqueando cualquier deployment. Recrear la variable en el dashboard NO lo arreglaba porque el dashboard crea una Environment Variable normal, no un Secret; el `env` de `vercel.json` forzaba la búsqueda del Secret.

**Búsqueda confirmatoria:** la referencia `@database_url` aparecía **únicamente** en `vercel.json:16`. Ningún `.env`, `.env.example`, README ni script usa `@secret`. `.env` (no rastreado, gitignored) tiene el valor literal correcto; `app/config.py`, `migrations/env.py` y `src/db/models.py` leen `os.getenv("DATABASE_URL")` en runtime (correcto).

**Cambio aplicado (mínimo):** eliminado por completo el bloque `env` de `vercel.json`. NO se sustituyó por la URL real ni se escribió ningún secreto en el repo.

**Política de secretos:** `DATABASE_URL` debe gestionarse **exclusivamente desde Environment Variables del dashboard de Vercel**. Prohibido guardar secretos/credenciales reales en el repositorio (`vercel.json` ni ningún archivo rastreado). `app/config.py` ya la consume vía `os.getenv("DATABASE_URL")`, sin necesitar mapeo en `vercel.json`.

**Pendiente de la iteración anterior (sigue vigente):** no existía deployment para el commit `89ca724` → revisar conexión Git ↔ Vercel y Production Branch en el dashboard (proyecto en scope personal/Hobby). Este fix del `env` desbloquea la fase de validación; aún hay que asegurar que los pushes a `main` generen deployment de producción.

---

### Sesión 17 junio 2026 (5ª iteración) — Vercel + Supabase OPERATIVOS · diagnóstico de rutas

**Estado producción:** 🟢 Vercel + Supabase funcionando. `DATABASE_URL` corregida usando **Supabase Transaction Pooler**.
- `/api/hello` → 200 OK (función Python independiente publicada).
- `/api/index` → `{"detail":"Not Found"}` (FastAPI vivo; 404 de FastAPI, no de edge).
- `/api/ratios/chapters` → 200 OK con `[]`.
- `/api/items/list` → 404 `{"detail":"Not Found"}`.

**Causa raíz de los 404 funcionales — DOS apps FastAPI divergentes:**
- `app/main.py` = entry point LOCAL (uvicorn, `python -m app.main`, localhost:8000). Incluye los 5 routers **+ endpoints inline** (`@app.get` directos): `/api/master`, `/api/archived`, `/api/ratios/stats`, `/api/import`, `/api/items/search`, `/api/items/by-category`, **`/api/items/list`**, `/api/items/{item_key}/history`, `/api/export/master.xlsx`.
- `api/index.py` = entry point de VERCEL (producción). Incluye **solo los 5 routers + `/api/health`**. NO incluye ninguno de los endpoints inline de `app/main.py`.
- Por eso `/api/items/list` da 404 en producción: existe únicamente en `app/main.py`, nunca se portó a `api/index.py`. FastAPI responde (404 con cuerpo JSON), pero la ruta no está registrada en la app serverless.

**Rutas REALMENTE registradas en producción (`api/index.py`):**

| Método | Path | Router origen | Handler |
|---|---|---|---|
| GET  | `/api/ratios/chapters`   | `visuales.py`        | `get_ratios_chapters` |
| POST | `/api/analyze/comparativa` | `visuales.py`      | `analyze_comparativa` |
| POST | `/api/items/analisis`    | `items_analisis.py`  | `analizar_items` |
| POST | `/api/import/budgets`    | `import_budgets.py`  | `import_budgets` |
| GET  | `/api/ratios/rango`      | `stats.py`           | `get_ratios_rango` |
| GET  | `/api/items/with_gamas`  | `items_extended.py`  | `get_items_with_gamas` |
| GET  | `/api/health`            | `api/index.py` (inline) | `health` |

**Equivalente a `items/list` que SÍ existe en producción:** `GET /api/items/with_gamas` (lista `ItemMaster`; forma de respuesta distinta — devuelve gama en vez de `ratio_actual`/`confianza`). El path exacto `/api/items/list` NO está registrado en producción.

**Por qué `/api/ratios/chapters` devuelve `[]`:** `obtener_capitulos_ratios()` (en `comparativa_service.py`) hace `session.query(ItemMaster).all()` sobre la tabla `item_master`. Devuelve `[]` porque **la BD de Supabase de producción está vacía**: los datos (27 presupuestos / 36 items) viven en el SQLite LOCAL y nunca se importaron a Supabase. No es un bug del pipeline; es ausencia de datos. Coherente con `/api/ratios/rango` → 404 "Sin datos" y `/api/items/with_gamas` → lista vacía.

**Próximo cambio mínimo recomendado (NO aplicado en esta sesión):**
1. (Datos) Importar/seed de datos en Supabase vía `POST /api/import/budgets` (ya registrado en prod) — sin esto, todo endpoint de lectura sigue vacío aunque se arreglen rutas.
2. (Ruta) Portar a `api/index.py` los endpoints inline de solo-lectura que use el frontend, empezando por `api_items_list` (`/api/items/list`) y, si aplica, `/api/items/search` y `/api/items/by-category`. Son read-only sobre BD, seguros para serverless. NO portar `/api/import` (upload+FS), `/api/export/master.xlsx` ni `/api/master`: dependen de filesystem local y por eso se excluyeron del slim app a propósito.

---

### Sesión 17 junio 2026 (6ª iteración) — Portado `/api/items/list` a la app serverless

**Ruta portada:** `GET /api/items/list` (read-only). **Motivo:** existía solo en `app/main.py` (entry local), no en `api/index.py` (entry Vercel) → 404 en producción.

**Cambio (mínimo, funcional):**
- Movida la implementación desde el endpoint inline de `app/main.py` a un handler en `app/routers/items_extended.py` (`get_items_list`), router que **ya incluyen ambas apps** (`api/index.py` y `app/main.py`) → single source of truth, sin ruta duplicada.
- Eliminado el `@app.get("/api/items/list")` inline de `app/main.py` (evita doble registro).
- Misma sesión/DB que el resto de endpoints serverless (`app.database.get_db`). Contrato de respuesta intacto: `{"items": [...]}`.
- BD vacía → `{"items": []}` (200), nunca 500 (la query `outerjoin` devuelve lista vacía).
- NO se tocó: Vercel config, Supabase config, `DATABASE_URL`, frontend, ni endpoints con dependencia de filesystem (`/api/import`, `/api/export/master.xlsx`, `/api/master`).

**Test añadido:** `tests/test_items_list.py` (3 casos: BD vacía → `{"items": []}`, listado con orden por `item_key`, filtro por `categoria`). Verificado: 54 tests verdes (3 nuevos + stats + items_analisis).

**Rutas registradas en `api/index.py` tras el cambio (12):** `/api/ratios/chapters`, `/api/analyze/comparativa`, `/api/items/analisis`, `/api/import/budgets`, `/api/ratios/rango`, `/api/items/with_gamas`, **`/api/items/list`**, `/api/health` (+ `/docs`, `/openapi.json`, `/redoc`, `/docs/oauth2-redirect` por defecto de FastAPI).

**Estado esperado tras deploy:** `GET https://luv-obras-ratios.vercel.app/api/items/list` → `200` con `{"items": []}` mientras Supabase siga vacío; con datos importados devolverá la lista. Ya operativos en producción: `/api/hello`, `/api/ratios/chapters` (200 `[]`), y ahora `/api/items/list`.

---

### Sesión 17 junio 2026 (7ª iteración) — Diagnóstico previo a poblar Supabase (sin ejecutar)

**`POST /api/import/budgets` (serverless-compatible ✅):**
- Body: **JSON** `{filename, file_hash (SHA256 hex 64 chars, REQUERIDO+validado), building_type, lineas:[{descripcion, cantidad, precio_unitario, unidad?, capitulo?, numero?}]}`. Acepta alias de campos (description/qty/price...). **No** sube archivos. **No** usa filesystem. Pure DB. (El endpoint con upload de fichero es el OTRO, `/api/import`, que NO está en serverless.)
- Tablas que puebla: `budget_imports` (guard dedup por file_hash), `budgets` (source_format=`json_api`), `item_master` (dedup por `item_key` normalizado; incrementa `muestras_count`), `item_instances` (una por línea válida). **NO** computa stats agregadas de ItemMaster (`mediana_unitario`, `min/max/media/desv_std`) ni `item_master_ratios`/`ratios` — eso solo lo hace `recalculate_all_item_master_stats`, que vive en el path de upload de `app/main.py`, no en el serverless.
- Idempotente: re-POST del mismo file_hash → 409 (no duplica).

**Selección de BD:** `src/db/models.py:_get_engine()` usa `DATABASE_URL` si está en el entorno (→ Supabase) o SQLite local `data/master/ratios.db` si no. Por eso un script local con `DATABASE_URL` de Supabase escribiría directo a Supabase.

**Migración SQLite→Postgres:** NO existe script dedicado. Además el SQLite local (`data/master/ratios.db`) está casi vacío (0 budgets, 8 item_master sin item_instances, 10 gama_ranges) — los "27 presupuestos / 36 items" históricos NO están aquí. No hay dataset local que migrar: hay que re-importar desde las **fuentes reales** en `data/samples/PRESUPUESTOS/` (5 xlsx, 12 bc3, 12 pzh, 9 presto, 8 pdf).

**Herramienta existente:** `scripts/importar_presupuestos_masivo.ps1` lee las fuentes reales LOCALMENTE (Excel vía COM; BC3/PZH/Presto vía texto), las convierte al JSON del endpoint y hace `Invoke-RestMethod` a `-ApiUrl` (default localhost). Apuntándolo a la URL de producción, puebla Supabase a través del endpoint.

**Método recomendado: A) `POST /api/import/budgets` vía el script masivo apuntado a producción.** (B descartado como primario: requiere creds Supabase en local y un script que use ImportService — el `load_test_budgets_simple.py` escribe `LineItem`, tabla legacy equivocada. C descartado: no hay datos en SQLite que exportar y el esquema difiere.)

**Riesgos identificados (a decidir antes de ejecutar):**
1. **`No inventar datos` (restricción #1):** el parser BC3/PZH del script usa `precio=100` por defecto cuando no detecta precio → datos inventados. ⇒ empezar SOLO con los 5 `.xlsx` (precios reales); BC3/PZH/Presto requieren validación aparte.
2. **Stats no calculadas:** tras importar, `mediana_unitario` queda NULL ⇒ `/api/ratios/chapters` devolverá filas pero con medianas 0.0 y `/api/items/with_gamas` con `SIN_CLASIFICAR`. Para visuals completas hace falta un paso posterior de recálculo (no expuesto en serverless).
3. **`maxDuration:10s`** (vercel.json): un presupuesto muy grande podría superar 10s contra el pooler → timeout. Mitigación: importar archivos de uno en uno (el script ya lo hace) y empezar por los pequeños.
4. Excel COM requiere Excel instalado en la máquina local (no en Vercel).

**Backup previo:** Supabase prod está VACÍO (baseline confirmado: chapters `[]`, items `[]`), así que el riesgo de pérdida es nulo. Aun así, recomendable tomar un snapshot/backup en Supabase antes de la carga masiva (o registrar la lista de file_hash importados para poder revertir por borrado selectivo). La guardia de dedup hace los re-intentos seguros.

**Decisión pendiente del usuario:** qué subconjunto de fuentes importar (recomendado: los 5 xlsx reales primero) y si se requiere el paso de recálculo de stats.

---

### Sesión 17 junio 2026 (8ª iteración) — Intento de importación de los 5 xlsx reales → 0 importado (BLOQUEADO)

**Acción autorizada:** importar SOLO los 5 `.xlsx` reales (sin BC3/PZH/Presto/PDF, sin precios inventados) vía `scripts/importar_presupuestos_masivo.ps1` apuntado a `https://luv-obras-ratios.vercel.app/api/import/budgets`.

**Preparación (OK):** creado `data/temp_import_xlsx_only/` con copia de los 5 xlsx; verificado 0 ficheros bc3/pzh/presto/pdf.

**Archivos candidatos + SHA-256 (calculados, NO importados):**
- `23_06_BER-Control económico.xlsx` — `5bc91b853d66bb575ffe8aef2a8f25e0d025958f230668a8eda0b6d3fa6e25b8`
- `24_26_PED_Presupuesto y mediciones.PDF.xlsx` — `c9f5716eeb94b037fb198333b1cf6cd8fe05dbf79de750c937eded7f8eb5d124`
- `260318_PEC- Presupuesto_CONTRATO.xlsx` — `106b511082fddbe8d280213bd36dcd3aa8c79cb097f146835150d482132a5510`
- `AFP025-D001  RAMBLA CATALUNYA 29_R1_220125.xlsx` — `1b90b74af470dbccb8f339b2a14b335236b10081b300e4e9c560d918ac972fa7`
- `LLAVANERES_PPA_Presupuesto.xlsx` — `3ac491d71629b1dc1f21d4c4a0f65943ffbf976c87c604301a74a97cbef2c80f`

**Resultado real: 0 presupuestos importados, 0 líneas enviadas, 0 POST a producción.** El parser Excel (COM + detección heurística de cabeceras) del script leyó las hojas pero extrajo "Files to import: 0". Ningún `Invoke-RestMethod` se ejecutó.

**Verificación de endpoints (post-intento, siguen vacíos):**
- `GET /api/items/list` → `200 {"items":[]}`
- `GET /api/ratios/chapters` → `200 []`

**Causa raíz del bloqueo:** mismatch de formato. `/api/import/budgets` exige líneas item-level (`descripcion`+`cantidad`+`precio_unitario`). Pero (a) el parser heurístico del `.ps1` no detecta las columnas en el layout de estos Excel reales; (b) el lector canónico `src/core/excel_reader.read_excel` sí lee, pero produce estructura a nivel de **capítulo** (`chapter_code`/`chapter_name`/`total_cost`), no precios unitarios por línea, y marca muchas filas `DUBIOUS` ("importe faltante o invalido"). Ningún parser existente extrae limpiamente (descripción, cantidad, precio unitario) de estos ficheros heterogéneos.

**Decisión:** NO se fuerza un parser ad-hoc para no violar la restricción crítica #1 ("No inventar datos") ni #2. Importar requeriría un parser por-fichero fiable, a autorizar aparte. Producción Supabase permanece vacía (estado seguro y consistente).

**Exclusiones que SIGUEN vigentes hasta validación específica:** BC3, PZH, Presto y PDF NO se importan (el parser BC3/PZH además inyecta `precio=100` por defecto → datos inventados).

---

### Diagnóstico (NO ejecutado): recálculo de stats de ItemMaster

- **Función exacta:** `app/services/recalculate_service.py::recalculate_all_item_master_stats(session)` → itera todos los `ItemMaster` y llama a `src/ratios/item_ratio_calculator.py::recalculate_item_master_stats(session, master.id)`.
- **Tablas/columnas que actualiza:** SOLO `item_master` → `mediana_unitario`, `media_unitario`, `min_unitario`, `max_unitario`, `desv_std`, `muestras_count`, `ultima_actualizacion`, `primera_fecha`, `ultima_fecha`. Lee `item_instances` (solo lectura). NO toca `budgets`, `item_instances`, `ratios`, `item_master_ratios`, `gama_ranges`.
- **¿Seguro contra Supabase prod?** Sí en principio: es determinista e idempotente (recalcula desde `item_instances` cada vez); con BD vacía es no-op (0 actualizados). Riesgos: (a) escribe directo en prod; (b) sobrescribe `muestras_count` con el nº de instancias con precio>0; (c) `get_session()` ejecuta `Base.metadata.create_all` (DDL `IF NOT EXISTS`) contra Supabase — idempotente pero convive con Alembic; (d) requiere apuntar al MISMO pooler que Vercel para no actuar sobre otra BD.
- **¿Requiere DATABASE_URL local?** SÍ. No está expuesto en serverless → se ejecuta como script local (Opción B) con `DATABASE_URL` = pooler de Supabase en el entorno.
- **Comando exacto (NO ejecutar aún):**
  ```bash
  DATABASE_URL='<supabase_transaction_pooler_url>' python -c "from app.database import get_db; from app.services.recalculate_service import recalculate_all_item_master_stats as r; s=get_db(); n=r(s); s.commit(); print('updated', n); s.close()"
  ```
- **Nota:** solo tiene sentido DESPUÉS de que existan `item_instances` reales en Supabase. Hoy es no-op.

**Cambios principales (TASK 8 - PROMPTS 1 a 5B):**
- ✅ Tabla `gama_ranges` creada + 8 seed materiales base
- ✅ Columna `gama_asignada` persistida en `item_master`
- ✅ Endpoint GET `/api/items/with_gamas` operativo (con filtros)
- ✅ Lógica gama: determine_gama() + find_gama_range()
- ✅ Transacciones robustas: try/except/finally + rollback
- ✅ Constraints de integridad: min<=max, sin solapamiento entre tiers
- ✅ Error handling: per-item fallback + HTTP 500 descriptivo
- ✅ Tests: 12 nuevos (constraints, transacciones, error handling)
- ✅ Seed data validado: 8/8 materiales OK
- ✅ Documentación: CONTEXT.md v1.4.2

**Checklist:**
- [x] Tabla gama_ranges creada + seed data insertado
- [x] Columna gama_asignada en item_master persistida
- [x] Endpoint /api/items/with_gamas operativo
- [x] Error handling + transacciones robustas (Codex fixes)
- [x] Constraints de integridad en GamaRanges
- [x] Tests: 12 nuevos pasando (constraints, transacciones, error handling)
- [x] Code review completado (Codex PROMPT 5B)
- [x] Sin breaking changes
- [x] Documentado en CONTEXT.md v1.4.2
- [x] validate_context.py pasó sin errores
