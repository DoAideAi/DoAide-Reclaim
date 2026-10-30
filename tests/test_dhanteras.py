"""reclaim.doaide.com/dhanteras/. Run: python3 -m unittest discover -s tests -v"""
import io
import json
import re
import struct
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from urllib.parse import unquote

from reclaim import cli, dhanteras

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")


def png_size(path: Path):
    head = path.read_bytes()[:24]
    assert head[:8] == b"\x89PNG\r\n\x1a\n", f"{path.name} is not a PNG"
    return struct.unpack(">II", head[16:24])


class CommittedFilesTest(unittest.TestCase):
    def test_page_and_svgs_match_the_generator(self):
        for name, text in (("index.html", dhanteras.render()), ("card.svg", dhanteras.card_svg()),
                           ("og.svg", dhanteras.og_svg())):
            with self.subTest(name=name):
                self.assertEqual((dhanteras.DIR / name).read_text(encoding="utf-8"), text,
                                 f"site/dhanteras/{name} is stale: run `python3 -m reclaim site` and commit it")

    def test_pngs_were_rendered_from_the_committed_svgs(self):
        recorded = json.loads((dhanteras.DIR / "pngs.json").read_text(encoding="utf-8"))
        self.assertEqual(recorded, dhanteras.png_sources(),
                         "a PNG is stale: run `python3 -m reclaim site --png` (needs Chrome) and commit it")
        self.assertEqual(png_size(dhanteras.DIR / "card.png"), dhanteras.CARD_SIZE)
        self.assertEqual(png_size(dhanteras.DIR / "og.png"), dhanteras.OG_SIZE)

    def test_cli_site_writes_the_dhanteras_page(self):
        with tempfile.TemporaryDirectory() as tmp, redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(["--data-dir", tmp, "site", "--out", tmp]), 0)
            written = (Path(tmp) / "dhanteras" / "index.html").read_text(encoding="utf-8")
        self.assertEqual(written, dhanteras.render())


class PageTest(unittest.TestCase):
    def setUp(self):
        self.page = dhanteras.render()

    def test_page_makes_no_network_requests(self):
        for request in ("<script src", "<link", "<img", "@import", "fetch(", "XMLHttpRequest", "sendBeacon",
                        "WebSocket", "EventSource"):
            self.assertNotIn(request, self.page)
        self.assertIsNone(re.search(r"url\((?!#)", self.page), "only same-document url(#id) references allowed")

    def test_every_figure_links_its_source_and_is_in_the_readme(self):
        for figure in dhanteras.FIGURES:
            with self.subTest(figure=figure["value_en"]):
                self.assertIn(figure["value_hi"], self.page)
                self.assertIn(figure["source"], self.page)
                self.assertIn(figure["value_en"], README)
                self.assertIn(figure["source"], README)
        self.assertIn("22.95 lakh", README)
        self.assertIn(dhanteras.DATE_SOURCE, self.page)

    def test_page_names_the_day_and_sends_people_to_the_guide(self):
        self.assertEqual(dhanteras.DATE, "2026-11-06")
        self.assertIn("शुक्रवार, 6 नवंबर 2026", self.page)
        self.assertIn('href="/"', self.page)
        self.assertIn(f'content="{dhanteras.URL}og.png"', self.page)

    def test_whatsapp_button_carries_the_share_text_and_the_link(self):
        href = dhanteras.whatsapp_href()
        self.assertTrue(href.startswith("https://wa.me/?text="))
        self.assertEqual(unquote(href.split("=", 1)[1]), dhanteras.SHARE_TEXT)
        self.assertTrue(dhanteras.SHARE_TEXT.endswith(dhanteras.URL))
        self.assertIn(href.replace("&", "&amp;"), self.page)

    def test_inline_card_is_sized_by_css_and_labelled(self):
        root = re.search(r"<svg [^>]*>", self.page).group(0)
        self.assertIn('viewBox="0 0 1080 1350"', root)
        self.assertIn('role="img"', root)
        self.assertIn("aria-label=", root)
        self.assertNotIn("width=", root)
        self.assertNotIn("height=", root)


class ImageTextTest(unittest.TestCase):
    def test_vowel_signs_that_sit_on_a_consonant_take_no_width(self):
        self.assertEqual(dhanteras.units("पुराना"), 5)   # the u-sign (U+0941) sits under प
        self.assertEqual(dhanteras.units("ढूँढ़िए"), 4)  # ू, ँ and the nukta take no width; ि does
        self.assertEqual(dhanteras.units("gold"), 4)

    def test_every_line_on_both_images_fits_and_stays_legible(self):
        for text, size, widest in dhanteras.card_lines() + dhanteras.og_lines():
            with self.subTest(line=text):
                self.assertGreaterEqual(size, dhanteras.SMALLEST)
                self.assertLessEqual(size * dhanteras.GLYPH_EM * dhanteras.units(text), widest)

    def test_cards_hold_only_the_campaign_not_any_family_data(self):
        for svg in (dhanteras.card_svg(), dhanteras.og_svg()):
            self.assertIn("6 नवंबर", svg)
            self.assertIn("₹86,917 करोड़", svg)
            self.assertIn(dhanteras.SHORT_URL, svg)
            self.assertNotIn("href", svg)  # nothing linked or loaded from inside the image


if __name__ == "__main__":
    unittest.main()
