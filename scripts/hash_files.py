#!/usr/bin/env python3
"""Compute SHA256 hashes for files under data/samples."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

SAMPLES_DIR = Path("data/samples")
REPORT_PATH = Path("reports/sample_inspections/file_hashes.json")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_hashes(root: Path, samples_dir: Path) -> dict:
    absolute_samples = root / samples_dir
    entries: list[dict] = []

    if not absolute_samples.exists():
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "samples_dir": str(samples_dir).replace("\\", "/"),
            "exists": False,
            "files_count": 0,
            "duplicates_by_hash": [],
            "files": [],
            "message": "Samples directory does not exist.",
        }

    files = [p for p in absolute_samples.rglob("*") if p.is_file()]
    for file_path in sorted(files):
        stat = file_path.stat()
        file_hash = sha256_file(file_path)
        rel_path = file_path.relative_to(root)
        entries.append(
            {
                "relative_path": str(rel_path).replace("\\", "/"),
                "filename": file_path.name,
                "extension": file_path.suffix.lower(),
                "size_bytes": stat.st_size,
                "sha256": file_hash,
                "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            }
        )

    grouped: dict[str, list[str]] = defaultdict(list)
    for entry in entries:
        grouped[entry["sha256"]].append(entry["relative_path"])

    duplicates = [
        {"sha256": hash_value, "paths": sorted(paths), "count": len(paths)}
        for hash_value, paths in grouped.items()
        if len(paths) > 1
    ]
    duplicates.sort(key=lambda item: (-item["count"], item["sha256"]))

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "samples_dir": str(samples_dir).replace("\\", "/"),
        "exists": True,
        "files_count": len(entries),
        "duplicates_by_hash": duplicates,
        "files": entries,
        "message": "OK",
    }


def save_report(root: Path, report: dict, report_path: Path) -> Path:
    absolute_report = root / report_path
    absolute_report.parent.mkdir(parents=True, exist_ok=True)
    absolute_report.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return absolute_report


def print_summary(report: dict, report_path: Path) -> None:
    print("Hash scan summary")
    print(f"- Samples dir: {report['samples_dir']}")
    print(f"- Exists: {report['exists']}")
    print(f"- Files: {report['files_count']}")
    print(f"- Duplicate groups: {len(report['duplicates_by_hash'])}")
    print(f"- JSON report: {str(report_path).replace('\\', '/')}")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    report = collect_hashes(root, SAMPLES_DIR)
    output_path = save_report(root, report, REPORT_PATH)
    print_summary(report, output_path.relative_to(root))

    if not report["exists"]:
        print("WARNING: data/samples directory does not exist.")
    elif report["files_count"] == 0:
        print("INFO: No files found in data/samples.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
