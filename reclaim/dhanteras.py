"""reclaim.doaide.com/dhanteras/: the Dhanteras push for the 20-family test.

Dhanteras (Friday 6 November 2026) is the day Indian families buy gold and new things for the
home. The page carries one message, Hindi first: before buying new gold, look for the money the
family already has and forgot. It sends people to the family guide at "/", carries a card to
forward in family WhatsApp groups, and a wide preview image so a shared link unfurls large.

Like the guide it makes no network requests and stores nothing. `python3 -m reclaim site` rebuilds
the page and the two SVGs; add `--png` to re-render card.png and og.png with headless Chrome. Tests
fail while a committed file is stale, PNGs included (pngs.json records the SVG each was drawn from).
"""
from __future__ import annotations

import hashlib
import html
import json
import textwrap
import unicodedata
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.parse import quote

from . import card

DIR = Path(__file__).resolve().parent.parent / "site" / "dhanteras"
URL = "https://reclaim.doaide.com/dhanteras/"
SHORT_URL = "reclaim.doaide.com/dhanteras"
DATE = "2026-11-06"
DATE_SOURCE = "https://www.drikpanchang.com/festivals/dhanteras/festivals-dhanteras-puja-timings.html"

# Every figure is also in the README's sourced list (a test holds the two together).
FIGURES = (
    {"value_hi": "₹86,917 करोड़", "value_en": "₹86,917 crore",
     "hi": "बैंकों में बिना दावे की जमा राशि, RBI के पास (जून 2026)",
     "en": "unclaimed bank deposits held by RBI (June 2026)",
     "source": "https://sansad.in/getFile/annex/271/AU2636_cT4tJc.pdf?source=pqars",
     "source_name": "Rajya Sabha reply, Aug 2026"},
    {"value_hi": "₹1.84 लाख करोड़", "value_en": "₹1.84 lakh crore",
     "hi": "शेयरों और डिविडेंड में बिना दावे का पैसा (IEPF प्राधिकरण का अनुमान)",
     "en": "unclaimed shares and dividends (IEPF Authority estimate)",
     "source": "https://www.forbesindia.com/article/30-under-30-2026/pooja-malik-recovering-your-assets/2990451/1",
     "source_name": "Forbes India, Jan 2026"},
    {"value_hi": "₹5,777 करोड़", "value_en": "₹5,777 crore",
     "hi": "सरकार के अभियान में 22.95 लाख दावों पर लौटाए गए (फ़रवरी 2026 तक)",
     "en": "returned on 22.95 lakh claims in the government's campaign (by Feb 2026)",
     "source": "https://www.pib.gov.in/PressReleasePage.aspx?PRID=2244475",
     "source_name": "PIB, Mar 2026"},
)

SHARE_TEXT = (
    "इस धनतेरस, नया सोना ख़रीदने से पहले परिवार का भूला हुआ पैसा ढूँढ़ें: पुराने बैंक खाते, शेयर, "
    "LIC और म्यूचुअल फंड। सिर्फ़ RBI के पास ₹86,917 करोड़ बिना दावे के पड़े हैं। सरकारी साइटों पर, "
    "एक शाम में, मुफ़्त।\n"
    "This Dhanteras, find the money your family forgot, free, on the official sites.\n" + URL
)

FONT = "'Noto Sans Devanagari', 'Kohinoor Devanagari', 'Nirmala UI', Mukta, " + card.FONT
GOLD, FLAME, TEXT, MUTED, BLUE = "#ffd166", "#ffb347", "#fbf3e4", "#d9c7a8", "#6ea8ff"
CARD_SIZE, OG_SIZE = (1080, 1350), (1200, 630)
GLYPH_EM = 0.58  # upper bound on the advance of one spacing character in these stacks
SMALLEST = 20    # no line on either image may be fitted below this size


def units(text: str) -> int:
    """Spacing characters: Devanagari vowel signs and nukta (category Mn) sit on their consonant.

    Measured on the Chrome render: Hindi lines come out 18-29% narrower than this estimate, Latin
    lines about 19% narrower, so a line fitted with it never reaches the margin.
    """
    return sum(1 for ch in text if unicodedata.category(ch) not in ("Mn", "Cf"))


def fit(text: str, widest: int, largest: int) -> int:
    """The largest font size, at most `largest`, that keeps `text` within `widest` px."""
    return min(largest, int(widest / (GLYPH_EM * max(units(text), 1))))


def _text(x, y, content, size, fill, weight=400, anchor="start", spacing=0, lang="hi"):
    extra = f' letter-spacing="{spacing}"' if spacing else ""
    return (f'<text x="{x}" y="{y}" xml:lang="{lang}" font-family="{html.escape(FONT)}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{extra}>'
            f'{html.escape(content, quote=False)}</text>')


def _diya(cx: int, cy: int, scale: float) -> str:
    """A small lamp: a bowl and a flame, drawn, not loaded."""
    def p(dx, dy):
        return f"{cx + dx * scale:.0f},{cy + dy * scale:.0f}"
    return (f'<circle cx="{cx}" cy="{cy - 60 * scale:.0f}" r="{150 * scale:.0f}" fill="url(#glow)"/>'
            f'<path d="M {p(-80, 0)} Q {p(0, 70)} {p(80, 0)} Z" fill="{GOLD}"/>'
            f'<path d="M {p(0, -12)} C {p(22, -42)} {p(10, -78)} {p(0, -104)} '
            f'C {p(-10, -78)} {p(-22, -42)} {p(0, -12)} Z" fill="{FLAME}"/>')


def _open(size: Tuple[int, int], inline: bool, label: str) -> List[str]:
    w, h = size
    head = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" '
            f'aria-label="{html.escape(label)}">' if inline else
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">')
    return [head,
            '<defs><linearGradient id="bg" x1="0" y1="0" x2="0.35" y2="1">'
            '<stop offset="0" stop-color="#4a0e14"/><stop offset="1" stop-color="#12060a"/></linearGradient>'
            '<radialGradient id="glow"><stop offset="0" stop-color="#ffd166" stop-opacity="0.45"/>'
            '<stop offset="1" stop-color="#ffd166" stop-opacity="0"/></radialGradient></defs>',
            f'<rect width="{w}" height="{h}" fill="url(#bg)"/>']


CARD_LINES = {
    "date": "धनतेरस · शुक्रवार, 6 नवंबर",
    "head1": "नया सोना ख़रीदने से पहले,",
    "head2": "पुराना पैसा ढूँढ़िए।",
    "english": "Before you buy new gold, find the money your family forgot.",
    "figure_label_en": "unclaimed bank deposits held by RBI, June 2026",
    "second": "+ ₹1.84 लाख करोड़ शेयरों और डिविडेंड में (IEPF का अनुमान)",
    "cta": "हर रिश्तेदार के लिए, एक शाम में, मुफ़्त:",
    "safety": "सिर्फ़ सरकारी साइटें · PAN या आधार हमें कभी न दें",
    "legal": "Official portals only. Not affiliated with RBI, SEBI, IRDAI, IEPF or LIC.",
    "brand": "DoAide Reclaim",
}


def card_lines() -> List[Tuple[str, int, int]]:
    """(text, size, widest) for every line on the card, so a test can check that each one fits."""
    w = CARD_SIZE[0] - 2 * card.MARGIN
    first = FIGURES[0]
    english = textwrap.wrap(CARD_LINES["english"], 34)
    return ([(CARD_LINES["date"], fit(CARD_LINES["date"], w, 40), w),
             (CARD_LINES["head1"], fit(CARD_LINES["head1"], w - 180, 84), w - 180),
             (CARD_LINES["head2"], fit(CARD_LINES["head2"], w - 180, 108), w - 180)]
            + [(line, fit(line, w, 42), w) for line in english]
            + [(first["value_hi"], fit(first["value_hi"], w, 150), w),
               (first["hi"], fit(first["hi"], w, 38), w),
               (CARD_LINES["figure_label_en"], fit(CARD_LINES["figure_label_en"], w, 30), w),
               (CARD_LINES["second"], fit(CARD_LINES["second"], w, 36), w),
               (CARD_LINES["cta"], fit(CARD_LINES["cta"], w, 44), w),
               (SHORT_URL, fit(SHORT_URL, w, 64), w),
               (CARD_LINES["safety"], fit(CARD_LINES["safety"], w, 32), w),
               (CARD_LINES["legal"], fit(CARD_LINES["legal"], w, 26), w),
               (CARD_LINES["brand"], 32, w)])


def card_svg(inline: bool = False) -> str:
    """The card to forward: 1080x1350, Hindi first, one sourced figure, the link."""
    m = card.MARGIN
    lines = {text: size for text, size, _ in card_lines()}
    first = FIGURES[0]
    english = textwrap.wrap(CARD_LINES["english"], 34)
    parts = _open(CARD_SIZE, inline, "धनतेरस: नया सोना ख़रीदने से पहले, पुराना पैसा ढूँढ़िए। " + SHORT_URL)
    parts.append(_diya(CARD_SIZE[0] - 150, 300, 1.0))
    parts.append(_text(m, 170, CARD_LINES["date"], lines[CARD_LINES["date"]], GOLD, 700, spacing=1))
    parts.append(_text(m, 300, CARD_LINES["head1"], lines[CARD_LINES["head1"]], TEXT, 800))
    parts.append(_text(m, 420, CARD_LINES["head2"], lines[CARD_LINES["head2"]], GOLD, 800))
    for i, line in enumerate(english):
        parts.append(_text(m, 500 + i * 52, line, lines[line], MUTED, 500, lang="en"))
    parts.append(f'<rect x="{m}" y="610" width="{CARD_SIZE[0] - 2 * m}" height="2" fill="{GOLD}" fill-opacity="0.35"/>')
    parts.append(_text(m, 770, first["value_hi"], lines[first["value_hi"]], GOLD, 800))
    parts.append(_text(m, 848, first["hi"], lines[first["hi"]], TEXT, 600))
    parts.append(_text(m, 895, CARD_LINES["figure_label_en"], lines[CARD_LINES["figure_label_en"]], MUTED, lang="en"))
    parts.append(_text(m, 968, CARD_LINES["second"], lines[CARD_LINES["second"]], TEXT, 500))
    parts.append(f'<rect x="{m}" y="1010" width="{CARD_SIZE[0] - 2 * m}" height="2" fill="{GOLD}" fill-opacity="0.35"/>')
    parts.append(_text(m, 1085, CARD_LINES["cta"], lines[CARD_LINES["cta"]], TEXT, 700))
    parts.append(_text(m, 1160, SHORT_URL, lines[SHORT_URL], GOLD, 800, lang="en"))
    parts.append(_text(m, 1222, CARD_LINES["safety"], lines[CARD_LINES["safety"]], MUTED, 500))
    parts.append(_text(m, 1262, CARD_LINES["legal"], lines[CARD_LINES["legal"]], MUTED, lang="en"))
    parts.append(f'<circle cx="{m + 12}" cy="1300" r="12" fill="{BLUE}"/>')
    parts.append(_text(m + 36, 1311, CARD_LINES["brand"], 32, TEXT, 700, lang="en"))
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


OG_LINES = {
    "date": "धनतेरस · शुक्रवार, 6 नवंबर",
    "head1": "नया सोना ख़रीदने से पहले,",
    "head2": "पुराना पैसा ढूँढ़िए।",
    "english": "Find the money your family forgot.",
    "figure": "₹86,917 करोड़ बिना दावे के, RBI के पास",
    "url": SHORT_URL + " · मुफ़्त · बिना साइन-अप",
}
OG_WIDEST = 860


def og_lines() -> List[Tuple[str, int, int]]:
    caps = {"date": 36, "head1": 72, "head2": 96, "english": 34, "figure": 56, "url": 34}
    return [(OG_LINES[k], fit(OG_LINES[k], OG_WIDEST, caps[k]), OG_WIDEST) for k in caps]


def og_svg() -> str:
    """The link preview (og:image): 1200x630, the size WhatsApp and X show large."""
    sizes = {text: size for text, size, _ in og_lines()}
    parts = _open(OG_SIZE, False, "")
    parts.append(_diya(1060, 330, 1.15))
    rows = (("date", 92, GOLD, 700, "hi"), ("head1", 190, TEXT, 800, "hi"), ("head2", 318, GOLD, 800, "hi"),
            ("english", 390, MUTED, 500, "en"), ("figure", 490, GOLD, 800, "hi"), ("url", 574, TEXT, 600, "hi"))
    for key, y, fill, weight, lang in rows:
        parts.append(_text(80, y, OG_LINES[key], sizes[OG_LINES[key]], fill, weight, lang=lang))
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def whatsapp_href() -> str:
    return "https://wa.me/?text=" + quote(SHARE_TEXT, safe="")


def render() -> str:
    stats = "\n".join(
        f'    <li><b>{f["value_hi"]}</b><span>{html.escape(f["hi"])}</span>'
        f'<span lang="en" class="en">{html.escape(f["value_en"])} {html.escape(f["en"])}</span>'
        f'<a href="{html.escape(f["source"])}" rel="noopener noreferrer" target="_blank">{html.escape(f["source_name"])}</a></li>'
        for f in FIGURES)
    return (TEMPLATE.replace("__STATS__", stats)
            .replace("__CARD__", card_svg(inline=True).strip())
            .replace("__WHATSAPP__", html.escape(whatsapp_href()))
            .replace("__DATE_SOURCE__", DATE_SOURCE)
            .replace("__URL__", URL))


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def png_sources() -> dict:
    """What pngs.json must say: the hash of the SVG each committed PNG was rendered from."""
    return {"card.png": _sha(card_svg()), "og.png": _sha(og_svg())}


def write(directory: Path = DIR, png: bool = False, chrome: Optional[str] = None) -> List[Path]:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    written = []
    for name, text in (("index.html", render()), ("card.svg", card_svg()), ("og.svg", og_svg())):
        (directory / name).write_text(text, encoding="utf-8")
        written.append(directory / name)
    if png:
        written.append(card.render_png(card_svg(), directory / "card.png", chrome=chrome, size=CARD_SIZE))
        written.append(card.render_png(og_svg(), directory / "og.png", chrome=chrome, size=OG_SIZE))
        (directory / "pngs.json").write_text(json.dumps(png_sources(), indent=1) + "\n", encoding="utf-8")
        written.append(directory / "pngs.json")
    return written


TEMPLATE = r"""<!doctype html>
<html lang="hi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>धनतेरस पर परिवार का भूला हुआ पैसा ढूँढ़ें · DoAide Reclaim</title>
<meta name="description" content="इस धनतेरस, नया सोना ख़रीदने से पहले परिवार का भूला हुआ पैसा ढूँढ़ें: बैंक खाते, शेयर, LIC और म्यूचुअल फंड, सरकार की आधिकारिक साइटों पर। मुफ़्त। Find the money your family forgot, free, on India's official portals.">
<meta property="og:title" content="इस धनतेरस, परिवार का भूला हुआ पैसा ढूँढ़ें">
<meta property="og:description" content="नया सोना ख़रीदने से पहले: पुराने बैंक खाते, शेयर, LIC और म्यूचुअल फंड, सरकारी साइटों पर एक शाम में। Free, no sign-up.">
<meta property="og:url" content="__URL__">
<meta property="og:type" content="website">
<meta property="og:image" content="__URL__og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="धनतेरस: नया सोना ख़रीदने से पहले, पुराना पैसा ढूँढ़िए। reclaim.doaide.com/dhanteras">
<meta name="twitter:card" content="summary_large_image">
<style>
  :root { --fg:#1d1410; --muted:#6b5a4c; --line:#eadfd3; --accent:#a3271c; --on-accent:#fff; --bg:#fffaf3; --card:#fbf0e2; --gold:#8a5a00 }
  @media (prefers-color-scheme: dark) {
    :root { --fg:#fbf3e4; --muted:#d9c7a8; --line:#3a2a22; --accent:#ffb347; --on-accent:#2a0d08; --bg:#12060a; --card:#1e0d10; --gold:#ffd166 }
  }
  * { box-sizing:border-box }
  body { margin:0; font:18px/1.6 "Noto Sans Devanagari", "Kohinoor Devanagari", "Nirmala UI", Mukta, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans", sans-serif; color:var(--fg); background:var(--bg) }
  main { max-width:760px; margin:0 auto; padding:40px 18px 72px }
  .date { color:var(--gold); font-weight:700; letter-spacing:.02em; margin:0 0 .6em }
  h1 { font-size:2.05rem; line-height:1.3; margin:0 0 .3em }
  h2 { font-size:1.3rem; margin:2.2em 0 .4em }
  p { margin:.5em 0 }
  .en { display:block; color:var(--muted); font-size:.93rem; line-height:1.5 }
  p.en, li .en { margin-top:.25em }
  .lead { font-size:1.08rem }
  a { color:var(--accent) }
  .stats { list-style:none; padding:0; margin:1.4em 0; display:grid; gap:10px }
  .stats li { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:12px 14px }
  .stats b { display:block; font-size:1.45rem; color:var(--gold) }
  .stats a { font-size:.8rem; color:var(--muted) }
  .cta, .button { display:inline-block; font:inherit; font-weight:700; text-decoration:none; border-radius:10px; padding:12px 18px; cursor:pointer }
  .cta { background:var(--accent); color:var(--on-accent); border:1px solid var(--accent); font-size:1.1rem }
  .cta small { display:block; font-weight:500; font-size:.8rem; opacity:.9 }
  .button { background:var(--bg); color:var(--fg); border:1px solid var(--line) }
  .row { display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin:1em 0 }
  ol.steps { padding-left:1.3em }
  ol.steps li { margin:.8em 0 }
  .card svg { display:block; width:min(100%, 420px); height:auto; border-radius:16px; margin:1em 0 }
  .note { border-left:3px solid var(--accent); padding:4px 12px; margin:1em 0 }
  footer { margin-top:3em; color:var(--muted); font-size:.85rem; border-top:1px solid var(--line); padding-top:1.2em }
  footer p { margin:.4em 0 }
  :focus-visible { outline:3px solid var(--accent); outline-offset:2px }
</style>
</head>
<body>
<main>
  <p class="date">धनतेरस · शुक्रवार, 6 नवंबर 2026</p>
  <h1>इस धनतेरस, नया सोना ख़रीदने से पहले परिवार का भूला हुआ पैसा ढूँढ़िए।</h1>
  <p lang="en" class="en">This Dhanteras, before you buy new gold, find the money your family forgot.</p>
  <p class="lead">पुराने बैंक खाते, शेयर और डिविडेंड, LIC और दूसरे बीमे, म्यूचुअल फंड: जिस पैसे पर किसी ने दावा नहीं किया, वह परिवार के लिए रखा रहता है, कई बार दशकों तक। सरकार की आधिकारिक साइटों पर हर रिश्तेदार के लिए एक शाम में खोजिए। मुफ़्त, बिना साइन-अप।</p>
  <p lang="en" class="en">Old bank accounts, shares and dividends, LIC and other insurance, mutual funds: money nobody claimed is held for the family, often for decades. Search the government's official sites for every relative in one evening. Free, no sign-up.</p>
  <p><a class="cta" href="/">खोज शुरू करें<small lang="en">Start the search</small></a></p>
  <ul class="stats">
__STATS__
  </ul>

  <h2>एक शाम, तीन क़दम <span lang="en" class="en">One evening, three steps</span></h2>
  <ol class="steps">
    <li>सूची बनाइए: दादा-दादी, नाना-नानी, माता-पिता, और जो रिश्तेदार अब नहीं रहे।<span lang="en" class="en">Make a list: grandparents, parents, and relatives who have passed away.</span></li>
    <li>गाइड खोलिए। वह बताती है कि हर सरकारी साइट पर क्या चाहिए। PAN, जन्मतिथि और खाता नंबर सिर्फ़ सरकारी साइट पर डालिए।<span lang="en" class="en">Open the guide. It shows what each official site needs. Type PAN, dates of birth and account numbers only on the official sites.</span></li>
    <li>जो दिखा, वह मार्क कीजिए और "Send on WhatsApp" से उसे भेज दीजिए जिसने आपको यह भेजा, कुछ न मिले तब भी।<span lang="en" class="en">Mark what each site showed and use "Send on WhatsApp" to send it to whoever sent you this, even if nothing turned up.</span></li>
  </ol>
  <p class="note">गाइड का पेज अभी अंग्रेज़ी में है। पहली खोज उसके साथ कीजिए जिसने आपको यह भेजा।<span lang="en" class="en">The guide is in English for now. Do the first search together with whoever sent you this.</span></p>

  <h2>परिवार के ग्रुप में भेजिए <span lang="en" class="en">Send it to the family group</span></h2>
  <div class="card">__CARD__</div>
  <div class="row">
    <a class="cta" href="__WHATSAPP__" target="_blank" rel="noopener noreferrer">WhatsApp पर भेजें<small lang="en">Send on WhatsApp</small></a>
    <button class="button" type="button" id="share" hidden>कार्ड शेयर करें</button>
    <a class="button" href="card.png" download="dhanteras-reclaim.png">कार्ड डाउनलोड करें</a>
  </div>

  <p class="note">मिलान का मतलब पैसा हाथ में आना नहीं है: दावा आप ख़ुद बैंक, कंपनी, बीमा कंपनी या फंड हाउस से करते हैं, और IEPF प्राधिकरण कहता है कि दावा सीधे करें, बिचौलियों के ज़रिए नहीं। यह पेज कोई जानकारी नहीं माँगता और कुछ भी सर्वर पर सेव नहीं करता।<span lang="en" class="en">A match is not money in hand: you claim it yourself from the bank, company, insurer or fund house, and the IEPF Authority asks claimants to file directly, without middlemen. This page asks for nothing and stores nothing on a server.</span></p>

  <footer lang="en">
    <p>Dhanteras date: <a href="__DATE_SOURCE__" rel="noopener noreferrer" target="_blank">Drik Panchang (New Delhi)</a>. Figures link to their sources above.</p>
    <p>Not affiliated with RBI, SEBI, IRDAI, the IEPF Authority, LIC or any bank. Open source: <a href="https://github.com/DoAideAi/DoAide-Reclaim">github.com/DoAideAi/DoAide-Reclaim</a>. A DoAide project.</p>
  </footer>
</main>
<script>
(function () {
  "use strict";
  var button = document.getElementById("share");
  var probe = typeof File === "function" ? new File([""], "probe.png", { type: "image/png" }) : null;
  if (!probe || !navigator.canShare || !navigator.canShare({ files: [probe] })) { return; }
  button.hidden = false;
  button.addEventListener("click", function () {
    var svg = document.querySelector(".card svg").cloneNode(true);
    svg.setAttribute("width", "1080");
    svg.setAttribute("height", "1350");
    var img = new Image();
    img.onload = function () {
      var canvas = document.createElement("canvas");
      canvas.width = 1080; canvas.height = 1350;
      canvas.getContext("2d").drawImage(img, 0, 0, 1080, 1350);
      canvas.toBlob(function (blob) {
        var file = new File([blob], "dhanteras-reclaim.png", { type: "image/png" });
        navigator.share({ files: [file], text: "__URL__" }).catch(function () {});
      }, "image/png");
    };
    img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(new XMLSerializer().serializeToString(svg));
  });
})();
</script>
</body>
</html>
"""
