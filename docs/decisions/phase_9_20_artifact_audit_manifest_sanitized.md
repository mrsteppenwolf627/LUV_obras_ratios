# Fase 9.20 - Manifest sanitizado de artefactos de revision humana

Version sanitizada del manifest local `MANIFEST_phase_9_20.json`. No incluye rutas absolutas
ni inputs reales. Los SHA-256 corresponden a la corrida local del 2026-05-21 con
`data/samples/20_07_GAV_Datos.xlsx` y `data/samples/exc.xlsx`. Cada regeneracion produce un
SHA-256 nuevo; el manifest local de la corrida es la fuente de verdad para verificar identidad.

- phase: `9.20`
- auto_promotion_enabled: `false`

## PHASE_9_20_REVIEW_001

- input_id: `SANITIZED_INPUT_001`
- output_relative_path: `outputs/live_excel_master/manual_review_phase_9_20/phase_9_20_review_001.xlsx`
- sha256: `84dff621e01a1fba7f172d8a13be9b47231478c16e92e719990d1a7da2083409`
- size_bytes: `64033`
- readme_phase: `9.20`
- active_sheet: `INDEX`
- required_sheets_present: `true`
- adaptive_views_present: `true`
- home_sheets: `BUDGET_REVIEW_001`
- adaptive_views: `BUDGET_REVIEW_001_Datos`, `BUDGET_REVIEW_001_Espacios`
- trace_sheets: `BUDGET_REVIEW_TRACE_001`
- validation_status: `PASSED`
- human_review_start_sheet: `INDEX`

## PHASE_9_20_REVIEW_002

- input_id: `SANITIZED_INPUT_002`
- output_relative_path: `outputs/live_excel_master/manual_review_phase_9_20/phase_9_20_review_002.xlsx`
- sha256: `4dee5fd6838d49297e5998be49e56404210f38d37d99e65769943060a71e73d2`
- size_bytes: `47295`
- readme_phase: `9.20`
- active_sheet: `INDEX`
- required_sheets_present: `true`
- adaptive_views_present: `true`
- home_sheets: `BUDGET_REVIEW_001`
- adaptive_views: `BUDGET_REVIEW_001_Hoja1` (COMPARISON_TABLE)
- trace_sheets: `BUDGET_REVIEW_TRACE_001`
- validation_status: `PASSED`
- human_review_start_sheet: `INDEX`

## Como verificar la identidad (usuario)

1. Abrir solo: `outputs/live_excel_master/manual_review_phase_9_20/phase_9_20_review_001.xlsx`
   y `..._002.xlsx`.
2. Confirmar que abren en `INDEX` y que `README_MASTER.phase = 9.20`.
3. (Opcional) Recalcular el SHA-256 del archivo en disco y compararlo con el del manifest local
   de su corrida (PowerShell: `Get-FileHash -Algorithm SHA256 <archivo>`).
