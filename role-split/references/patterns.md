# Patterns

## Role sets by task type

| Task | Roles | Why these |
|------|-------|-----------|
| Teaching or presentation deck | Verifier (content against sources) + Designer (composition, legibility at projection size) + Adversary (curriculum gaps, overreach) | A deck fails in three separate ways - wrong content, unusable delivery, missing or overstated substance - and each is invisible from inside the other two checks. |
| Poster, infographic or single-page visual | Designer (hierarchy, viewing distance, reading order) + Verifier (any figure or claim on it) | One page carries the whole argument, so the visual failure and the factual failure are both fatal and neither check finds the other. |
| Written analysis or report | Verifier (figures against source data) + Adversary (missing analysis, confounders, overclaiming) + Audience (can the reader decide?) | Numbers and interpretation fail differently, and the decision maker's use is a third, independent test. |
| Data work or a model | Verifier (independent recomputation on the same inputs) + Adversary (stress the assumptions, not the arithmetic) | Recomputing catches implementation error; only challenging the assumptions catches a correct calculation of the wrong thing. |
| Code change or script | Verifier (reuse the `review-agent` skill for a read-only defect review) + Adversary (edge cases, failure modes, security) | The review skill already defines a rigorous read-only pass; do not restate it. |
| Research question or explanation | Verifier (sources, current facts) + Adversary (strongest counterargument, weakest evidence) | Recall is the dominant failure mode, and a counterargument pass exposes confidence that was never earned. |
| Quick edit, single question, exploratory draft | none | Any role costs more than the change. Self-check once and move. |

Scale to stakes: one role for a medium-stakes deliverable, two or three when it is external, irreversible,
or carries numbers someone will act on.

## When splitting backfires

- **Role theatre** - several roles reacting to the same draft. Feels thorough, checks nothing. Fix: at least one role verifies against something outside the draft.
- **Anchoring** - the verifier is told what to conclude, or reads the author's summary first. Fix: hand over the raw artefact and nothing else.
- **False corroboration** - two overlapping roles agree, and the integrator reads agreement as confirmation. Fix: disjoint scopes.
- **Volume as signal** - the report with the most findings wins the integrator's attention. Fix: rank by severity and impact, and drop trivia.
- **Loop** - re-verifying unchanged work until the budget is gone. Fix: one round, then re-check only what changed.
- **Deference** - the integrator adopts every finding to look responsive, including the wrong ones. Fix: decide on evidence, and state what you rejected.
- **Scope creep** - a role starts rewriting the deliverable. Fix: read-only checkers, and a brief that states the boundary.
- **Splitting too early** - verifying a half-finished artefact. Fix: get a real draft first; verification sharpens work, it does not create it.

## Proportionality

Ask what a wrong answer costs. If nothing consequential rides on it, skip the split. If someone will present
it, decide on it, or act on the numbers, one extra independent pass is cheap against the cost of being
confidently wrong.
