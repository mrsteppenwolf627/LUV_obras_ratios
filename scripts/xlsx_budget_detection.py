"""Focused XLSX budget heuristics for PREVIEW_ONLY extraction."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import re
import unicodedata
from typing import Any


ROW_CHAPTER = "CHAPTER"
ROW_SUBCHAPTER = "SUBCHAPTER"
ROW_COST_ITEM = "COST_ITEM"
ROW_SUBTOTAL = "SUBTOTAL"
ROW_TOTAL = "TOTAL"
ROW_HEADER = "HEADER"
ROW_EMPTY = "EMPTY"
ROW_NON_BUDGET = "NON_BUDGET_ROW"
ROW_UNKNOWN = "UNKNOWN"
ROW_AMBIGUOUS = "AMBIGUOUS"
ROW_MANUAL_REVIEW = "MANUAL_REVIEW_REQUIRED"

MAPPING_MAPPED = "MAPPED"
MAPPING_UNMAPPED = "UNMAPPED"
MAPPING_NOT_COST_ITEM = "NOT_COST_ITEM"
MAPPING_AMBIGUOUS = "AMBIGUOUS"
MAPPING_MANUAL_REVIEW = "MANUAL_REVIEW_REQUIRED"

NUMERIC_HIGH = "HIGH"
NUMERIC_LOW = "LOW"
NUMERIC_NONE = "NONE"

HEADER_HIGH = "HIGH"
HEADER_LOW = "LOW"
HEADER_NONE = "NONE"

FIELD_ORDER = [
    "chapter_code",
    "chapter_name",
    "item_code",
    "item_description",
    "unit",
    "quantity",
    "unit_price",
    "amount",
]

HEADER_ALIASES: dict[str, tuple[str, ...]] = {
    "chapter_code": (
        "capitulo codigo",
        "codigo capitulo",
        "chapter code",
        "cap code",
    ),
    "chapter_name": (
        "capitulo",
        "capitulo nombre",
        "chapter",
        "chapter name",
        "subcapitulo",
    ),
    "item_code": (
        "codigo",
        "codigo partida",
        "cod",
        "ref",
        "referencia",
        "item code",
        "partida codigo",
        "partida",
    ),
    "item_description": (
        "descripcion",
        "description",
        "concepto",
        "texto",
        "detalle",
        "resumen",
        "nombre",
    ),
    "unit": (
        "unidad",
        "unidades",
        "ud",
        "uds",
        "unit",
    ),
    "quantity": (
        "cantidad",
        "medicion",
        "med",
        "qty",
        "quantity",
    ),
    "unit_price": (
        "precio unitario",
        "p unitario",
        "p unit",
        "punitario",
        "precio ud",
        "precio unidad",
        "precio",
        "unitario",
        "unit price",
    ),
    "amount": (
        "importe",
        "importe total",
        "total presupuesto",
        "presupuesto",
        "coste",
        "coste total",
        "amount",
        "total",
        "pem",
    ),
}

UNIT_VALUES = {
    "m",
    "m2",
    "m3",
    "ml",
    "kg",
    "t",
    "tn",
    "ud",
    "uds",
    "u",
    "h",
    "pa",
    "l",
}

TOTAL_WORDS = {"total", "totales", "presupuesto total", "total presupuesto"}
SUBTOTAL_WORDS = {"subtotal", "sub total", "sub-total"}
HEADER_HINT_WORDS = {alias for aliases in HEADER_ALIASES.values() for alias in aliases}


@dataclass(frozen=True)
class ParsedNumber:
    normalized: str
    confidence: str
    reason: str = ""

    @property
    def is_valid(self) -> bool:
        return bool(self.normalized)


@dataclass(frozen=True)
class HeaderDetection:
    header_row: int
    mapping: dict[str, int]
    confidence: str
    score: int
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class BudgetRowExtraction:
    source_sheet_name: str
    source_row_number: int
    chapter_code: str
    chapter_name: str
    item_code: str
    item_description: str
    unit: str
    quantity: str
    unit_price: str
    amount: str
    validation_status: str
    notes: str
    row_class: str
    mapping_status: str

    @property
    def should_create_cost_item(self) -> bool:
        return self.mapping_status == MAPPING_MAPPED and self.row_class == ROW_COST_ITEM


def normalize_label(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.strip().lower()
    text = "".join(
        char for char in unicodedata.normalize("NFD", text) if unicodedata.category(char) != "Mn"
    )
    text = text.replace("\n", " ").replace("\r", " ").replace("_", " ")
    text = re.sub(r"[^\w\s]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _safe_text(value: object) -> str:
    return "" if value is None else str(value).strip()


def _is_empty(value: object) -> bool:
    return value is None or str(value).strip() == ""


def _decimal_to_text(value: Decimal) -> str:
    normalized = format(value.normalize(), "f")
    if "." in normalized:
        normalized = normalized.rstrip("0").rstrip(".")
    return normalized or "0"


def parse_budget_number(value: object, field_context: str = "") -> ParsedNumber:
    if value is None or isinstance(value, bool):
        return ParsedNumber("", NUMERIC_NONE, "empty_or_bool")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if field_context in {"item_code", "chapter_code"}:
            return ParsedNumber("", NUMERIC_NONE, "code_context")
        return ParsedNumber(_decimal_to_text(Decimal(str(value))), NUMERIC_HIGH)

    raw = str(value).strip()
    if not raw:
        return ParsedNumber("", NUMERIC_NONE, "empty")

    lowered = raw.lower()
    has_money_context = any(token in lowered for token in ("€", "eur", "euro"))
    negative = False
    if raw.startswith("(") and raw.endswith(")"):
        negative = True
        raw = raw[1:-1].strip()
    if raw.startswith("-"):
        negative = True
        raw = raw[1:].strip()

    cleaned = raw.replace("€", "").replace("EUR", "").replace("eur", "").strip()
    cleaned = cleaned.replace("\u00a0", " ").replace(" ", "")

    if field_context in {"item_code", "chapter_code"}:
        return ParsedNumber("", NUMERIC_NONE, "code_context")
    if re.search(r"[A-Za-z]", cleaned):
        return ParsedNumber("", NUMERIC_NONE, "letters_present")
    if not re.fullmatch(r"\d+(?:[.,]\d+)*(?:[.,]\d+)?", cleaned):
        return ParsedNumber("", NUMERIC_NONE, "not_numeric")
    if re.fullmatch(r"\d+(?:[.]\d+){2,}", cleaned) or re.fullmatch(r"\d+(?:[,]\d+){2,}", cleaned):
        return ParsedNumber("", NUMERIC_NONE, "code_like_number")
    if (
        not has_money_context
        and field_context not in {"amount", "quantity", "unit_price"}
        and re.fullmatch(r"\d{4}", cleaned)
        and 1900 <= int(cleaned) <= 2100
    ):
        return ParsedNumber("", NUMERIC_NONE, "year_like")

    decimal_separator = ""
    if "," in cleaned and "." in cleaned:
        decimal_separator = "," if cleaned.rfind(",") > cleaned.rfind(".") else "."
    elif "," in cleaned:
        parts = cleaned.split(",")
        if len(parts[-1]) in (1, 2):
            decimal_separator = ","
        elif len(parts[-1]) == 3 and field_context in {"amount", "quantity", "unit_price"}:
            decimal_separator = ""
        else:
            return ParsedNumber("", NUMERIC_LOW, "ambiguous_comma")
    elif "." in cleaned:
        parts = cleaned.split(".")
        if len(parts) == 2 and len(parts[-1]) in (1, 2):
            decimal_separator = "."
        elif len(parts[-1]) == 3 and field_context in {"amount", "quantity", "unit_price"}:
            decimal_separator = ""
        else:
            return ParsedNumber("", NUMERIC_LOW, "ambiguous_dot")

    if decimal_separator:
        thousands_separator = "." if decimal_separator == "," else ","
        numeric = cleaned.replace(thousands_separator, "").replace(decimal_separator, ".")
    else:
        numeric = cleaned.replace(".", "").replace(",", "")

    try:
        parsed = Decimal(numeric)
    except InvalidOperation:
        return ParsedNumber("", NUMERIC_NONE, "decimal_error")
    if negative:
        parsed = -parsed

    confidence = NUMERIC_HIGH if field_context in {"amount", "quantity", "unit_price"} or has_money_context else NUMERIC_LOW
    return ParsedNumber(_decimal_to_text(parsed), confidence)


def looks_like_budget_number(value: object, field_context: str = "") -> bool:
    return parse_budget_number(value, field_context=field_context).is_valid


def contains_budget_number(value: object) -> bool:
    text = _safe_text(value)
    if not text:
        return False
    if parse_budget_number(text, field_context="amount").is_valid:
        return True
    candidates = re.findall(r"(?:€\s*)?-?\(?\d[\d\s.,]*\)?\s*(?:€|eur|EUR)?", text)
    for candidate in candidates:
        if parse_budget_number(candidate, field_context="amount").is_valid:
            return True
    return False


def _split_trailing_amount_from_description(text: str) -> tuple[str, str]:
    cleaned = text.strip()
    if not cleaned:
        return "", ""
    match = re.search(
        r"(?P<amount>(?:€\s*)?-?\(?\d[\d\s.,]*\)?\s*(?:€|eur|EUR)?)\s*$",
        cleaned,
    )
    if not match:
        return cleaned, ""
    candidate = match.group("amount").strip()
    parsed = parse_budget_number(candidate, field_context="amount")
    if not parsed.is_valid:
        return cleaned, ""
    description = cleaned[: match.start("amount")].strip(" -:;\t")
    if not description or not re.search(r"[A-Za-z]", description):
        return cleaned, ""
    return description, parsed.normalized


def _header_match_score(header: str, alias: str) -> int:
    if not header or not alias:
        return 0
    if header == alias:
        return 4
    header_tokens = set(header.split())
    alias_tokens = set(alias.split())
    if alias_tokens and alias_tokens.issubset(header_tokens):
        return 3
    if alias in header:
        return 2
    return 0


def _field_for_header(value: object) -> tuple[str, int]:
    header = normalize_label(value)
    tokens = set(header.split())
    if "capitulo" in tokens and ("codigo" in tokens or "cod" in tokens):
        return "chapter_code", 4
    if any(token in header.split() for token in ("descripcion", "concepto", "texto", "detalle")):
        return "item_description", 4
    if any(token in tokens for token in ("codigo", "cod", "ref", "referencia")):
        return "item_code", 4
    best_field = ""
    best_score = 0
    for field, aliases in HEADER_ALIASES.items():
        for alias in aliases:
            score = _header_match_score(header, alias)
            if score > best_score:
                best_field = field
                best_score = score
    return best_field, best_score


def _row_values(ws: object, row_idx: int, max_col: int) -> list[object]:
    return [ws.cell(row=row_idx, column=col_idx).value for col_idx in range(1, max_col + 1)]


def detect_header_row_and_mapping(ws: object, max_scan_rows: int = 25) -> HeaderDetection:
    scan_to = min(getattr(ws, "max_row", 1), max_scan_rows)
    max_col = min(getattr(ws, "max_column", 1), 50)
    best_row = 1
    best_map: dict[str, int] = {}
    best_score = 0

    for row_idx in range(1, scan_to + 1):
        row_map: dict[str, int] = {}
        score = 0
        for col_idx in range(1, max_col + 1):
            field, match_score = _field_for_header(ws.cell(row=row_idx, column=col_idx).value)
            if not field or field in row_map:
                continue
            row_map[field] = col_idx
            score += match_score
        if "amount" in row_map and ("item_description" in row_map or "chapter_name" in row_map):
            score += 3
        if "item_code" in row_map and ("item_description" in row_map or "chapter_name" in row_map):
            score += 1
        if score > best_score:
            best_row = row_idx
            best_map = row_map
            best_score = score

    if best_score >= 7 and ("amount" in best_map or "item_description" in best_map):
        confidence = HEADER_HIGH
        notes: tuple[str, ...] = ()
    elif best_score >= 4:
        confidence = HEADER_LOW
        notes = ("ECONOMIC_HEADER_LOW_CONFIDENCE",)
    else:
        confidence = HEADER_NONE
        best_map = {}
        notes = ("NO_HEADER_DETECTION",)

    completed_map = _infer_missing_mapping_from_content(ws, best_row, dict(best_map), confidence)
    if completed_map != best_map and confidence == HEADER_NONE:
        notes = ("ECONOMIC_HEADER_LOW_CONFIDENCE",)
        confidence = HEADER_LOW
    elif completed_map != best_map and "ECONOMIC_HEADER_LOW_CONFIDENCE" not in notes:
        notes = notes + ("ECONOMIC_HEADER_LOW_CONFIDENCE",)

    return HeaderDetection(
        header_row=best_row,
        mapping=completed_map,
        confidence=confidence,
        score=best_score,
        notes=notes,
    )


def _infer_missing_mapping_from_content(
    ws: object,
    header_row: int,
    mapping: dict[str, int],
    confidence: str,
) -> dict[str, int]:
    max_col = min(getattr(ws, "max_column", 1), 50)
    max_row = getattr(ws, "max_row", 1)
    sample_start = header_row + 1 if confidence != HEADER_NONE else 1
    sample_end = min(max_row, sample_start + 40)
    stats: dict[int, dict[str, int]] = {
        col_idx: {"text": 0, "long_text": 0, "number": 0, "unit": 0, "code": 0, "nonempty": 0}
        for col_idx in range(1, max_col + 1)
    }

    for row_idx in range(sample_start, sample_end + 1):
        for col_idx, value in enumerate(_row_values(ws, row_idx, max_col), start=1):
            text = _safe_text(value)
            if not text:
                continue
            stats[col_idx]["nonempty"] += 1
            normalized = normalize_label(text)
            parsed = parse_budget_number(value, field_context="amount")
            if parsed.is_valid:
                stats[col_idx]["number"] += 1
            if normalized in UNIT_VALUES:
                stats[col_idx]["unit"] += 1
            if re.fullmatch(r"\d+(?:[.]\d+)*", text) or re.fullmatch(r"[A-Za-z]?\d+(?:[.-]\d+)*", text):
                stats[col_idx]["code"] += 1
            if re.search(r"[A-Za-z]", text):
                stats[col_idx]["text"] += 1
                if len(text) >= 8:
                    stats[col_idx]["long_text"] += 1

    used = set(mapping.values())
    if "amount" not in mapping:
        numeric_candidates = [
            (col_idx, data["number"], data["nonempty"])
            for col_idx, data in stats.items()
            if data["number"] >= 3 and data["number"] >= max(1, data["nonempty"] // 2)
        ]
        if numeric_candidates:
            numeric_candidates.sort(key=lambda item: (item[1], item[0]), reverse=True)
            mapping["amount"] = numeric_candidates[0][0]
            used.add(numeric_candidates[0][0])

    if "unit" not in mapping:
        unit_candidates = [
            (col_idx, data["unit"], data["nonempty"])
            for col_idx, data in stats.items()
            if col_idx not in used and data["unit"] >= 2
        ]
        if unit_candidates:
            unit_candidates.sort(key=lambda item: (item[1], -item[0]), reverse=True)
            mapping["unit"] = unit_candidates[0][0]
            used.add(unit_candidates[0][0])

    if "item_description" not in mapping:
        if "chapter_name" in mapping:
            mapping["item_description"] = mapping["chapter_name"]
        else:
            text_candidates = [
                (col_idx, data["long_text"], data["text"], data["nonempty"])
                for col_idx, data in stats.items()
                if col_idx not in used and data["text"] > data["number"] and data["long_text"] >= 2
            ]
            if text_candidates:
                text_candidates.sort(key=lambda item: (item[1], item[2], -item[0]), reverse=True)
                mapping["item_description"] = text_candidates[0][0]
                used.add(text_candidates[0][0])

    if "item_code" not in mapping:
        code_candidates = [
            (col_idx, data["code"], data["nonempty"])
            for col_idx, data in stats.items()
            if col_idx not in used and data["code"] >= 2 and data["code"] >= data["nonempty"] // 2
        ]
        if code_candidates:
            code_candidates.sort(key=lambda item: (item[1], -item[0]), reverse=True)
            mapping["item_code"] = code_candidates[0][0]
            used.add(code_candidates[0][0])

    numeric_unused = [
        (col_idx, data["number"], data["nonempty"])
        for col_idx, data in stats.items()
        if col_idx not in used and data["number"] >= 3
    ]
    numeric_unused.sort(key=lambda item: (item[1], item[0]), reverse=True)
    if "quantity" not in mapping and numeric_unused:
        mapping["quantity"] = numeric_unused[0][0]
        used.add(numeric_unused[0][0])
        numeric_unused = [item for item in numeric_unused if item[0] not in used]
    if "unit_price" not in mapping and numeric_unused:
        mapping["unit_price"] = numeric_unused[0][0]

    return mapping


def _get_mapped_value(values: list[object], mapping: dict[str, int], field: str) -> object:
    col_idx = mapping.get(field)
    if not col_idx or col_idx < 1 or col_idx > len(values):
        return None
    return values[col_idx - 1]


def _row_has_header_shape(values: list[object]) -> bool:
    hits = 0
    nonempty = 0
    for value in values:
        if _is_empty(value):
            continue
        nonempty += 1
        field, score = _field_for_header(value)
        if field and score >= 4:
            hits += 1
    return hits >= 2


def _row_contains_any(values: list[object], words: set[str]) -> bool:
    text = " ".join(normalize_label(value) for value in values if not _is_empty(value))
    return any(word in text for word in words)


def classify_budget_row(
    values: list[object],
    mapping: dict[str, int],
    row_idx: int,
    header_row: int,
) -> str:
    if all(_is_empty(value) for value in values):
        return ROW_EMPTY
    if _row_contains_any(values, SUBTOTAL_WORDS):
        return ROW_SUBTOTAL
    if _row_contains_any(values, TOTAL_WORDS):
        return ROW_TOTAL
    if row_idx == header_row or _row_has_header_shape(values):
        return ROW_HEADER

    description = _safe_text(_get_mapped_value(values, mapping, "item_description"))
    chapter = _safe_text(_get_mapped_value(values, mapping, "chapter_name"))
    item_code = _safe_text(_get_mapped_value(values, mapping, "item_code"))
    unit = _safe_text(_get_mapped_value(values, mapping, "unit"))
    amount = parse_budget_number(_get_mapped_value(values, mapping, "amount"), field_context="amount")
    quantity = parse_budget_number(_get_mapped_value(values, mapping, "quantity"), field_context="quantity")
    unit_price = parse_budget_number(_get_mapped_value(values, mapping, "unit_price"), field_context="unit_price")
    has_description = bool(description or chapter)

    if has_description and (amount.is_valid or quantity.is_valid or unit_price.is_valid or unit):
        return ROW_COST_ITEM
    if has_description and item_code and not amount.is_valid:
        return ROW_CHAPTER
    if has_description and not amount.is_valid:
        return ROW_CHAPTER
    if amount.is_valid and not has_description:
        if not any(re.search(r"[A-Za-z]", _safe_text(value)) for value in values):
            return ROW_NON_BUDGET
        return ROW_AMBIGUOUS
    if any(not _is_empty(value) for value in values):
        if not amount.is_valid and not quantity.is_valid and not unit_price.is_valid and not unit:
            return ROW_NON_BUDGET
        return ROW_UNKNOWN
    return ROW_EMPTY


def mapping_status_for_row_class(row_class: str) -> str:
    if row_class == ROW_COST_ITEM:
        return MAPPING_MAPPED
    if row_class in {ROW_HEADER, ROW_EMPTY, ROW_TOTAL, ROW_SUBTOTAL, ROW_CHAPTER, ROW_SUBCHAPTER, ROW_NON_BUDGET}:
        return MAPPING_NOT_COST_ITEM
    if row_class == ROW_AMBIGUOUS:
        return MAPPING_AMBIGUOUS
    if row_class == ROW_MANUAL_REVIEW:
        return MAPPING_MANUAL_REVIEW
    return MAPPING_UNMAPPED


def extract_budget_rows_from_worksheet(ws: object, source_file_id: str = "") -> list[BudgetRowExtraction]:
    detection = detect_header_row_and_mapping(ws)
    max_col = min(getattr(ws, "max_column", 1), 50)
    start_row = detection.header_row + 1 if detection.confidence != HEADER_NONE else 1
    rows: list[BudgetRowExtraction] = []

    for row_idx in range(start_row, getattr(ws, "max_row", 0) + 1):
        values = _row_values(ws, row_idx, max_col)
        row_class = classify_budget_row(values, detection.mapping, row_idx, detection.header_row)
        if row_class in {ROW_EMPTY, ROW_HEADER, ROW_NON_BUDGET, ROW_UNKNOWN}:
            continue

        notes = list(detection.notes)
        if row_class != ROW_COST_ITEM:
            notes.append(f"ROW_CLASS_{row_class}")

        chapter_code = _safe_text(_get_mapped_value(values, detection.mapping, "chapter_code"))
        chapter_name = _safe_text(_get_mapped_value(values, detection.mapping, "chapter_name"))
        item_code = _safe_text(_get_mapped_value(values, detection.mapping, "item_code"))
        item_description = _safe_text(_get_mapped_value(values, detection.mapping, "item_description"))
        if not item_description and chapter_name:
            item_description = chapter_name
        if not item_description:
            text_candidates = [
                _safe_text(value)
                for value in values
                if _safe_text(value)
                and re.search(r"[A-Za-z]", _safe_text(value))
                and not parse_budget_number(value, field_context="amount").is_valid
            ]
            if text_candidates:
                item_description = max(text_candidates, key=len)
            else:
                item_description = next((_safe_text(value) for value in values if _safe_text(value)), "")
                if item_description and contains_budget_number(item_description):
                    notes.append("DESCRIPTION_AMOUNT_SPLIT_FAILED")

        unit = _safe_text(_get_mapped_value(values, detection.mapping, "unit"))
        quantity_parse = parse_budget_number(_get_mapped_value(values, detection.mapping, "quantity"), "quantity")
        unit_price_parse = parse_budget_number(_get_mapped_value(values, detection.mapping, "unit_price"), "unit_price")
        amount_parse = parse_budget_number(_get_mapped_value(values, detection.mapping, "amount"), "amount")

        if not amount_parse.is_valid and item_description:
            split_description, split_amount = _split_trailing_amount_from_description(item_description)
            if split_amount:
                item_description = split_description
                amount_parse = ParsedNumber(split_amount, NUMERIC_LOW)
                notes.append("AMOUNT_EXTRACTED_FROM_DESCRIPTION_LOW_CONFIDENCE")

        if not amount_parse.is_valid:
            notes.append("AMOUNT_NOT_DETECTED")
        elif amount_parse.confidence == NUMERIC_LOW:
            notes.append("NUMERIC_PARSE_AMBIGUOUS")
        if not quantity_parse.is_valid:
            notes.append("QUANTITY_NOT_DETECTED")
        if not unit_price_parse.is_valid:
            notes.append("UNIT_PRICE_NOT_DETECTED")
        if contains_budget_number(item_description) and amount_parse.is_valid:
            notes.append("DESCRIPTION_AMOUNT_SPLIT_FAILED")
            row_class = ROW_AMBIGUOUS

        mapping_status = mapping_status_for_row_class(row_class)
        validation_status = "MANUAL_REVIEW_REQUIRED" if mapping_status in {MAPPING_AMBIGUOUS, MAPPING_MANUAL_REVIEW} else "PENDING"
        rows.append(
            BudgetRowExtraction(
                source_sheet_name=str(getattr(ws, "title", "")),
                source_row_number=row_idx,
                chapter_code=chapter_code,
                chapter_name=chapter_name,
                item_code=item_code,
                item_description=item_description,
                unit=unit,
                quantity=quantity_parse.normalized,
                unit_price=unit_price_parse.normalized,
                amount=amount_parse.normalized,
                validation_status=validation_status,
                notes="|".join(dict.fromkeys(notes)),
                row_class=row_class,
                mapping_status=mapping_status,
            )
        )
    return rows


def classify_rows_in_worksheet(ws: object) -> dict[int, str]:
    detection = detect_header_row_and_mapping(ws)
    max_col = min(getattr(ws, "max_column", 1), 50)
    classes: dict[int, str] = {}
    for row_idx in range(1, getattr(ws, "max_row", 0) + 1):
        values = _row_values(ws, row_idx, max_col)
        classes[row_idx] = classify_budget_row(values, detection.mapping, row_idx, detection.header_row)
    return classes
