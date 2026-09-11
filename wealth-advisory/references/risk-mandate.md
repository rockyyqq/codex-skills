# Risk mandate

"I prefer lower risk" is not yet an instruction a portfolio can be built to. This file turns it into limits that can be checked, and puts the risks in the order that actually matters for a family.

## Four things people mean by lower risk

1. **Lower volatility** - a smoother ride from year to year.
2. **Smaller worst-case fall** - a drawdown the household can sit through without selling.
3. **Lower chance of permanent loss** - capital preservation in the money that matters.
4. **Higher chance the plan works** - which, over a long horizon, can argue for *more* equity, not less.

Ask which one, because they point in different directions. Most people who say "lower risk" mean the second, and are often surprised to find that pursuing only the first makes the fourth worse.

## The long-horizon paradox

Cutting equity reduces the visible risk and increases the invisible one. Over a 15-year horizon, a portfolio that is too cautious may need a materially higher savings rate, or a later finishing date, to fund the same spending.

This is why the mandate is set from the drawdown tolerance rather than from a headline allocation. Decide the fall you can hold through - that is behavioural and non-negotiable - then find the *least* risk that still meets the goal, rather than the most risk you can stomach.

The risk tools in this skill report volatility and probability of failure side by side precisely so this trade-off is visible rather than argued about.

## Turning it into limits

The tool enforces whatever you set. Typical shapes, not advice:

| Limit | What it controls | A reasonable starting point |
|---|---|---|
| Maximum portfolio volatility | The general ride | 8-11% a year for a cautious-but-invested household |
| Maximum drawdown tolerance | The number you can hold through | Set this from behaviour, before anything else |
| Maximum equity share | The main risk dial | 40-60% |
| Maximum single asset class | One bet dominating | 50-60% |
| Maximum single region, measured look-through | Country concentration | 20-25%, and the binding one for Greater China |
| Maximum single holding or issuer | Company risk | 5-10%; lower as the holding gets less liquid |
| Minimum cash and near-cash | Forced-selling protection | 1-2 years of household spending |
| Minimum secure income | Spending covered without markets | Whatever covers the baseline, ideally via CPF LIFE |

If a limit and a target conflict, the limit wins. A target allocation that breaches the mandate is a mandate problem, not a rounding error.

## Put the family risks first

For family savings, market risk is rarely the risk that ruins the plan. In rough order of damage:

1. **Death of a breadwinner** - income stops, and the survivor's plan changes permanently.
2. **Disability or long illness stopping work** - the most commonly under-insured risk, and the one that drains savings while also removing income.
3. **Job loss** - survivable with a buffer, catastrophic without one.
4. **Long-term care** - a slow, unpredictable cost that lands late.
5. **Market losses** - real, but recoverable in a way the others are not.

If 1 to 3 are not properly covered, then tuning the portfolio's risk is a rounding exercise. Buying adequate disability and life cover reduces a family's true risk far more than moving 10% from equities into bonds. Work the order top down and say plainly in the report which layer is still exposed.

## The glide path to a hard date

A fixed date changes the arithmetic. When money is needed on a known day - university fees, a relocation - the risk it can carry falls as that day approaches, because there is no time to recover a fall.

Split the portfolio by when the money is needed rather than by what it is invested in:

| Horizon | Purpose | Risk it can carry |
|---|---|---|
| 0-3 years | Fees, buffer, any spending already committed | Cash and short-dated bonds only |
| 3-10 years | Known obligations further out | Modest risk, mostly defensive |
| 10+ years | Retirement income, long-term growth | The long-term allocation |

This matters directly when two currencies and two countries are involved: money that must be spent in Singapore dollars shortly before a move should not be exposed to equity or currency risk at all.

## Writing the mandate down

A mandate is one paragraph, in the household's own words, and it goes in the file:

> We can accept a fall of up to X% in a bad year without selling. We want at least Y years of expenses in cash. We will hold no more than Z% in any single region and no more than W% in any single company. We want at least an 85% chance of funding our spending to age 95. Everything else follows from those numbers.

The tool checks the numbers. The household chooses them. Do not let the tool choose them by default, and do not silently relax a limit in order to make a target allocation fit.

## Review triggers

Revisit the mandate when: income or employment changes, a child arrives, the relocation date moves, interest rates change materially, a holding falls outside its band, or the household finds it cannot actually hold through the drawdown it said it could. That last one is the most important and the least often recorded.

## The check that runs between reviews

A limit that is only tested once a year is not really a limit. Run `scripts/check_mandate.py` monthly against the household's holdings file, with `scripts/refresh_prices.py` refreshing the market values first.

Two rules make the check worth having:

- **A pass has to be earned.** The check returns CANNOT JUDGE, not PASS, when the holdings file is stale, a price could not be refreshed, or the config is incomplete. Reporting a pass on data nobody verified is the failure mode that discredits monitoring.
- **A concentration breach and a volatility breach are not the same claim.** Concentration is a fact about what is held. Volatility and worst-case fall are downstream of the return and correlation assumptions, so a breach there is a statement about the assumptions. Fix the concentration; re-examine the assumptions.

The holdings file carries `portfolio.as_of`, the date the household last confirmed the positions and quantities. That date is separate from the price date, and both matter: prices move daily, but a new holding, a contribution or a sale is invisible to the market data and only appears when the household updates the file. That is what the staleness limit catches.
