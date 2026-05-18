# Fase 4.4.3: análisis acotado de bloqueo estructural en BC3_03 y regresión sintética

## 1. Objetivo

Analizar de forma acotada el bloqueo estructural de `BC3_03` (`ORPHAN_RELATIONS_BLOCKING`) para determinar si el origen está en parser preliminar, validador, variante BC3/FIEBDC o inconsistencia real del archivo.

## 2. Contexto heredado

- Fase 4.4.2 cerrada con 5 BC3 clasificados.
- `BC3_03` quedó en:
  - `validation_readiness=VALIDATION_BLOCKED`
  - `file_eligibility_status=BLOCKED_STRUCTURAL_ISSUE`
- Bloqueador principal: `ORPHAN_RELATIONS_BLOCKING`.

## 3. Evidencia técnica sanitizada de BC3_03 (lectura local)

- Conceptos parseados (`~C`): **517**
- Relaciones parseadas (`~D`): **52**
- Huérfanas según lógica actual de validación: **37/52** (ratio **0.71**)
- Cabecera `~V`: **presente**
- Parse de `~C` y `~D`: **presente** (sin errores de parse)

Detalle relevante:

- Padres huérfanos detectados: `00..34` y `VIVIENDA_UNIFAMILIAR`.
- Hijo huérfano detectado: `00`.
- Para `00..34` y `00` existe su variante con `#` dentro de conceptos (`00#..34#`), por lo que la orfandad masiva proviene mayoritariamente de comparación literal (`code` vs `code#`) y no de ausencia real de concepto.
- `VIVIENDA_UNIFAMILIAR` permanece sin equivalente detectado en conceptos parseados.

## 4. Diagnóstico

1. **No parece fallo principal de parse de `~C`**: hay volumen alto de conceptos y estructura coherente.
2. **No parece fallo principal de parse de `~D`**: hay relaciones parseadas consistentes, pero con codificación heterogénea (`00` frente a `00#`).
3. **Sí hay desalineación de validación por variante de código**:
   - comparación estricta actual no normaliza equivalencia `X`/`X#`;
   - esto infla artificialmente el conteo de huérfanas.
4. **Permanece posible inconsistencia parcial real**:
   - `VIVIENDA_UNIFAMILIAR` no mapea a concepto parseado.

## 5. Clasificación del bloqueo (BC3_03)

- Tipo predominante: **variante BC3/FIEBDC no cubierta en validación** (equivalencia de sufijo `#`).
- Tipo secundario: **inconsistencia real parcial** (referencia raíz no mapeada).
- No hay evidencia suficiente de archivo auxiliar/corrupto.

## 6. Acción aplicada en esta fase

- Ajuste menor y acotado en validador intermedio:
  - normalizar comparación de códigos para aceptar equivalencia entre `code` y `code#`.
- Regresión sintética mínima:
  - caso que reproducía falso positivo de orfandad masiva por sufijo `#`.
  - caso con referencia realmente ausente para mantener bloqueo cuando corresponde.

## 7. Riesgos y límites

- No se implementa parser definitivo.
- No se normalizan categorías finales ni importes.
- No se calcula ratio económico.
- La equivalencia `code`/`code#` se limita a validación de pertenencia en conceptos.

## 8. Estado recomendado tras 4.4.3

- Tratar el patrón `X` vs `X#` como variante cubierta en validación preliminar.
- Mantener bloqueo estructural cuando persistan referencias sin equivalente real.
- Re-ejecutar validación del corpus para confirmar nuevo estado real de `BC3_03`.
