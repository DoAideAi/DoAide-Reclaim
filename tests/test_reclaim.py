"""Behaviour tests for DoAide Reclaim.

Run:  python3 -m unittest discover -s tests -v     (stdlib only; pytest also works)
"""
from __future__ import annotations

import contextlib
import io
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from reclaim import card, cases, checklist, cli, portals, report  # noqa: E402
from reclaim.money import format_inr, inr_words, parse_amount  # noqa: E402
from reclaim.privacy import IdentifierError, check_text, find_identifiers  # noqa: E402


class TempData(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="reclaim-test-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.store = cases.Store(self.tmp)

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.main(["--data-dir", str(self.tmp), *argv])
        return code, out.getvalue(), err.getvalue()


def found(portal, amount=None, estimate=False):
    return {"member": "m1", "portal": portal, "status": "found", "amount": amount,
            "estimate": estimate, "reason": None, "at": ""}


class PortalRegistry(unittest.TestCase):
    def test_every_portal_is_sourced_https_and_uses_known_facts(self):
        ids = [p["id"] for p in portals.PORTALS]
        self.assertEqual(len(ids), len(set(ids)))
        for p in portals.PORTALS:
            with self.subTest(portal=p["id"]):
                self.assertEqual(urlparse(p["url"]).scheme, "https")
                self.assertTrue(p["sources"])
                self.assertTrue(all(urlparse(s).scheme == "https" for s in p["sources"]))
                self.assertTrue(set(portals.usable_facts(p)) <= set(portals.FACTS))

    def test_udgam_needs_one_identifier_or_an_old_address(self):
        udgam = portals.get("udgam")
        self.assertFalse(portals.is_ready(udgam, []))
        self.assertTrue(portals.is_ready(udgam, ["dob"]))
        self.assertTrue(portals.is_ready(udgam, ["address"]))

    def test_lic_needs_a_second_field_besides_the_name(self):
        lic = portals.get("lic")
        self.assertFalse(portals.is_ready(lic, ["address"]))
        self.assertTrue(portals.is_ready(lic, ["dob"]))

    def test_mitra_needs_key_plus_additional_detail_or_a_full_address(self):
        mitra = portals.get("mitra")
        self.assertFalse(portals.is_ready(mitra, ["dob"]))
        self.assertFalse(portals.is_ready(mitra, ["nominee"]))
        self.assertTrue(portals.is_ready(mitra, ["dob", "nominee"]))
        self.assertTrue(portals.is_ready(mitra, ["address"]))

    def test_irdai_form_needs_a_policy_number(self):
        form = portals.get("insurers")
        self.assertFalse(portals.is_ready(form, ["dob", "address"]))
        self.assertTrue(portals.is_ready(form, ["policy_number", "dob", "address"]))

    def test_fact_aliases_and_unknown_facts(self):
        self.assertEqual(portals.normalise_facts(["DL", "voter", "dob", "dob"]),
                         ["driving_licence", "voter_id", "dob"])
        with self.assertRaises(ValueError):
            portals.normalise_facts(["aadhaar"])


class Privacy(unittest.TestCase):
    def test_identifier_values_are_refused(self):
        for text in ["ABCDE1234F", "1234 5678 9012", "9876543210", "+91 9876543210",
                     "acct 001234567890", "ram@example.com", "12/03/1951", "1951-03-12"]:
            with self.subTest(text=text):
                self.assertTrue(find_identifiers(text))
                with self.assertRaises(IdentifierError):
                    check_text("detail", text)

    def test_ordinary_words_and_amounts_pass(self):
        for text in ["Grandpa's 1994 shares", "SBI and Canara Bank", "₹3.2 lakh", "42,000", "friends"]:
            with self.subTest(text=text):
                self.assertEqual(find_identifiers(text), [])


class Money(unittest.TestCase):
    def test_indian_digit_grouping(self):
        self.assertEqual(format_inr(999), "₹999")
        self.assertEqual(format_inr(42000), "₹42,000")
        self.assertEqual(format_inr(320000), "₹3,20,000")
        self.assertEqual(format_inr(12345678), "₹1,23,45,678")

    def test_headline_never_rounds_up(self):
        self.assertEqual(inr_words(320000), "₹3.2 lakh")
        self.assertEqual(inr_words(100000), "₹1 lakh")
        self.assertEqual(inr_words(129999), "₹1.29 lakh")
        self.assertEqual(inr_words(12500000), "₹1.25 crore")
        self.assertEqual(inr_words(99999), "₹99,999")

    def test_parses_the_ways_families_write_amounts(self):
        for text, rupees in [("42000", 42000), ("42,000", 42000), ("1,20,000", 120000), ("42k", 42000),
                             ("3.2 lakh", 320000), ("3.2L", 320000), ("₹1.5 cr", 15000000),
                             ("Rs. 2 crore", 20000000)]:
            with self.subTest(text=text):
                self.assertEqual(parse_amount(text), rupees)
        for bad in ["", "lots", "3.2 million", "0", "-5"]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                parse_amount(bad)


class Cases(TempData):
    def test_no_case_without_consent_and_ids_count_up(self):
        with self.assertRaises(cases.CaseError):
            self.store.create(consent=False)
        self.assertEqual(self.store.create(consent=True)["id"], "R001")
        self.assertEqual(self.store.create(consent=True)["id"], "R002")

    def test_identifier_values_cannot_enter_a_case(self):
        with self.assertRaises(IdentifierError):
            self.store.create(consent=True, channel="9876543210")
        case = self.store.create(consent=True)
        with self.assertRaises(ValueError):
            cases.add_member(case, "father", knows=["ABCDE1234F"])

    def test_record_rules(self):
        case = self.store.create(consent=True)
        cases.add_member(case, "mother", knows=["dob"], skip=["mitra"])
        bad = [
            ("m1", "mitra", "not_found", {}),            # skipped for this family
            ("m1", "udgam", "not_found", {"amount": 5}),  # only a find has an amount
            ("m1", "udgam", "blocked", {}),               # a block needs a reason
            ("m2", "udgam", "found", {}),                 # no such member
        ]
        for member_id, portal_id, status, extra in bad:
            with self.subTest(case=(member_id, portal_id, status)), self.assertRaises(cases.CaseError):
                cases.record(case, member_id, portal_id, status, **extra)
        cases.record(case, "m1", "udgam", "not_found")
        cases.record(case, "m1", "udgam", "found")
        self.assertEqual([(r["portal"], r["status"]) for r in case["results"]], [("udgam", "found")])

    def test_reply_is_applied_whole_or_not_at_all(self):
        case = self.store.create(consent=True)
        cases.add_member(case, "father", deceased=True, knows=["dob", "address"])
        applied = cases.apply_reply(
            case, "m1 udgam found\n*m1 iepf found ~1,20,000*\nm1 lic no\nm1 mitra blocked otp\n"
        )
        self.assertEqual(len(applied), 4)
        iepf = [r for r in case["results"] if r["portal"] == "iepf"][0]
        self.assertEqual((iepf["amount"], iepf["estimate"]), (120000, True))
        before = json.dumps(case, sort_keys=True)
        with self.assertRaises(cases.CaseError) as raised:
            cases.apply_reply(case, "m1 insurers no\nm1 udgam maybe\nm9 lic no\n")
        self.assertIn("line 2", str(raised.exception))
        self.assertIn("m9", str(raised.exception))
        self.assertEqual(json.dumps(case, sort_keys=True), before)

    def test_delete_erases_the_case(self):
        self.store.create(consent=True)
        self.store.delete("R001")
        self.assertEqual(self.store.ids(), [])


class Checklist(TempData):
    def test_marks_what_is_ready_and_keeps_values_out_of_chat(self):
        case = self.store.create(consent=True)
        cases.add_member(case, "grandfather", deceased=True, knows=["address"], skip=["insurers"])
        text = checklist.render(case)

        def block(code):
            return text.split(f"[{code}]")[1].split("\n  [")[0]

        self.assertNotIn("[m1 insurers]", text)
        self.assertNotIn("NOT READY", block("m1 udgam"))   # an old address is enough for UDGAM
        self.assertIn("NOT READY", block("m1 lic"))        # LIC needs DOB, PAN or a policy number
        self.assertIn("never in this chat", text)
        self.assertIn("https://udgam.rbi.org.in", text)


class Report(TempData):
    def family(self, outcomes, shared=None):
        case = self.store.create(consent=True)
        cases.add_member(case, "father", knows=["dob", "address", "policy_number"])
        for portal_id, status, amount in outcomes:
            cases.record(case, "m1", portal_id, status, amount=amount,
                         reason="otp" if status == "blocked" else None)
        if shared is not None:
            case["card"] = {"at": cases.now(), "shared": shared}
        self.store.save(case)

    def test_wilson_interval_matches_the_textbook_value(self):
        low, high = report.wilson(2, 20)
        self.assertAlmostEqual(low, 0.0279, places=3)
        self.assertAlmostEqual(high, 0.3010, places=3)

    def test_incomplete_until_the_target_is_reached(self):
        self.family([("udgam", "found", None)], shared=True)
        self.assertTrue(report.summarize(self.store.all(), target=20)["verdict"].startswith("INCOMPLETE"))

    def test_go_and_not_yet(self):
        for _ in range(8):
            self.family([("udgam", "not_found", None), ("lic", "not_found", None)])
        self.family([("udgam", "found", None)], shared=True)
        self.family([("iepf", "found", 320000), ("udgam", "blocked", None)], shared=False)
        summary = report.summarize(self.store.all(), target=10, min_hit_rate=0.10, min_share_rate=0.30)
        self.assertEqual((summary["searched"], summary["hit_families"]), (10, 2))
        self.assertEqual((summary["finds"], summary["finds_with_amount"], summary["rupees_found"]), (2, 1, 320000))
        self.assertEqual(summary["portals"]["udgam"]["blocked"], {"otp": 1})
        self.assertEqual(summary["verdict"], "GO to phase 2 (claim packets)")
        strict = report.summarize(self.store.all(), target=10, min_hit_rate=0.25)
        self.assertTrue(strict["verdict"].startswith("NOT YET"))
        self.assertIn("hit rate", strict["verdict"])
        self.assertIn("Verdict: GO", report.render(summary))


class Card(unittest.TestCase):
    def test_rupees_only_when_an_amount_was_reported(self):
        text = card.svg([found("iepf", 320000), found("udgam")])
        self.assertIn("₹3.2 lakh", text)
        self.assertIn("₹3,20,000", text)
        self.assertIn("+ 1 more holding", text)
        text = card.svg([found("udgam"), found("udgam")])
        self.assertNotIn("lakh", text)
        self.assertIn("forgotten family accounts", text)

    def test_estimates_are_labelled(self):
        self.assertIn("WE FOUND ABOUT", card.svg([found("iepf", 150000, estimate=True)]))

    def test_no_card_without_a_find_and_no_identifiers_on_it(self):
        with self.assertRaises(card.CardError):
            card.svg([])
        with self.assertRaises(IdentifierError):
            card.svg([found("lic", 5000)], detail="policy 123456789")
        page = card.page(card.svg([found("lic", 5000)], detail="Grandpa's 1994 shares"))
        self.assertIn("<svg", page)
        self.assertIn("Grandpa&#x27;s 1994 shares", page)

    def test_worst_case_layout_keeps_the_detail_clear_of_chips_and_footer(self):
        # four asset chips wrap to a second row; with no amounts the headline is tallest
        text = card.svg([found("udgam"), found("iepf"), found("lic"), found("mitra")],
                        detail="Nana's Reliance shares from 1988")
        detail_y = int(re.search(r'y="(\d+)"[^>]*font-style="italic"', text).group(1))
        chip_bottom = max(int(y) + 64 for y in re.findall(r'<rect x="\d+" y="(\d+)" width', text))
        self.assertLessEqual(detail_y, card.FOOT - 100)
        self.assertGreater(detail_y - 52, chip_bottom)

    def test_png_without_chrome_explains_the_fallback(self):
        with mock.patch.object(card, "find_chrome", return_value=None):
            with self.assertRaises(card.CardError) as raised:
                card.render_png(card.svg([found("lic", 5000)]), Path("unused.png"))
        self.assertIn("save button", str(raised.exception))


class CommandLine(TempData):
    def test_full_operator_flow(self):
        code, out, err = self.run_cli("new", "--consent", "--channel", "friends")
        self.assertEqual((code, out.strip()), (0, "R001"), err)
        self.assertEqual(self.run_cli("member", "R001", "--relation", "father", "--deceased",
                                      "--knows", "dob,address")[0], 0)
        self.assertIn("[m1 mitra]", self.run_cli("checklist", "R001")[1])
        reply = self.tmp / "reply.txt"
        reply.write_text("m1 udgam found\nm1 iepf found 1.2 lakh\nm1 lic no\nm1 insurers no\nm1 mitra no\n")
        self.assertEqual(self.run_cli("record", "R001", "--reply", str(reply))[0], 0)
        self.assertEqual(self.run_cli("done", "R001", "--minutes", "35")[0], 0)
        code, _, err = self.run_cli("card", "R001", "--detail", "Dad's old shares")
        self.assertEqual(code, 0, err)
        self.assertTrue((self.tmp / "cards" / "R001" / "card.svg").exists())
        self.assertEqual(self.run_cli("shared", "R001", "yes")[0], 0)
        summary = json.loads(self.run_cli("report", "--json")[1])
        self.assertEqual((summary["hit_families"], summary["shared"], summary["median_minutes"]), (1, 1, 35))
        self.assertEqual(self.run_cli("delete", "R001")[0], 1)
        self.assertEqual(self.run_cli("delete", "R001", "--yes")[0], 0)

    def test_errors_are_one_line_not_tracebacks(self):
        code, _, err = self.run_cli("member", "R001", "--relation", "father")
        self.assertEqual(code, 1)
        self.assertIn("no case R001", err)


if __name__ == "__main__":
    unittest.main()
