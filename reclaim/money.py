"""Rupee amounts the way Indian families read them: ₹3,20,000 and ₹3.2 lakh."""
from __future__ import annotations

import math
import re

_UNITS = {
    None: 1,
    "k": 1_000,
    "thousand": 1_000,
    "l": 100_000,
    "lac": 100_000,
    "lacs": 100_000,
    "lakh": 100_000,
    "lakhs": 100_000,
    "cr": 10_000_000,
    "crore": 10_000_000,
    "crores": 10_000_000,
}
_AMOUNT = re.compile(r"(\d+(?:\.\d+)?)\s*([a-z]+)?")


def format_inr(amount: int) -> str:
    """Indian digit grouping: 320000 -> '₹3,20,000', 12345678 -> '₹1,23,45,678'."""
    digits = str(int(amount))
    if len(digits) <= 3:
        return "₹" + digits
    head, tail = digits[:-3], digits[-3:]
    groups = []
    while len(head) > 2:
        groups.insert(0, head[-2:])
        head = head[:-2]
    if head:
        groups.insert(0, head)
    return "₹" + ",".join(groups + [tail])


def inr_words(amount: int) -> str:
    """Headline form, never rounded up: 320000 -> '₹3.2 lakh', 12500000 -> '₹1.25 crore'."""
    if amount >= 10_000_000:
        unit, size = "crore", 10_000_000
    elif amount >= 100_000:
        unit, size = "lakh", 100_000
    else:
        return format_inr(amount)
    value = math.floor(amount * 100 / size) / 100
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return f"₹{text} {unit}"


def parse_amount(text: str) -> int:
    """'42000', '42,000', '1,20,000', '42k', '3.2 lakh', '3.2L', '₹1.5 cr' -> whole rupees."""
    cleaned = re.sub(r"^(₹|rs\.?|inr)\s*", "", text.strip().lower()).replace(",", "").strip()
    match = _AMOUNT.fullmatch(cleaned)
    if not match or match.group(2) not in _UNITS:
        raise ValueError(f"not an amount: {text!r} (try 42000, 1,20,000, 3.2 lakh or 1.5 crore)")
    rupees = round(float(match.group(1)) * _UNITS[match.group(2)])
    if rupees <= 0:
        raise ValueError(f"amount must be above zero: {text!r}")
    return int(rupees)
