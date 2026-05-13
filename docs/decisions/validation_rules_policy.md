# Política preliminar de validación matemática y de consistencia

## 1. Propósito

Esta política define las reglas de validación matemática y de consistencia que deben aplicarse antes de que datos importados puedan alimentar ratios.

Una importación puede conservarse como RAW aunque no sea válida para ratios.

## 2. Alcance

Esta política cubre validaciones sobre:

- archivos fuente;
- lotes de importación;
- proyectos;
- versiones de presupuesto;
- capítulos y partidas;
- importes;
- cantidades;
- precios unitarios;
- superficies;
- categorías normalizadas;
- duplicados;
- conflictos entre fuentes;
- versiones;
- presupuestos parciales;
- elegibilidad para ratios.

## 3. Niveles de severidad

### INFO

Dato registrado sin problema bloqueante.

Consecuencia: se conserva el registro y no bloquea flujo.

### WARNING

Dato sospechoso o incompleto, pero no necesariamente bloqueante.

Consecuencia: puede permitir continuidad con trazabilidad y seguimiento.

### ERROR

Dato incorrecto o inconsistente que impide usar esa entidad para ratios.

Consecuencia: la entidad afectada no entra en cálculo hasta resolución.

### BLOCKED

Situación crítica que bloquea toda la importación, versión o proyecto.

Consecuencia: se detiene el avance a capas posteriores para esa unidad.

### MANUAL_REVIEW_REQUIRED

Caso que no debe decidirse automáticamente.

Consecuencia: requiere decisión humana registrada antes de continuar.

## 4. Estados de validación

- `NOT_VALIDATED`: entidad aún no evaluada.
- `VALID`: entidad válida sin incidencias relevantes.
- `VALID_WITH_WARNINGS`: entidad válida con advertencias no bloqueantes.
- `WARNING`: entidad con incidencias que requieren seguimiento.
- `ERROR`: entidad inválida para ratios.
- `BLOCKED`: entidad bloqueada por regla crítica.
- `MANUAL_REVIEW_REQUIRED`: resolución pendiente por revisión humana.
- `EXCLUDED`: entidad excluida de cálculo, conservada para trazabilidad.
- `REJECTED`: entidad rechazada para procesamiento posterior.

## 5. Validaciones de archivo fuente

Reglas preliminares para `SOURCE_FILE`.

### Reglas bloqueantes

- Archivo sin extensión reconocida.
- Archivo corrupto o ilegible.
- Hash no calculable.
- Archivo duplicado exacto ya importado, salvo que se registre como duplicado y no alimente ratios.
- Archivo en backup usado como fuente principal sin revisión humana.
- PDF usado como fuente automática principal.

### Reglas de advertencia

- Nombre de archivo ambiguo.
- Extensión reconocida pero tipo real dudoso.
- Archivo muy antiguo o sin fecha fiable.
- Archivo Presto/PZH no interpretable todavía.
- Archivo con caracteres raros en nombre.
- Archivo con ruta que sugiere copia o backup.

## 6. Validaciones de lote de importación

Reglas para `IMPORT_BATCH`:

- Debe registrar fecha, usuario, carpeta origen y archivos detectados.
- Debe registrar cuántos archivos fueron importados, rechazados o pendientes.
- Si todos los archivos fallan, el lote queda `FAILED`.
- Si parte falla y parte pasa, el lote queda `PARTIAL`.
- Si hay conflictos de fuente, el lote queda `MANUAL_REVIEW_REQUIRED`.
- Un lote no debe actualizar ratios automáticamente si contiene errores bloqueantes.

## 7. Validaciones de proyecto

Reglas para `PROJECT`.

### Bloqueantes para ratios

- Falta `project_id` o identificador interno.
- Falta superficie base.
- Superficie base igual a cero.
- Superficie base negativa.
- Tipo de superficie no definido.
- Proyecto duplicado no resuelto.
- Proyecto sin versión de presupuesto válida.

### Advertencias

- Falta localización.
- Falta tipo de obra.
- Falta categoría actual.
- Falta año.
- Falta constructora o agente si en el futuro se usa para segmentación.

La falta de datos descriptivos puede no bloquear la importación RAW, pero sí puede limitar análisis posteriores.

## 8. Validaciones de superficie base

La superficie base es requisito obligatorio para ratios €/m2.

Reglas:

- No calcular ratio si `surface_base_value` falta.
- No calcular ratio si `surface_base_value <= 0`.
- No mezclar superficies de tipos distintos en un mismo cálculo.
- No asumir superficie útil como construida ni viceversa.
- No convertir superficies sin fuente explícita.
- `surface_base_type` debe estar definido.
- `surface_base_source` debe registrarse.
- Si hay varias superficies candidatas, marcar `MANUAL_REVIEW_REQUIRED`.

Estados posibles:

- `SURFACE_NOT_PROVIDED`
- `SURFACE_VALID`
- `SURFACE_ZERO`
- `SURFACE_NEGATIVE`
- `SURFACE_TYPE_UNKNOWN`
- `MULTIPLE_SURFACES_CONFLICT`
- `MANUAL_REVIEW_REQUIRED`

No se define todavía cuál es la superficie oficial del proyecto. Queda pendiente de decisión humana.

## 9. Validaciones de versión de presupuesto

Reglas para `BUDGET_VERSION`.

### Bloqueantes para ratios

- Versión marcada como duplicada exacta.
- Versión `SUPERSEDED` sin aprobación.
- Versión parcial usada como presupuesto completo.
- Versión con conflicto no resuelto frente a otra fuente.
- Versión sin estado de aprobación.
- Versión de backup usada como principal sin revisión.
- Versión no trazable a archivo origen.

### Advertencias

- Falta fecha de versión.
- Falta tipo de versión.
- Falta indicación de si incluye impuestos.
- Falta moneda.
- Nombre de versión ambiguo.

Estados posibles:

- `NOT_VERSIONED`
- `VERSION_CANDIDATE`
- `CURRENT`
- `SUPERSEDED`
- `CONTRACTUAL`
- `APPROVED`
- `REJECTED`
- `PARTIAL`
- `MANUAL_REVIEW_REQUIRED`

Debe respetar la política de duplicados y versionado ya definida.

## 10. Validaciones de importes

### Bloqueantes para ratio

- Importe total ausente.
- Importe no numérico.
- Importe negativo sin justificación explícita.
- Importe cero en presupuesto o capítulo principal sin justificación.
- Diferencia no resuelta entre total declarado y total calculado.
- Moneda no definida si hay posibilidad de mezcla de monedas.
- Impuestos no identificados si afectan comparabilidad.

### Advertencias

- Importe muy bajo o muy alto respecto a otros datos, sin fijar umbrales todavía.
- Importe con redondeos.
- Importe procedente de fuente secundaria.
- Importe calculado desde partidas incompletas.

No se fijan tolerancias numéricas exactas. Quedan pendientes de decisión humana.

## 11. Validación entre total declarado y total calculado

- `total_amount_declared` debe compararse con `total_amount_calculated` cuando ambos existan.
- Si no coinciden, se registra diferencia absoluta y relativa.
- Si la diferencia supera una tolerancia definida, la versión queda `ERROR` o `BLOCKED` según gravedad.
- La tolerancia queda pendiente de decisión.
- Si no hay total declarado, se puede conservar cálculo, pero queda `WARNING` o `MANUAL_REVIEW_REQUIRED` según contexto.
- Si no hay partidas suficientes para calcular total, no puede validarse consistencia.

Campos sugeridos:

- `total_amount_declared`
- `total_amount_calculated`
- `total_difference_absolute`
- `total_difference_relative`
- `total_difference_status`
- `tolerance_rule_id`

## 12. Validaciones de partidas y capítulos

Reglas para `COST_ITEM` y `NORMALIZED_COST_ITEM`.

### Bloqueantes

- Partida sin importe cuando debe tenerlo.
- Cantidad no numérica.
- Precio unitario no numérico.
- Cantidad negativa sin justificación.
- Precio unitario negativo sin justificación.
- Importe negativo sin justificación.
- Código o descripción totalmente ausentes.
- Partida duplicada no resuelta.
- Partida de fuente excluida.
- Partida sin vínculo a versión de presupuesto.

### Advertencias

- Unidad ausente.
- Descripción ambigua.
- Código ausente.
- Nivel jerárquico no identificado.
- Capítulo sin partidas hijas.
- Partida sin categoría normalizada.
- Mapeo de baja confianza.

## 13. Validaciones de mapeo de categorías

Reglas para `CATEGORY_MAPPING` y `NORMALIZED_COST_ITEM`:

- Toda partida/capítulo que vaya a ratios debe tener categoría normalizada.
- Si falta categoría, no entra en ratio.
- Si el mapeo tiene baja confianza, requiere revisión humana.
- Si varias reglas de mapeo compiten, marcar conflicto.
- Las categorías definitivas aún no están cerradas.
- No crear categorías automáticamente sin revisión.
- No fusionar categorías por similitud textual sin regla explícita.

Estados posibles:

- `MAPPED`
- `UNMAPPED`
- `LOW_CONFIDENCE_MAPPING`
- `MULTIPLE_MAPPING_CANDIDATES`
- `MANUAL_REVIEW_REQUIRED`
- `EXCLUDED_FROM_RATIOS`

## 14. Validaciones de duplicados

Esta sección se apoya en `docs/decisions/duplicates_and_budget_versions_policy.md`.

Reglas:

- Duplicado exacto no alimenta ratios dos veces.
- Duplicado lógico requiere revisión humana.
- Backup no alimenta ratios si existe fuente válida equivalente.
- Fuente de referencia no alimenta ratios.
- Fuente secundaria no alimenta ratios salvo decisión explícita.
- Todo duplicado excluido debe conservarse.

## 15. Validaciones de conflictos entre fuentes

Conflictos típicos:

- BC3 y Excel con totales distintos.
- BC3 y PDF contractual con importes contradictorios.
- Excel y contrato con versiones diferentes.
- Distintas fechas para supuesta misma versión.
- Distintos alcances para mismo proyecto.
- Distinta moneda o impuestos.

Reglas:

- Conflictos no resueltos bloquean ratio.
- Conflictos se registran como `VALIDATION_RESULT`.
- Resolución humana debe registrar motivo, usuario y fecha.
- No se decide automáticamente qué fuente gana salvo reglas ya documentadas.

## 16. Validaciones de elegibilidad para ratios

Un dato solo puede pasar a `RATIO_INPUT` si:

- Tiene proyecto válido.
- Tiene versión de presupuesto válida.
- Tiene fuente trazable.
- No es duplicado activo.
- No está excluido.
- No pertenece a versión superseded no aprobada.
- Tiene superficie base válida.
- Tiene importe válido.
- Tiene categoría normalizada si es ratio por categoría.
- No tiene conflictos bloqueantes.
- Ha pasado validación matemática.
- Tiene estado `include_in_ratio = true`.

Estados sugeridos:

- `ELIGIBLE`
- `NOT_ELIGIBLE`
- `PENDING_REVIEW`
- `EXCLUDED`
- `BLOCKED`
- `SUPERSEDED`

## 17. Validaciones para cálculo de ratios

Reglas para `RATIOS_CALCULATED`:

- No calcular ratio con `sample_count = 0`.
- No calcular ratio si `total_surface <= 0`.
- No calcular ratio si `total_amount < 0` salvo caso explícito.
- No mezclar monedas.
- No mezclar impuestos incluidos y excluidos si no hay normalización explícita.
- No mezclar tipos de superficie.
- No mezclar tipos de obra incompatibles.
- Registrar `calculation_version`.
- Registrar fecha de cálculo.
- Registrar filtros aplicados.
- Registrar número de excluidos.
- El cálculo debe ser reproducible desde `RATIO_INPUT`.

No se fija todavía fórmula definitiva más allá de documentar que el ratio ponderado será `total_amount / total_surface` cuando aplique y con datos válidos.

## 18. Tolerancias pendientes de decisión

Pendientes:

- Tolerancia entre total declarado y total calculado.
- Tolerancia de redondeos.
- Umbral de capítulos sin mapear permitido.
- Umbral de partidas sin unidad permitido.
- Umbral de diferencias entre BC3 y Excel.
- Umbral para outliers.
- Criterio para importes negativos.
- Criterio para partidas a cero.
- Criterio para capítulos auxiliares.
- Criterio para IVA/impuestos.
- Criterio para moneda.
- Criterio para actualización por año o inflación.

## 19. Matriz preliminar de validaciones

| Código de regla | Entidad | Regla | Severidad | Bloquea importación RAW | Bloquea normalización | Bloquea ratio | Requiere revisión humana | Pendiente de decisión |
|---|---|---|---|---|---|---|---|---|
| VAL-SRC-001 | SOURCE_FILE | Hash no calculable | BLOCKED | Sí | Sí | Sí | No | No |
| VAL-SRC-002 | SOURCE_FILE | Archivo ilegible | BLOCKED | Sí | Sí | Sí | No | No |
| VAL-SRC-003 | SOURCE_FILE | PDF como fuente principal automática | BLOCKED | No | Sí | Sí | Sí | No |
| VAL-DUP-001 | SOURCE_FILE/BUDGET_VERSION | Duplicado exacto | ERROR | No | No | Sí | No | No |
| VAL-DUP-002 | SOURCE_FILE/BUDGET_VERSION | Duplicado lógico candidato | MANUAL_REVIEW_REQUIRED | No | No | Sí | Sí | No |
| VAL-VER-001 | BUDGET_VERSION | Versión superseded | ERROR | No | No | Sí | No | No |
| VAL-VER-002 | BUDGET_VERSION | Versión parcial usada como completa | BLOCKED | No | Sí | Sí | Sí | No |
| VAL-PROJ-001 | PROJECT | Proyecto sin superficie base | ERROR | No | No | Sí | No | Sí |
| VAL-SURF-001 | PROJECT | Superficie base <= 0 | BLOCKED | No | No | Sí | No | No |
| VAL-AMT-001 | COST_ITEM/BUDGET_VERSION | Importe no numérico | ERROR | No | Sí | Sí | No | No |
| VAL-AMT-002 | COST_ITEM/BUDGET_VERSION | Importe negativo sin justificación | ERROR | No | Sí | Sí | Sí | Sí |
| VAL-AMT-003 | BUDGET_VERSION | Total declarado no cuadra con total calculado | ERROR/BLOCKED | No | No | Sí | Sí | Sí |
| VAL-CAT-001 | NORMALIZED_COST_ITEM | Capítulo sin categoría normalizada | WARNING/ERROR | No | No | Sí | Sí | Sí |
| VAL-CONF-001 | BUDGET_VERSION | Conflicto BC3 vs Excel | MANUAL_REVIEW_REQUIRED | No | No | Sí | Sí | No |
| VAL-RATIO-001 | RATIOS_CALCULATED | Ratio sin muestra válida | BLOCKED | No | No | Sí | No | No |
| VAL-RATIO-002 | RATIOS_CALCULATED | Mezcla de tipos de superficie | BLOCKED | No | No | Sí | Sí | No |
| VAL-RATIO-003 | RATIOS_CALCULATED | Mezcla de monedas | BLOCKED | No | No | Sí | Sí | Sí |
| VAL-RATIO-004 | RATIO_INPUT/BUDGET_VERSION | Versión no aprobada | ERROR | No | No | Sí | Sí | No |

## 20. Pendientes de decisión humana

- Superficie base oficial.
- Categorías definitivas.
- Tolerancias numéricas.
- Tratamiento de IVA.
- Tratamiento de moneda.
- Tratamiento de importes negativos.
- Tratamiento de partidas a cero.
- Tratamiento de outliers.
- Tratamiento de fases.
- Tratamiento de versiones contractuales.
- Rol que puede aprobar datos para ratios.
- Política de recálculo de ratios cuando se corrige una importación.

## 21. Criterios para pasar a análisis de archivos reales

Antes de analizar archivos reales, debe quedar claro:

- Qué reglas bloquean ratios.
- Qué reglas bloquean importación.
- Qué reglas solo generan advertencia.
- Qué casos requieren revisión humana.
- Qué estados se usarán.
- Qué tolerancias quedan pendientes.
- Qué datos pueden pasar a `RATIO_INPUT`.
- Qué datos quedan solo como RAW.
