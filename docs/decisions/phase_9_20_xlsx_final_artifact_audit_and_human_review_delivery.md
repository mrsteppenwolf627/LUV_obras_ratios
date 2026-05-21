# Fase 9.20 - Auditoria forense de artefactos XLSX finales y entrega inequivoca para revision humana

## Objetivo

Eliminar definitivamente la discrepancia repetida entre los outputs XLSX que el pipeline
reporta generar y los archivos que el usuario abre y revisa manualmente. La fase no mejora
el Excel: garantiza que estamos mirando el archivo correcto. Criterio nuclear:

```
archivo generado = archivo validado = archivo entregado = archivo abierto por el usuario
```

## Discrepancia detectada

El usuario reporto, sobre `xlsx_generalization_001/002_preview.xlsx`, sintomas propios de
una salida de fase 9.9 (anterior a 9.16/9.18):

- abrir en `COST_ITEMS` / `README_MASTER` en lugar de `INDEX`;
- `README_MASTER.phase = 9.9`;
- `=HYPERLINK(...)` visible en `INDEX`;
- ausencia de vistas adaptativas (`_Datos`, `_Espacios`, comparativa);
- `BUDGET_REVIEW_001` como plantilla clasica plana;
- formulas auxiliares (`=PEM * PorGasGen`, etc.) en `Descripcion` y en `COST_ITEMS`;
- en 002, capitulos comparativos interpretados como partidas (`Cap.` -> cantidad).

Codex, en cambio, reportaba fase 9.19 COMPLETE, validacion post-generacion OK y 269 tests.

## Por que las fases anteriores no bastaban

La auditoria de disco demostro que **los artefactos reales eran correctos** y que el problema
era de **trazabilidad/identidad del artefacto**, no del pipeline:

1. Los nombres de salida (`xlsx_generalization_00N_preview.xlsx`) se **reutilizaban entre
   fases**. Conviven decenas de XLSX homonimos de distintas edades bajo `outputs/`.
2. El `003` en disco seguia siendo fase 9.9 (no se regenero en la corrida de 2 archivos de
   9.19): prueba directa de que persisten archivos antiguos con el mismo patron de nombre.
3. La carpeta de trabajo esta bajo un directorio de escritorio sincronizable, lo que anade
   posible lag entre lo que el pipeline escribe y lo que la copia abierta por el usuario refleja.

Conclusion: el usuario abria **copias obsoletas/equivocadas**. Las fases 9.16-9.19 corregian
el contenido, pero ninguna rompia la reutilizacion de nombres ni emitia un manifest verificable,
asi que la confusion podia repetirse indefinidamente.

Ademas se verifico una hipotesis tecnica clave: el pipeline **no** valida un workbook en memoria
mientras guarda otro archivo. `validate_generated_xlsx_preview()` y `validate_workbook_file()`
**reabren el archivo desde disco** (`load_workbook(output_path)`) tras `wb.save(...)`. La
validacion post-guardado ya operaba sobre disco; lo que faltaba era una entrega con nombre
inequivoco y un manifest con SHA-256.

## Inventario forense de outputs (resumen)

29 archivos `.xlsx` bajo `outputs/`. Clasificacion aproximada por marcadores:

- `PHASE_9_19_VALID_OUTPUT`: 2 (`xlsx_generalization_001/002_preview.xlsx`, fase 9.19, abren en INDEX, vistas adaptativas, COST_ITEMS limpio, validacion PASSED).
- `PHASE_9_17_OR_OLDER`: 16 (incluye `real_dry_run_001/002/003_preview.xlsx` en fase 9.9 que abren en README_MASTER, y `xlsx_generalization_003_preview.xlsx` en fase 9.9 que abre en BUDGET_REVIEW_001).
- `UNKNOWN` (plantillas tecnicas/sinteticas y snapshots): 11.

Estado de identidad: los nombres genericos no permiten distinguir a simple vista la fase que
produjo cada archivo. Esa es la causa raiz de la discrepancia.

## Ruta oficial nueva de revision humana

Carpeta nueva, exclusiva de la fase y nunca reutilizada:

```
outputs/live_excel_master/manual_review_phase_9_20/
```

Archivos exactos a abrir por el usuario:

```
outputs/live_excel_master/manual_review_phase_9_20/phase_9_20_review_001.xlsx
outputs/live_excel_master/manual_review_phase_9_20/phase_9_20_review_002.xlsx
```

## Manifest

`outputs/live_excel_master/manual_review_phase_9_20/MANIFEST_phase_9_20.json` (local, no se sube
a git). Version sanitizada apta para documentacion en
`docs/decisions/phase_9_20_artifact_audit_manifest_sanitized.md`. Vincula, por artefacto:
`artifact_id`, `output_relative_path`, `sha256`, `size_bytes`, `modified_at_local`,
`readme_phase`, `active_sheet`, `sheets`, `required_sheets_present`, `adaptive_views_present`,
`validation_status`, `human_review_start_sheet`.

## Checks post-guardado (desde disco)

Por cada artefacto, el wrapper `run_xlsx_generalization_dry_run.py`:

1. Genera y guarda el workbook.
2. Calcula SHA-256 del archivo en disco (`sha_before`).
3. Ejecuta `validate_generated_xlsx_preview()` (reabre desde disco).
4. Recalcula SHA-256 (`sha_after`) y exige `sha_before == sha_after` (la validacion no muta el
   archivo: se descarta validar-en-memoria-guardar-otro).
5. Reabre desde disco para leer hojas, fase y hoja activa.
6. Exige `readme_phase == 9.20` y `active_sheet == INDEX`.
7. Escribe el manifest con el SHA-256 del archivo realmente entregado.

## Resultado de generacion (sintetico y real)

Generacion real local con `data/samples/20_07_GAV_Datos.xlsx` y `data/samples/exc.xlsx`:

- `phase_9_20_review_001.xlsx`: phase=9.20, active=INDEX, hojas
  `INDEX, BUDGET_REVIEW_001, BUDGET_REVIEW_001_Datos, BUDGET_REVIEW_001_Espacios, BUDGET_REVIEW_TRACE_001, ...`,
  COST_ITEMS sin filas auxiliares ni formulas (29 filas limpias), validacion PASSED.
- `phase_9_20_review_002.xlsx`: phase=9.20, active=INDEX, hojas
  `INDEX, BUDGET_REVIEW_001, BUDGET_REVIEW_001_Hoja1 (COMPARISON_TABLE), BUDGET_REVIEW_TRACE_001, ...`,
  vista comparativa con columnas `Cap. | Nombre del capitulo | Importe (€) | Nombre equivalente | Importe equivalente | Diferencia`,
  sin columnas clasicas inventadas, COST_ITEMS vacio (no se proyectan filas comparativas como partidas), validacion PASSED.

SHA-256 completos de la ultima corrida en el manifest sanitizado.

## Que archivos exactos debe abrir el usuario

Unicamente los dos archivos de `manual_review_phase_9_20/`. Cualquier
`xlsx_generalization_*` o `real_dry_run_*` es de fases anteriores y NO debe usarse para revisar 9.20.

## Limitaciones

- La fase no resuelve un eventual lag de sincronizacion del sistema de archivos del usuario;
  lo mitiga haciendo el nombre inequivoco y verificable por SHA-256.
- Los SHA-256 cambian en cada regeneracion (timestamps internos del workbook); la identidad se
  verifica contra el manifest de la corrida correspondiente, no contra un hash fijo historico.
- La generalizacion sigue limitada a XLSX bajo `data/samples` y a un maximo de 5 archivos.

## Riesgos

- Si en el futuro se vuelven a reutilizar nombres genericos para entregas, la confusion puede
  reaparecer; ADR-020 lo prohibe explicitamente.
- Outputs antiguos homonimos siguen en disco; se recomienda no borrarlos en esta fase (auditoria)
  pero documentar que solo `manual_review_phase_9_20/` es valido para 9.20.

## Recomendacion para Fase 9.21

- Consolidar traduccion de formulas avanzadas (nombres definidos/rangos cruzados) con matriz de
  compatibilidad por tipo semantico.
- Considerar limpieza/cuarentena controlada de outputs antiguos homonimos (con registro), para
  reducir superficie de confusion.
- Mantener el patron de entrega por fase con manifest+SHA-256 para toda revision humana.
