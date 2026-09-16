# Risk and position sizing

This is the part of technical analysis that is arithmetic, and therefore the part that can
be right or wrong. An entry level is a judgement; a position size is a calculation.

## Every idea has three numbers

**Entry, stop, target.** An analysis that gives one or two of them cannot be acted on and
should not pretend to be actionable.

The stop is the price at which the reading is wrong - not a comfortable distance, not a
round number, but the level at which the reason for the trade no longer exists. If that
level is far away, the trade is smaller. It is never the other way round.

## R multiples

Define **1R** as the distance from entry to stop, expressed in money at the chosen size.
Then every outcome is measured in R, not in currency.

- Risking S$1,000 with a stop 5% away: 1R = S$1,000.
- A winner at +15% with a 5% stop is +3R.
- A loser is −1R by construction.

Quoting outcomes in R strips out account size and makes a record comparable across
positions and across time. A system's quality is visible in R terms and invisible in
currency.

## Expectancy

```
Expectancy (in R) = (win rate x average win in R) - (loss rate x average loss in R)
```

Worked example, and the reason hit rate alone is meaningless:

| System | Win rate | Average win | Average loss | Expectancy |
|---|---:|---:|---:|---:|
| A | 70% | +1R | −3R | **−0.2R** |
| B | 40% | +3R | −1R | **+0.6R** |

System A wins seven times in ten and loses money. System B wins four times in ten and
makes money. **A high win rate with poor payoff is a losing system**, and it is the most
common shape of a losing system, because taking profits early and holding losses feels
like competence.

This is the arithmetic behind the household pattern of small realised gains and large
unrealised losses.

## Position sizing

The standard formula:

```
Position size = (Account x risk per trade) / (Entry - Stop)
```

Worked: a S$100,000 account, 1% risk = S$1,000. Entry 79.00, stop 74.00, so the stop
distance is S$5.00 per share. Size = 1,000 / 5 = **200 shares**. Position value S$15,800,
which is 15.8% of the account.

Two things this makes visible:

- **The stop distance sets the size, not the conviction.** A wider stop means a smaller
  position for the same risk.
- **Small caps and volatile instruments produce small positions.** A stock with a 20% stop
  distance takes a quarter the position of one with a 5% stop, at the same risk.

## Risk per trade, and why it is usually 0.5-2%

At 1% per trade, ten consecutive losses cost about 9.6% of the account. At 5% per trade,
the same run costs about 40%, and recovering from 40% requires a 67% gain. The number is
not about confidence; it is about surviving a losing streak that will arrive.

Ten losses in a row at a 40% win rate has a probability of roughly 0.6% per run of ten. Over
several hundred trades it is close to certain.

## Correlation and total exposure

Risk per trade is not portfolio risk if the positions are correlated. Three positions in
the same sector at 1% each is closer to a 3% bet on one thing. Cap total open risk at a
figure the account can lose and still function - commonly 4-6% - and count correlated
positions as one.

## What a stop is not

- **Not a prediction.** It is the price at which the analysis has failed.
- **Not a limit on the loss.** A gap through the stop fills lower. Sizing must assume the
  loss can exceed 1R.
- **Not a substitute for size.** A tight stop on a large position is still a large position.

## Reporting format

When an analysis includes a level to act at, use this structure:

```
Entry     79.00
Stop      74.00        (the prior swing low, and the level at which the setup fails)
Target    89.00        (the prior high; a 2R objective)
Risk      1% of account = S$1,000
Size      200 shares   (S$15,800, 15.8% of the account)
Reward    2.0R
Invalidation   a daily close below 74.00
```

Six numbers, and the last one is the only one that is a fact rather than a judgement.
