# Fase 9.0: definicion del Excel maestro vivo como salida principal del sistema

## 1. Objetivo

Documentar y fijar metodologicamente que la salida principal del sistema sera un archivo Excel maestro vivo, iterativo y actualizable, que acumulara presupuestos procesados, validaciones, trazabilidad y ratios cada vez mas precisos.

## 2. Decision humana

La salida final del sistema no debe entenderse como una base de datos externa ni como un informe aislado. La salida principal debe ser un documento Excel maestro vivo.

## 3. Contexto del cambio

- BC3 ya esta cubierto con parser estricto, validador estricto, normalizacion intermedia y validacion de contrato.
- Excel ya dispone de lector integral, validacion del lector, normalizacion intermedia inicial e inventario multi-formato.
- Presto/PZH sigue siendo obligatorio y requiere una via tecnica valida.
- El sistema ya dispone de contrato multi-formato y puede leer/diagnosticar fuentes principales.
- Falta fijar el contenedor operativo final donde convergiran datos procesados, validaciones y calculos progresivos.

## 4. Diferencia entre artefactos

### 4.1 Reports temporales

- Son salidas de diagnostico o validacion.
- Sirven para inspeccion local y auditoria tecnica.
- No son el producto operativo final.

### 4.2 Estructuras intermedias

- Representan lectura, parseo y normalizacion parcial.
- Conservan trazabilidad y señales de calidad.
- No son aun el master operativo.

### 4.3 Excel maestro vivo

- Es el contenedor operativo final del sistema.
- Se actualiza/sobrescribe de forma controlada en cada iteracion.
- Puede añadir nuevas hojas internas.
- Acumula presupuestos procesados, validaciones, exclusiones, trazabilidad y ratios progresivos.

### 4.4 Outputs de diagnostico

- Son inspecciones locales de corpus real o fixtures.
- No deben confundirse con el master operativo.

## 5. Definicion de Excel maestro vivo

El Excel maestro vivo es un archivo Excel unico, versionable y trazable que funciona como producto operativo final del sistema. No es un simple informe y no depende de una base de datos externa como salida principal.

## 6. Reglas de actualizacion y sobrescritura controlada

- El Excel maestro puede regenerarse por iteracion.
- La sobrescritura debe ser controlada y auditable.
- Cada nueva iteracion debe conservar historial o referencias a versiones anteriores.
- Los cambios no deben destruir trazabilidad ni historial de decisiones.

## 7. Reglas para añadir nuevas hojas

- Se pueden añadir hojas internas cuando aporten valor operativo.
- Las hojas nuevas deben tener proposito explicito y trazabilidad.
- No deben duplicar informacion sin necesidad.
- Deben permitir separar datos usados, excluidos, pendientes y calculados.

## 8. Hojas minimas propuestas

- `README / INSTRUCCIONES`
- `IMPORT_LOG`
- `SOURCE_FILES`
- `PROJECTS`
- `BUDGET_VERSIONS`
- `RAW_IMPORTS_INDEX`
- `COST_ITEMS`
- `NORMALIZED_COST_ITEMS`
- `CATEGORY_MAPPING_PENDING`
- `VALIDATION_RESULTS`
- `MANUAL_REVIEW`
- `EXCLUSIONS`
- `RATIO_INPUTS`
- `RATIOS_CALCULATED`
- `RATIO_HISTORY`
- `FORMAT_STATUS`
- `TRACEABILITY`

## 9. Hojas futuras posibles

- `SUPPLIER_EXPORTS`
- `HUMAN_DECISIONS`
- `CHANGE_LOG`
- `MODEL_FLAGS`
- `QUALITY_METRICS`

## 10. Relacion con fuentes

### 10.1 Excel origen

- Fuente prioritaria y ya operativa.
- Aporta lectura integral y trazabilidad por celda.

### 10.2 BC3

- Fuente avanzada ya operativa.
- Aporta estructura y compatibilidad con el flujo intermedio.

### 10.3 Presto/exportaciones

- Fuente obligatoria del roadmap.
- Debe entrar via exportacion BC3, exportacion Excel, herramienta externa o flujo equivalente validado.

### 10.4 PDF/referencias

- Solo respaldo documental o referencia manual, no fuente automatica principal.

## 11. Relacion con trazabilidad

- Cada dato del Excel maestro debe poder vincularse a su fuente.
- La trazabilidad debe conservar archivo, formato, version, hoja o registro cuando aplique.
- Las exclusiones y revisiones manuales tambien deben quedar trazadas.

## 12. Relacion con validaciones

- Solo deben incorporarse datos validados o explicitamente marcados como elegibles para su uso.
- Los datos bloqueados no deben alimentar ratios.
- Los errores, warnings y manual review deben conservarse como estado operativo.

## 13. Relacion con exclusiones

- Las exclusiones no desaparecen.
- Deben mantenerse visibles y reversibles cuando corresponda.
- El Excel maestro debe distinguir datos usados, excluidos y pendientes.

## 14. Relacion con revision humana

- La revision humana sigue siendo necesaria para casos ambiguos.
- El Excel maestro debe conservar los elementos que requieran revision futura.

## 15. Relacion con ratios progresivos

- Los ratios no se congelan como un unico calculo final sin contexto.
- Se recalculan o refinan a medida que crece el volumen de datos procesados y validados.
- El master vivo debe reflejar ese progreso.

## 16. Que significa que los ratios mejoran con mas volumen

- Aumenta la base de comparacion.
- Se reducen sesgos de muestras pequenas.
- Se estabilizan categorias y agrupaciones cuando hay mas evidencia.
- No significa inventar datos ni forzar resultados; significa refinar con mas informacion valida.

## 17. Riesgos

- Confundir el master vivo con un informe estatico.
- Sobrescribir sin preservar trazabilidad.
- Mezclar datos no validados con datos elegibles.
- Intentar calcular ratios sin superficie base.
- Ocultar exclusiones o manual review.

## 18. Decisiones pendientes

- Estructura tecnica del generador del Excel maestro vivo.
- Versionado exacto del archivo maestro.
- Mecanismo de historial interno o de snapshots.
- Regla de actualizacion por iteracion.
- Tratamiento de ratios parciales y refinados.

## 19. Criterios para pasar a Fase 9.1

- ADR-019 aprobada y reflejada en la documentacion.
- Hojas minimas y responsabilidades del master definidas.
- Reglas de sobrescritura y versionado explicitadas.
- Estructura tecnica del generador lista para diseno.
- No existe todavia carga real al master, salvo aprobacion futura.

