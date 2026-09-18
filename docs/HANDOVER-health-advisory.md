# health-advisory — handover

Written 2026-09-18. State: **plan 1 complete — all 5 tasks committed and
verified. Plan 2 written, not started.** Everything is pushed.

## Where everything lives

| Thing | Path |
|---|---|
| Skill (the deliverable) | `health-advisory/` in `C:\Users\yuanq\.codex\skills` |
| Vault (the data, outside every repo) | `C:\Users\yuanq\Desktop\chatgpt folder\health-vault` |
| Design spec | `docs/specs/2026-09-18-health-advisory-design.md` |
| Implementation plan 1 (machinery) | `docs/plans/2026-09-18-health-advisory-machinery.md` |
| Implementation plan 2 (workflows) | `docs/plans/2026-09-18-health-advisory-workflows.md` |
| Progress ledger (git-ignored) | `.superpowers/sdd/2026-09-18-health-advisory-machinery/progress.md` |

Branch: `health-advisory-machinery`, tracking `origin/health-advisory-machinery`.
`health-advisory/` is 13 files, 638 lines; the branch is ahead of `main`.

**Everything is pushed**, including `main` (spec, spec amendment, plan 1) and
this branch. There is also an open pull-request link GitHub offered on push.

## What is built and verified

| Commit | What |
|---|---|
| `0565e5b` | `vault.ps1` (DPAPI encryption) + `boundary-and-privacy.md` + its test |
| `0d082dd` | `check_sources.py` + `singapore-sources.json` + its test |
| `80aafb4` | three Singapore sources verified and dated |
| `18055ea` | `build_query.py` (de-identification) + its test |
| `d5673d1` | `validate_report.py` + its test |
| `cc614c8` | `.gitignore` for `.superpowers/` |

Evidence, not assertion:

- **Vault**: 4/4 checks pass. Round-trips, the file on disk carries no
  plaintext, `status` leaks nothing, and a missing boundary file refuses to run.
- **The sandbox genuinely cannot decrypt.** Reading the record from a sandboxed
  shell returns unparseable Base64, and a decrypt attempt is refused. This was
  the core privacy claim and it is now demonstrated.
- **Source ledger**: 7/7 checks pass. Staleness was proven three ways — normal
  run `OK`; `--today 2028-01-01` fails naming all three; an unverified entry
  fails naming it.
- **Query builder**: 10/10 checks pass. `"my 4-year-old in Singapore was given
  ibuprofen"` is refused with `age` and `location` flagged, exit 2.
- **Report validator**: 7/7 checks pass. All five machinery checks exit 0 in a
  single run.

The vault now holds `records/household_health.json` — an encrypted, empty
schema-2 record written as Task 1's proof. No personal data.

## The next action

**Execute plan 2**, at `docs/plans/2026-09-18-health-advisory-workflows.md` —
1120 lines, 5 tasks, 34 steps. Same shape as plan 1: verbatim code, TDD per task,
a commit at the end of each.

| Task | What | Note |
|---|---|---|
| 1 | `routing.json` + the spec's question-class triage | the gap identified after plan 1 |
| 2 | `urgency.json` + `urgency.md` + a verified emergency source | the gate's content needs a source the ledger does not yet hold |
| 3 | `source-ladder.md` + `record-fields.md` | cross-checked against `routing.json` |
| 4 | `due_report.ps1` | writes a file, prints counts only |
| 5 | `SKILL.md` + `agents/openai.yaml` | **this is the task that makes the skill load** |

Task 5 is the milestone. Until it lands, the skill cannot be invoked at all.

Execute inline, as in plan 1 — the subagent path delivered nothing twice. Follow
the same routine: run each RED step before its implementation, rename nothing,
and commit per task. Tasks 2 and 4 need escalated shells (network fetches, and
DPAPI).

## How to run things

```powershell
# python checks (plain asserts, no pytest)
python health-advisory/tests/test_check_sources.py
python health-advisory/tests/test_build_query.py
python health-advisory/scripts/check_sources.py

# vault checks — MUST be escalated; DPAPI fails inside the sandbox
pwsh -NoProfile -File health-advisory/tests/test_vault.ps1
pwsh -NoProfile -File health-advisory/scripts/vault.ps1 status
```

## Environment facts found the hard way

1. **No bash on this machine.** The superpowers SDD helper scripts
   (`sdd-workspace`, `task-brief`, `review-package`) are POSIX shell and cannot
   run. A PowerShell equivalent of `review-package` is at
   `.superpowers/sdd/2026-09-18-health-advisory-machinery/review-package.ps1`.
2. **DPAPI only works outside the sandbox.** Vault scripts must run escalated.
   That is also the security gate, so don't "fix" it.
3. **`Write-Error` under `ErrorActionPreference = 'Stop'` throws before `exit N`
   runs.** For a CLI error path that must return a specific code, use
   `[Console]::Error.WriteLine`. This cost a real bug in Task 1.
4. **`moh.gov.sg` and `hsa.gov.sg` return 403 to a bot user agent** and 200 to a
   browser one. Recorded in the ledger's `_fetch_note`.
5. **Subagent dispatch delivered an empty task twice.** The
   subagent-driven-development path is non-functional here, so execution was
   inline. Do not re-attempt it without checking delivery first.
6. **No pytest.** Tests are plain `assert` scripts that exit non-zero.
7. **Pester 3.4.0 exists but is unused** — PowerShell checks are self-contained
   scripts for the same reason.

## Rulings made, so they are not re-litigated

All are also in the ledger with their cost-if-wrong.

- **Inline, not subagent-driven** — the subagent path delivered nothing twice.
- **A feature branch, not `main`** — satisfies the isolation requirement
  without a consent round-trip.
- **Fail-closed narrowed** to entry points that read or write the vault.
  `build_query`, `check_sources` and `validate_report` never touch the record
  and emit no clinical text.
- **Duplicated identifier regexes in `build_query` and `validate_report` kept
  separate** — different failure semantics, and they already diverge on the
  rest. Deferred minor.
- **`--today` used to prove staleness** rather than editing a `review_by` to a
  past date: identical evidence, no risk of leaving a mutation behind.

## Open decisions

1. **Backup destination and method.** Unresolved, and it is the durability half
   of your data-loss worry. The vault currently has no backup at all. Encrypt-
   then-sync is the working assumption; DPAPI-encrypted files will not open if
   the Windows account or machine changes, which argues for a passphrase-based
   export for the backup specifically.
2. **Which specialty lenses to build** — driven by the record's contents, so it
   waits until the record has contents.
3. **Whether to publish**, and the four conditions in spec section 11
   (institutional clearance, stated separation, non-goals in the README, and a
   cadence or a visible expiry).
4. **OneDrive's own settings were never confirmed.** The Desktop path has no
   reparse point, so it is not redirected — but I could not read OneDrive's
   configuration. Worth thirty seconds in OneDrive → Settings → Sync and backup
   to confirm Desktop is not backed up.

## What is not built

No `SKILL.md`, so the skill does not yet load in Codex. No `due_report.ps1`. No
reference prose beyond the boundary document. No publication scaffolding.
