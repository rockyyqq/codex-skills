# health-advisory — design

Date: 2026-09-18
Status: draft, for review before implementation

## 1. Purpose

Answer household health questions from dated, graded sources, and keep a
household health record that is reviewed on a schedule. The output is
information and preparation, never clinical judgement.

The skill exists because a general assistant will answer a health question
confidently from recall, with no source, no date, and no statement of what it
cannot know. Every rule below is a constraint against that failure.

## 2. Non-goals

Never, under any input:

- Diagnose, or name a likely condition for a person
- Calculate, adjust or recommend a dose
- Triage downward — say care is not needed, or that something is not serious
- Prognose an individual
- Recommend, sequence, start, stop or modify treatment
- Answer whether an insurer will pay
- Correct a treating clinician

The skill may escalate. It may never de-escalate. That asymmetry is the hardest
rule in the design: over-referring wastes an appointment, under-referring can
kill.

## 3. Architecture — three zones of exposure

**Vault** — the household record, the consultation log and generated reports.
Local only. Never in a prompt, never in a conversation, never in git, never in
a synced folder. Read by scripts, not by the agent.

**Skill** — boundaries, source ladder, workflows, scripts. Contains no data.
Lives in the skills repo and is pushed publicly.

**Egress** — de-identified search terms and the question. Nothing else leaves.

The rule that carries the most weight is not encryption: it is that **scripts
emit derived values, never record content**. Content read into a conversation
is written to `~/.codex/sessions` and `thread_history_1.sqlite` in plaintext
and persists. This was verified on this machine, not assumed.

## 4. Components

```
health-advisory/
  SKILL.md
  agents/openai.yaml
  references/
    boundary-and-privacy.md
    source-ladder.md
    urgency.md
    singapore-sources.md
    record-fields.md
    specialty-lenses.md
  scripts/
    vault.ps1            the only component that touches ciphertext
    due_report.ps1       the periodic review; reads the vault
    check_sources.py     fail on unverified or stale sources
    build_query.py       emit de-identified search strings
    validate_report.py   reject identifiers and unsourced claims
```

Vault, outside the skill folder and outside every synced or versioned tree:

```
records/household_health.json
records/consultation-log.jsonl
records/emergency-card.md
reports/<date>-review.md
```

### Why PowerShell for the vault

The household has ruled out installing anything, which leaves Windows DPAPI as
the at-rest encryption. DPAPI is reachable from PowerShell with no dependency,
and was verified working here as the real user account. The other scripts stay
in Python, matching the rest of the repo.

DPAPI fails inside the Codex sandbox and succeeds outside it. That is both a
constraint — vault scripts must run with approval — and an accidental access
gate, since the agent cannot decrypt the vault unattended.

This produces a clean split rather than a preference:

- **Anything that reads the vault is PowerShell**, because DPAPI is only
  reachable that way. `vault.ps1` and `due_report.ps1`.
- **Everything that never touches the vault is Python**, matching the rest of
  the repo. `check_sources.py`, `build_query.py`, `validate_report.py`.

No Python script is ever handed decrypted record content. If one needs a
derived value, PowerShell computes it and passes the value, not the record.

### The vault interface

Two operations, `read` and `write`, behind one small file with a documented
contract. One backend ships: DPAPI on Windows. Documenting the contract means a
macOS Keychain or Linux Secret Service backend is a contribution rather than a
refactor.

The Windows constraint is one file, not the project. The source ladder, the
ledger checks, the query builder and report validation are platform-independent,
and the README says so rather than leaving it to be discovered.

## 5. The record

Fields per person, keyed by role label rather than name:

- conditions, each with `onset` and `last_confirmed`
- medications: name, dose, prescriber, `started`, `stopped` and `stop_reason`,
  and `source` — one of `label`, `pharmacy`, `memory`
- allergies: substance, reaction type, `last_confirmed`
- family history: relative, relationship, condition, age at diagnosis, side of
  family. A vague entry is rejected rather than stored
- measurements: value, unit, the lab's own reference range, and the conditions
  of measurement for home readings
- screening and vaccination events, including negative findings
- unknowns recorded as unknown, never as blank

Five rules govern the fields:

1. **Deltas, not state.** What changed and when matters more than current
   values. The record stores starts, stops and changes as dated events.
2. **Observations and conclusions are separate fields.** The person's own words
   are recorded as reported; a diagnosis is stored marked as reported by the
   household, not as established.
3. **Functional impact accompanies every symptom**, not just intensity.
4. **Every field carries a confirmation date.** A three-year-old medication
   list is more dangerous than none, because it looks authoritative.
5. **Blank is not "none".** "No known allergies" and "not asked" are different
   values and must never collapse into one.

## 6. Privacy protocol

Inherited from the `peer-review` skill's confidentiality section, extended for
a record that must persist.

1. Vault outside OneDrive, outside the skills repo, outside the session store.
2. Encrypted at rest with DPAPI. The passphrase route is reserved for portable
   backups, where a typed passphrase is required and stays out of any chat.
3. Scripts print counts and IDs, never content. A script that would echo a
   medication name is a defect.
4. Search terms are de-identified before leaving. Personal details — age band,
   relationship, location — appear only when the clinical question requires
   them.
5. No third-party service enters the loop. No consumer health site, no grammar
   checker, no upload tool.
6. Reports carry no identifiers and have a stated retention.
7. **Emergency card is the one deliberate exception.** Blood type, allergies,
   current medications and emergency contacts, kept reachable without
   unlocking, on the grounds that in an emergency this is what someone needs.
   The exception is written down rather than assumed.
8. Deletion is real. A forget operation removes the entry, not just a view.

## 7. The evidence workflow

### Source ladder

| Question class | First source class | Not |
|---|---|---|
| Does X work? | systematic review, Cochrane | a single study |
| What is recommended? | guidelines — NICE, WHO, MOH CPGs | a health blog |
| Dose, interaction, contraindication | the approved label — HSA, FDA, EMA | a forum |
| Safety signal | regulator communications | news coverage |
| What is X? | MSD Manuals, MedlinePlus, patient education | a journal article |

### Question-class triage

The ladder selects a source. This selects a *process and an effort*, so that a
terminology question does not trigger a literature sweep, and a symptom question
does not get an evidence section where the urgency gate is what matters. The four
classes and their processes live in `references/routing.json`, as data rather
than prose, because a rule the model re-derives each time cannot be audited.

Two rules bind it:

1. **The emergency gate runs before routing**, for every class. It is not a
   branch; it is the first step regardless of the question.
2. **The route is announced.** The answer states which route it took, so a
   misroute is visible to the reader rather than silently producing a
   confidently wrong shape of answer.

Only effectiveness questions get the 12-month literature sweep. Everything else
is answered from a single authoritative source class.

### Reviews first, with named fall-throughs

A systematic review is used when it fits. The skill moves to primary studies in
five cases, and states which one fired:

1. The review is superseded — a large trial published after its search date
2. It does not fit the question — wrong population or comparator
3. It is empty — no studies met inclusion criteria
4. It is inconclusive — "insufficient evidence" is reported, then primary work
5. It cannot answer the question — interactions and dosing are label questions

"No reviews available" must be demonstrated by a logged search, never assumed.

### The recency lane

Recency is a lane, not a filter. Filtering by date would discard the oldest and
often strongest evidence, and would weight the result toward small,
unreplicated and preprint findings.

1. **Standing answer** — the best available review or guideline, of any date,
   with its date stated
2. **12-month sweep** — restricted by study type, reporting what supersedes,
   contradicts or adds. Emptiness is a finding: "nothing since <date>"

Verified mechanics: PubMed `datetype=edat` with `mindate`/`maxdate`, filtered
by study type — on the test query this reduced 1,610 hits to 114. Europe PMC
`FIRST_PDATE:[...]` with `sort=P_PDATE_D desc`.

The recency idea appears at three levels, enforced once:

| Level | Form |
|---|---|
| Per question | the recency block in the evidence section |
| Per review | has any guideline been superseded since last year |
| Per source ledger | `check_sources.py` fails on any source past its class threshold |

The public expiry claim is generated from the ledger's earliest `review_by`,
never written by hand. A hand-written "reviewed 2026" line rots silently; a
generated one cannot.

### Output shape

```
## Evidence
**Reviews** — review, date, what it pooled, conclusion. Or: none fits, with the search that shows it.
**Why primary studies** — the trigger, named.
**Primary studies** — design, n, population, effect, date. Strongest design first.
**Last 12 months** — what is new, or "nothing since <date>".
**What this doesn't settle** — gaps, disagreement and why, person-specific unknowns.
**Sources** — every claim with source and date.
```

Three items the evidence section must always state: that absence of evidence is
not evidence of absence; where only the abstract was retrieved; and where
sources disagree, with the reason.

## 8. The consultation workflow

Two outputs, not one. A differential handed to a clinician anchors the
consultation and wastes the appointment.

**Household-facing** — possibilities, the must-not-miss list, and what would
change the picture. This is decision support and stays at home.

**Bring-to-clinician** — history only. Timeline, medications with doses,
allergies with reaction type, relevant past history, what has been tried and
what happened, the plan from last time and whether it happened, and the
questions to ask. No differential.

Order of operations for a symptom question:

1. Emergency gate, before any retrieval
2. Elicitation — three to five discriminators, or a stated list of what the
   answer is conditional on
3. Structured history in the shape a clinician takes one
4. Most likely, alongside must-not-miss
5. What distinguishes them
6. Safety netting — specific and observable
7. Referral package when a specialty lens applies: which specialty, what to
   bring, what only they can answer

### Structural limits

The rules that matter are made unrepresentable rather than prohibited. The
output schema has no dose field, so no code path can emit one. The urgency gate
runs before any retrieval and cannot be skipped by any argument. A prohibition
can be argued with; a missing field cannot.

The clinician outranks the skill. A treating clinician's advice is recorded as
fact about the plan; disagreement with a guideline becomes a question, never a
correction.

## 9. The annual review

Three statuses, mirroring `check_mandate.py`:

**OK** — checked, nothing due.

**DUE / FLAGGED** — split into two classes that never merge:

- *hard signals*: a screening past its sourced interval, a monitoring test not
  done, a vaccination due, two listed medications flagged against each other, a
  recorded allergy matching a recorded medication. A flag here is a fact.
- *assumption-dependent*: a family history meeting a guideline's
  earlier-screening criteria, a trend in a tracked value. Reported as questions
  for a clinician, in their own section.

**CANNOT JUDGE** — record incomplete, source stale, data unreachable. Never a
pass.

Interactions carry a severity class. Unclassified flags produce alert fatigue,
which is worse than not flagging.

The next review date is computed from the earliest due interval, not fixed to a
calendar month. A clean review says "these checks are up to date" and never
"you are healthy", and names what was not checked.

## 10. Failure handling

**Fail closed everywhere.** Each of these stops the tool rather than degrading
it, because the dangerous failure is a tool that keeps working after it has
stopped being trustworthy:

- Stale red-flag criteria fail the whole skill, not one claim
- A source past its `review_by` fails the report
- A missing or unreadable `boundary-and-privacy.md` fails the run
- An absent or unrecognised vault backend fails the run
- A missing recency block is a failed output, not a stylistic omission
- An identifier appearing in a report is a validation failure
- An empty search is reported as empty, never backfilled with weaker material

This is the fourth instance of a pattern already in the repo: `check_params.py`
exits non-zero, `check_mandate.py` has `CANNOT JUDGE`, `validate_deliverable.py`
prints `FAIL`.

## 11. Publication

The skill is intended to be publishable, and the repo is already publishable by
construction: the household example states in its own first line that every
figure is made up, and the parameter file holds published government figures
with per-entry provenance. The obstacles are therefore policy and maintenance,
not disclosure.

**Four conditions before a public release.**

1. **Institutional clearance.** Check the outside-work policy for
   health-related public projects. That is a question for the employer, not a
   judgment the project can make for itself.
2. **Separation stated.** "Personal project, not affiliated with or endorsed by
   my employer." The attribution stance — real name or neutral handle — is
   chosen deliberately rather than drifted into.
3. **Non-goals repeated in the README**, including: not a research instrument,
   not validated, no clinical claim, not citable as evidence that anything
   works.
4. **A stated review cadence, or a visible expiry.** The README carries the
   generated expiry. An unmaintained health tool that looks maintained is worse
   than none.

**Bug reports must never require disclosing health information.**

- Two diagnostic entry points cover a bug report between them:
  `vault.ps1 status` reports the backend, its availability and the last write,
  without content; `check_sources.py --diagnostic` reports versions, source IDs,
  timestamps and rule failures. Attaching both never requires pasting anything
  personal.
- Issue templates ask for the version, the source ID, the output and the
  expectation. They never ask for a condition or a history.
- A stated route for reporting a data-handling problem privately, and a
  standing commitment to delete an issue containing personal health information
  on request.
- The never-paste rule appears on the README's first screen, not in a policy
  file.

**Validation before publication.**

- Build and use it privately for a set period: three months, or twenty real
  questions.
- Record field notes — what it was used for, what broke, what changed.
- At that review, every rule must be justified by an incident. Rules that never
  fired are cut.
- The first public release is therefore v2: the design plus the evidence it
  survived contact.

## 12. Verification plan

Established in this repo's style: prove each check can fail.

- Age a source past its threshold; `check_sources.py` must fail
- Put a name in the record; `validate_report.py` must reject it
- Put a personal detail in a question; `build_query.py` must strip it
- Remove the recency block; the report must be rejected
- Round-trip the vault through DPAPI and confirm the plaintext is recoverable
- Restore a backup on this machine and record the date

## 13. Decisions still open

1. **Vault path.** An earlier suggestion was declined. Needs a location outside
   OneDrive, outside the skills repo and outside the session store.
2. **Backup destination and method.** Encrypt-then-sync is the working
   assumption; the destination is undecided.
3. **Which specialty lenses to build.** Driven by the record's contents rather
   than a textbook list of specialties.

## 14. Build sequence

1. Vault location, DPAPI round-trip, ignore rules
2. `boundary-and-privacy.md` — written before anything depends on it
3. Verify the first three Singapore sources by hand, dated
4. `source-ladder.md` and `urgency.md`
5. Record schema, then `due_report` end to end
6. `SKILL.md`, then validation

Steps 1 and 2 are prerequisites for everything else. Nothing that reads or
writes the vault is written before the boundary file exists.
