from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd
import pdfplumber

from utils import normalize_text, parse_number

CANONICAL_FS_MAP = {
    "revenue": ["revenue", "professional fees", "fees", "honoraires", "produits"],
    "supplies": ["supplies", "dental supplies", "fournitures"],
    "rent": ["rent", "lease", "loyer"],
    "wages": ["wages", "salaries", "payroll", "salaires", "traitements"],
    "utilities": ["utilities", "hydro", "electricity", "services publics"],
    "other_expenses": ["other expenses", "general and admin", "autres charges"],
}


@dataclass
class FSExtractionResult:
    income_statement: pd.DataFrame
    metadata: dict


def _parse_text_lines(text: str) -> list[dict]:
    rows: list[dict] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        nums = re.findall(r"\(?\$?[-+]?\d[\d,]*(?:\.\d+)?\)?", line)
        if len(nums) < 1:
            continue

        label = re.sub(r"\(?\$?[-+]?\d[\d,]*(?:\.\d+)?\)?", "", line).strip(" -:\t")
        if not label:
            continue

        amounts = [parse_number(n) for n in nums]
        amounts = [a for a in amounts if a is not None]
        if not amounts:
            continue

        row = {
            "line_item": label,
            "amount_year_1": amounts[-2] if len(amounts) >= 2 else amounts[-1],
            "amount_year_2": amounts[-1],
        }
        rows.append(row)
    return rows


def _canonicalize(line_item: str) -> str | None:
    norm = normalize_text(line_item)
    for canonical, aliases in CANONICAL_FS_MAP.items():
        if any(alias in norm for alias in aliases):
            return canonical
    return None


def extract_financial_statement(fs_pdf_path: str) -> FSExtractionResult:
    all_rows = []
    with pdfplumber.open(fs_pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            all_rows.extend(_parse_text_lines(text))

    df = pd.DataFrame(all_rows)
    if df.empty:
        return FSExtractionResult(
            income_statement=pd.DataFrame(
                columns=["line_item", "canonical_line_item", "amount_year_1", "amount_year_2"]
            ),
            metadata={"pages": 0, "status": "no_rows_detected"},
        )

    df["canonical_line_item"] = df["line_item"].map(_canonicalize)
    # Keep last occurrence of each canonical item where available.
    canon = df.dropna(subset=["canonical_line_item"]).drop_duplicates(
        subset=["canonical_line_item"], keep="last"
    )

    return FSExtractionResult(
        income_statement=canon[["line_item", "canonical_line_item", "amount_year_1", "amount_year_2"]],
        metadata={"pages": len(all_rows), "status": "ok"},
    )
