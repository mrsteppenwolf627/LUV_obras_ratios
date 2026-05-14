# Fase 4.2: contrato de validacion preliminar de estructura intermedia BC3

## 1. Objetivo

Definir e implementar validaciones preliminares sobre la estructura intermedia BC3 para comprobar coherencia estructural, completitud minima y clasificacion de severidades sin invadir fases de normalizacion, importacion o ratios.

## 2. Alcance

- Validacion de JSON generado por `scripts/parse_bc3_preliminary.py`.
- Validacion de bloques globales minimos.
- Validacion por archivo de bloques estructurales requeridos.
- Clasificacion de hallazgos en `INFO`, `WARNING`, `ERROR`, `MANUAL_REVIEW_REQUIRED`, `BLOCKED`.
- Salida JSON y Markdown de validacion en ruta dedicada.

## 3. Fuera de alcance

- Importacion al master.
- Calculo de ratios.
- Consolidacion de importes.
- Normalizacion final de categorias.
- Resolucion definitiva de jerarquia o semantica economica.

## 4. Estructura intermedia esperada

- Nivel global:
  - `metadata`
  - `files`
  - `global_summary`
- Por archivo:
  - `file_ref`
  - `decode`
  - `header`
  - `records`
  - `concepts`
  - `relations`
  - `units`
  - `risk_flags`
  - `errors`
  - `warnings`
  - `manual_review_required`

## 5. Reglas de validacion preliminar

1. Comprobar existencia de `metadata`, `files`, `global_summary`.
2. Comprobar bloques requeridos por archivo.
3. Si no hay cabecera `~V`, marcar `ERROR`.
4. Si no hay conceptos `~C`, marcar `WARNING` y posible `MANUAL_REVIEW_REQUIRED`.
5. Validar `~D` contra conceptos disponibles:
   - padre/hijo no encontrados -> warning y manual review.
   - no resolver jerarquia final.
6. Evaluar `unknown_record_types`:
   - bajo umbral configurable -> `WARNING`.
   - sobre umbral -> `MANUAL_REVIEW_REQUIRED`.
7. Verificar separacion entre errores bloqueantes y warnings.
8. Verificar que `manual_review_required` contiene razones explicitas.

## 6. Severidades

- `INFO`
- `WARNING`
- `ERROR`
- `MANUAL_REVIEW_REQUIRED`
- `BLOCKED`

## 7. Criterios de bloqueo

- JSON no legible o estructura base ausente (`metadata/files/global_summary`).
- Errores estructurales minimos que impidan validar archivos.

## 8. Criterios de warning

- Ausencia de conceptos `~C`.
- Unknown record types por debajo de umbral.
- Relaciones sin correspondencia parcial padre/hijo.

## 9. Criterios de manual_review

- Unknown record types por encima de umbral.
- Relaciones huerfanas reiteradas.
- `manual_review_required` vacio cuando hay ambiguedad estructural relevante.

## 10. Criterios de aceptacion

1. Validador ejecutable sobre JSON intermedio.
2. Emite JSON y Markdown de validacion.
3. Preserva input original sin modificarlo.
4. Separa errores, warnings y manual review.
5. Tests sinteticos en verde.

## 11. Limitaciones conocidas

- No verifica semantica de negocio final.
- No valida importes consolidados.
- No valida mapeo final de categorias.
- No decide version final de presupuesto valido.

## 12. Riesgos

- Alta variabilidad de BC3 puede generar falsos warnings.
- Umbral de unknowns puede requerir ajuste por lote real.
- Dependencia de calidad de parseo preliminar.

## 13. Siguientes pasos

1. Ejecutar validacion sobre salidas preliminares locales.
2. Revisar resultados de severidad y ajustar umbrales si procede.
3. Preparar Fase 4.3 para refinar reglas de validacion estructural antes del parser definitivo.
