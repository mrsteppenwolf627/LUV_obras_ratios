#!/usr/bin/env python3
"""Diagnostic BC3 inspection without parsing/importing data."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Any

SAMPLES_DIR = Path("data/samples")
REPORT_DIR = Path("reports/bc3_diagnostics")
JSON_REPORT = REPORT_DIR / "bc3_diagnostic_inventory.json"
MD_REPORT = REPORT_DIR / "bc3_diagnostic_inventory_report.md"

FIEBDC_RE = re.compile(r"(?i)fiebdc[^|\\]*")
REG_TYPE_RE = re.compile(r"^(~[A-Za-z])")
NUMERIC_RE = re.compile(r"^-?\d+(?:[.,]\d+)?$")
AMOUNT_LIKE_RE = re.compile(r"^-?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})$")
UNIT_RE = re.compile(r"^(m2|m3|ml|m|ud|u|kg|l|h)$", re.IGNORECASE)
CODE_CHAPTER_RE = re.compile(r"^[A-Za-z]{0,3}\d+[A-Za-z0-9]*#?$")
CODE_ITEM_RE = re.compile(r"^[A-Za-z]{0,3}\d+[A-Za-z0-9]+$")
ABSOLUTE_PATH_HINT_RE = re.compile(r"(?i)([a-z]:\\\\|/home/|/users/|\\\\\\\\)")


def detect_encoding(raw: bytes) -> dict[str, Any]:
    if not raw:
        return {
            "encoding": "unknown",
            "confidence": "low",
            "strategy": "empty_file",
        }

    try:
        raw.decode("utf-8")
        return {"encoding": "utf-8", "confidence": "high", "strategy": "utf-8"}
    except UnicodeDecodeError:
        pass

    try:
        raw.decode("cp1252")
        return {"encoding": "cp1252", "confidence": "medium", "strategy": "cp1252_fallback"}
    except UnicodeDecodeError:
        return {"encoding": "binary_or_unknown", "confidence": "low", "strategy": "decode_failed"}


def _candidate_code(token: str) -> str:
    return token.split("\\", 1)[0].strip()


def _sanitize_sample(line: str, limit: int = 80) -> str:
    compact = line.replace("\t", " ").strip()
    compact = re.sub(r"\d{3,}", "[NUM]", compact)
    compact = ABSOLUTE_PATH_HINT_RE.sub("[PATH]", compact)
    return compact[:limit]


def _sanitize_code(code: str, keep: int = 4) -> str:
    cleaned = code.strip()
    if len(cleaned) <= keep:
        return cleaned
    return f"{cleaned[:keep]}..."


def _is_chapter_candidate(code: str) -> bool:
    if code.endswith("#"):
        return True
    # Heuristic: short alphanumeric roots (e.g., CAP01) are chapter-like.
    return bool(re.match(r"^[A-Za-z]{2,4}\d{1,3}$", code))


def _estimate_depth(relations: set[tuple[str, str]]) -> int:
    if not relations:
        return 0
    children_by_parent: dict[str, set[str]] = {}
    for parent, child in relations:
        children_by_parent.setdefault(parent, set()).add(child)

    max_depth = 0
    for root in children_by_parent:
        stack: list[tuple[str, int, set[str]]] = [(root, 1, {root})]
        while stack:
            node, depth, seen = stack.pop()
            max_depth = max(max_depth, depth)
            for child in children_by_parent.get(node, set()):
                if child in seen:
                    continue
                stack.append((child, depth + 1, seen | {child}))
    return max_depth


def _build_file_risks(inspection: dict[str, Any]) -> list[dict[str, str]]:
    risks: list[dict[str, str]] = []
    status = inspection.get("status")
    if status in {"BC3_READ_FAILED", "BC3_DECODE_UNCERTAIN"}:
        risks.append({"severity": "BLOCKED", "code": "DECODE_OR_READ_BLOCKED", "detail": status})
    if not inspection.get("fiebdc_header_line"):
        risks.append({"severity": "ERROR", "code": "MISSING_V_HEADER", "detail": "No ~V header detected"})
    if inspection.get("encoding_confidence") == "medium":
        risks.append({"severity": "WARNING", "code": "ENCODING_MEDIUM_CONFIDENCE", "detail": "Encoding fallback used"})
    if inspection.get("hierarchy_summary", {}).get("incomplete_relations_count", 0) > 0:
        risks.append({"severity": "MANUAL_REVIEW_REQUIRED", "code": "INCOMPLETE_RELATIONS", "detail": "Found relations without parent/child"})
    if not inspection.get("hierarchy_relations_candidates"):
        risks.append({"severity": "WARNING", "code": "NO_D_RELATIONS", "detail": "No ~D relations detected"})
    non_common = inspection.get("fiebdc_variant_signals", {}).get("non_common_record_types", [])
    if len(non_common) >= 3:
        risks.append({"severity": "MANUAL_REVIEW_REQUIRED", "code": "MANY_UNKNOWN_RECORDS", "detail": f"{len(non_common)} non-common record types"})
    elif non_common:
        risks.append({"severity": "WARNING", "code": "UNKNOWN_RECORD_TYPES", "detail": ",".join(non_common)})
    if inspection.get("economic_field_diagnostics", {}).get("ambiguous_economic_tokens"):
        risks.append({"severity": "WARNING", "code": "AMBIGUOUS_ECONOMIC_TOKENS", "detail": "Numeric tokens exceed amount-like tokens"})
    units_count = len(inspection.get("units_detected", []))
    if units_count > 5:
        risks.append({"severity": "WARNING", "code": "MULTIPLE_UNITS", "detail": str(units_count)})
    elif units_count > 1:
        risks.append({"severity": "INFO", "code": "MULTIPLE_UNITS", "detail": str(units_count)})
    if not risks:
        risks.append({"severity": "INFO", "code": "NO_RELEVANT_RISKS", "detail": "Diagnostic signals look stable"})
    return risks


def _compute_readiness(files: list[dict[str, Any]]) -> dict[str, Any]:
    severity_counts = Counter()
    reasons: list[str] = []
    for entry in files:
        for risk in entry.get("risk_matrix", []):
            sev = risk.get("severity", "INFO")
            severity_counts[sev] += 1

    if severity_counts["BLOCKED"] > 0:
        status = "BLOCKED_BY_DECODING_OR_STRUCTURE"
        reasons.append("At least one file is blocked by decoding/readability issues.")
    elif severity_counts["ERROR"] > 0 or severity_counts["MANUAL_REVIEW_REQUIRED"] > 0:
        status = "NEEDS_MORE_DIAGNOSTIC_HEURISTICS"
        reasons.append("Critical structure warnings still require manual/heuristic iteration.")
    else:
        status = "READY_FOR_PRELIMINARY_PARSER_DESIGN"
        reasons.append("No blocked or critical structural risks detected.")

    conditions = [
        "Keep parser scope preliminary and diagnostic-aware.",
        "Do not import into master during parser design.",
        "Keep sensitive real reports outside Git.",
    ]
    blockers = [k for k in ("BLOCKED", "ERROR", "MANUAL_REVIEW_REQUIRED") if severity_counts[k] > 0]
    return {
        "status": status,
        "reasons": reasons,
        "blockers": blockers,
        "severity_counts": dict(severity_counts),
        "minimum_conditions_for_phase_4": conditions,
    }


def inspect_bc3_file(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
    except Exception as exc:
        return {
            "status": "BC3_READ_FAILED",
            "encoding": "unknown",
            "encoding_confidence": "low",
            "record_types_present": [],
            "record_type_counts": {},
            "fiebdc_header_line": None,
            "fiebdc_version_candidate": None,
            "chapter_code_candidates": [],
            "hierarchy_relations_candidates": [],
            "units_detected": [],
            "amount_indicators": {"numeric_tokens_count": 0, "amount_like_tokens_count": 0},
            "c_code_classification": {},
            "hierarchy_summary": {},
            "record_type_stats": {},
            "economic_field_diagnostics": {},
            "text_field_diagnostics": {},
            "fiebdc_variant_signals": {},
            "warnings": ["READ_FAILED"],
            "notes": f"Could not read file: {exc}",
        }

    enc = detect_encoding(raw)
    if enc["encoding"] == "binary_or_unknown":
        return {
            "status": "BC3_DECODE_UNCERTAIN",
            "encoding": enc["encoding"],
            "encoding_confidence": enc["confidence"],
            "record_types_present": [],
            "record_type_counts": {},
            "fiebdc_header_line": None,
            "fiebdc_version_candidate": None,
            "chapter_code_candidates": [],
            "hierarchy_relations_candidates": [],
            "units_detected": [],
            "amount_indicators": {"numeric_tokens_count": 0, "amount_like_tokens_count": 0},
            "c_code_classification": {},
            "hierarchy_summary": {},
            "record_type_stats": {},
            "economic_field_diagnostics": {},
            "text_field_diagnostics": {},
            "fiebdc_variant_signals": {},
            "warnings": ["DECODE_UNCERTAIN"],
            "notes": "Could not decode file with supported encodings.",
        }

    text = raw.decode(enc["encoding"], errors="replace")
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    record_type_counts: Counter[str] = Counter()
    record_type_lengths: Counter[str] = Counter()
    record_type_numeric_tokens: Counter[str] = Counter()
    record_type_amount_like_tokens: Counter[str] = Counter()
    record_type_long_text_fields: Counter[str] = Counter()
    record_type_text_len: Counter[str] = Counter()
    record_type_text_count: Counter[str] = Counter()
    record_type_samples: dict[str, list[str]] = {}
    chapter_codes: set[str] = set()
    item_codes: set[str] = set()
    other_codes: set[str] = set()
    relations: set[tuple[str, str]] = set()
    incomplete_relations = 0
    units: set[str] = set()
    numeric_tokens_count = 0
    amount_like_tokens_count = 0
    fiebdc_header_line: str | None = None
    fiebdc_version_candidate: str | None = None

    for line in lines:
        if line.startswith("~") is False:
            continue

        m_type = REG_TYPE_RE.match(line)
        if not m_type:
            continue
        record_type = m_type.group(1).upper()
        record_type_counts[record_type] += 1
        record_type_lengths[record_type] += len(line)
        if record_type not in record_type_samples:
            record_type_samples[record_type] = []
        if len(record_type_samples[record_type]) < 2:
            record_type_samples[record_type].append(_sanitize_sample(line))

        if record_type == "~V" and fiebdc_header_line is None:
            fiebdc_header_line = _sanitize_sample(line, 120)
            m_fiebdc = FIEBDC_RE.search(line)
            if m_fiebdc:
                fiebdc_version_candidate = m_fiebdc.group(0)

        payload = line[2:].lstrip("|")
        fields = payload.split("|")

        if record_type == "~C" and fields:
            code = _candidate_code(fields[0])
            if code:
                if _is_chapter_candidate(code):
                    chapter_codes.add(code)
                elif CODE_ITEM_RE.match(code):
                    item_codes.add(code)
                else:
                    other_codes.add(code)

        if record_type == "~D":
            parent = _candidate_code(fields[0]) if len(fields) >= 1 else ""
            child = _candidate_code(fields[1]) if len(fields) >= 2 else ""
            if parent and child:
                relations.add((parent, child))
            else:
                incomplete_relations += 1

        for field in fields:
            if len(field) >= 30:
                record_type_long_text_fields[record_type] += 1
                record_type_text_len[record_type] += len(field)
                record_type_text_count[record_type] += 1
            for token in re.split(r"[\\;,\s]+", field):
                candidate = token.strip()
                if not candidate:
                    continue
                if UNIT_RE.match(candidate):
                    units.add(candidate.lower())
                if NUMERIC_RE.match(candidate):
                    numeric_tokens_count += 1
                    record_type_numeric_tokens[record_type] += 1
                if AMOUNT_LIKE_RE.match(candidate):
                    amount_like_tokens_count += 1
                    record_type_amount_like_tokens[record_type] += 1

    total_records = sum(record_type_counts.values())
    record_type_stats: dict[str, Any] = {}
    for rtype in sorted(record_type_counts.keys()):
        count = record_type_counts[rtype]
        pct = (count / total_records * 100.0) if total_records else 0.0
        avg_len = (record_type_lengths[rtype] / count) if count else 0.0
        record_type_stats[rtype] = {
            "count": count,
            "percentage_of_total": round(pct, 2),
            "avg_length": round(avg_len, 2),
            "samples_sanitized": record_type_samples.get(rtype, []),
        }

    parents = {p for p, _ in relations}
    children = {c for _, c in relations}
    depth = _estimate_depth(relations)
    hierarchy_summary = {
        "relations_count": len(relations),
        "parent_nodes_count": len(parents),
        "child_nodes_count": len(children),
        "max_depth_approx": depth,
        "incomplete_relations_count": incomplete_relations,
    }

    unknown_record_types = sorted(
        r for r in record_type_counts.keys() if r not in {"~V", "~C", "~D", "~K", "~M", "~T"}
    )
    warnings: list[str] = []
    if enc["confidence"] == "medium":
        warnings.append("ENCODING_MEDIUM_CONFIDENCE")
    if unknown_record_types:
        warnings.append(f"NON_COMMON_RECORD_TYPES:{','.join(unknown_record_types)}")
    if incomplete_relations > 0:
        warnings.append(f"INCOMPLETE_RELATIONS:{incomplete_relations}")
    if amount_like_tokens_count > 0 and amount_like_tokens_count < numeric_tokens_count:
        warnings.append("AMBIGUOUS_ECONOMIC_TOKENS")
    if len(units) > 3:
        warnings.append(f"MULTIPLE_UNITS:{len(units)}")

    return {
        "status": "BC3_DIAGNOSTIC_OK",
        "encoding": enc["encoding"],
        "encoding_confidence": enc["confidence"],
        "record_types_present": sorted(record_type_counts.keys()),
        "record_type_counts": dict(sorted(record_type_counts.items())),
        "fiebdc_header_line": fiebdc_header_line,
        "fiebdc_version_candidate": fiebdc_version_candidate,
        "chapter_code_candidates": sorted(chapter_codes),
        "c_code_classification": {
            "chapter_candidates_count": len(chapter_codes),
            "item_candidates_count": len(item_codes),
            "other_candidates_count": len(other_codes),
            "chapter_candidates_sample": [_sanitize_code(c) for c in sorted(chapter_codes)[:10]],
            "item_candidates_sample": [_sanitize_code(c) for c in sorted(item_codes)[:10]],
            "other_candidates_sample": [_sanitize_code(c) for c in sorted(other_codes)[:10]],
        },
        "hierarchy_relations_candidates": [
            {"parent": parent, "child": child} for parent, child in sorted(relations)
        ],
        "hierarchy_summary": hierarchy_summary,
        "record_type_stats": record_type_stats,
        "units_detected": sorted(units),
        "amount_indicators": {
            "numeric_tokens_count": numeric_tokens_count,
            "amount_like_tokens_count": amount_like_tokens_count,
        },
        "economic_field_diagnostics": {
            "numeric_tokens_by_record_type": dict(sorted(record_type_numeric_tokens.items())),
            "amount_like_tokens_by_record_type": dict(sorted(record_type_amount_like_tokens.items())),
            "ambiguous_economic_tokens": amount_like_tokens_count > 0 and amount_like_tokens_count < numeric_tokens_count,
        },
        "text_field_diagnostics": {
            "long_text_fields_by_record_type": dict(sorted(record_type_long_text_fields.items())),
            "avg_text_length_by_record_type": {
                key: round(record_type_text_len[key] / record_type_text_count[key], 2)
                for key in sorted(record_type_text_count.keys())
                if record_type_text_count[key] > 0
            },
            "most_textual_record_types": [
                key
                for key, _ in sorted(
                    record_type_text_len.items(),
                    key=lambda kv: kv[1],
                    reverse=True,
                )[:3]
            ],
        },
        "fiebdc_variant_signals": {
            "version_candidate": fiebdc_version_candidate,
            "non_common_record_types": unknown_record_types,
        },
        "warnings": warnings,
        "notes": "Diagnostic-only extraction. No parser, no totals, no master update.",
    }


def inspect_bc3_samples(root: Path) -> dict[str, Any]:
    samples_path = root / SAMPLES_DIR
    generated_at = datetime.now(timezone.utc).isoformat()

    if not samples_path.exists():
        return {
            "generated_at": generated_at,
            "samples_dir": str(SAMPLES_DIR).replace("\\", "/"),
            "exists": False,
            "bc3_files_count": 0,
            "message": "Samples directory does not exist.",
            "files": [],
        }

    bc3_files = sorted([p for p in samples_path.rglob("*") if p.is_file() and p.suffix.lower() == ".bc3"])
    entries: list[dict[str, Any]] = []
    for index, file_path in enumerate(bc3_files, start=1):
        rel = file_path.relative_to(root)
        inspection = inspect_bc3_file(file_path)
        risk_matrix = _build_file_risks(inspection)
        sanitized_id = f"BC3_{index:02d}"
        entries.append(
            {
                "sanitized_id": sanitized_id,
                "relative_path": str(rel).replace("\\", "/"),
                "filename": file_path.name,
                "extension": file_path.suffix.lower(),
                "size_bytes": file_path.stat().st_size,
                "inspection": inspection,
                "risk_matrix": risk_matrix,
            }
        )

    variant_versions = sorted(
        {
            entry["inspection"].get("fiebdc_version_candidate")
            for entry in entries
            if entry["inspection"].get("fiebdc_version_candidate")
        }
    )
    common_types: set[str] | None = None
    for entry in entries:
        types = set(entry["inspection"].get("record_types_present", []))
        if common_types is None:
            common_types = types
        else:
            common_types = common_types & types

    variant_warnings: list[str] = []
    if len(variant_versions) > 1:
        variant_warnings.append(f"MULTIPLE_FIEBDC_VERSIONS:{','.join(variant_versions)}")
    if entries:
        union_types = set().union(*(set(e["inspection"].get("record_types_present", [])) for e in entries))
        common_types = common_types or set()
        uncommon = sorted(union_types - common_types)
        if uncommon:
            variant_warnings.append(f"RECORD_TYPES_NOT_COMMON_TO_ALL:{','.join(uncommon)}")

    common_units: set[str] | None = None
    units_union: set[str] = set()
    for entry in entries:
        u = set(entry["inspection"].get("units_detected", []))
        units_union |= u
        if common_units is None:
            common_units = u
        else:
            common_units = common_units & u

    by_file_exclusive_types: dict[str, list[str]] = {}
    by_file_exclusive_units: dict[str, list[str]] = {}
    all_types_by_file = {
        e["sanitized_id"]: set(e["inspection"].get("record_types_present", []))
        for e in entries
    }
    all_units_by_file = {
        e["sanitized_id"]: set(e["inspection"].get("units_detected", []))
        for e in entries
    }
    for sid, rtypes in all_types_by_file.items():
        others = set().union(*(v for k, v in all_types_by_file.items() if k != sid)) if len(all_types_by_file) > 1 else set()
        by_file_exclusive_types[sid] = sorted(rtypes - others)
    for sid, units in all_units_by_file.items():
        others = set().union(*(v for k, v in all_units_by_file.items() if k != sid)) if len(all_units_by_file) > 1 else set()
        by_file_exclusive_units[sid] = sorted(units - others)

    hierarchy_depths = {
        e["sanitized_id"]: e["inspection"].get("hierarchy_summary", {}).get("max_depth_approx", 0)
        for e in entries
    }
    economic_density = {
        e["sanitized_id"]: e["inspection"].get("amount_indicators", {}).get("numeric_tokens_count", 0)
        for e in entries
    }
    text_density = {
        e["sanitized_id"]: sum(e["inspection"].get("text_field_diagnostics", {}).get("long_text_fields_by_record_type", {}).values())
        for e in entries
    }

    comparison = {
        "files_considered": [e["sanitized_id"] for e in entries],
        "fiebdc_versions_detected": variant_versions,
        "record_types_common_to_all": sorted(common_types or set()),
        "record_types_exclusive_by_file": by_file_exclusive_types,
        "units_common_to_all": sorted(common_units or set()),
        "units_exclusive_by_file": by_file_exclusive_units,
        "hierarchy_depth_by_file": hierarchy_depths,
        "economic_density_by_file": economic_density,
        "text_density_by_file": text_density,
        "variability_warnings": variant_warnings,
    }

    readiness = _compute_readiness(entries)
    sensitive = any(
        entry["inspection"].get("amount_indicators", {}).get("numeric_tokens_count", 0) > 0
        or bool(entry["inspection"].get("chapter_code_candidates"))
        for entry in entries
    )
    sensitivity = {
        "contains_potentially_sensitive_data": sensitive,
        "policy": "Real BC3 reports are local-only and must stay outside Git.",
    }

    return {
        "generated_at": generated_at,
        "samples_dir": str(SAMPLES_DIR).replace("\\", "/"),
        "exists": True,
        "bc3_files_count": len(entries),
        "message": "OK" if entries else "No BC3 files found in data/samples.",
        "variant_warnings": variant_warnings,
        "readiness_summary": readiness,
        "bc3_comparison": comparison,
        "sensitivity": sensitivity,
        "files": entries,
    }


def write_reports(root: Path, report: dict[str, Any]) -> tuple[Path, Path]:
    json_path = root / JSON_REPORT
    md_path = root / MD_REPORT
    json_path.parent.mkdir(parents=True, exist_ok=True)

    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    lines: list[str] = []
    lines.append("# BC3 Diagnostic Report")
    lines.append("")
    lines.append("> Local diagnostic report. May contain sensitive metadata from real samples.")
    lines.append("")
    lines.append(f"- Generated at (UTC): {report['generated_at']}")
    lines.append(f"- Samples directory: {report['samples_dir']}")
    lines.append(f"- Exists: {report['exists']}")
    lines.append(f"- BC3 files count: {report['bc3_files_count']}")
    lines.append(f"- Message: {report['message']}")
    if report.get("sensitivity"):
        lines.append(
            f"- Potentially sensitive: {report['sensitivity'].get('contains_potentially_sensitive_data')}"
        )
    if report.get("variant_warnings"):
        lines.append(f"- Variant warnings: {', '.join(report['variant_warnings'])}")
    readiness = report.get("readiness_summary", {})
    if readiness:
        lines.append(f"- Readiness: {readiness.get('status')}")
        lines.append(f"- Readiness reasons: {', '.join(readiness.get('reasons', []))}")
    lines.append("")
    lines.append("## Global Readiness")
    lines.append("")
    if readiness:
        lines.append(f"- Status: {readiness.get('status')}")
        lines.append(f"- Blockers: {', '.join(readiness.get('blockers', [])) or 'none'}")
        sev = readiness.get("severity_counts", {})
        lines.append(
            "- Severity counts: "
            + ", ".join(f"{k}={v}" for k, v in sorted(sev.items()))
        )
    lines.append("")
    lines.append("## BC3 Comparison")
    lines.append("")
    comparison = report.get("bc3_comparison", {})
    if comparison:
        lines.append(f"- Files considered: {', '.join(comparison.get('files_considered', [])) or 'none'}")
        lines.append(f"- FIEBDC versions: {', '.join(comparison.get('fiebdc_versions_detected', [])) or 'none'}")
        lines.append(f"- Common record types: {', '.join(comparison.get('record_types_common_to_all', [])) or 'none'}")
        if comparison.get("variability_warnings"):
            lines.append(f"- Variability warnings: {', '.join(comparison.get('variability_warnings', []))}")
    lines.append("")
    lines.append("## Files")
    lines.append("")

    if report.get("files"):
        for entry in report["files"]:
            insp = entry["inspection"]
            lines.append(f"### {entry.get('sanitized_id', 'BC3')} ({entry['extension']}, {entry['size_bytes']} bytes)")
            lines.append(f"- Status: {insp['status']}")
            lines.append(f"- Encoding: {insp['encoding']} ({insp['encoding_confidence']})")
            lines.append(f"- FIEBDC candidate: {insp.get('fiebdc_version_candidate')}")
            lines.append(f"- Record types present: {', '.join(insp.get('record_types_present', [])) or 'none'}")
            lines.append(
                f"- Chapter candidates: {len(insp.get('chapter_code_candidates', []))} | Relations: {len(insp.get('hierarchy_relations_candidates', []))}"
            )
            lines.append(
                f"- Amount indicators: numeric={insp['amount_indicators']['numeric_tokens_count']}, amount_like={insp['amount_indicators']['amount_like_tokens_count']}"
            )
            classif = insp.get("c_code_classification", {})
            lines.append(
                f"- C code classes: chapters={classif.get('chapter_candidates_count', 0)}, items={classif.get('item_candidates_count', 0)}, others={classif.get('other_candidates_count', 0)}"
            )
            hs = insp.get("hierarchy_summary", {})
            lines.append(
                f"- Hierarchy summary: relations={hs.get('relations_count', 0)}, parents={hs.get('parent_nodes_count', 0)}, children={hs.get('child_nodes_count', 0)}, depth~={hs.get('max_depth_approx', 0)}"
            )
            text_diag = insp.get("text_field_diagnostics", {})
            lines.append(
                f"- Text diagnostics: most_textual={', '.join(text_diag.get('most_textual_record_types', [])) or 'none'}"
            )
            if insp.get("warnings"):
                lines.append(f"- Warnings: {', '.join(insp['warnings'])}")
            if entry.get("risk_matrix"):
                rendered_risks = [f"{r['severity']}:{r['code']}" for r in entry["risk_matrix"]]
                lines.append(f"- Risk matrix: {', '.join(rendered_risks)}")
            lines.append("")
    else:
        lines.append("No BC3 files found.")
        lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def print_summary(report: dict[str, Any], json_path: Path, md_path: Path, root: Path) -> None:
    print("BC3 diagnostic summary")
    print(f"- Samples dir: {report['samples_dir']}")
    print(f"- Exists: {report['exists']}")
    print(f"- BC3 files: {report['bc3_files_count']}")
    print(f"- JSON report: {json_path.relative_to(root).as_posix()}")
    print(f"- Markdown report: {md_path.relative_to(root).as_posix()}")


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    report = inspect_bc3_samples(root)
    json_path, md_path = write_reports(root, report)
    print_summary(report, json_path, md_path, root)
    if report["exists"] and report["bc3_files_count"] == 0:
        print("INFO: No BC3 files found in data/samples.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
