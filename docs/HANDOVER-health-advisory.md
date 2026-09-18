# health-advisory — handover

Written 2026-09-18. State: **the skill is complete and loads in Codex.** Both
plans executed, all 10 tasks committed and verified.

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

## It loads

Verified two ways, not assumed:

```
quick_validate.py health-advisory  ->  Skill is valid!
codex debug prompt-input "test"    ->  - health-advisory: ... (file: r0/health-advisory/SKILL.md)
```

The second is the one that matters: the skill is in Codex's runtime skill list.

## What is left

In rough priority order.

1. **Use it.** It has not answered a single real health question. Expect one or
   two of the design decisions to prove unnecessary once it meets your family —
   that is what the private-use period is for.
2. **The emergency gate covers children only.** The single verified source is
   HealthHub's *Emergency Care (Children)*, so adult red flags — chest pain,
   stroke signs, severe bleeding, overdose, suicidal ideation — have no entry.
   `references/urgency.md` records this as a known gap rather than papering over
   it. To close it: verify a Singapore source for adult emergency presentations,
   add it to the ledger as `"class": "emergency-guidance"`, add one entry per
   presentation it names.
3. **No backup yet.** The vault has never been backed up, and a DPAPI-encrypted
   file will not open if the Windows account or machine changes. A
   passphrase-based export is the right shape for the backup specifically.
4. **Publication scaffolding**, deferred from spec section 11: the README
   never-paste rule, a generated expiry, issue templates that never ask for a
   condition, and the two diagnostic entry points a bug report needs.
5. **Specialty lenses** — driven by the record's contents, so they wait until
   the record has contents.
6. **Record some actual family data.** The vault holds an empty schema-2 record,
   so `due_report.ps1` has nothing to review yet.

## First real use, and what it broke

The skill was used on a real case on 2026-09-18 — a child's booked day surgery —
and it found four defects that no amount of design would have surfaced.
All four are fixed and committed (`d5f8d16`, `d1032e3`).

1. **The schema could not hold the facts the decision turned on.** There was no
   field for what conservative treatment had been tried, no way to record which
   informant gave an onset date, and `events` is shaped for intervals so a
   one-off planned procedure did not fit. Schema is now v3: `onset_reports`
   (a list, so conflicting reports are preserved rather than averaged),
   `treatments_tried` (where `null` means not recorded, not "none tried"), and
   `planned_procedures`. New rule 6: *a report is not a measurement.*
2. **`due_report.ps1` reported `OK` while a pre-operative step was outstanding.**
   It only read `events`, so a booked procedure was invisible. That is
   exactly the false-reassurance failure the script exists to prevent. It now
   surfaces `pre_op_outstanding`.
3. **`validate_report.py` failed the very review it was meant to guard** —
   demanding an Evidence section of a household review. A gate that fires
   falsely teaches the operator to bypass it. It now detects the report kind,
   with `--kind` to override, and fails an unrecognised document closed.
4. **The status check was case-sensitive**, so `**Status: DUE**` did not match
   `status:`. Section matching is now case-insensitive throughout.

Two less far-reaching lessons:

- **A search needs checking as much as a result.** A Europe PMC query was
  malformed and returned 8,607 irrelevant hits sorted by citations. The count
  looked like a result; it was noise.
- **A single observation delayed the answer usefully.** "Noticed two months
  ago" is a lower bound, not an onset — a distinction the record now encodes.

## Second round: the analysis pass, and five more

Running the analysis surfaced five further defects. All fixed.

5. **Nothing validated the record against its schema.** A single misspelled key
   made a live item invisible: `planned_procedures` typed as
   `planned_procedure` produced `status: OK`, `due: 0`, exit 0, no warning. A
   typo caused a false all-clear. `scripts/validate_record.ps1` now fails closed
   on any unknown key.
6. **`cannot judge: 0` was false.** The record carried `onset_unknown` and
   `treatments_tried: null`, yet the review reported zero unknowns, because it
   only understood dates. It now runs a completeness pass, and the spec's own
   words apply: record incomplete → `CANNOT JUDGE`.
7. **The report's disclaimer overclaimed.** It said "the recorded items were
   compared against dated sources"; conditions were never compared against
   anything. The wording now says exactly what was done.
8. **The analysis was produced from memory**, not from the artifact — which is
   the failure `evidence-first-app-maintenance` names. `scripts/record_view.ps1`
   now prints a derived view: structure, flags and gaps, never clinical values.
9. **The report kind was inferred by string matching**, and `test_skill.py` only
   checked `*.py`, so an unmentioned PowerShell script would never have been
   caught. `due_report.ps1` now stamps `<!-- kind: review -->`; the validator
   reads the stamp before inferring; the test checks every script.

The pattern is worth stating: **every one of these was found by using the skill,
not by reviewing it.** Four came from the first real case, five more from being
asked to look at the analysis. The author reviewing his own work found none of
them.

## Third round: three real cases, and a documented artefact that never existed

Using it on the household itself — a child's surgery, an adult's sinus and
medication, and a second adult's five-month rash — surfaced more. All fixed
unless noted.

10. **Provenance was inferred from appearance, and it was wrong.** A ChatGPT
    summary of the household's own account was read as a clinical referral
    letter: `reported_by` said "relaying a dermatologist assessment", and all six
    medications were recorded `source: label` when no label was ever seen. The
    knock-on was worse than the label: it *inverted* a finding, since the summary's
    diagnosis word differed from the household's own. New rule in SKILL.md and
    the field docs: **provenance is asked for, never inferred.**
11. **An unasked section was recorded as "none".** `family_history: []` and
    `events: []` mean "asked and there are none". Nobody had asked. Both are now
    `null`, and the shared gap function covers every section.
12. **Measurements had no name, and blood pressure is two numbers.** `110` with
    unit `mg/dL` did not say what it was. `name` is now required and `value` may
    be a string for paired readings like `"97/60"`.
13. **A gap list implemented twice drifted** — `record_view` named a missing
    allergy list, `due_report` did not. Now one `record_gaps.ps1`.
14. **`@($null).Count` is 1, not 0**, so a null section displayed as one item.
    And a multi-element array in the review stringified to `System.Object[]`
    — hidden until a record had two items.
15. **The emergency card does not exist.** `records/emergency-card.md` is named
    in the vault's own README as "the one deliberate exception to the
    encryption", and spec section 6 says it holds blood type, allergies, current
    medications and emergency contacts. **It was never built.** The README
    asserts an artefact that is not there. Not yet fixed: it is a deliberate hole
    in the encryption and needs the household's decision, not mine.

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
