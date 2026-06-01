# LUV Ratios - Project Status

**Fecha:** 1 de junio de 2026
**Estado:** FUNCIONAL - en desarrollo activo
**Version:** 1.1.0
**Ciclo:** snapshot funcional de `visuales` verificado, con roadmap principal anclado en Fase 9.20

---

## Completado en el snapshot actual

### Backend (FASE 1-3 de visuales)

- [x] Schema de `ratios` ampliado con `percentil_25`, `percentil_75` y `std_dev`
- [x] Migraciones e indices para endpoints de visualizacion
- [x] Endpoint `GET /api/ratios/chapters` operativo con cache in-memory
- [x] Endpoint `POST /api/analyze/comparativa` operativo
- [x] CORS y proxy de desarrollo alineados para trabajo local
- [x] Router de visuales registrado en `app/main.py`
- [x] `pytest`: 528 tests pasando

### Frontend (FASE 4 de visuales)

- [x] Pagina `frontend/src/pages/Visuales.tsx` implementada
- [x] 3 componentes: `RangoValidacion`, `TablaConfiabilidad`, `ComparativaDesviacion`
- [x] Cliente API `frontend/src/api/visuales.ts`
- [x] Hook `frontend/src/hooks/useVisuales.ts`
- [x] Tests de integracion y componente en Vitest
- [x] `npm test`: 6 tests pasando

### Infraestructura local verificada

- [x] Backend levantado en `http://localhost:8000`
- [x] Frontend Vite levantado en `http://localhost:5173`
- [x] `python scripts/validate_context.py`: OK
- [x] `python scripts/inspect_repo.py`: OK

---

## Estado actual

### Subsistema visuales

- Funcional y arrancable localmente.
- La API backend responde y la UI tiene infraestructura local operativa.
- La validacion manual final de UX en navegador sigue siendo recomendable cuando se retome revision funcional.

### Datos

- Presupuestos importados en la BD local: 6
- Capitulos consolidados en la documentacion de la linea visuales: 49
- Confiabilidad actual: limitada por bajo volumen de datos historicos

### Producto principal

- El producto principal sigue siendo el Excel maestro vivo.
- La fase canonica vigente del roadmap principal es la Fase 9.20.
- La linea `/visuales` es soporte funcional complementario y no reemplaza el contrato del workbook.

---

## Metricas

| Metrica | Valor | Estado |
|---------|-------|--------|
| Backend tests | 528 | OK |
| Frontend tests | 6 | OK |
| Endpoints visuales | 2 | OK |
| Componentes visuales | 3 | OK |
| Backend local | `localhost:8000` | OK |
| Frontend local | `localhost:5173` | OK |
| Solidez estadistica | limitada por `N` bajo | WARNING |

---

## Bloqueadores y pendientes

1. Verificar manualmente en navegador la experiencia final de `http://localhost:5173/visuales`.
2. Importar mas presupuestos si se quiere mejorar utilidad estadistica real.
3. Mantener sincronia documental entre el snapshot de visuales y la linea canonica de Fase 9.x.

---

## Proxima sesion sugerida

1. Abrir `/visuales` y confirmar carga correcta de las tres tabs con DevTools.
2. Revisar si el negocio necesita priorizar mas la linea de visuales o seguir concentrando esfuerzo en el workbook.
3. Continuar cierre verificable de Fase 9.20 y preparar la apertura de Fase 9.21 cuando corresponda.

---

## Referencia Git al inicio de esta actualizacion

- Rama: `main`
- Estado previo al commit: limpio, `ahead 6` respecto a `origin/main`
- Ultimos commits antes de esta actualizacion:
  - `c83b184` `Pause: Project state snapshot before resuming later`
  - `58aa365` `Fix: Add Vercel origin to CORS allow_origins`
  - `23a7386` `Feat: API integration and code review for visuales (via Codex)`
  - `4d92d9b` `Feat: Add database indexes and optimization (FASE 3)`
  - `887f4cc` `Feat: Add visualization endpoints with cache (FASE 2)`
