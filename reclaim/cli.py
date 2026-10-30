"""reclaim: the operator console for the phase-1 hit-rate test.

    python3 -m reclaim new --consent --channel friends      -> R001
    python3 -m reclaim member R001 --relation father --deceased --knows dob,address
    python3 -m reclaim checklist R001                        -> paste into WhatsApp
    python3 -m reclaim record R001 --reply reply.txt         -> or: record R001 m1 udgam found
    python3 -m reclaim done R001 --minutes 35
    python3 -m reclaim card R001 --png --detail "Grandpa's 1994 shares"
    python3 -m reclaim shared R001 yes
    python3 -m reclaim report
    python3 -m reclaim site                                  -> rebuild site/index.html and site/dhanteras/
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from . import cases, checklist, dhanteras, portals, report, site
from . import card as cards
from .money import parse_amount
from .privacy import IdentifierError

DEFAULT_DATA = Path(__file__).resolve().parent.parent / "data"


def _split(value: str) -> List[str]:
    return [part for part in (value or "").split(",") if part.strip()]


def cmd_portals(args, store):
    print(f"Portal facts checked {portals.CHECKED}. Hub: {portals.HUB_URL}\n")
    for p in portals.PORTALS:
        flag = "" if p["inputs_verified"] else "   [search fields NOT verified: site blocks automated reads]"
        print(f"{p['id']:<9} {p['name']} · {p['asset']}{flag}")
        print(f"          {p['url']}")
        print(f"          needs: {p['needs_text']}")
        print(f"          login: {p['login'] or 'none'}")
        print(f"          a hit shows: {p['hit_shows']}")
        print(f"          next: {p['next_step']}")
        if args.sources:
            for source in p["sources"]:
                print(f"          source: {source}")
        print()


def cmd_new(args, store):
    case = store.create(consent=args.consent, channel=args.channel)
    print(case["id"])


def cmd_member(args, store):
    case = store.load(args.case)
    entry = cases.add_member(case, args.relation, args.deceased, _split(args.knows), _split(args.skip))
    store.save(case)
    print(f"{case['id']} {entry['id']}: {entry['relation']}" + (" (late)" if entry["deceased"] else ""))


def cmd_checklist(args, store):
    sys.stdout.write(checklist.render(store.load(args.case)))


def cmd_record(args, store):
    case = store.load(args.case)
    if args.reply:
        text = sys.stdin.read() if args.reply == "-" else Path(args.reply).read_text(encoding="utf-8")
        applied = cases.apply_reply(case, text)
        store.save(case)
        listed = sum(1 for entry in applied if entry.get("type") == "member")
        print(f"{case['id']}: {len(applied) - listed} results recorded"
              + (f", {listed} relatives listed" if listed else ""))
        return
    if not (args.member and args.portal and args.status):
        raise cases.CaseError("give MEMBER PORTAL STATUS, or --reply FILE")
    status = {"no": "not_found", "not-found": "not_found"}.get(args.status, args.status)
    amount = parse_amount(args.amount) if args.amount else None
    cases.record(case, args.member, args.portal, status, amount=amount, estimate=args.estimate, reason=args.reason)
    store.save(case)
    print(f"{case['id']} {args.member} {args.portal}: {status}")


def cmd_done(args, store):
    case = store.load(args.case)
    cases.mark_done(case, args.minutes)
    store.save(case)
    print(f"{case['id']} finished")


def cmd_card(args, store):
    case = store.load(args.case)
    finds = [r for r in case["results"] if r["status"] == "found"]
    svg_text = cards.svg(finds, detail=args.detail, url=args.url)
    out = Path(args.out) if args.out else store.root / "cards" / case["id"]
    out.mkdir(parents=True, exist_ok=True)
    (out / "card.svg").write_text(svg_text, encoding="utf-8")
    (out / "card.html").write_text(cards.page(svg_text), encoding="utf-8")
    written = [out / "card.svg", out / "card.html"]
    if args.png:
        written.append(cards.render_png(svg_text, out / "card.png"))
    previous = case.get("card") or {}
    case["card"] = {"at": cases.now(), "shared": previous.get("shared")}
    store.save(case)
    for path in written:
        print(path)


def cmd_shared(args, store):
    case = store.load(args.case)
    cases.set_shared(case, args.answer == "yes")
    store.save(case)
    print(f"{case['id']} shared: {args.answer}")


def cmd_report(args, store):
    summary = report.summarize(store.all(), args.target, args.min_hit_rate, args.min_share_rate)
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        sys.stdout.write(report.render(summary))


def cmd_delete(args, store):
    if not args.yes:
        raise cases.CaseError(f"this erases {args.case} for good; add --yes")
    store.delete(args.case)
    print(f"{args.case} deleted")


def cmd_site(args, store):
    root = Path(args.out) if args.out else site.SITE.parent
    print(site.write(root / "index.html"))
    for path in dhanteras.write(root / "dhanteras", png=args.png):
        print(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="reclaim", description=__doc__.split("\n\n")[0])
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA), help="where cases and cards live (git-ignored)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("portals", help="what each official portal needs, with sources")
    p.add_argument("--sources", action="store_true")
    p.set_defaults(func=cmd_portals)

    p = sub.add_parser("new", help="enrol a family (after reading them the consent script)")
    p.add_argument("--consent", action="store_true", help="the family heard the consent script v1 and agreed")
    p.add_argument("--channel", default="", help="how they were recruited, e.g. friends, x, linkedin")
    p.set_defaults(func=cmd_new)

    p = sub.add_parser("member", help="add a relative to search for")
    p.add_argument("case")
    p.add_argument("--relation", required=True, help=", ".join(cases.RELATIONS))
    p.add_argument("--deceased", action="store_true")
    p.add_argument("--knows", default="", help="facts the family HAS (never the values): " + ",".join(portals.FACTS))
    p.add_argument("--skip", default="", help="portals that do not apply, e.g. mitra,iepf")
    p.set_defaults(func=cmd_member)

    p = sub.add_parser("checklist", help="the WhatsApp-ready search list for a family")
    p.add_argument("case")
    p.set_defaults(func=cmd_checklist)

    p = sub.add_parser("record", help="record what a portal showed")
    p.add_argument("case")
    p.add_argument("member", nargs="?")
    p.add_argument("portal", nargs="?")
    p.add_argument("status", nargs="?", choices=["found", "not_found", "not-found", "no", "blocked"])
    p.add_argument("--amount", help="when the site showed one: 42000, 1,20,000, 3.2 lakh")
    p.add_argument("--estimate", action="store_true", help="the amount is the family's estimate")
    p.add_argument("--reason", choices=cases.BLOCK_REASONS, help="why a search was blocked")
    p.add_argument("--reply", help="a file with the family's reply lines, or - for stdin")
    p.set_defaults(func=cmd_record)

    p = sub.add_parser("done", help="the family finished every search they could")
    p.add_argument("case")
    p.add_argument("--minutes", type=int, help="total minutes the family spent")
    p.set_defaults(func=cmd_done)

    p = sub.add_parser("card", help="make the shareable 'we found' card")
    p.add_argument("case")
    p.add_argument("--detail", default="", help="optional line the family chose, e.g. \"Grandpa's 1994 shares\"")
    p.add_argument("--url", default="", help="optional link on the card (only once it is live)")
    p.add_argument("--out", help="output folder (default: <data-dir>/cards/<case>)")
    p.add_argument("--png", action="store_true", help="also render card.png with headless Chrome")
    p.set_defaults(func=cmd_card)

    p = sub.add_parser("shared", help="did the family share their card?")
    p.add_argument("case")
    p.add_argument("answer", choices=["yes", "no"])
    p.set_defaults(func=cmd_shared)

    p = sub.add_parser("report", help="hit rate, share rate and the go/no-go verdict")
    p.add_argument("--json", action="store_true")
    p.add_argument("--target", type=int, default=report.TARGET)
    p.add_argument("--min-hit-rate", type=float, default=report.MIN_HIT_RATE)
    p.add_argument("--min-share-rate", type=float, default=report.MIN_SHARE_RATE)
    p.set_defaults(func=cmd_report)

    p = sub.add_parser("delete", help="erase a family's case")
    p.add_argument("case")
    p.add_argument("--yes", action="store_true")
    p.set_defaults(func=cmd_delete)

    p = sub.add_parser("site", help="rebuild the reclaim.doaide.com pages (guide and /dhanteras/)")
    p.add_argument("--out", help="output folder (default: site/ in the repository)")
    p.add_argument("--png", action="store_true", help="also re-render dhanteras/card.png and og.png with Chrome")
    p.set_defaults(func=cmd_site)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    store = cases.Store(Path(args.data_dir))
    try:
        args.func(args, store)
    except (cases.CaseError, cards.CardError, IdentifierError, ValueError) as exc:
        print(f"reclaim: {exc}", file=sys.stderr)
        return 1
    return 0
