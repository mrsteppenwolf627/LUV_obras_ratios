# ADRs: Architecture Decision Records

Registro de decisiones arquitectonicas del proyecto.

**Proyecto:** LUV Ratios
**Actualizado:** 1 de junio de 2026
**Estado del producto:** funcional, con doble linea activa:

- Linea canonica: Excel maestro vivo y trazable.
- Linea complementaria: backend/frontend de visuales para consulta y comparativa.

## Estado operativo de referencia

- El estado canonico del producto sigue anclado en el roadmap multi-fase del Excel maestro vivo.
- La Fase 9.20 sigue vigente como fase principal del producto.
- El 1 de junio de 2026 se verifico ademas el subsistema `visuales`:
  - backend local operativo;
  - frontend Vite operativo;
  - `pytest`: 528 tests pasando;
  - `npm test` en frontend: 6 tests pasando.
- Este snapshot funcional no sustituye el roadmap principal; lo complementa.

## Indice ADR

- ADR-001 a ADR-008: principios fundacionales de trazabilidad y gobierno del dato.
- ADR-013 a ADR-018: decisiones de parsing/normalizacion multi-formato y soporte Presto/PZH.
- ADR-019: Excel maestro vivo como salida principal del sistema.
- ADR-020: identidad inequivoca del artefacto XLSX entregado para revision humana.
- ADR-021: backend stateless con cache in-memory para visuales.
- ADR-022: calculo de estadisticas y comparativas en backend.
- ADR-023: confiabilidad determinada por numero de muestras.
- ADR-024: proxy de Vite para desarrollo local de `/api/*`.
- ADR-025: hook custom `useVisuales` y estado local para la UI de visuales.

## ADR-001 a ADR-008: Principios fundacionales

**Estado:** vigentes

**Resumen**

- ADR-001: reparto de responsabilidades por herramientas.
- ADR-002: el dato bruto nunca se sobrescribe.
- ADR-003: separacion entre RAW, normalizado, validacion, calculo y exportacion.
- ADR-004: no se actualizan ratios sin validacion.
- ADR-005: prioridad de fuentes estructuradas sobre PDF.
- ADR-006: trazabilidad obligatoria extremo a extremo.
- ADR-007: exclusion sin borrado del historico.
- ADR-008: no calcular ratios definitivos sin superficie base definida.

**Impacto**

- Siguen condicionando cualquier cambio posterior del producto.
- Ninguna fase nueva puede ignorar estos principios sin ADR de reemplazo.

## ADR-013 a ADR-018: Parsing, normalizacion y estrategia multi-formato

**Estado:** vigentes

**Resumen**

- ADR-013: extractor diagnostico BC3 antes de parser definitivo.
- ADR-014: diseno preliminar de parser BC3 antes de importar al master.
- ADR-015: normalizacion intermedia BC3 en capa separada.
- ADR-016: estrategia multi-formato con prioridad operativa para Excel y Presto/PZH.
- ADR-017: contrato comun multi-formato para lectura y normalizacion intermedia.
- ADR-018: soporte obligatorio Presto/PZH solo mediante ruta tecnica evidenciada.

**Impacto**

- El sistema no debe forzar lectura nativa no evidenciada.
- BC3 sigue soportado, pero no monopoliza el roadmap.
- Excel y artefactos derivados siguen siendo primera clase en el producto.

## ADR-019: Excel maestro vivo como salida principal del sistema

**Status:** CONGELADA
**Fecha:** 18 de mayo de 2026
**Actualizada:** 1 de junio de 2026

**Decision**

- La salida principal del sistema es un Excel maestro vivo.
- Ese Excel es iterativo, actualizable y trazable.
- No se sustituye por una base de datos externa ni por un informe estatico salvo nueva ADR.
- Cualquier API o UI interna es complementaria al Excel maestro, no su reemplazo.

**Por que**

- El artefacto operativo del dominio es el workbook vivo.
- La trazabilidad y la revision manual encajan mejor en ese formato.
- El negocio necesita un producto manipulable y auditable, no solo almacenamiento.

**Impacto**

- Toda nueva funcionalidad debe respetar el contrato del workbook.
- La linea `/visuales` sirve para consulta y apoyo, no redefine el producto principal.

## ADR-020: Identidad inequivoca del artefacto XLSX entregado para revision humana

**Status:** CONGELADA
**Fecha:** 28 de mayo de 2026
**Actualizada:** 1 de junio de 2026

**Decision**

- Archivo generado = archivo validado = archivo exportado = archivo revisado.
- Las entregas de revision deben usar carpeta nueva por fase y nombres no reutilizables.
- Cada entrega debe ir acompanada de manifest con SHA-256 y metadatos minimos.
- La validacion debe reabrir el archivo desde disco, no solo validar el workbook en memoria.

**Por que**

- Se detectaron confusiones por reutilizacion de nombres de salida entre fases.
- La trazabilidad del artefacto final tiene que ser verificable y no depender de memoria humana.

**Impacto**

- La entrega humana de outputs XLSX queda gobernada por hashes y manifests.
- Los outputs siguen fuera de Git.

## ADR-021: Backend stateless con cache in-memory para visuales

**Status:** CONGELADA
**Fecha:** 27 de mayo de 2026
**Actualizada:** 1 de junio de 2026

**Decision**

- El endpoint `GET /api/ratios/chapters` usa cache in-memory con TTL de 1 hora.
- El backend de visuales se mantiene stateless en lo funcional; no persiste sesiones de UI.
- La cache se invalida cuando una importacion recalcula ratios.

**Por que**

- Reduce latencia para consultas repetidas.
- Mantiene el backend simple para entorno local y despliegue ligero.
- Evita introducir Redis u otra infraestructura que hoy no aporta valor proporcional.

**Impacto**

- La coherencia del dato depende de invalidar cache tras importaciones.
- La UI no necesita coordinar cache de negocio compleja.

## ADR-022: Calculo de estadisticas y comparativas en backend

**Status:** CONGELADA
**Fecha:** 27 de mayo de 2026
**Actualizada:** 1 de junio de 2026

**Decision**

- El backend calcula min, max, mediana, percentiles, desviacion y comparativa economica.
- El frontend solo renderiza y orquesta interaccion.
- Las reglas de confiabilidad y analisis viven del lado servidor.

**Por que**

- Hay una unica fuente de verdad.
- La logica queda cubierta por Pytest.
- Se reduce el riesgo de divergencia entre UI y API.

**Impacto**

- `GET /api/ratios/chapters` devuelve datos listos para visualizacion.
- `POST /api/analyze/comparativa` devuelve analisis cerrado para la UI.

## ADR-023: Confiabilidad determinada por numero de muestras

**Status:** CONGELADA
**Fecha:** 27 de mayo de 2026
**Actualizada:** 1 de junio de 2026

**Decision**

- La solidez del ratio se determina por el numero de muestras disponibles.
- La UI expresa ese estado como confiabilidad legible para usuario interno.
- Un sistema funcional con `N=1` sigue siendo util para exploracion, pero no implica referencia estadistica fuerte.

**Por que**

- La interpretacion depende mas del volumen de evidencia que de la presentacion visual.
- Evita sobrerreclamar precision cuando el corpus aun es pequeno.

**Impacto**

- La mejora real del sistema requiere importar mas presupuestos, no solo mas interfaz.
- La documentacion debe recordar siempre el limite actual de solidez.

## ADR-024: Proxy de Vite para desarrollo local de `/api/*`

**Status:** CONGELADA
**Fecha:** 28 de mayo de 2026
**Actualizada:** 1 de junio de 2026

**Decision**

- En desarrollo, Vite proxea `/api/*` al backend local.
- El frontend trabaja con rutas relativas en lugar de URLs backend hardcodeadas.

**Por que**

- Reduce friccion de CORS y configuracion local.
- Mantiene una experiencia uniforme entre componentes y tests de integracion.

**Impacto**

- Si cambia el destino del backend local, hay que revisar `frontend/vite.config.ts`.
- La validacion manual en navegador debe considerar cache/restart de Vite cuando se cambia el proxy.

## ADR-025: Hook custom `useVisuales` y estado local para la UI de visuales

**Status:** CONGELADA
**Fecha:** 28 de mayo de 2026
**Actualizada:** 1 de junio de 2026

**Decision**

- La UI de visuales usa un hook custom `useVisuales`.
- El estado se resuelve de forma local en React para esta feature; no se congelo un store global adicional.
- La capa API se mantiene separada en `frontend/src/api/visuales.ts`.

**Por que**

- La complejidad actual de la pantalla no justifica introducir otra capa de estado.
- El patron hook + cliente API es suficiente, testeable y facil de seguir.

**Impacto**

- La feature puede evolucionar sin acoplarse a un store global prematuro.
- Si la superficie funcional crece, se podra abrir una ADR futura para estado compartido mas amplio.

## Como proponer cambios a ADRs

1. No cambiar una ADR congelada sin documentar una ADR de reemplazo o supersesion.
2. Si la realidad del codigo cambia, actualizar primero la implementacion y luego la ADR correspondiente.
3. Mantener `CONTEXT.md`, `PROJECT_STATUS.md` y `README.md` sincronizados con estas decisiones.
