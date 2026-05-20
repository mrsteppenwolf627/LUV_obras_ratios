# Fase 9.11: cierre post-piloto real dry-run y plan de endurecimiento

## 1. Objetivo de la fase

Cerrar formalmente los resultados de Fase 9.10, consolidar hallazgos reales por archivo sanitizado y definir el plan tecnico de endurecimiento previo a cualquier futura promocion `PREVIEW_ONLY -> OPERATIVE`.

## 2. Contexto desde Fase 9.10

- Fase 9.10 quedo cerrada tecnicamente con evidencia real multi-archivo en modo local y dry-run.
- El flujo mostro una primera candidatura operativa en `XLSX`, pero no habilita promocion general.
- Se mantienen las restricciones: sin promocion operativa, sin actualizacion de master operativo, sin ratios finales, sin normalizacion final, sin consolidacion definitiva de importes y sin modificaciones RAW.

## 3. Resumen ejecutivo del piloto real dry-run

- Resultado global: capacidad real inicial validada para un subconjunto `XLSX`, con bloqueos tecnicos aun abiertos para robustez y cobertura multi-formato.
- Hallazgo principal positivo: preservacion y trazabilidad estables.
- Hallazgos principales pendientes: separacion economica heterogenea en `XLSX` y ausencia de ruta preservada `BC3` en flujo 9.x.
- Decision 9.11: cierre documental con plan tecnico de endurecimiento antes de repetir prueba real o permitir promocion operativa.

## 4. Tabla de resultados por archivo sanitizado

| run_id | formato | estado | mapping_rate | traceability_rate | amount_separation_rate | motivos relevantes |
|---|---|---|---:|---:|---:|---|
| REAL_DRY_RUN_001 | XLSX | OPERATIVE_CANDIDATE | 0.7938144329896907 | 1.0 | 1.0 | limitacion de deteccion de cabeceras economicas |
| REAL_DRY_RUN_002 | BC3 | PROMOTION_BLOCKED | 0.0 | 0.0 | 0.0 | format_not_supported_for_preview_phase_9_10 |
| REAL_DRY_RUN_003 | XLSX | PROMOTION_BLOCKED | 0.8048780487804879 | 1.0 | 0.0 | amount_mixed_in_description; insufficient_amount_separation |

## 5. Que funciono correctamente

- Preservacion visible de input en previews `XLSX`.
- Trazabilidad por fila/hoja en casos `XLSX` evaluados (`traceability_rate = 1.0`).
- Aplicacion correcta de bloqueo en casos no aptos.
- No se alimentaron `RATIO_INPUTS` ni `RATIOS_CALCULATED`.
- No hubo promocion automatica ni actualizacion de master operativo.

## 6. Que fallo o quedo bloqueado

- Ruta de preview preservada para `BC3` inexistente en fase 9.10 (`PROMOTION_BLOCKED` tecnico de flujo).
- Extraccion economica insuficiente en `XLSX` heterogeneo (`REAL_DRY_RUN_003`).
- `mapping_rate` aun con margen de mejora para reducir `UNMAPPED`.

## 7. Evaluacion de XLSX

- Estado: parcialmente apto bajo condiciones.
- Evidencia: un caso `OPERATIVE_CANDIDATE` y un caso `PROMOTION_BLOCKED` por separacion economica.
- Conclusión: la preservacion/trazabilidad es solida, pero la robustez economica no es uniforme en layouts reales heterogeneos.

## 8. Evaluacion de BC3

- Estado: bloqueado en flujo 9.x actual para preview preservada.
- `REAL_DRY_RUN_002` no implica fallo del parser general BC3: el bloqueo corresponde al contrato de preview de esta fase.
- Presto/PZH permanecen fuera del alcance de esta fase; se mantiene ADR-018 como marco.

## 9. Evaluacion de preservacion del input

- Correcta en los `XLSX` con previews generadas (`REAL_DRY_RUN_001` y `REAL_DRY_RUN_003`).
- Pendiente para `BC3` dentro de un formato de preservacion equivalente en el master.

## 10. Evaluacion de mapping preserved -> COST_ITEMS

- Resultado: funcional pero no maduro para ingesta operativa general.
- Lectura: `mapping_rate` ~0.79-0.80 en `XLSX` evaluados, con volumen aun mejorable de filas no mapeadas.
- Necesidad: clasificar mejor filas no presupuestarias vs partidas reales para reducir ruido en `UNMAPPED`.

## 11. Evaluacion de separacion de campos economicos

- `REAL_DRY_RUN_001`: `amount_separation_rate = 1.0`.
- `REAL_DRY_RUN_003`: `amount_separation_rate = 0.0`, con `amount_mixed_in_description` e `insufficient_amount_separation`.
- Conclusion: la separacion economica es actualmente el bloqueo tecnico prioritario para robustez `XLSX`.

## 12. Evaluacion de umbrales preliminares

- `traceability_rate` y `blocked_rate` muestran comportamiento coherente con el contrato.
- `amount_separation_rate` discrimina correctamente entre candidato y bloqueo.
- Muestra insuficiente (3 archivos) para fijar umbrales definitivos; mantener caracter preliminar.

## 13. Analisis obligatorio de resultados Fase 9.10

### REAL_DRY_RUN_001

- Formato: `XLSX`.
- Estado: `OPERATIVE_CANDIDATE`.
- Trazabilidad: correcta.
- `amount_separation_rate = 1.0`.
- `mapping_rate` aproximado: `0.79`.
- Limitacion: deteccion de cabeceras economicas parcial.
- No se promovio.
- No alimento ratios.

### REAL_DRY_RUN_002

- Formato: `BC3`.
- Estado: `PROMOTION_BLOCKED`.
- Motivo: `format_not_supported_for_preview_phase_9_10`.
- Conclusion: no se considera fallo del parser general BC3 en esta fase; el bloqueo es de ruta preservada en flujo 9.x.
- Presto/PZH: fuera del alcance de esta fase.

### REAL_DRY_RUN_003

- Formato: `XLSX`.
- Estado: `PROMOTION_BLOCKED`.
- Trazabilidad: correcta.
- `mapping_rate` aproximado: `0.80`.
- `amount_separation_rate = 0.0`.
- Motivos:
  - `amount_mixed_in_description`
  - `insufficient_amount_separation`
- Conclusion: preservacion correcta con extraccion economica insuficiente.

## 14. Bloqueos antes de promocion operativa

1. Separacion economica inconsistente en `XLSX` heterogeneo.
2. Cobertura de mapping insuficiente para reducir `UNMAPPED` con confianza operativa.
3. Ausencia de ruta preservada `BC3` en flujo 9.x preview.
4. Muestra real aun pequena para congelar umbrales finales.

## 15. Plan de endurecimiento tecnico

### Linea A: XLSX economico heterogeneo

Objetivo: mejorar extraccion de campos economicos en `XLSX`.

Tareas:

- Mejorar deteccion de cabeceras economicas.
- Detectar columnas de importe con nombres variables.
- Detectar cantidad/precio/importe por patrones numericos.
- Evitar importes embebidos en descripcion.
- Identificar filas total/subtotal/capitulo/partida.
- Mejorar heuristicas multi-hoja.
- Anadir fixtures sinteticas con layouts heterogeneos.
- Anadir tests de separacion descripcion/importe.

### Linea B: Mapping preserved -> COST_ITEMS

Objetivo: reducir filas `UNMAPPED` cuando exista evidencia suficiente.

Tareas:

- Mejorar reglas de mapping por fila origen.
- Mejorar mapping por `item_code`.
- Mejorar mapping por descripcion + importe.
- Distinguir fila preservada no presupuestaria de partida real.
- Introducir estados explicitos:
  - `MAPPED`
  - `UNMAPPED`
  - `NOT_COST_ITEM`
  - `AMBIGUOUS`
  - `MANUAL_REVIEW_REQUIRED`
- Anadir tests sinteticos de clasificacion/mapping.

### Linea C: Ruta BC3 preservada

Objetivo: definir representacion preservada de `BC3` dentro del master.

Tareas:

- Definir hoja preservada visible equivalente para BC3.
- Crear vista por registros/capitulos/partidas.
- Conservar registros originales sanitizados.
- Mapear registros BC3 hacia `COST_ITEMS`.
- Mantener trazabilidad `source_record_type` / `source_record_index`.
- No incluir aun Presto/PZH en esta implementacion.

### Linea D: Recalibracion de umbrales

Objetivo: revisar realismo de umbrales preliminares con mayor muestra.

Tareas:

- Revisar `traceability_rate`.
- Revisar `amount_separation_rate`.
- Revisar `mapping_rate`.
- Revisar `manual_review_rate`.
- Mantener `blocked_rate = 0` para promocion.
- No congelar umbrales definitivos con solo tres archivos.

## 16. Priorizacion recomendada para Fase 9.12

1. Linea A (`XLSX` economico heterogeneo y separacion importe-descripcion).
2. Linea B (mapping `preserved -> COST_ITEMS`).
3. Linea C (ruta `BC3` preservada en flujo 9.x).
4. Linea D (recalibracion de umbrales con muestra ampliada).

Justificacion: A y B atacan directamente el bloqueo observado en `XLSX` y maximizan impacto inmediato para repetir prueba real con mejor tasa de candidatura; C amplia cobertura de formato; D requiere evidencia ampliada posterior.

## 17. Criterios de cierre para repetir prueba real

- Heuristicas de separacion economica reforzadas y validadas con fixtures sinteticas heterogeneas.
- Cobertura de tests ampliada para mapping y separacion.
- Reduccion medible de falsos bloqueos por `amount_mixed_in_description`.
- Evidencia de mejora de `mapping_rate` sin degradar `traceability_rate`.
- Ejecucion dry-run multi-archivo repetida sin promocion operativa.

## 18. Condiciones minimas para futura promocion OPERATIVE

- Cumplimiento de contrato `PREVIEW_ONLY -> OPERATIVE` de Fase 9.6.
- `traceability_rate` alto y estable; `blocked_rate = 0`; `critical_errors = 0`.
- Separacion economica robusta en `XLSX` reales heterogeneos.
- Mapping `preserved -> COST_ITEMS` suficientemente fiable con estados explicitos.
- Rutas y bloqueos por formato documentados y auditables.
- Promocion siempre explicita, trazada, reversible y nunca automatica.

## 19. Riesgos

- Sobreajuste de heuristicas a pocos layouts reales.
- Incremento de complejidad de parsing sin cobertura de tests adecuada.
- Falsa sensacion de readiness por muestra limitada.
- Ambiguedad de filas no presupuestarias degradando mapping.

## 20. Limitaciones

- Muestra real de Fase 9.10 pequena (3 archivos).
- BC3 sin preview preservada dentro del flujo 9.x en esta fase.
- Umbrales aun preliminares.
- Sin ejecucion operativa real ni alimentacion de ratios.

## 21. Decisiones pendientes

- Diseno final de vista preservada BC3 en el master.
- Contrato exacto de estados de mapping ampliados.
- Criterios cuantitativos finales para promocion operativa.
- Tamano minimo de muestra real para fijar umbrales definitivos.

## 22. Recomendacion para Fase 9.12

Abrir Fase 9.12 como fase tecnica de endurecimiento incremental (A -> B -> C -> D), manteniendo bloqueo de promocion automatica y ejecutando nuevas pruebas reales solo en modo dry-run aislado, con IDs sanitizados y salidas locales ignoradas por Git.
