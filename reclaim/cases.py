"""Case files: one JSON file per participant family under <data>/cases/.

A case is pseudonymous: relation labels ("father"), which facts the family has (never the values),
and what each portal search showed. Keep the case-id -> person mapping outside this tool, and erase
a case with `reclaim delete` when the family asks or the test ends.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from . import portals
from .money import parse_amount
from .privacy import check_text

SCHEMA = 1
CONSENT_SCRIPT = "v1"  # the text lives in docs/HIT_RATE_TEST.md
RELATIONS = (
    "self", "spouse", "father", "mother", "grandfather", "grandmother", "father-in-law",
    "mother-in-law", "uncle", "aunt", "sibling", "other",
)
STATUSES = ("found", "not_found", "blocked")
BLOCK_REASONS = ("otp", "missing_info", "name_mismatch", "site_down", "too_hard", "other")
_CASE_ID = re.compile(r"^R\d{3,}$")
_REPLY_STATUS = {
    "found": "found", "yes": "found", "hit": "found",
    "no": "not_found", "none": "not_found", "nil": "not_found", "notfound": "not_found",
    "not_found": "not_found",
    "blocked": "blocked", "stuck": "blocked",
}
_REPLY_REASONS = {
    "otp": "otp", "missing": "missing_info", "missing_info": "missing_info", "name": "name_mismatch",
    "name_mismatch": "name_mismatch", "down": "site_down", "site_down": "site_down",
    "hard": "too_hard", "too_hard": "too_hard",
}


class CaseError(ValueError):
    pass


def now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


class Store:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.dir = self.root / "cases"

    def path(self, case_id: str) -> Path:
        if not _CASE_ID.match(case_id or ""):
            raise CaseError(f"not a case id: {case_id!r} (they look like R001)")
        return self.dir / f"{case_id}.json"

    def ids(self) -> List[str]:
        if not self.dir.is_dir():
            return []
        found = [p.stem for p in self.dir.glob("R*.json") if _CASE_ID.match(p.stem)]
        return sorted(found, key=lambda cid: int(cid[1:]))

    def load(self, case_id: str) -> dict:
        path = self.path(case_id)
        if not path.exists():
            raise CaseError(f"no case {case_id} in {self.dir}")
        return json.loads(path.read_text(encoding="utf-8"))

    def all(self) -> List[dict]:
        return [self.load(cid) for cid in self.ids()]

    def save(self, case: dict) -> Path:
        path = self.path(case["id"])
        self.dir.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self.dir, prefix=".tmp-", suffix=".json")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(case, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
            os.chmod(tmp, 0o600)
            os.replace(tmp, path)
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise
        return path

    def create(self, consent: bool, channel: str = "") -> dict:
        if not consent:
            raise CaseError(
                "read the consent script in docs/HIT_RATE_TEST.md to the family first, then pass --consent"
            )
        existing = self.ids()
        number = int(existing[-1][1:]) + 1 if existing else 1
        case = {
            "schema": SCHEMA,
            "id": f"R{number:03d}",
            "created": now(),
            "consent": {"script": CONSENT_SCRIPT, "at": now()},
            "channel": check_text("channel", channel, limit=40),
            "members": [],
            "results": [],
            "done": None,
            "card": None,
        }
        self.save(case)
        return case

    def delete(self, case_id: str) -> None:
        path = self.path(case_id)
        if not path.exists():
            raise CaseError(f"no case {case_id} in {self.dir}")
        path.unlink()


def member(case: dict, member_id: str) -> dict:
    for item in case["members"]:
        if item["id"] == member_id:
            return item
    known = ", ".join(m["id"] for m in case["members"]) or "none yet"
    raise CaseError(f"{case['id']} has no member {member_id!r} (members: {known})")


def add_member(case: dict, relation: str, deceased: bool = False, knows=(), skip=()) -> dict:
    relation = relation.strip().lower()
    if relation not in RELATIONS:
        raise CaseError(f"relation must be one of {', '.join(RELATIONS)}")
    skip_ids = []
    for portal_id in skip:
        portal_id = portal_id.strip().lower()
        if portal_id:
            portals.get(portal_id)
            if portal_id not in skip_ids:
                skip_ids.append(portal_id)
    entry = {
        "id": f"m{len(case['members']) + 1}",
        "relation": relation,
        "deceased": bool(deceased),
        "knows": portals.normalise_facts(knows),
        "skip": skip_ids,
    }
    case["members"].append(entry)
    return entry


def record(
    case: dict,
    member_id: str,
    portal_id: str,
    status: str,
    amount: Optional[int] = None,
    estimate: bool = False,
    reason: Optional[str] = None,
) -> dict:
    """Store what one portal showed for one relative; a later record for the same pair replaces it."""
    who = member(case, member_id)
    portal = portals.get(portal_id)
    if portal_id in who["skip"]:
        raise CaseError(f"{member_id} skips {portal_id}; that search is not part of this family's scan")
    if status not in STATUSES:
        raise CaseError(f"status must be one of {', '.join(STATUSES)}")
    if amount is not None and status != "found":
        raise CaseError("only a 'found' result can carry an amount")
    if amount is not None and amount <= 0:
        raise CaseError("amount must be above zero")
    if estimate and amount is None:
        raise CaseError("--estimate needs an amount")
    if status == "blocked":
        if reason not in BLOCK_REASONS:
            raise CaseError(f"a blocked search needs a reason: {', '.join(BLOCK_REASONS)}")
    elif reason is not None:
        raise CaseError("a reason only applies to a blocked search")
    result = {
        "member": member_id,
        "portal": portal["id"],
        "status": status,
        "amount": amount,
        "estimate": bool(estimate),
        "reason": reason,
        "at": now(),
    }
    case["results"] = [
        r for r in case["results"] if not (r["member"] == member_id and r["portal"] == portal_id)
    ] + [result]
    return result


def mark_done(case: dict, minutes: Optional[int] = None) -> None:
    if minutes is not None and not 0 < minutes <= 600:
        raise CaseError("minutes must be between 1 and 600")
    case["done"] = {"at": now(), "minutes": minutes}


def set_shared(case: dict, shared: bool) -> None:
    if not case.get("card"):
        raise CaseError(f"{case['id']} has no card yet; run `reclaim card {case['id']}` first")
    case["card"]["shared"] = bool(shared)


def parse_reply(text: str) -> Tuple[List[dict], List[str]]:
    """Read a family's WhatsApp reply, one search per line.

        m1 udgam found            m1 iepf found 3.2 lakh     m1 iepf found ~1.5 lakh (estimate)
        m1 lic no                 m2 mitra blocked otp

    Replies from reclaim.doaide.com also list the relatives first, as `m1 is father late knows
    dob,address`. Returns (records, errors); errors name the line so nothing is guessed.
    """
    records: List[dict] = []
    errors: List[str] = []
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip().strip("*_").strip()
        if not line or line.startswith("#"):
            continue
        words = line.split()
        if len(words) >= 3 and words[1].lower() == "is":
            try:
                records.append(_parse_member_line(words))
            except CaseError as exc:
                errors.append(f"line {number}: {exc}")
            continue
        if len(words) < 3:
            errors.append(f"line {number}: expected '<member> <portal> <found|no|blocked> ...': {raw!r}")
            continue
        member_id, portal_id, word = words[0].lower(), words[1].lower(), words[2].lower()
        status = _REPLY_STATUS.get(word)
        rest = " ".join(words[3:])
        entry: Dict[str, object] = {"member": member_id, "portal": portal_id, "status": status,
                                    "amount": None, "estimate": False, "reason": None}
        if status is None:
            errors.append(f"line {number}: {word!r} is not found, no or blocked")
            continue
        if status == "found" and rest:
            estimate = rest.startswith(("~", "about ", "approx"))
            amount_text = re.sub(r"^(~|about|approx\.?|approximately)\s*", "", rest)
            try:
                entry["amount"] = parse_amount(amount_text)
            except ValueError as exc:
                errors.append(f"line {number}: {exc}")
                continue
            entry["estimate"] = estimate
        elif status == "blocked":
            entry["reason"] = _REPLY_REASONS.get(rest.split()[0].lower() if rest else "", "other")
        elif rest:
            errors.append(f"line {number}: unexpected text after {word!r}: {rest!r}")
            continue
        records.append(entry)
    return records, errors


def _parse_member_line(words: List[str]) -> dict:
    member_id = words[0].lower()
    if not re.fullmatch(r"m\d+", member_id):
        raise CaseError(f"{words[0]!r} is not a relative id like m1")
    rest = [word.lower() for word in words[2:]]
    relation = rest.pop(0)
    deceased = bool(rest) and rest[0] in ("late", "deceased")
    if deceased:
        rest.pop(0)
    knows: List[str] = []
    if rest and rest[0] == "knows":
        knows = [name for word in rest[1:] for name in word.split(",") if name]
        rest = []
    if rest:
        raise CaseError(f"unexpected {' '.join(rest)!r}; expected 'm1 is father late knows dob,address'")
    return {"type": "member", "member": member_id, "relation": relation, "deceased": deceased, "knows": knows}


def _describe(entry: dict) -> str:
    return entry["relation"] + (" (late)" if entry["deceased"] else "")


def _ensure_member(case: dict, entry: dict) -> None:
    """Add a relative listed in a reply, or confirm the one the operator already added."""
    for existing in case["members"]:
        if existing["id"] == entry["member"]:
            if (existing["relation"], existing["deceased"]) != (entry["relation"], entry["deceased"]):
                raise CaseError(f"is {_describe(existing)} in {case['id']}, but the reply says {_describe(entry)}")
            existing["knows"] = portals.normalise_facts(entry["knows"])
            return
    expected = f"m{len(case['members']) + 1}"
    if entry["member"] != expected:
        raise CaseError(f"the next relative in {case['id']} is {expected}")
    add_member(case, entry["relation"], entry["deceased"], entry["knows"])


def apply_reply(case: dict, text: str) -> List[dict]:
    """Apply every line of a reply or none of them; listed relatives are added before results."""
    records, errors = parse_reply(text)
    trial = json.loads(json.dumps(case))
    for entry in sorted(records, key=lambda item: item.get("type") != "member"):
        try:
            if entry.get("type") == "member":
                _ensure_member(trial, entry)
            else:
                record(trial, entry["member"], entry["portal"], entry["status"],
                       amount=entry["amount"], estimate=entry["estimate"], reason=entry["reason"])
        except (CaseError, ValueError) as exc:
            errors.append(f"{entry['member']} {entry.get('portal', '')}".rstrip() + f": {exc}")
    if errors:
        raise CaseError("reply not applied:\n  " + "\n  ".join(errors))
    case.clear()
    case.update(trial)
    return records
