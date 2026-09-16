# Deliverables

Structures for the documents this skill produces. The skeleton is adapted from the workflow shapes in Anthropic's `financial-services` repository; the additions are the assumptions, verification, and disclosure sections that make the work defensible in Singapore.

This skill is used for a household's own planning rather than a client book. The documents are therefore written for the family to decide on, and they carry the same discipline an adviser would apply: assumptions visible, sources named, and the limits of the work stated rather than implied.

## Every document carries these

1. **Assumptions page** - every material assumption, its value, and where it came from: client documents, the client's own instruction, or a named official source.
2. **Parameter verification status** - which dated parameters were confirmed against their source and which remain unconfirmed. The scripts print this for you.
3. **Basis note** - today's dollars or nominal; gross or net of fees; reporting currency.
4. **Scope and status statement** - a draft prepared for the household to decide on, not licensed advice, and a named next step for a professional where one is needed.
5. **Risk mandate** - the limits the portfolio is measured against, in the household's own words.
6. **Protection status** - what the death, disability, illness and care layers currently cover, and where the gaps are.
7. **Tax residency and relief position** - each spouse's residency for the plan year, the reliefs claimed against the $80,000 cap, and any contribution that would fall above it. Residency decides whether any relief exists at all, so this comes before the numbers that depend on it.
8. **Goals with dates and costs** - each goal funded and tested on its own date, not only inside the retirement projection.

## The recommendation record

A recommendation is not a sentence. Each one carries, beside it rather than in an
appendix:

| Field | What belongs there |
|---|---|
| Recommendation | The decision being put to the household, in one sentence |
| Rationale | Why this, in terms of their stated goals and constraints |
| Expected benefit | In dollars or probability, with the assumption it depends on |
| Risk | What could make it wrong, including the case where it works but does not help |
| Alternatives considered | What else was on the table and why it was not chosen |
| Assumptions | Every figure it rests on, labelled as a fact or an assumption |

`scripts/validate_deliverable.py` fails a document that carries recommendations
without alternatives and assumptions beside them. Where a recommendation needs a
licence to act on - a specific security or insurance product - the record stops at
the analysis and names the professional who acts.

## Retirement planning pack

1. Situation summary - household, goals with dates and costs, and what prompted the exercise
2. Assumptions and their sources
3. Cash-flow projection - accumulation years, then drawdown
4. Retirement sustainability - probability of success, the poor-tail depletion age, and the withdrawal rate
5. CPF and SRS position - balances, projected CPF LIFE income, SRS drawdown schedule across the ten-year window
6. Scenarios - the stress table from `planning-methods.md`, with the base case first
7. Recommendations, prioritised, each tied to the analysis that supports it
8. Action list with owners and dates
9. Open items and what is still unconfirmed

## Client review pack

Prepared for the adviser, not the client. Sections: relationship and household summary; holdings and recent activity; performance against the benchmark named in the investment policy statement; allocation drift and any band breaches; planning items that moved since the last meeting (income, health, family, property, tax); three to five talking points; proposed actions; and the questions to ask before the next meeting.

## Performance report

Cover; executive summary; performance by account and household against the policy benchmark; allocation against target; holdings detail; market commentary written for this household's level of sophistication; activity summary including contributions, withdrawals, income received, and fees charged; planning notes; disclosures.

Singapore-specific handling: there is no capital gains tax, so do not carry over a "tax cost of rebalancing" line from US templates. Do reflect foreign withholding tax on dividends, SRS withdrawals if any occurred, and the fee total in dollars and as a percentage. Performance is stated net of fees unless the client requires gross, and if gross is used, say so prominently.

## Investment proposal

Firm and service model; the household's situation restated in their own terms; proposed strategy and why it fits; expected range of outcomes with the assumptions visible; fees stated in dollars as well as percentages, including underlying fund costs; what the service does not include; onboarding steps and timeline; disclosures.

Do not include a performance projection that the assumptions cannot support, and do not compare against an index the household could not actually hold.

## Rebalancing worksheet

Target allocation and bands from the investment policy statement; current allocation by account; drift in percentage and dollars; positions outside band; proposed trades with account, direction, amount, and estimated transaction cost; the new contribution direction if that is being used instead of trading; before-and-after allocation; and the date the sheet was prepared.

Where the household holds SRS or CPF-related assets, state explicitly which accounts are locked and which are flexible, because that constraint usually decides where the trade happens.

## Family financial plan

1. Situation summary - the household, its goals with dates and costs, and what prompted the plan
2. Risk mandate, in the household's own words
3. Protection review - death, disability, illness and care, with the gaps named
4. Assumptions and their sources, with assumptions clearly separated from facts
5. Cash flow through the working years, including any phase change such as a relocation
6. Retirement sustainability - probability of success, the poor-tail depletion age, and the withdrawal rate
7. Currency plan - what is held in which currency, what will be spent in which currency, and the path between them
8. Portfolio risk check - true look-through exposure and whether the mandate is met
9. Education funding, with fees in the currency they will actually be paid in
10. Recommendations, prioritised, each tied to the analysis supporting it
11. Action list with owners and dates, and what still needs a professional

## Annual review

A short document, written to be read once a year rather than filed. What changed in the household; what changed in the world; whether the mandate still fits; performance against the policy benchmark; whether any limit was breached; what the previous year's actions produced; and the two or three decisions the coming year actually requires.

## Net wealth statement

One page. Assets by account and currency, CPF and SRS balances shown separately because of their different access rules, liabilities, and the net position. Where a holding sits in a foreign currency, show both the local value and the reporting-currency value, so the effect of currency movement is visible rather than buried in a return figure.

## Continuity pack

The document that matters if something happens to both parents. It is not an investment document and it should not contain passwords.

1. Who to contact - adviser, lawyer, accountant, insurance agent, employer
2. Where the accounts are held, and in whose name
3. Existing cover and how to claim, with policy numbers
4. CPF and SRS nominations, and where the originals are kept
5. The will, the named guardian for the children, and where it is held
6. Lasting Power of Attorney, and what it does and does not cover
7. Property, loans, and any guarantees given
8. The plan itself, in plain language, and what the surviving spouse should and should not do first
9. A short statement of what the family wanted

Review it after every life event, and tell one other person that it exists and where it is.
