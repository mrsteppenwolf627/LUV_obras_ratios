# Fase 5.3: estrategia multi-formato con prioridad Excel y Presto/PZH

## 1. Motivo del cambio

Se formaliza la decision humana de no profundizar temporalmente en endurecimiento adicional BC3 y reorientar el roadmap hacia los formatos mas habituales del negocio: Excel y Presto/PZH.

## 2. Estado actual de BC3

- Parser BC3 estricto implementado.
- Validador BC3 estricto implementado.
- Normalizador intermedio BC3 implementado.
- Validador de contrato de normalizacion BC3 implementado.
- Estado consolidado: avance permitido con exclusiones controladas.

## 3. Por que no seguir profundizando BC3 ahora

- El retorno marginal de otro endurecimiento BC3 inmediato es menor frente a la brecha de cobertura en Excel/Presto.
- BC3 ya dispone de una base tecnica suficiente para operar como modulo avanzado.
- La prioridad de negocio exige cubrir primero las fuentes mas frecuentes.

## 4. Formatos prioritarios reales

Prioridad operativa inmediata:

1. Excel.
2. Presto/PZH y relacionados.
3. BC3 como modulo ya disponible para casos compatibles.

## 5. Estado actual de Excel

- Existe diagnostico inicial de muestras reales (Fase 2.x).
- Se observo variabilidad de hojas y presencia de chartsheets.
- No existe aun extractor/normalizador Excel robusto para flujo intermedio comparable al de BC3.

## 6. Estado actual de Presto/PZH

- Existe evidencia de presencia real en muestras.
- Estado tecnico: requiere investigacion de formato y viabilidad de lectura estructurada.
- No existe aun contrato de parseo/normalizacion para Presto/PZH.

## 7. Roadmap revisado

- Fase 6: Diagnostico Excel real.
- Fase 7: Extractor/normalizador Excel.
- Fase 8: Investigacion tecnica Presto/PZH.
- Fase 9: Decision de soporte Presto.
- Fase 10: Modelo comun multi-formato.
- Fase 11: Master / ratios / UX.

## 8. Riesgos de Excel

- Alta heterogeneidad estructural (hojas, encabezados, celdas combinadas, chartsheets).
- Ambiguedad semantica de columnas segun proveedor/proyecto.
- Riesgo de inferencias incorrectas si se fuerza normalizacion temprana.

## 9. Riesgos de Presto/PZH

- Incertidumbre de compatibilidad tecnica directa.
- Posible necesidad de conversion previa o pipeline especializado.
- Riesgo de invertir en soporte profundo sin garantia de cobertura suficiente.

## 10. Estrategia de diagnostico por formato

- Mantener fase diagnostica acotada antes de implementar parser definitivo por formato.
- Definir contrato minimo por formato (estructura, trazabilidad, errores, exclusiones, manual review).
- Reutilizar patrones de gobernanza ya probados en BC3: separacion de capas, exclusiones controladas y validacion contractual.

## 11. Modelo comun futuro multi-formato

Objetivo: converger salidas de BC3, Excel y potencial Presto/PZH a un modelo intermedio comun con:

- trazabilidad de origen por archivo/hoja/registro;
- entidades compartidas (chapters, cost_items, relations, units, descriptions, signals);
- banderas de calidad y manual_review por formato;
- exclusiones controladas sin borrado.

## 12. Decisiones pendientes

- Contrato tecnico de diagnostico Excel (alcance minimo y severidades).
- Viabilidad de soporte directo Presto/PZH frente a conversion o referencia.
- Criterios de entrada para convergencia multi-formato en fase 10.
- Umbrales de calidad para habilitar futura integracion al master.

## 13. Siguiente fase recomendada

Fase 6: diagnostico Excel real con corpus ampliado, reglas de trazabilidad y criterios de aptitud de archivo, manteniendo restricciones activas:

- no master;
- no ratios;
- no consolidacion final;
- no normalizacion final;
- no UX;
- no subida de muestras reales ni reports sensibles.
