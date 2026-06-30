# FASE MASTER

## Objetivo

FASE MASTER define el flujo canonico para actualizar ratios oficiales y regenerar el workbook oficial del sistema con trazabilidad y aprobacion humana previa.

El objetivo es evitar que una importacion alimente ratios definitivos de forma automatica sin revision.

## Flujo operativo

```text
POST /api/import
  -> Budget + BudgetImport
  -> approval_status = PENDING_REVIEW

Revision master
  -> GET /api/master/imports/pending
  -> GET /api/master/imports/{id}

Decision humana
  -> POST /api/master/imports/{id}/approve
  -> POST /api/master/imports/{id}/reject

Si APPROVED
  -> recalculate_after_approval()
  -> recalculo approved-only
  -> export oficial LUV_RATIOS_MASTER.xlsx
```

## Endpoints disponibles

### Flujo master

- `GET /api/master/status`
- `GET /api/master/imports`
- `GET /api/master/imports/pending`
- `GET /api/master/imports/{id}`
- `POST /api/master/imports/{id}/approve`
- `POST /api/master/imports/{id}/reject`

### Export oficial

- `GET /api/export/master.xlsx`

Nota: el archivo oficial generado internamente es `data/master/LUV_RATIOS_MASTER.xlsx`.

## Que hace `/api/import` ahora

`POST /api/import` queda congelado como flujo legacy de ingesta:

- sigue leyendo e importando archivos;
- conserva hash, RAW y trazabilidad;
- crea `Budget` y registra `BudgetImport`;
- deja `approval_status="PENDING_REVIEW"`;
- no recalcula ratios definitivos;
- no genera el master oficial automaticamente.

Respuesta funcional esperada:

- `approval_status: "PENDING_REVIEW"`
- `master_update: "pending_approval"`
- `ratios_updated: false`

## Que hace `/api/items/analisis` ahora

`POST /api/items/analisis` queda congelado como endpoint de analisis en solo lectura:

- sigue clasificando;
- sigue comparando contra ratio historico persistido;
- sigue devolviendo desviacion, impacto y resumenes;
- no crea `ItemMaster`;
- no modifica `ItemMasterRatio`;
- no hace commit de cambios estadisticos.

Respuesta funcional esperada:

- `ratios_updated: false`
- `mode: "read_only"`

## Frontend minimo de revision

La pantalla minima de revision master queda disponible en:

- `/master`
- `/master/revision`

Permite:

- listar importaciones pendientes;
- ver detalle;
- aprobar importaciones;
- rechazar importaciones.

Mensajes UX clave:

- aprobar una importacion recalcula ratios oficiales y actualiza `LUV_RATIOS_MASTER.xlsx`;
- rechazar una importacion la excluye del master oficial.

## Como descargar `LUV_RATIOS_MASTER.xlsx`

1. Importar el archivo por el flujo legacy de ingesta.
2. Revisar la importacion pendiente en el flujo master.
3. Aprobarla si procede.
4. El backend ejecuta el recalculo canónico approved-only y regenera el workbook oficial.
5. Descargar el artefacto desde `GET /api/export/master.xlsx`.

## Limitaciones actuales

### Vinculo temporal Budget <-> BudgetImport

Mientras no exista FK directa entre `Budget` y `BudgetImport`, el flujo master vincula ambos registros temporalmente por `file_hash`.

### Deuda controlada approved-only

El flujo canónico approved-only ya reconstruye la tabla `ratios` y el export oficial filtrado, pero sigue pendiente una reconstruccion approved-only completa de:

- `ItemMaster`
- `ItemMasterRatio`

Consecuencia actual:

- `RATIOS_SUMMARY` y `ITEM_MASTER` pueden seguir leyendo agregados legacy historicos hasta una fase posterior de saneamiento.

### Presto

El subflujo legacy de Presto mantiene su export tecnico propio de `space_ratios`.

Eso no forma parte del master oficial y no debe confundirse con `LUV_RATIOS_MASTER.xlsx`.

## Estado de cierre

FASE MASTER queda cerrada como fase documental y operativa:

- flujo canonico definido;
- endpoints registrados;
- export oficial approved-only activo;
- writers legacy congelados;
- revision minima disponible en frontend.

Siguiente fase propuesta:

- validacion con archivos reales;
- prueba end-to-end completa del flujo canonico;
- saneamiento de deuda approved-only restante si se confirma necesaria.
