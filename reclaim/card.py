"""The shareable card: what a family found, never who they are.

The card shows a rupee figure only when the family reported one. UDGAM and MITRA never show an
amount on a hit, so a find without one becomes "2 forgotten accounts" instead of a guess.
"""
from __future__ import annotations

import html
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path
from typing import Dict, List, Optional

from . import portals
from .money import format_inr, inr_words
from .privacy import check_text

W, H = 1080, 1350
MARGIN = 80
FOOT = 1090  # baseline of the footer's first line; everything above must end before it
FONT = "Inter, 'SF Pro Display', 'Segoe UI', Roboto, 'Noto Sans', 'Helvetica Neue', Arial, sans-serif"
GOLD, MINT, TEXT, MUTED, BLUE = "#ffd166", "#8be0b5", "#f2f2f2", "#a7b3ad", "#0a66ff"
CHROME_PATHS = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
)


class CardError(ValueError):
    pass


def facts(finds: List[dict]) -> Dict[str, object]:
    """The numbers a card is allowed to state, from the case's 'found' results only."""
    if not finds:
        raise CardError("nothing found yet: a card is only made for a find")
    valued = [r for r in finds if r["amount"]]
    assets: List[str] = []
    for result in finds:
        asset = portals.get(result["portal"])["asset"]
        if asset not in assets:
            assets.append(asset)
    only_bank = all(r["portal"] == "udgam" for r in finds)
    return {
        "count": len(finds),
        "rupees": sum(r["amount"] for r in valued),
        "unvalued": len(finds) - len(valued),
        "estimate": any(r["estimate"] for r in valued),
        "assets": assets,
        "noun": "account" if only_bank else "holding",
    }


def _plural(n: int, noun: str) -> str:
    return f"{n} {noun}" + ("" if n == 1 else "s")


def _text(x, y, content, size, fill, weight=400, anchor="start", spacing=0, opacity=1.0, italic=False):
    extra = f' letter-spacing="{spacing}"' if spacing else ""
    extra += f' opacity="{opacity}"' if opacity != 1.0 else ""
    extra += ' font-style="italic"' if italic else ""
    return (
        f'<text x="{x}" y="{y}" font-family="{html.escape(FONT)}" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{extra}>{html.escape(content)}</text>'
    )


def _fit(text: str, widest: int, largest: int) -> int:
    """A font size that keeps text within `widest` px (about 0.58em per glyph for this stack)."""
    return max(40, min(largest, int(widest / (0.58 * max(len(text), 1)))))


def svg(finds: List[dict], detail: str = "", url: str = "") -> str:
    f = facts(finds)
    detail = check_text("detail", detail, limit=60)
    url = check_text("url", url, limit=60)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        '<defs><linearGradient id="bg" x1="0" y1="0" x2="0.4" y2="1">'
        '<stop offset="0" stop-color="#0a3a2a"/><stop offset="1" stop-color="#0b0f0d"/>'
        '</linearGradient></defs>',
        f'<rect width="{W}" height="{H}" fill="url(#bg)"/>',
        _text(W - 40, 980, "₹", 900, GOLD, weight=800, anchor="end", opacity=0.05),
    ]
    y = 230
    if f["rupees"]:
        parts.append(_text(MARGIN, y, "WE FOUND ABOUT" if f["estimate"] else "WE FOUND", 34, MINT, 700, spacing=6))
        big = inr_words(f["rupees"])
        size = _fit(big, W - 2 * MARGIN, 190)
        y += 40 + size
        parts.append(_text(MARGIN, y, big, size, GOLD, 800))
        exact = format_inr(f["rupees"])
        if exact != big:
            y += 70
            parts.append(_text(MARGIN, y, exact, 48, GOLD, 600, opacity=0.75))
        y += 90
        parts.append(_text(MARGIN, y, "of forgotten family money", 60, TEXT, 700))
        if f["unvalued"]:
            y += 64
            more = _plural(f["unvalued"], "more " + f["noun"])
            parts.append(_text(MARGIN, y, f"+ {more}, valued when we claim", 40, MUTED))
    else:
        parts.append(_text(MARGIN, y, "WE FOUND", 34, MINT, 700, spacing=6))
        y += 300
        parts.append(_text(MARGIN, y, str(f["count"]), 320, GOLD, 800))
        y += 100
        noun = f"forgotten family {f['noun']}" + ("" if f["count"] == 1 else "s")
        parts.append(_text(MARGIN, y, noun, _fit(noun, W - 2 * MARGIN, 72), TEXT, 700))
        y += 64
        parts.append(_text(MARGIN, y, "The amount shows up when we claim it.", 40, MUTED))

    y += 80
    x = MARGIN
    for asset in f["assets"]:
        width = int(len(asset) * 0.56 * 32) + 56
        if x + width > W - MARGIN:
            x, y = MARGIN, y + 84
        parts.append(
            f'<rect x="{x}" y="{y}" width="{width}" height="64" rx="32" fill="#ffffff" '
            'fill-opacity="0.08" stroke="#ffffff" stroke-opacity="0.25"/>'
        )
        parts.append(_text(x + width // 2, y + 43, asset, 32, TEXT, 600, anchor="middle"))
        x += width + 16
    if detail:
        y = min(y + 150, FOOT - 100)
        parts.append(_text(MARGIN, y, f"“{detail}”", _fit(detail, W - 2 * MARGIN, 52), TEXT, 500, italic=True))

    foot = FOOT
    parts.append(_text(MARGIN, foot, "Search your family's forgotten money", 44, TEXT, 700))
    parts.append(_text(MARGIN, foot + 56, "on the official RBI, SEBI, IRDAI and IEPF portals", 34, MUTED))
    parts.append(f'<circle cx="{MARGIN + 12}" cy="{foot + 125}" r="12" fill="{BLUE}"/>')
    brand = "DoAide Reclaim" + (f"  ·  {url}" if url else "")
    parts.append(_text(MARGIN + 36, foot + 137, brand, 36, TEXT, 700))
    small = "Found on official portals. Claims go directly to the bank, company, insurer or fund house."
    for i, line in enumerate(textwrap.wrap(small, 70)):
        parts.append(_text(MARGIN, foot + 185 + i * 30, line, 22, MUTED, opacity=0.8))
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DoAide Reclaim card</title>
<style>
body{{margin:0;background:#111;color:#eee;font-family:system-ui,sans-serif;display:flex;
flex-direction:column;align-items:center;gap:16px;padding:16px}}
#card svg{{width:min(100%,540px);height:auto;border-radius:18px}}
button{{font-size:18px;padding:12px 22px;border-radius:999px;border:0;background:#0a66ff;color:#fff}}
</style></head><body>
<div id="card">{svg}</div>
<button id="save">Save or share as PNG</button>
<script>
document.getElementById("save").onclick = function () {{
  var svg = document.querySelector("#card svg");
  var img = new Image();
  img.onload = function () {{
    var canvas = document.createElement("canvas");
    canvas.width = {w}; canvas.height = {h};
    canvas.getContext("2d").drawImage(img, 0, 0, {w}, {h});
    canvas.toBlob(function (blob) {{
      var file = new File([blob], "reclaim-card.png", {{type: "image/png"}});
      if (navigator.canShare && navigator.canShare({{files: [file]}})) {{
        navigator.share({{files: [file]}}).catch(function () {{}});
        return;
      }}
      var link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = "reclaim-card.png";
      link.click();
    }}, "image/png");
  }};
  img.src = "data:image/svg+xml;charset=utf-8," +
    encodeURIComponent(new XMLSerializer().serializeToString(svg));
}};
</script>
</body></html>
"""


def page(svg_text: str) -> str:
    return PAGE.format(svg=svg_text, w=W, h=H)


def find_chrome() -> Optional[str]:
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"):
        found = shutil.which(name)
        if found:
            return found
    for path in CHROME_PATHS:
        if Path(path).exists():
            return path
    return None


def render_png(svg_text: str, out_png: Path, chrome: Optional[str] = None, size=(W, H)) -> Path:
    chrome = chrome or find_chrome()
    if not chrome:
        raise CardError("a PNG needs Chrome or Chromium; open the .html card and use its save button instead")
    out_png = Path(out_png).resolve()
    with tempfile.TemporaryDirectory() as tmp:
        sheet = Path(tmp) / "card.html"
        sheet.write_text(
            '<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;padding:0;'
            f'background:#000}}svg{{display:block}}</style></head><body>{svg_text}</body></html>',
            encoding="utf-8",
        )
        command = [
            chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
            "--no-default-browser-check", "--force-device-scale-factor=1",
            f"--user-data-dir={Path(tmp) / 'profile'}", f"--window-size={size[0]},{size[1]}",
            f"--screenshot={out_png}", sheet.as_uri(),
        ]
        try:
            subprocess.run(command, check=True, capture_output=True, timeout=90)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            detail = (getattr(exc, "stderr", b"") or b"").decode("utf-8", "replace").strip()[-300:]
            raise CardError(f"Chrome could not render the PNG ({exc.__class__.__name__}) {detail}") from None
    if not out_png.exists():
        raise CardError(f"Chrome did not write {out_png}")
    return out_png
