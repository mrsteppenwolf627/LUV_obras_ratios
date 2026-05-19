# LUV Obras Ratios

Sistema interno para importacion, parsing, validacion estructural y futura normalizacion de presupuestos, con trazabilidad completa desde las fuentes hasta capas intermedias y salida operativa final.

## Estado operativo actual (2026-05-19)

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
- Fase 9.8 iniciada: implementacion incremental de preservacion y mapeo hacia `COST_ITEMS`.
- Decision vigente: la salida principal del sistema sera un Excel maestro vivo, iterativo y actualizable (ADR-019).
- BC3: modulo avanzado ya operativo, no prioridad unica.
- Excel: lector integral y flujo multi-formato operativo.
- Presto/PZH: objetivo obligatorio por ruta tecnica evidenciada (export/herramienta), sin lectura nativa directa confirmada.
- Proxima fase recomendada: Fase 9.9 (endurecimiento del evaluador dry-run combinado y reglas avanzadas de mapeo).

## Restricciones criticas activas

- No realizar ingesta masiva real.
- No promocionar automaticamente preview a master operativo sin criterios de contrato.
- No calcular ratios finales.
- No consolidar importes finales.
- No normalizar categorias finales.
- No modificar RAW.
- No subir muestras reales ni reports/outputs sensibles.
- No subir Excels generados.
- Respetar contratos documentales de Fase 9.1/9.2/9.3/9.4/9.5/9.6/9.7 durante Fase 9.8.

## Referencias de estado

- `CONTEXT.md`
- `ADRs.md` (ADR-019)
- `docs/decisions/phase_8_presto_pzh_support_strategy.md`
- `docs/decisions/phase_9_0_live_excel_master_output_definition.md`

## Comandos base

```bash
python scripts/validate_context.py
python scripts/inspect_repo.py
pytest
```
