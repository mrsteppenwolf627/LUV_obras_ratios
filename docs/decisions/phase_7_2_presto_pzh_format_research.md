# Fase 7.2: investigacion tecnica Presto/PZH

## 1. Objetivo

Determinar, con evidencia tecnica local y no destructiva, si los archivos Presto/PZH y variantes relacionadas pueden leerse directamente, si requieren biblioteca estandar, si dependen de herramienta externa o si solo son viables via exportacion del proveedor.

## 2. Contexto

- BC3 ya esta cubierto como modulo avanzado.
- Excel ya dispone de lector integral.
- Presto/PZH aparece en el corpus real local como familia de archivos a investigar.

## 3. Preguntas de investigacion

- Tipo fisico real de los archivos.
- Magic bytes.
- Si son texto, zip, sqlite, binarios propietarios o contenedores mixtos.
- Si exponen nombres internos visibles.
- Si permiten inspeccion segura con librerias estandar.
- Si requieren exportacion externa a Excel o BC3.

## 4. Alcance

- Inspeccion tecnica no destructiva.
- Clasificacion de soporte tecnico.
- Registro de metadatos basicos.
- Informe sintetico local.

## 5. Fuera de alcance

- Parser nativo de presupuesto Presto.
- Importacion al master.
- Ratios.
- Consolidacion final.
- Normalizacion final de categorias.

## 6. Clasificacion de soporte tecnico

- `DIRECTLY_READABLE`
- `READABLE_WITH_STANDARD_LIBRARY`
- `NEEDS_EXTERNAL_TOOL`
- `NEEDS_VENDOR_EXPORT`
- `UNSUPPORTED_OR_UNKNOWN`

## 7. Entregables

- Script diagnostico tecnico.
- Reporte JSON local.
- Reporte Markdown local.
- Tests sintenticos.

## 8. Riesgos

- Confundir extension con formato real.
- Invertir en soporte nativo sin evidencia de lectura fiable.
- Tratar como presupuesto algo que en realidad sea backup o exportacion intermedia.

## 9. Criterios de aceptacion

- Clasificacion tecnica reproducible.
- No modificacion de RAW.
- No subida de reportes sensibles.
- Decision clara sobre soporte nativo o necesidad de exportacion externa.

## 10. Hallazgo local inicial

- En el corpus local analizado hay 10 archivos Presto-like.
- Todos quedaron clasificados como `NEEDS_VENDOR_EXPORT`.
- No se obtuvo evidencia de lectura nativa utilizable con la libreria estandar.
- La decision tecnica inmediata es tratar Presto/PZH como formato a soportar por exportacion o herramienta externa, no por parser nativo improvisado.
