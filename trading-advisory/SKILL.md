---
name: trading-advisory
description: Run the household's separate trading stream - use outside tools to produce an independent, attributed, reviewable note on a specific listed security, log the call before the outcome, and leave the decision with the household. Use when the household asks for the separate trading stream, a TradingAgents run, or an independent read on a named ticker outside the plan. Not for plan questions, mandate checks or allocation (use wealth-advisory), not for a price-only question (use technical-analysis), and not for whether a name belongs in the plan (use investment-review).
---

# Trading Advisory

Run the household's separate trading stream. It sits **outside** the family plan on purpose: the
household wants outside opinions on named securities that it can read, weigh and decide on itself.
This skill's job is to produce those inputs honestly and keep a record that can be checked later.

It is not a plan activity, and it does not inherit the plan's rules. Those still govern the plan.

## Where this sits

| Skill | The question it answers |
|---|---|
| `wealth-advisory` | Does this belong in the plan, and at what size? |
| `investment-review` | Is this investment, or this claim about it, sound? |
| `technical-analysis` | What does the price history show, with no claim attached? |
| **`trading-advisory`** | **What do outside tools say about this name, and what exactly would I be betting on?** |

If the request is really a plan question, it belongs to `wealth-advisory`. If it is one security
with a claim attached, `investment-review` does it better for free. Reach for this skill when the
household specifically wants the outside stream.

## The wall

Five rules, and they are the reason this can be an outside stream at all. They are mirrored in
`TradingLab\README.md`, which is the household-facing copy.

1. **Nothing here moves a plan limit.** A limit changes only by a written decision made before the
   trade.
2. **Nothing here becomes a plan operation.** The plan's task list gains no item from this stream.
3. **Every output is labelled with what produced it** - tool, version, model, and run date. Output
   without that label is not usable.
4. **Tool output is an opinion, not evidence.** It never enters a fetched figure, a statement value,
   or a planning assumption.
5. **The plan never reads this.** The daily brief and the monthly mandate check do not touch this
   folder, and nothing here is quoted in a plan deliverable.

## Workflow

1. **Get the ticker and the question.** What is being asked about it - a view, a comparison, a check
   on something the household already believes? If there is no question beyond "run it", say so in
   the note rather than manufacturing one.
2. **Run the engine.** `references/lab.md` has the location, the environment, the command, the cost
   and the failure modes.
3. **Write the note** in the format below, into `TradingLab\runs\`.
4. **Log it before the outcome is known.** Add the row to the run log in `TradingLab\README.md` -
   date, tool, version, model, ticker, output file, and the decision the household took. Logging
   after the result is known destroys the only thing that makes this stream checkable. Re-read
   `references/evaluation.md` before running a batch.

## The note

Keep the case reading and the price reading in separate sections and never merge them into a
verdict. Where they disagree, name the disagreement and stop; price and narrative agreeing is one
piece of evidence, not two.

```
| | |
|---|---|
| **Instrument** | What it is, in one line |
| **Run** | Tool, version, model, analysis date, and that the run was one sample |
| **What the tool said** | Its rating, quoted, attributed, with the date |
| **The case** | What is being claimed, by whom, and whether it is checkable |
| **Price reading** | From technical-analysis, unmodified, with timeframe and adjustment basis |
| **Valuation** | Against a named hurdle rate, not a bare multiple |
| **Already owned** | Look-through, with the fund and the weight |
| **What would invalidate it** | The price, level or fact at which the reading is wrong |
| **What this does not settle** | The open questions, named |
| **Decision** | The household's, dated, recorded before the outcome |
```

## Non-negotiables

**The tool's rating is quoted, never adopted.** "TradingAgents rated this Buy on 2 October 2026,
model X" reports an output. "This is a buy" states a conclusion the stream has not earned. The
household is the one that decides, so the note has to leave the decision visibly open.

**One run is one sample.** Runs of the same ticker and date can differ, by the project's own
statement. Record the run that happened; never present it as the tool's considered view in general.

**No size without an account and a risk figure.** A level without the account size and the risk per
trade is not actionable arithmetic, so a size appears only when the household has supplied both for
this stream - and it is labelled illustrative even then.

**Say CANNOT JUDGE when it applies.** No reachable data, no run, no statements, no key - say so
plainly rather than assembling a thin note that looks complete.

**Never let this stream leak into the plan.** Not a limit, not a task, not a figure, not a phrase.
The five rules above are the whole reason the household can hold two views at once.

## References

- `references/lab.md` - where the lab lives, the Python environment, how to run a job, what each run
  costs, and what to do when a run fails.
- `references/evaluation.md` - the only way to find out whether any of this has value:
  pre-registration, the do-nothing benchmark, out-of-sample dates, and sample size.

