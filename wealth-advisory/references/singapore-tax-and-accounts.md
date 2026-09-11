# Singapore tax and accounts

Read this before optimising anything, and re-verify the parameters in `sg-parameters-2026.json` before an output reaches a client. Local rules are revised at every Budget, usually in February.

## Four structural facts that change the whole approach

1. **No capital gains tax for individuals.** There is no loss harvesting to do and no wash-sale rule to respect. Any workflow imported from a US advisory toolkit that revolves around tax-loss harvesting has no analogue here. The levers are tax reliefs and asset location instead.
2. **No estate duty.** Abolished in February 2008. Estate planning is therefore about distribution, probate efficiency, and nominations - not death taxes. The exception to watch is a US-connected household, where US estate tax exposure on US-situs assets can be severe.
3. **Singapore-sourced dividends are not taxed in the individual's hands**, under the single-tier corporate tax system. Foreign dividends can carry withholding tax deducted at source, often invisible in a reported return.
4. **Foreign-sourced income remitted by a resident individual is generally exempt**, with exceptions including income from a Singapore partnership. Confirm the position for the specific facts before relying on it.

## Income tax

Personal income tax is progressive and tops out at 24%. The brackets have applied since YA 2024; the full table is in the parameter file and is implemented in `scripts/sg_relief.py`.

Employment income, rental income, and most other Singapore-sourced income are taxable. What matters for planning is the *marginal* rate: it determines the value of every relief, which is why relief planning is worth doing precisely when income is high and worth skipping when it is not.

## CPF

CPF is a mandatory, account-based system for citizens and permanent residents. The accounts serve different purposes and are not interchangeable:

- **Ordinary Account (OA)** - housing, education, and investment. Lower interest.
- **Special Account (SA)** - retirement. Higher interest, then converted into the Retirement Account at 55.
- **MediSave Account (MA)** - healthcare.
- **Retirement Account (RA)** - formed at 55 from SA and OA savings; funds CPF LIFE.

Contribution rates fall with age. The rates in force from 1 January 2026 and the Ordinary Wage ceiling are recorded in the parameter file and were confirmed against the official CPF rate table on 10 September 2026.

Two consequences for planning:

- CPF is the household's secure income base. Because CPF LIFE pays for life, it is the floor that everything else sits on top of.
- CPF funds are not freely investable. Money in CPF is not the same as money in an SRS account or a brokerage account, and a projection that treats them as fungible will overstate flexibility.

Additional Wage ceiling equals the Annual Salary Ceiling less the Ordinary Wages already subject to CPF in that year. Confirm both figures for the relevant year.

## SRS

The Supplementary Retirement Scheme is voluntary, available to citizens, PRs, and foreigners, and is the main tax-relief lever for higher earners.

- **Contributions are relieved** up to an annual cap, which differs for citizens/PRs and for foreigners.
- **Withdrawals taken from the statutory retirement age are 50% taxable**, spread over a ten-year window. This is the mechanic that makes SRS work: contribute at the marginal rate, withdraw at a lower rate in retirement.
- **Early withdrawal is penalised.** Expect a percentage penalty on the amount withdrawn plus full taxation of the amount. Confirm the current penalty before advising anyone to touch it early.

The planning implication is counter-intuitive and worth stating plainly: the risk with SRS is not withdrawing too early, it is *never withdrawing*. Funds left in the account past the ten-year window become fully taxable and the relief is wasted. A drawdown schedule across the window belongs in every plan that has an SRS balance.

## Reliefs worth checking each year

| Relief | Effect | Note |
|---|---|---|
| SRS contribution | Dollar-for-dollar reduction in chargeable income up to the cap | The largest lever for most higher earners |
| CPF cash top-up (RSTU) to self and to family members | Relief up to a cap per recipient | The recipient must meet the eligibility conditions |
| Voluntary CPF contributions | Capped overall, and shared with the top-up reliefs | Confirm how the caps interact before assuming a full deduction |
| Life insurance premiums | Capped, and there are sub-limits for the MediSave-related portion | Usually modest |
| Earned income relief | Automatic, scaled by age | Small, but it is free |

Reliefs reduce chargeable income, so their value is the marginal rate applied to the amount - not the amount itself. Never describe a relief as "saving $8,000 of tax".

## Insurance and healthcare

MediShield Life is universal basic hospital cover. Integrated Shield Plans layer private or higher-tier cover on top and can be paid from MediSave within limits. CareShield Life provides basic long-term care income, and is usually well short of the cost of a real care event - quantify the gap rather than assuming the scheme is sufficient.

For a long-term care event, model the shortfall against actual nursing or home-care costs, and test what drawing that shortfall does to the portfolio.

## Property

Buyer's and seller's stamp duties are the main transaction taxes, and the additional buyer's stamp duty rate depends on residency status and the number of properties. Rates change; confirm current rates before advising.

Two recurring errors: counting the family home as a retirement income asset when no downsizing is planned, and counting CPF monies used for the property as an asset while ignoring that they must be repaid with accrued interest on sale.

## Parameter verification duty

Every value in `sg-parameters-2026.json` carries a source URL and, where it was checked, the date it was checked. Values that are still unconfirmed are marked with `"verified_on": null` and the scripts print a warning listing them.

Before an output goes to a client:

1. Confirm every parameter marked unverified against its source URL.
2. Update the `verified_on` field.
3. Check for announced changes taking effect in the plan year - CPF rates in particular have been on a published multi-year schedule.

Primary sources:

- CPF contribution rates and wage ceilings: `https://www.cpf.gov.sg/employer/employer-obligations/how-much-cpf-contributions-to-pay`
- CPF interest rates: `https://www.cpf.gov.sg/member/growing-your-savings/earning-interest/interest-rates`
- CPF LIFE and retirement sums: `https://www.cpf.gov.sg/member/retirement-income`
- Individual income tax rates: `https://www.iras.gov.sg/taxes/individual-income-tax/basics-of-individual-income-tax/tax-residency-and-tax-rates/individual-income-tax-rates`
- SRS contribution and withdrawal rules: `https://www.iras.gov.sg/taxes/individual-income-tax/basics-of-individual-income-tax/special-tax-schemes/supplementary-retirement-scheme-(srs)`

The IRAS and CPF pages for SRS caps, interest rates, and CPF LIFE payouts render their tables dynamically, so a plain page fetch may return navigation text with no figures. Read the rendered page or the linked PDF rather than concluding the value does not exist.
