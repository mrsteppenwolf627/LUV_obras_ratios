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
- ADR-015: Normalizacion intermedia BC3 antes de importacion al master (Aprobado fase 5.0)
- ADR-016: Estrategia multi-formato con prioridad Excel y Presto/PZH (Aprobado fase 5.3)
- ADR-017: Contrato comun multi-formato para lectura y normalizacion intermedia (Aprobado fase 7.2)
- ADR-018: Soporte obligatorio Presto/PZH mediante ruta tecnica evidenciada (Aprobado fase 8)
- ADR-019: Excel maestro vivo como salida principal del sistema (Aprobado fase 9.0)

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

## ADR-015: Normalizacion intermedia BC3 antes de importacion al master

**Estado:** Aprobado (fase 5.0)

**Decision**

- La normalizacion intermedia BC3 se disena e implementa en capa separada y no importa datos al master en esta fase.
- La normalizacion intermedia no calcula ratios.
- La normalizacion intermedia no consolida importes finales.
- La normalizacion intermedia no decide categorias finales.
- La normalizacion intermedia preserva trazabilidad a BC3 (archivo, registro y contexto de origen cuando aplique).
- Los datos ambiguos se marcan y quedan para revision humana; no se fuerzan interpretaciones.
- `CATEGORY_MAPPING` se define en una fase posterior.
- La importacion al master se define en una fase posterior con contrato y validaciones propias.

**Racional**

Con Fase 4 cerrada tecnicamente (parser y validador estrictos operativos, avance permitido sobre subconjunto valido con exclusiones controladas), el siguiente paso requiere estructurar datos sin mezclar decisiones de negocio final. Esta separacion reduce riesgo de sobreinterpretacion, protege auditabilidad y mantiene control de alcance antes de mapping final y carga al master.

## ADR-016: Estrategia multi-formato con prioridad Excel y Presto/PZH

**Estado:** Aprobado (fase 5.3)

**Decision**

- BC3 se mantiene como modulo avanzado disponible, pero deja de ser prioridad unica del roadmap.
- Se pausa el endurecimiento adicional de schema BC3 previsto tras Fase 5.2.
- Excel y Presto/PZH pasan a prioridad alta por frecuencia real de uso en fuentes del negocio.
- El siguiente bloque de trabajo se centra en diagnostico tecnico por formato (Excel y Presto/PZH) antes de nuevas implementaciones de extraccion/normalizacion.
- Se mantiene el marco de restricciones: sin importacion al master, sin calculo de ratios, sin consolidacion final de importes, sin normalizacion final de categorias y sin UX en esta etapa.

**Racional**

La evidencia operativa indica que BC3 no sera siempre la fuente principal y que Excel/Presto/PZH tendran mayor presencia. Continuar invirtiendo solo en BC3 incrementa riesgo de desalineacion con la realidad de entrada. La estrategia multi-formato reduce ese riesgo, preserva el trabajo ya consolidado de BC3 y reequilibra esfuerzo hacia las fuentes con mayor impacto esperado.

## ADR-017: Contrato comun multi-formato para lectura y normalizacion intermedia

**Estado:** Aprobado (fase 7.2)

**Decision**

- El sistema debe converger a un contrato comun de lectura y diagnostico para Excel, Presto/PZH y BC3.
- Excel requiere lector integral y una normalizacion intermedia antes de cualquier mapping final.
- Presto/PZH se investigan primero con diagnostico tecnico para decidir si existe lectura directa o si requiere exportacion externa.
- BC3 permanece como modulo avanzado ya operativo y no debe bloquear la consolidacion multi-formato.
- Ningun formato debe importar al master ni calcular ratios en esta fase.

**Racional**

La realidad operativa mezcla formatos con frecuencias distintas. Un contrato comun evita desarrollar silos incompatibles, mantiene trazabilidad comparativa entre formatos y permite decidir por evidencia tecnica si Presto/PZH puede leerse nativamente o solo via exportacion.

## ADR-018: Soporte obligatorio Presto/PZH mediante ruta tecnica evidenciada

**Estado:** Aprobado (fase 8)

**Decision**

- Presto/PZH es un objetivo obligatorio del proyecto y no puede omitirse del roadmap sin permiso explicito.
- El estado tecnico actual no justifica un parser nativo improvisado.
- La via de soporte debe basarse en evidencia tecnica y puede ser una de estas rutas:
  - exportacion desde Presto a BC3;
  - exportacion desde Presto a Excel;
  - herramienta externa especializada;
  - libreria especializada si demuestra viabilidad real;
  - investigacion tecnica adicional;
  - flujo alternativo documentado.
- Mientras no exista evidencia adicional, los archivos Presto-like clasificados como `NEEDS_VENDOR_EXPORT` permanecen como referencia tecnica y no se fuerzan a lectura nativa.

**Racional**

Presto/PZH forma parte del corpus real del proyecto y no debe desaparecer del roadmap por conveniencia tecnica. A la vez, el diagnostico actual muestra ausencia de lectura nativa directa utilizable, por lo que la opcion segura es sostener el soporte por una ruta evidenciada y trazable, no inventar un parser sin base suficiente.

## ADR-019: Excel maestro vivo como salida principal del sistema

**Estado:** Aprobado (fase 9.0)

**Decision**

- La salida principal del sistema sera un Excel maestro vivo.
- El Excel maestro vivo sera un archivo iterativo y actualizable.
- El mismo archivo podra sobrescribirse de forma controlada en cada iteracion.
- El Excel maestro podra incorporar nuevas hojas internas segun evolucione el corpus procesado.
- El Excel maestro acumulera presupuestos procesados, validaciones, exclusiones, trazabilidad y ratios progresivos.
- El Excel maestro sera el producto operativo final del sistema.
- No se sustituye por una base de datos externa salvo decision humana futura documentada.
- No se sustituye por un informe estatico.
- Cualquier base de datos futura, si aparece, sera auxiliar salvo nueva ADR.
- El calculo de ratios debera estar documentado y trazado.
- El Excel maestro no debe alimentarse con datos no validados.
- El Excel maestro debe distinguir datos usados, excluidos y pendientes de revision.

**Racional**

El proyecto no necesita solo una capa de calculo o un report puntual, sino un artefacto operativo vivo que acumule conocimiento y mejore con el volumen procesado. Fijar el master como Excel vivo mantiene la trazabilidad, encaja con la realidad de trabajo del dominio y evita separar el producto final en una base de datos abstracta que no sea el objeto operativo principal de la organizacion.
