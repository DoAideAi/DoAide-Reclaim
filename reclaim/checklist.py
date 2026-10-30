"""The message a family receives: what to search, where, with which details, and how to reply."""
from __future__ import annotations

from typing import List

from . import portals
from .cases import CaseError


def searches(case: dict) -> List[tuple]:
    """(member, portal) pairs this family's scan covers, in a stable order."""
    pairs = []
    for who in case["members"]:
        for portal in portals.PORTALS:
            if portal["id"] not in who["skip"]:
                pairs.append((who, portal))
    return pairs


def render(case: dict) -> str:
    if not case["members"]:
        raise CaseError(f"add relatives first: reclaim member {case['id']} --relation father ...")
    pairs = searches(case)
    lines = [
        f"DoAide Reclaim · family scan {case['id']}",
        "Search each line below on the official site. Type PAN, dates of birth and account numbers",
        "only on those sites, never in this chat.",
        "",
        "When you are done, reply with one line per search:",
        "  m1 udgam found",
        "  m1 iepf found 1.2 lakh      (add the amount when the site shows one)",
        "  m1 lic no",
        "  m2 mitra blocked otp        (stuck? say otp, missing, name, down or hard)",
        "UDGAM and MITRA never show an amount: 'found' is enough.",
        "",
    ]
    used = []
    for _, portal in pairs:
        if portal not in used:
            used.append(portal)
    logins = [p for p in used if p["login"]]
    if logins:
        lines.append("Before you start")
        lines.extend(f"  {p['name']}: {p['login']}" for p in logins)
        lines.append("")
    for who in case["members"]:
        label = who["relation"] + (" (late)" if who["deceased"] else "")
        known = ", ".join(portals.FACTS[f] for f in who["knows"]) or "nothing noted yet"
        lines.append(f"{who['id']} · {label}. You have: {known}")
        mine = [p for w, p in pairs if w is who]
        if not mine:
            lines.append("  nothing to search")
        for portal in mine:
            lines.append(f"  [{who['id']} {portal['id']}] {portal['asset']} · {portal['name']}")
            lines.append(f"      {portal['url']}")
            if portals.is_ready(portal, who["knows"]):
                lines.append(f"      Enter {portal['needs_text']}.")
            else:
                lines.append(
                    f"      NOT READY: needs {portal['needs_text']}. Ask relatives, or look in old "
                    "passbooks, policies and certificates."
                )
        lines.append("")
    lines.append(f"The government links all of these at {portals.HUB_URL}")
    return "\n".join(lines) + "\n"
