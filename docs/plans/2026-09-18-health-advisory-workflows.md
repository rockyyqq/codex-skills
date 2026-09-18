# health-advisory workflows — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the machinery from plan 1 into a skill that loads in Codex and can be used: routing by question class, the emergency gate, the record schema, the periodic review, and `SKILL.md`.

**Architecture:** Two machine-readable data files carry the rules that must not be improvised (`routing.json`, `urgency.json`), checked by cross-reference against the verified source ledger. One PowerShell script reads the vault, writes its report to a file, and prints only counts. `SKILL.md` ties it together and is what makes the skill loadable.

**Tech Stack:** PowerShell 7.6.5, Python 3.13.1. **No installs.** Tests are plain `assert` scripts run directly; there is no pytest, and Pester is unused.

**Spec:** `docs/specs/2026-09-18-health-advisory-design.md`

**Depends on:** plan 1 (`docs/plans/2026-09-18-health-advisory-machinery.md`), all five tasks committed.

## Global Constraints

- Vault root: `C:\Users\yuanq\Desktop\chatgpt folder\health-vault`, overridable via `$env:HEALTH_VAULT_ROOT`
- No new software may be installed on this machine
- **Scripts emit derived values, never record content.** A script that prints a medication name is a defect
- **May escalate, never de-escalate.** No code path may say care is not needed
- **No dose field exists in any output schema**
- Identifiers are never stored: role labels (`adult-a`, `child-a`), never names
- Entry points that read or write the vault fail closed when `references/boundary-and-privacy.md` is missing
- **The emergency gate runs before any retrieval, for every question class**
- Every source referenced anywhere resolves to an entry in `references/singapore-sources.json`
- The vault is never committed and `.superpowers/` is never committed
- Commit after every task

---

### Task 1: Question-class routing as data

**Files:**
- Create: `health-advisory/references/routing.json`
- Create: `health-advisory/tests/test_routing.py`
- Modify: `docs/specs/2026-09-18-health-advisory-design.md` — add the triage to section 7

**Interfaces:**
- Consumes: nothing
- Produces: `routing.json` with a `classes` list and a `gate` object. Task 3 asserts every `sources` name appears in `source-ladder.md`; Task 5 asserts the gate is described in `SKILL.md`.

**Why data rather than prose:** the ladder must be auditable and correctable. A rule the model re-derives each time cannot be inspected. This file is the thing you edit when a route is wrong.

- [ ] **Step 1: Write the failing test**

`health-advisory/tests/test_routing.py`:

```python
"""Self-contained checks for routing.json. Run directly; no pytest."""
import json
import sys
from pathlib import Path

ROUTING = Path(__file__).resolve().parent.parent / "references" / "routing.json"
FAILURES = []


def check(name, fn):
    try:
        fn()
        print(f"PASS  {name}")
    except AssertionError as exc:
        print(f"FAIL  {name} :: {exc}")
        FAILURES.append(name)


def data():
    return json.loads(ROUTING.read_text(encoding="utf-8"))


def test_every_class_has_a_process():
    for klass in data()["classes"]:
        assert klass.get("process"), f"{klass.get('id')} has no process"


def test_every_class_has_a_boolean_evidence_sweep():
    for klass in data()["classes"]:
        assert isinstance(klass.get("evidence_sweep"), bool), f"{klass.get('id')} evidence_sweep is not boolean"


def test_every_class_names_at_least_one_source():
    for klass in data()["classes"]:
        assert klass.get("sources"), f"{klass.get('id')} names no source"


def test_class_ids_are_unique():
    ids = [klass["id"] for klass in data()["classes"]]
    assert len(ids) == len(set(ids)), f"duplicate class id in {ids}"


def test_the_gate_runs_before_everything():
    assert data()["gate"]["runs_before"] == "all"


def test_routing_is_announced():
    assert data()["announce"] is True


def test_only_effectiveness_questions_get_a_literature_sweep():
    sweeping = [k["id"] for k in data()["classes"] if k["evidence_sweep"]]
    assert sweeping == ["effectiveness"], f"unexpected sweep classes: {sweeping}"


check("every class has a process", test_every_class_has_a_process)
check("every class has a boolean evidence_sweep", test_every_class_has_a_boolean_evidence_sweep)
check("every class names a source", test_every_class_names_at_least_one_source)
check("class ids are unique", test_class_ids_are_unique)
check("the gate runs before everything", test_the_gate_runs_before_everything)
check("routing is announced", test_routing_is_announced)
check("only effectiveness gets a literature sweep", test_only_effectiveness_questions_get_a_literature_sweep)

if FAILURES:
    print(f"\n{len(FAILURES)} check(s) failed")
    sys.exit(1)
print("\nall routing checks passed")
```

- [ ] **Step 2: Run it, expect failure**

Run: `python health-advisory/tests/test_routing.py`
Expected: `FileNotFoundError` — `routing.json` does not exist.

- [ ] **Step 3: Write the routing file**

`health-advisory/references/routing.json`:

```json
{
  "_note": "Which process a question gets, chosen by the nature of the question. The purpose is to be boring when the question is boring: a terminology question must not trigger a literature sweep. Edit this file when a route is wrong, not the skill prose.",
  "gate": {
    "id": "urgency",
    "file": "urgency.json",
    "runs_before": "all",
    "note": "Checked before any retrieval, for every class below."
  },
  "announce": true,
  "_announce_note": "State the route in the answer, e.g. 'this is a drug-interaction question, so I am going to the label'. A misroute must be visible rather than silently producing a confidently wrong shape of answer.",
  "classes": [
    {
      "id": "terminology",
      "match": "what is X; what does this test measure; what does this term mean",
      "process": "answer",
      "evidence_sweep": false,
      "sources": ["patient-education", "guideline"]
    },
    {
      "id": "drug",
      "match": "dose; interaction; contraindication; adverse effect of a named drug",
      "process": "label",
      "evidence_sweep": false,
      "sources": ["label", "regulator"]
    },
    {
      "id": "effectiveness",
      "match": "does X work; is X effective; what does the evidence say about X",
      "process": "evidence-section",
      "evidence_sweep": true,
      "sources": ["systematic-review", "guideline", "primary-study"]
    },
    {
      "id": "symptom",
      "match": "a person has a symptom, or asks what a symptom means for them",
      "process": "consultation",
      "evidence_sweep": false,
      "sources": ["guideline", "patient-education"]
    }
  ]
}
```

- [ ] **Step 4: Run the test, expect it to pass**

Run: `python health-advisory/tests/test_routing.py`
Expected: seven `PASS` lines, then `all routing checks passed`, exit 0.

- [ ] **Step 5: Add the triage to the spec**

Append to section 7 of `docs/specs/2026-09-18-health-advisory-design.md`, immediately after the source-ladder table:

```markdown
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
```

- [ ] **Step 6: Commit**

```bash
git add health-advisory/references/routing.json health-advisory/tests/test_routing.py docs/specs/2026-09-18-health-advisory-design.md
git commit -m "feat(health-advisory): question-class routing as data, and the triage in the spec"
```

---

### Task 2: The emergency gate

**Files:**
- Create: `health-advisory/references/urgency.json`
- Create: `health-advisory/references/urgency.md`
- Create: `health-advisory/tests/test_urgency.py`
- Modify: `health-advisory/references/singapore-sources.json`

**Interfaces:**
- Consumes: `check_sources.py`'s ledger shape; `routing.json`'s `gate.file`
- Produces: `urgency.json` with `entries[]`, each carrying `source_id` and `review_by`. Task 5 asserts `SKILL.md` describes the gate.

**The gate's content needs a source we have not verified.** The three ledger
entries are a guideline index, a consumer-safety index and a patient-education
index. None of them is an emergency-presentation list, so citing them here would
be inventing provenance. Step 1 fixes that.

- [ ] **Step 1: Verify a source for the gate, and add it to the ledger**

Fetch a Singapore source for emergency presentations. Candidates, in order:

```bash
curl -sL -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36" -o /dev/null -w "%{http_code} %{url_effective}\n" https://www.healthhub.sg/health-conditions
curl -sL -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36" -o /dev/null -w "%{http_code} %{url_effective}\n" https://www.moh.gov.sg/
```

A browser user agent is required: MOH and HSA return 403 to a bot agent.

Add an entry to `sources` with `"class": "emergency-guidance"` and a 6-month
`review_by`, since emergency guidance changes faster than a guideline. If no
Singapore page states emergency presentations, record the closest page that
does and name it accurately in `title` — do not widen the claim to fit.

Run: `python health-advisory/scripts/check_sources.py`
Expected: `OK: 4 source(s) verified, none past review`, exit 0.

- [ ] **Step 2: Write the failing test**

`health-advisory/tests/test_urgency.py`:

```python
"""Self-contained checks for urgency.json. Run directly; no pytest."""
import json
import sys
from datetime import date
from pathlib import Path

REFS = Path(__file__).resolve().parent.parent / "references"
FAILURES = []


def check(name, fn):
    try:
        fn()
        print(f"PASS  {name}")
    except AssertionError as exc:
        print(f"FAIL  {name} :: {exc}")
        FAILURES.append(name)


def urgency():
    return json.loads((REFS / "urgency.json").read_text(encoding="utf-8"))


def ledger_ids():
    ledger = json.loads((REFS / "singapore-sources.json").read_text(encoding="utf-8"))
    return {source["id"] for source in ledger["sources"]}


def test_there_is_at_least_one_entry():
    assert urgency()["entries"], "the gate has no entries"


def test_every_entry_has_an_action():
    for entry in urgency()["entries"]:
        assert entry.get("action"), f"{entry.get('id')} has no action"


def test_every_entry_cites_a_ledger_source():
    known = ledger_ids()
    for entry in urgency()["entries"]:
        assert entry.get("source_id") in known, f"{entry.get('id')} cites unknown source {entry.get('source_id')!r}"


def test_every_entry_has_a_future_review_date():
    today = date.today()
    for entry in urgency()["entries"]:
        review = date.fromisoformat(entry["review_by"])
        assert review >= today, f"{entry.get('id')} review date {review} has passed"


def test_entry_ids_are_unique():
    ids = [entry["id"] for entry in urgency()["entries"]]
    assert len(ids) == len(set(ids)), f"duplicate id in {ids}"


def test_the_gate_states_it_runs_first():
    assert urgency()["runs_before"] == "all"


def test_every_action_escalates_and_none_de_escalates():
    banned = ("no need", "not serious", "nothing to worry", "wait and see")
    for entry in urgency()["entries"]:
        lowered = entry["action"].lower()
        for phrase in banned:
            assert phrase not in lowered, f"{entry.get('id')} de-escalates: {entry['action']!r}"


check("there is at least one entry", test_there_is_at_least_one_entry)
check("every entry has an action", test_every_entry_has_an_action)
check("every entry cites a ledger source", test_every_entry_cites_a_ledger_source)
check("every entry has a future review date", test_every_entry_has_a_future_review_date)
check("entry ids are unique", test_entry_ids_are_unique)
check("the gate states it runs first", test_the_gate_states_it_runs_first)
check("no action de-escalates", test_every_action_escalates_and_none_de_escalates)

if FAILURES:
    print(f"\n{len(FAILURES)} check(s) failed")
    sys.exit(1)
print("\nall urgency-gate checks passed")
```

- [ ] **Step 3: Run it, expect failure**

Run: `python health-advisory/tests/test_urgency.py`
Expected: `FileNotFoundError` — `urgency.json` does not exist.

- [ ] **Step 4: Write the gate**

`health-advisory/references/urgency.json` — populate `entries` from the source verified in Step 1, one entry per presentation that source names. Use the exact wording the source uses for the presentation, and set `source_id` to the ledger id from Step 1:

```json
{
  "_note": "The emergency gate. Checked before any retrieval, for every question class, before any explanation is written. An entry here means: say this first. Never add an entry without a source_id that exists in singapore-sources.json.",
  "gate_id": "urgency",
  "runs_before": "all",
  "entries": []
}
```

An empty `entries` list fails the test at Step 2, which is the point: the gate is not shippable until it has sourced content. Populate it, then re-run.

- [ ] **Step 5: Write the explanation**

`health-advisory/references/urgency.md`:

```markdown
# The emergency gate

This runs before anything else, for every question class. It is not a branch in
the routing; it is the first step regardless of the question.

If the question describes a presentation listed in `urgency.json`, the first line
of the answer is the action from that entry. The explanation comes after, and it
may be short.

## Why it is data

The gate is the one rule that cannot be approximately right. Keeping it in
`urgency.json` means it can be read, diffed, dated and corrected. Keeping it in
prose would mean re-deriving it every time.

## Why every entry cites a source

An emergency list invented from general knowledge is exactly the artefact this
skill exists to avoid. `test_urgency.py` fails on any entry whose `source_id` is
not in `singapore-sources.json`, and on any whose `review_by` has passed.

## The asymmetry

No entry may de-escalate. A test enforces this by failing on phrases like
"no need" or "not serious". Over-referring wastes an appointment;
under-referring can kill.
```

- [ ] **Step 6: Run the test, expect it to pass**

Run: `python health-advisory/tests/test_urgency.py`
Expected: seven `PASS` lines, then `all urgency-gate checks passed`, exit 0.

- [ ] **Step 7: Prove the cross-reference bites**

Temporarily change one entry's `source_id` to `"SG-NOT-REAL"`.

Run: `python health-advisory/tests/test_urgency.py`
Expected: `FAIL every entry cites a ledger source`, exit 1.

Restore it and re-run. Expected: all pass, exit 0.

- [ ] **Step 8: Commit**

```bash
git add health-advisory/references/urgency.json health-advisory/references/urgency.md health-advisory/tests/test_urgency.py health-advisory/references/singapore-sources.json
git commit -m "feat(health-advisory): the emergency gate, sourced and dated"
```

---

### Task 3: The two reference documents

**Files:**
- Create: `health-advisory/references/source-ladder.md`
- Create: `health-advisory/references/record-fields.md`
- Create: `health-advisory/tests/test_references.py`

**Interfaces:**
- Consumes: the `sources` names in `routing.json`, the field names in `record-fields.md`
- Produces: prose that Task 5's `SKILL.md` links to

- [ ] **Step 1: Write the failing test**

`health-advisory/tests/test_references.py`:

```python
"""Cross-checks that the reference prose agrees with the data files."""
import json
import sys
from pathlib import Path

REFS = Path(__file__).resolve().parent.parent / "references"
FAILURES = []


def check(name, fn):
    try:
        fn()
        print(f"PASS  {name}")
    except AssertionError as exc:
        print(f"FAIL  {name} :: {exc}")
        FAILURES.append(name)


def ladder_text():
    return (REFS / "source-ladder.md").read_text(encoding="utf-8")


def fields_text():
    return (REFS / "record-fields.md").read_text(encoding="utf-8")


def test_every_routed_source_class_is_in_the_ladder():
    routing = json.loads((REFS / "routing.json").read_text(encoding="utf-8"))
    wanted = {name for klass in routing["classes"] for name in klass["sources"]}
    text = ladder_text()
    missing = sorted(name for name in wanted if name not in text)
    assert not missing, f"routing names source classes absent from the ladder: {missing}"


def test_the_five_fall_throughs_are_documented():
    text = ladder_text().lower()
    for phrase in ("superseded", "does not fit", "empty", "inconclusive", "cannot answer"):
        assert phrase in text, f"the ladder does not mention the {phrase!r} fall-through"


def test_the_recency_lane_is_not_a_filter():
    text = ladder_text().lower()
    assert "lane, not a filter" in text, "the ladder does not state that recency is a lane"
    assert "nothing since" in text, "the ladder does not say emptiness is a finding"


def test_absence_of_evidence_is_stated():
    assert "not evidence of absence" in ladder_text().lower()


def test_blank_is_not_none():
    assert "blank" in fields_text().lower(), "record-fields does not rule on blank values"


def test_confirmation_dates_are_required():
    text = fields_text().lower()
    assert "confirmation date" in text or "last_confirmed" in text


def test_no_dose_field_exists():
    assert "dose" not in fields_text().lower().replace("no dose field", ""), \
        "record-fields mentions a dose field; the schema must not have one"


check("every routed source class is in the ladder", test_every_routed_source_class_is_in_the_ladder)
check("the five fall-throughs are documented", test_the_five_fall_throughs_are_documented)
check("recency is a lane, not a filter", test_the_recency_lane_is_not_a_filter)
check("absence of evidence is stated", test_absence_of_evidence_is_stated)
check("blank is not none", test_blank_is_not_none)
check("confirmation dates are required", test_confirmation_dates_are_required)
check("no dose field exists", test_no_dose_field_exists)

if FAILURES:
    print(f"\n{len(FAILURES)} check(s) failed")
    sys.exit(1)
print("\nall reference checks passed")
```

- [ ] **Step 2: Run it, expect failure**

Run: `python health-advisory/tests/test_references.py`
Expected: `FileNotFoundError` — `source-ladder.md` does not exist.

- [ ] **Step 3: Write the source ladder**

`health-advisory/references/source-ladder.md`. Every source class named in `routing.json` — `patient-education`, `guideline`, `label`, `regulator`, `systematic-review`, `primary-study` — must appear by that exact name. The five fall-throughs are quoted from the spec's section 7, as are the recency-lane and absence-of-evidence rules:

```markdown
# The source ladder

| Question class | First source class | Not |
|---|---|---|
| Does X work? | `systematic-review` — Cochrane, or another systematic review | a single study |
| What is recommended? | `guideline` — NICE, WHO, MOH clinical guidelines | a health blog |
| Dose, interaction, contraindication | `label` — the approved product label | a forum |
| Safety signal | `regulator` — HSA, FDA | news coverage |
| What is X? | `patient-education` — HealthHub, MSD Manuals, MedlinePlus | a journal article |

## Reviews first, with named fall-throughs

A systematic review is used when it fits. Move to `primary-study` in five cases,
and say which one fired:

1. The review is **superseded** — a large trial published after its search date
2. It **does not fit** the question — wrong population or comparator
3. It is **empty** — no studies met inclusion criteria
4. It is **inconclusive** — "insufficient evidence" is reported, then primary work
5. It **cannot answer** the question — interactions and dosing are label questions

"No reviews available" must be demonstrated by a logged search, never assumed.

## The recency lane

Recency is a **lane, not a filter**. Filtering by date would discard the oldest
and often strongest evidence, and would weight the result toward small,
unreplicated and preprint findings.

1. **Standing answer** — the best available review or guideline, of any date,
   with its date stated
2. **12-month sweep** — restricted by study type, reporting what supersedes,
   contradicts or adds. Emptiness is a finding: "**nothing since** <date>"

Verified mechanics: PubMed `datetype=edat` with `mindate`/`maxdate`, filtered by
study type — on the test query this reduced 1,610 hits to 114. Europe PMC
`FIRST_PDATE:[...]` with `sort=P_PDATE_D desc`.

## Three things the evidence section must always state

1. That absence of evidence is **not evidence of absence**
2. Where only the abstract was retrieved, rather than the full text
3. Where sources disagree, and the reason — population, comparator, setting,
   time horizon, outcome definition
```

- [ ] **Step 4: Write the record fields**

`health-advisory/references/record-fields.md`:

```markdown
# Record fields

The vault holds one JSON document. People are keyed by role label, never by name.

## Per person

| Field | Shape | Rule |
|---|---|---|
| `conditions` | list of `{name, onset, last_confirmed}` | `last_confirmed` is required |
| `medications` | list of `{name, dose_text, prescriber, started, stopped, stop_reason, source}` | `source` is one of `label`, `pharmacy`, `memory` |
| `allergies` | list of `{substance, reaction, last_confirmed}` | the reaction type is required, not just the substance |
| `family_history` | list of `{relative, condition, age_at_diagnosis, side}` | a vague entry is rejected rather than stored |
| `measurements` | list of `{value, unit, reference_range, conditions_of_measurement, taken_on}` | home readings record the conditions |
| `events` | list of `{id, kind, code, last_done, interval_months, basis, source_id}` | see below |

`events.kind` is one of `screening`, `vaccination`, `monitoring`.
`events.basis` is `fact` or `assumption`, and it decides which section of the
review the item appears in.

## There is no dose field

The schema has no field for a recommended or calculated dose, and no code path
may emit one. A dose is a prescriber decision. `dose_text` records what the label
or the prescription says, for identification only — not a quantity to act on.

## Five rules

1. **Deltas, not state.** What changed and when matters more than current
   values. Starts, stops and changes are dated events.
2. **Observations and conclusions are separate fields.** The person's own words
   are recorded as reported; a diagnosis is stored marked as reported by the
   household, not as established.
3. **Functional impact accompanies every symptom**, not just intensity.
4. **Every field carries a confirmation date.** A three-year-old medication list
   is more dangerous than none, because it looks authoritative.
5. **Blank is not "none".** "No known allergies" and "not asked" are different
   values and must never collapse into one.

## Identifiers are never stored

No names. No full dates of birth — year or age band only. No national ID, no
address, no phone number, no email. `validate_report.py` rejects a generated
report containing any of these patterns.
```

- [ ] **Step 5: Run the test, expect it to pass**

Run: `python health-advisory/tests/test_references.py`
Expected: seven `PASS` lines, then `all reference checks passed`, exit 0.

- [ ] **Step 6: Commit**

```bash
git add health-advisory/references/source-ladder.md health-advisory/references/record-fields.md health-advisory/tests/test_references.py
git commit -m "feat(health-advisory): the source ladder and the record field rules"
```

---

### Task 4: The periodic review

**Files:**
- Create: `health-advisory/scripts/due_report.ps1`
- Test: `health-advisory/tests/test_due_report.ps1`

**Interfaces:**
- Consumes: `vault.ps1`'s `Get-VaultRecord`, `Assert-Boundary`, `$script:VaultRoot`; the ledger from plan 1
- Produces: a markdown report written to `<vault>/reports/<date>-review.md`; stdout carries counts and the path only

**The rule this task enforces:** the report is written to a file, and stdout
carries counts and the path. Report content never reaches stdout, because stdout
is persisted by the session store — that was verified in plan 1.

- [ ] **Step 1: Write the failing test**

`health-advisory/tests/test_due_report.ps1`:

```powershell
#Requires -Version 7
$ErrorActionPreference = 'Stop'

$env:HEALTH_VAULT_ROOT = Join-Path $env:TEMP ('hv-due-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path (Join-Path $env:HEALTH_VAULT_ROOT 'records') -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $env:HEALTH_VAULT_ROOT 'reports') -Force | Out-Null

. (Join-Path $PSScriptRoot '..\scripts\vault.ps1')

$script:Failures = 0
function Check {
    param([string]$Name, [scriptblock]$Body)
    try { & $Body; Write-Host "PASS  $Name" }
    catch { Write-Host "FAIL  $Name :: $($_.Exception.Message)"; $script:Failures++ }
}
function Assert-True {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) { throw $Message }
}

# A record with one overdue item, keyed by a role label we can search for.
$roleLabel = 'zzrole' + [guid]::NewGuid().ToString('N').Substring(0, 6)
Set-VaultRecord -Record @{
    schema = 2
    people = @{ $roleLabel = @{
        conditions  = @()
        medications = @()
        allergies   = @()
        events      = @(@{ id = 'E1'; kind = 'screening'; code = 'demo-test'
                           last_done = '2020-01-01'; interval_months = 12; basis = 'fact' })
    } }
}

$dueScript = Join-Path $PSScriptRoot '..\scripts\due_report.ps1'
$stdout = & pwsh -NoProfile -File $dueScript 2>&1 | Out-String
$code = $LASTEXITCODE

Check 'it exits 0' {
    Assert-True ($code -eq 0) "exit was $code"
}

Check 'stdout carries no role label' {
    Assert-True ($stdout -notmatch $roleLabel) 'stdout leaked a role label from the record'
}

Check 'it reports a DUE status' {
    Assert-True ($stdout -match 'DUE') "stdout did not report DUE: $stdout"
}

Check 'it wrote a report file' {
    $files = Get-ChildItem (Join-Path $env:HEALTH_VAULT_ROOT 'reports') -Filter '*-review.md'
    Assert-True ($files.Count -ge 1) 'no review file was written'
}

Check 'the written report names the overdue item' {
    $files = Get-ChildItem (Join-Path $env:HEALTH_VAULT_ROOT 'reports') -Filter '*-review.md'
    $body = Get-Content -LiteralPath $files[0].FullName -Raw
    Assert-True ($body -match 'demo-test') 'the report does not name the overdue item'
}

Remove-Item -LiteralPath $env:HEALTH_VAULT_ROOT -Recurse -Force -ErrorAction SilentlyContinue
if ($script:Failures -gt 0) { Write-Host "`n$($script:Failures) check(s) failed"; exit 1 }
Write-Host "`nall due-report checks passed"; exit 0
```

- [ ] **Step 2: Run it, expect failure**

Run (escalated — DPAPI needs the real user): `pwsh -NoProfile -File health-advisory/tests/test_due_report.ps1`
Expected: FAIL — `due_report.ps1` does not exist.

- [ ] **Step 3: Write the review script**

`health-advisory/scripts/due_report.ps1`:

```powershell
#Requires -Version 7
<#
  The periodic review. Reads the vault, computes what is due, writes the report
  to a file, and prints counts and the path only.

  It prints no record content: stdout is persisted by the session store, so a
  role label or a medication name on stdout would defeat the whole design.
#>
[CmdletBinding()]
param(
    [string]$OutDir,
    [string]$Today
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'vault.ps1')

Assert-Boundary

$ledgerPath = Join-Path $PSScriptRoot '..\references\singapore-sources.json'
$todayDate  = if ($Today) { [datetime]::ParseExact($Today, 'yyyy-MM-dd', $null) } else { Get-Date }
if (-not $OutDir) { $OutDir = Join-Path $script:VaultRoot 'reports' }

# A source past its review date means nothing dependent on it can be judged.
$stale = @()
if (Test-Path -LiteralPath $ledgerPath) {
    $ledger = Get-Content -LiteralPath $ledgerPath -Raw | ConvertFrom-Json -AsHashtable
    foreach ($source in $ledger['sources']) {
        if ($source['review_by']) {
            $review = [datetime]::ParseExact($source['review_by'], 'yyyy-MM-dd', $null)
            if ($review -lt $todayDate) { $stale += $source['id'] }
        }
    }
} else {
    $stale += 'ledger-missing'
}

$facts = @(); $assumptions = @(); $people = 0
$record = Get-VaultRecord
if ($record -and $record['people']) {
    $people = $record['people'].Keys.Count
    foreach ($personKey in $record['people'].Keys) {
        $person = $record['people'][$personKey]
        foreach ($event in @($person['events'])) {
            if (-not $event['last_done'] -or -not $event['interval_months']) { continue }
            $last  = [datetime]::ParseExact($event['last_done'], 'yyyy-MM-dd', $null)
            $dueOn = $last.AddMonths([int]$event['interval_months'])
            if ($dueOn -lt $todayDate) {
                $line = "- $personKey / $($event['code']): due $($dueOn.ToString('yyyy-MM-dd'))"
                if ($event['basis'] -eq 'assumption') { $assumptions += $line } else { $facts += $line }
            }
        }
    }
}

if ($stale.Count -gt 0) {
    $status = 'CANNOT JUDGE'
} elseif ($facts.Count -gt 0) {
    $status = 'DUE'
} else {
    $status = 'OK'
}

$stamp = $todayDate.ToString('yyyy-MM-dd')
$lines = @(
    "# Household review — $stamp",
    "",
    "**Status: $status**",
    "",
    "## Facts",
    "",
    $(if ($facts.Count) { $facts } else { "- nothing due" }),
    "",
    "## Assumption-dependent — questions for a clinician",
    "",
    $(if ($assumptions.Count) { $assumptions } else { "- nothing to raise" }),
    "",
    "## Cannot judge",
    "",
    $(if ($stale.Count) { "- source(s) past their review date: $($stale -join ', ')" } else { "- nothing outstanding" }),
    "",
    "## What this is not",
    "",
    "These checks being up to date does **not** mean anyone is healthy. It means",
    "the recorded items were compared against dated sources. Nothing here was",
    "examined, and no conclusion about a person was drawn.",
    ""
)

if (-not (Test-Path -LiteralPath $OutDir)) { New-Item -ItemType Directory -Path $OutDir -Force | Out-Null }
$reportPath = Join-Path $OutDir "$stamp-review.md"
Set-Content -LiteralPath $reportPath -Value ($lines -join "`n") -Encoding utf8

# Counts and the path only. Never the content.
Write-Output "status: $status"
Write-Output "people: $people"
Write-Output "due (facts): $($facts.Count)"
Write-Output "to raise: $($assumptions.Count)"
Write-Output "cannot judge: $($stale.Count)"
Write-Output "report: $reportPath"
```

- [ ] **Step 4: Run the test, expect it to pass**

Run (escalated): `pwsh -NoProfile -File health-advisory/tests/test_due_report.ps1`
Expected: five `PASS` lines, then `all due-report checks passed`, exit 0.

- [ ] **Step 5: Prove it reports CANNOT JUDGE on a stale source**

Run (escalated): `pwsh -NoProfile -File health-advisory/scripts/due_report.ps1 -Today 2030-01-01`
Expected: `status: CANNOT JUDGE`, and `cannot judge:` greater than zero.

- [ ] **Step 6: Commit**

```bash
git add health-advisory/scripts/due_report.ps1 health-advisory/tests/test_due_report.ps1
git commit -m "feat(health-advisory): the periodic review, writing to a file and printing counts only"
```

---

### Task 5: `SKILL.md` — the step that makes it load

**Files:**
- Create: `health-advisory/SKILL.md`
- Create: `health-advisory/agents/openai.yaml`
- Create: `health-advisory/tests/test_skill.py`

**Interfaces:**
- Consumes: every reference file and script from plans 1 and 2
- Produces: a loadable skill

**Without this task the skill does not exist as far as Codex is concerned.**
Everything before it is machinery for something that cannot be invoked.

- [ ] **Step 1: Write the failing test**

`health-advisory/tests/test_skill.py`:

```python
"""Self-contained checks on SKILL.md and its metadata. Run directly; no pytest."""
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
FAILURES = []


def check(name, fn):
    try:
        fn()
        print(f"PASS  {name}")
    except AssertionError as exc:
        print(f"FAIL  {name} :: {exc}")
        FAILURES.append(name)


def skill_text():
    return (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")


def frontmatter():
    text = skill_text()
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert match, "SKILL.md has no frontmatter block"
    fields = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    return fields


def test_name_matches_the_folder():
    assert frontmatter().get("name") == SKILL_DIR.name, frontmatter().get("name")


def test_the_description_states_the_boundary_early():
    description = frontmatter().get("description", "")
    first_clause = description.split(".")[0].lower()
    assert "never" in first_clause, f"the boundary is not in the first clause: {first_clause!r}"
    for word in ("diagnosis", "dosing", "triage"):
        assert word in description.lower(), f"the description never mentions {word}"


def test_the_description_routes_away():
    description = frontmatter().get("description", "").lower()
    assert "not for" in description, "the description does not say what it is not for"
    assert "research" in description, "the description does not hand evidence appraisal to research"


def test_the_gate_is_stated_as_running_first():
    text = skill_text().lower()
    assert "emergency gate" in text, "SKILL.md does not name the emergency gate"
    assert "before" in text, "SKILL.md does not say the gate runs before anything else"


def test_every_reference_file_is_named():
    missing = []
    for path in sorted((SKILL_DIR / "references").glob("*")):
        if path.is_file() and path.name not in skill_text():
            missing.append(path.name)
    assert not missing, f"SKILL.md never names: {missing}"


def test_every_script_is_named():
    missing = []
    for path in sorted((SKILL_DIR / "scripts").glob("*.py")):
        if path.name not in skill_text():
            missing.append(path.name)
    assert not missing, f"SKILL.md never names: {missing}"


def test_the_openai_yaml_exists_and_is_named():
    yaml_path = SKILL_DIR / "agents" / "openai.yaml"
    assert yaml_path.is_file(), "agents/openai.yaml is missing"
    assert "display_name" in yaml_path.read_text(encoding="utf-8")


check("the name matches the folder", test_name_matches_the_folder)
check("the description states the boundary early", test_the_description_states_the_boundary_early)
check("the description routes away", test_the_description_routes_away)
check("the gate is stated as running first", test_the_gate_is_stated_as_running_first)
check("every reference file is named", test_every_reference_file_is_named)
check("every script is named", test_every_script_is_named)
check("agents/openai.yaml exists", test_the_openai_yaml_exists_and_is_named)

if FAILURES:
    print(f"\n{len(FAILURES)} check(s) failed")
    sys.exit(1)
print("\nall skill checks passed")
```

- [ ] **Step 2: Run it, expect failure**

Run: `python health-advisory/tests/test_skill.py`
Expected: `FileNotFoundError` — `SKILL.md` does not exist.

- [ ] **Step 3: Write `SKILL.md`**

`health-advisory/SKILL.md`. The `description` is the trigger, so its first clause carries the boundary — that is the only part everyone reads:

```markdown
---
name: health-advisory
description: Answer household health questions from dated, graded sources and keep a family health record — information and preparation, never diagnosis, dosing, triage or prognosis. The emergency gate runs before anything else. Use for health questions, medication and interaction questions, "is there anything new on X", screening and vaccination intervals, understanding a diagnosis or a lab result, preparing for a consultation, and the periodic household review. Not for diagnosis, dosing, triage or prognosis — those leave the room only with a clinician; not for appraising research evidence (use research); not for insurance coverage decisions.
---

# Health Advisory

Answer a health question from dated sources, and keep a household record that is
reviewed on a schedule. The output is information and preparation, never clinical
judgement.

This skill exists because a general assistant answers a health question
confidently from recall, with no source, no date, and no statement of what it
cannot know.

## Boundary — a hard dependency

Read `references/boundary-and-privacy.md`. Every script refuses to run without it.
In short:

- No diagnosis, no dose, no triage downward, no prognosis, no treatment change
- No answer to whether an insurer will pay
- Never correct a treating clinician
- **May escalate. Never de-escalate.**

## Order of operations

1. **The emergency gate runs first**, before any retrieval and for every question
   class. `references/urgency.json` holds the presentations; if the question
   matches one, the first line of the answer is that entry's action. Read
   `references/urgency.md` for why it is data rather than prose.
2. **Route the question.** `references/routing.json` selects the process and the
   effort: terminology, drug, effectiveness or symptom. **Announce the route** —
   "this is a drug-interaction question, so I am going to the label" — so a
   misroute is visible.
3. **Elicit before answering a symptom question.** Ask the three to five
   discriminators, or state what the answer is conditional on. The question as
   typed is often not the question.
4. **Then answer**, per the route.

Only effectiveness questions get the literature sweep. Everything else is
answered from one authoritative source class — being boring when the question is
boring is the point.

## The evidence section

Read `references/source-ladder.md`. Reviews first, with five named fall-throughs
to primary studies; recency as a lane rather than a filter; and always state that
absence of evidence is not evidence of absence.

## Two outputs for anything clinical

- **Household-facing** — the possibilities, the must-not-miss list, and what
  would change the picture. This stays at home.
- **Bring-to-clinician** — history only. Timeline, medications, allergies,
  relevant history, what has been tried, the plan from last time and whether it
  happened, and the questions to ask. **No differential:** a list of
  possibilities anchors the consultation and wastes the appointment.

The clinician outranks this skill. Disagreement with a guideline becomes a
question, never a correction.

## The record

Read `references/record-fields.md`. The vault is
`C:\Users\yuanq\Desktop\chatgpt folder\health-vault`, outside every repository.

- `scripts/vault.ps1` is the only component that touches ciphertext. It exposes
  `status` and deliberately has no command that prints record content.
- **Scripts print counts and IDs, never record content.** Everything read into a
  conversation is written to the local session store in plaintext and persists.
  This is the load-bearing privacy rule; encryption does not substitute for it.
- `scripts/due_report.ps1` writes the periodic review to a file and prints counts.
  It reports **OK**, **DUE** or **CANNOT JUDGE** — the third is not a pass.
- Facts and assumption-dependent items never merge. A due screening is a fact; a
  family-history criterion met is a question for a clinician.
- A clean review says "these checks are up to date" and **never** "you are
  healthy".

## Before any search leaves the machine

Run `scripts/build_query.py`. It refuses rather than sanitises: a question
containing a relationship, an age, a date of birth, an identifier, a contact
detail or a place is rejected with what to rewrite. Search the clinical term.

## Before delivering a report

Run `scripts/validate_report.py`. It rejects identifiers and unsourced claims.
Run `scripts/check_sources.py` too: it fails the whole report on any source past
its review date.

## References

Read only what the task needs.

- `references/boundary-and-privacy.md` — the prohibitions and the privacy protocol
- `references/urgency.json` + `references/urgency.md` — the gate and why it is data
- `references/routing.json` — question class to process
- `references/source-ladder.md` — which source class answers which question
- `references/record-fields.md` — the record schema and its five rules
- `references/singapore-sources.json` — verified sources with review dates

## What this skill is not

Not a research-evidence appraiser — use `research`. Not a poster or deck tool —
use `poster-review`. Not a substitute for a clinician, ever.
```

- [ ] **Step 4: Write the UI metadata**

`health-advisory/agents/openai.yaml`:

```yaml
display_name: "Health Advisory"
short_description: "Household health questions from dated sources, and a record that is reviewed"
default_prompt: "Answer this health question from dated sources, and tell me what it does not settle."
```

- [ ] **Step 5: Run the test, expect it to pass**

Run: `python health-advisory/tests/test_skill.py`
Expected: seven `PASS` lines, then `all skill checks passed`, exit 0.

- [ ] **Step 6: Validate the skill with the official checker**

Run: `python "C:\Users\yuanq\.codex\skills\.system\skill-creator\scripts\quick_validate.py" health-advisory`
Expected: `Skill is valid!`

If it reports an unexpected frontmatter key, that is the checker being stricter
than the runtime — `compatibility` behaves this way and still loads. Do not add
keys the checker rejects without checking that a plugin skill already uses one.

- [ ] **Step 7: Confirm it actually loads**

Run: `codex debug prompt-input "test" | Select-String 'health-advisory'`
Expected: a `health-advisory:` line in the rendered skill list, naming
`SKILL.md`. This is the step that proves the skill is usable — not the validator.

- [ ] **Step 8: Commit**

```bash
git add health-advisory/SKILL.md health-advisory/agents/openai.yaml health-advisory/tests/test_skill.py
git commit -m "feat(health-advisory): SKILL.md, so the skill loads"
```

---

## What this plan does not cover

The publication scaffolding from spec section 11, deliberately deferred until
after a private-use period:

- the README's first-screen never-paste rule and generated expiry
- `.github/ISSUE_TEMPLATE/` that never asks for a condition or a history
- `vault.ps1 status` and `check_sources.py --diagnostic` as the two diagnostic
  entry points a bug report needs
- institutional clearance, the attribution stance, and the non-goals repeated in
  the README

Also deferred: specialty lenses, which are driven by the record's contents and
so wait until the record has contents.
