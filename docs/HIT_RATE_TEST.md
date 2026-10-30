# The hit-rate test

Phase 2 (claim paperwork) only gets built if this test says families actually find money, and
that the people who find it want to tell others.

## What we measure

| Measure | Definition | Why |
|---|---|---|
| Family hit rate | families with at least one find / families that completed at least one search | is there anything to find? |
| Finds with an amount | finds that came with a rupee figure / all finds | can the card say "₹X"? UDGAM and MITRA never show one |
| Share rate | finding families who shared their card / finding families | does the result spread on its own? |
| Blocks per portal | searches stopped by OTP, missing details, name mismatch, a site being down, or difficulty | where the guide must get better |
| Minutes per family | the family's own estimate, recorded with `done --minutes` | is the scan an evening or a weekend? |

A **find** is any match: a UDGAM UDRN, an IEPF entry, an LIC or insurer amount, or a MITRA fund
house. It is not money in hand. Claims take weeks to months and are out of scope for this test.

## Proposed decision rule

**GO to phase 2** when at least 20 families have searched, at least 10% of them found something,
and at least 30% of the finding families shared their card. `reclaim report` applies the rule; the
thresholds can be changed with `--target`, `--min-hit-rate` and `--min-share-rate`.

With 20 families every rate is directional. For example, 2 finds out of 20 has a 95% interval of
3% to 30%, and the report prints that interval next to the hit rate. Friends and family also skew
urban and salaried, so recruit from at least three channels and record each with `--channel`.

## Running it

1. **Recruit** 20 families from at least three channels (family, friends, X/LinkedIn, a WhatsApp
   group). Older relatives who have died are the most promising searches. Ask in advance whether
   anyone kept old passbooks, share certificates or policies. Ready-to-send invites in English and
   Hindi, and the steps for results sent from reclaim.doaide.com, are in [RECRUITING.md](RECRUITING.md).
2. **Consent.** Read or send the script below, then run `reclaim new --consent --channel <where>`.
   Families who use the page do steps 3 to 5 there: send them the script when their results arrive,
   and record nothing until they agree.
3. **Roster.** Run `reclaim member` once per relative, with `--knows` set to the details the family
   *has* (never the values) and `--skip` for portals that clearly do not apply.
4. **Checklist.** Send them the output of `reclaim checklist R00N`. A NOT READY line tells them which
   detail to dig up first.
5. **Results.** Paste their reply into a file and run `reclaim record R00N --reply file`. When they
   stop, run `reclaim done R00N --minutes <their estimate>`. If a bank later tells them an amount,
   record it again: `reclaim record R00N m1 udgam found --amount 42000`.
6. **Card.** Run `reclaim card R00N --png`, add `--detail` only with a line the family wrote, and send
   them `card.png`. A week later, ask whether they shared it and record `reclaim shared R00N yes|no`.
7. **Decide.** Run `reclaim report`, then delete every case (`reclaim delete R00N --yes`) once the
   numbers are written down.

## Consent script v1

> We are testing a free guide that helps families search the government's official portals (RBI,
> SEBI, IRDAI, IEPF and LIC) for money a relative may have left behind. You do the searches yourself
> on those official websites. We never ask for PAN, Aadhaar, dates of birth, account or policy
> numbers, so please don't send them to us. We write down only which relatives you searched for
> (for example "father"), which kinds of details you had (not the details themselves), and what the
> portals showed: found or not found, and an amount only if you choose to tell us. If you find
> something, we can make an image without your name that you may share or not. You can ask us to
> delete your record at any time, and we will delete all records when the test ends. Is that okay?

## Known limits of the guide

* iepf.gov.in blocks automated reads, so the IEPF search fields have not been verified. The first
  family to search IEPF should note exactly what it asked for, and `reclaim/portals.py` should be
  updated with that.
* LIC refreshes its unclaimed list every six months. A miss today is not a miss forever.
* MITRA allows a limited number of searches per name per day, and its matches are "probable": the
  fund house confirms.
* IEPFA warns against middlemen. This test helps families search, and any claim is theirs to file.
