from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class AuditRow:
    timestamp: str
    deal_id: str
    sheet: str
    cell: str
    value_written: Any
    source_file: str
    extraction_method: str
    confidence: float
    status: str
    notes: str = ""


def normalize_text(value: str) -> str:
    """Normalize strings for robust EN/FR matching."""
    if value is None:
        return ""
    value = value.lower().strip()
    value = unicodedata.normalize("NFD", value)
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def parse_number(text: str) -> float | None:
    if text is None:
        return None
    cleaned = text.strip().replace(",", "")
    if not cleaned:
        return None

    negative = False
    if cleaned.startswith("(") and cleaned.endswith(")"):
        negative = True
        cleaned = cleaned[1:-1]
    cleaned = cleaned.replace("$", "").replace(" ", "")

    match = re.search(r"[-+]?\d+(?:\.\d+)?", cleaned)
    if not match:
        return None
    num = float(match.group(0))
    return -num if negative else num
