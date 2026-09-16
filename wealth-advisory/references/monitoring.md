# Monitoring

A plan that is only tested when someone remembers to test it is not monitored.
This file sets what runs, how often, and what each kind of alert means - so an
observation is never confused with a breach, and a breach is never softened into
an observation.

## What runs, and when

| Cadence | What runs | Why this interval |
|---|---|---|
| Monthly | `refresh_prices.py`, then `check_mandate.py` | A limit can be breached quietly between annual reviews; this is the cheapest check that catches it |
| Annual | The full review: goals, protection, tax position, projection, mandate | Income, reliefs, tax residency and the retirement sums all move on a yearly cycle |
| Event-driven | The same review, triggered early | A birth or death, employment change, property purchase or sale, immigration or residency change, relocation date change, a windfall, or any change to CPF/SRS/tax rules |

The monthly run belongs on a schedule rather than on memory. A recurring reminder
that runs the two scripts and reports **only when something changed** is the
difference between a plan that is watched and a plan that was watched once.

## Four alert classes

**1. Mandate breach.** A hard, portfolio-level limit failed. It names the limit,
and it goes to the escalation gate: the household chooses whether the position or
the limit moves, and the decision is recorded with its date and reason. A breach is
a fact about what is held.

**2. Assumption-dependent breach.** Volatility or estimated worst-case fall has
failed, on the return and correlation assumptions supplied. This says the
assumptions imply a breach; it does not say anything was measured. Re-examine the
assumptions before reacting to the number.

**3. CANNOT JUDGE.** The data cannot support the check: the holdings are stale past
their confirmation limit, a price failed to refresh, a quote is past the five
trading-day limit, or the config is incomplete. **This is not a pass.** The limits
were not checked.

**4. Proactive observation.** Something is worth a decision but no limit has
failed. These are the observations that make the difference between a dashboard and
a monitor:

- cash above the buffer by a material amount, and what it is doing there
- a goal behind its own schedule, with the monthly gap
- concentration building up through appreciation rather than purchase
- a deadline approaching: the end of the SRS withdrawal window, a re-entry permit,
  a fixed-rate loan reset, a fee falling due
- a life event recorded in the file that the plan has not been re-run against

An observation states the position, the size of the decision and the options. It
does not issue an instruction: no buy or sell language, no entry price, no target,
no share count. The household or a licensed professional decides.

## What to say when something fires

The next sentence after a failed check is the gate decision, not a softening of the
failure. "The mandate check returns BREACH on the regional limit, the household has
not yet decided whether to change the position or the limit, and no recommendation
is offered until they do" is a finished answer.

## Keeping the monitor honest

- A pass has to be earned. If the run used stale data, the output says CANNOT
  JUDGE and names what was stale.
- Every alert carries its as-of date and its source, like any other figure.
- If the monthly run produces the same observation three times without a decision,
  the decision is the missing input, not more monitoring.
- Do not let an alert change the mandate by itself. Limits move only through the
  escalation gate, with the household's decision recorded.
