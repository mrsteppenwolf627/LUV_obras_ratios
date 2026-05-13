# ADRs.md

Registro de decisiones arquitect?nicas del proyecto.

## ADR-001: Adaptaci?n de roles multi-modelo

**Estado:** Aprobado (inicial)

**Decisi?n**

- ChatGPT coordina y razona.
- Codex implementa backend, parsers, validaciones, tests y auditor?a.
- Gemini CLI desarrolla frontend y prototipos visuales.
- Claude no forma parte de la suite actual del estudio.

**Racional**

Separaci?n expl?cita de responsabilidades para reducir fricci?n y mejorar trazabilidad de decisiones.

## ADR-002: El dato bruto nunca se sobrescribe

**Estado:** Aprobado (inicial)

**Decisi?n**

- Todo archivo importado debe conservarse.
- La normalizaci?n no sustituye al dato original.
- Las correcciones se registran como capas adicionales, no como destrucci?n del dato fuente.

**Racional**

Garantiza auditor?a retroactiva, reproducibilidad y control de cambios de interpretaci?n.

## ADR-003: Separaci?n entre RAW, normalizado, validaci?n, c?lculo y exportaci?n

**Estado:** Aprobado (inicial)

**Decisi?n**

El sistema debe separar claramente:

- dato bruto;
- dato normalizado;
- mapeos;
- validaciones;
- ratios calculados;
- logs de importaci?n;
- exportaciones.

**Racional**

Permite aislar errores por etapa y evita contaminaci?n de datos entre capas.

## ADR-004: No se actualizan ratios sin validaci?n

**Estado:** Aprobado (inicial)

**Decisi?n**

- Una importaci?n solo puede afectar a ratios agregados si supera controles m?nimos.
- Si faltan datos cr?ticos, la importaci?n queda pendiente de revisi?n.

**Racional**

Evita introducir ruido sist?mico y protege la fiabilidad del master.

## ADR-005: Prioridad de fuentes

**Estado:** Aprobado (inicial)

**Decisi?n inicial**

- BC3 y Excel son fuentes preferentes.
- PDF es respaldo documental o fuente manual, no fuente autom?tica principal.
- Archivos Presto nativos o PZH requieren an?lisis antes de considerarse fuente fiable.

**Racional**

Minimiza p?rdida sem?ntica y reduce errores de extracci?n no estructurada.

## ADR-006: Trazabilidad obligatoria

**Estado:** Aprobado (inicial)

**Decisi?n**

Cada dato importado debe poder vincularse a:

- archivo origen;
- hash del archivo;
- fecha de importaci?n;
- tipo de archivo;
- proyecto;
- l?nea, hoja, partida o cap?tulo de origen cuando sea posible.

**Racional**

Habilita auditor?a extremo a extremo y depuraci?n precisa de discrepancias.

## ADR-007: Exclusi?n sin borrado

**Estado:** Aprobado (inicial)

**Decisi?n**

- Si un dato es incorrecto, dudoso o no comparable, se marca como excluido.
- No se elimina f?sicamente del hist?rico.

**Racional**

Mantiene evidencia hist?rica y evita p?rdida irreversible de contexto.

## ADR-008: Superficie base pendiente de definici?n

**Estado:** Aprobado (inicial)

**Decisi?n**

- No se calcular?n ratios definitivos si no est? definida la superficie base aplicable.
- La superficie base debe decidirse expl?citamente antes de consolidar ratios.

**Racional**

Sin superficie base estable no hay comparabilidad confiable entre proyectos.
