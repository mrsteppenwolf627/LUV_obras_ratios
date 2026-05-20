# Fase 9.13 - Prueba real ampliada XLSX post-hardening y validacion de generalizacion

## Objetivo de la fase

Validar en modo local/dry-run si las mejoras tecnicas de Fase 9.12 para extraccion economica XLSX y mapping `preserved -> COST_ITEMS` generalizan en varios layouts reales, sin promocion operativa.

## Contexto desde Fase 9.12

- Fase 9.12 cerro el endurecimiento de:
  - deteccion de cabeceras economicas heterogeneas;
  - parseo numerico europeo/anglosajon;
  - separacion `item_description` / `unit` / `quantity` / `unit_price` / `amount`;
  - clasificacion de filas y estados de mapping extendidos.
- Casos de referencia previos:
  - `REAL_DRY_RUN_001`: `OPERATIVE_CANDIDATE`.
  - `REAL_DRY_RUN_003`: de `PROMOTION_BLOCKED` en 9.10 a `OPERATIVE_CANDIDATE` en 9.12.

## Alcance de la prueba real ampliada

- Evaluacion local de XLSX reales aislados bajo `data/samples/`.
- Generacion de previews en ruta ignorada por Git:
  - `outputs/live_excel_master/xlsx_generalization/`
- Evaluacion por archivo con IDs sanitizados y reporte sanitizado.
- Sin promocion a operativo.

## Fuera de alcance

- Ruta BC3 preservada en flujo 9.x.
- Ingesta real operativa.
- Calculo final de ratios.
- Normalizacion final de categorias.
- Consolidacion definitiva de importes.
- Cualquier modificacion de `RAW`.
- Subida de archivos reales, previews generadas o reportes sensibles.

## Archivos XLSX reales evaluados (sanitizados)

- `REAL_XLSX_GENERALIZATION_001`
- `REAL_XLSX_GENERALIZATION_002`
- `REAL_XLSX_GENERALIZATION_003`

## Seleccion de muestra y limitaciones

- Disponibilidad local real: 3 XLSX.
- Objetivo inicial era hasta 5; no se alcanzan 5 por disponibilidad local en esta iteracion.
- Muestra usada:
  - un caso historico ya candidato operativo;
  - un caso historico previamente bloqueado por mezcla importe-descripcion;
  - un caso adicional de layout heterogeneo para probar generalizacion real fuera del par historico.

## Resultado por archivo

| ID sanitizado | Estado dry-run | Motivos |
| --- | --- | --- |
| REAL_XLSX_GENERALIZATION_001 | OPERATIVE_CANDIDATE | ninguno |
| REAL_XLSX_GENERALIZATION_002 | OPERATIVE_CANDIDATE | ninguno |
| REAL_XLSX_GENERALIZATION_003 | PROMOTION_BLOCKED | description_amount_split_failed; amount_mixed_in_description; economic_header_low_confidence; numeric_parse_ambiguous |

## Metricas por archivo

| ID sanitizado | mapping_rate | mapping_rate_on_candidate_cost_items | traceability_rate | manual_review_rate | blocked_rate | amount_separation_rate | not_cost_item_rows | ambiguous_rows | candidate_cost_item_rows | ratio_input_rows | ratio_calculated_rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| REAL_XLSX_GENERALIZATION_001 | 1.0 | 1.0 | 1.0 | 0.0 | 0.0 | 1.0 | 74.0 | 0.0 | 23.0 | 0.0 | 0.0 |
| REAL_XLSX_GENERALIZATION_002 | 1.0 | 1.0 | 1.0 | 0.0 | 0.0 | 1.0 | 9.0 | 0.0 | 31.0 | 0.0 | 0.0 |
| REAL_XLSX_GENERALIZATION_003 | 1.0 | 1.0 | 1.0 | 0.017857142857142856 | 0.0 | 0.9444444444444444 | 44.0 | 0.0 | 39.0 | 0.0 | 0.0 |

## Comparativa con Fase 9.10 (cuando aplica)

### Caso historico candidato operativo

Cruce sanitizado:
- `REAL_DRY_RUN_001` (Fase 9.10) <-> `REAL_XLSX_GENERALIZATION_001` (Fase 9.13).

Comparativa:
- estado: `OPERATIVE_CANDIDATE` -> `OPERATIVE_CANDIDATE` (sin degradacion);
- mapping_rate: `0.7938144329896907` -> `1.0`;
- traceability_rate: `1.0` -> `1.0`;
- amount_separation_rate: `1.0` -> `1.0`;
- motivos: `ninguno` -> `ninguno`.

### Caso historico previamente bloqueado por importe en descripcion

Cruce sanitizado:
- `REAL_DRY_RUN_003` (Fase 9.10) <-> `REAL_XLSX_GENERALIZATION_002` (Fase 9.13).

Comparativa:
- estado: `PROMOTION_BLOCKED` -> `OPERATIVE_CANDIDATE`;
- mapping_rate: `0.8048780487804879` -> `1.0`;
- traceability_rate: `1.0` -> `1.0`;
- amount_separation_rate: `0.0` -> `1.0`;
- motivos: `amount_mixed_in_description; insufficient_amount_separation` -> `ninguno`.

## Evaluacion visual resumida por archivo

### REAL_XLSX_GENERALIZATION_001

- Hojas del input preservadas: si (2 hojas preservadas visibles + indices tecnicos).
- Hoja preservada reconocible como presupuesto: si.
- Logica de filas/columnas conservada: si.
- Separacion de importes y descripcion: correcta en filas monetarias detectadas.
- Conservacion de unidad/cantidad/precio: parcial (unidad/cantidad/precio unitario ausentes en este layout, sin degradar importes).
- Mapping a `COST_ITEMS`: razonable para filas candidatas (`mapping_rate_on_candidate_cost_items=1.0`).
- Parte confusa remanente: cabecera economica en confianza baja (anotacion recurrente), aunque sin bloqueo.

### REAL_XLSX_GENERALIZATION_002

- Hojas del input preservadas: si (1 hoja preservada visible + indices tecnicos).
- Hoja preservada reconocible como presupuesto: si.
- Logica de filas/columnas conservada: si.
- Separacion de importes y descripcion: correcta.
- Conservacion de unidad/cantidad/precio: cantidad conservada; precio unitario no detectado en este layout.
- Mapping a `COST_ITEMS`: consistente (`mapping_rate_on_candidate_cost_items=1.0`).
- Parte confusa remanente: cabecera economica clasificada como baja confianza, no bloqueante.

### REAL_XLSX_GENERALIZATION_003

- Hojas del input preservadas: si (2 hojas preservadas visibles + indices tecnicos).
- Hoja preservada reconocible como presupuesto: si.
- Logica de filas/columnas conservada: si.
- Separacion de importes y descripcion: mejora parcial (amount_separation_rate alto), pero persiste al menos una fila con mezcla descripcion-importe.
- Conservacion de unidad/cantidad/precio: parcial; precio unitario y cantidad incompletos en parte del layout.
- Mapping a `COST_ITEMS`: razonable para filas candidatas, pero no suficiente para promover por bloqueo economico.
- Parte confusa remanente: cabecera economica ambigua y parseo numerico ambiguo puntual.

## Patrones que ahora se resuelven

- Casos historicos 9.10 con trazabilidad correcta pero separacion economica debil ya no quedan bloqueados por defecto.
- `mapping_rate_on_candidate_cost_items` estable en `1.0` en los casos evaluados.
- No se alimentan `RATIO_INPUTS` ni `RATIOS_CALCULATED` en previews.

## Patrones que siguen fallando

- Layouts con cabeceras economicas de baja confianza sostenida.
- Casos puntuales con importe mezclado en descripcion incluso con separacion global alta.
- Deteccion de `unit_price` y `quantity` aun parcial en ciertos formatos heterogeneos.

## Umbrales preliminares: evaluacion

Con la muestra actual (3 archivos):
- `traceability_rate >= 0.95`: razonable.
- `amount_separation_rate >= 0.85`: razonable, pero no suficiente por si sola si hay mezcla puntual bloqueante.
- `manual_review_rate <= 0.25`: razonable.
- `blocked_rate = 0`: razonable para promocion.

Decision:
- Mantenerlos como preliminares; no convertir a definitivos con muestra tan limitada.

## BC3 vs mas endurecimiento XLSX

Recomendacion tecnica:
- No abrir BC3 preservado todavia como frente principal.
- Priorizar una iteracion corta adicional de endurecimiento XLSX enfocada en:
  - reduccion de `economic_header_low_confidence`;
  - reduccion de `description_amount_split_failed`/`amount_mixed_in_description` en layouts ambiguos.

Razon:
- Ya hay evidencia de generalizacion positiva en 2/3 casos.
- El bloqueo restante es exactamente del frente XLSX economico, y su cierre reduce riesgo antes de ampliar complejidad con BC3 preservado.

## Riesgos

- Sobreajuste a muestras actuales sin cubrir variedad suficiente de layouts.
- Falsos positivos de mezcla descripcion-importe en casos limite.
- Confianza de cabecera baja cronica aunque el estado final sea candidato.

## Limitaciones

- Muestra real reducida (3 XLSX).
- Sin cobertura BC3 en esta fase por alcance.
- Evaluacion visual resumida, no auditoria funcional de negocio completa.

## Recomendacion para Fase 9.14

1. Ejecutar mini-hardening XLSX de precision sobre los motivos remanentes (`economic_header_low_confidence`, `description_amount_split_failed`, `numeric_parse_ambiguous`).
2. Repetir generalizacion con muestra XLSX ampliada (ideal >= 5).
3. Si no hay degradaciones y el bloqueo economico puntual desaparece o queda en umbral controlado, abrir Fase BC3 preservada.
