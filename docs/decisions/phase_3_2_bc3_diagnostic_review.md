# Fase 3.2: revision diagnostica de reports BC3 reales

## 1. Objetivo de la revision

Analizar los outputs reales del extractor diagnostico BC3 para identificar hallazgos tecnicos, limites actuales y riesgos antes de decidir la siguiente iteracion, sin crear parser definitivo, sin importar al master y sin calcular ratios.

## 2. Fuentes revisadas

- `reports/bc3_diagnostics/bc3_diagnostic_inventory.json`
- `reports/bc3_diagnostics/bc3_diagnostic_inventory_report.md`
- `docs/decisions/phase_3_bc3_diagnostic_extractor_plan.md`
- `CONTEXT.md`
- `ADRs.md`

Nota: los reports BC3 completos pueden contener metadatos sensibles y deben permanecer fuera de Git cuando incluyan datos reales.

## 3. Archivos BC3 analizados (sanitizado)

- BC3_A (muestra de `proyecto_001`)
- BC3_B (muestra de `proyecto_002`)

## 4. Encodings detectados

- BC3_A: `cp1252` (confianza media)
- BC3_B: `cp1252` (confianza media)

Conclusion: el soporte de `cp1252` es necesario como primera linea en la fase diagnostica.

## 5. Cabeceras y versiones FIEBDC candidatas

- BC3_A: cabecera `~V` presente, candidato `FIEBDC-3/2020`
- BC3_B: cabecera `~V` presente, candidato `FIEBDC-3/2002`

Conclusion: hay coexistencia de variantes FIEBDC en el lote real, por lo que no se debe asumir una unica version.

## 6. Tipos de registros detectados

- BC3_A: `~V`, `~C`, `~D`, `~G`, `~K`, `~L`, `~M`, `~T`, `~X`
- BC3_B: `~V`, `~C`, `~D`, `~K`, `~M`, `~T`

Presencia/ausencia relevante:

- `~V`: presente en ambos.
- `~C`: presente en ambos.
- `~D`: presente en ambos.
- `~K`: presente en ambos.
- `~G`, `~L`, `~X`: observados en BC3_A y no observados en BC3_B.

Implicacion: el futuro parser no puede asumir un conjunto fijo y minimo de tipos de registro.

## 7. Capitulos candidatos y relaciones jerarquicas

- BC3_A:
  - volumen alto de codigos candidatos de capitulo (centenares).
  - relaciones jerarquicas candidatas detectadas: 68.
- BC3_B:
  - volumen alto de codigos candidatos de capitulo (centenares).
  - relaciones jerarquicas candidatas detectadas: 57.

Observacion: se confirma estructura jerarquica no trivial en ambos archivos, suficiente para justificar una fase diagnostica adicional de heuristicas antes de parser definitivo.

## 8. Unidades detectadas

- BC3_A: detectadas unidades como `m2`, `m3`, `m`, `ml`, `ud`, `u`, `kg`, `l`.
- BC3_B: detectadas unidades como `m2`, `m3`, `m`, `ml`, `u`, `kg`, `h`.

Nota: deteccion de unidades es diagnostica; no se fija semantica final ni normalizacion de unidades en esta fase.

## 9. Importes aparentes (sin consolidar)

- BC3_A: indicadores numericos altos y presencia de patrones tipo importe.
- BC3_B: indicadores numericos altos y presencia de patrones tipo importe.

Interpretacion permitida:

- Existe densidad numerica compatible con importes/mediciones en ambos BC3.
- No se consolidan importes.
- No se calculan totales.
- No se calculan ratios.

## 10. Limites del extractor actual

- Deteccion de encoding por heuristica simple (`utf-8` y fallback `cp1252`).
- Extraccion de relaciones basada en patrones basicos por tipo de registro.
- Sin interpretacion semantica completa por variante FIEBDC.
- Sin validacion cruzada interna de coherencia economica.
- Sin capa de sanitizacion automatica de codigos para compartir externo.

## 11. Riesgos para un futuro parser

- Variabilidad de versiones FIEBDC (al menos 2002 y 2020 en muestra real).
- Variabilidad de tipos de registro presentes entre archivos.
- Jerarquias complejas y potencialmente profundas.
- Ambiguedad entre codigos de capitulo y codigos de partida sin reglas explicitas.
- Riesgo de sobreinterpretacion de importes si se acelera a parser definitivo.
- Riesgo de exponer datos sensibles si se versionan reports completos reales.

## 12. Decisiones pendientes

- Reglas definitivas de mapeo capitulo/partida.
- Tratamiento semantico por variante FIEBDC.
- Politica de normalizacion de unidades.
- Politica final de importes (IVA, moneda, tolerancias) en fases posteriores.
- Criterio de sanitizacion automatica de reportes para comparticion.
- Momento de transicion de extractor diagnostico a parser preliminar.

## 13. Recomendacion tecnica

Recomendacion: **ampliar una iteracion adicional de heuristicas diagnosticas BC3 antes de pasar a diseno de parser preliminar**.

Justificacion:

- Ya hay evidencia de heterogeneidad real (versiones y tipos de registro).
- Una capa diagnostica mas rica puede reducir riesgo de diseno prematuro del parser.
- Se mantiene alineacion con ADR-013 (diagnostico antes de parser definitivo).

Alcance sugerido de la siguiente iteracion diagnostica (sin parser definitivo):

1. Refinar deteccion de variantes FIEBDC y metadatos de cabecera.
2. Mejorar heuristicas de clasificacion de codigos (capitulo/subcapitulo/partida candidato).
3. Añadir reporte sanitizado BC3 para comparticion segura.
4. Mantener prohibicion de importacion a master y calculo de ratios.
