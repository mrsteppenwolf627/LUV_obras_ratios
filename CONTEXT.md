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

- Pausa operativa documentada: 2026-05-28.
- Estado de sesion al pausar: snapshot documental creada en `PROJECT_STATUS.md` para la linea Backend FASE 1-3 + Frontend FASE 4 (`/visuales`).
- Nota de pausa: backend API en `localhost:8000` verificado por curl, frontend `/visuales` pendiente de validacion final en navegador y puede requerir hard-refresh de Vite.
- Condicion funcional de datos de ratios en esta linea: 49 capitulos consolidados, todos con `N=1` (`MUY_DEBIL`), por lo que la solidez estadistica sigue bloqueada por falta de mas presupuestos importados.
- Proxima reanudacion sugerida para esta linea: validar conexion frontend API, confirmar carga correcta de las 3 tabs visuales e incrementar volumen de presupuestos reales antes de evaluar solidez.
- Fecha de consolidacion documental: 2026-05-21.
- Fase 8: cerrada tecnicamente.
- Fase 9.0: iniciada y vigente.
- Fase 9.1: cerrada documentalmente.
- Fase 9.2: cerrada tecnicamente.
- Fase 9.3: cerrada tecnicamente.
- Fase 9.4: cerrada tecnicamente.
- Fase 9.5: cerrada tecnicamente.
- Fase 9.6-preview: ejecutada (segura metodologicamente, insuficiente como salida operativa).
- Fase 9.6-preview-fix: ejecutada (hoja operativa `IMPORTED_BUDGET_VIEW` integrada en preview).
- Fase 9.6 formal: cerrada documentalmente (contrato PREVIEW_ONLY -> OPERATIVE definido).
- Fase 9.7: cerrada documentalmente (contrato de preservacion del presupuesto original y enlace con ratios progresivos).
- Fase 9.8: cerrada tecnicamente.
- Fase 9.9: cerrada tecnicamente.
- Fase 9.10: cerrada tecnicamente (piloto real dry-run ejecutado, sin promocion operativa).
- Fase 9.11: cerrada documentalmente (cierre post-piloto real dry-run y plan de endurecimiento).
- Fase 9.12: cerrada tecnicamente (endurecimiento de extraccion economica XLSX heterogenea y mapping preserved -> COST_ITEMS).
- Fase 9.13: cerrada tecnicamente (prueba real ampliada XLSX post-hardening y validacion de generalizacion).
- Fase 9.14: cerrada tecnicamente (hoja profesional inicial + trazabilidad separada).
- Fase 9.15: cerrada tecnicamente (profesionalizacion global del workbook y formato completo del Excel maestro).
- Fase 9.16: cerrada tecnicamente (correccion semantica inicial de `BUDGET_REVIEW_001` e `INDEX` profesional).
- Fase 9.17: cerrada tecnicamente (auditoria de outputs reales XLSX y enforcement del pipeline oficial).
- Fase 9.18: cerrada tecnicamente (clasificacion semantica de hojas XLSX y vistas profesionales adaptativas por tipo de hoja).
- Fase 9.19: reportada como COMPLETE por Codex (formulas adaptativas, navegacion profesional y recalibracion del evaluador por tipo semantico XLSX).
- Fase 9.20: iniciada (auditoria forense de artefactos XLSX finales y entrega inequivoca para revision humana).
- Discrepancia critica detectada (2026-05-21): revision manual reportaba archivos `xlsx_generalization_001/002_preview.xlsx` con contenido de fase 9.9 (plantilla clasica, HYPERLINK, COST_ITEMS contaminado), incompatible con el reporte 9.19 de Codex.
- Hallazgo de auditoria 9.20: los artefactos reales en disco de 001/002 SI son fase 9.19 validos (phase=9.19, abren en INDEX, vistas adaptativas, COST_ITEMS limpio, validacion post-generacion PASSED). El usuario abria copias obsoletas/equivocadas por reutilizacion de nombres entre fases y posible lag de sincronizacion.
- Objetivo 9.20: garantizar identidad entre archivo generado = validado = exportado = revisado mediante carpeta nueva, nombres inequivocos, manifest con SHA-256 y validacion post-guardado reabriendo desde disco.
- Decision vigente: la salida principal del sistema es un Excel maestro vivo, iterativo y actualizable (ADR-019 y `docs/decisions/phase_9_0_live_excel_master_output_definition.md`).
- Decision de direccion 9.7: el output debe conservar una logica equivalente al input cuando sea posible.
- Decision de direccion 9.7: el Excel maestro puede anadir tantas hojas nuevas como sean necesarias para preservar y trazar.
- Decision de direccion 9.7: la capa preservada/operativa y la capa tecnica/normalizada deben coexistir.
- Decision vigente 9.8: se permite crear tantas hojas nuevas como sean necesarias para trazabilidad, claridad y utilidad operativa.
- Decision de producto 9.14: la salida visual profesional es obligatoria.
- Decision de producto 9.14: la capa tecnica no sustituye a la hoja profesional de presupuesto.
- Decision de producto 9.14: las columnas tecnicas deben quedar ocultas o separadas en hojas de trazabilidad.
- Decision de producto 9.15: no basta con profesionalizar solo `BUDGET_REVIEW_*`.
- Decision de producto 9.15: todas las hojas visibles deben tener presentacion cuidada y navegable.
- Decision de producto 9.15: hojas internas demasiado tecnicas pueden moverse al final y/o ocultarse manteniendo auditoria.
- Diagnostico de integracion 9.15 (2026-05-21): algunos previews en `xlsx_generalization` conservaban `activeTab/firstSheet` apuntando a hojas tecnicas pese a tener orden correcto; se corrige para abrir siempre en `INDEX`.
- Problema confirmado por usuario al inicio de 9.18: el pipeline seguia forzando una plantilla clasica unica en hojas de naturaleza distinta (resumen, espacios, comparativas, metadata y calculo).
- Problema confirmado por usuario al inicio de 9.18: `xlsx_generalization_001_preview.xlsx` mezclaba hojas `Datos` + `Espacios` e inventaba jerarquias/subtotales sin evidencia fiable.
- Problema confirmado por usuario al inicio de 9.18: `xlsx_generalization_002_preview.xlsx` (comparativa) se interpretaba como presupuesto clasico, moviendo `Cap.` a cantidad y `Importe equivalente` a codigo.
- Decision 9.18: clasificar semanticamente cada hoja XLSX antes de construir vistas profesionales y evitar mezclas entre tipos incompatibles.
- Problema confirmado al inicio de 9.19: en vistas comparativas se heredaban formulas de coordenadas antiguas (ej. `=+H4-F4`) que no corresponden a columnas de la vista profesional.
- Problema confirmado al inicio de 9.19: formulas con nombres definidos no preservados podian quedar activas en vistas profesionales y producir errores al abrir en Excel.
- Problema confirmado al inicio de 9.19: INDEX/HOME debian orientar mejor la navegacion a vistas adaptativas y el evaluador penalizaba casos no clasicos con reglas de presupuesto clasico.
- BC3: modulo avanzado operativo, no prioridad unica.
- Excel: lector integral operativo y contrato multi-formato vigente.
- Presto/PZH: obligatorio en roadmap mediante ruta tecnica evidenciada (export/herramienta equivalente), sin lectura nativa directa confirmada.

## Fase vigente

- Fase vigente: 9.20 - auditoria forense de artefactos XLSX finales y entrega inequivoca para revision humana.
- Estado: en implementacion tecnica.
- Objetivo: eliminar la discrepancia entre outputs reportados y outputs revisados garantizando que el archivo generado = validado = exportado = revisado = abierto por el usuario.
- Alcance: inventario forense de XLSX, generacion en carpeta nueva inequivoca (`outputs/live_excel_master/manual_review_phase_9_20/`), nombres `phase_9_20_review_###.xlsx`, manifest con SHA-256, validacion post-guardado reabriendo desde disco, tests de integridad de entrega.
- No es una fase para mejorar el Excel: es para garantizar trazabilidad del artefacto final.
- Resultado esperado: dos archivos exactos para el usuario, ambos phase=9.20, ambos abren en INDEX, ambos validados desde disco, ambos con SHA-256 reportado.
- Fuera de alcance: nuevas features, BC3, ratios finales, promocion operativa, modificacion de RAW.
- Restriccion metodologica: trabajo en modo `PREVIEW_ONLY`/dry-run, trazable y reversible, sin promocion automatica ni ingesta real operativa.

## Proxima fase recomendada

- Proxima fase: 9.21 - consolidacion de traduccion de formulas avanzadas (nombres definidos/rangos) y cierre de no-regresion visual/semantica ampliada antes de abrir BC3 preservado.
- Condicion: mantener contrato 9.6-9.20 sin habilitar promocion automatica.

## Restricciones activas (fase 9.20)

- No promocion automatica a master operativo.
- No actualizacion del master operativo.
- Promocion solo explicita, trazada y bloqueable.
- No ingesta real operativa masiva.
- No calculo de ratios finales.
- No normalizacion final de categorias.
- No consolidacion definitiva de importes.
- No modificar RAW.
- No subir archivos reales ni muestras reales.
- No subir Excels generados.
- No subir reports/outputs sensibles.
- No abrir BC3 en esta fase.
- No abrir Presto/PZH en esta fase.
- No disenar interfaz, dashboard ni flujo UX en esta fase.
- BC3 preservado queda fuera de alcance de esta fase salvo no-regresion documental.
- Mantener compatibilidad con contratos 9.1/9.2/9.3/9.4/9.5/9.6/9.7/9.8/9.9/9.10/9.11/9.12/9.13/9.14/9.15/9.16.

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

- Implementar clasificacion semantica por hoja XLSX (`BUDGET_CLASSIC`, `BUDGET_SUMMARY`, `SPACE_BREAKDOWN`, `COMPARISON_TABLE`, `FORMULA_CALCULATION_SHEET`, `AUXILIARY`, `METADATA`, `UNKNOWN`).
- Generar vistas profesionales adaptativas por hoja semantica sin mezcla entre hojas incompatibles.
- Endurecer validacion post-generacion para bloquear mezclas, comparativas mal proyectadas y metadata tratada como partidas/importes.

### P1

- Repetir dry-run real local con IDs sanitizados y comparar evidencia objetiva pre/post-fix.
- Recalibrar umbrales preliminares solo tras muestra ampliada.

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
- Fase 9.5: idempotencia por run_id, checksum SHA-256 y rollback negativo.
- Fase 9.6-preview: salida local con archivo real aislado (segura, no operativa suficiente).
- Fase 9.6-preview-fix: salida preview con capa operativa legible (`IMPORTED_BUDGET_VIEW`).
- Fase 9.6 formal: contrato PREVIEW_ONLY -> OPERATIVE con criterios de promocion/bloqueo/revision.
- Fase 9.7: contrato de preservacion del presupuesto original (Opcion C: hojas visibles + indice/mapa tecnico).
- Fase 9.8: scaffolding de preservacion implementado (`PRESERVED_BUDGETS_INDEX`, `PRESERVED_BUDGET_SHEETS`, `PRESERVED_TO_COST_ITEMS_MAP` y hojas `PRES_*` visibles).
- Fase 9.9: evaluador dry-run combinado implementado (`OPERATIVE_CANDIDATE`, `PROMOTION_BLOCKED`, `MANUAL_REVIEW_REQUIRED`, `PRESERVATION_INCOMPLETE`).
- Fase 9.10: piloto real dry-run multi-archivo ejecutado y cerrado tecnicamente (1 candidato operativo XLSX, 2 bloqueos controlados).
- Fase 9.11: cierre documental post-piloto y plan de endurecimiento (Linea A XLSX y Linea B mapping priorizadas).
- Fase 9.12: endurecimiento tecnico de extraccion economica XLSX heterogenea y mapping preserved -> COST_ITEMS.
- Fase 9.13: prueba real ampliada XLSX post-hardening y validacion de generalizacion (cerrada tecnicamente).
- Fase 9.14: salida profesional inicial de presupuesto preservado (cerrada tecnicamente).
- Fase 9.15: profesionalizacion global de todo el workbook (cerrada tecnicamente).
- Fase 9.16: correccion semantica de `BUDGET_REVIEW_001` e `INDEX` profesional (cerrada tecnicamente).
- Fase 9.17: auditoria de outputs reales XLSX y correccion integral de pipeline oficial (iniciada).

## Fuentes canonicas de estado actual

- `ADRs.md` (ADR-019).
- `docs/decisions/phase_8_presto_pzh_support_strategy.md`.
- `docs/decisions/phase_9_0_live_excel_master_output_definition.md`.
- `docs/decisions/phase_9_1_live_excel_master_generator_design.md`.
- `docs/decisions/phase_9_2_live_excel_master_generator_implementation.md`.
- `docs/decisions/phase_9_3_live_excel_master_hardening.md`.
- `docs/decisions/phase_9_4_live_excel_integrity_validation_refactor.md`.
- `docs/decisions/phase_9_10_real_dry_run_pilot.md`.
- `docs/decisions/phase_9_11_post_pilot_hardening_plan.md`.
- `docs/decisions/phase_9_12_xlsx_economic_extraction_and_mapping_hardening.md`.
- `docs/decisions/phase_9_13_xlsx_real_dry_run_generalization.md`.
- `docs/decisions/phase_9_14_professional_budget_review_output.md`.
- `docs/decisions/phase_9_15_workbook_wide_professional_formatting.md`.
- `docs/decisions/phase_9_16_budget_review_semantic_correction.md`.
- `docs/decisions/phase_9_17_xlsx_output_pipeline_audit_and_fix.md`.
- `docs/decisions/phase_9_18_xlsx_sheet_semantic_classification_and_adaptive_reviews.md`.
- `docs/decisions/phase_9_19_adaptive_formula_translation_navigation_and_evaluator_calibration.md`.
- `README.md` (resumen operativo).

## 🎯 HITO 1: Core + Master Excel

Estado: **COMPLETADO** (2026-05-26)
Tareas (9 totales, ~23 horas)

1. **Schema SQLite** (2h) ✅
   - budgets, line_items, chapters, ratios, validations

2. **Excel Reader** (3h) ✅
   - Detecta capítulos (C01, C02...)
   - Extrae importes

3. **BC3 Reader** (3h) ✅
   - Lee formato Presto .bc3
   - Detecta capítulos en líneas ~C

4. **Normalizer** (2h) ✅
   - Convierte Excel/BC3 a JSON común

5. **Auditor** (2h) ✅
   - SHA-256 hashes
   - JSON logs

6. **Import.py** (3h) ✅
   - Orquesta todo: lectura → validación → BD → ratios → MASTER EXCEL → archivo

7. **Calculator** (2h) ✅
   - Calcula mediana €/m² por capítulo

8. **Excel Master Generator** (4h) ✅ CRÍTICA
   - Genera las 5 hojas del master
   - Inserta ratios actualizados
   - Crea inventario

9. **Tests** (2h) ✅
   - Coverage >80%
   - 36 tests verdes

## Historial

| Fecha | Hito | Nivel de completitud |
|-------|------|----------------------|
| 2026-05-26 | HITO 1 COMPLETADO (9 tareas, 36 tests ✅) | 3 (Operativo) |

## ✅ Éxito de HITO 1 = ...

```bash
# 1. Importar presupuesto
python scripts/import.py data/samples/proyecto_001/22_10_SCE_Datos.xlsx --confirm --surface 450 --type residential
# ✅ Master generado

# 2. Importar otro
python scripts/import.py "data/samples/proyecto_001/P22-143.1 Pressupost Sant Celoni.bc3" --confirm
# ✅ Master actualizado con ratios refinados

# 3. Tests
pytest tests/ --cov
# ✅ 36/36 tests passing, 85%+ coverage - HITO 1 COMPLETADO

# 4. Abrir master
start data/master/master_latest.xlsx
# ✅ VES: INDEX (2 presupuestos), RATIOS (medianas), AUDIT (trazabilidad)
```

## Reglas de actualización

- `CONTEXT.md` debe actualizarse despues de cada tarea relevante.
- Cada decision arquitectonica nueva o cambio sustancial debe registrarse en `ADRs.md`.
- El estado y backlog deben reflejar el avance real del repositorio.
- No se deben cerrar tareas sin evidencia verificable (codigo, tests, o documentacion).
- La seccion "Estado operativo vigente (canonico)" prevalece sobre bloques historicos.
