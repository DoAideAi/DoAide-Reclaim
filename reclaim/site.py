"""reclaim.doaide.com: the family-facing guide, built from the same portal registry as the CLI.

One static file with no server, no account and no third-party requests. The page keeps a family's
list on their own device and turns what they saw into reply lines that `reclaim record --reply`
reads, the list of relatives included. Regenerate with `python3 -m reclaim site` after any change
to reclaim/portals.py; a test fails while site/index.html is stale.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import cases, portals

SITE = Path(__file__).resolve().parent.parent / "site" / "index.html"
PUBLIC = ("id", "name", "asset", "url", "login", "needs", "needs_text", "hit_shows", "amount_on_hit")
REASONS = (
    ("otp", "The code (OTP) never came"),
    ("missing", "We don't have a detail it needs"),
    ("name", "The name doesn't match"),
    ("down", "The site was down"),
    ("hard", "Too hard to use"),
    ("other", "Something else"),
)


def data() -> dict:
    return {
        "checked": portals.CHECKED,
        "hub": portals.HUB_URL,
        "facts": portals.FACTS,
        "relations": list(cases.RELATIONS),
        "reasons": [list(pair) for pair in REASONS],
        "portals": [{key: p[key] for key in PUBLIC} for p in portals.PORTALS],
    }


def render() -> str:
    payload = json.dumps(data(), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return TEMPLATE.replace("__DATA__", payload).replace("__CHECKED__", portals.CHECKED)


def write(path: Path = SITE) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(), encoding="utf-8")
    return path


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DoAide Reclaim: find the money your family forgot</title>
<meta name="description" content="A free guide to search India's official unclaimed-money portals (RBI UDGAM, IEPF, LIC, IRDAI, SEBI MITRA) for every relative in one evening. No account, nothing stored on a server.">
<meta property="og:title" content="Find the money your family forgot">
<meta property="og:description" content="Old bank accounts, shares, insurance and mutual funds nobody claimed. Search for every relative on the official portals in one evening. Free.">
<meta property="og:url" content="https://reclaim.doaide.com/">
<meta property="og:type" content="website">
<style>
  :root { --fg:#111; --muted:#5b6560; --line:#e3e6e4; --accent:#0a66ff; --on-accent:#fff; --bg:#fff; --card:#f6f8f7; --gold:#a66f00; --warn:#9a3412; --ok:#166534 }
  @media (prefers-color-scheme: dark) {
    :root { --fg:#eee; --muted:#a7b3ad; --line:#2a302d; --accent:#6ea8ff; --on-accent:#08152b; --bg:#0d0f0e; --card:#151918; --gold:#ffd166; --warn:#fdba74; --ok:#86efac }
  }
  * { box-sizing:border-box }
  body { margin:0; font:17px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans", Helvetica, Arial, sans-serif; color:var(--fg); background:var(--bg) }
  main { max-width:760px; margin:0 auto; padding:48px 18px 80px }
  h1 { font-size:2.2rem; line-height:1.15; margin:0 0 .4em; letter-spacing:-.01em }
  h2 { font-size:1.3rem; margin:2.4em 0 .5em }
  h3 { font-size:1.08rem; margin:0 }
  p { margin:.5em 0 }
  p.lead { font-size:1.15rem; color:var(--muted); margin:0 0 1.2em }
  a { color:var(--accent) }
  .stats { display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:10px; padding:0; margin:1.2em 0; list-style:none }
  .stats li { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:12px 14px; font-size:.92rem; color:var(--muted) }
  .stats b { display:block; font-size:1.25rem; color:var(--gold) }
  .small { color:var(--muted); font-size:.9rem }
  .note { border-left:3px solid var(--accent); padding:4px 12px; margin:1em 0; color:var(--muted) }
  form.add { display:flex; flex-wrap:wrap; gap:10px; align-items:center; background:var(--card); border:1px solid var(--line); border-radius:12px; padding:14px }
  select, input[type=text], button { font:inherit; color:inherit }
  select, input[type=text] { padding:9px 10px; border:1px solid var(--line); border-radius:8px; background:var(--bg) }
  button { cursor:pointer; border-radius:8px; border:1px solid var(--line); background:var(--bg); padding:9px 14px }
  button.primary, a.cta { background:var(--accent); border-color:var(--accent); color:var(--on-accent); font-weight:600; text-decoration:none; display:inline-block; padding:10px 16px; border-radius:8px }
  button.link { border:0; background:none; color:var(--muted); text-decoration:underline; padding:4px }
  label.check { display:inline-flex; gap:6px; align-items:center }
  .member { border:1px solid var(--line); border-radius:12px; margin:16px 0; overflow:hidden }
  .member > header { display:flex; justify-content:space-between; align-items:center; gap:8px; background:var(--card); padding:12px 14px; border-bottom:1px solid var(--line) }
  fieldset { border:0; margin:0; padding:12px 14px 4px }
  legend { font-size:.92rem; color:var(--muted); padding:0; margin-bottom:6px }
  .chips { display:flex; flex-wrap:wrap; gap:8px }
  .chips label { border:1px solid var(--line); border-radius:999px; padding:5px 12px; font-size:.9rem; display:inline-flex; gap:6px; align-items:center; cursor:pointer }
  .chips input:checked + span { font-weight:600 }
  ol.places { list-style:none; margin:0; padding:4px 14px 14px }
  .place { border-top:1px solid var(--line); padding:12px 0 }
  .place:first-child { border-top:0 }
  .place .head { display:flex; flex-wrap:wrap; gap:6px; align-items:baseline }
  .tag { font-size:.75rem; font-weight:700; letter-spacing:.04em; text-transform:uppercase; border-radius:999px; padding:2px 8px }
  .tag.ready { color:var(--ok); border:1px solid var(--ok) }
  .tag.notready { color:var(--warn); border:1px solid var(--warn) }
  .warn { color:var(--warn) }
  .result { display:flex; flex-wrap:wrap; gap:8px; align-items:center; margin-top:8px }
  .result label { border:1px solid var(--line); border-radius:8px; padding:6px 12px; display:inline-flex; gap:6px; align-items:center; cursor:pointer }
  .result label:has(input:checked) { border-color:var(--accent); font-weight:600 }
  .result input[type=text] { flex:1 1 220px }
  .found { color:var(--gold); font-weight:700 }
  pre { background:var(--card); border:1px solid var(--line); padding:12px 14px; border-radius:10px; overflow:auto; font-size:.88rem; white-space:pre-wrap }
  .row { display:flex; flex-wrap:wrap; gap:10px; align-items:center }
  footer { margin-top:3em; color:var(--muted); font-size:.88rem; border-top:1px solid var(--line); padding-top:1.2em }
  :focus-visible { outline:3px solid var(--accent); outline-offset:2px }
</style>
</head>
<body>
<main>
  <h1>Find the money your family forgot.</h1>
  <p class="lead">Old bank accounts, shares, insurance payouts and mutual funds that nobody claimed are held for the family, often for decades. Search for every relative on the official government portals in one evening. Free, with no account.</p>
  <ul class="stats">
    <li><b>₹86,917 crore</b>in unclaimed bank deposits with RBI (June 2026)</li>
    <li><b>₹1.84 lakh crore</b>in unclaimed shares and dividends (IEPF Authority estimate)</li>
    <li><b>₹12,700+ crore</b>in unclaimed insurance and mutual funds (PIB, March 2026)</li>
  </ul>
  <p class="note">Type PAN, Aadhaar, dates of birth and account numbers only on the official sites. This page never asks for them and has no server storage: your list stays on this device until you clear it.</p>

  <h2>1. Who should you look for?</h2>
  <p class="small">Start with relatives who have died, then elders who had bank accounts, shares, LIC policies or mutual funds.</p>
  <form class="add" id="add">
    <label for="relation">Relative</label>
    <select id="relation"></select>
    <label class="check"><input type="checkbox" id="late"> has passed away</label>
    <button class="primary" type="submit">Add</button>
  </form>

  <div id="family"></div>

  <h2>2. Send what you found</h2>
  <p class="small">These lines say which relatives you searched for, which kinds of details you had and what each site showed. They contain no names, numbers or dates. Send them to whoever shared this page with you.</p>
  <pre id="reply" aria-live="polite"></pre>
  <div class="row">
    <button class="primary" type="button" id="copy">Copy</button>
    <a class="cta" id="whatsapp" href="#" target="_blank" rel="noopener noreferrer">Send on WhatsApp</a>
    <button class="link" type="button" id="clear">Clear everything</button>
    <span class="small" id="status"></span>
  </div>

  <h2>Where this searches</h2>
  <div id="sources"></div>
  <p class="small">The government links all of these from <a id="hub" rel="noopener noreferrer" target="_blank"></a>. A match is not money in hand: you claim it yourself from the bank, company, insurer or fund house, and the IEPF Authority asks claimants to file directly, without middlemen.</p>
  <p class="small">Figures on this page: deposits from a <a href="https://sansad.in/getFile/annex/271/AU2636_cT4tJc.pdf?source=pqars" rel="noopener noreferrer" target="_blank">Rajya Sabha reply (Aug 2026)</a>; insurance (₹8,974 crore) and mutual funds (₹3,749 crore) from <a href="https://www.pib.gov.in/PressReleasePage.aspx?PRID=2244475" rel="noopener noreferrer" target="_blank">PIB (Mar 2026)</a>; the IEPF estimate as reported by <a href="https://www.forbesindia.com/article/30-under-30-2026/pooja-malik-recovering-your-assets/2990451/1" rel="noopener noreferrer" target="_blank">Forbes India (Jan 2026)</a>.</p>

  <footer>
    Portal details checked __CHECKED__. Not affiliated with RBI, SEBI, IRDAI, the IEPF Authority, LIC or any bank.
    Open source: <a href="https://github.com/DoAideAi/DoAide-Reclaim">github.com/DoAideAi/DoAide-Reclaim</a>. A DoAide project.
  </footer>
</main>
<script>
(function () {
  "use strict";
  var DATA = __DATA__;
  var KEY = "reclaim-v1";
  var UNITS = { "": 1, k: 1e3, thousand: 1e3, l: 1e5, lac: 1e5, lacs: 1e5, lakh: 1e5, lakhs: 1e5,
                cr: 1e7, crore: 1e7, crores: 1e7 };
  var state = load();

  function load() {
    try {
      var saved = JSON.parse(localStorage.getItem(KEY) || "null");
      if (saved && Array.isArray(saved.members)) { return saved; }
    } catch (e) { /* private mode or corrupt: start fresh */ }
    return { members: [] };
  }

  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) { /* storage unavailable */ }
  }

  function el(tag, attrs, children) {
    var node = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (key) {
      var value = attrs[key];
      if (key === "text") { node.textContent = value; }
      else if (key === "class") { node.className = value; }
      else if (key.indexOf("on") === 0) { node.addEventListener(key.slice(2), value); }
      else if (value === true) { node.setAttribute(key, ""); }
      else if (value !== false && value !== null && value !== undefined) { node.setAttribute(key, value); }
    });
    (children || []).forEach(function (child) {
      if (child) { node.appendChild(typeof child === "string" ? document.createTextNode(child) : child); }
    });
    return node;
  }

  function cap(text) { return text.charAt(0).toUpperCase() + text.slice(1); }
  function relationLabel(relation) { return relation === "self" ? "Me" : cap(relation); }

  function isReady(portal, knows) {
    return portal.needs.some(function (alternative) {
      return alternative.every(function (group) {
        return group.some(function (fact) { return knows.indexOf(fact) >= 0; });
      });
    });
  }

  // Mirrors reclaim.money.parse_amount: 42000, 1,20,000, 42k, 3.2 lakh, ~1.5 cr.
  function parseAmount(text) {
    var t = String(text || "").trim().toLowerCase();
    var estimate = /^(~|about|approx)/.test(t);
    t = t.replace(/^(~|about|approx\.?|approximately)\s*/, "").replace(/^(₹|rs\.?|inr)\s*/, "")
         .replace(/,/g, "").trim();
    var match = /^(\d+(?:\.\d+)?)\s*([a-z]*)$/.exec(t);
    if (!match || !Object.prototype.hasOwnProperty.call(UNITS, match[2])) { return null; }
    var rupees = Math.round(parseFloat(match[1]) * UNITS[match[2]]);
    return rupees > 0 ? { rupees: rupees, estimate: estimate } : null;
  }

  function replyLines() {
    var lines = ["# Reclaim results from reclaim.doaide.com"];
    state.members.forEach(function (m, i) {
      var line = "m" + (i + 1) + " is " + m.relation + (m.late ? " late" : "");
      if (m.knows.length) { line += " knows " + m.knows.join(","); }
      lines.push(line);
    });
    state.members.forEach(function (m, i) {
      DATA.portals.forEach(function (p) {
        var r = m.results[p.id];
        if (!r || !r.status) { return; }
        var code = "m" + (i + 1) + " " + p.id;
        if (r.status === "found") {
          var amount = r.amount ? parseAmount(r.amount) : null;
          lines.push(code + " found" + (amount ? " " + (amount.estimate ? "~" : "") + amount.rupees : ""));
        } else if (r.status === "not_found") {
          lines.push(code + " no");
        } else {
          lines.push(code + " blocked " + (r.reason || "other"));
        }
      });
    });
    return lines.join("\n");
  }

  function renderReply() {
    var text = state.members.length ? replyLines() : "Add a relative above to start.";
    document.getElementById("reply").textContent = text;
    document.getElementById("whatsapp").href = "https://wa.me/?text=" + encodeURIComponent(text);
    var marked = 0, found = 0;
    state.members.forEach(function (m) {
      Object.keys(m.results).forEach(function (id) {
        if (m.results[id].status) { marked += 1; }
        if (m.results[id].status === "found") { found += 1; }
      });
    });
    document.getElementById("status").textContent =
      marked ? marked + " searches marked, " + found + " found" : "";
    save();
  }

  function changed() { renderFamily(); renderReply(); }

  function placeItem(m, index, portal) {
    var result = m.results[portal.id] || {};
    var ready = isReady(portal, m.knows);
    var group = "r-m" + (index + 1) + "-" + portal.id;
    var head = el("div", { class: "head" }, [
      el("strong", { text: portal.asset }), " · ",
      el("a", { href: portal.url, target: "_blank", rel: "noopener noreferrer", text: portal.name }),
      el("span", { class: "tag " + (ready ? "ready" : "notready"), text: ready ? "ready" : "not ready yet" })
    ]);
    var needs = ready
      ? el("p", { text: "Enter " + portal.needs_text + "." })
      : el("p", { class: "warn", text: "Needs " + portal.needs_text +
          ". Ask relatives, or look in old passbooks, policies and certificates." });
    var info = el("p", { class: "small", text: "A match shows " + portal.hit_shows + "." +
      (portal.login ? " To search: " + portal.login + "." : "") });
    var choices = [["found", "Found"], ["not_found", "Not found"], ["blocked", "Stuck"]].map(function (c) {
      return el("label", {}, [
        el("input", { type: "radio", name: group, value: c[0], checked: result.status === c[0],
          onchange: function () {
            m.results[portal.id] = { status: c[0] };
            changed();
          } }),
        c[1]
      ]);
    });
    var extra = [];
    if (result.status === "found" && portal.amount_on_hit !== false) {
      var amount = el("input", { type: "text", inputmode: "decimal", value: result.amount || "",
        "aria-label": "Amount the site showed for " + portal.name,
        placeholder: "Amount it showed (optional), e.g. 1.2 lakh",
        oninput: function () {
          result.amount = amount.value;
          amount.setCustomValidity(amount.value && !parseAmount(amount.value) ? "Try 42000, 1,20,000 or 3.2 lakh" : "");
          amount.reportValidity();
          renderReply();
        } });
      extra.push(amount);
    }
    if (result.status === "found") {
      extra.push(el("span", { class: "found", text: "Found. Note what the site shows; you claim it yourself." }));
    }
    if (result.status === "blocked") {
      var select = el("select", { "aria-label": "Why were you stuck on " + portal.name,
        onchange: function () { result.reason = select.value; renderReply(); } },
        DATA.reasons.map(function (pair) {
          return el("option", { value: pair[0], text: pair[1], selected: (result.reason || "other") === pair[0] });
        }));
      extra.push(select);
    }
    return el("li", { class: "place" }, [head, needs, info,
      el("div", { class: "result", role: "group", "aria-label": "What did " + portal.name + " show?" },
        choices.concat(extra))]);
  }

  function memberCard(m, index) {
    var title = "m" + (index + 1) + " · " + relationLabel(m.relation) + (m.late ? " (passed away)" : "");
    var chips = Object.keys(DATA.facts).map(function (fact) {
      return el("label", {}, [
        el("input", { type: "checkbox", checked: m.knows.indexOf(fact) >= 0, onchange: function (e) {
          m.knows = m.knows.filter(function (f) { return f !== fact; });
          if (e.target.checked) { m.knows.push(fact); }
          m.knows.sort(function (a, b) {
            return Object.keys(DATA.facts).indexOf(a) - Object.keys(DATA.facts).indexOf(b);
          });
          changed();
        } }),
        el("span", { text: cap(DATA.facts[fact]) })
      ]);
    });
    return el("article", { class: "member" }, [
      el("header", {}, [
        el("h3", { text: title }),
        el("button", { class: "link", type: "button", text: "Remove",
          "aria-label": "Remove " + relationLabel(m.relation),
          onclick: function () { state.members.splice(index, 1); changed(); } })
      ]),
      el("fieldset", {}, [
        el("legend", { text: "Which details do you have? Tick them; type them only on the official sites." }),
        el("div", { class: "chips" }, chips)
      ]),
      el("ol", { class: "places" }, DATA.portals.map(function (p) { return placeItem(m, index, p); }))
    ]);
  }

  function renderFamily() {
    var family = document.getElementById("family");
    family.textContent = "";
    state.members.forEach(function (m, i) { family.appendChild(memberCard(m, i)); });
  }

  function renderSources() {
    var list = el("ul", {}, DATA.portals.map(function (p) {
      return el("li", {}, [el("a", { href: p.url, target: "_blank", rel: "noopener noreferrer", text: p.name }),
        " · " + p.asset]);
    }));
    document.getElementById("sources").appendChild(list);
    var hub = document.getElementById("hub");
    hub.href = DATA.hub;
    hub.textContent = DATA.hub.replace(/^https:\/\/(www\.)?/, "").replace(/\/$/, "");
  }

  var relation = document.getElementById("relation");
  DATA.relations.forEach(function (r) {
    relation.appendChild(el("option", { value: r, text: relationLabel(r), selected: r === "father" }));
  });

  document.getElementById("add").addEventListener("submit", function (e) {
    e.preventDefault();
    state.members.push({ relation: relation.value, late: document.getElementById("late").checked,
      knows: [], results: {} });
    document.getElementById("late").checked = false;
    changed();
    var cards = document.querySelectorAll(".member");
    cards[cards.length - 1].scrollIntoView({ behavior: "smooth", block: "start" });
  });

  document.getElementById("copy").addEventListener("click", function () {
    var text = document.getElementById("reply").textContent;
    var done = function () { document.getElementById("status").textContent = "Copied"; };
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(done, function () { selectReply(); });
    } else {
      selectReply();
    }
  });

  function selectReply() {
    var range = document.createRange();
    range.selectNodeContents(document.getElementById("reply"));
    var selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
    document.getElementById("status").textContent = "Selected: copy it with your keyboard or long-press";
  }

  document.getElementById("clear").addEventListener("click", function () {
    if (window.confirm("Remove every relative and result from this device?")) {
      state = { members: [] };
      changed();
    }
  });

  renderSources();
  changed();
})();
</script>
</body>
</html>
"""
