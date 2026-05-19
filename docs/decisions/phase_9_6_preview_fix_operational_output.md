# Fase 9.6-preview-fix: output operativo equivalente al input

## Objetivo de la correccion

Corregir la preview local para que el Excel generado no sea solo plantilla tecnica y ofrezca una vista operativa legible del presupuesto importado, manteniendo `PREVIEW_ONLY`.

## Contexto desde Fase 9.6-preview

- La preview previa fue metodologicamente segura.
- Resultado funcional: insuficiente para lectura operativa humana del estudio.
- Se requiere separar mejor capa tecnica y capa operativa.

## Problema detectado en la preview

- La salida parecia plantilla tecnica.
- Campos economicos y descriptivos no estaban suficientemente separados.
- Faltaba una hoja de lectura equivalente al input.

## Diferencia entre capa tecnica y capa operativa

- Capa tecnica: trazabilidad, lotes, snapshots, validaciones, exclusiones y auditoria.
- Capa operativa: representacion del presupuesto importado como presupuesto (capitulos/partidas/unidades/mediciones/precios/importes).

## Definicion de output equivalente al input

- Preservar referencia de hoja origen y fila origen.
- Intentar separar codigo/capitulo/descripcion/unidad/cantidad/precio/importe cuando sea detectable.
- No inventar valores faltantes.
- Marcar toda la salida como `PREVIEW_ONLY`.

## Hojas operativas añadidas o propuestas

- Añadida: `IMPORTED_BUDGET_VIEW`.
- Funcion: vista operativa de lectura humana del input XLSX aislado.

## Criterios minimos de utilidad visual

- Filas con referencia de hoja y fila de origen.
- Campos economicos separados de descripcion cuando sea posible.
- Estado de validacion visible.
- Indicador `preview_only=TRUE` por fila.

## Como se conservan trazabilidad y validacion

- Se mantiene la capa tecnica (`SOURCE_FILES`, `IMPORT_LOG`, `RAW_IMPORTS`, `VALIDATION_RESULTS`, `CHANGELOG`).
- `IMPORTED_BUDGET_VIEW` registra `source_sheet_name` y `source_row_number`.
- El workbook final mantiene validacion de esquema e integridad del contrato vigente.

## Que datos se pueden poblar desde XLSX real aislado

- `chapter_code`, `chapter_name`, `item_code`, `item_description`, `unit`, `quantity`, `unit_price`, `amount` cuando las cabeceras sean detectables.
- Si no se detecta una columna, queda vacia y se documenta en `notes`.

## Que datos quedan pendientes

- `NORMALIZED_COST_ITEMS`, `CATEGORY_MAPPING`, `RATIO_INPUTS`, `RATIOS_CALCULATED` siguen fuera de alcance en preview-fix.
- No hay promocion a master operativo ni ingesta formal.

## Limitaciones

- Deteccion de columnas depende de cabeceras del XLSX origen.
- No hay interpretacion semantica avanzada de estructuras no tabulares.
- No se resuelven decisiones finales de categorias ni ratios.

## Riesgos

- Estructuras XLSX heterogeneas pueden reducir separacion automatica.
- Riesgo de interpretar preview como salida operativa final si no se mantiene etiqueta `PREVIEW_ONLY`.

## Confirmacion metodologica

- Sigue siendo `PREVIEW_ONLY`.
- No hay promocion a master operativo.
- No se modifica RAW.
- No se suben archivos reales ni Excels generados.

## Recomendacion para Fase 9.6 formal

- Definir contrato de ingesta real controlada al master.
- Establecer umbrales minimos de separacion operativa antes de promocion.
- Mantener capa operativa y capa tecnica sincronizadas por trazabilidad.
