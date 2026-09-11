# Planning methods

## Real versus nominal - decide and declare

The most common way a plan flatters itself is mixing today's-dollar spending with nominal returns. Pick one basis, state it on the first page, and never mix.

Convert with `real return = (1 + nominal) / (1 + inflation) - 1`. `scripts/plan_projection.py` works in nominal dollars and expresses spending in today's dollars in the config, then inflates the schedule - so its output is nominal and must be labelled that way.

## Setting return assumptions

- Use long-run, diversified, after-cost assumptions. Never extrapolate the last decade forward.
- Derive the portfolio return from the allocation rather than asserting a single number, or state plainly that the number is an assumption.
- Test the low end of the equity risk premium, not the midpoint.
- For retirement outcomes, volatility matters as much as the mean, because of sequencing.
- Include every layer of cost: fund expense ratios, platform fees, advisory fees, and transaction costs. A 1% annual drag compounds to roughly a quarter of terminal wealth over 30 years. If the plan cannot survive its own fees, the plan is the problem.
- Currency: state the reporting currency, and whether foreign holdings are hedged, unhedged, or unexamined. Unhedged foreign equity is a real risk that is often absent from a plan built on an SGD-only return assumption.

## Sequence-of-returns risk

Two retirees can average the same return over 30 years and have opposite outcomes depending on when the bad years arrive. Early losses hurt disproportionately because withdrawals sell units at depressed prices and those units never recover.

Always run a bad-first-decade scenario. For a household near or in retirement this is the single most informative stress test, and it is the one a simple average-return projection hides completely.

## Withdrawal sequencing in Singapore

The order in which pots are drawn is a planning decision with tax consequences, and it is one place where Singapore differs sharply from US-oriented tools.

1. **SRS, in tranches.** SRS must be drawn within a ten-year window starting from the statutory retirement age. Half of each withdrawal is taxable, so spreading withdrawals across the window keeps each year inside the low brackets. Deferring SRS entirely is a common and expensive mistake: it concentrates the withdrawals and pushes them into higher rates.
2. **Portfolio.** Singapore has no capital gains tax for individuals, so selling is not itself a tax event. Watch transaction costs, and watch foreign withholding tax on dividends, which is deducted before you ever see it.
3. **CPF LIFE.** This is the longevity floor, not a pot to be spent down. Pay it attention first when deciding how much lifetime income to buy.
4. **Cash buffer.** Hold one to two years of net spending in cash or near-cash so the household is never a forced seller. The buffer costs a little return and buys a great deal of resilience.

## CPF LIFE as the longevity floor

CPF LIFE converts a lump sum into a lifetime income, so it protects against the one risk a portfolio cannot diversify: living a long time. It raises the sustainable withdrawal rate available from the rest of the portfolio and shrinks sequence risk, because part of the spending is no longer exposed to markets.

Treat payouts as fixed nominal income unless the escalating plan is chosen, and be aware the escalating plan starts lower. Model the trade-off between keeping the money liquid and buying more guaranteed lifetime income - the answer depends on the rest of the household's secure income, not on the payout alone.

## Longevity

Plan to at least age 95, and test one spouse living to 100. Do not use average life expectancy as a planning horizon: roughly half of all people outlive it, and the household does not get to spend the average.

## Property

The family home is illiquid and is not a retirement income asset unless downsizing is modelled explicitly, with a realistic haircut for agent fees, legal costs, and seller's stamp duty if the holding period has not run. Treat "we'll sell the house" as an assumption to be tested, not a given.

CPF withdrawn for property must be repaid with accrued interest when the property is sold. That obligation sits inside the CPF balances, so it should not be counted twice - once as home equity and again as a CPF asset.

## Stress tests to have run before any plan is presented

| Scenario | What it exposes |
|---|---|
| Bad first decade in retirement | Sequence risk, the most damaging and most hidden risk |
| Inflation 2 percentage points above assumption | Whether the plan depends on a benign inflation path |
| Living to 100, or one spouse to 100 | Longevity risk and the value of the CPF LIFE floor |
| Spending 20% higher than planned | The margin for error in the spending estimate, which is the least reliable input |
| Early death of one spouse | Loss of an income stream, survivor spending needs, and nomination failures |
| A long-term care event | Whether CareShield Life and any supplementary cover are enough, and what the shortfall does to the portfolio |
| Retiring two years early | The combined cost of two fewer saving years and two more spending years |

## Interpreting probability of success

- It is a model output conditional on assumptions, not a forecast, and it should be labelled that way wherever it appears.
- 85% or better is a convention, not a rule. The right target depends on how much flexibility the household has and how bad failure would actually be.
- Report the age at which the poor tail (5th percentile) runs out of money. That single number changes behaviour more effectively than any percentage.
- Failure is usually a plan failure rather than a model failure. When it appears, present the levers: spend less, work longer or part-time, save more now, take more risk, or downsize the home.

## Errors to check for before delivery

- Today's-dollar spending against nominal returns
- Fees excluded from the return assumption
- Average returns used with no sequence test
- CPF LIFE omitted from secure income
- The home counted as liquid, or counted twice
- SRS left untouched until late, forcing concentrated withdrawals
- An inheritance treated as a funding source
- A projection rounded to the dollar when the assumptions support only a range
