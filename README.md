# DoAide Reclaim

**Find the money your family forgot.** One guided scan of a whole family (parents, grandparents,
relatives who have died) across India's official unclaimed-asset portals: RBI UDGAM for bank
deposits, IEPF for shares and dividends, LIC and IRDAI Bima Bharosa for insurance, SEBI MITRA for
mutual funds. The family types every identity detail into the official sites themselves. Reclaim
tells them where to look and what each site needs, and turns a find into a card worth sharing.

> Status: phase 1, the hit-rate test. This is an operator console (Python, standard library only)
> for running guided scans with 20 families: checklists, result logging, the shareable card and the
> go/no-go report. It does not file claims yet. Portal requirements were checked against official
> sources on 29 Oct 2026, except IEPF's search fields: iepf.gov.in refuses automated access, so they
> are marked unverified. It has not yet been run with a real family.

## Why

* ₹86,917 crore of unclaimed bank deposits sat in RBI's DEA Fund on 30 June 2026. The IEPF
  Authority estimates another ₹1.84 lakh crore in unclaimed shares and dividends. Insurers hold
  ₹8,974 crore and mutual funds ₹3,749 crore.
* People do come for it. The government's three-month "Your Money, Your Right" campaign
  (Oct–Dec 2025) had returned ₹5,777 crore on 22.95 lakh claims by February 2026 (about ₹25,000
  per claim).
* Searching is still hard. There are four regulators and five sites, each with its own login and its
  own required fields. UDGAM only searches, it doesn't settle claims, and a grandparent who died
  before PAN existed has no PAN to enter. The government's own gateway just links out to the
  separate portals.

## What a scan covers

| Search | Covers | Needs, besides the person's name | A hit shows |
|---|---|---|---|
| [RBI UDGAM](https://udgam.rbi.org.in/unclaimed-deposits/#/login) | bank deposits in RBI's DEA Fund (30 banks, about 90% by value) | the bank, plus one of PAN, date of birth, driving licence, voter ID or passport, or else an old address | name, bank, place and UDRN; **no amount** |
| [IEPF](https://www.iepf.gov.in/) | shares, dividends, matured company deposits | company and folio from old certificates help; *exact fields unverified* | company, amount and shares |
| [LIC](https://licindia.in/unclaimed-amounts-of-policyholders) | LIC policy payouts | date of birth, PAN or policy number (any two fields including the name) | unclaimed amounts, refreshed every six months |
| [IRDAI Bima Bharosa](https://bimabharosa.irdai.gov.in/Home/UnclaimedAmountsQuery) | other insurers | policy number, date of birth, PIN/district/state | the insurer replies |
| [SEBI MITRA](https://app.mfcentral.com/links/mitra) | mutual funds | one of PAN, mobile, email, date of birth or bank account, plus an address or nominee; or a full old address | fund houses where a folio probably exists; **no amount** |

`python3 -m reclaim portals --sources` prints the same table with the source behind every claim.

Two consequences shape the product. First, most finds arrive **without a rupee figure**: UDGAM and
MITRA confirm that something exists, and the amount only appears when the family claims. The card
therefore says "2 forgotten family accounts" rather than guessing, and the report counts how many
finds came with an amount. Second, IEPFA tells claimants to file Form IEPF-5 themselves and warns
against middlemen. Reclaim is built to help families file their own claims, never to broker them.

## Quick start (operator)

```sh
git clone https://github.com/DoAideAi/DoAide-Reclaim && cd DoAide-Reclaim
python3 -m reclaim new --consent --channel friends          # after reading the consent script -> R001
python3 -m reclaim member R001 --relation father --deceased --knows dob,address,shares
python3 -m reclaim member R001 --relation grandmother --deceased --knows address --skip mitra
python3 -m reclaim checklist R001                            # paste into WhatsApp
python3 -m reclaim record R001 --reply reply.txt             # their reply, pasted into a file
python3 -m reclaim done R001 --minutes 40
python3 -m reclaim card R001 --png --detail "Dad's 1994 shares"
python3 -m reclaim shared R001 yes
python3 -m reclaim report                                    # hit rate, share rate, verdict
python3 -m reclaim delete R001 --yes                         # erase when asked or when the test ends
```

The family replies one line per search: `m1 udgam found`, `m1 iepf found 3.2 lakh`, `m1 lic no`,
`m2 mitra blocked otp`. Amounts can be written however people write them (`1,20,000`, `42k`,
`3.2 lakh`, `~1.5 lakh` for an estimate). A reply is applied in full or not at all, and the error
names the line. Cards (`card.svg`, a `card.html` with a save/share button, and `card.png` when
Chrome or Chromium is installed) go to `data/cards/<case>/`.

How to run the 20-family test, the consent script and the decision rule are in
[docs/HIT_RATE_TEST.md](docs/HIT_RATE_TEST.md).

## Privacy

* Reclaim records **which** details a family has ("knows a date of birth"), never the details. PAN,
  Aadhaar, dates of birth, account and policy numbers are typed only on the official sites.
* Every free-text field (recruitment channel, the card's detail line, its link) is checked for
  anything that looks like a PAN, Aadhaar, mobile, account number, email or date, and refused.
* Cases are pseudonymous: `R001`, relation labels and results. Keep the mapping from case to person
  outside this tool. No case can be created without recorded consent (`--consent`, script v1). Case
  files are written owner-only (0600) under `data/`, which is git-ignored, and `delete` erases a case.
* The card never shows names, only what was found and which kind of asset.

## Phase 2, not built

The plan is claim packets on the DoAide Suite's ClaimPack engine: entitlement-letter requests, Form
IEPF-5 preparation, indemnity bond and advance receipt checklists, and bank claim letters with the
UDRN. It is gated on the hit-rate test. The revenue model is also open. A success fee looks like the
"middleman" IEPFA warns about, so phase 2 must stay a self-filing assistant.

## Development

```sh
python3 -m unittest discover -s tests -v     # behaviour tests, stdlib only, Python 3.9+
python3 -m reclaim portals --sources         # re-check these against the live sites before launch
```

## Sources

* Unclaimed deposits ₹86,917 crore (30 Jun 2026): [Rajya Sabha reply, 11 Aug 2026](https://sansad.in/getFile/annex/271/AU2636_cT4tJc.pdf?source=pqars)
* Campaign returns, insurance and mutual fund figures: [PIB, 24 Mar 2026](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2244475)
* IEPF ₹1.84 lakh crore estimate: [Forbes India, Jan 2026](https://www.forbesindia.com/article/30-under-30-2026/pooja-malik-recovering-your-assets/2990451/1)
* UDGAM inputs and results: [RBI FAQ](https://rbidocs.rbi.org.in/rdocs/faqs/PDFs/FAQONUDGAMPORTAL.PDF), [ET on the result grid](https://economictimes.indiatimes.com/wealth/save/more-than-8-lakh-people-got-unclaimed-deposits-back-from-bank-via-udgam/articleshow/122998219.cms)
* MITRA: [SEBI circular, 12 Feb 2025](https://www.sebi.gov.in/legal/circulars/feb-2025/service-platform-for-investors-to-trace-inactive-and-unclaimed-mutual-fund-folios-mitra-mutual-fund-investment-tracing-and-retrieval-assistant-_91847.html)
* IEPF-5 claim steps: [Form IEPF-5 (Gazette, 2025)](https://egazette.gov.in/WriteReadData/2025/266617.pdf); LIC and Bima Bharosa fields were read from the live forms on 29 Oct 2026.

MIT licence. Not affiliated with RBI, SEBI, IRDAI, the IEPF Authority, LIC or any bank.
