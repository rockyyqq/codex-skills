---
name: evidence-first-app-maintenance
description: Use when keeping an existing app working across sessions -- a green test suite that must be genuinely trustworthy, a change that should show no visible difference, a build that has to be read back, or work handed to whoever continues it. Holds the evidence loop and the local verification traps; defers to test-driven-development and verification-before-completion for their own gates.
metadata:
  short_description: Prove each change on the artifact
---

# Evidence-first app maintenance

**Core principle:** in a long-lived app, a claim is only as good as the artifact behind it. A suite
passing, a build exiting 0 and a screenshot looking right are three different claims, and each needs
its own evidence.

This skill is for work on something that already exists and has to keep working: not a new feature on
a branch, but a suite you must be able to trust, a package you hand to someone, and a project another
session will pick up. For lifecycle gates, use the superpowers skills -- `test-driven-development` when
writing a new test, `verification-before-completion` before claiming done, `systematic-debugging` when
a cause is unclear. What follows is what they do not cover.

## The loop

1. **Know the state before touching anything.** Read the project's own record, run the suites, and
   report where things actually stand rather than where the documents claim.
2. **Say what the step does, in plain terms, before doing it** -- and how the person who asked can
   check it themselves.
3. **Make the slice small enough to prove**, and pick the invariant that proves it: identical output,
   the same totals to the cent, the same test lines as before the move.
4. **Prove the checks can fail.** A green suite is not evidence until each rule has been broken and
   the suite watched to notice.
5. **Look at the result** -- render the screens and examine them, edges included -- and **read the built
   artifact back** rather than trusting the build log.
6. **Record the slice**: what changed, why, what it cost; true up the status documents, and leave a
   page the next session can act on.

## Signs you are about to claim something you have not shown

- "It should work now" -- the suite has not been run since the change.
- "The tests pass" -- and none of them has ever been seen to fail.
- "The build succeeded" -- the artifact has not been opened.
- "The screen looks right" -- nobody has looked at the screen, only at the check's name.
- "The docs say X" -- the code has not been read to see whether it still does.

Each of those is one command away from being evidence. Run it.

## Only as the task needs them

- **Proving a suite bites** -- baselines, named misses, anchors, and what to do when a check cannot
  fail: read [references/checks-that-bite.md](references/checks-that-bite.md).
- **Reading an artifact back, and rendering to look** -- byte swaps that keep offsets, platform-native
  forms, keeping old builds, and how to look at a screen properly: read
  [references/artifacts-and-renders.md](references/artifacts-and-renders.md).
- **Running the local loop** -- the exact headless-browser, node, Python, git and shell invocations,
  and the environment traps that silently waste an hour: read
  [references/environment-windows.md](references/environment-windows.md).

## What this skill is not

Not a framework, style, or architecture guide; not a substitute for the project's own documents; and
not a licence to refactor or extend beyond what was asked. Domain rules and project history belong in
the project's plan and handovers -- keep them there, and keep this skill general.
