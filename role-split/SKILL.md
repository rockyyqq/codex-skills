---
name: role-split
description: Split a task into independent roles - who builds, who verifies against primary sources, who attacks the result, who judges it under real conditions, and for visual work who reviews the rendered design - and scale the number of roles to the stakes. Use for high-stakes or externally presented deliverables, and for any work carrying numbers or factual claims that matter. Not for quick edits, single questions, or exploratory drafting, where the overhead exceeds the gain.
---

# Role Split

Raise the quality of finished work by separating making from checking, and by checking against outside
evidence instead of against the draft's own wording.

## What actually improves quality

Independent verification improves results. Extra opinions do not. Several agents reading the same draft and
reacting to it produce cost, latency and a feeling of rigour without checking anything. Every split must
contain at least one role whose job is to falsify the result against a source the author did not write.

## Choose the tier

The user can set the tier, or leave it to you. Read the words attached to the request:

| Spoken | Tier | Roles |
|--------|------|-------|
| "`$role-split` no split", "just check it", "don't overdo it" | 0 | none - one deliberate self-check pass |
| "`$role-split simple`", "light", "quick" | 1 | exactly 2: builder + one checker |
| "`$role-split complex`", "full", "deep", "max" | 3 | the maximum for the task, up to four roles |
| nothing named | you decide | apply the complexity test, then state the tier you chose |

These words are conventions, not parsed arguments: nothing in the system reads them, so the mapping has to
live in this skill for the words to mean anything. When the user names a tier, honour it exactly rather than
re-deriving it - they know things about the deliverable that you do not.

**Complexity test.** Count how many apply: externally presented; load-bearing numbers or factual claims;
multi-part deliverable; expensive or irreversible to redo; more than about half a day of work.
Zero or one gives Tier 1 (2 roles), two gives Tier 2 (3 roles), three or more gives Tier 3 (4 roles).

Tier 1 has a single checker, so pick it by what could actually go wrong: the verifier when facts and numbers
carry weight, the designer when the artefact is visual and its correctness is not in doubt.

## Roles

- **Builder** - produces the artefact. Usually the main agent.
- **Verifier** - re-derives every consequential claim, number, formula and citation from a primary source. When a number was itself derived from an artefact - measured off an image, scanned from a PDF, transcribed from a report - that artefact is the primary source, and the verifier re-derives from it rather than reading the author's extraction.
- **Adversary** - assumes the work fails, and argues the strongest case against it: gaps, overreach, unstated assumptions, what an expert or an end user would attack.
- **Designer** - judges a visual artefact from its rendered output rather than its source. Include it only when the deliverable is a deck, poster, infographic or chart-heavy page, and never for text documents, analysis or code. Read [references/designer-role.md](references/designer-role.md) when it applies.
- **Audience or delivery** - judges the work under the conditions it will actually be used in: projected, timed, read by a decision maker, run by a caller.
- **Integrator** - the main agent, always. Resolves conflicts, makes every edit, owns the outcome.

Take the roles the tier allows and the task needs. Two well-scoped roles beat four that overlap.

## Operating rules

1. The maker never verifies its own work.
2. Hand each role the raw artefact, not your conclusions, your reasoning or your worries. Knowledge of the intended answer destroys the check.
3. Give scopes that do not overlap. Two roles covering the same ground return the same findings twice and create false confidence.
4. Checkers are read-only. Every edit is made by the integrator, after integration.
5. Run at most three roles at once; a fourth waits for the second wave. Do not let a role spawn its own subagents.
6. Require evidence per finding: what, where (file plus slide, section, page, cell or line), what it was checked against, confidence, and severity.
7. Bound the work: one round per role, then re-check only what changed. Stop when a new role only repeats findings you already hold.
8. "Could not verify" is a result, and so is "nothing found here" - the first marks a gap, the second marks ground that is already solid.
9. Without subagents available, run the passes sequentially and say plainly that the verification was not independent.

## Procedure

1. Fix the deliverable, the acceptance criteria and the tier; state the plan and the tier in a line or two.
2. Brief each role - use [references/role-briefs.md](references/role-briefs.md) - and give it its own output file so reports cannot collide.
3. Run the roles, in parallel where they are genuinely independent.
4. Integrate: de-duplicate, rank by severity, resolve disagreement on evidence rather than on volume, and decide what is worth fixing.
5. Make the changes yourself, then re-verify only what moved.
6. Report what each role found, what you changed, what you rejected and why, and what remains unverified.

## Reporting

Lead with the findings that change the deliverable, ranked, with locations. Then what you changed. Keep
residual uncertainty explicit, so a reader can see what has been checked and what has not.

## References

- [references/role-briefs.md](references/role-briefs.md) - brief templates per role, the finding format, and the mistakes that make a brief useless. Read before writing briefs.
- [references/patterns.md](references/patterns.md) - role sets per task type and the ways splitting backfires. Read when choosing roles or when a split is not paying off.
- [references/designer-role.md](references/designer-role.md) - the designer brief and its two review gates for decks, posters and other visual artefacts. Read only when the deliverable is visual.
