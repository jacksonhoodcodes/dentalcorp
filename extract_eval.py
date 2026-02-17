from __future__ import annotations

import re
from dataclasses import dataclass

import pandas as pd
import pdfplumber

from utils import normalize_text, parse_number

MONTH_ALIASES = {
    "jan": 1,
    "january": 1,
    "janvier": 1,
    "feb": 2,
    "february": 2,
    "fevrier": 2,
    "mars": 3,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "avr": 4,
    "may": 5,
    "mai": 5,
    "jun": 6,
    "june": 6,
    "juin": 6,
    "jul": 7,
    "july": 7,
    "juillet": 7,
    "aug": 8,
    "aout": 8,
    "september": 9,
    "sep": 9,
    "sept": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
    "decembre": 12,
}

PROVIDER_SYNONYMS = {
    "principal": ["principal", "owner", "proprietaire"],
    "associate": ["associate", "associe"],
    "hygienist": ["hygienist", "hygieniste"],
}

ROLE_SYNONYMS = {
    "assistant": ["assistant", "dental assistant", "adjointe"],
    "hygienist": ["hygienist", "hygieniste"],
    "reception": ["reception", "admin", "receptionniste"],
    "associate": ["associate", "dentist", "dentiste", "associe"],
}


@dataclass
class EvalExtractionResult:
    production: pd.DataFrame
    provider_split: pd.DataFrame
    payroll: pd.DataFrame
    metadata: dict


def _month_from_line(line: str) -> int | None:
    norm = normalize_text(line)
    for k, v in MONTH_ALIASES.items():
        if re.search(rf"\b{k}\b", norm):
            return v
    return None


def _extract_provider(line: str) -> tuple[str | None, float | None]:
    norm = normalize_text(line)
    pct_match = re.search(r"(\d+(?:\.\d+)?)\s*%", line)
    pct = float(pct_match.group(1)) if pct_match else None
    provider = None
    for k, aliases in PROVIDER_SYNONYMS.items():
        if any(a in norm for a in aliases):
            provider = k
            break
    return provider, pct


def _extract_role_wage_days(line: str) -> tuple[str | None, float | None, float | None]:
    norm = normalize_text(line)
    role = None
    for k, aliases in ROLE_SYNONYMS.items():
        if any(a in norm for a in aliases):
            role = k
            break

    wage = None
    days = None
    wage_match = re.search(r"\$?\s*(\d+(?:\.\d+)?)\s*(?:/h|per hour|hourly|h)\b", normalize_text(line))
    if wage_match:
        wage = float(wage_match.group(1))
    day_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:days?/week|j(?:ours?)?/semaine)", normalize_text(line))
    if day_match:
        days = float(day_match.group(1))
    return role, wage, days


def extract_evaluation(eval_pdf_path: str) -> EvalExtractionResult:
    production_rows = []
    provider_rows = []
    payroll_rows = []

    with pdfplumber.open(eval_pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in text.splitlines():
                month = _month_from_line(line)
                if month is not None:
                    nums = re.findall(r"\(?\$?[-+]?\d[\d,]*(?:\.\d+)?\)?", line)
                    if nums:
                        amount = parse_number(nums[-1])
                        if amount is not None:
                            production_rows.append({"month": month, "gross_revenue": amount})

                provider, pct = _extract_provider(line)
                if provider and pct is not None:
                    provider_rows.append({"provider_type": provider, "percent": pct})

                role, wage, days = _extract_role_wage_days(line)
                if role and (wage is not None or days is not None):
                    inferred_hours = days * 8 if days is not None else None
                    payroll_rows.append(
                        {
                            "role": role,
                            "hourly_rate": wage,
                            "days_per_week": days,
                            "inferred_hours_per_week": inferred_hours,
                        }
                    )

    prod_df = pd.DataFrame(production_rows).drop_duplicates(subset=["month"], keep="last")
    prov_df = pd.DataFrame(provider_rows).drop_duplicates(subset=["provider_type"], keep="last")
    payroll_df = pd.DataFrame(payroll_rows).drop_duplicates(subset=["role"], keep="last")

    return EvalExtractionResult(
        production=prod_df,
        provider_split=prov_df,
        payroll=payroll_df,
        metadata={
            "production_rows": len(prod_df),
            "provider_rows": len(prov_df),
            "payroll_rows": len(payroll_df),
            "status": "ok",
        },
    )
