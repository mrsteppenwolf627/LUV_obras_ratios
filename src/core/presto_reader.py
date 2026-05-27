"""Parser for Presto binary budget files (.Presto).

The .Presto format is a proprietary binary format. Key observations:
- Space names are stored after the marker sequence b'_SPC_\x00\x02\x01'
- Per-space total costs follow the pattern b'\x06\x01{NAME}\x00\x07\x00{8-byte LE double}'
- Budget code appears after b'\x04\x01' near the beginning of the file
- Files with a single 'Spc0010' space have no per-room breakdown
"""

from __future__ import annotations

import re
import struct
from pathlib import Path
from typing import Optional


# Zones for classifying spaces
_ZONE_MAP: dict[str, str] = {
    "AMENITIES": "COMUNES",
    "ASEO": "SERVICIO",
    "BALCONES": "EXTERIORES",
    "BAÑO MASTER": "NOBLE",
    "BAÑOS SECUNDARIOS": "NOBLE",
    "COCINA": "SERVICIO",
    "COCINA SERVICIO": "SERVICIO",
    "COMEDOR": "NOBLE",
    "COMUNES ARQUITECTURA": "COMUNES",
    "COMUNES FACHADA": "EXTERIORES",
    "HABITACION MASTER": "NOBLE",
    "HABITACIONES SECUNDARIAS": "NOBLE",
    "HABITACIONES DE SERVICIO": "SERVICIO",
    "JARDIN": "EXTERIORES",
    "PASILLOS": "COMUNES",
    "PISCINA": "EXTERIORES",
    "SALA": "NOBLE",
    "TERRAZAS": "EXTERIORES",
    "ZONAS DE SERVICIOS": "SERVICIO",
    "INSTALACIONES": "COMUNES",
}


def read_presto(filepath: str | Path) -> dict:
    """
    Parse a .Presto file and return a structured dict.

    Returns:
        {
            "filename": str,
            "source_format": "presto",
            "budget_code": str,
            "spaces": [
                {
                    "nombre": str,
                    "zona": str,
                    "coste": float,
                }
            ],
            "total_coste": float,
            "has_space_breakdown": bool,
            "errors": list[str],
            "warnings": list[str],
        }
    """
    filepath = Path(filepath)
    errors: list[str] = []
    warnings: list[str] = []

    try:
        with open(filepath, "rb") as f:
            raw = f.read()
    except OSError as e:
        return {
            "filename": filepath.name,
            "source_format": "presto",
            "budget_code": "UNKNOWN",
            "spaces": [],
            "total_coste": 0.0,
            "has_space_breakdown": False,
            "errors": [f"Cannot read file: {e}"],
            "warnings": [],
        }

    budget_code = _extract_budget_code(raw)
    spaces_raw = _extract_space_names(raw)
    space_costs = _extract_space_costs(raw, spaces_raw)

    # Detect whether this file has a real per-space breakdown
    has_breakdown = (
        len(spaces_raw) > 1
        or (len(spaces_raw) == 1 and spaces_raw[0] != "Spc0010")
    )

    if not has_breakdown:
        warnings.append(
            "File has no per-space breakdown (single generic space 'Spc0010'). "
            "Use BC3 import for chapter-level data."
        )

    # Build space list
    spaces = []
    for name in spaces_raw:
        if name == "Spc0010" and has_breakdown is False:
            # Generic placeholder — skip or include with warning
            continue
        cost = space_costs.get(name, 0.0)
        zona = _resolve_zone(name)
        spaces.append({"nombre": name, "zona": zona, "coste": cost})

    # If no real spaces, create a fallback
    if not spaces and not errors:
        fallback_cost = space_costs.get("Spc0010", 0.0)
        spaces.append({"nombre": "SIN DESGLOSE", "zona": "GLOBAL", "coste": fallback_cost})
        warnings.append("No per-space data found; using aggregate cost as a single space.")

    total_coste = sum(s["coste"] for s in spaces)

    return {
        "filename": filepath.name,
        "source_format": "presto",
        "budget_code": budget_code,
        "spaces": spaces,
        "total_coste": total_coste,
        "has_space_breakdown": has_breakdown,
        "errors": errors,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _extract_budget_code(raw: bytes) -> str:
    """Extract budget identifier from the first 20 000 bytes."""
    # Pattern: tag 0x04, tag 0x01, then a null-terminated ASCII-ish string
    for m in re.finditer(rb"\x04\x01([A-Za-z0-9._\- ]{2,30})\x00", raw[:20_000]):
        code = m.group(1).decode("latin-1", errors="replace").strip()
        if code and "_SPC_" not in code and len(code) >= 2:
            return code
    return "UNKNOWN"


def _extract_space_names(raw: bytes) -> list[str]:
    """Extract ordered space names from _SPC_ markers."""
    spaces: list[str] = []
    seen: set[str] = set()
    for m in re.finditer(rb"_SPC_\x00\x02\x01([^\x00]{2,50})\x00", raw):
        name = m.group(1).decode("latin-1", errors="replace").strip()
        if name and name not in seen:
            seen.add(name)
            spaces.append(name)
    return spaces


def _extract_space_costs(raw: bytes, space_names: list[str]) -> dict[str, float]:
    """
    For each space name, find the pattern:
      06 01 {NAME_BYTES} 00 07 00 {8-byte LE double}
    and return the cost.
    """
    costs: dict[str, float] = {}
    for name in space_names:
        try:
            name_bytes = name.encode("latin-1", errors="replace")
        except Exception:
            name_bytes = name.encode("ascii", errors="replace")

        pattern = b"\x06\x01" + name_bytes + b"\x00\x07\x00"
        for m in re.finditer(re.escape(pattern), raw):
            pos = m.end()
            if pos + 8 <= len(raw):
                val = struct.unpack_from("<d", raw, pos)[0]
                # Sanity check: positive finite float in plausible range
                if 0.01 < val < 1e8 and val == val:
                    costs[name] = round(val, 2)
                    break
    return costs


def _resolve_zone(space_name: str) -> str:
    """Map a space name to its architectural zone."""
    upper = space_name.upper()
    for key, zone in _ZONE_MAP.items():
        if key in upper or upper in key:
            return zone
    return "COMUNES"


# ---------------------------------------------------------------------------
# Hito 3: enhanced parser
# ---------------------------------------------------------------------------

def parse_presto(filepath: str | Path) -> dict:
    """
    High-level Presto parser for Hito 3 (space-level ratios).

    Returns:
        {
            "filename": str,
            "source_format": "presto",
            "budget_code": str,
            "espacios": [
                {
                    "nombre": str,
                    "zona": str,
                    "planta": "TOTAL",   # binary has no per-floor breakdown
                    "coste": float,
                    "m2": float,         # always 0.0 — binary does not expose m²
                    "partidas": [        # one synthetic entry per space
                        {
                            "codigo": str,
                            "descripcion": str,
                            "cantidad": float,
                            "unitario": float,
                            "coste": float,
                            "m2": float,
                        }
                    ],
                }
            ],
            "total_coste": float,
            "total_m2": float,
            "has_space_breakdown": bool,
            "errors": list[str],
            "warnings": list[str],
        }
    """
    base = read_presto(filepath)

    espacios = []
    for spc in base["spaces"]:
        nombre = spc["nombre"]
        coste = spc["coste"]
        zona = spc["zona"]
        # Presto binary stores only aggregate cost per space — no plant or m² data.
        espacios.append(
            {
                "nombre": nombre,
                "zona": zona,
                "planta": "TOTAL",
                "coste": coste,
                "m2": 0.0,
                "partidas": [
                    {
                        "codigo": f"{nombre[:8].replace(' ', '_')}.TOT",
                        "descripcion": f"Total {nombre}",
                        "cantidad": 1.0,
                        "unitario": coste,
                        "coste": coste,
                        "m2": 0.0,
                    }
                ],
            }
        )

    return {
        "filename": base["filename"],
        "source_format": "presto",
        "budget_code": base["budget_code"],
        "espacios": espacios,
        "total_coste": base["total_coste"],
        "total_m2": 0.0,
        "has_space_breakdown": base["has_space_breakdown"],
        "errors": base["errors"],
        "warnings": base["warnings"],
    }
