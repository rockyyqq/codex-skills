---
name: technical-analysis
description: Read a listed security's price and volume history - trend, support and resistance, moving averages, momentum and volatility indicators, chart patterns, and the risk arithmetic that converts an entry and a stop into a position size. Use when the request is about a specific chart, what an indicator is saying, where a level sits, or how to size a position. Not for household portfolio construction, allocation or mandate checks (use wealth-advisory), and not for appraising evidence or verifying citations (use research).
---

# Technical Analysis

Read the chart, then say what it does and does not support. The failure mode this skill
exists to prevent is technical analysis presented as forecasting - a pattern named with
confidence and a direction implied, when all that has been established is where the price
has been.

## What this can and cannot do

**State the limits before the reading, not after.** Technical analysis describes the
distribution of past prices. It does not know why a price moved, what it will do next, or
whether a pattern will resolve as it did last time.

Three things follow, and they belong in every output:

- **An indicator is a transformation of price.** A moving average average, an RSI a ratio,
  a MACD a difference of two averages. None of them contains information the price series
  did not already contain. They reorganise; they do not inform.
- **Pattern identification is partly retrospective.** A head and shoulders is obvious once
  it has completed and ambiguous while it forms. Anyone who labels a pattern in real time
  is making a judgement with a substantial error rate, and should say so.
- **A win rate is not an edge.** Ten winners of one unit and one loser of fifteen is a
  losing system with a 91% hit rate. Report the payoff, not just the frequency.

Say plainly when a question cannot be answered from price. "Where is support" has an
answer. "Will it hold" does not.

## Workflow

1. **Get real data, and say where from and as of when.** Never analyse from memory or from
   a remembered price. `scripts/analyse.py` fetches daily history and computes the standard
   measures; see `references/data-sources.md` for the free sources that work.
2. **Establish the structure before the indicators.** Trend direction on the chart's own
   timeframe, the levels that have mattered, whether volume confirms the moves. Read
   `references/chart-reading.md`.
3. **Then the indicators, and only the ones that answer the question.** A trend question
   does not need the stochastic. Read `references/indicators.md`.
4. **Convert any entry into a size.** If the output includes a level to act at, it must
   include the distance to the stop and the resulting position size. Read
   `references/risk-and-sizing.md`.
5. **State what would invalidate the reading.** Not "this could go either way", but the
   specific price or level at which the interpretation is wrong.

## Non-negotiables

**No target without an invalidation.** A price objective with no level at which the idea is
admitted to be wrong is a prediction, not an analysis.

**No position size without an account and a risk figure.** "Buy at 79" is not advice that
can be acted on. "Buy at 79 with a stop at 74, risking 1% of a S$100,000 account, is 200
shares" is.

**Indicators do not stack into confidence.** RSI, MACD and a moving average are all
functions of the same prices. Three of them agreeing is one piece of evidence counted
three times, not three confirmations. Say so when a reading leans on the same data twice.

**Timeframe must be declared.** A daily uptrend and a weekly downtrend are both true. An
analysis that does not name the timeframe cannot be wrong, which is the same as being
useless.

**No strategy without a track record.** Where a question invites a rule - "should I buy
when it crosses the 50-day" - the honest answer is that the rule needs testing on data
out of sample before it is believed, and that a rule which worked on one market in one
period is a hypothesis.

**Sizing does not travel into a plan.** This skill's position-sizing arithmetic belongs to
a trading decision, and it needs an account and a risk figure to mean anything. When a
reading is used inside a household plan - the `wealth-advisory` skill - the reading travels
and the sizing does not: a planning deliverable carries no entry, stop, target or share
count, and the household's agreed mandate and limits prevail over anything read off a chart.
The data layer is the shared part: `references/data-sources.md` is the catalogue both skills
fetch from.

## Scripts

`scripts/analyse.py` fetches daily OHLCV for a symbol and reports the structural and
indicator readings in one pass: trend state, moving averages, RSI, MACD, ATR, Bollinger
position, volume against its average, and the recent swing levels.

```
python scripts/analyse.py --symbol 1211.HK --period 1y
python scripts/analyse.py --symbol AAPL --json out.json
```

It reports what the data shows. It does not rank, score or recommend, and it says so in
its own output.

`scripts/opend_probe.py` tests whether the household's broker gateway (Futu or moomoo
OpenD) is reachable on `127.0.0.1:11111` and, if it is, reads a snapshot and daily bars
through it. OpenD must be running and logged in, and the script needs normal permissions
rather than the sandbox. See `references/data-sources.md`.

`scripts/valuation.py` reads official price-earnings and dividend-yield figures for China
index codes from the China Securities Index Company, and converts the P/E into an earnings
yield - the figure that can be compared with a bond yield. Price history says where an index
has been; only valuation says whether it is cheap.

## References

Read only what the question needs.

- `references/chart-reading.md` - trend, support and resistance, volume confirmation, chart
  patterns and what they are worth, and multiple-timeframe analysis.
- `references/indicators.md` - the standard indicator set, what each measures, and the
  misreadings that are common enough to be worth naming.
- `references/risk-and-sizing.md` - stops, R multiples, expectancy, position sizing, and
  why a hit rate alone tells you nothing.
- `references/data-sources.md` - the free sources that supply price history, what each
  covers, and how to tell a failed fetch from a flat market.
