#!/usr/bin/env python3
"""Validate that CONTEXT.md contains mandatory governance sections."""

from pathlib import Path
import sys

REQUIRED_SECTIONS = [
    "## Arquitectura",
    "## Objetivo del proyecto",
    "## Herramientas operativas",
    "## Restricciones cr?ticas",
    "## Estado actual",
    "## Backlog priorizado",
    "## Riesgos t?cnicos",
    "## Reglas de actualizaci?n",
]


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    context_path = root / "CONTEXT.md"

    if not context_path.exists():
        print("ERROR: CONTEXT.md no existe en la ra?z del repositorio.")
        return 1

    content = context_path.read_text(encoding="utf-8")

    missing = [section for section in REQUIRED_SECTIONS if section not in content]
    if missing:
        print("ERROR: CONTEXT.md no contiene todas las secciones obligatorias.")
        for section in missing:
            print(f"- Falta: {section}")
        return 1

    print("OK: CONTEXT.md contiene todas las secciones obligatorias.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
