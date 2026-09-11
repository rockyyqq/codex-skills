# Data provenance and freshness

A plan is only as good as its weakest figure, and the weakest figure is usually the
one nobody dated. This file sets the rule for where every number comes from and how
old it is allowed to be.

## Three classes of figure, never mixed

Every number in a deliverable is one of these, and the document says which:

| Class | What it is | How it is labelled |
|---|---|---|
| **Live** | Fetched from a market source, with a quote date | "HKD 79.85, close 11 Sep 2026" |
| **Statement** | Taken from a document the household holds — a policy schedule, a bank page, a CPF statement | "as stated on the schedule dated 13 Jun 2022" |
| **Assumption** | A return, a volatility, an inflation rate, a growth rate | "assumed, not measured" |

The distinction is not decoration. A live price that could not be fetched is **not** a
statement value and **not** an assumption; it is a gap, and the report says so.

## Every fetched figure carries its source and its date

A price without a date is unusable, because two sources will disagree and both be right
on different days. The same security quoted through two providers within one session
has produced two closes for the same position. Record both, and say which one the
working used.

State in one line, per deliverable:

- which figures were fetched, from where, and as of when
- which were taken from a household document, and the document's date
- which are assumptions
- which could not be obtained at all

## Freshness limits

| Figure | Treat as stale after |
|---|---|
| Holdings quantities | 90 days without household confirmation |
| Market prices | 5 trading days |
| Unit-trust NAVs | 5 trading days |
| Policy schedule values | 12 months |
| CPF balances | 12 months |
| Tax parameters | one year of assessment |

Past the limit, the figure is not used to support a conclusion. It can be shown as
context, labelled as stale, and the conclusion waits for a refresh.

## When a source fails

Market data sources rate-limit, block by address, and change their endpoints without
notice. A failed fetch is a normal event, not an error to paper over.

The rule is the same one `check_mandate.py` applies: **a value that could not be
verified is not silently replaced by the last one you had.** The holding keeps its
statement value, the report names it as not marked to market, and the reader can see
which parts of the output rest on fresh data and which do not.

Never report a pass, a limit check, or a performance figure on data that failed to
refresh.

## Practical notes

- **Prefer a stated date to a rounded number.** "About HKD 80" is worse than "HKD 79.55, 10 Sep".
- **Round to what the source supports.** A daily close does not justify four decimal places in a conclusion.
- **Two sources disagreeing is information.** It usually means different dates, or an adjustment for a corporate action, or one is a stale cache.
- **Corporate actions move prices mechanically.** A bonus issue or split changes the quoted price without anything economic happening. Unadjusted history will show a fall that did not occur. Before reporting a fall from a peak, check the series is adjusted.
- **A currency conversion needs its own date.** HKD 79.55 on 10 September and HKD 79.55 on 11 September are the same price in two different SGD values.
