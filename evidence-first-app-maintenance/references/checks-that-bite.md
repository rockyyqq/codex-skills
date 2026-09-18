# Proving a suite bites

Test-driven development covers **new** tests: write it, watch it fail, then make it pass. This file is
about the other half -- a suite that **already exists and already passes**, in an app that has been
alive for weeks or years. The question is not "is there a test?" but "would this suite notice if the
rule it describes stopped being true?"

An untested rule and a rule whose test cannot fail look identical in a green report. Both are
unprotected; only one of them looks protected.

## The method: break the rule, watch the suite notice

For each rule you care about, apply a small, deliberate defect to a throwaway copy of the code and run
the suite. If the suite stays green, the rule is not actually checked.

1. **Baseline first, always.** Run the suite unmutated before any mutation. A tree that cannot build or
   load will otherwise report *every* rule as caught, and the sweep will look perfect while proving
   nothing.
2. **One defect at a time**, applied by exact text anchor, then restored -- including on failure. If the
   anchor is missing, say `SKIP` loudly rather than counting the rule as covered: code moves, and an
   anchor that silently stops matching is a check that silently stopped checking.
3. **A missing verdict is not a pass.** If the suite dies before printing its summary, that run proves
   nothing about the rule. Report it as `UNPROVEN`, not as caught. A suite that crashes is not a suite
   that objected.
4. **Name the misses, do not just count them.** "94 of 95" costs the next person an hour of hunting;
   "not caught: *the comparison measures from a different day than the lines do*" is a finding.
5. **Filter for speed**: a substring flag that runs one area's rules is what makes this a habit rather
   than an occasion.

## When a check cannot fail, fix the check -- not the mutation

A rule that survives its own mutation is a finding, and there are three honest outcomes:

- **The check was testing a consequence, not the fact.** Two quantities that move together can never
  disagree, so comparing them proves nothing. Pin the fact itself: the day the chart measures from,
  the identity of the thing, the field that must survive.
- **The check was too tolerant.** Rounding, a wide epsilon, or a `>=` where the rule is exact will
  swallow small defects. Compare what the rule actually says.
- **The mutation was not a defect.** If the "broken" version behaves identically on every observable
  path, it is a bad mutation, not a missed check. Say so in the runner's comments and leave it out --
  do not weaken the check to make the sweep look clean.

Prefer, in this order: pin the fact -> tighten the comparison -> replace the mutation.

## Writing a check that can fail, the first time

- **Watch it fail before you believe it.** Write the check, run it against the unfixed code, and read
  the failure message. If it passes before the fix, it is not testing the fix.
- **A failure message must name the thing**: the value against the expected value, the element, the
  account. A check that fails with "false" costs another run to diagnose.
- **Compare like with like.** Reading rendered markup is reading a *re-serialisation*: what you wrote
  as `<circle ... />` may come back as `<circle ...></circle>`. Normalise both sides, or assert on the
  model rather than the markup wherever the model is available.
- **Measure the thing, not a proxy for it.** A byte size once passed an icon that was 68% background;
  measuring the actual pixels' spread caught it. File size, exit code, "it rendered something" -- all
  proxies.
- **One claim per check.** Two claims in one check means a failure tells you less than it could.

## Reading a harness's verdict safely

- Read the report from the region the harness writes (its own output element), not from the whole
  dumped page: page source, comments and templates can contain report-shaped text, and a parser will
  happily read those numbers instead.
- Never spell a verdict out inside a comment in the thing being parsed.
- Keep the counts machine-readable (`N passed, M failed`) so a runner can assert on them, and keep the
  human detail beside them.

## Isolating areas, so one failure names itself

A single suite file with one `try` means one exception erases every other result and names nothing.
Split checks by **area**, and give each area its own `try`: the failure then reads
*"stage 3 - kid mode did not finish -> rowsIn is not defined"*, and the other areas still report. When
splitting an existing single-file suite, keep the strongest possible invariant -- that the same checks,
with the same names, in the same order, still produce **the same lines** -- and diff them to prove it.
