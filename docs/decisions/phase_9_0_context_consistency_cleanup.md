# Fase 9.0: limpieza de consistencia documental previa a Fase 9.1

## 1. Motivo de la limpieza

Se detectaron discrepancias entre secciones de `CONTEXT.md` y el estado operativo real del repositorio, lo que podia inducir a interpretar como vigentes fases antiguas ya cerradas.

## 2. Discrepancia detectada

- Existian bloques historicos extensos mezclados con bloques de estado actual sin jerarquia explicita.
- Varias secciones reflejaban "Fase 8 iniciada" mientras otros documentos ya indicaban Fase 8 cerrada tecnicamente y Fase 9.0 iniciada.
- El estado canonico no estaba priorizado de forma inequivoca al inicio del contexto.

## 3. Estado actual confirmado

- Fase 8 cerrada tecnicamente.
- Fase 9.0 iniciada y vigente.
- Decision vigente: salida principal como Excel maestro vivo (ADR-019).
- Presto/PZH obligatorio mediante ruta tecnica evidenciada, sin lectura nativa directa confirmada.

## 4. Fuentes usadas

- `CONTEXT.md`
- `ADRs.md`
- `README.md`
- `docs/decisions/phase_8_presto_pzh_support_strategy.md`
- `docs/decisions/phase_9_0_live_excel_master_output_definition.md`

## 5. Decision de consistencia documental

Se adopta explicitamente Fase 9.0 como punto vigente del estado operativo y se reorganiza `CONTEXT.md` para separar:

- estado canonico actual;
- fase vigente;
- proxima fase recomendada;
- historico referencial.

## 6. Recomendacion de siguiente apertura

Abrir Fase 9.1 como diseno tecnico del generador del Excel maestro vivo, sin iniciar implementacion de codigo en esta limpieza documental.

## 7. Restricciones vigentes

- No crear todavia el Excel maestro real con datos.
- No importar datos reales al master.
- No calcular ratios finales.
- No consolidar importes finales.
- No normalizar categorias finales.
- No modificar RAW.
- No subir muestras reales ni reports/outputs sensibles.
