"""
asp_utils.py — Shared utility functions.
No side effects, fully deterministic, no I/O.
"""

from __future__ import annotations

from datetime import date, datetime
import re
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
#  Date helpers
# ─────────────────────────────────────────────────────────────────────────────

_DATE_FORMATS = (
    "%d/%m/%Y", "%d-%m-%Y",
    "%d/%m/%y", "%d-%m-%y",
    "%Y-%m-%d",
)


def today_str() -> str:
    """Return today as DD/MM/YYYY."""
    return date.today().strftime("%d/%m/%Y")


def parse_date(s: str) -> str:
    """
    Normalise any common date string to DD/MM/YYYY.
    Returns input unchanged if no format matches.
    """
    s = s.strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue
    return s


def fy_start(syear: int) -> str:
    """Return financial year start date as DD/MM/YYYY."""
    return f"01/04/{syear}"


# ─────────────────────────────────────────────────────────────────────────────
#  Number helpers
# ─────────────────────────────────────────────────────────────────────────────

def to_float(value: object) -> float:
    """
    Safe conversion to float.
    Returns 0.0 for None, empty string, non-numeric input.
    """
    if value is None:
        return 0.0
    try:
        return float(str(value).replace(",", "").strip())
    except (ValueError, TypeError):
        return 0.0


def fmt_amt(value: float, decimals: int = 2) -> str:
    """Format float to fixed decimal string."""
    return f"{value:.{decimals}f}"


def normalize_gstno(gstno: str) -> str:
    """
    Normalise GST number for consistent matching/storage.
    - uppercase
    - remove non-alphanumeric chars (spaces, dashes, etc.)
    """
    return re.sub(r"[^A-Z0-9]", "", (gstno or "").upper().strip())


# ─────────────────────────────────────────────────────────────────────────────
#  Indian amount-in-words
# ─────────────────────────────────────────────────────────────────────────────

_ONES = [
    "", "one", "two", "three", "four", "five", "six", "seven",
    "eight", "nine", "ten", "eleven", "twelve", "thirteen",
    "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen",
]
_TENS = [
    "", "", "twenty", "thirty", "forty", "fifty",
    "sixty", "seventy", "eighty", "ninety",
]


def _below_hundred(n: int) -> str:
    if n == 0:
        return ""
    if n < 20:
        return _ONES[n]
    tens_word = _TENS[n // 10]
    ones_word = _ONES[n % 10]
    return tens_word + (" " + ones_word if ones_word else "")


def _below_thousand(n: int) -> str:
    if n < 100:
        return _below_hundred(n)
    h = _ONES[n // 100] + " hundred"
    rem = _below_hundred(n % 100)
    return h + (" " + rem if rem else "")


def amount_words(amount: float) -> str:
    """
    Convert a non-negative float to Indian currency words.
    Handles paise (decimal part).
    E.g. 14921.10 → 'Rupees fourteen thousand nine hundred twenty-one and paise ten only.'
    """
    if amount < 0:
        return "negative amount"
    amount = round(amount, 2)
    rupees = int(amount)
    paise  = round((amount - rupees) * 100)

    parts: list[str] = []
    n = rupees
    if n == 0:
        parts.append("zero")
    else:
        if n >= 10_000_000:
            parts.append(_below_thousand(n // 10_000_000) + " crore")
            n %= 10_000_000
        if n >= 100_000:
            parts.append(_below_thousand(n // 100_000) + " lakh")
            n %= 100_000
        if n >= 1_000:
            parts.append(_below_thousand(n // 1_000) + " thousand")
            n %= 1_000
        if n > 0:
            parts.append(_below_thousand(n))

    result = "Rupees " + " ".join(parts).strip().capitalize()
    if paise:
        result += f" and paise {_below_hundred(paise)}"
    result += " only."
    return result


# ─────────────────────────────────────────────────────────────────────────────
#  GST calculation
# ─────────────────────────────────────────────────────────────────────────────

def calc_gst(
    taxable: float,
    gst_pct: float,
    gstno: str,
) -> dict[str, float]:
    """
    Calculate GST components.
    If party GST starts with '33' (Tamil Nadu) → CGST + SGST.
    Otherwise → IGST only.
    Returns dict with keys: taxable, cgst, sgst, igst, total.
    """
    taxable = round(max(taxable, 0.0), 2)
    gst_pct = max(gst_pct, 0.0)
    gstno   = normalize_gstno(gstno)

    state_code = gstno[:2]
    intrastate = (state_code == "33") or (not gstno)

    if intrastate:
        half   = round(taxable * gst_pct / 200, 2)   # each half
        cgst   = half
        sgst   = round(taxable * gst_pct / 100 - half, 2)
        igst   = 0.0
    else:
        cgst   = 0.0
        sgst   = 0.0
        igst   = round(taxable * gst_pct / 100, 2)

    total = round(taxable + cgst + sgst + igst, 2)
    return {
        "taxable": taxable,
        "cgst":    cgst,
        "sgst":    sgst,
        "igst":    igst,
        "total":   total,
    }
