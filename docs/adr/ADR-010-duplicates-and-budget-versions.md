# ADR-010: Política preliminar de duplicados y versionado de presupuestos

**Estado:** PROPUESTA

## Contexto

Los presupuestos históricos pueden llegar en múltiples archivos, formatos, versiones y copias. Sin política explícita, el sistema podría duplicar importes, elegir una versión incorrecta o alimentar ratios con presupuestos no comparables.

## Decisión

Adoptar una política preliminar para detectar duplicados exactos, duplicados lógicos, versiones, backups, fuentes principales, fuentes secundarias y fuentes de referencia antes de importar datos al master.

## Motivos

- Evitar doble conteo.
- Evitar pérdida de histórico.
- Evitar selección automática incorrecta.
- Separar versión contractual, versión actualizada, versión parcial y backup.
- Mantener trazabilidad.
- Requerir revisión humana ante conflictos.

## Consecuencias

- Mayor carga de metadatos.
- Más estados intermedios antes de validar ratios.
- Menor riesgo de contaminación del master.
- Los parsers futuros deberán respetar esta política.

## Documento relacionado

- `docs/decisions/duplicates_and_budget_versions_policy.md`

## Estado de cambio

No congelar todavía hasta revisión humana.
