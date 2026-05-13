# Política Preliminar de Duplicados y Versionado de Presupuestos

## 1. Propósito

Esta política define cómo detectar, clasificar y tratar duplicados, versiones de presupuesto y fuentes múltiples antes de alimentar el master de ratios.

## 2. Alcance

Aplica a los siguientes casos:

- Archivos idénticos con mismo hash.
- Archivos idénticos con distinto nombre.
- Archivos con mismo nombre pero distinto contenido.
- Excel y BC3 del mismo presupuesto.
- PDF de contrato junto a BC3 o Excel.
- Archivos Presto o PZH no interpretados.
- Carpetas `_bkp`.
- Presupuestos por fases.
- Presupuestos actualizados.
- Versiones de contrato.
- Versiones preliminares.
- Versiones parciales.
- Versiones finales.

## 3. Definiciones

### Duplicado exacto

Archivo con el mismo hash que otro ya registrado.

### Duplicado lógico

Archivo distinto a nivel de hash, pero que parece representar el mismo presupuesto, proyecto o versión.

### Versión de presupuesto

Archivo que representa una evolución de un presupuesto anterior.

### Fuente principal

Archivo usado como base estructurada para extracción automática.

### Fuente secundaria

Archivo usado para contraste, revisión o complemento.

### Fuente de referencia

Archivo conservado para trazabilidad documental, pero no usado para cálculo automático.

### Backup

Archivo o carpeta que parece copia de seguridad.

### Versión aprobada

Presupuesto que puede considerarse válido para consolidación si supera validaciones.

### Versión contractual

Presupuesto asociado a contrato, adjudicación o documento formal.

### Versión parcial

Presupuesto que cubre solo una fase, capítulo o alcance parcial.

## 4. Criterios de detección de duplicados

Reglas preliminares de clasificación, sin implementación automática en esta fase.

### Criterios fuertes

- Mismo hash.
- Mismo tamaño y mismo hash.
- Misma ruta relativa y mismo hash.
- Mismo archivo detectado en carpeta normal y backup.

### Criterios medios

- Mismo nombre normalizado.
- Mismo proyecto detectado.
- Misma fecha de archivo.
- Misma extensión.
- Mismo total declarado.
- Mismo número de capítulos o partidas.
- Misma estructura de capítulos.

### Criterios débiles

- Nombres parecidos.
- Fechas cercanas.
- Códigos de proyecto similares.
- Textos como `actualizado`, `final`, `contrato`, `fase`, `mediciones`, `copia`, `backup`.

Los criterios medios y débiles no deben excluir automáticamente sin validación o revisión humana.

## 5. Clasificación de archivos

Etiquetas preliminares:

- `UNIQUE`
- `EXACT_DUPLICATE`
- `LOGICAL_DUPLICATE`
- `VERSION_CANDIDATE`
- `BACKUP_COPY`
- `PRIMARY_SOURCE_CANDIDATE`
- `SECONDARY_SOURCE`
- `REFERENCE_ONLY`
- `MANUAL_REVIEW_REQUIRED`
- `REJECTED_FOR_IMPORT`
- `SUPERSEDED_BY_NEWER_VERSION`

## 6. Prioridad preliminar de fuentes

Prioridad inicial:

1. BC3 estructurado válido.
2. Excel estructurado válido.
3. Archivo Presto/PZH interpretable, si en el futuro se confirma lectura fiable.
4. PDF contractual como referencia o validación manual.
5. PDF no estructurado como referencia documental.
6. Backup solo como respaldo si no existe fuente principal válida.

Esta prioridad puede cambiar tras análisis real de archivos.

## 7. Política para BC3 vs Excel

### BC3 y Excel coinciden

- Elegir BC3 como fuente principal si contiene estructura más completa.
- Marcar Excel como fuente secundaria o referencia.
- No duplicar importes en ratios.

### BC3 y Excel difieren

- No decidir automáticamente.
- Marcar conflicto.
- Crear `VALIDATION_RESULT`.
- Requiere revisión humana.

### Solo Excel disponible

- Puede ser fuente principal si pasa validaciones.

### Solo BC3 disponible

- Puede ser fuente principal si pasa validaciones.

### Solo PDF disponible

- No usar automáticamente para ratios.
- Marcar como `MANUAL_ONLY` o `REFERENCE_ONLY` salvo revisión manual.

## 8. Política de presupuestos por fases

Casos de referencia: Fase 1, Fase 2, mediciones de fase actualizada, proyecto completo frente a alcance parcial.

Reglas preliminares:

- No sumar fases automáticamente si no hay evidencia clara.
- Cada fase debe conservar su identidad.
- Una fase no debe reemplazar al presupuesto total.
- Si varias fases forman un presupuesto completo, debe existir relación explícita.
- Si no se puede determinar, marcar `MANUAL_REVIEW_REQUIRED`.

## 9. Política de versiones actualizadas

Reglas preliminares:

- Una versión nueva no borra una anterior.
- La anterior puede quedar `SUPERSEDED_BY_NEWER_VERSION`.
- La versión más reciente no siempre es la válida.
- Una versión contractual puede tener prioridad sobre una versión actualizada si esta no está aprobada.
- El sistema debe registrar relación entre versiones.

Campos sugeridos:

- `previous_budget_version_id`
- `supersedes_budget_version_id`
- `version_relation_type`
- `version_confidence`
- `version_decision_reason`
- `decided_by`
- `decided_at`

## 10. Política de contratos y PDFs

- PDF contractual puede ser documento de referencia.
- No se extraerán importes automáticamente de PDF en fases iniciales.
- Si hay conflicto entre contrato PDF y BC3/Excel, se marca conflicto.
- La revisión humana decide si el contrato fija la versión válida.
- Toda decisión debe registrarse.

## 11. Política de backups

- Carpetas o nombres con `_bkp`, `backup`, `copia`, `old`, `antiguo` se clasifican inicialmente como `BACKUP_COPY`.
- No se usan como fuente principal si existe fuente equivalente fuera de backup.
- Se conservan para recuperación o trazabilidad.
- Pueden usarse si no existe otra fuente y revisión humana lo aprueba.

## 12. Reglas de decisión automática

Puede decidir automáticamente:

- `EXACT_DUPLICATE` si hash idéntico.
- `BACKUP_COPY` si está en carpeta claramente marcada como backup.
- `REFERENCE_ONLY` para PDF si existe BC3/Excel equivalente.
- `MANUAL_REVIEW_REQUIRED` si hay conflicto.

No puede decidir automáticamente:

- Que una versión actualizada es válida para ratios.
- Que dos fases suman presupuesto completo.
- Que un PDF contradice definitivamente a un BC3.
- Que un Excel reemplaza a un BC3.
- Que una versión contractual está aprobada si no hay evidencia.

## 13. Reglas de exclusión

- Los duplicados exactos no se eliminan.
- Se marcan como duplicados y se excluyen de cálculo.
- Las versiones `SUPERSEDED` no alimentan ratios si hay una versión válida más reciente o aprobada.
- Las fuentes de referencia no alimentan ratios directamente.
- Toda exclusión debe registrar motivo y ser reversible.

## 14. Estados recomendados

### duplicate_status

- `NOT_CHECKED`
- `UNIQUE`
- `EXACT_DUPLICATE`
- `LOGICAL_DUPLICATE_CANDIDATE`
- `DUPLICATE_CONFIRMED`
- `NOT_DUPLICATE`
- `MANUAL_REVIEW_REQUIRED`

### version_status

- `NOT_VERSIONED`
- `VERSION_CANDIDATE`
- `CURRENT`
- `SUPERSEDED`
- `CONTRACTUAL`
- `APPROVED`
- `REJECTED`
- `PARTIAL`
- `MANUAL_REVIEW_REQUIRED`

### source_role

- `PRIMARY`
- `SECONDARY`
- `REFERENCE`
- `BACKUP`
- `MANUAL_ONLY`
- `EXCLUDED`

### conflict_status

- `NO_CONFLICT`
- `POSSIBLE_CONFLICT`
- `CONFIRMED_CONFLICT`
- `RESOLVED`
- `MANUAL_REVIEW_REQUIRED`

## 15. Impacto en el master schema

Entidades afectadas del esquema preliminar:

- `SOURCE_FILE`
- `IMPORT_BATCH`
- `BUDGET_VERSION`
- `VALIDATION_RESULT`
- `EXCLUSION`
- `RATIO_INPUT`

Campos adicionales candidatos (propuesta):

- `SOURCE_FILE`: `duplicate_status`, `source_role`, `conflict_status`, `duplicate_of_source_file_id`.
- `BUDGET_VERSION`: `version_status`, `previous_budget_version_id`, `supersedes_budget_version_id`, `version_relation_type`.
- `VALIDATION_RESULT`: reglas de conflicto entre fuentes.
- `EXCLUSION`: motivos específicos de duplicidad/versionado.
- `RATIO_INPUT`: exclusión explícita de duplicados y versiones no aprobadas.

## 16. Casos de ejemplo abstractos

### Caso A

Mismo BC3 aparece dos veces con distinto nombre de archivo: se clasifica como `EXACT_DUPLICATE` si hash coincide.

### Caso B

BC3 y Excel del mismo presupuesto: BC3 candidato a principal, Excel secundario o referencia, sin doble cómputo.

### Caso C

Contrato PDF y mediciones BC3: PDF como referencia, BC3 para extracción estructurada, conflicto si los metadatos no encajan.

### Caso D

Fase 1 y Fase 2: conservar separado, sin suma automática, relación explícita si representan un conjunto.

### Caso E

Archivo en carpeta `_bkp` y archivo equivalente fuera de backup: backup marcado como `BACKUP_COPY`.

### Caso F

Versión actualizada y versión contractual: no se reemplaza automáticamente; revisión humana para elegir versión válida para ratios.

## 17. Pendientes de decisión humana

- Cómo identificar versión contractual de forma fiable.
- Qué palabras clave internas se usarán para detectar fases.
- Qué palabras clave internas se usarán para detectar actualización.
- Qué hacer cuando una versión actualizada contradice contrato.
- Si se prioriza fecha de modificación, fecha del documento o fecha interna del presupuesto.
- Cómo tratar presupuestos parciales.
- Cómo tratar presupuestos con alcance ampliado.
- Cómo tratar presupuestos con IVA o sin IVA.
- Qué usuario o rol puede aprobar una versión para ratios.

## 18. Criterios para pasar a análisis de archivos reales

Antes de analizar archivos reales, debe quedar claro:

- Qué es un duplicado exacto.
- Qué es un duplicado lógico.
- Qué es una versión.
- Qué es una fuente principal.
- Qué casos requieren revisión humana.
- Qué estados se usarán en el master.
