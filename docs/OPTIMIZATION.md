# Optimización de BD — LUV Ratios

## Índices (Migración `a1b2c3d4e5f6`)

| Índice | Tabla | Columna | Razón |
|---|---|---|---|
| `ix_line_items_chapter_code` | line_items | chapter_code | GROUP BY en `recalculate_all_ratios` |
| `ix_ratios_chapter_code` | ratios | chapter_code | Lookups en `/api/analyze/comparativa` y `/api/ratios/chapters` |
| `ix_line_items_validation_status` | line_items | validation_status | Filtro `VALID` en todas las queries de cálculo |
| `ix_line_items_budget_id` | line_items | budget_id | JOINs contra `budgets` en `_collect_cost_per_m2_values` |

Para verificar en producción:

```python
from sqlalchemy import create_engine, text
engine = create_engine("sqlite:///data/master/ratios.db")
with engine.connect() as conn:
    rows = conn.execute(text("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'ix_%'")).fetchall()
    print([r[0] for r in rows])
```

## Cache In-Memory

- **`GET /api/ratios/chapters`:** TTL 3600s (1 hora), clave por `building_type`
- **Invalidación:** Automática al finalizar `POST /api/import` exitoso (`invalidar_cache_chapters()`)
- **Implementación:** Dict global + timestamp — sin dependencias externas

## Normalización de Capítulos

Toda búsqueda de capítulo en `analizar_comparativa` normaliza el input:

- `.upper().strip()` sobre el código recibido del usuario
- `func.upper(Ratio.chapter_code)` en la query SQL
- Resultado: `"  estructura  "` → encuentra `"ESTRUCTURA"` en BD

## Performance Esperada

| Endpoint | Sin caché | Con caché |
|---|---|---|
| `GET /api/ratios/chapters` | < 50ms | < 5ms |
| `POST /api/analyze/comparativa` | < 100ms | — |
| `recalculate_all_ratios()` | < 500ms | — |

```bash
pytest tests/test_optimization.py -v
```
