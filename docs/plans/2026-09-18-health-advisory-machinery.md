# health-advisory machinery — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the safety and data machinery for the `health-advisory` skill: an encrypted vault the agent cannot read, a source ledger that fails closed when stale, a query builder that strips personal detail, and a report validator that rejects identifiers.

**Architecture:** Windows DPAPI for encryption at rest, reached from PowerShell, which is the only component that touches ciphertext. Everything that never touches the vault is Python. Every entry point fails closed when the boundary file is missing. No script prints record content.

**Tech Stack:** PowerShell 7.6.5, Python 3.13.1, Windows DPAPI via `System.Security.Cryptography.ProtectedData`. **No installs** — no pytest, and no Pester dependency (Pester 3.4.0 is present but unused).

**Spec:** `docs/specs/2026-09-18-health-advisory-design.md`

## Global Constraints

- Vault root: `C:\Users\yuanq\Desktop\chatgpt folder\health-vault`, overridable via `$env:HEALTH_VAULT_ROOT`
- No new software may be installed on this machine
- Python tests are plain `assert` scripts run directly; there is no pytest
- **Scripts emit derived values, never record content.** A script that prints a medication name is a defect
- **May escalate, never de-escalate.** No code path may say care is not needed
- **No dose field exists in any output schema**
- Identifiers are never stored: role labels (`adult-a`, `child-a`), never names
- Every entry point fails closed when `references/boundary-and-privacy.md` is missing
- Commit after every task

---

### Task 1: Boundary document and the encrypted vault

**Files:**
- Create: `health-advisory/references/boundary-and-privacy.md`
- Create: `health-advisory/scripts/vault.ps1`
- Test: `health-advisory/tests/test_vault.ps1`

**Interfaces:**
- Consumes: nothing
- Produces: dot-sourceable functions `Assert-Boundary`, `Get-VaultRecord` (hashtable or `$null`), `Set-VaultRecord -Record <hashtable>`, `Get-VaultStatus` (a `pscustomobject` of counts). Script-scope variable `$script:RecordFile`.

- [ ] **Step 1: Write the failing test**

`health-advisory/tests/test_vault.ps1`:

```powershell
#Requires -Version 7
$ErrorActionPreference = 'Stop'

# Isolate the vault: a test must never touch the real record.
$env:HEALTH_VAULT_ROOT = Join-Path $env:TEMP ('hv-test-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path (Join-Path $env:HEALTH_VAULT_ROOT 'records') -Force | Out-Null

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

$marker = 'ZZPROBE' + [guid]::NewGuid().ToString('N')

Check 'round-trip returns the record' {
    $sample = @{
        schema = 2
        people = @{ 'adult-a' = @{
            conditions  = @()
            allergies   = @()
            events      = @()
            medications = @(@{ name = $marker; source = 'label' })
        } }
    }
    Set-VaultRecord -Record $sample
    $back = Get-VaultRecord
    Assert-True ($back['people']['adult-a']['medications'][0]['name'] -eq $marker) 'round-trip mismatch'
}

Check 'the file on disk does not contain the plaintext' {
    $raw = Get-Content -LiteralPath $script:RecordFile -Raw
    Assert-True ($raw -notmatch [regex]::Escape($marker)) 'plaintext found on disk'
}

Check 'status reports counts and leaks no content' {
    $status = Get-VaultStatus | Out-String
    Assert-True ($status -notmatch [regex]::Escape($marker)) 'status leaked record content'
    Assert-True ($status -match 'People') 'status did not report a people count'
}

Check 'a missing boundary file refuses to run' {
    $saved = $script:BoundaryFile
    $script:BoundaryFile = Join-Path $env:TEMP 'hv-no-such-boundary.md'
    try {
        try { Get-VaultRecord | Out-Null; throw 'expected a refusal, got a result' }
        catch { Assert-True ($_.Exception.Message -like 'REFUSING*') "wrong error: $($_.Exception.Message)" }
    } finally { $script:BoundaryFile = $saved }
}

Remove-Item -LiteralPath $env:HEALTH_VAULT_ROOT -Recurse -Force -ErrorAction SilentlyContinue
if ($script:Failures -gt 0) { Write-Host "`n$($script:Failures) check(s) failed"; exit 1 }
Write-Host "`nall vault checks passed"; exit 0
```

- [ ] **Step 2: Run it, expect failure**

Run: `pwsh -File "health-advisory/tests/test_vault.ps1"`
Expected: FAIL — `vault.ps1` does not exist yet, so the dot-source throws.

- [ ] **Step 3: Write the boundary document**

`health-advisory/references/boundary-and-privacy.md`:

```markdown
# Boundary and privacy

This file is a hard dependency. Every script refuses to run without it.

## Never, under any input

- Diagnose, or name a likely condition for a person
- Calculate, adjust or recommend a dose
- Triage downward — say care is not needed, or that something is not serious
- Prognose an individual
- Recommend, sequence, start, stop or modify treatment
- Answer whether an insurer will pay
- Correct a treating clinician

**May escalate. Never de-escalate.** Over-referring wastes an appointment;
under-referring can kill. No code path may say care is not needed.

## Privacy

1. The vault is local. Never synced, never committed, never moved into a repo.
2. Encrypted at rest with DPAPI bound to the current Windows user.
3. **Scripts print counts and IDs, never record content.** A script that would
   echo a medication name is a defect.
4. Search terms are de-identified before leaving. Personal detail appears only
   when the clinical question requires it.
5. No third-party service enters the loop.
6. Reports carry no identifiers and have a stated retention.
7. The emergency card is the one deliberate exception, because in an emergency
   this is what someone needs.
8. Deletion is real: removing an entry removes it, not just a view.

## What this skill is not

Information and preparation, never clinical judgement. Every conclusion that
depends on examining a person belongs to a clinician.
```

- [ ] **Step 4: Write the vault backend**

`health-advisory/scripts/vault.ps1`:

```powershell
#Requires -Version 7
<#
  The only component that touches vault ciphertext.
  Deliberately exposes no command that prints record content.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$script:VaultRoot = if ($env:HEALTH_VAULT_ROOT) { $env:HEALTH_VAULT_ROOT }
                    else { 'C:\Users\yuanq\Desktop\chatgpt folder\health-vault' }
$script:BoundaryFile = Join-Path $PSScriptRoot '..\references\boundary-and-privacy.md'
$script:RecordFile   = Join-Path $script:VaultRoot 'records\household_health.json'

function Assert-Boundary {
    if (-not (Test-Path -LiteralPath $script:BoundaryFile)) {
        throw "REFUSING TO RUN: boundary-and-privacy.md is missing at $($script:BoundaryFile)"
    }
}

function Protect-Text {
    param([Parameter(Mandatory)][string]$Text)
    Add-Type -AssemblyName System.Security
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
    $enc = [System.Security.Cryptography.ProtectedData]::Protect($bytes, $null, 'CurrentUser')
    [Convert]::ToBase64String($enc)
}

function Unprotect-Text {
    param([Parameter(Mandatory)][string]$Base64)
    Add-Type -AssemblyName System.Security
    $enc = [Convert]::FromBase64String($Base64)
    $bytes = [System.Security.Cryptography.ProtectedData]::Unprotect($enc, $null, 'CurrentUser')
    [System.Text.Encoding]::UTF8.GetString($bytes)
}

function Get-VaultRecord {
    Assert-Boundary
    if (-not (Test-Path -LiteralPath $script:RecordFile)) { return $null }
    $b64 = (Get-Content -LiteralPath $script:RecordFile -Raw).Trim()
    Unprotect-Text -Base64 $b64 | ConvertFrom-Json -AsHashtable
}

function Set-VaultRecord {
    param([Parameter(Mandatory)]$Record)
    Assert-Boundary
    $json = $Record | ConvertTo-Json -Depth 12
    $dir = Split-Path -Parent $script:RecordFile
    if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    Set-Content -LiteralPath $script:RecordFile -Value (Protect-Text -Text $json) -NoNewline
}

function Get-VaultStatus {
    Assert-Boundary
    $exists = Test-Path -LiteralPath $script:RecordFile
    $people = 0; $meds = 0; $conditions = 0; $events = 0
    if ($exists) {
        $record = Get-VaultRecord
        if ($record -and $record['people']) {
            $people = $record['people'].Keys.Count
            foreach ($key in $record['people'].Keys) {
                $person = $record['people'][$key]
                if ($person['medications']) { $meds += @($person['medications']).Count }
                if ($person['conditions'])  { $conditions += @($person['conditions']).Count }
                if ($person['events'])      { $events += @($person['events']).Count }
            }
        }
    }
    [pscustomobject]@{
        Backend       = 'DPAPI (CurrentUser)'
        RecordPath    = $script:RecordFile
        Exists        = $exists
        LastWriteTime = if ($exists) { (Get-Item -LiteralPath $script:RecordFile).LastWriteTime.ToString('s') } else { $null }
        People        = $people
        Medications   = $meds
        Conditions    = $conditions
        Events        = $events
    }
}

# CLI entry point. Only 'status' exists: there is deliberately no command that
# prints record content, because stdout is persisted by the session store.
if ($MyInvocation.InvocationName -ne '.' -and $args.Count -ge 1) {
    switch ($args[0]) {
        'status' { Get-VaultStatus | Format-List; exit 0 }
        default  { Write-Error "Unknown command '$($args[0])'. Only 'status' exists."; exit 2 }
    }
}
```

- [ ] **Step 5: Run the test, expect it to pass**

Run: `pwsh -File "health-advisory/tests/test_vault.ps1"`
Expected: four `PASS` lines, then `all vault checks passed`, exit 0.

- [ ] **Step 6: Verify the CLI exposes only `status`**

Run: `pwsh -NoProfile -File "health-advisory/scripts/vault.ps1" status`
Expected: a `Backend` line and counts, exit 0, and no record content.

Run: `pwsh -NoProfile -File "health-advisory/scripts/vault.ps1" read`
Expected: `Unknown command 'read'`, exit 2. There is no command that prints content.

- [ ] **Step 7: Prove the sandbox cannot read the vault**

Write a record, then read the raw file from a sandboxed shell and confirm it is not JSON.

Run (sandboxed): `Get-Content -LiteralPath "C:\Users\yuanq\Desktop\chatgpt folder\health-vault\records\household_health.json" -Raw`
Expected: a Base64 blob that does not parse as JSON. If readable JSON appears, DPAPI is not being applied — stop and fix this task before continuing.

- [ ] **Step 8: Commit**

```bash
git add health-advisory/references/boundary-and-privacy.md health-advisory/scripts/vault.ps1 health-advisory/tests/test_vault.ps1
git commit -m "feat(health-advisory): encrypted vault backend and the boundary document"
```

---

### Task 2: Source ledger and the staleness checker

**Files:**
- Create: `health-advisory/scripts/check_sources.py`
- Create: `health-advisory/references/singapore-sources.json`
- Test: `health-advisory/tests/test_check_sources.py`

**Interfaces:**
- Consumes: nothing
- Produces: `check_sources.load(path) -> dict`; `check_sources.problems(entries, today) -> list[tuple[str, str]]`; `check_sources.main(argv) -> int` (0 clean, 1 problems). Ledger shape: `{"sources": [ {id, title, url, class, verified_on, review_by, status?} ]}`.

- [ ] **Step 1: Write the failing test**

`health-advisory/tests/test_check_sources.py`:

```python
"""Self-contained checks for check_sources.py. Run directly; no pytest."""
import json
import sys
import tempfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import check_sources as cs

TODAY = date(2026, 9, 18)
FAILURES = []


def entry(**overrides):
    base = {
        "id": "SG-EXAMPLE-1",
        "title": "Example source",
        "url": "https://example.org/guidance",
        "class": "guideline",
        "verified_on": "2026-09-18",
        "review_by": "2027-09-18",
    }
    base.update(overrides)
    return base


def check(name, fn):
    try:
        fn()
        print(f"PASS  {name}")
    except AssertionError as exc:
        print(f"FAIL  {name} :: {exc}")
        FAILURES.append(name)


def test_valid_entry_has_no_problems():
    assert cs.problems([entry()], TODAY) == []


def test_unverified_status_is_a_problem():
    found = cs.problems([entry(status="unverified")], TODAY)
    assert any("unverified" in msg for _, msg in found), found


def test_past_review_date_is_a_problem():
    found = cs.problems([entry(review_by="2026-01-01")], TODAY)
    assert any("passed" in msg for _, msg in found), found


def test_missing_url_is_a_problem():
    found = cs.problems([entry(url="")], TODAY)
    assert any("missing url" in msg for _, msg in found), found


def test_unparseable_date_is_a_problem():
    found = cs.problems([entry(verified_on="September 2026")], TODAY)
    assert any("not an ISO date" in msg for _, msg in found), found


def test_missing_ledger_exits_nonzero():
    missing = Path(tempfile.gettempdir()) / "hv-nope-does-not-exist.json"
    assert cs.main(["--ledger", str(missing)]) == 1


def test_invalid_json_exits_nonzero():
    bad = Path(tempfile.gettempdir()) / "hv-bad-ledger.json"
    bad.write_text("{not json", encoding="utf-8")
    assert cs.main(["--ledger", str(bad)]) == 1


check("a valid entry has no problems", test_valid_entry_has_no_problems)
check("an unverified entry is a problem", test_unverified_status_is_a_problem)
check("a past review date is a problem", test_past_review_date_is_a_problem)
check("a missing url is a problem", test_missing_url_is_a_problem)
check("an unparseable date is a problem", test_unparseable_date_is_a_problem)
check("a missing ledger exits non-zero", test_missing_ledger_exits_nonzero)
check("invalid JSON exits non-zero", test_invalid_json_exits_nonzero)

if FAILURES:
    print(f"\n{len(FAILURES)} check(s) failed")
    sys.exit(1)
print("\nall source-ledger checks passed")
```

- [ ] **Step 2: Run it, expect failure**

Run: `python "health-advisory/tests/test_check_sources.py"`
Expected: `ModuleNotFoundError: No module named 'check_sources'`.

- [ ] **Step 3: Write the checker**

`health-advisory/scripts/check_sources.py`:

```python
"""Fail on any source entry that is unverified or past its review date.

Exit codes: 0 all entries valid; 1 problems found or the ledger is unreadable.
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

REQUIRED = ("id", "title", "url", "class", "verified_on", "review_by")
DEFAULT_LEDGER = Path(__file__).resolve().parent.parent / "references" / "singapore-sources.json"


def load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def parse_day(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def problems(entries, today):
    """Return (id, message) for every entry that cannot be trusted."""
    found = []
    for index, source in enumerate(entries):
        identifier = source.get("id") or f"entry #{index + 1}"
        for key in REQUIRED:
            if not source.get(key):
                found.append((identifier, f"missing {key}"))
        for key in ("verified_on", "review_by"):
            value = source.get(key)
            if value and parse_day(value) is None:
                found.append((identifier, f"{key} is not an ISO date: {value!r}"))
        if source.get("status") == "unverified":
            found.append((identifier, "status is unverified"))
        review = parse_day(source.get("review_by"))
        if review and review < today:
            found.append((identifier, f"review date {review.isoformat()} has passed"))
    return found


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    parser.add_argument("--today", default=None, help="override today's date, for testing")
    args = parser.parse_args(argv)

    today = date.fromisoformat(args.today) if args.today else date.today()
    try:
        data = load(args.ledger)
    except FileNotFoundError:
        print(f"FAIL: ledger not found: {args.ledger}")
        return 1
    except json.JSONDecodeError as exc:
        print(f"FAIL: ledger is not valid JSON: {exc}")
        return 1

    entries = data.get("sources", [])
    found = problems(entries, today)
    if found:
        print(f"FAIL: {len(found)} problem(s) across {len(entries)} entr(ies)")
        for identifier, message in found:
            print(f"  {identifier}: {message}")
        return 1
    print(f"OK: {len(entries)} source(s) verified, none past review")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Write the ledger, with an explicitly empty source list**

`health-advisory/references/singapore-sources.json`:

```json
{
  "_note": "Every entry names its source, the date it was confirmed, and the date it must be re-checked. check_sources.py fails the whole report on any entry that is unverified or past its review date. Do not add an entry without fetching it first.",
  "jurisdiction": "Singapore",
  "last_reviewed": "2026-09-18",
  "sources": []
}
```

- [ ] **Step 5: Run the tests and the checker**

Run: `python "health-advisory/tests/test_check_sources.py"`
Expected: seven `PASS` lines, then `all source-ledger checks passed`, exit 0.

Run: `python "health-advisory/scripts/check_sources.py"`
Expected: `OK: 0 source(s) verified, none past review`, exit 0. An empty ledger passes; Task 3 fills it.

- [ ] **Step 6: Commit**

```bash
git add health-advisory/scripts/check_sources.py health-advisory/tests/test_check_sources.py health-advisory/references/singapore-sources.json
git commit -m "feat(health-advisory): source ledger schema and the fail-closed staleness checker"
```

---

### Task 3: Verify three Singapore sources into the ledger

**Files:**
- Modify: `health-advisory/references/singapore-sources.json`

**Interfaces:**
- Consumes: the ledger shape from Task 2, and `check_sources.main` as the gate
- Produces: three verified entries whose `id` values later tasks cite

This is a research task, not a coding task. The acceptance criterion is objective: three entries, each with a URL that returns HTTP 200, a `verified_on` of the day it was fetched, and a `review_by` set by source class.

- [ ] **Step 1: Fetch each candidate and record the status code**

```bash
curl -sL -o /dev/null -w "%{http_code} %{url_effective}\n" https://www.moh.gov.sg/
curl -sL -o /dev/null -w "%{http_code} %{url_effective}\n" https://www.hsa.gov.sg/
curl -sL -o /dev/null -w "%{http_code} %{url_effective}\n" https://www.healthhub.sg/
```

Expected: `200` for each. A non-200 rejects that candidate; find a replacement before continuing.

- [ ] **Step 2: Read each page and confirm it is what we claim it is**

Open each URL and write, into `title`, exactly what the page is — not what we hoped it would be. If a page turns out to be a landing page rather than the guideline index, record it as a landing page and narrow the URL to the specific index.

Expected: three URLs, each describable in one accurate sentence.

- [ ] **Step 3: Add the three entries**

Append to `sources` in `health-advisory/references/singapore-sources.json` in this exact shape. Set `review_by` to 12 months for a guideline index, 6 months for a safety-alert feed.

```json
{
  "id": "SG-MOH-CPG",
  "title": "<what the page actually is>",
  "url": "<the URL that returned 200>",
  "class": "guideline",
  "verified_on": "YYYY-MM-DD",
  "review_by": "YYYY-MM-DD"
}
```

- [ ] **Step 4: Prove the gate bites**

Temporarily set one entry's `review_by` to a past date.

Run: `python "health-advisory/scripts/check_sources.py"`
Expected: `FAIL: 1 problem(s) across 3 entr(ies)` naming that entry, exit 1.

Restore the correct date and re-run. Expected: `OK: 3 source(s) verified, none past review`, exit 0.

- [ ] **Step 5: Commit**

```bash
git add health-advisory/references/singapore-sources.json
git commit -m "feat(health-advisory): verify three Singapore sources with review dates"
```

---

### Task 4: The de-identifying query builder

**Files:**
- Create: `health-advisory/scripts/build_query.py`
- Test: `health-advisory/tests/test_build_query.py`

**Interfaces:**
- Consumes: nothing
- Produces: `build_query.find_personal(text) -> list[tuple[str, str]]`; `build_query.build_query(terms) -> str`; `build_query.main(argv) -> int` (0 query printed, 2 refused)

- [ ] **Step 1: Write the failing test**

`health-advisory/tests/test_build_query.py`:

```python
"""Self-contained checks for build_query.py. Run directly; no pytest."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import build_query as bq

FAILURES = []


def check(name, fn):
    try:
        fn()
        print(f"PASS  {name}")
    except AssertionError as exc:
        print(f"FAIL  {name} :: {exc}")
        FAILURES.append(name)


def labels(text):
    return {label for label, _ in bq.find_personal(text)}


def test_relationship_is_detected():
    assert "relationship" in labels("my son has a fever")


def test_age_is_detected():
    assert "age" in labels("a 3-year-old with a rash")


def test_date_of_birth_is_detected():
    assert "date of birth" in labels("born 2019-04-02")


def test_national_id_is_detected():
    assert "national ID" in labels("S1234567D")


def test_location_is_detected():
    assert "location" in labels("is this common in Singapore")


def test_a_clinical_question_is_clean():
    assert bq.find_personal("warfarin and aspirin interaction") == []


def test_clinical_terms_are_joined_with_and():
    assert bq.build_query(["warfarin", "aspirin"]) == "warfarin AND aspirin"


def test_a_personal_question_is_refused():
    assert bq.main(["--question", "my son has a fever"]) == 2


def test_a_clean_question_with_no_terms_is_used_directly():
    assert bq.main(["--question", "warfarin and aspirin interaction"]) == 0


def test_an_empty_question_is_refused():
    assert bq.main(["--question", "   "]) == 2


check("a relationship is detected", test_relationship_is_detected)
check("an age is detected", test_age_is_detected)
check("a date of birth is detected", test_date_of_birth_is_detected)
check("a national ID is detected", test_national_id_is_detected)
check("a location is detected", test_location_is_detected)
check("a clinical question is clean", test_a_clinical_question_is_clean)
check("terms are joined with AND", test_clinical_terms_are_joined_with_and)
check("a personal question is refused", test_a_personal_question_is_refused)
check("a clean question is used directly", test_a_clean_question_with_no_terms_is_used_directly)
check("an empty question is refused", test_an_empty_question_is_refused)

if FAILURES:
    print(f"\n{len(FAILURES)} check(s) failed")
    sys.exit(1)
print("\nall query-builder checks passed")
```

- [ ] **Step 2: Run it, expect failure**

Run: `python "health-advisory/tests/test_build_query.py"`
Expected: `ModuleNotFoundError: No module named 'build_query'`.

- [ ] **Step 3: Write the builder**

`health-advisory/scripts/build_query.py`:

```python
"""Turn a household question into a de-identified search string.

This refuses rather than sanitises: if personal detail would leave the machine,
the query is rejected and the caller is told what to rewrite.

Exit codes: 0 a query was printed; 2 refused.
"""
import argparse
import re
import sys

PERSONAL_PATTERNS = (
    (re.compile(r"\b(?:my|our|his|her|their)\s+(?:son|daughter|wife|husband|mother|father|child|kid|baby)\b", re.I), "relationship"),
    (re.compile(r"\b\d{1,3}\s*(?:-|\s)?(?:year|yr|month|week|day)s?[-\s]?old\b", re.I), "age"),
    (re.compile(r"\b(?:i am|aged|age)\s*\d{1,3}\b", re.I), "age"),
    (re.compile(r"\b(?:19|20)\d{2}-\d{2}-\d{2}\b"), "date of birth"),
    (re.compile(r"\b[STFG]\d{7}[A-Z]\b"), "national ID"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "email"),
    (re.compile(r"\b(?:\+65|65)?\s?[689]\d{3}\s?\d{4}\b"), "phone"),
    (re.compile(r"\b(?:singapore|hong kong|shanghai|beijing|taipei)\b", re.I), "location"),
)


def find_personal(text):
    """Return (label, matched text) for every personal marker found."""
    hits = []
    for pattern, label in PERSONAL_PATTERNS:
        for match in pattern.finditer(text):
            hits.append((label, match.group(0)))
    return hits


def build_query(terms):
    return " AND ".join(term.strip() for term in terms if term.strip())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--question", required=True)
    parser.add_argument("--term", action="append", default=[],
                        help="a clinical term; repeat for more")
    args = parser.parse_args(argv)

    hits = find_personal(args.question)
    if hits:
        print("REFUSED: the question contains personal detail that must not leave the machine:")
        for label, text in hits:
            print(f"  {label}: {text!r}")
        print("Rewrite using clinical terms only, and pass them with --term.")
        return 2

    query = build_query(args.term) if args.term else args.question.strip()
    if not query:
        print("REFUSED: nothing to search.")
        return 2

    print(query)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the test, expect it to pass**

Run: `python "health-advisory/tests/test_build_query.py"`
Expected: ten `PASS` lines, then `all query-builder checks passed`, exit 0.

- [ ] **Step 5: Prove it refuses a real-shaped question**

Run: `python "health-advisory/scripts/build_query.py" --question "my 4-year-old in Singapore was given ibuprofen"`
Expected: exit 2, listing `relationship`, `age` and `location`, and printing no query.

- [ ] **Step 6: Commit**

```bash
git add health-advisory/scripts/build_query.py health-advisory/tests/test_build_query.py
git commit -m "feat(health-advisory): de-identifying query builder that refuses rather than sanitises"
```

---

### Task 5: The report validator

**Files:**
- Create: `health-advisory/scripts/validate_report.py`
- Test: `health-advisory/tests/test_validate_report.py`

**Interfaces:**
- Consumes: nothing
- Produces: `validate_report.check(text) -> list[str]`; `validate_report.main(argv) -> int` (0 passes, 1 problems)

- [ ] **Step 1: Write the failing test**

`health-advisory/tests/test_validate_report.py`:

```python
"""Self-contained checks for validate_report.py. Run directly; no pytest."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import validate_report as vr

FAILURES = []

CLEAN = """# Household review

## Evidence
**Reviews** — nothing fits this question (search logged 2026-09-18).
**Last 12 months** — nothing since 2024-03-01.

**Sources**
- https://www.moh.gov.sg/ (verified 2026-09-18)
"""


def check(name, fn):
    try:
        fn()
        print(f"PASS  {name}")
    except AssertionError as exc:
        print(f"FAIL  {name} :: {exc}")
        FAILURES.append(name)


def test_a_clean_report_passes():
    assert vr.check(CLEAN) == []


def test_a_national_id_is_rejected():
    found = vr.check(CLEAN + "\nS1234567D\n")
    assert any("national ID" in problem for problem in found), found


def test_an_email_is_rejected():
    found = vr.check(CLEAN + "\nreach me at a@b.com\n")
    assert any("email" in problem for problem in found), found


def test_a_diagnostic_assertion_is_rejected():
    found = vr.check(CLEAN + "\nyou likely have influenza\n")
    assert any("diagnostic assertion" in problem for problem in found), found


def test_a_dose_instruction_is_rejected():
    found = vr.check(CLEAN + "\ntake 500 mg twice a day\n")
    assert any("dose instruction" in problem for problem in found), found


def test_a_missing_recency_block_is_rejected():
    found = vr.check(CLEAN.replace("**Last 12 months** — nothing since 2024-03-01.", ""))
    assert any("recency" in problem for problem in found), found


def test_a_missing_evidence_section_is_rejected():
    found = vr.check("# Household review\n\nnothing here\n")
    assert any("Evidence section" in problem for problem in found), found


check("a clean report passes", test_a_clean_report_passes)
check("a national ID is rejected", test_a_national_id_is_rejected)
check("an email is rejected", test_an_email_is_rejected)
check("a diagnostic assertion is rejected", test_a_diagnostic_assertion_is_rejected)
check("a dose instruction is rejected", test_a_dose_instruction_is_rejected)
check("a missing recency block is rejected", test_a_missing_recency_block_is_rejected)
check("a missing Evidence section is rejected", test_a_missing_evidence_section_is_rejected)

if FAILURES:
    print(f"\n{len(FAILURES)} check(s) failed")
    sys.exit(1)
print("\nall report-validator checks passed")
```

- [ ] **Step 2: Run it, expect failure**

Run: `python "health-advisory/tests/test_validate_report.py"`
Expected: `ModuleNotFoundError: No module named 'validate_report'`.

- [ ] **Step 3: Write the validator**

`health-advisory/scripts/validate_report.py`:

```python
"""Reject a generated report that carries identifiers or unsourced claims.

Exit codes: 0 the report passes; 1 problems found.
"""
import argparse
import re
import sys
from pathlib import Path

IDENTIFIERS = (
    (re.compile(r"\b[STFG]\d{7}[A-Z]\b"), "national ID"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "email"),
    (re.compile(r"\b(?:\+65|65)?\s?[689]\d{3}\s?\d{4}\b"), "phone"),
    (re.compile(r"\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(?:19|20)\d{2}\b"), "exact date of birth"),
)

ASSERTIONS = (
    (re.compile(r"\b(?:you|he|she|they)\s+(?:likely\s+)?(?:has|have)\b", re.I), "diagnostic assertion"),
    (re.compile(r"\bthe diagnosis is\b", re.I), "diagnostic assertion"),
    (re.compile(r"\bstop taking\b", re.I), "treatment instruction"),
    (re.compile(r"\btake\s+\d+(?:\.\d+)?\s?mg\b", re.I), "dose instruction"),
    (re.compile(r"\bincrease the dose\b", re.I), "dose instruction"),
)

REQUIRED = (
    ("## Evidence", "no Evidence section"),
    ("Last 12 months", "no recency block"),
    ("Sources", "no Sources block"),
    ("http", "no resolvable source link"),
)


def check(text):
    """Return a list of problems. An empty list means the report passes."""
    found = []
    for needle, message in REQUIRED:
        if needle not in text:
            found.append(message)
    for pattern, label in IDENTIFIERS + ASSERTIONS:
        for match in pattern.finditer(text):
            found.append(f"{label}: {match.group(0)!r}")
    return found


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report")
    args = parser.parse_args(argv)

    path = Path(args.report)
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"FAIL: report not found: {path}")
        return 1

    found = check(text)
    if found:
        print(f"FAIL: {len(found)} problem(s) in {path.name}")
        for problem in found:
            print(f"  {problem}")
        return 1
    print(f"OK: {path.name} carries no identifiers and no unsourced claims")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the test, expect it to pass**

Run: `python "health-advisory/tests/test_validate_report.py"`
Expected: seven `PASS` lines, then `all report-validator checks passed`, exit 0.

- [ ] **Step 5: Run every check in the machinery**

```bash
pwsh -File "health-advisory/tests/test_vault.ps1"
python "health-advisory/tests/test_check_sources.py"
python "health-advisory/tests/test_build_query.py"
python "health-advisory/tests/test_validate_report.py"
python "health-advisory/scripts/check_sources.py"
```

Expected: every command exits 0.

- [ ] **Step 6: Commit**

```bash
git add health-advisory/scripts/validate_report.py health-advisory/tests/test_validate_report.py
git commit -m "feat(health-advisory): report validator rejecting identifiers and unsourced claims"
```

---

## What this plan does not cover

Deliberately, so that this plan produces working software on its own:

- `due_report.ps1`, the periodic review — plan 2
- `references/source-ladder.md`, `urgency.json`, `urgency.md`, `record-fields.md` — plan 2
- `SKILL.md` and `agents/openai.yaml` — plan 2
- Publication scaffolding from spec section 11 — deferred until after the private-use period
