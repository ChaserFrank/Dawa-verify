"""
Deterministic verification rules.

Per the proposal (section 9) and ADR 0004: the AI model only extracts
data. Every decision about dates, missing fields and category assignment
happens here, in plain testable Python, never inside the extraction step.
"""
from __future__ import annotations

import calendar
import dataclasses
import datetime
import re
from typing import List, Optional

from .extraction import ExtractionResult
from .models import Batch, Product, VerificationRequest

REQUIRED_FIELDS = ["product_name", "strength", "manufacturer", "batch_number", "expiry_raw_text"]

_MONTH_YEAR_RE = re.compile(r"^\s*(\d{1,2})\s*/\s*(\d{4})\s*$")
_DAY_MONTH_YEAR_RE = re.compile(r"^\s*(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})\s*$")
_MONTH_NAMES = {m.lower(): i for i, m in enumerate(calendar.month_name) if m}
_MONTH_ABBR = {m.lower(): i for i, m in enumerate(calendar.month_abbr) if m}


class UnparseableExpiry(Exception):
    """Raised when expiry_raw_text cannot be parsed into a date at all."""


def parse_expiry(raw_text: str) -> tuple[str, datetime.date]:
    """Parse a printed expiry string into (precision, expiry_date), per ADR 0003.

    Supports:
      - "MM/YYYY"                    -> month precision
      - "DD/MM/YYYY"                 -> day precision
      - "Month YYYY" / "Mon YYYY"    -> month precision (e.g. "August 2027", "Aug 2027")

    Raises UnparseableExpiry for anything else, so an ambiguous date never
    silently becomes a guessed date -- it becomes "Could not verify".
    """
    text = raw_text.strip()

    match = _DAY_MONTH_YEAR_RE.match(text)
    if match:
        day, month, year = (int(g) for g in match.groups())
        try:
            return Batch.compute_expiry_date(year, month, day)
        except (ValueError, calendar.IllegalMonthError) as exc:
            raise UnparseableExpiry(f"Invalid calendar date in {raw_text!r}") from exc

    match = _MONTH_YEAR_RE.match(text)
    if match:
        month, year = int(match.group(1)), int(match.group(2))
        if not 1 <= month <= 12:
            raise UnparseableExpiry(f"Invalid month in {raw_text!r}")
        return Batch.compute_expiry_date(year, month)

    words = text.replace(",", " ").split()
    if len(words) == 2:
        month_word, year_word = words[0].lower(), words[1]
        month = _MONTH_NAMES.get(month_word) or _MONTH_ABBR.get(month_word.rstrip("."))
        if month and year_word.isdigit() and len(year_word) == 4:
            return Batch.compute_expiry_date(int(year_word), month)

    raise UnparseableExpiry(f"Could not parse expiry text {raw_text!r}")


def is_expired(expiry_date: datetime.date, as_of: Optional[datetime.date] = None) -> bool:
    as_of = as_of or datetime.date.today()
    return expiry_date < as_of


def expires_within(expiry_date: datetime.date, days: int, as_of: Optional[datetime.date] = None) -> bool:
    as_of = as_of or datetime.date.today()
    return as_of <= expiry_date <= as_of + datetime.timedelta(days=days)


@dataclasses.dataclass
class VerificationOutcome:
    category: str
    evidence: List[str]
    matched_product: Optional[Product] = None
    parsed_expiry_date: Optional[datetime.date] = None
    expiry_precision: Optional[str] = None


def evaluate(extraction: ExtractionResult, as_of: Optional[datetime.date] = None) -> VerificationOutcome:
    """Apply deterministic rules to one extraction and return a category
    with the evidence behind it. Never returns "verified" on the strength
    of the AI reading alone -- catalogue/expiry checks decide that.
    """
    evidence: List[str] = []

    data = extraction.as_dict()
    missing = [f for f in REQUIRED_FIELDS if not data.get(f)]
    if missing:
        evidence.append(
            "Missing from the photographed package: " + ", ".join(sorted(missing)) + "."
        )
        return VerificationOutcome(category=VerificationRequest.CATEGORY_UNVERIFIABLE, evidence=evidence)

    try:
        precision, expiry_date = parse_expiry(extraction.expiry_raw_text)
    except UnparseableExpiry as exc:
        evidence.append(f"Expiry date could not be read reliably: {exc}")
        return VerificationOutcome(category=VerificationRequest.CATEGORY_UNVERIFIABLE, evidence=evidence)

    as_of = as_of or datetime.date.today()

    if is_expired(expiry_date, as_of):
        evidence.append(f"This batch expired on {expiry_date.isoformat()}.")
        return VerificationOutcome(
            category=VerificationRequest.CATEGORY_EXPIRY_WARNING,
            evidence=evidence,
            parsed_expiry_date=expiry_date,
            expiry_precision=precision,
        )

    matched_product = (
        Product.objects.filter(
            name__iexact=extraction.product_name,
            manufacturer__iexact=extraction.manufacturer,
            strength__iexact=extraction.strength,
        ).first()
    )

    if matched_product is None:
        evidence.append(
            f"No matching entry for \"{extraction.product_name} {extraction.strength}\" "
            f"by {extraction.manufacturer} in the reference catalogue."
        )
        return VerificationOutcome(
            category=VerificationRequest.CATEGORY_UNVERIFIABLE,
            evidence=evidence,
            parsed_expiry_date=expiry_date,
            expiry_precision=precision,
        )

    evidence.append(
        f"Matches reference catalogue entry for \"{matched_product}\"."
    )
    evidence.append(f"Not expired (expires {expiry_date.isoformat()}).")

    if expires_within(expiry_date, days=60, as_of=as_of):
        evidence.append("Expires within 60 days -- consider prioritising this stock.")

    return VerificationOutcome(
        category=VerificationRequest.CATEGORY_VERIFIED,
        evidence=evidence,
        matched_product=matched_product,
        parsed_expiry_date=expiry_date,
        expiry_precision=precision,
    )
