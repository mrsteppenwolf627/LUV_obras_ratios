# Fase 7.2: contrato comun multi-formato Excel/Presto

## 1. Objetivo

Consolidar una base comun de lectura y diagnostico para los formatos principales del proyecto: Excel, Presto/PZH y BC3, sin importar aun al master, sin calcular ratios y sin normalizar categorias finales.

## 2. Motivo del cambio de ritmo

La base BC3 ya existe y es operativa. Excel ya dispone de lector integral. La brecha real ahora esta en un contrato comun que permita avanzar sobre formatos frecuentes sin seguir sobreinvirtiendo en endurecimientos aislados.

## 3. Estado BC3

- Parser estricto implementado.
- Validador estricto implementado.
- Normalizacion intermedia implementada.
- Validacion de contrato de normalizacion intermedia implementada.
- BC3 queda como modulo avanzado disponible.

## 4. Estado Excel

- Lector integral Excel implementado.
- Perfilado real de workbook, hoja y celda disponible.
- Existen reportes sanitizados locales y un inventario reproducible.

## 5. Estado Presto/PZH

- Hay evidencia real de archivos `Presto`, `PrestoBackup` y `PrestoRecord` en el corpus local.
- El formato nativo no esta aun validado como legible de forma directa.
- Se necesita investigacion tecnica antes de prometer un lector nativo.

## 6. Alcance

- Definir contrato comun de lectura/diagnostico.
- Completar validacion y normalizacion intermedia inicial de Excel.
- Investigar Presto/PZH de forma tecnica y no destructiva.
- Generar un inventario multi-formato comun.

## 7. Fuera de alcance

- Importacion al master.
- Calculo de ratios.
- Consolidacion final de importes.
- Normalizacion final de categorias.
- `CATEGORY_MAPPING`.
- UX.
- Modificacion de RAW.

## 8. Contrato comun de lectura

El contrato comun debe permitir representar, por archivo:

- formato detectado;
- estado de lectura;
- lector/parser usado;
- elegibilidad;
- exclusiones controladas;
- advertencias;
- manual review;
- siguiente accion.

## 9. Riesgos por formato

- Excel: alta heterogeneidad estructural y presencia de hojas no tabulares.
- Presto/PZH: posible formato propietario, binario o dependiente de exportacion externa.
- BC3: modulo ya operativo, pero no debe volver a absorber la prioridad del roadmap.

## 10. Estrategia de outputs

- Mantener reportes locales por formato.
- Mantener JSON y Markdown sanitizados.
- No subir muestras reales ni reportes reales al repositorio.
- Conservar trazabilidad por archivo y, cuando proceda, por hoja o registro.

## 11. Reglas de trazabilidad

- Cada salida debe conservar referencia al archivo origen.
- Excel debe conservar archivo, hoja y celda cuando aplique.
- Presto/PZH debe conservar al menos archivo, tipo detectado y razon de soporte.
- BC3 debe conservar archivo, registro y linea cuando aplique.

## 12. Reglas de exclusion controlada

- Archivos no soportados quedan clasificados, no borrados.
- Archivos no legibles quedan como referencia tecnica.
- La exclusion no debe ocultar el estado del corpus completo.

## 13. Severidades

- INFO.
- WARNING.
- MANUAL_REVIEW_REQUIRED.
- ERROR.
- BLOCKED.

## 14. Criterios de aceptacion

- Excel validado y normalizado intermediaramente.
- Presto/PZH investigado con evidencia tecnica reproducible.
- Inventario multi-formato comun generado.
- Ningun formato rompe el flujo por no ser el prioritario.
- El corpus real se puede resumir sin subir artefactos sensibles.

## 15. Decisiones pendientes

- Si Presto/PZH admite lectura nativa o requiere exportacion externa.
- Profundidad exacta de la normalizacion intermedia Excel.
- Contrato comun final de inventario multi-formato.
- Umbrales de calidad para entrada futura al modelo comun.

## 16. Recomendacion posterior

Avanzar con validacion de Excel, investigacion tecnica Presto/PZH y un inventario multi-formato que sirva de base para el modelo comun posterior.

