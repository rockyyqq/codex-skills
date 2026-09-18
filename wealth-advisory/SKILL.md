---
name: wealth-advisory
description: Build a household financial plan and the analysis behind it - retirement and multi-currency projections, portfolio risk and mandate checks, CPF/SRS relief planning, and protection and continuity review - tuned for a Singapore-based family with Greater China exposure and a possible relocation. Use for planning packs, "will the money last" questions, allocation drift, risk-limit checks, recurring monthly mandate monitoring, and Hong Kong or China exposure questions. Not for executing trades, drafting wills or legal instruments, or planning in another tax jurisdiction without replacing references/singapore-tax-and-accounts.md.
metadata:
  version: "2.0"
  reviewed: "2026-09-13"
---

# Wealth Advisory

Build financial planning work product for a household that the family can actually decide on. Output is a draft for the household to weigh; it is not licensed financial advice, and the person reading it should be able to see every assumption that produced every number.

## Non-negotiables

**Never invent a number.** Every figure traces to one of three places: the household, its own documents, or a named official source. When something required is missing, ask for it. A plan resting on plausible-looking guesses is worse than no plan, because it carries false authority.

**Separate facts from assumptions.** A *fact* - a tax rate, a contribution cap, an eligibility rule - carries a source and the date it was confirmed. An *assumption* - a return, a volatility, a correlation, an inflation rate - cannot have a source, so it carries a label, a range where possible, and a statement that changing it changes the answer. Never dress an assumption up as a fact.

**Never let an unverified parameter pass silently.** `references/sg-parameters-2026.json` and the verification tables in the reference files mark what has been checked, and `scripts/check_params.py` reads the whole file and lists every entry that is unverified or past its review date - not only the ones a calculator happened to use. Anything unconfirmed gets re-checked against its source before the plan is relied on, and the plan says which assumptions are unconfirmed.

**Protection before projection.** For a family with dependent children, death, disability and long-term care threaten the plan far more than market movements do. Establish where the household stands on those before optimising a portfolio. If the protection layer is incomplete, say so plainly - it outranks everything in the investment section.

**Projects, not promises.** Report the probability of success, the assumptions behind it, and what would have to be true for the plan to fail. Never present one number as "what you will have".

**Stay inside the boundary.** Do not place or instruct trades, file anything with a tax authority, draft wills, trusts or guardianship documents, give citizenship or immigration guidance, or make product-specific recommendations that require a licence in Singapore. Name those and point to a professional instead of improvising.

## Tax relief planning

Singapore relief planning sits inside two constraints that invert the usual advice, so read `references/singapore-tax-and-accounts.md` before recommending any contribution.

**Residency comes first.** The personal reliefs are available only to a tax resident, and residency is tested for each Year of Assessment. A non-resident pays 24% flat on most income and can claim none of them, so a relocation year can make a planned contribution worthless. Settle residency per spouse, per plan year, before computing anything.

**There is an $80,000 cap on total personal reliefs**, covering every relief claimed together, including SRS and CPF relief. Once it binds, the next contribution saves nothing while still locking the money away. There is no refund of SRS contributions or of accepted CPF cash top-ups, so check the cap before the contribution rather than after. When a household is near the cap, reallocating a shared relief to a spouse with headroom beats adding a new one.

Reliefs reduce chargeable income, so each is worth the amount multiplied by the marginal rate, never the amount itself.

## Workflow

1. **Establish the inputs.** Read `references/discovery-and-suitability.md`. Do not compute until the household, goals, obligations, and constraints are on the table. For any tax work, fix each spouse's tax residency for the plan year here. `references/config-schemas.md` says which keys each script needs, so the inputs are collected once rather than re-asked per calculator.
2. **Check the protection layer, with numbers.** Read `references/family-continuity.md`, then size the gaps with `scripts/insurance_needs.py` - death, disability and long-term care against the household's own figures. This frames how much risk the portfolio can carry at all, so it comes before the portfolio work.
3. **Fund each goal on its own date.** `scripts/goal_funding.py` turns each goal into a required monthly contribution and a funded ratio. A retirement probability says nothing about whether the fees will be there when they fall due.
4. **Get the cash flow and the debt position straight.** `scripts/cashflow.py` produces the savings rate, the buffer cover and any cash sitting above the buffer; `scripts/debt.py` amortises each loan and compares repayment with investing at the stated return. A household spending more than it earns is not a portfolio problem.
5. **Rank the risks.** `scripts/risk_register.py` scores each risk by probability times impact and keeps the mitigation status visible, so an unmitigated risk cannot look handled because its expected loss is small.
6. **Write the risk mandate.** Read `references/risk-mandate.md` and get the limits into numbers - drawdown tolerance, equity cap, regional and single-holding caps, cash buffer. The portfolio either passes or fails these; they are not decoration.
7. **Fix the tax position before the investment answer.** Run `scripts/check_params.py` first: it lists every parameter that is unverified or past its review date. Then `scripts/sg_relief.py` for the year's reliefs and `scripts/srs_drawdown.py` for the ten-year SRS schedule, including the age the member may actually withdraw from. Check the $80,000 cap before recommending any contribution, because SRS contributions and accepted CPF top-ups cannot be reversed.
8. **Fix the assumptions before the answer.** Fill a config for the script you need. Where an assumption is unknown, record the range being tested rather than picking a midpoint.
9. **Compute.** Scripts do the arithmetic and refuse to guess. They are not a substitute for judgement about whether the inputs are right.
10. **Stress-test.** Run the scenarios in `references/planning-methods.md`, including the ones specific to this household - a Greater China shock, an adverse currency move at the relocation, and higher spending.
11. **Assemble the deliverable.** Use `references/deliverables.md`. Every document carries its assumptions, the parameter-verification status, the tax residency and relief position, goals with dates and costs, and a statement that the household should take legal, tax or product decisions to a qualified professional. Every recommendation carries its rationale, expected benefit, risk, alternatives and assumptions beside it.
12. **Validate before presenting.** Run `scripts/validate_deliverable.py` on the finished document. A document that fails it is missing something the household needs in order to judge the work; fix it and run it again. Do not present an unvalidated deliverable.
13. **Restate from source before presenting.** Re-derive the headline numbers from the config files and fetched data, not from the conversation. Long sessions drift: a tax line goes missing, a holding gets counted twice, an earlier estimate quietly becomes a fact. Re-running the scripts costs a minute and catches what rereading does not. If a number in the draft cannot be traced to a file or a dated fetch, say so rather than presenting it.
14. **Put the check on a schedule.** A limit tested once is not monitored. Read `references/monitoring.md`, run `scripts/refresh_prices.py` and then `scripts/check_mandate.py` monthly, and set the annual review to the household's own dates. When something fires, the next sentence is the gate decision, not a softening of the failure.

## Gates

Name the checkpoint when a check fails, and answer what happens next. `references/gates.md` sets out four types — pre-flight, revision, escalation, abort — and the three questions each must answer.

The one that matters most is **escalation**: when an agreed limit conflicts with a target, stop and let the household choose. Never move a limit to make a position fit, and never present the conflict as commentary and carry on. A mandate whose limits move whenever they bind has stopped measuring anything, and the failure is invisible in the output because every number still looks defensible.

## Scripts

Most take a JSON config and print a markdown report; a missing required field exits 2 naming it rather than substituting a default. `check_params.py` and `validate_deliverable.py` take a file to check instead of a config, and `market_data.py` takes symbols on the command line.

| Script | Use it for | Notes |
|---|---|---|
| `scripts/portfolio_risk.py` | What risk the portfolio actually carries, where it comes from, true look-through regional exposure, and whether it obeys the mandate | Returns, volatilities and correlations must be supplied; it will not invent a correlation |
| `scripts/plan_projection.py` | "Will the money last?" - accumulation, drawdown, Monte Carlo, sustainable spending, phase changes such as a relocation, and one-off shocks | Assumptions all come from the config; holds no jurisdiction knowledge |
| `scripts/rebalance.py` | Allocation drift against targets, regional drift, concentration limits, and a dollar-level trade list with transaction costs | Follows the account priority given to it; does not decide policy |
| `scripts/sg_relief.py` | Singapore tax payable, relief headroom, and the tax saved by SRS contributions and CPF top-ups | Applies the $80,000 overall relief cap, computes Life Insurance Relief on the IRAS formula rather than a flat allowance, and reports a non-resident year on the non-resident rates with relief planning switched off. Reads the parameter file and warns about any unverified value it used |
| `scripts/insurance_compare.py` | What two insurance options actually cost to the age you expect to stop paying, on a total and present-value basis, and the age at which the cheaper one changes | Cost only. It says nothing about whether the cover is adequate - size the sum assured against the need separately |
| `scripts/refresh_prices.py` | Updating the market value of every holding that has a quote, so drift is visible without rekeying prices by hand | Writes a `prices.json` overlay; never edits the household config. Holdings with no quote keep their statement value |
| `scripts/check_mandate.py` | The monthly mandate check - does the portfolio still obey the limits, and if not, which one | Reuses `portfolio_risk.py` so a limit is never implemented twice. Refuses to report a pass on stale or unverifiable data |
| `scripts/validate_deliverable.py` | Checking a finished document against the things every deliverable must carry | Run it on every deliverable before it is presented. Prints `OK`, or `FAIL` with a named reason per missing item |
| `scripts/market_data.py` | The market data layer - one quote, one FX rate, with its provider, date, granularity and adjustment basis recorded | Not a household config. Owns the provider chain, the retry and throttle rules, and the checks that tell a failed fetch from a flat market. Every script that needs a price imports it, so a rule is implemented once |
| `scripts/cashflow.py` | The savings rate, the emergency buffer's true cover in months, and cash sitting above the buffer | Spending is what the household stated. Locked money is excluded from every buffer figure |
| `scripts/debt.py` | Amortisation, the interest cost, and repayment versus investing the same money | Reports a payment that does not cover the interest as non-amortising rather than projecting it. Repayment is a certain saving at the loan rate; the investment is an assumption |
| `scripts/goal_funding.py` | Each goal's required monthly contribution, funded ratio and shortfall on its own date | Tested per goal. It does not rank the goals against each other - that is the household's decision |
| `scripts/insurance_needs.py` | The death, disability and long-term care gaps against the household's own figures | Sizes sums assured. It does not price products or recommend one |
| `scripts/risk_register.py` | Risks ranked by probability times impact, with the mitigation status kept separate | A probability entered as a percentage is refused rather than read as a 100x larger risk |
| `scripts/srs_drawdown.py` | The ten-year SRS drawdown schedule, the tax-free capacity, the deemed withdrawal at the end of the window, and the age the member may withdraw from | Derives the prescribed retirement age from the first-contribution date, never from today's statutory age |
| `scripts/check_params.py` | Listing every parameter that is unverified or past its review date | Reads the whole parameter file. Exits non-zero, so it can gate a deliverable rather than advise |

`portfolio_risk.py` takes an optional `theme` on each holding, and an optional `max_theme` in the mandate. A regional cap answers "which country"; a theme cap answers "how many separate ways am I making the same bet". Several funds in one country, across different asset classes, can be a single theme, and only the theme check can see it. Configs without themes behave exactly as before.

Run them as `python scripts/<name>.py --config <file.json>`. Add `--json <out.json>` to capture machine-readable results alongside the report.

## The monthly mandate check

The annual review is the wrong interval for a limit that can be breached quietly in between. `scripts/check_mandate.py` is the check that runs monthly, on the household's own holdings file.

It reports three statuses and they mean different things:

- **PASS** - every limit satisfied, on data fresh enough to trust. It writes nothing.
- **BREACH** - at least one limit failed. It names every failure, not a count.
- **CANNOT JUDGE** - the holdings are stale, a price could not be refreshed, or the config is incomplete. **This is not a pass.** The limits were not checked, and the report says so.

That third status is the point of the tool. A watcher that reports "fine" on three-month-old positions is worse than no watcher, because it manufactures confidence the household never earned.

It keeps two classes of result apart, which is the facts-and-assumptions rule applied to monitoring. **Hard signals** - regional look-through, single-holding and asset-class concentration, equity share, cash buffer - depend only on what the portfolio holds, so a breach is a fact. **Assumption-dependent** results - portfolio volatility and the estimated worst-case fall - move when the return and correlation assumptions move, so a breach there means the assumptions imply a breach, not that anything was measured.

A position with no market quote keeps its statement value. CPF, SRS, property and anything unlisted belong in that group, and the report always lists which holdings were marked to market and which were not, so a figure that cannot drift is never mistaken for one that was checked.

## Live market data and technical-analysis overlay

Use live prices and price/volume analysis only to improve monitoring of listed holdings and to describe current market conditions. It is a **tactical observation layer**, not a replacement for financial planning and not a forecasting engine. The household's goals, protection needs, liquidity, tax position and written risk mandate remain the strategic layer; they are assessed first and cannot be overridden by a chart signal.

Before relying on a live-data result, record the provider; verified instrument identifier and exchange; currency; retrieval timestamp and timezone; quote or bar timestamp; market session; data granularity; and adjusted/unadjusted basis. `market_data.py` returns all of those on every quote. It cannot report delayed-versus-real-time entitlement, because the free sources do not expose it: when a broker feed (OpenD) is used instead, state the entitlement per market explicitly, since an unentitled feed is delayed or snapshot-only. Keep live values, household statement values, planning assumptions and **price-derived observations** separate. A price-derived observation must identify its lookback, timeframe and indicators used; it is neither a fact about the future nor a planning assumption. If a quote is stale, unavailable, from an unverified symbol mapping, or materially conflicts with the household record, report **CANNOT JUDGE** for the affected live-data check. Market closure and missing data are not evidence that a price is unchanged.

For price-history interpretation, use the `technical-analysis` skill. Its output may describe trend, volatility, volume, support/resistance or an indicator on a declared timeframe. It must also state its limits: indicators transform past price; agreeing indicators are not independent evidence; and a level or pattern does not predict an outcome. Do not promote a technical reading into an expected return, retirement projection assumption, probability of success, or product recommendation without separate evidence.

Keep alert classes distinct:

- **Mandate breach** — a hard, portfolio-level limit has failed; name the limit and follow the escalation gate.
- **CANNOT JUDGE** — data freshness, provenance or completeness prevents the check; do not present this as a pass.
- **Technical condition** — a time-bounded, price-derived market observation; state the source, as-of time, timeframe, lookback and limitations. It is not a command to trade.

Real-time technical data can prompt a review, but it cannot by itself relax an equity cap, cash-buffer floor, concentration limit, regional limit, tax constraint or protection requirement. In a wealth-advisory deliverable, do not place trades or issue execution instructions, including buy/sell language, entry prices, targets, stop orders, share counts or position sizes. When a tactical reading conflicts with an agreed mandate or plan target, stop at the escalation gate and present the conflict, alternatives and assumptions for household or qualified-professional review.

Before calculating whole-portfolio drift or risk from refreshed data, reconcile each holding's valuation basis and date. Mark whether it is quote-eligible and technical-analysis-eligible. If a material holding is stale or cannot be reconciled, return **CANNOT JUDGE** for any portfolio result that depends on its weight; never infer regional, theme or look-through conclusions from a security chart.

### The data layer, and where it stops

Fetching is not duplicated per script. `scripts/market_data.py` owns the provider chain per symbol, the retry and throttle rules, and the three checks that tell a failed fetch from a flat market - did the response arrive, was it at the granularity asked for, and does the last date match the last trading day. Every quote carries its provider, quote date, granularity, adjustment basis and age, because an unadjusted series shows a split as a fall that never happened, and because two providers can disagree and both be right on different dates.

The catalogue of which free sources work, what each covers and how each fails is maintained by the **`technical-analysis` skill** in its `references/data-sources.md`. That file is the single source for source selection; it is not copied here, because two copies of a source list drift apart.

**The precedence rule, so the two skills cannot give opposite answers.** The data layer is shared. The *price reading* belongs to `technical-analysis`; a planning deliverable may quote a trend, volatility or level as a time-bounded observation with its source and as-of date. Within a wealth-advisory deliverable there are no execution instructions of any kind - no buy or sell language, entry prices, targets, stop orders, share counts or position sizes - and the sizing arithmetic in that skill's `references/risk-and-sizing.md` does not travel into a plan. Where a chart reading conflicts with an agreed limit or plan target, stop at the escalation gate and present the conflict.

## References

Read only what the task needs.

- `references/discovery-and-suitability.md` - what to establish before projecting, risk capacity versus tolerance, and when to escalate to a professional.
- `references/risk-mandate.md` - turning "lower risk" into enforceable limits, the order the family risks should be handled in, and glide paths to a fixed date.
- `references/family-continuity.md` - insurance adequacy, emergency funding, nominations, wills and guardianship, and the cross-border wrinkles for a mixed-status family.
- `references/planning-methods.md` - projection mechanics, return and inflation assumptions, withdrawal sequencing for CPF/SRS/portfolio, longevity, and the stress tests to run every time.
- `references/singapore-tax-and-accounts.md` - what is and is not taxed in Singapore, the residency tests, resident and non-resident rates, rebates, the $80,000 relief cap, each relief's conditions, CPF and SRS mechanics including withdrawal, and the verification duty.
- `references/greater-china-access.md` - Hong Kong and mainland access as one exposure, what each route actually owns, tax and currency by route, and the region's specific risks.
- `references/data-provenance.md` - the live/statement/assumption split, the freshness limits, and what to do when a source fails. Read it before quoting any fetched figure.
- `references/config-schemas.md` - what each script needs, so a config is written from a schema rather than guessed. Read it when building a household file.
- `references/monitoring.md` - what runs monthly, annually and on an event, the four alert classes, and how a proactive observation differs from a breach. Read it before turning a monthly result into a recommendation.
- `references/gates.md` - the four checkpoint types and where they sit in this workflow. Read it when a check fails and the next step is not obvious.
- `references/sg-parameters-2026.json` - the dated parameter file the scripts read.
- `references/examples/` - worked configs for the scripts, with made-up figures. Use them to test a script, never as household data.
- `references/deliverables.md` - field-by-field structures for a family plan, annual review, net wealth statement, and continuity pack.

## Working with money numbers

- Work in today's dollars and say so, or work in nominal dollars and say so. Mixing them is the most common way a plan looks better than it is.
- Report the withdrawal rate as a percentage as well as a dollar figure, so an implausible drawdown is visible at a glance.
- State the reporting currency, and be explicit about which future spending is in a different currency. A household that will spend in one currency and save in another carries a risk that never appears in a return assumption.
- Round to the precision the assumptions support. A 2.5% inflation assumption does not justify a terminal-wealth figure to the dollar.

## Reading household documents

The household will send screenshots, policy schedules, bank pages, product brochures, tax calculators and statements. These are **source documents**, and a figure taken from one is a *statement* value, not an assumption and not a live price. `references/data-provenance.md` sets out the three classes and the freshness limits for each.

Read what is on the page rather than what the document implies. A quotation's first-year premium is not its cost; a sample table's sum assured is not the household's; a rate table's headline is not the rate on the balance held. Where a document gives a range of ages and sums assured, quote the row that matches the household.

Read the whole document before drawing on it. Premium tables, distribution costs and definitions are usually several pages in, and the first page of an insurance illustration is marketing. A 74-page policy document contains the schedule that matters on page three.

When a figure comes from a document:

- name the document and its date, so the household can check it
- distinguish what the document states from what you infer from it
- say which pages or tables you used when the conclusion is contested
- flag anything the document does not answer rather than filling the gap

If the same figure appears in two documents, say which one you used and why. If a document contradicts an earlier assumption, the document wins — and say that the earlier figure changed.
