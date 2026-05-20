# LUV Obras Ratios

Sistema interno para importacion, parsing, validacion estructural y futura normalizacion de presupuestos, con trazabilidad completa desde las fuentes hasta capas intermedias y salida operativa final.

## Estado operativo actual (2026-05-20)

- Fase 8 cerrada tecnicamente.
- Fase 9.0 iniciada y vigente.
- Fase 9.1 cerrada documentalmente.
- Fase 9.2 cerrada tecnicamente: implementacion controlada del generador del Excel maestro vivo.
- Fase 9.3 cerrada tecnicamente: hardening con carga sintetica incremental, integridad referencial, snapshots, rollback y retencion.
- Fase 9.4 cerrada tecnicamente: validaciones de integridad extraidas a modulo dedicado.
- Fase 9.5 cerrada tecnicamente: idempotencia por run_id, checksum SHA-256 y rollback negativo.
- Fase 9.6-preview ejecutada: preview local segura con archivo real aislado.
- Fase 9.6-preview-fix ejecutada: salida operativa legible con `IMPORTED_BUDGET_VIEW`.
- Fase 9.6 formal cerrada documentalmente: contrato de ingesta real controlada `PREVIEW_ONLY -> OPERATIVE`.
- Fase 9.7 cerrada documentalmente: contrato de preservacion del presupuesto original y enlace con ratios progresivos.
- Fase 9.8 cerrada tecnicamente: scaffolding de preservacion y mapeo base implementados.
- Fase 9.9 cerrada tecnicamente: evaluador dry-run combinado implementado.
- Fase 9.10 cerrada tecnicamente: piloto dry-run con varios presupuestos reales aislados (sin promocion operativa).
- Fase 9.11 cerrada documentalmente: cierre post-piloto real dry-run y plan de endurecimiento previo a cualquier promocion.
- Fase 9.12 cerrada tecnicamente: endurecimiento de extraccion economica XLSX heterogenea y mapping `preserved -> COST_ITEMS`.
- Fase 9.13 cerrada tecnicamente: prueba real ampliada XLSX post-hardening.
- Fase 9.14 iniciada: salida profesional de presupuesto preservado para revision humana.
- Decision vigente: la salida principal del sistema sera un Excel maestro vivo, iterativo y actualizable (ADR-019).
- BC3: modulo avanzado ya operativo, no prioridad unica.
- Excel: lector integral y flujo multi-formato operativo.
- Presto/PZH: objetivo obligatorio por ruta tecnica evidenciada (export/herramienta), sin lectura nativa directa confirmada.
- Proxima fase recomendada: Fase 9.15 (cierre de aceptacion humana de salida profesional y decision de apertura BC3 preservado).

## Restricciones criticas activas

- No realizar ingesta masiva real.
- No actualizar master operativo en esta fase.
- No promocionar automaticamente preview a master operativo sin criterios de contrato.
- No calcular ratios finales.
- No consolidar importes finales.
- No normalizar categorias finales.
- No modificar RAW.
- No subir muestras reales ni reports/outputs sensibles.
- No subir Excels generados.
- Respetar contratos documentales de Fase 9.1/9.2/9.3/9.4/9.5/9.6/9.7/9.8/9.9/9.10/9.11/9.12/9.13 durante Fase 9.14.
- BC3 preservado queda fuera del alcance tecnico de Fase 9.14 salvo no-regresion documental.

## Referencias de estado

- `CONTEXT.md`
- `ADRs.md` (ADR-019)
- `docs/decisions/phase_8_presto_pzh_support_strategy.md`
- `docs/decisions/phase_9_0_live_excel_master_output_definition.md`
- `docs/decisions/phase_9_10_real_dry_run_pilot.md`
- `docs/decisions/phase_9_11_post_pilot_hardening_plan.md`
- `docs/decisions/phase_9_12_xlsx_economic_extraction_and_mapping_hardening.md`
- `docs/decisions/phase_9_13_xlsx_real_dry_run_generalization.md`
- `docs/decisions/phase_9_14_professional_budget_review_output.md`

## Comandos base

```bash
python scripts/validate_context.py
python scripts/inspect_repo.py
python scripts/run_real_dry_run_pilot.py --files data/samples/<sanitized_selection> --output-dir outputs/live_excel_master/real_dry_run
python scripts/run_xlsx_generalization_dry_run.py --files data/samples/<xlsx_1> data/samples/<xlsx_2> --output-dir outputs/live_excel_master/xlsx_generalization
pytest
```
