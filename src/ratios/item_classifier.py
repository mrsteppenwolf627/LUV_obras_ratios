"""Automatic item category classification using keyword + unit rules."""

from __future__ import annotations

from typing import Optional


CATEGORIZATION_RULES: dict[str, dict] = {
    "ESTRUCTURA": {
        "keywords": [
            "hormigón", "hormigon", "ha-", "hl-", "hm-", "hp-",
            "acero", "encofrado", "desencofrado", "armadura", "armado", "ferrallado",
            "cimentación", "cimentacion", "pilote", "zapata", "losa", "solera",
            "forjado", "viga", "pilar", "muro", "murete", "jácena",
        ],
        "unidades": ["m³", "m3", "kg", "t", "ton", "tn", "ml", "m"],
        "subcategorias": {
            "Hormigonado": ["hormigón", "hormigon", "ha-", "hl-", "hm-", "hp-"],
            "Acero": ["acero", "armadura", "armado", "ferrallado"],
            "Encofrado": ["encofrado", "desencofrado"],
            "Cimentación": ["cimentación", "cimentacion", "pilote", "zapata"],
        },
    },
    "INSTALACIONES": {
        "keywords": [
            "electricidad", "eléctric", "electric", "fontanería", "fontaneria",
            "climatización", "climatizacion", "gas", "calefacción", "calefaccion",
            "ventilación", "ventilacion", "saneamiento", "tubería", "tuberia",
            "cable", "cableado", "contador", "cuadro eléctrico", "cuadro electrico",
            "bomba", "radiador", "depósito", "deposito", "aire acondicionado",
        ],
        "unidades": ["kw", "kwh", "m", "ud", "u", "pa"],
        "subcategorias": {
            "Eléctrica": [
                "electricidad", "eléctric", "electric", "cable", "cableado",
                "cuadro eléctrico", "cuadro electrico",
            ],
            "Fontanería": ["fontanería", "fontaneria", "tubería", "tuberia", "bomba", "saneamiento"],
            "Clima": [
                "climatización", "climatizacion", "ventilación", "ventilacion",
                "calefacción", "calefaccion", "radiador", "aire acondicionado",
            ],
            "Gas": ["gas", "depósito", "deposito"],
        },
    },
    "ACABADOS": {
        "keywords": [
            "pintura", "barniz", "imprimación", "imprimacion",
            "suelo", "revestimiento", "alicatado", "azulejo", "baldosa",
            "parquet", "tarima", "pavimento", "gres", "porcelánico", "porcelanico",
            "terrazo", "moqueta", "papel pintado", "enlucido", "yeso", "escayola",
            "falso techo", "puerta", "ventana", "carpintería", "carpinteria",
        ],
        "unidades": ["l", "litro", "m²", "m2", "m", "ud", "u"],
        "subcategorias": {
            "Pintura": ["pintura", "barniz", "imprimación", "imprimacion"],
            "Pavimentos": [
                "suelo", "baldosa", "parquet", "tarima", "pavimento",
                "gres", "porcelánico", "porcelanico", "terrazo", "moqueta",
            ],
            "Revestimientos": [
                "revestimiento", "alicatado", "azulejo", "enlucido", "yeso", "escayola",
                "papel pintado",
            ],
            "Carpintería": ["puerta", "ventana", "carpintería", "carpinteria"],
            "Techos": ["falso techo", "escayola"],
        },
    },
    "MOBILIARIO": {
        "keywords": [
            "mueble", "armario", "mobiliario", "laminado",
            "encimera", "lavabo", "inodoro", "bañera", "plato de ducha",
            "grifo", "grifería", "griferia", "cocina amueblada",
        ],
        "unidades": ["ud", "u", "m", "m²", "m2"],
        "subcategorias": {
            "Muebles": ["mueble", "armario", "mobiliario", "laminado"],
            "Cocinas": ["cocina amueblada", "encimera"],
            "Baños": ["lavabo", "inodoro", "bañera", "plato de ducha", "grifo", "grifería", "griferia"],
        },
    },
    "DEMOLICIÓN": {
        "keywords": [
            "derribo", "demolición", "demolicion", "excavación", "excavacion",
            "movimiento de tierras", "desescombro", "retirada de escombros",
            "desmontaje", "relleno", "compactación", "compactacion",
        ],
        "unidades": ["m³", "m3", "kg", "ud", "u", "m²", "m2"],
        "subcategorias": {
            "Derribo": ["derribo", "demolición", "demolicion", "desmontaje"],
            "Excavación": ["excavación", "excavacion", "movimiento de tierras"],
            "Gestión de residuos": [
                "desescombro", "retirada de escombros", "relleno",
                "compactación", "compactacion",
            ],
        },
    },
}

# Score weights
_KW_WEIGHT = 0.7
_UNIT_WEIGHT = 0.3
_DUBIOUS_THRESHOLD = 0.6


def classify_item(item: dict) -> dict:
    """
    Classify an item into a construction category.

    Returns:
    {
        "categoria": str,
        "subcategoria": str | None,
        "keywords_detectados": list[str],
        "confianza": float,          # 0.0–1.0
        "reglas_aplicadas": list[str],
    }
    """
    desc_lower = (item.get("descripcion") or "").lower()
    unit_lower = (item.get("unidad") or "").lower().strip()

    scores: dict[str, float] = {}
    kw_hits: dict[str, list[str]] = {}

    for cat, rules in CATEGORIZATION_RULES.items():
        score = 0.0
        hits: list[str] = []

        for kw in rules["keywords"]:
            if kw.lower() in desc_lower:
                score += _KW_WEIGHT
                hits.append(kw)

        for unit in rules["unidades"]:
            if unit.lower() == unit_lower or (unit_lower and unit.lower() in unit_lower):
                score += _UNIT_WEIGHT
                break

        if score > 0:
            scores[cat] = score
            kw_hits[cat] = hits

    if not scores:
        return {
            "categoria": "OTROS",
            "subcategoria": None,
            "keywords_detectados": [],
            "confianza": 0.0,
            "reglas_aplicadas": ["sin_coincidencia"],
        }

    best_cat = max(scores, key=lambda c: scores[c])
    best_score = scores[best_cat]

    # Normalize: max possible score per keyword hit is _KW_WEIGHT + _UNIT_WEIGHT = 1.0
    # Cap at 1.0
    confianza = min(best_score, 1.0)

    subcategoria = _find_subcategory(best_cat, desc_lower)

    reglas = [f"descripción contiene '{kw}'" for kw in kw_hits[best_cat]]

    return {
        "categoria": best_cat,
        "subcategoria": subcategoria,
        "keywords_detectados": kw_hits[best_cat],
        "confianza": round(confianza, 4),
        "reglas_aplicadas": reglas,
    }


def _find_subcategory(categoria: str, desc_lower: str) -> Optional[str]:
    rules = CATEGORIZATION_RULES.get(categoria, {})
    for subcat, keywords in rules.get("subcategorias", {}).items():
        for kw in keywords:
            if kw.lower() in desc_lower:
                return subcat
    return None
