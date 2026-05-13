# LUV Obras Ratios

Sistema interno para importaci?n, validaci?n y c?lculo progresivo de ratios econ?micos de obra a partir de presupuestos hist?ricos.

## Objetivo

Construir una base trazable y auditable para alimentar un master de ratios sin invenci?n de datos, preservando el origen de cada valor (archivo, hash y referencia de origen).

## Estado actual

Fase de inicializaci?n metodol?gica y t?cnica.

- Estructura base creada.
- Gobernanza documental inicial creada (`CONTEXT.md`, `ADRs.md`).
- Scripts iniciales de verificaci?n creados.
- Sin parsers definitivos.
- Sin c?lculo consolidado de ratios.

**Advertencia:** este repositorio todav?a no produce ratios definitivos y no debe usarse para decisiones econ?micas finales.

## Estructura

```text
/docs
  /adr
  /decisions
/data
  /raw
  /processed
  /master
  /samples
  /exports
/logs
  /imports
  /validation
/reports
/src
  /parsers
  /validators
  /mappers
  /exporters
  /models
  /utils
/scripts
/tests
  /parsers
  /validators
  /mappers
  /exporters
  /scripts
.context-backups
CONTEXT.md
ADRs.md
README.md
.gitignore
```

## Principios de datos

- No inventar datos.
- No estimar datos ausentes.
- No sobrescribir datos brutos.
- No borrar hist?rico de importaciones.
- No actualizar ratios con datos no validados.
- Priorizar Excel y BC3/Presto sobre PDF.
- Conservar fuente original y hash de archivo.
- Separar RAW, normalizaci?n, validaci?n, c?lculo y exportaci?n.
- Mantener trazabilidad extremo a extremo.

## Flujo previsto (alto nivel)

1. Ingesta de archivo de origen (Excel, BC3/Presto, otros compatibles).
2. Registro de metadatos e identidad del archivo (incluyendo hash).
3. Persistencia de dato bruto sin modificaci?n.
4. Normalizaci?n y mapeo a esquema interno.
5. Validaciones matem?ticas y de consistencia.
6. Aprobaci?n/manual review si procede.
7. Actualizaci?n controlada del master de ratios.
8. Exportes y reportes auditables.

## Herramientas usadas

- ChatGPT: coordinaci?n metodol?gica, arquitectura y documentaci?n.
- Codex / Antigravity: backend, parsers, validaciones, tests y auditor?a t?cnica.
- Gemini CLI: frontend, UX y prototipado visual.

## Scripts iniciales

Ejecutar desde la ra?z del repositorio:

```bash
python scripts/validate_context.py
python scripts/inspect_repo.py
```

## Qu? no hace todav?a el proyecto

- No parsea Excel de forma definitiva.
- No parsea BC3/Presto de forma definitiva.
- No calcula ratios consolidados.
- No actualiza autom?ticamente el master.
- No incluye interfaz web.
- No incluye base de datos.
