# Finding out whether any of this works

One run gives one opinion. It cannot tell the household whether the tool decides well, and the
household has already said it will carry the risk. This file is about making that risk a real
decision rather than an unfalsifiable one: you cannot price a risk you have no way to measure.

## The three tests, before anything is trusted

**1. Pre-register.** Write the call, the date, the model and the reason **before** the outcome. The
run log in `TradingLab\README.md` is the mechanism. A call recorded afterwards is not evidence of
anything, and a stream that keeps no pre-registered record can never be judged - only believed.

**2. Beat doing nothing.** The benchmark is not zero, and it is not another trading idea. It is the
household's own alternative: buy the index, or do nothing at all. If the stream does not beat
"do nothing" after costs, the correct reading is that it added cost and noise, and the question is
settled. State the benchmark in the note, every time.

**3. Use dates the model could not have read.** The framework can restrict its **data** to what was
published before the analysis date - that is a real and well-implemented protection. It cannot remove
what the **model** already read while it was being trained. So a backtest over a period the model saw
during training is contaminated: the model may not be forecasting, it may be recalling. Ask for the
model's training cutoff, and treat any period before it as in-sample and therefore as marketing.

## How much evidence is enough

- **A handful of calls proves nothing**, in either direction. Three wins is not a method; three losses
  is not a refutation.
- **A hit rate alone is not an edge.** Ten winners of one unit and one loser of fifteen units is a
  losing stream with a 91% hit rate. Record the size of the wins and losses, not just how often the
  direction was right.
- **Compare against the same period's benchmark**, not against cash. A rising market makes every
  method look clever.
- **Count the failures.** Failed runs, abandoned tickets, and calls quietly not acted on all belong in
  the log.

## What to record, so a later check is possible

Per run: date and time, tool and version, the exact model IDs, the ticker, the analysis date, the
rating as issued, the reasoning in one line, the price at the time, the benchmark level, the decision
taken, and the run's outcome once the holding window has passed. Anything less and the later check is
a memory test.

## What would count as evidence of value

Pre-registered calls, scored against the household's own do-nothing alternative, over dates after the
model's training cutoff, with enough of them for the result not to be luck - and with the losses
included. Until that exists, the honest description of this stream is: **interesting, unmeasured.**

## What a good result would not mean

It would not license a size, and it would not move a plan limit. A stream that has earned a small
ring-fenced allocation has earned exactly that, and the plan's own rules still decide whether
anything joins the plan.

