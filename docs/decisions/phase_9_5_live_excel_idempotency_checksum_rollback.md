# Fase 9.5: idempotencia, checksum fuerte y rollback negativo

## 1. Objetivo de la fase

Endurecer el generador del Excel maestro vivo en tres ejes: idempotencia explicita por `run_id` en cargas sinteticas multi-lote, checksum fuerte SHA-256 para snapshots y control de rollback negativo ante snapshots no confiables.

## 2. Contexto desde Fase 9.4

- Fase 9.4 separo la integridad en `scripts/live_excel_integrity.py`.
- Persistian riesgos en idempotencia operacional, checksum debil (`size:<bytes>`) y rollback negativo parcial.

## 3. Alcance

- Añadir control de idempotencia por `run_id` en `load_synthetic_incremental`.
- Introducir SHA-256 para checksums de snapshots en hoja `SNAPSHOTS`.
- Endurecer rollback para:
  - snapshot inexistente;
  - snapshot fuera de ruta permitida;
  - snapshot corrupto;
  - snapshot con esquema invalido.
- Mantener `scripts/generate_live_excel_master.py` como CLI principal.

## 4. Fuera de alcance

- Datos reales.
- Importacion real de presupuestos al master.
- Calculo de ratios finales.
- Normalizacion final de categorias.
- Interfaz, dashboard o flujo UX.

## 5. Implementacion aplicada

- `scripts/generate_live_excel_master.py`:
  - nuevo `--run-id` opcional para cargas sinteticas;
  - idempotencia explicita: si `IMPORT_LOG.run_id` ya existe, se bloquea duplicacion y se devuelve `idempotent_skip=true`;
  - checksum SHA-256 en eventos de snapshot;
  - rollback con restauracion segura del pre-snapshot si falla validacion del snapshot destino;
  - error controlado para snapshot invalido durante rollback.

## 6. Compatibilidad contractual

- Se mantiene contrato de hojas/columnas de Fase 9.1.
- Se mantiene flujo principal de Fase 9.2.
- Se mantiene hardening y retencion de Fase 9.3.
- Se mantiene modulo de integridad extraido en Fase 9.4.

## 7. Tests añadidos

- `tests/scripts/test_live_excel_master_idempotency_and_rollback.py`:
  - idempotencia con mismo `run_id` sin duplicar `IMPORT_LOG`;
  - checksum SHA-256 valido en `SNAPSHOTS`;
  - rollback negativo por snapshot inexistente;
  - rollback negativo por snapshot corrupto con restauracion segura;
  - rollback negativo por snapshot con esquema roto con restauracion segura.

## 8. Riesgos y limitaciones

- SHA-256 cubre integridad de archivo, no autenticidad del origen.
- La recuperacion de rollback depende de disponibilidad del pre-snapshot local.
- No se incorpora aun politica avanzada de firma/verificacion externa de snapshots.

## 9. Recomendacion para Fase 9.6

- Definir contrato pre-real de entrada (todavia sintetico) con pruebas de frontera mas amplias.
- Consolidar telemetria de ejecucion (eventos de idempotencia, rollback bloqueado y recuperaciones).
- Evaluar estrategia de verificacion adicional de snapshots (firma o catalogo de confianza) sin abrir datos reales.
