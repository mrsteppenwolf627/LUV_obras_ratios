# Revisión humana Fase 1.5: congelación parcial metodológica

## 1. Propósito

Esta fase revisa las decisiones documentales previas antes de permitir análisis de archivos reales o construcción de parsers. El objetivo es separar decisiones que ya pueden congelarse de decisiones que deben seguir abiertas hasta contar con evidencia de datos reales y revisión humana.

## 2. Documentos revisados

- `docs/decisions/master_schema_preliminar.md`
- `docs/decisions/duplicates_and_budget_versions_policy.md`
- `docs/decisions/validation_rules_policy.md`
- `docs/adr/ADR-009-master-schema-preliminar.md`
- `docs/adr/ADR-010-duplicates-and-budget-versions.md`
- `docs/adr/ADR-011-validation-rules.md`
- `CONTEXT.md`
- `ADRs.md`

## 3. Revisión de ADR-009

### Decisiones que pueden congelarse

- El master se diseña por capas y no como una tabla plana única.
- RAW es inmutable y no se sobrescribe.
- Se separan explícitamente datos brutos, normalizados, validación, cálculo de ratios y logs.
- Los datos rechazados/excluidos no se eliminan del histórico.
- Todo ratio debe ser trazable hasta su origen documental.

### Decisiones que NO deben congelarse todavía

- Campos definitivos y cerrados del master.
- Categorías definitivas.
- Superficie base oficial.
- Tolerancias numéricas.
- Tratamiento definitivo de IVA, moneda e inflación.
- Estructura final de exportación.

### Recomendación de estado

- Recomendación: **CONGELADA PARCIALMENTE**.
- Estado actual de la ADR: se mantiene en **PROPUESTA** hasta validación humana explícita.

## 4. Revisión de ADR-010

### Decisiones que pueden congelarse

- Duplicados exactos por hash no deben alimentar ratios dos veces.
- Los duplicados no se eliminan; se conservan con estado y trazabilidad.
- Backups no son fuente principal salvo revisión humana.
- PDF no es fuente automática principal si existe fuente estructurada equivalente.
- Conflictos BC3 vs Excel requieren revisión humana.
- Fases no se suman automáticamente.
- La versión más reciente no siempre es la versión válida.

### Decisiones que NO deben congelarse todavía

- Heurísticas exactas de duplicado lógico.
- Palabras clave definitivas para detectar fases.
- Criterio final de identificación de versión contractual.
- Prioridad definitiva entre fecha de archivo, fecha interna y fecha documental.
- Tratamiento final de presupuestos parciales complejos.

### Recomendación de estado

- Recomendación: **CONGELADA PARCIALMENTE**.
- Estado actual de la ADR: se mantiene en **PROPUESTA** hasta validación humana explícita.

## 5. Revisión de ADR-011

### Decisiones que pueden congelarse

- No calcular ratios sin superficie base.
- No calcular ratios con datos no validados.
- No mezclar monedas en un mismo cálculo de ratios.
- No mezclar tipos de superficie en un mismo cálculo.
- Conflictos no resueltos bloquean la elegibilidad para ratios.
- Las tolerancias numéricas quedan pendientes de decisión humana.
- RAW puede conservarse aunque no alimente ratios.

### Decisiones que NO deben congelarse todavía

- Tolerancias numéricas exactas.
- Umbrales de capítulos sin mapear.
- Umbrales para outliers.
- Criterios definitivos para importes negativos.
- Criterios definitivos para partidas a cero.
- Política de recálculo tras correcciones.

### Recomendación de estado

- Recomendación: **CONGELADA PARCIALMENTE**.
- Estado actual de la ADR: se mantiene en **PROPUESTA** hasta validación humana explícita.

## 6. Lista de decisiones congelables

- Arquitectura por capas con separación RAW/normalización/validación/cálculo/exportación.
- Inmutabilidad del dato RAW.
- Trazabilidad obligatoria de extremo a extremo.
- Exclusión sin borrado físico del histórico.
- No uso de PDF como fuente automática principal cuando haya BC3/Excel.
- No doble conteo por duplicado exacto.
- No suma automática de fases.
- No cálculo de ratios sin superficie base válida.
- No cálculo de ratios con datos no validados o con conflictos no resueltos.
- Gate de revisión humana para casos ambiguos o conflictivos.

## 7. Lista de decisiones pendientes

- Superficie base oficial.
- Categorías definitivas.
- Tolerancias numéricas.
- Tratamiento de IVA.
- Tratamiento de moneda.
- Tratamiento de inflación/año.
- Política final de outliers.
- Criterio final para versiones contractuales.
- Heurísticas de duplicado lógico.
- Umbral de capítulos sin mapear.
- Tratamiento de presupuestos parciales.

## 8. Gate para pasar a análisis de archivos reales

Condiciones mínimas para pasar a Fase 2:

- Fase 1.2 revisada humanamente.
- Fase 1.3 revisada humanamente.
- Fase 1.4 revisada humanamente.
- Decisiones congelables identificadas y aceptadas.
- Decisiones pendientes documentadas y aceptadas como abiertas.
- Aceptación explícita de que el análisis de archivos reales en Fase 2 será solo diagnóstico.
- Confirmación de que en Fase 2 no se actualizará ningún master real.

## 9. Recomendación operativa

Siguiente paso recomendado: **Fase 2 - Análisis controlado de archivos reales de muestra**.

Alcance de Fase 2: diagnóstico de estructura, calidad y variabilidad de fuentes; no parser definitivo y no importación al master.
