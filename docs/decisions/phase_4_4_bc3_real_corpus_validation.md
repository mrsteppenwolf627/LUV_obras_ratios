# Fase 4.4: validación ampliada con corpus BC3 real

## 1. Objetivo

Evaluar robustez del parser preliminar (`scripts/parse_bc3_preliminary.py`) y del validador intermedio (`scripts/validate_bc3_intermediate.py`) sobre un corpus BC3 real ampliado local, manteniendo el alcance no destructivo de fases previas.

## 2. Alcance y restricciones activas

- Solo análisis BC3.
- Ignorados en esta fase: Excel, PDF, Presto, PrestoBackup, PrestoRecord, PZH y otros formatos no BC3.
- Sin importación al master.
- Sin cálculo de ratios.
- Sin consolidación de importes.
- Sin normalización de categorías finales.
- Sin modificación de RAW.
- Sin subida de muestras reales.
- Sin subida de outputs reales sensibles.

## 3. Protección de datos y versionado

- `data/samples/` está protegido en `.gitignore` (`data/samples/*` con excepción de `.gitkeep`).
- El corpus real se usó solo localmente.
- No se documentan nombres reales, rutas absolutas ni contenido literal sensible.
- En este documento se usan identificadores sanitizados del tipo `BC3_001..BC3_005`.

## 4. Ejecución realizada

1. Inventario recursivo de `data/samples/` para conteo global y detección BC3.
2. Ejecución secuencial:
   - `python scripts/parse_bc3_preliminary.py`
   - `python scripts/validate_bc3_intermediate.py`
3. Revisión local de JSON/Markdown de salida sin versionarlos.

## 5. Resumen sanitizado del corpus

- Total de archivos en `data/samples/`: **24**
- BC3 detectados recursivamente: **5**
- BC3 analizados por parser: **5**
- BC3 parseados correctamente (sin `errors`): **4**
- BC3 con validación generada: **5**

Readiness por archivo (sanitizado):

- `VALIDATION_READY_FOR_STRICTER_PARSER_DESIGN`: **0**
- `VALIDATION_READY_WITH_NON_BLOCKING_MANUAL_REVIEW`: **3**
- `VALIDATION_NEEDS_MINOR_ADJUSTMENTS`: **0**
- `VALIDATION_BLOCKED`: **2**

Resultado global del corpus:

- `validation_metadata.status`: **ERROR**
- `validation_readiness.global`: **VALIDATION_BLOCKED**

## 6. Hallazgos frecuentes (sanitizados)

Warnings más frecuentes (top):

- `RELATION_CHILD_NOT_IN_CONCEPTS`: 71
- `RELATION_PARENT_NOT_IN_CONCEPTS`: 36
- `AMBIGUOUS_ECONOMIC_TOKENS`: 4
- `ENCODING_MEDIUM_CONFIDENCE`: 4
- `MULTIPLE_UNITS_DETECTED`: 4

Manual review más frecuente (top):

- `MULTIPLE_UNITS_NON_BLOCKING`: 4
- `AMBIGUOUS_ECONOMIC_TOKENS_NON_BLOCKING`: 4
- `RELATION_ORPHAN_CHILD_NON_BLOCKING`: 3
- `UNKNOWN_RECORDS_UNDER_THRESHOLD`: 1
- `UNKNOWN_RECORDS_OVER_THRESHOLD`: 1

Bloqueos reales detectados:

- `MISSING_V_HEADER`
- `CONCEPTS_ABSENT_REVIEW`
- `ORPHAN_RELATIONS_BLOCKING`

## 7. Unknown records detectados (sanitizados)

Tipos detectados en el corpus ampliado:

- `~G`
- `~L`
- `~X`

Conclusión: los unknowns observados no son por sí mismos el principal bloqueo global; el bloqueo aparece por estructura mínima insuficiente en una parte del corpus.

## 8. Patrones nuevos y clasificación

1. **Asumibles**
- Alta frecuencia de relaciones con referencias fuera de conceptos parseados, manteniéndose no bloqueantes cuando la orfandad no supera umbral crítico.
- Variantes unknown (`~G/~L/~X`) preservadas como contexto diagnóstico.

2. **Requieren fixture sintética de regresión**
- Mezcla real de formatos no BC3 dentro de `data/samples/` con BC3 en subcarpetas: se protege con test sintético para asegurar descubrimiento recursivo solo BC3 e ignorar no BC3.

3. **Requieren ajuste menor**
- No se identifica ajuste menor obligatorio adicional en esta fase; `minor_adjustment_items` permanece en 0 en el resultado validado final del corpus.

4. **Bloquean avance**
- Subconjunto del corpus con señales de bloqueo estructural (`MISSING_V_HEADER`, `CONCEPTS_ABSENT_REVIEW`, `ORPHAN_RELATIONS_BLOCKING`).

## 9. Conclusión de fase

Con el corpus ampliado actual, el estado global queda en `VALIDATION_BLOCKED` por bloqueos estructurales reales en parte de los BC3. No procede avanzar directamente a parser más estricto para todo el lote sin una estrategia acotada para esos casos bloqueados.

## 10. Recomendación

- Mantener avance selectivo: separar BC3 listos/no bloqueantes de BC3 bloqueados.
- Abrir ajuste acotado posterior solo para bloqueos estructurales detectados en este corpus (sin ampliar parser de forma general).
- Repetir validación sobre corpus ampliado tras ese ajuste.
