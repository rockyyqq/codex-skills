# Config schemas

Every script takes one JSON config and prints a markdown report. This file is the
data layer: what each script needs, so a config is written from a schema rather
than reverse-engineered from a docstring. One household file can carry the blocks
several scripts need.

Worked examples live in `references/examples/`. The figures in them are made up.

| Example file | Exercises |
|---|---|
| `examples/household-2026.json` | cashflow, debt, goal_funding, insurance_needs, risk_register, refresh_prices, check_mandate |
| `examples/tax-2026.json` | sg_relief |
| `examples/srs-2026.json` | srs_drawdown |

## Conventions

- A missing **required** key exits 2 and names every field that is missing. Nothing
  is defaulted into a deliverable.
- Money is in the config's `currency` (default SGD) unless stated otherwise.
- Rates and returns are decimals: 2.6% is `0.026`, not `26`.
- Dates are `YYYY-MM-DD`.
- `--json out.json` writes the raw result beside the report, so a headline figure
  can be re-derived from a file rather than from the conversation.

## cashflow.py

Required: `income[]`, `expenses[]`.

| Key | Meaning |
|---|---|
| `income[].monthly`, `.stability` | Enter variable income at a level the household would rely on in a bad year |
| `expenses[].monthly`, `.essential` | `essential: true` drives the optional essential-only buffer basis |
| `cash[].value`, `.access` | `instant`, `days` or `locked`. Locked money is excluded from every buffer figure |
| `buffer_months` (12), `buffer_basis` (`total` or `essential`), `savings_target` | |

## debt.py

Required: `loans[]` with `name`, `balance`, `annual_rate`, `monthly_payment`.
Optional: `extra_monthly`, `invest_expected_return`, `invest_tax_rate`, `horizon_years`.

A payment that does not cover the monthly interest is reported as non-amortising
rather than projected.

## goal_funding.py

Required: `goals[]` with `name`, `target_amount`, `target_date`; plus
`current_amount`, `monthly_contribution`, `expected_annual_return` and optional
`inflation`. Optional global keys: `as_of`, `inflate_targets` (default false).

Per-goal output is the required monthly contribution, the funded ratio on the
goal's own date, and the same requirement if the goal slips two years.

## insurance_needs.py

Required: `lives[]` with `name`, `annual_income`, `income_years_to_replace`, and
`outstanding_debt`, `education_costs_remaining`, `existing_life_cover`,
`cpf_available`, `survivor_benefits`, `survivor_annual_spending` as they apply.

Optional blocks: `disability` (`annual_income_gap`, `years_to_cover`,
`existing_cover`, `liquid_assets`) and `long_term_care` (`monthly_cost`,
`monthly_scheme_payout`, `years`, `existing_cover`).

It sizes sums assured. It does not price products and does not recommend one.

## risk_register.py

Required: `risks[]` with `name`, `probability` (a fraction, so 1-in-50 is `0.02`),
`impact`; plus `status` (`covered`, `partial`, `uncovered`, `accepted`),
`mitigation`, `owner`. Optional: `material_expected_loss` (default 1000).

A probability entered as a percentage is refused rather than silently read as a
100x larger risk.

## sg_relief.py

Required: `employment_income`. Optional: `other_taxable_income`,
`employee_cpf_contributions`, `planned_srs_contribution`,
`employer_srs_contribution`, `planned_cpf_topup_self`, `planned_cpf_topup_family`,
`srs_withdrawn_in_same_year`, `srs_account_suspended`,
`becoming_citizen_pr_in_year`, `tax_residency_next_ya`, `insurance_premiums` +
`insurance_insured_value`, `other_reliefs`, `relief_priority`, `residency`
(`citizen_pr` or `foreigner`), `age_band`, `tax_residency` (`resident` or
`non_resident`), `params`.

`relief_priority` decides which reliefs the $80,000 cap absorbs first. The default
keeps automatic reliefs first; the report names what the cap cut.

## srs_drawdown.py

Required: `srs_balance`. Optional: `first_withdrawal_year`, `annual_withdrawal`
(defaults to the tax-free capacity on the stated facts), `other_taxable_income`,
`other_reliefs`, `tax_resident`, `first_contribution_date`,
`death_or_terminal_illness_year`, `params`.

`first_contribution_date` is what the prescribed retirement age is derived from.

## refresh_prices.py

Required: `portfolio.holdings[]`. Optional: `currency`, `portfolio.as_of`,
`--max-age-trading-days` (default 5).

Each holding may carry `quantity`, `price_symbol` and `price_currency`. Holdings
without `price_symbol` - CPF, SRS, property, anything unlisted - keep their
statement value and are listed as unpriced. A Chinese unit trust is priced by NAV
with the symbol prefix `FUND:`.

## market_data.py

Not a household config. `--symbol` (repeatable) and `--fx BASE/QUOTE`, plus
`--window`, `--max-age-trading-days`, `--selftest`. Every returned quote carries
its provider, quote date, granularity, adjustment basis and age.

## check_mandate.py

Uses the same household file as `refresh_prices.py` plus the mandate block from
`portfolio_risk.py`. Run `refresh_prices.py` first: the check reports CANNOT JUDGE
when the overlay is missing, a quote failed, or a quote is past its freshness
limit.

## portfolio_risk.py, plan_projection.py, rebalance.py, insurance_compare.py

Schemas are in each script's docstring; they are documented there because their
configs are the ones that change most often. `plan_projection.py` works in nominal
dollars and expresses spending in today's dollars in the config.
