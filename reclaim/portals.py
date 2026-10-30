"""The official portals a family scan covers, and what each one needs before a search can run.

Every fact below was read from the portal itself or from an official/primary source on CHECKED
(URLs in each entry's "sources"). Portals change their forms: re-check before a public launch and
bump CHECKED. iepf.gov.in refuses automated access, so its search fields are marked unverified.
"""
from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

CHECKED = "2026-10-29"

# What a family may KNOW about a relative. Reclaim stores only that a fact is known, never the
# fact itself: values are typed straight into the official site by the family.
FACTS: Dict[str, str] = {
    "pan": "PAN",
    "dob": "date of birth",
    "driving_licence": "driving licence number",
    "voter_id": "voter ID number",
    "passport": "passport number",
    "address": "an old address with city and PIN",
    "mobile": "the mobile number they used",
    "email": "the email they used",
    "bank_account": "a bank account number",
    "nominee": "a nominee's name",
    "policy_number": "an insurance policy number",
    "share_records": "old share certificates or dividend warrants",
}

ALIASES: Dict[str, str] = {
    "dl": "driving_licence",
    "licence": "driving_licence",
    "license": "driving_licence",
    "voter": "voter_id",
    "epic": "voter_id",
    "birth": "dob",
    "account": "bank_account",
    "policy": "policy_number",
    "shares": "share_records",
    "folio": "share_records",
    "certificates": "share_records",
    "phone": "mobile",
}

# needs: alternatives; a portal is ready when EVERY group of ANY one alternative has at least one
# known fact. The member's name is always assumed known. [[]] means "the name is enough".
PORTALS: Tuple[dict, ...] = (
    {
        "id": "udgam",
        "name": "RBI UDGAM",
        "asset": "Bank deposits",
        "url": "https://udgam.rbi.org.in/unclaimed-deposits/#/login",
        "login": "register once with your own name and mobile number",
        "needs": [[["pan", "dob", "driving_licence", "voter_id", "passport", "address"]]],
        "needs_text": (
            "their name as in the bank's records, the bank (or all banks), and one of PAN, "
            "date of birth, driving licence, voter ID or passport (an old address if none is known)"
        ),
        "hit_shows": "name, bank, place and a UDRN; no amount, the bank tells you that when you claim",
        "amount_on_hit": False,
        "next_step": (
            "Export the result as PDF and note the UDRN. Claim at that bank; the bank name in the "
            "result links to its claim process."
        ),
        "inputs_verified": True,
        "sources": [
            "https://rbidocs.rbi.org.in/rdocs/faqs/PDFs/FAQONUDGAMPORTAL.PDF",
            "https://economictimes.indiatimes.com/wealth/save/more-than-8-lakh-people-got-unclaimed-deposits-back-from-bank-via-udgam/articleshow/122998219.cms",
        ],
    },
    {
        "id": "iepf",
        "name": "IEPF Authority",
        "asset": "Shares & dividends",
        "url": "https://www.iepf.gov.in/",
        "login": "the new IEPF search facility asks you to register and log in",
        "needs": [[]],
        "needs_text": (
            "the investor's name; company names and folio numbers from old share certificates or "
            "dividend warrants make it much easier"
        ),
        "hit_shows": "the company and the amount and shares transferred to IEPF",
        "amount_on_hit": True,
        "next_step": (
            "Ask the company or its registrar for an entitlement letter, file Form IEPF-5 yourself on "
            "iepf.gov.in, then post the signed papers to the company's IEPF nodal officer. IEPFA "
            "warns against using middlemen."
        ),
        "inputs_verified": False,
        "sources": [
            "https://iepfa.gov.in/",
            "https://www.iepf.gov.in/content/iepf/global/master/Home/Home.html",
            "https://egazette.gov.in/WriteReadData/2025/266617.pdf",
            "https://www.tcs.com/content/dam/tcs/pdf/discover-tcs/investor-relations/faq/iepf-process-to-claim-jan-2025.pdf",
        ],
    },
    {
        "id": "lic",
        "name": "LIC unclaimed amounts",
        "asset": "Insurance",
        "url": "https://licindia.in/unclaimed-amounts-of-policyholders",
        "login": "",
        "needs": [[["dob", "pan", "policy_number"]]],
        "needs_text": "any two of name, date of birth, PAN and policy number (name and date of birth is enough)",
        "hit_shows": "unclaimed amounts under LIC policies (LIC refreshes this list every six months)",
        "amount_on_hit": None,
        "next_step": "Contact the LIC branch that serviced the policy with the policy details and KYC.",
        "inputs_verified": True,
        "sources": ["https://licindia.in/unclaimed-amounts-of-policyholders"],
    },
    {
        "id": "insurers",
        "name": "IRDAI Bima Bharosa",
        "asset": "Insurance",
        "url": "https://bimabharosa.irdai.gov.in/Home/UnclaimedAmountsQuery",
        "login": "a code sent to your mobile",
        "needs": [[["policy_number"], ["dob"], ["address"]]],
        "needs_text": (
            "policy number, the policyholder's name, date of birth and PIN, district and state; the same "
            "page links each insurer's own unclaimed search"
        ),
        "hit_shows": "the insurer answers the query",
        "amount_on_hit": None,
        "next_step": "Follow up with the insurer and keep the query reference.",
        "inputs_verified": True,
        "sources": ["https://bimabharosa.irdai.gov.in/Home/UnclaimedAmountsQuery"],
    },
    {
        "id": "mitra",
        "name": "SEBI MITRA",
        "asset": "Mutual funds",
        "url": "https://app.mfcentral.com/links/mitra",
        "login": "your own PAN (or PEKRN) and a code sent to your mobile or email",
        "needs": [
            [["pan", "mobile", "email", "dob", "bank_account"], ["address", "nominee"]],
            [["address"]],
        ],
        "needs_text": (
            "their name, one of PAN, mobile, email, date of birth or bank account, plus an address "
            "or a nominee's name; with none of those, a full old address (address, city and PIN)"
        ),
        "hit_shows": "the fund houses where a folio probably exists; no amount",
        "amount_on_hit": False,
        "next_step": (
            "Contact that fund house or its registrar (CAMS or KFintech) with the documents listed "
            "in MITRA's FAQ."
        ),
        "inputs_verified": True,
        "sources": [
            "https://www.sebi.gov.in/legal/circulars/feb-2025/service-platform-for-investors-to-trace-inactive-and-unclaimed-mutual-fund-folios-mitra-mutual-fund-investment-tracing-and-retrieval-assistant-_91847.html",
            "https://economictimes.indiatimes.com/wealth/invest/find-forgotten-lost-mutual-fund-investments-via-sebis-mitra-online-database/articleshow/120411565.cms",
        ],
    },
)

BY_ID: Dict[str, dict] = {p["id"]: p for p in PORTALS}
HUB_URL = "https://www.unclaimedassetsportal.in/"


def get(portal_id: str) -> dict:
    try:
        return BY_ID[portal_id]
    except KeyError:
        raise ValueError(f"unknown portal {portal_id!r}; use one of {', '.join(BY_ID)}") from None


def normalise_facts(names: Iterable[str]) -> List[str]:
    """Map user spellings ('dl', 'voter') to fact keys; refuse unknown ones."""
    out = []
    for raw in names:
        key = raw.strip().lower().replace("-", "_")
        if not key:
            continue
        key = ALIASES.get(key, key)
        if key not in FACTS:
            raise ValueError(f"unknown fact {raw!r}; use any of {', '.join(FACTS)}")
        if key not in out:
            out.append(key)
    return out


def usable_facts(portal: dict) -> List[str]:
    seen: List[str] = []
    for alternative in portal["needs"]:
        for group in alternative:
            for fact in group:
                if fact not in seen:
                    seen.append(fact)
    return seen


def is_ready(portal: dict, knows: Iterable[str]) -> bool:
    known = set(knows)
    return any(all(known & set(group) for group in alternative) for alternative in portal["needs"])
