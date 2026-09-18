# Data sources

What each source covers, what it fails on, and the traps found by using them.
Verify before relying, because entitlements and endpoints change.

## The catalogue

| Source | Covers | Fails on |
|---|---|---|
| **Broker gateway** (OpenD, 127.0.0.1:11111) | **Hong Kong and US** — price, history, **and fundamentals**: trailing and static P/E, P/B, EPS, trailing dividend and yield, market value, shares outstanding, 52-week range | **No Singapore entitlement. No A-share index entitlement.** Returns a permission error rather than failing quietly, which is the useful behaviour |
| **Yahoo Finance chart API** | Singapore, global indices, gold, oil, FX, government yields, and Hong Kong as a fallback | **Hong Kong history is unadjusted** — see the trap below |
| **China Securities Index Company** | CSI-series indices: level history, rolling P/E, dividend yield | **Carries no exchange-series index codes.** A valid index can be absent entirely |
| **Financial Modeling Prep** | **US large caps only** | Returns HTTP 402 for every Hong Kong and mainland ticker tested. Useless outside US large caps |
| **Eastmoney fund pages** | Fund holdings by quarter (`fundf10.eastmoney.com/FundArchivesDatas.aspx?type=jjcc&code=<code>`), NAV history | Top twenty only; feeder funds hide the underlying |
| **In-app browser** | Sites that block scripted requests — forums, and some financial portals | Not scriptable. Read manually and quote the result |
| **Institution product pages** | Deposit tier tables, account terms, product brochures | Marketing pages state maximums, not effective rates |

## The traps

**Unadjusted versus adjusted history.** This is the one that produced two
different technical readings for the same security on the same day — one
"extremely oversold", the other "mid-range". An unadjusted series carries an
artificial fall on the ex-dividend date, and inside a short momentum window it
distorts the reading badly.

> **How to tell, and how to reconcile.** Divide the trailing dividend by the
> price to get the yield, then divide it out of the higher 52-week high. If the
> result lands near the lower figure, the higher series is unadjusted. **State
> which basis every level comes from.**

**A hidden 31-day month.** A calculator quoting a monthly interest figure on a
31-day basis, annualised by multiplying by twelve, overstates the year by about
3%. Check what day-count the figure assumes before scaling it.

**The headline rate at an unstated balance.** Deposit accounts advertise maximum
effective rates that apply at a specific balance, to a specific tranche, subject
to categories that may each last only twelve months. Establish the rate **at the
balance actually held**, and the duration of each qualifying category.

**An index that a provider simply does not carry.** Absence is not invalidity.
When one provider returns nothing for a code, try another provider or the
exchange before concluding the instrument does not exist.

**Fund holdings that are not the portfolio.** A feeder fund's holding table
shows the direct sleeve. Percentages far smaller than any real weight are the
signal that the rest sits in the underlying fund and is not listed.

**Failing silently versus failing loudly.** The broker gateway returns a
permission error for an unentitled market, which is honest. Other sources return
an empty result that can be misread as "no data exists". **Treat empty and
forbidden as different things.**

## Recording a figure

Every figure carries:

- the source
- the retrieval date
- the market and session
- the currency
- the granularity, and whether the series is adjusted

Where a source gives no date — some forums serve none to a logged-out browser —
record that the date is missing rather than inferring one from the content.

## When a source fails

Say which one failed and what it cost the review. In one worked case the
decisive question — whether a dividend was covered by free cash flow — could not
be answered because no statements were reachable, and that limitation was the
honest headline of the review rather than a footnote.
