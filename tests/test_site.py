"""reclaim.doaide.com and the reply it produces. Run: python3 -m unittest discover -s tests -v"""
import io
import json
import re
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from reclaim import cases, cli, portals, site

# What the page's "Send on WhatsApp" text looks like (replyLines() in reclaim/site.py).
PAGE_REPLY = """# Reclaim results from reclaim.doaide.com
m1 is father late knows dob,address,share_records
m2 is grandmother late knows address
m1 udgam found
m1 iepf found ~320000
m1 lic no
m2 mitra blocked otp
"""


def new_case(root):
    return cases.Store(Path(root)).create(consent=True, channel="site")


class PageTest(unittest.TestCase):
    def test_committed_page_matches_the_portal_registry(self):
        self.assertEqual(site.SITE.read_text(encoding="utf-8"), site.render(),
                         "site/index.html is stale: run `python3 -m reclaim site` and commit it")

    def test_page_carries_every_portal_and_makes_no_network_requests(self):
        html = site.render()
        match = re.search(r"var DATA = (\{.*?\});\n", html)
        assert match is not None, "the page lost its embedded DATA"
        embedded = json.loads(match.group(1))
        self.assertEqual(embedded, json.loads(json.dumps(site.data())))
        self.assertEqual([p["id"] for p in embedded["portals"]], [p["id"] for p in portals.PORTALS])
        for portal in portals.PORTALS:
            self.assertIn(portal["url"], html)
        for request in ("<script src", "<link", "<img", "@import", "url(", "fetch(", "XMLHttpRequest",
                        "sendBeacon", "WebSocket", "EventSource"):
            self.assertNotIn(request, html)

    def test_cli_rebuilds_the_page(self):
        with tempfile.TemporaryDirectory() as tmp, redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(["--data-dir", tmp, "site", "--out", tmp]), 0)
            self.assertEqual((Path(tmp) / "index.html").read_text(encoding="utf-8"), site.render())


class PageReplyTest(unittest.TestCase):
    def test_a_page_reply_lists_the_relatives_and_records_their_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = new_case(tmp)
            applied = cases.apply_reply(case, PAGE_REPLY)
        self.assertEqual(len(applied), 6)
        self.assertEqual(
            [(m["id"], m["relation"], m["deceased"], m["knows"]) for m in case["members"]],
            [("m1", "father", True, ["dob", "address", "share_records"]),
             ("m2", "grandmother", True, ["address"])],
        )
        results = {(r["member"], r["portal"]): r for r in case["results"]}
        self.assertEqual(results[("m1", "iepf")]["amount"], 320000)
        self.assertTrue(results[("m1", "iepf")]["estimate"])
        self.assertEqual(results[("m1", "lic")]["status"], "not_found")
        self.assertEqual(results[("m2", "mitra")]["reason"], "otp")

    def test_sending_the_same_reply_twice_changes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = new_case(tmp)
            cases.apply_reply(case, PAGE_REPLY)
            first = (json.dumps(case["members"]), len(case["results"]))
            cases.apply_reply(case, PAGE_REPLY)
        self.assertEqual((json.dumps(case["members"]), len(case["results"])), first)

    def test_listed_relatives_must_line_up_with_the_case(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = new_case(tmp)
            cases.add_member(case, "father", deceased=True)
            before = json.dumps(case)
            refused = {
                "m1 is mother": "but the reply says mother",
                "m3 is uncle": "the next relative in R001 is m2",
                "m2 is uncle knows horoscope": "unknown fact",
                "m2 is uncle knows ABCDE1234F": "unknown fact",
                "m2 is uncle maybe": "expected 'm1 is father late knows dob,address'",
                "x2 is uncle": "is not a relative id",
                "m2 is cousin": "relation must be one of",
            }
            for line, message in refused.items():
                with self.subTest(line=line):
                    with self.assertRaises(cases.CaseError) as ctx:
                        cases.apply_reply(case, line + "\nm1 udgam found\n")
                    self.assertIn(message, str(ctx.exception))
                    self.assertEqual(json.dumps(case), before)

    def test_operator_added_relatives_keep_their_skips(self):
        with tempfile.TemporaryDirectory() as tmp:
            case = new_case(tmp)
            cases.add_member(case, "father", deceased=True, skip=["mitra"])
            cases.apply_reply(case, "m1 is father late knows pan\nm1 udgam no\n")
        self.assertEqual((case["members"][0]["knows"], case["members"][0]["skip"]), (["pan"], ["mitra"]))


if __name__ == "__main__":
    unittest.main()
