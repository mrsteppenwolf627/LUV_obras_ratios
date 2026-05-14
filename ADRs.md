# ADRs.md

Registro de decisiones arquitectonicas del proyecto.

## Indice ADR

- ADR-001: Adaptacion de roles multi-modelo (Aprobado inicial)
- ADR-002: El dato bruto nunca se sobrescribe (Aprobado inicial)
- ADR-003: Separacion entre RAW, normalizado, validacion, calculo y exportacion (Aprobado inicial)
- ADR-004: No se actualizan ratios sin validacion (Aprobado inicial)
- ADR-005: Prioridad de fuentes (Aprobado inicial)
- ADR-006: Trazabilidad obligatoria (Aprobado inicial)
- ADR-007: Exclusion sin borrado (Aprobado inicial)
- ADR-008: Superficie base pendiente de definicion (Aprobado inicial)
- ADR-009: Diseno preliminar del master de ratios (PROPUESTA, ver `docs/adr/ADR-009-master-schema-preliminar.md`)
- ADR-010: Politica preliminar de duplicados y versionado de presupuestos (PROPUESTA, ver `docs/adr/ADR-010-duplicates-and-budget-versions.md`)
- ADR-011: Politica preliminar de validacion matematica y consistencia (PROPUESTA, ver `docs/adr/ADR-011-validation-rules.md`)
- ADR-012: Congelacion parcial metodologica antes del analisis de datos reales (PROPUESTA, ver `docs/adr/ADR-012-freeze-methodology-before-real-data.md`)
- ADR-013: Extractor diagnostico BC3 antes de parser definitivo (Aprobado fase 3)
- ADR-014: Diseno preliminar de parser BC3 antes de importacion al master (Aprobado fase 4.0)

## ADR-001: Adaptacion de roles multi-modelo

**Estado:** Aprobado (inicial)

**Decision**

- ChatGPT coordina y razona.
- Codex implementa backend, parsers, validaciones, tests y auditoria.
- Gemini CLI desarrolla frontend y prototipos visuales.
- Claude no forma parte de la suite actual del estudio.

**Racional**

Separacion explicita de responsabilidades para reducir friccion y mejorar trazabilidad de decisiones.

## ADR-002: El dato bruto nunca se sobrescribe

**Estado:** Aprobado (inicial)

**Decision**

- Todo archivo importado debe conservarse.
- La normalizacion no sustituye al dato original.
- Las correcciones se registran como capas adicionales, no como destruccion del dato fuente.

**Racional**

Garantiza auditoria retroactiva, reproducibilidad y control de cambios de interpretacion.

## ADR-003: Separacion entre RAW, normalizado, validacion, calculo y exportacion

**Estado:** Aprobado (inicial)

**Decision**

El sistema debe separar claramente:

- dato bruto;
- dato normalizado;
- mapeos;
- validaciones;
- ratios calculados;
- logs de importacion;
- exportaciones.

**Racional**

Permite aislar errores por etapa y evita contaminacion de datos entre capas.

## ADR-004: No se actualizan ratios sin validacion

**Estado:** Aprobado (inicial)

**Decision**

- Una importacion solo puede afectar a ratios agregados si supera controles minimos.
- Si faltan datos criticos, la importacion queda pendiente de revision.

**Racional**

Evita introducir ruido sistemico y protege la fiabilidad del master.

## ADR-005: Prioridad de fuentes

**Estado:** Aprobado (inicial)

**Decision inicial**

- BC3 y Excel son fuentes preferentes.
- PDF es respaldo documental o fuente manual, no fuente automatica principal.
- Archivos Presto nativos o PZH requieren analisis antes de considerarse fuente fiable.

**Racional**

Minimiza perdida semantica y reduce errores de extraccion no estructurada.

## ADR-006: Trazabilidad obligatoria

**Estado:** Aprobado (inicial)

**Decision**

Cada dato importado debe poder vincularse a:

- archivo origen;
- hash del archivo;
- fecha de importacion;
- tipo de archivo;
- proyecto;
- linea, hoja, partida o capitulo de origen cuando sea posible.

**Racional**

Habilita auditoria extremo a extremo y depuracion precisa de discrepancias.

## ADR-007: Exclusion sin borrado

**Estado:** Aprobado (inicial)

**Decision**

- Si un dato es incorrecto, dudoso o no comparable, se marca como excluido.
- No se elimina fisicamente del historico.

**Racional**

Mantiene evidencia historica y evita perdida irreversible de contexto.

## ADR-008: Superficie base pendiente de definicion

**Estado:** Aprobado (inicial)

**Decision**

- No se calcularan ratios definitivos si no esta definida la superficie base aplicable.
- La superficie base debe decidirse explicitamente antes de consolidar ratios.

**Racional**

Sin superficie base estable no hay comparabilidad confiable entre proyectos.

## ADR-013: Extractor diagnostico BC3 antes de parser definitivo

**Estado:** Aprobado (fase 3)

**Decision**

- Fase 3 implementa solo un extractor diagnostico BC3.
- Fase 3 no crea parser definitivo BC3.
- Fase 3 no alimenta el master.
- Fase 3 no calcula ratios.
- Fase 3 no decide categorias finales.
- Fase 3 no consolida importes.
- Fase 3 se enfoca en estructura, encoding, tipos de registro y riesgos antes del parser real.

**Racional**

La evidencia de Fase 2.2 muestra variabilidad real de fuentes y necesidad de inspeccion controlada previa. Un extractor diagnostico reduce riesgo de disenar un parser definitivo sobre supuestos incorrectos y preserva la separacion entre diagnostico e integracion al master.

## ADR-014: Diseno preliminar de parser BC3 antes de importacion al master

**Estado:** Aprobado (fase 4.0)

**Decision**

- Antes de implementar parser BC3, se realiza diseno documental preliminar.
- El parser BC3 preliminar no alimenta directamente el master.
- El parser BC3 preliminar produce estructura intermedia trazable.
- Parsing, validacion, normalizacion e importacion se mantienen como fases separadas.
- Los datos ambiguos se marcan para revision humana y no se fuerzan.
- Los registros desconocidos no rompen el proceso salvo bloqueo estructural minimo.
- El calculo de ratios queda explicitamente fuera de alcance en esta fase.

**Racional**

Tras Fase 3.5 hay readiness positivo para diseno preliminar, pero persiste variabilidad de variantes FIEBDC y ambiguedad de senales economicas/unidades. Congelar esta separacion en ADR evita acoplar prematuramente parsing con decisiones de negocio, protege trazabilidad y reduce riesgo de contaminar el master con interpretaciones no consolidadas.
