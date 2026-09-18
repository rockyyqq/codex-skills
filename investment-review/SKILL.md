---
name: investment-review
description: Review one investment end to end - what it is, what the case claims, whether the claim is checkable, whether it addresses the price, what the price history shows, how the valuation compares with the alternatives, and whether the household already owns it. Use for "is X worth holding", "should I buy X", "how about X", "would you change your answer on X". Covers shares, indices, funds, ETFs, deposits, bonds and leveraged products. Not for portfolio construction or allocation (use wealth-advisory), not for appraising research evidence (use research), and not for a pure chart question with no claim attached (use technical-analysis).
---

# Investment Review

Review one investment. Output is a single document: what the instrument is, what
the case for it claims, what the price history shows, what it is worth against
the alternatives, and whether the household already owns it.

The review ends by handing the decision to the plan. It does not make it.

## The rule that holds this together

**Report the case reading and the price reading in separate sections. Never
combine them into a verdict. Where they disagree, name the disagreement and
stop.**

The failure this prevents is **cross-domain false confirmation** - a
beaten-down chart making a weak thesis feel confirmed, or a rigorous-sounding
thesis making a downtrend feel like an opportunity. **Price and narrative
agreeing is one piece of evidence, not two.** It is the same error as stacking
three indicators, extended to fundamentals.

A worked case: the chart showed a year of selling on a tenth of normal volume
while the bull case claimed the market was wrong. **The disagreement was the
finding.** Averaging the two readings would have destroyed the answer.

## Workflow

**0. What is this instrument?** Before anything else. A share, an index, a fund,
a deposit, a bond, a leveraged product - each carries a different bundle of
checks, and two similarly named indices can be entirely different things.
Read `references/instrument-types.md` for the bundle that applies.

**1. The claim.** Source, date, the claimant's own words, restated as
predictions, and whether it is a claim or a decision.
Read `references/claim-intake.md`.

**2. Is it checkable?** Predictions with dates and numbers can be tested. Vague
ones get restated first, and the restatement is labelled as one.

**3. Does it address the price?** A thesis with no valuation is half an
argument, and the missing half decides the return.

**4. Does the mechanism support the conclusion?** One published bull case
argued for both doubled profit *and* a transition to low-capex maturity. Those
cannot both pay you.

**5. The price reading.** Delegate to the `technical-analysis` skill. Report its
output unmodified, under its own heading, with its timeframe and its
adjusted/unadjusted basis stated.

**6. Valuation against the alternative.** Earnings yield against the hurdle
rate; the multiple against peers. Read `references/valuation-spreads.md`.

**7. Look-through.** Does the household already own this exposure, through a
fund, an index or another holding? This step ended three separate reviews in one
week with the answer "you already own it".

**8. What this settles, and what it does not.** Name the open questions
explicitly. Then hand the decision to the plan.

## Opening summary block

Eight rows, no score. A rating is a combined verdict, which is the one thing
this review forbids - and a headline number travels without its caveats.

```
| | |
|---|---|
| **Instrument** | What it is, in one line |
| **Claim as stated** | Whose, or "none" |
| **Claim testability** | Checkable / Partly / Unfalsifiable |
| **Evidence verified** | n of 8 sections checked against source |
| **Price reading** | One line, from technical-analysis, unmodified |
| **Valuation spread** | vs the hurdle rate, with the hurdle named |
| **Already owned** | Yes/No, with the fund and rank |
| **Action** | None indicated / Available / Blocked by rule |
```

## Non-negotiables

**No claim, no review.** If nobody has stated one, that is the finding, and it
is written first. An absent claim is not a reason to skip section 1 - it is the
most useful thing the review can produce.

**A decision is not a claim.** "Held for life, no exit condition" is a
decision. It stands on a claim, and if that claim is unrecorded the position
cannot be tested, cannot be exited on evidence, and cannot be added to on
principle.

**Include the assistant's own prior claims.** A recommendation made last week is
a claim like any other, with the same requirement for a source and a date. In
one worked example the only stated claim was the assistant's, and the
load-bearing part of it had already been refuted by the household's own
evidence.

**Steelman.** Review the strongest version of the case. Refuting a straw man
costs a page and proves nothing.

**Valuation is relative.** An earnings yield means nothing alone. Name the
hurdle rate and state the spread.

**Declare the adjustment basis before reading any level.** The same security, on
the same day, produced "extremely oversold" from an unadjusted series and
"mid-range" from an adjusted one. An unadjusted series carries an artificial
fall on the ex-dividend date that never happened as a market move.

**Reconcile sources that disagree.** When two feeds give different highs or
different readings, find the cause before reporting either. Dividing the
trailing dividend out of the higher figure is often enough to close the gap.

**Peers are fetched, never recalled.** A multiple quoted from memory is not
evidence.

**Every figure carries a source and a date.** Where a date is unavailable - some
forums serve none to a logged-out browser - say the date is missing rather than
inferring one.

**Sizing does not travel.** No entry, stop, target, share count or position
size. Those belong to a trading decision and need an account and a risk figure.

**Say CANNOT JUDGE when it applies.** No claim, no reachable data, no
statements - say so plainly rather than assembling a thin review that looks
complete.

## Boundaries

| Skill | Question |
|---|---|
| `investment-review` | Is this investment, or this claim about it, sound? |
| `technical-analysis` | What does the price history show, with no claim attached? |
| `wealth-advisory` | Does it belong in this plan, and at what size? |

Do not put a price reading into the plan's language of limits and targets. A
trend is an observation; the agreed mandate prevails over it.

## Scripts

`scripts/appraise.py` builds the spread table - earnings yield and dividend
yield against the hurdle rate, and against a peer set - and runs the look-through
against the household's holdings file. It records the claim so a later review
can check whether the prediction came true.

The price reading comes from `technical-analysis/scripts/analyse.py`. **Do not
reimplement it here.** Two copies of an indicator set drift apart.

## References

- `references/instrument-types.md` - the review bundle for each instrument type.
  Read the section for the instrument in front of you.
- `references/claim-intake.md` - the four sources, the three states, and two
  worked examples in full.
- `references/valuation-spreads.md` - earnings yield, dividend yield, the hurdle
  rate, and what a spread over cash means.
- `references/sources.md` - what each data source covers, what it fails on, and
  the traps found by using them.
