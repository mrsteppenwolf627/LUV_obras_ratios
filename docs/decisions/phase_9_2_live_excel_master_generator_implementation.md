# Fase 9.2: implementacion controlada del generador del Excel maestro vivo

## 1. Objetivo de la fase

Implementar una primera version controlada del generador del Excel maestro vivo conforme al contrato documental de Fase 9.1, sin usar datos reales ni habilitar calculo final de ratios.

## 2. Contexto desde Fase 9.1

- Fase 9.1 cerro el contrato tecnico del maestro vivo.
- ADR-019 mantiene que el producto operativo principal es un Excel maestro vivo.
- Esta fase implementa estructura, validacion de esquema y snapshots controlados.

## 3. Alcance de implementacion

- Script CLI para crear/actualizar plantilla del maestro vivo.
- Creacion de hojas obligatorias del contrato 9.1.
- Creacion de columnas minimas por hoja.
- Validacion automatica de hojas y columnas obligatorias.
- Snapshots pre/post en actualizaciones controladas.
- Bloqueo de sobrescritura no controlada.
- Tests sinteticos automatizados.

## 4. Fuera de alcance

- Importacion de datos reales.
- Importacion de BC3/Excel reales al master.
- Tratamiento nuevo de Presto/PZH.
- Calculo de ratios finales.
- Normalizacion final de categorias.
- Consolidacion final de importes.
- Modificacion de RAW.

## 5. Archivos creados

- `scripts/generate_live_excel_master.py`
- `tests/scripts/test_generate_live_excel_master.py`

## 6. Archivos modificados

- `CONTEXT.md`
- `README.md`
- `.gitignore`

## 7. Diseño tecnico implementado

- Contrato declarativo de esquema (`REQUIRED_SHEETS_COLUMNS`) en el script.
- Creacion de workbook con hojas requeridas y headers en fila 1.
- Metadata tecnica no sensible en `README_MASTER`.
- Modo actualizacion solo con `--update`.
- Verificacion de ruta de salida dentro de `outputs/live_excel_master`.

## 8. Hojas implementadas

- `README_MASTER`
- `IMPORT_LOG`
- `SOURCE_FILES`
- `PROJECTS`
- `BUDGET_VERSIONS`
- `RAW_IMPORTS`
- `COST_ITEMS`
- `NORMALIZED_COST_ITEMS`
- `CATEGORY_MAPPING`
- `VALIDATION_RESULTS`
- `RATIO_INPUTS`
- `RATIOS_CALCULATED`
- `EXCLUSIONS`
- `SNAPSHOTS`
- `CHANGELOG`

## 9. Validacion de esquema implementada

- Validacion de existencia de todas las hojas obligatorias.
- Validacion de columnas minimas por hoja (coincidencia exacta de header en fila 1).
- Error explicito (`SchemaValidationError`) si falta hoja o columna.

## 10. Sistema de snapshots implementado

- En actualizacion controlada (`--update`) se crea snapshot pre-update del archivo existente.
- Tras guardar la nueva version, se crea snapshot post-update.
- Snapshots en `outputs/live_excel_master/snapshots`.
- Registro de snapshots en hoja `SNAPSHOTS`.

## 11. Reglas de rollback si aplica

- Si falla la validacion previa de esquema, la actualizacion se bloquea sin escribir.
- El snapshot pre-update permite restauracion manual del estado previo.
- No se realiza rollback automatico en esta fase.

## 12. Tests añadidos

- Creacion de maestro vacio.
- Existencia de hojas obligatorias.
- Existencia de columnas minimas por hoja.
- Validacion de esquema correcta.
- Fallo controlado por hoja obligatoria faltante.
- Fallo controlado por columna obligatoria faltante.
- Snapshots pre/post en actualizacion controlada.
- Bloqueo de escritura fuera de ruta permitida.
- Compatibilidad con ejecucion repetida.
- Verificacion de no uso de datos reales (solo headers y metadata tecnica).

## 13. Riesgos

- Deriva de contrato si Fase 9.1 cambia y no se sincroniza constante de esquema.
- Crecimiento de snapshots si se ejecuta con alta frecuencia sin politica de poda.
- Falta de rollback automatico en errores posteriores al guardado.

## 14. Limitaciones

- No integra ingesta real ni normalizacion real.
- `CATEGORY_MAPPING` mantiene semantica pendiente de fases posteriores.
- `RATIOS_CALCULATED` puede quedar vacia por restriccion metodologica.

## 15. Recomendacion para Fase 9.3

- Habilitar carga sintetica incremental end-to-end sobre la plantilla.
- Definir estrategia de retencion/poda de snapshots.
- Endurecer validaciones referenciales entre hojas.
- Diseñar rollback semiautomatico basado en snapshot pre-update.
