# Record fields

The vault holds one JSON document. People are keyed by role label, never by name.

## Per person

| Field | Shape | Rule |
|---|---|---|
| `conditions` | list of `{name, onset, onset_reports, last_confirmed}` | `last_confirmed` is required; `onset_reports` carries who said what |
| `medications` | list of `{name, dose_text, prescriber, started, stopped, stop_reason, source}` | `source` is one of `label`, `pharmacy`, `memory` |
| `allergies` | list of `{substance, reaction, last_confirmed}` | the reaction type is required, not just the substance |
| `family_history` | list of `{relative, condition, age_at_diagnosis, side}` | a vague entry is rejected rather than stored |
| `measurements` | list of `{value, unit, reference_range, conditions_of_measurement, taken_on}` | home readings record the conditions |
| `treatments_tried` | list of `{name, kind, started, stopped, outcome, informant}` | `null` means **not recorded**, which is not the same as "none tried" |
| `planned_procedures` | list of `{code, name, tosp_table, setting, planned_for, status, pre_op_outstanding}` | a booked procedure is not an event; it has a date and a decision point, not an interval |
| `events` | list of `{id, kind, code, last_done, interval_months, basis, source_id}` | see below |

`events.kind` is one of `screening`, `vaccination`, `monitoring`.
It is also `procedure` for an operation that has already happened, which is how a
surgical history is recorded without inventing a separate section.
`events.basis` is `fact` or `assumption`, and it decides which section of the
review the item appears in.

## Onset reports, and who said so

Duration is often the fact a decision turns on, and it is also the fact a
household is least able to state precisely. So `onsets` are stored as **reports,
not as a single value**:

```json
"onset_reports": [
  { "when": "2025-09", "precision": "month", "informant": "parent", "approximate": true },
  { "when": "2026-07", "precision": "month", "informant": "helper", "approximate": true,
    "note": "noticed, which is a lower bound and not an onset" }
]
```

**Disagreement is preserved, never averaged.** Two informants giving different
dates is itself a finding — it means the true onset is unknown, and that
uncertainty belongs in the record rather than being resolved by picking one.

Two rules follow:

- **"Noticed on <date>" is a lower bound, not an onset.** A condition can be
  present for a long time before anyone looks.
- **Never store a single onset date when the reports conflict.** Store both and
  mark the conflict.

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
6. **A report is not a measurement.** Where a fact comes from a person's memory
   rather than a document, record the informant and mark it approximate.

## Identifiers are never stored

No names. No full dates of birth — year or age band only. No national ID, no
address, no phone number, no email. `validate_report.py` rejects a generated
report containing any of these patterns.

## Known keys

`validate_record.ps1` enforces exactly these, and **fails on any key not listed
here**. That is deliberate: a misspelled key makes a real item invisible, and the
review then reports a false all-clear. A typo must be loud, not silent.

| Level | Required | Optional |
|---|---|---|
| document | `schema`, `people` | `as_of` |
| person | `conditions`, `medications`, `allergies` | `age_band`, `blood_type`, `family_history`, `measurements`, `lifestyle`, `treatments_tried`, `treatments_tried_note`, `planned_procedures`, `events` |
| blood type | `value`, `source`, `last_confirmed` | — |
| lifestyle | `name`, `value`, `last_confirmed` | `note` |
| condition | `name`, `last_confirmed` | `onset_reports`, `onset_unknown`, `onset_conflict`, `severity`, `reported_by`, `note` |
| onset report | `when`, `informant`, `approximate` | `precision`, `note` |
| medication | `name`, `source` | `dose_text`, `prescriber`, `started`, `stopped`, `stop_reason`, `stated_reason` |
| allergy | `substance`, `reaction`, `last_confirmed` | — |
| family history | `relative`, `condition` | `age_at_diagnosis`, `side` |
| measurement | `name`, `value`, `unit`, `taken_on` | `reference_range`, `conditions_of_measurement` |
| planned procedure | `code`, `status`, `planned_for`, `pre_op_outstanding` | `name`, `tosp_table`, `setting`, `source` |
| event | `id`, `kind`, `code`, `last_done`, `interval_months`, `basis`, `source_id` | — |

`schema` must be a version this skill knows. An unrecognised version is refused
rather than read, so an old record cannot be silently misread by new code.

`stated_reason` is what the household believes the medicine is for, in their
words. It is kept separate from any indication because a mismatch between the two
is a real and checkable error — a medicine prescribed for one thing, understood
at home as being for another. Recording only the drug name loses the evidence.

## `null` means not recorded; `[]` means none

`conditions`, `medications` and `allergies` are required keys, so they can never
be absent. That made rule 5 unenforceable — a person whose allergies were never
asked could only be written as `[]`, which reads as "none known", the exact
conflation the rule forbids.

The semantics are therefore:

| Value | Means |
|---|---|
| `null` | **not recorded** — nobody has asked |
| `[]` | recorded, and there are none |
| a list with entries | recorded, with the entries |

The same applies to `treatments_tried`. A gap is a fact about the record, and it
belongs in the record rather than in someone's memory of what was asked.

## Measurements need a name, and blood pressure is two numbers

A measurement without a name is unreadable: `110` with unit `mg/dL` does not say
what was measured, and `97` with unit `mmHg` does not say which pressure. So
`name` is required — `"weight"`, `"height"`, `"blood pressure"`, `"pulse rate"`.

Blood pressure is inherently a pair, so `value` may be a **string** where the
reading is a pair: `"97/60"` with unit `mmHg`. Numeric trending is not supported
and is not wanted; a chart of self-reported readings is the artefact this skill
refuses to produce.

`reference_range` must come from a source. Where no verified range has been
fetched, leave it unrecorded rather than filling in a remembered one — an
invented "normal range" is exactly the kind of plausible-looking number rule 4
exists to stop.

`conditions_of_measurement` matters more than it looks for a home reading: which
arm, seated or standing, how long after activity or a meal. A blood pressure
without its conditions is close to uninterpretable.

## `condition.note` holds what is not the diagnosis

Morphology, what relieves and what aggravates, a second label a clinician used, a
diagnosis described as "considered" rather than confirmed. None of that is the
diagnosis name, and without a note it has nowhere to go — so it gets dropped, and
dropped detail is how a record becomes less useful than the patient.

The note is where a **disagreement between labels is preserved rather than
resolved**, in the same way a conflicting onset is kept as two reports.

## Provenance is recorded, and it is asked for

`reported_by` on a condition and `source` on a medication are not decoration.
They are the difference between a clinician's finding, the household's account,
and a summary of that account produced by something else.

**A document's appearance does not establish its source.** An AI-generated
summary of the household's own description reads like a clinical history and is
not one; it can add, smooth and rename. Record which it is, and when the source
is not established, ask before writing it down.
