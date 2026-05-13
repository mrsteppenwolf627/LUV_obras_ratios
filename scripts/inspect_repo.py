#!/usr/bin/env python3
"""Print a simple summary of repository governance and structure."""

from pathlib import Path

MAIN_DIRS = [
    "docs",
    "data",
    "logs",
    "reports",
    "src",
    "scripts",
    "tests",
    ".context-backups",
]

METHODOLOGY_FILES = [
    "CONTEXT.md",
    "ADRs.md",
    "README.md",
]

REQUIRED_DATA_DIRS = [
    "data/raw",
    "data/processed",
    "data/master",
    "data/samples",
]

REQUIRED_SRC_DIRS = [
    "src/parsers",
    "src/validators",
    "src/mappers",
    "src/exporters",
]


def exists_label(root: Path, relative: str) -> str:
    return "YES" if (root / relative).exists() else "NO"


def print_group(title: str, items: list[str], root: Path) -> None:
    print(title)
    for item in items:
        print(f"- {item}: {exists_label(root, item)}")
    print()


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    print(f"Repository: {root}")
    print()

    print_group("Main directories", MAIN_DIRS, root)
    print_group("Methodology files", METHODOLOGY_FILES, root)
    print_group("Required data folders", REQUIRED_DATA_DIRS, root)
    print_group("Required src folders", REQUIRED_SRC_DIRS, root)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
