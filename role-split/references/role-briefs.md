# Role briefs

A brief is what turns a role into a check rather than an opinion. Write it before the role starts, and keep
it to what the role cannot infer for itself.

## What every brief contains

- The deliverable: absolute path, and what it is for.
- Acceptance criteria: what "correct" and "finished" mean here.
- The role's scope: the exact question it owns.
- Its ground truth: the files, data or sources it must check against.
- Explicit prohibitions: do not edit the deliverable, do not spawn subagents, do not stray outside scope.
- Output: a file path for the report, the finding format below, and a short reply carrying the top findings.
- The instruction to state what it could not verify.

Precision matters more than length. A five-line brief that names the source and forbids editing does more
than a page of encouragement.

## Finding format

| Field | Content |
|-------|---------|
| What | The problem, one sentence, imperative where possible |
| Where | File plus slide, section, page, line or cell |
| Evidence | What it was checked against, quoted or located precisely |
| Confidence | High / medium / low, with the reason for anything below high |
| Severity | Does it mislead, embarrass, break something, or merely polish? |

Rank by severity. "Nothing found in area X" is a valid entry and worth stating.

## Verifier

> You are the verifier. The deliverable is <path>. Check every consequential claim, number, formula and
> citation in it against <primary sources>. Re-derive the numbers yourself rather than reading them out of
> the draft. Where a number was measured, read or transcribed out of another artefact - a chart image, a
> scan, a PDF - start again from that artefact; reusing the tool that produced the author's extraction is
> allowed, but a sample of the values must also be checked by eye against the source, or a systematic error
> in that tool passes straight through your check and reads as agreement. You do not edit anything and you
> do not decide what to fix; you report. For each item use the
> finding format: what, where, evidence, confidence, severity. Mark items you cannot check as unverifiable
> rather than guessing, and name the source you would need. Work from the highest-consequence items down;
> do not pad the report with trivia. Write to <path> and reply with your top findings.

## Adversary

> You are the adversary. Assume <deliverable> will be criticised by <audience: a sceptical expert, a
> participant, a reviewer, a caller>. Build the strongest honest case against it: what is missing, what is
> asserted beyond the evidence, which assumption is doing unacknowledged work, what would make the author
> look unprepared when questioned. Rank the objections by the damage they do, give each a concrete remedy,
> and name the single weakest part with the reason. Do not soften the case to be polite, and do not invent
> objections - where a section is solid, say so.

## Audience or delivery

> Judge <deliverable> under the conditions it will actually be used in: <projection, time budget, reader,
> caller, load>. Work from <the rendered output, the real artefact>, not from the source text alone. Report
> every point where those conditions break it - illegible, over time, off-message, unusable - with the
> location, the severity and the concrete fix. Also report what already lands well, so the integrator does
> not "fix" it.

## Builder

> Produce <artefact> at <path> to these acceptance criteria: <criteria>. Do not touch <anything else>.
> Where a judgement call is needed, follow <stated preference> or ask. Reply with what you made and what
> you are unsure about.

## Briefs that fail

- **Anchored** - tells the verifier what the author concluded, so it confirms the conclusion.
- **Open-ended** - "review this and tell me what you think" produces impressions, not checks.
- **Overlapping** - two roles on one question; duplicated findings read as corroboration and are not.
- **Scope-free** - no boundary, so the role starts rewriting the deliverable instead of reporting on it.
- **Unbounded** - no instruction to stop, so the role manufactures marginal findings to look thorough.
- **Unsourceable** - no ground truth named, so the verdict is just the role's memory of the subject.
