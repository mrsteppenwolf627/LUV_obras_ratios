# PROMPT: Claude Code — Arquitectura Backend para Visuales Gestor Obra

## CONTEXTO

Lee el documento: DESIGN_VISUALES_GESTOR_OBRA.md (arriba en esta conversación)

Proyecto: LUV Ratios  
Stack: FastAPI + SQLAlchemy + Pydantic v2  
Objetivo: Agregar endpoints y lógica para soportar 3 nuevas visuales (Rango, Confiabilidad, Comparativa)

---

## TAREA ESPECÍFICA

Diseña la **arquitectura backend** necesaria para soportar las visuales. No implementes aún, **diseña**.

### Punto 1: Validar Endpoints Necesarios

**Pregunta:** ¿Qué endpoints faltan o qué endpoints existentes necesitan refactor?

Revisa:
- GET /api/ratios/chapters — ¿Existe? ¿Qué devuelve ahora? ¿Qué debería devolver?
- GET /api/ratios/statistics — ¿Existe? ¿Incluye min/max/mediana/desviación?

Responde con:
```
Endpoint | Existe | Cambio Necesario | Salida Esperada
---------|--------|------------------|------------------
GET /api/ratios/chapters | SÍ/NO | [cambio] | [JSON spec]
```

---

### Punto 2: Modelos Pydantic

**Pregunta:** ¿Qué esquemas nuevos necesitamos?

Propone:

```python
# Esquema para respuesta de /api/ratios/chapters
class CapituloRatioResponse(BaseModel):
    capitulo: str
    descripcion: str
    minimo: float
    mediana: float
    maximo: float
    cantidad_datos: int
    estado_confiabilidad: Literal['muy_solido', 'solido', 'debil', 'muy_debil']
    percentil_25: Optional[float] = None
    percentil_75: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "capitulo": "ESTRUCTURA",
                "descripcion": "Estructura",
                "minimo": 280.0,
                "mediana": 334.67,
                "maximo": 450.0,
                "cantidad_datos": 8,
                "estado_confiabilidad": "solido",
                "percentil_25": 310.0,
                "percentil_75": 350.0
            }
        }

# Esquema para presupuesto del usuario (input)
class ItemPresupuesto(BaseModel):
    capitulo: str
    valor_unitario: float
    cantidad: int
    unidad: str

class PresupuestoAnalisis(BaseModel):
    items: List[ItemPresupuesto]
    area_total: float

# Esquema para salida de comparativa
class ComparativaCapitulo(BaseModel):
    capitulo: str
    valor_mio: float
    valor_ratio: float
    desviacion_pct: float
    impacto_monetario: float
```

¿Esto es correcto o necesita ajustes?

---

### Punto 3: Lógica de Cálculo

**Pregunta:** ¿Dónde va la lógica? ¿Backend o Frontend?

Opciones:
1. **Backend calcula TODO** (desviaciones, impactos) → Frontend solo renderiza
2. **Backend proporciona ratios** → Frontend calcula desviaciones
3. **Híbrido**: Backend calcula agregados, Frontend cálculos rápidos

Propuesta: **Opción 1 (Backend calcula todo)**
- Ventaja: Frontend limpio, auditable, single source of truth
- Desventaja: Más requests si cambia presupuesto frecuentemente

¿Acuerdo?

---

### Punto 4: Endpoint para Comparativa

Propone un endpoint tipo:

```
POST /api/analyze/comparativa
Body: PresupuestoAnalisis
Response: {
  "capitulos": [ComparativaCapitulo],
  "resumen": {
    "total_presupuesto": float,
    "total_ratio": float,
    "diferencia_pct": float,
    "diferencia_monetaria": float
  }
}
```

¿Falta algo en respuesta?

---

### Punto 5: Queries de BD

**Pregunta:** ¿Las queries para calcular ratios por capítulo están optimizadas?

Necesitamos:
```sql
-- Para cada capítulo:
SELECT 
  capitulo,
  MIN(precio_unitario) as minimo,
  PERCENTILE_CONT(0.25) as p25,
  PERCENTILE_CONT(0.50) as mediana,
  PERCENTILE_CONT(0.75) as p75,
  MAX(precio_unitario) as maximo,
  COUNT(DISTINCT presupuesto_id) as cantidad_datos,
  STDDEV_POP(precio_unitario) as desviacion
FROM ratios_historicos
GROUP BY capitulo
```

¿Esto es lo que hace ahora? ¿Hay índices para optimizar?

---

### Punto 6: Confiabilidad (Lógica)

Propone función:

```python
def calcular_estado_confiabilidad(cantidad_datos: int) -> str:
    if cantidad_datos >= 10:
        return 'muy_solido'
    elif cantidad_datos >= 5:
        return 'solido'
    elif cantidad_datos >= 2:
        return 'debil'
    else:
        return 'muy_debil'
```

¿Estos umbrales (10/5/2) son correctos? ¿O debería ser otro?

---

## ENTREGA ESPERADA

No código, solo **documento de arquitectura** con:

1. ✅ Tabla de endpoints (existe/cambio/salida)
2. ✅ Esquemas Pydantic propuestos
3. ✅ Decisión: ¿Backend o Frontend calcula?
4. ✅ Spec del endpoint POST /analyze/comparativa
5. ✅ Review de queries SQL
6. ✅ Función de confiabilidad validada
7. ✅ Notas de optimización (índices, caching)

---

## RESTRICCIONES

- No ejecutes queries contra BD aún
- No modifiques código aún
- Solo diseño + validación
- Propón mejoras si ves bottlenecks

---

## NOTAS OPERATIVAS

- El proyecto usa Transaction Pooler de Supabase (puerto 6543)
- SQLAlchemy 2.0 con ORM
- Tests con pytest (487 tests verdes actualmente)
- Si necesitas ver estructura de tablas, pide en próxima iteración

**Siguiente:** Este documento lo revisaré, confirmaré cambios, y entonces Gemini implementa frontend.
