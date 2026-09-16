# Indicators

Every indicator here is a function of the price and volume series. Nothing in this file
adds information that was not already in the data; the value is in seeing a particular
property of the series clearly.

When several indicators from the same family agree, that is one observation, not several.

## Moving averages

A mean of the last *n* closes. Its only real properties are the length and whether it is
simple or exponential.

- **Short (10-20)** - turns quickly, whipsaws often.
- **Medium (50)** - the common trend filter for daily charts.
- **Long (200)** - the line most participants watch; its breach is treated as a regime
  change whether or not that is what it is.

**What it tells you.** Whether the recent average price is above or below an older one, and
the slope. Price above a rising 200-day average is a different environment from price below
a falling one, and the distinction is worth stating.

**Common misreading.** A moving average is not support or resistance in any mechanical
sense. It is a line many people *watch*, which gives it a mild self-fulfilling property at
the most-watched lengths and nothing at the others. Price crossing a moving average is not
a signal; it is a description.

**The lag.** A 200-day average responds to today only one-two-hundredth. It is slow by
construction, and that is the point.

## MACD

The difference between two exponential averages (usually 12 and 26), with a 9-period signal
line of that difference, and a histogram of the gap between them.

**What it tells you.** Whether medium-term momentum is strengthening or weakening, and
whether it is above or below its own recent average.

**Better use than crossover signals.** The histogram's direction - expanding or contracting
- often turns before the lines cross. A crossover alone is late by construction, because it
requires the move to have already happened.

**Divergence.** Price making a higher high while MACD makes a lower high is worth noting as
a change in momentum. It is also extremely common and frequently resolves upward. It is an
observation, not a reversal signal.

## RSI

A ratio of average gains to average losses over *n* periods (usually 14), scaled to 0-100.

**What it tells you.** The proportion of recent movement that has been upward. That is all.

**The misreading worth naming.** Above 70 is called "overbought", and in a strong uptrend
RSI can stay above 70 for months. Selling an uptrend because RSI is high is one of the most
reliable ways to underperform the asset. RSI measures the *character* of recent movement,
not the likelihood of a reversal.

**Where it is more useful.** Below 30 in a range-bound market, and extreme readings at any
level alongside a named support or resistance zone.

**Divergence**, as with MACD, is an observation about momentum and not a signal.

## Bollinger Bands

A moving average with bands two standard deviations above and below.

**What they tell you.** Where price sits relative to its recent distribution, and whether
volatility is expanding or contracting. The width of the bands *is* the volatility measure.

**The misreading.** Touching the upper band is not a sell signal. In a trending market
price rides the band. What the bands are good for is recognising a squeeze - unusually
narrow bands - which indicates that a large move is likely and says nothing about its
direction.

**Statistically.** About 95% of observations fall inside two standard deviations *if* the
returns are normally distributed. They are not, which is why the price closes outside the
bands more often than the arithmetic suggests.

## ATR

The average true range over *n* periods: the average distance the price travels, including
gaps.

**The most useful of the set, and the least used as a signal.** ATR does not predict
direction. It measures how much the instrument moves, which is exactly what a stop
distance and a position size need.

A stop one ATR away will be hit by ordinary noise. A stop three ATRs away is a real level.
This is why ATR belongs with sizing, not with entry.

## Stochastic

Where the close sits within the recent high-low range, scaled to 0-100.

**What it tells you.** How far into its recent range the price closed. Sensitive, fast, and
prone to giving the same reading dozens of times in a trend.

**The misreading.** As with RSI, "overbought" in an uptrend is a description of strength,
not a warning.

## ADX

Measures the *strength* of a trend without its direction. Above roughly 25 indicates a
trending market; below 20 a range.

**Its real use is choosing which tool to apply.** A trending reading says use trend logic;
a range reading says use level logic. Applying trend logic in a range produces repeated
losses, and this is the indicator that would have said so.

## Volume measures

- **On-balance volume (OBV)** - a running total, adding volume on up days and subtracting
  on down days. A crude proxy for accumulation.
- **Volume against its average** - the simplest and most useful. Report the ratio.
- **Volume at price (profile)** - where the most volume traded, which maps the levels with
  the most settled positions.

## Combining indicators honestly

The standard mistake is stacking. RSI, MACD, stochastics and a moving average all derive
from the same closes. Four agreeing is one piece of information counted four times.

The only genuinely independent inputs on a price chart are **price**, **volume**, and
**time**. Everything else is arithmetic on those three. If an analysis uses two indicators
from the same family, say that it is one observation.

The useful combinations are across families: **trend** (moving average, ADX), **momentum**
(MACD, RSI), **volatility** (ATR, bands) and **volume**. One from each, and only when each
answers part of the question.
