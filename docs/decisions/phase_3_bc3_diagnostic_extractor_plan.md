# Fase 3: plan del extractor diagnostico BC3

## 1. Objetivo

Implementar un extractor diagnostico BC3, no destructivo, para entender estructura real de archivos BC3 antes de disenar un parser definitivo.

## 2. Alcance

- Lectura local de archivos `.bc3` en `data/samples`.
- Deteccion de encoding probable (`utf-8`, `cp1252` y fallback seguro).
- Deteccion de cabecera y version FIEBDC cuando sea visible.
- Conteo de registros por tipo (`~V`, `~K`, `~C`, `~D`, etc.).
- Inventario de tipos de registro presentes.
- Listado diagnostico de codigos candidatos de capitulos.
- Deteccion basica de relaciones jerarquicas candidatas.
- Deteccion diagnostica de unidades e importes aparentes sin consolidar.
- Generacion de reportes JSON y Markdown en `reports/bc3_diagnostics/`.

## 3. Fuera de alcance

- Parser BC3 definitivo.
- Importacion al master.
- Calculo de ratios.
- Normalizacion de categorias finales.
- Consolidacion de importes.
- Modificacion de archivos RAW.
- OCR o extraccion automatica de PDF.
- Tratamiento de Presto/PZH en esta fase.

## 4. Entradas esperadas

- Archivos locales con extension `.bc3` dentro de `data/samples/`.
- Contexto diagnostico previo de Fase 2 (`reports/sample_inspections/`), si existe.

## 5. Salidas esperadas

- `reports/bc3_diagnostics/bc3_diagnostic_inventory.json`
- `reports/bc3_diagnostics/bc3_diagnostic_inventory_report.md`

Los reportes sobre muestras reales pueden contener metadatos sensibles y deben mantenerse fuera de Git.

## 6. Reglas de seguridad

- Lectura no destructiva de entradas.
- Sin escritura en `data/raw`, `data/master` ni archivos de muestra.
- Sin transformaciones irreversibles.
- Sin consolidacion economica.
- Sin decisiones automaticas de version valida o categoria final.
- Reportes completos con datos reales fuera de Git.

## 7. Estructura prevista del reporte JSON

- Metadatos globales: fecha de generacion, ruta de muestras, conteos.
- Estado de ejecucion por archivo BC3.
- Para cada BC3:
  - ruta relativa, tamano, hash opcional de referencia;
  - encoding detectado y confianza;
  - cabecera/linea `~V` y version FIEBDC candidata;
  - tipos de registro presentes;
  - conteo por tipo de registro;
  - codigos de capitulo candidatos;
  - relaciones jerarquicas basicas candidatas;
  - unidades detectadas;
  - indicadores de importes aparentes (sin totalizar);
  - advertencias/errores diagnosticos.

## 8. Estructura prevista del reporte Markdown

- Resumen global de ejecucion.
- Conteo de archivos BC3 inspeccionados.
- Tabla/lista por archivo:
  - estado;
  - encoding;
  - version FIEBDC candidata;
  - tipos de registro detectados;
  - incidencias.
- Riesgos y notas tecnicas.
- Recordatorio de limites (sin parser definitivo, sin master, sin ratios).

## 9. Limites conocidos

- Deteccion de encoding es heuristica.
- Variantes FIEBDC pueden requerir parseo mas profundo.
- Relaciones jerarquicas seran aproximadas en fase diagnostica.
- Deteccion de importes y unidades sera indicativa, no normativa.
- La validez final por version/proyecto requiere revision humana.

## 10. Criterios de aceptacion

- Script ejecutable: `python scripts/inspect_bc3.py`.
- Genera JSON y Markdown de diagnostico en la ruta prevista.
- Soporta `cp1252` y maneja bytes no decodificables sin romper el flujo.
- Detecta y cuenta registros por tipo.
- Detecta `~V` y posibles senales de version FIEBDC.
- Incluye pruebas automaticas en `tests/scripts/test_inspect_bc3.py`.
- No modifica archivos de entrada.

## 11. Proximos pasos posteriores

1. Revisar resultados diagnosticos BC3 con revision humana.
2. Ajustar cobertura de variantes FIEBDC en modo diagnostico.
3. Diseñar extractor diagnostico Excel como segunda linea.
4. Mantener Presto/PZH como investigacion separada.
5. Preparar diseno de parser normalizador definitivo en fase posterior.
