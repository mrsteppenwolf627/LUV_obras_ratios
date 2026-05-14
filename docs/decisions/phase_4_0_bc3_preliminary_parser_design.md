# Fase 4.0: diseño documental del parser BC3 preliminar

## 1. Objetivo

Definir el diseño técnico del parser BC3 preliminar antes de implementarlo, manteniendo separación estricta entre parsing, validación, normalización, importación al master y cálculo de ratios.

## 2. Contexto heredado de Fase 3

- Fase 3.1 a 3.5 cerradas con extractor diagnóstico BC3 operativo.
- Readiness real final: `READY_FOR_PRELIMINARY_PARSER_DESIGN`.
- Persisten warnings no bloqueantes y necesidad de revisión humana en datos ambiguos.

## 3. Decisión de pasar a diseño de parser preliminar

Se aprueba iniciar diseño documental de parser preliminar porque no hay bloqueadores de decodificación o estructura mínima en las muestras reales evaluadas.

## 4. Alcance del parser preliminar

- Lectura BC3 no destructiva.
- Parsing estructural inicial de registros principales.
- Salida a estructura intermedia trazable.
- Registro explícito de errores, warnings, unknowns y `manual_review_required`.

## 5. Fuera de alcance

- Parser BC3 definitivo.
- Importación al master.
- Cálculo de ratios.
- Consolidación de importes finales.
- Normalización final de categorías.
- Decisión de superficie base o tolerancias definitivas.

## 6. Entradas esperadas

- Archivos `.bc3` locales.
- Metadatos mínimos del archivo: ruta relativa, hash, tamaño, encoding detectado.

## 7. Salidas esperadas

- JSON intermedio de parsing preliminar.
- Markdown de auditoría de parsing.
- Señales de bloqueos y revisión manual.

## 8. Estructura interna propuesta

1. Descubrimiento de archivos BC3.
2. Lectura y detección de encoding.
3. Tokenización por línea/registro.
4. Parsing por tipo de registro soportado.
5. Ensamblado de estructura intermedia.
6. Emisión de errores, warnings y `manual_review`.
7. Exportación JSON/Markdown diagnóstica de parsing.

## 9. Registros BC3 soportados inicialmente

- `~V` (cabecera/versionado candidato).
- `~C` (conceptos/códigos candidatos).
- `~D` (relaciones jerárquicas básicas).
- `~K`, `~M`, `~T` como soporte preliminar contextual.

## 10. Registros BC3 no soportados o tratados como unknown

- Cualquier tipo distinto del alcance inicial, incluyendo variantes (`~G`, `~L`, `~X`, otros), se conserva en `unknown_record_types` sin romper el proceso salvo bloqueo estructural.

## 11. Tratamiento de encoding

- Intento `utf-8`.
- Fallback `cp1252`.
- Si falla: error bloqueante con trazabilidad de archivo.

## 12. Tratamiento de cabecera `~V`

- Detectar presencia/ausencia.
- Extraer versión FIEBDC candidata de forma diagnóstica.
- Ausencia de `~V`: `ERROR` y posible bloqueo de diseño.

## 13. Tratamiento de conceptos `~C`

- Extraer código bruto + representación sanitizada.
- Clasificación diagnóstica preliminar: capítulo candidato, partida candidata, otro.
- Sin categorización final de negocio.

## 14. Tratamiento de relaciones `~D`

- Parseo padre/hijo cuando exista estructura mínima.
- Detección de relaciones incompletas.
- Cálculo aproximado de profundidad, sin asumir jerarquía total.

## 15. Tratamiento de mediciones (si aplica)

- Solo detección de señales de medición en registros soportados.
- Sin consolidación numérica ni cómputo final.

## 16. Tratamiento de textos

- Capturar métricas textuales básicas (longitud, densidad por tipo).
- Sanitizar y truncar muestras para evitar fuga sensible.

## 17. Tratamiento de unidades

- Detectar unidades presentes por archivo.
- Registrar diversidad/unidades múltiples como warning.
- Sin normalización definitiva.

## 18. Tratamiento de posibles precios/importes

- Detectar tokens numéricos y señales de importe de forma diagnóstica.
- Marcar ambigüedad.
- No consolidar ni decidir precio definitivo.

## 19. Reglas de trazabilidad

- Cada registro parseado debe poder referenciar: archivo, tipo de registro y posición/línea cuando sea viable.
- Mantener vínculo entre dato interpretado y dato ambiguo.

## 20. Reglas de errores

- Errores bloqueantes: lectura/decodificación fallida, ausencia estructural mínima.
- Errores no deben destruir ejecución global del lote; se reportan por archivo.

## 21. Reglas de warnings

- Warnings no bloqueantes: encoding medio, variantes FIEBDC, tokens ambiguos, unidades múltiples.
- Deben quedar explícitos y diferenciados de bloqueadores.

## 22. Reglas de `manual_review`

- Activar cuando exista inconsistencia estructural relevante o ambigüedad no resoluble por heurística segura.
- Debe explicar motivo concreto.

## 23. Estructura JSON preliminar propuesta

- `metadata`: fecha, versión del parser preliminar, política de sensibilidad.
- `files[]`:
  - `file_ref`: id sanitizado, ruta relativa, hash, tamaño.
  - `decode`: encoding, confianza, estado.
  - `header`: `has_v`, `fiebdc_version_candidate`.
  - `records`: conteos por tipo, `unknown_record_types`.
  - `concepts`: clasificaciones candidatas.
  - `relations`: enlaces básicos y métricas de jerarquía.
  - `units`: detectadas.
  - `economic_signals`: diagnóstico sin consolidación.
  - `errors`, `warnings`, `manual_review_required`.
- `global_summary`: readiness para avanzar de fase, no para importar master.

## 24. Estructura Markdown preliminar propuesta

- Resumen ejecutivo del lote.
- Estado por archivo (sanitizado).
- Riesgos y bloqueadores.
- Warnings no bloqueantes.
- Recomendación de siguiente fase.

## 25. Tests mínimos exigidos antes de implementar

1. Detección de `utf-8` y `cp1252`.
2. Error seguro en bytes no decodificables.
3. Detección de `~V`.
4. Parsing básico de `~C`.
5. Parsing básico de `~D` y relaciones incompletas.
6. Registro de `unknown_record_types`.
7. Separación `errors` vs `warnings` vs `manual_review_required`.
8. Persistencia JSON/Markdown.
9. Inmutabilidad de archivos de entrada.

## 26. Riesgos

- Variantes FIEBDC con campos no homogéneos.
- Ambigüedad semántica de códigos y unidades.
- Riesgo de sobreinterpretación económica.
- Riesgo de exposición de datos sensibles si falla sanitización.

## 27. Decisiones pendientes

- Contrato final del parser definitivo.
- Política final de normalización de categorías.
- Tratamiento definitivo de unidades, IVA, moneda, tolerancias y superficie base.
- Criterios finales de importación al master.

## 28. Criterios de aceptación

- Diseño documentado y validado en repositorio.
- Separación explícita entre parsing preliminar y fases posteriores.
- Definidos errores/warnings/manual review y trazabilidad mínima.
- Sin implementación de parser en esta fase.

## 29. Condiciones para pasar a Fase 4.1

1. Aprobación de este diseño documental.
2. Confirmación de alcance acotado (preliminar, no definitivo).
3. Confirmación de que la salida será intermedia y no actualizará master.
4. Confirmación de que ratios siguen fuera de alcance.
