# Gates

A planning workflow stops being reliable in one specific way: a check fails and nobody
decided what should happen next, so the output carries the failure forward as
commentary. This file names the four checkpoints so that cannot happen quietly.

Every gate answers three questions. If any is unanswered, the gate is not a gate.

1. What condition triggers it?
2. What happens when it fails — block, loop back, ask the household, or stop?
3. Who resumes, and from where?

## The four types

### Pre-flight gate

**Fails when:** a precondition the work depends on is missing.

**Behaviour:** block. Produce nothing until it is met, because everything downstream
would rest on a gap.

For this skill, a pre-flight gate is triggered by:

- no dated holdings file
- a fetched price that failed to refresh
- an assumption the household has not seen
- a required document the household has not supplied

**Recovery:** obtain the missing input, then start.

### Revision gate

**Fails when:** output exists but does not meet a stated requirement — most commonly a
mandate breach, or a deliverable that fails `scripts/validate_deliverable.py`.

**Behaviour:** loop back once with the specific failure named, and state what changed.
Cap the loop. If the same failure recurs, it is not a drafting problem.

**Recovery:** fix and re-check. On a second failure, escalate.

### Escalation gate

**Fails when:** a limit and a target conflict, and the choice changes the plan.

**Behaviour:** stop and ask the household. **Never choose for them, and never move a
limit to make a target fit.** Their own rules are the constraint; a limit relaxed to
accommodate a position is no longer a limit.

Triggered by:

- a holding that breaches a limit already agreed
- a purchase decision that contradicts an agreed contribution rule
- two reasonable readings of an instruction that lead to different plans
- a stress test that fails at every allocation, which means the spending assumption is the problem

**Recovery:** the household decides. Record the decision, the date and the reason, and
say plainly whether the limit moved or the position did.

**This is the load-bearing gate.** A plan whose limits move whenever a position
breaches them has stopped measuring anything, and the failure is invisible in the
output — every number still looks defensible.

### Abort gate

**Fails when:** continuing would produce something misleading or unusable.

**Behaviour:** stop, preserve what exists, and name the reason. Do not emit a partial
answer that reads as complete.

Triggered by:

- holdings stale beyond the freshness limit in `references/data-provenance.md`
- the data layer unavailable and no verifiable fallback
- a deliverable that cannot carry its assumptions
- any point where the work would have to invent a number to continue

**Recovery:** remove the cause, then restart from the preserved state.

## Where each gate sits in this skill's workflow

```
[Pre-flight] holdings dated, prices fresh, assumptions stated   -> no: block, ask
        |
     compute  (plan_projection.py, portfolio_risk.py)
        |
[Revision]  mandate check and validate_deliverable.py           -> fail: fix once, re-check
        |                                                        -> fail again: escalate
        |
[Escalation] does any agreed limit conflict with a stated target? -> yes: stop, ask
        |
     present
        |
(if data cannot be verified at any point)  [Abort] stop and say so
```

## Working rule

When a check fails, the next sentence in the report is the gate decision, not a
softening of the failure. "The mandate check returns BREACH on one limit, the
household has not yet decided whether to change the position or the limit, and no
recommendation is offered until they do" is a finished answer. A breach mentioned in
passing and then worked around is not.
