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
