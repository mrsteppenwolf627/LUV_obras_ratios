# Fase 8: estrategia tecnica obligatoria para soporte Presto/PZH

## 1. Objetivo

Definir una estrategia tecnica fiable para incorporar Presto/PZH al sistema sin improvisar un parser nativo si no hay evidencia suficiente, pero sin omitir Presto del roadmap.

## 2. Decision humana obligatoria

Presto/PZH es necesario para el proyecto y no debe omitirse ni dejarse fuera del roadmap sin permiso explicito.

## 3. Estado actual de Presto/PZH

- El corpus local contiene 10 archivos Presto-like.
- El diagnostico tecnico actual los clasifica todos como `NEEDS_VENDOR_EXPORT`.
- No existe evidencia local de lectura nativa directa utilizable.
- La decision tecnica segura es mantener Presto/PZH como objetivo obligatorio, pero soportarlo por una via tecnica evidenciada.

## 4. Numero de archivos Presto-like detectados

- Total detectado: 10.

## 5. Clasificacion actual de esos archivos

- `NEEDS_VENDOR_EXPORT`: 10.
- `DIRECTLY_READABLE`: 0.
- `READABLE_WITH_STANDARD_LIBRARY`: 0.
- `NEEDS_EXTERNAL_TOOL`: 0.
- `UNSUPPORTED_OR_UNKNOWN`: 0.

## 6. Limitaciones detectadas por el diagnostico actual

- Los archivos muestran firma fisica binaria/proprietaria.
- No se ha detectado lectura nativa directa utilizable con la libreria estandar.
- No se ha confirmado una estructura comun suficientemente estable para asumir parser propio.
- La extension por si sola no permite asumir formato real ni semantica interna.

## 7. Por que no se debe improvisar un parser nativo sin evidencia

- Un parser nativo sin evidencia puede perder datos o interpretar mal el contenido.
- Un error de interpretacion en Presto/PZH puede ser mas costoso que en Excel o BC3 porque el formato real puede ser propietario o exportado parcialmente.
- La presencia de archivos `Presto`, `PrestoBackup` y `PrestoRecord` no garantiza que el contenido sea homogeno ni apto para parseo directo.
- La trazabilidad del proyecto exige que la decision tecnica se base en evidencia reproducible, no en suposiciones.

## 8. Opciones tecnicas evaluadas

### 8.1 Exportacion desde Presto a BC3

- Viabilidad: alta si Presto permite exportacion estable.
- Riesgo: depende de que la exportacion preserve suficiente semantica.
- Dependencia externa: alta.
- Trazabilidad: buena si se conserva el archivo exportado y el origen.
- Automatizacion posible: media-alta.
- Compatibilidad futura con master: alta.
- Coste operativo: medio.
- Riesgo de perdida de datos: medio.

### 8.2 Exportacion desde Presto a Excel

- Viabilidad: alta si la exportacion es consistente.
- Riesgo: puede introducir variacion de formato y semantica tabular.
- Dependencia externa: alta.
- Trazabilidad: buena si se conserva la exportacion y el origen.
- Automatizacion posible: alta una vez estandarizado.
- Compatibilidad futura con master: alta.
- Coste operativo: medio.
- Riesgo de perdida de datos: medio.

### 8.3 Herramienta externa especializada

- Viabilidad: media.
- Riesgo: disponibilidad, licencias y mantenimiento.
- Dependencia externa: media-alta.
- Trazabilidad: variable segun herramienta.
- Automatizacion posible: media.
- Compatibilidad futura con master: alta si la salida es BC3 o Excel.
- Coste operativo: medio-alto.
- Riesgo de perdida de datos: medio.

### 8.4 Libreria especializada

- Viabilidad: desconocida hasta verificar soporte real.
- Riesgo: alto si la libreria no cubre variantes reales.
- Dependencia externa: media.
- Trazabilidad: buena si expone metadatos y origen.
- Automatizacion posible: alta si existe soporte real.
- Compatibilidad futura con master: media-alta.
- Coste operativo: medio.
- Riesgo de perdida de datos: medio-alto.

### 8.5 Investigacion tecnica adicional

- Viabilidad: alta.
- Riesgo: bajo.
- Dependencia externa: baja.
- Trazabilidad: alta.
- Automatizacion posible: no aplica de forma inmediata.
- Compatibilidad futura con master: alta porque evita decisiones prematuras.
- Coste operativo: bajo-medio.
- Riesgo de perdida de datos: bajo.

### 8.6 Flujo manual controlado temporal

- Viabilidad: alta como medida transitoria.
- Riesgo: error humano y coste operativo.
- Dependencia externa: alta.
- Trazabilidad: media-alta si el proceso esta documentado.
- Automatizacion posible: baja.
- Compatibilidad futura con master: media.
- Coste operativo: alto.
- Riesgo de perdida de datos: bajo-medio.

### 8.7 Flujo vendor/export

- Viabilidad: alta si el proveedor soporta exportaciones estables.
- Riesgo: dependencia de la herramienta original.
- Dependencia externa: alta.
- Trazabilidad: buena si se conserva el export y el origen.
- Automatizacion posible: alta.
- Compatibilidad futura con master: alta.
- Coste operativo: medio.
- Riesgo de perdida de datos: medio.

## 9. Estrategia recomendada

La via recomendada es una estrategia de soporte Presto/PZH basada en exportacion o herramienta externa:

1. Prioridad 1: exportacion desde Presto a BC3.
2. Prioridad 2: exportacion desde Presto a Excel.
3. Prioridad 3: herramienta externa o libreria especializada si demuestra viabilidad real.
4. Medida transitoria: flujo manual controlado y documentado.

El parser nativo Presto no debe considerarse opcion base hasta que haya evidencia tecnica suficiente.

## 10. Plan de pruebas para la estrategia recomendada

- Conseguir uno o varios ejemplos exportados desde Presto a BC3.
- Conseguir uno o varios ejemplos exportados desde Presto a Excel.
- Ejecutar el contrato multi-formato existente sobre esos exports.
- Verificar trazabilidad de origen entre archivo Presto y exportacion.
- Comparar estabilidad entre exportaciones del mismo origen.
- Validar que la salida exportada entra en el flujo comun sin ratios, sin master y sin normalizacion final.

## 11. Que se necesita del usuario o equipo

- Acceso a Presto o a un entorno donde se puedan generar exports.
- Exportacion de prueba a BC3.
- Exportacion de prueba a Excel.
- Documentacion tecnica del proveedor si existe.
- Herramienta instalada o disponible para el flujo elegido.
- Ejemplos exportados no sensibles para prueba local.

## 12. Decisiones pendientes

- Si existe exportacion estable a BC3.
- Si existe exportacion estable a Excel.
- Si hace falta herramienta externa especializada.
- Si una libreria especializada puede cubrir el caso real.
- Si debe mantenerse un flujo manual transitorio.

## 13. Criterios para pasar a Fase 8.1

- Evidencia concreta de una via de soporte Presto/PZH.
- Al menos una ruta valida de exportacion o lectura reproducible.
- Criterios de trazabilidad definidos para la ruta elegida.
- Evidencia de que la salida puede integrarse en el contrato comun multi-formato.

## 14. Riesgos si se intenta parser nativo

- Interpretacion incorrecta de datos.
- Perdida de semantica.
- Bloqueo tecnico por formato propietario o parcialmente documentado.
- Inversion de esfuerzo en una ruta no sostenible.

## 15. Riesgos si se depende de exportacion externa

- Dependencia de la herramienta original o del proveedor.
- Variabilidad de exportacion entre versiones.
- Posible perdida de semantica en la conversion.
- Coste operativo adicional.

## 16. Integracion con el modelo comun multi-formato

Presto/PZH debe integrarse al modelo comun por medio de su salida exportada o de una capa tecnicamente valida que preserve:

- archivo origen;
- tipo de exportacion;
- trazabilidad de conversion;
- estado de elegibilidad;
- advertencias;
- manual review;
- exclusiones controladas.

Mientras no exista una via confirmada, los archivos Presto-like quedan como `NEEDS_VENDOR_EXPORT` y se mantienen como referencia tecnica, no como lectura nativa.

