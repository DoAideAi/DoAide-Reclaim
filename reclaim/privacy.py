"""Keep identifier values out of everything Reclaim stores or prints.

Reclaim records WHICH facts a family knows ("has a PAN"), never the facts. Every free-text field
goes through check_text(), so a PAN, Aadhaar, phone or account number, email or date typed by
mistake is refused instead of saved.
"""
from __future__ import annotations

import re
from typing import List

PATTERNS = (
    ("a PAN", re.compile(r"\b[A-Za-z]{5}\d{4}[A-Za-z]\b")),
    ("an Aadhaar number", re.compile(r"(?<!\d)\d{4}[ -]?\d{4}[ -]?\d{4}(?!\d)")),
    ("a mobile number", re.compile(r"(?<!\d)(?:\+?91[ -]?)?[6-9]\d{9}(?!\d)")),
    ("an account or ID number", re.compile(r"(?<!\d)\d{9,18}(?!\d)")),
    ("an email address", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")),
    ("a date", re.compile(r"(?<!\d)\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}(?!\d)|(?<!\d)\d{4}-\d{2}-\d{2}(?!\d)")),
)


class IdentifierError(ValueError):
    pass


def find_identifiers(text: str) -> List[str]:
    return [kind for kind, pattern in PATTERNS if pattern.search(text or "")]


def check_text(field: str, text: str, limit: int = 80) -> str:
    text = (text or "").strip()
    if len(text) > limit:
        raise ValueError(f"{field} is longer than {limit} characters")
    found = find_identifiers(text)
    if found:
        raise IdentifierError(
            f"{field} looks like it contains {' and '.join(found)}. Reclaim records which details "
            "a family has, never the details: those are typed only on the official site."
        )
    return text
