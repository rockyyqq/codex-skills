---
name: wealth-advisory
description: Build a household financial plan and the analysis behind it - retirement and multi-currency projections, portfolio risk and mandate checks, CPF/SRS relief planning, and protection and continuity review - tuned for a Singapore-based family with Greater China exposure and a possible relocation. Use for planning packs, "will the money last" questions, allocation drift, risk-limit checks, recurring monthly mandate monitoring, and Hong Kong or China exposure questions. Not for executing trades, drafting wills or legal instruments, or planning in another tax jurisdiction without replacing references/singapore-tax-and-accounts.md.
---

# Wealth Advisory

Build financial planning work product for a household that the family can actually decide on. Output is a draft for the household to weigh; it is not licensed financial advice, and the person reading it should be able to see every assumption that produced every number.

## Non-negotiables

**Never invent a number.** Every figure traces to one of three places: the household, its own documents, or a named official source. When something required is missing, ask for it. A plan resting on plausible-looking guesses is worse than no plan, because it carries false authority.

**Separate facts from assumptions.** A *fact* - a tax rate, a contribution cap, an eligibility rule - carries a source and the date it was confirmed. An *assumption* - a return, a volatility, a correlation, an inflation rate - cannot have a source, so it carries a label, a range where possible, and a statement that changing it changes the answer. Never dress an assumption up as a fact.

**Never let an unverified parameter pass silently.** `references/sg-parameters-2026.json` and the verification tables in the reference files mark what has been checked. Anything unconfirmed gets re-checked against its source before the plan is relied on, and the plan says which assumptions are unconfirmed.

**Protection before projection.** For a family with dependent children, death, disability and long-term care threaten the plan far more than market movements do. Establish where the household stands on those before optimising a portfolio. If the protection layer is incomplete, say so plainly - it outranks everything in the investment section.

**Projects, not promises.** Report the probability of success, the assumptions behind it, and what would have to be true for the plan to fail. Never present one number as "what you will have".

**Stay inside the boundary.** Do not place or instruct trades, file anything with a tax authority, draft wills, trusts or guardianship documents, give citizenship or immigration guidance, or make product-specific recommendations that require a licence in Singapore. Name those and point to a professional instead of improvising.

## Workflow

1. **Establish the inputs.** Read `references/discovery-and-suitability.md`. Do not compute until the household, goals, obligations, and constraints are on the table.
2. **Check the protection layer.** Read `references/family-continuity.md`. Record what is covered and what is exposed; this frames how much risk the portfolio can carry at all.
3. **Write the risk mandate.** Read `references/risk-mandate.md` and get the limits into numbers - drawdown tolerance, equity cap, regional and single-holding caps, cash buffer. The portfolio either passes or fails these; they are not decoration.
4. **Fix the assumptions before the answer.** Fill a config for the script you need. Where an assumption is unknown, record the range being tested rather than picking a midpoint.
5. **Compute.** Scripts do the arithmetic and refuse to guess. They are not a substitute for judgement about whether the inputs are right.
6. **Stress-test.** Run the scenarios in `references/planning-methods.md`, including the ones specific to this household - a Greater China shock, an adverse currency move at the relocation, and higher spending.
7. **Assemble the deliverable.** Use `references/deliverables.md`. Every document carries its assumptions, the parameter-verification status, and a statement that the household should take legal, tax or product decisions to a qualified professional.
8. **Validate before presenting.** Run `scripts/validate_deliverable.py` on the finished document. A document that fails it is missing something the household needs in order to judge the work; fix it and run it again. Do not present an unvalidated deliverable.
9. **Restate from source before presenting.** Re-derive the headline numbers from the config files and fetched data, not from the conversation. Long sessions drift: a tax line goes missing, a holding gets counted twice, an earlier estimate quietly becomes a fact. Re-running the scripts costs a minute and catches what rereading does not. If a number in the draft cannot be traced to a file or a dated fetch, say so rather than presenting it.

## Gates

Name the checkpoint when a check fails, and answer what happens next. `references/gates.md` sets out four types — pre-flight, revision, escalation, abort — and the three questions each must answer.

The one that matters most is **escalation**: when an agreed limit conflicts with a target, stop and let the household choose. Never move a limit to make a position fit, and never present the conflict as commentary and carry on. A mandate whose limits move whenever they bind has stopped measuring anything, and the failure is invisible in the output because every number still looks defensible.

## Scripts

Each takes a JSON config, prints a markdown report, and exits with an explicit list of missing fields rather than substituting defaults.

| Script | Use it for | Notes |
|---|---|---|
| `scripts/portfolio_risk.py` | What risk the portfolio actually carries, where it comes from, true look-through regional exposure, and whether it obeys the mandate | Returns, volatilities and correlations must be supplied; it will not invent a correlation |
| `scripts/plan_projection.py` | "Will the money last?" - accumulation, drawdown, Monte Carlo, sustainable spending, phase changes such as a relocation, and one-off shocks | Assumptions all come from the config; holds no jurisdiction knowledge |
| `scripts/rebalance.py` | Allocation drift against targets, regional drift, concentration limits, and a dollar-level trade list with transaction costs | Follows the account priority given to it; does not decide policy |
| `scripts/sg_relief.py` | Singapore tax payable, relief headroom, and the tax saved by SRS contributions and CPF top-ups | Reads the parameter file and warns about any unverified value it used |
| `scripts/insurance_compare.py` | What two insurance options actually cost to the age you expect to stop paying, on a total and present-value basis, and the age at which the cheaper one changes | Cost only. It says nothing about whether the cover is adequate - size the sum assured against the need separately |
| `scripts/refresh_prices.py` | Updating the market value of every holding that has a quote, so drift is visible without rekeying prices by hand | Writes a `prices.json` overlay; never edits the household config. Holdings with no quote keep their statement value |
| `scripts/check_mandate.py` | The monthly mandate check - does the portfolio still obey the limits, and if not, which one | Reuses `portfolio_risk.py` so a limit is never implemented twice. Refuses to report a pass on stale or unverifiable data |
| `scripts/validate_deliverable.py` | Checking a finished document against the six things every deliverable must carry | Run it on every deliverable before it is presented. Prints `OK`, or `FAIL` with a named reason per missing item |

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

## References

Read only what the task needs.

- `references/discovery-and-suitability.md` - what to establish before projecting, risk capacity versus tolerance, and when to escalate to a professional.
- `references/risk-mandate.md` - turning "lower risk" into enforceable limits, the order the family risks should be handled in, and glide paths to a fixed date.
- `references/family-continuity.md` - insurance adequacy, emergency funding, nominations, wills and guardianship, and the cross-border wrinkles for a mixed-status family.
- `references/planning-methods.md` - projection mechanics, return and inflation assumptions, withdrawal sequencing for CPF/SRS/portfolio, longevity, and the stress tests to run every time.
- `references/singapore-tax-and-accounts.md` - what is and is not taxed in Singapore, CPF and SRS mechanics, reliefs, and the verification duty.
- `references/greater-china-access.md` - Hong Kong and mainland access as one exposure, what each route actually owns, tax and currency by route, and the region's specific risks.
- `references/data-provenance.md` - the live/statement/assumption split, the freshness limits, and what to do when a source fails. Read it before quoting any fetched figure.
- `references/gates.md` - the four checkpoint types and where they sit in this workflow. Read it when a check fails and the next step is not obvious.
- `references/sg-parameters-2026.json` - the dated parameter file the scripts read.
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
