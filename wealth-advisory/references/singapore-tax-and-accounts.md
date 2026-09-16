# Singapore tax and accounts

Read this before optimising anything, and re-verify the parameters in `sg-parameters-2026.json` before an output reaches a client. Local rules are revised at every Budget, usually in February.

The income tax rates, residency tests, rebate, relief cap and relief conditions in this file were read from the IRAS pages listed at the bottom on **13 September 2026**, and the parameter file records that date. CPF rates carry their own confirmation date because they come from CPF Board.

## Four structural facts that change the whole approach

1. **No capital gains tax for individuals.** There is no loss harvesting to do and no wash-sale rule to respect. Any workflow imported from a US advisory toolkit that revolves around tax-loss harvesting has no analogue here. The levers are tax reliefs and asset location instead.
2. **No estate duty.** Abolished in February 2008. Estate planning is therefore about distribution, probate efficiency, and nominations - not death taxes. The exception to watch is a US-connected household, where US estate tax exposure on US-situs assets can be severe.
3. **Singapore-sourced dividends are not taxed in the individual's hands**, under the single-tier corporate tax system. Foreign dividends can carry withholding tax deducted at source, often invisible in a reported return.
4. **Foreign-sourced income remitted by a resident individual is generally exempt**, with exceptions including income from a Singapore partnership. Confirm the position for the specific facts before relying on it.

## Tax residency comes before the numbers

Everything else in this file depends on one question, so settle it first. An individual is a **tax resident** for a Year of Assessment (YA) if they are a:

1. Singapore Citizen or Singapore Permanent Resident who resides in Singapore except for temporary absences; or
2. Foreigner who has stayed or worked in Singapore for at least 183 days in the previous calendar year; or
3. Foreigner who has stayed or worked in Singapore continuously for 3 consecutive years, even where the stay was under 183 days in the first and/or third year; or
4. Foreigner who worked in Singapore for a continuous period straddling 2 calendar years with a total stay of at least 183 days, counting physical presence immediately before and after the employment. This route is for employees and excludes company directors, public entertainers and professionals.

Anyone who does not meet these tests is a **non-resident** for that YA. Three consequences drive the plan:

- **Reliefs are for residents only.** A non-resident cannot claim the personal reliefs, so relief planning has no application to a non-resident year. The relief cap and every relief below are resident-only.
- **The rate structure changes completely.** A non-resident pays 24% flat on most income, not the progressive scale. Employment income is taxed at 15% flat or the resident progressive rates, whichever gives the higher tax. See below.
- **Residency can change mid-plan.** It is tested each YA. A relocation, a long posting abroad, or a year split between Singapore and China can move a spouse from resident to non-resident between one year and the next, and with it the value of every relief. This household has a mixed-status profile and a possible relocation, so re-test residency at every plan year rather than assuming the current position holds.

## Income tax

Personal income tax is progressive and tops out at 24%. The brackets have applied since YA 2024; the full table is in the parameter file and is implemented in `scripts/sg_relief.py`.

| Chargeable income | Rate on the band | Gross tax payable at the top of the band |
|---|---|---|
| First $20,000 | 0% | $0 |
| Next $10,000 | 2% | $200 |
| Next $10,000 | 3.5% | $550 |
| Next $40,000 | 7% | $3,350 |
| Next $40,000 | 11.5% | $7,950 |
| Next $40,000 | 15% | $13,950 |
| Next $40,000 | 18% | $21,150 |
| Next $40,000 | 19% | $28,750 |
| Next $40,000 | 19.5% | $36,550 |
| Next $40,000 | 20% | $44,550 |
| Next $180,000 | 22% | $84,150 |
| Next $500,000 | 23% | $199,150 |
| Above $1,000,000 | 24% | - |

The cumulative column is IRAS's own, and it is the cheapest check on a tax computation: if an arithmetic result does not land on these figures at a band boundary, the computation is wrong. The parameter file stores these as `income_tax_gross_payable_checkpoints`.

Employment income, rental income, and most other Singapore-sourced income are taxable. What matters for planning is the *marginal* rate: it determines the value of every relief, which is why relief planning is worth doing precisely when income is high and worth skipping when it is not.

### Tax rebates are not reliefs

A **relief** reduces chargeable income, so it is worth the amount multiplied by the marginal rate. A **rebate** reduces the tax payable itself, after the reliefs have been applied. They are not interchangeable and should never be added together.

A personal income tax rebate has been granted in some years and not others: 60% of tax payable capped at $200 for YA 2025, and 50% capped at $200 for YA 2024. IRAS lists no rebate for YA 2026 - an absence, not a statement, so confirm it against the Budget for the plan year rather than carrying this line forward. Read the row for the plan year rather than assuming one applies.

### Non-resident rates

- **Employment income:** 15% flat, or the resident progressive rates, whichever produces the *higher* tax bill.
- **All other income**, including rental income, pension and director's fees: 24% flat. This rate applied from YA 2024; it was 22% before that.
- Certain income is taxed at reduced withholding rates instead. The planning-relevant entries are in the parameter file, and the ones that matter most for this household are the SRS rows: a withdrawal by a non-Singapore SRS account holder is subject to 24% withholding, reduced to 15% where the cumulative withdrawal in the calendar year does not exceed $200,000 and the holder has no other income that year.

Withholding tax is not necessarily the final tax. For a foreigner or PR the amount withheld is a credit against the actual liability, and any unused credit is refundable on filing.

## The relief cap: $80,000

There is an **overall cap of $80,000 on the total personal income tax reliefs** one individual can claim in a YA, and it has applied since YA 2018. It covers *all* personal reliefs claimed together, including relief on SRS contributions and CPF relief.

This is the constraint that makes relief planning a portfolio problem rather than a list of separate opportunities. It matters because the household's own situation can plausibly reach it: a working mother claim can alone run into five figures, and on a $150,000 income IRAS's own worked example accumulates $86,650 of reliefs that are cut back to $80,000. Three consequences:

- **Once the cap binds, the next relief is worth nothing.** A further dollar of SRS contribution or CPF top-up produces no tax saving at all, while still locking the money away or being irreversible.
- **Which reliefs to keep is the household's choice, not the market's.** IRAS allows reliefs to be given up so another claimant can use them - a qualifying child relief, parent relief or grandparent caregiver relief can be left to a spouse or sibling who has cap headroom. Where the cap binds, that reallocation is worth more than any new top-up.
- **Money put into SRS or CPF cannot be taken back.** There is no refund of SRS contributions or of accepted CPF cash top-ups. Check the cap *before* the contribution, never after. IRAS says this explicitly, and it is the single most common way this planning destroys value.

`scripts/sg_relief.py` applies the cap and reports both the capped position and the headroom left under it. Run it before recommending any contribution.

## Reliefs worth checking each year

Amounts below are confirmed against IRAS at the date at the top of this file. Every relief is available only to a tax resident.

| Relief | Amount | Note |
|---|---|---|
| Earned income relief | $1,000 below 55; $6,000 age 55-59; $8,000 age 60 and above (age as at 31 Dec of the previous year) | Automatic, no claim needed. Capped at the amount of taxable earned income. |
| Earned income relief (disability) | $4,000 / $10,000 / $12,000 by the same age bands | Replaces the standard relief for a person whose disability severely affects their ability to work. Evidence needed on first claim. |
| SRS contribution | Actual contribution up to $15,300 for citizens and PRs, $35,700 for foreigners | The largest lever for most higher earners. Automatic, but see the conditions below. |
| CPF cash top-up (RSTU) | Up to $8,000 for self plus up to $8,000 for family members, so $16,000 in total | Cash only, and only up to the recipient's headroom below the Full Retirement Sum. Automatic. |
| Life insurance premiums | Varies - see below | Not a flat $5,000. The formula usually produces much less. |
| CPF relief for employees | The employee's own mandatory contribution | Automatic; counts towards the $80,000 cap. |
| MediSave and voluntary CPF contributions | By category | Self-employed and platform-worker variants exist. Read the specific page. |
| Spouse, parent, grandparent caregiver, sibling (disability), qualifying child, working mother's child relief, NSman relief, parenthood tax rebate | Not itemised in the parameter file | These exist and can be large. Read the IRAS page for the plan year and enter the amount as its own parameter before using it. |

Two reliefs have **lapsed** and must not be claimed: Foreign Domestic Worker Levy Relief from YA 2025, and Course Fees Relief from YA 2026. An older checklist that still carries them is out of date.

Reliefs reduce chargeable income, so their value is the marginal rate applied to the amount - not the amount itself. Never describe a relief as "saving $8,000 of tax".

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

### Retirement sums

The **Full Retirement Sum (FRS)** caps the SA/RA balance that a cash top-up can build towards, and therefore caps the relief. The **Basic Healthcare Sum (BHS)** does the same for MediSave. Both are in the parameter file by the year the top-up is made, because the relief for a top-up made in one year is claimed in the next year's assessment:

| Top-up made in | FRS | BHS |
|---|---|---|
| 2025 (YA 2026) | $213,000 | $75,500 |
| 2026 (YA 2027) | $220,400 | $79,000 |

The BHS is adjusted annually until a member reaches 65, after which it is fixed for life. A member who reached 65 in 2025 has a permanently fixed BHS of $75,500.

The **Enhanced Retirement Sum** is higher than the FRS, but a cash top-up above the FRS headroom attracts no relief even though CPF will accept it. Two different ceilings, and only one of them is a tax ceiling.

## CPF cash top-up relief in detail

Claimed automatically from CPF Board records, so the risk is not a missed claim - it is a top-up that produces no relief.

- **Cash only.** A transfer from the client's own CPF account does not qualify, however it is arranged.
- **Relief is capped twice.** $8,000 for the client's own accounts and $8,000 for family members combined, so $16,000 in total per YA. The family cap is *not* $8,000 per recipient; two parents topped up by $5,000 each still give only $8,000.
- **Relief is limited by the recipient's headroom below the FRS** - or below the Basic Healthcare Sum for a MediSave top-up - and not by the amount contributed. A recipient whose RA has already reached the FRS generates no relief at all, even where a top-up up to the Enhanced Retirement Sum is permitted and accepted.
- **For a spouse or sibling, the dependant's income in the year before the top-up must not exceed $8,000** (raised from $4,000 with effect from YA 2025). That test counts taxable income, tax-exempt income such as bank interest, dividends and pension, and foreign-sourced income whether or not it was remitted. It does not apply to parents, grandparents or a disabled dependant.
- **Matching grants now remove the relief.** Top-ups that attract a Matched Retirement Savings Scheme grant do not qualify from YA 2026, and top-ups attracting a Matched MediSave Scheme grant do not qualify from YA 2027.
- **No refunds.** Accepted top-ups cannot be reversed. With a $150,000 income the relief is worth up to $1,800 of tax; against the loss of access to $8,000 of cash, and against the $80,000 cap, decide deliberately.

## SRS

The Supplementary Retirement Scheme is voluntary, available to citizens, PRs, and foreigners, and is the main tax-relief lever for higher earners.

- **Contributions are relieved** up to an annual cap: $15,300 for citizens and PRs, $35,700 for foreigners. The relief is granted automatically, based on what the operator reports.
- **The relief requires tax residency for the YA following the contribution.** A PR or foreigner who leaves Singapore before that YA can lose the relief on contributions already made, with no refund. For this household that is a live risk on any relocation year, and it should be checked before the final contribution is made.
- **Contribute by 31 December** of the year (or the operator's earlier cut-off) for relief in the following YA.
- **No relief where the account is suspended at 31 December**, or where the amount contributed is withdrawn in the same year. A same-year contribution and withdrawal is tested in order: contribute first and the withdrawn portion simply loses its relief; withdraw first and the withdrawal is taxed in full *and* penalised.
- **Employer contributions are taxable remuneration** declared on Form IR8A, but the individual receives the relief for them. Do not treat an employer SRS contribution as free.
- **Investment returns are tax-free inside the account**, and only 50% of a qualifying withdrawal is taxable.

### Withdrawals

The mechanics are where the value is realised, and where a plan usually goes wrong.

- **50% of a qualifying withdrawal is taxable**, spread over a **ten-year window** that starts from the date of the first penalty-free withdrawal.
- **Penalty-free means on or after the prescribed retirement age**, which is the statutory retirement age prevailing at the time of the member's *first* contribution. It is 64 from 1 July 2026 - it was 63 before that - and rises to 65 from 2030. Later increases do not affect a member who has already contributed, so the age to plan against is the one at first contribution, not today's.

Because of that, the age is derived rather than read: `sg-parameters-2026.json` holds `srs_prescribed_retirement_age_schedule`, keyed by first-contribution date, and `scripts/srs_drawdown.py` returns the member's own age from it. Reading the current statutory age for a member who has already contributed is a live error - it moves the whole drawdown window.
- **Early withdrawal is expensive**: 100% taxable plus a 5% penalty. The penalty is waived on death, on medical grounds, on bankruptcy, and on a qualifying one-time full withdrawal by a foreigner who has held the account at least ten years and has been neither citizen nor PR for ten years.
- **The window is a deadline, not an allowance.** Except for life annuities, the balance is *deemed withdrawn* at the end of the tenth year and 50% of it is taxed in one hit. This is the counter-intuitive part worth stating plainly: the risk with SRS is not withdrawing too early, it is *never withdrawing*. A drawdown schedule belongs in every plan that has an SRS balance.
- **The tax-free capacity is $40,000 a year, not $40,000 of tax-free income.** Half the withdrawal is taxable, and the first $20,000 of chargeable income is taxed at nil. So $40,000 a year comes out tax-free over the window - but only for a member with no other taxable income and no other reliefs. Any other income eats the nil-rate band and the figure falls. Over a full ten-year window that is up to $400,000 out tax-free.
- **On terminal illness or death** the full withdrawal, or the balance deemed withdrawn on death, is exempt up to $400,000, reduced for prior penalty-free withdrawals and for the years already used in the window. Half of any excess is taxable.
- **No beneficiary nomination is possible.** SRS is the one account in the plan where a nomination cannot be made: the balance forms part of the estate and is distributed under the will, or under the law if there is none. For a household with dependent children this is a continuity point, not a tax point - the will has to cover it, and the executor may need probate before the SRS operator releases the funds.
- **Foreigners and PRs face withholding on withdrawal** at 24%, reduced to 15% on the conditions above, with the withheld amount creditable and any excess refundable.

## Life insurance relief in detail

This is the relief most often overstated, because the figure people remember is the $5,000 ceiling rather than the formula. Relief is the **lower** of:

1. $5,000 less the individual's own compulsory CPF contributions (and, for a self-employed person, compulsory MediSave or voluntary CPF contributions), measured in the year before the YA; and
2. the smaller of the premiums paid, or 7% of the insured value.

If the individual's own CPF contributions reach $5,000, the relief is **nil** however much premium was paid. For anyone in employment on a normal salary this is the usual answer, which is why the relief rarely matters for the household's main earner and may still matter for a lower-earning or self-employed spouse.

What does **not** qualify: accident, hospitalisation and health policies including MediShield and Integrated Shield Plans; disability policies including ElderShield and CareShield Life; riders under a life policy including total and permanent disability, critical illness and premium waiver riders; critical illness policies; endowment policies; and investment-linked policies where the investment component is a fundamental consideration. Where a policy bundles a life plan and a critical illness rider, only the life portion of the premium counts.

From YA 2026 the relief covers premiums paid by a wife on her husband's policy; before that it was limited to the individual's own policy and a husband paying for his wife's.

## Insurance and healthcare

MediShield Life is universal basic hospital cover. Integrated Shield Plans layer private or higher-tier cover on top and can be paid from MediSave within limits. CareShield Life provides basic long-term care income, and is usually well short of the cost of a real care event - quantify the gap rather than assuming the scheme is sufficient. Note the tax consequence while doing it: none of these premiums attract life insurance relief.

For a long-term care event, model the shortfall against actual nursing or home-care costs, and test what drawing that shortfall does to the portfolio.

## Property

Buyer's and seller's stamp duties are the main transaction taxes, and the additional buyer's stamp duty rate depends on residency status and the number of properties. Rates change; confirm current rates before advising.

Two recurring errors: counting the family home as a retirement income asset when no downsizing is planned, and counting CPF monies used for the property as an asset while ignoring that they must be repaid with accrued interest on sale.

## Parameter verification duty

Every value in `sg-parameters-2026.json` carries a source URL and, where it was checked, the date it was checked. Values that are still unconfirmed are marked with `"verified_on": null` and the scripts print a warning listing them.

Before an output goes to a client:

1. Run `scripts/check_params.py`. It reads the whole parameter file, not only the entries one script happened to use, and lists everything unverified or past its review window.
2. Confirm each one against its source URL and update the `verified_on` field.
3. Check for announced changes taking effect in the plan year - CPF rates in particular have been on a published multi-year schedule.
4. Re-check the relief cap and the residency tests against the plan year. Both change the value of everything downstream.

Primary sources:

- Individual income tax rates, residency tests, rebates, non-resident rates and withholding: `https://www.iras.gov.sg/taxes/individual-income-tax/basics-of-individual-income-tax/tax-residency-and-tax-rates/individual-income-tax-rates`
- Personal reliefs index, the $80,000 relief cap, and the list of available reliefs: `https://www.iras.gov.sg/taxes/individual-income-tax/basics-of-individual-income-tax/tax-reliefs-rebates-and-deductions/tax-reliefs`
- CPF cash top-up relief: `https://www.iras.gov.sg/taxes/individual-income-tax/basics-of-individual-income-tax/tax-reliefs-rebates-and-deductions/tax-reliefs/central-provident-fund-(cpf)-cash-top-up-relief`
- Life insurance relief: `https://www.iras.gov.sg/taxes/individual-income-tax/basics-of-individual-income-tax/tax-reliefs-rebates-and-deductions/tax-reliefs/life-insurance-relief`
- Earned income relief: `https://www.iras.gov.sg/taxes/individual-income-tax/basics-of-individual-income-tax/tax-reliefs-rebates-and-deductions/tax-reliefs/earned-income-relief`
- SRS contributions and tax relief: `https://www.iras.gov.sg/schemes/individual-income-tax/srs-contributions-and-tax-relief`
- Tax on SRS withdrawals: `https://www.iras.gov.sg/schemes/individual-income-tax/tax-on-srs-withdrawals`
- CPF contribution rates and wage ceilings: `https://www.cpf.gov.sg/employer/employer-obligations/how-much-cpf-contributions-to-pay`
- CPF interest rates: `https://www.cpf.gov.sg/member/growing-your-savings/earning-interest/interest-rates`
- CPF LIFE and retirement sums: `https://www.cpf.gov.sg/member/retirement-income`

The IRAS SRS pages and the CPF pages for interest rates and CPF LIFE payouts render some tables dynamically, so a plain page fetch may return navigation text with no figures. Read the rendered page or the linked PDF rather than concluding the value does not exist. The income tax rates, reliefs index, CPF cash top-up, life insurance, earned income and SRS contribution and withdrawal pages were fetched and read in full on 13 September 2026.
