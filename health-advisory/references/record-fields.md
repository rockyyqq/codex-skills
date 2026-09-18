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

**`interval_months` is optional, and must be sourced when present.** An event with
a date but no sourced interval is a gap, not an error. Recording "a Pap smear in
2025" is useful on its own, and inventing a three-year interval from memory is
the kind of number this record refuses. The gap function reports such an event as
*no sourced interval*, so the missing guideline stays visible.

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

**The patterns themselves are Singapore-shaped** — the NRIC format, `+65` phone
numbers, the "7 July 2026" date form. A check keyed to one country's formats does
not notice another country's, so the identifier list is one of the four things
that must be re-verified rather than carried across a relocation. See
`source-ladder.md`.

**All dates in the record are ISO** — `2026-09-18`. A date written as
"7 July 2026" is indistinguishable from a date of birth, which is the shape the
privacy check exists to catch, so the check flags it. Writing every date in ISO
keeps that check strict and useful instead of loosening it until it catches
nothing.

## Known keys

`validate_record.ps1` enforces exactly these, and **fails on any key not listed
here**. That is deliberate: a misspelled key makes a real item invisible, and the
review then reports a false all-clear. A typo must be loud, not silent.

| Level | Required | Optional |
|---|---|---|
| document | `schema`, `people` | `as_of` |
| person | `conditions`, `medications`, `allergies` | `relationship`, `age_band`, `blood_type`, `family_history`, `measurements`, `lifestyle`, `treatments_tried`, `treatments_tried_note`, `planned_procedures`, `events` |
| blood type | `value`, `source`, `last_confirmed` | — |
| lifestyle | `name`, `value`, `last_confirmed` | `note` |
| condition | `name`, `last_confirmed` | `onset_reports`, `onset_unknown`, `onset_conflict`, `severity`, `reported_by`, `note` |
| onset report | `when`, `informant`, `approximate` | `precision`, `note` |
| medication | `name`, `source` | `dose_text`, `prescriber`, `started`, `stopped`, `stop_reason`, `stated_reason`, `note` |
| allergy | `substance`, `reaction`, `last_confirmed` | `note` |
| family history | `relative`, `condition` | `age_at_diagnosis`, `side`, `note` |
| measurement | `name`, `value`, `unit`, `taken_on` | `reference_range`, `conditions_of_measurement` |
| planned procedure | `code`, `status`, `planned_for`, `pre_op_outstanding` | `name`, `tosp_table`, `setting`, `source` |
| event | `id`, `kind`, `code`, `basis` | `last_done`, `interval_months`, `source_id`, `note` |

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

## Role labels need a relationship

`child-a` and `adult-b` are anonymised identifiers: they carry no names, which is
the point. But they also carry no meaning, so nothing in the record says which
person is the daughter, the son, the mother or the father — and a household read
months later cannot tell them apart.

`relationship` supplies that in one word (`daughter`, `son`, `mother`, `father`)
without breaking the no-identifiers rule. A relationship is not an identifier;
a name is.

## Family history is blood relatives

A spouse's conditions are **not** family history for the other spouse — a
spouse is not a blood relative. They are household context, and they live in the
spouse's own record. For a child, both parents and any sibling are blood
relatives, so all of their conditions belong in the child's family history.

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

## Ask whoever can observe it — not whoever is closest

**The right informant depends on the symptom, not on who holds the record.**

- **Throat phlegm, pain, mood, how something feels** — the person. These relocate
  when they travel. Two descriptions in this household arrived second-hand and
  both were wrong: "sinus symptoms" was a throat problem, and an "eczema-like"
  label came back from a summary as "urticarial". Neither informant was lying;
  a description moving through another person changes where it points.
- **Snoring, breathing at night, a rash on someone's back** — an observer. A
  person cannot report what happens while they are asleep, and "I don't know, I
  was asleep" is a correct answer. Here the observer supplied the frequency, the
  loudness, the aggravating factor, and a next-morning consequence the person
  could never have connected to the night before.

So the rule is not "first-hand always wins". It is **ask whoever is in a position
to know**, and record which it was. When a record was built from a proxy and the
person later answers, their account replaces the proxy's — and say so, because
the correction is itself information.

## An unquantified descriptor is not an entry

"Severe", "quite bad", "occasionally", "a lot" are the shape of a finding with the
content missing.

One entry in this household read *"a severe allergic reaction"*. Asked what
actually happened, it became: generalised plaques a centimetre or two across from
head to foot, one joining the next, **no throat swelling, no breathing
difficulty**, taken to A&E, a high-dose oral antihistamine, no injection, resolved
in about a week.

**Those are different histories.** One with airway involvement is not the same as
one without, and the adjective did not distinguish them. When a descriptor
arrives, ask what was seen or what happened and record that. The adjective can
stay; it cannot stand alone.

## Preserve conflict; never average it

Two informants giving different onsets. A clinician using two labels. A symptom
described as both occasional and constantly present. None of these is resolved by
picking one, and none is improved by splitting the difference.

Record both, mark the conflict, and where the difference might be a real
distinction rather than a contradiction, say that too — a constant sensation and
occasional episodes may be two true statements about one symptom. **A record that
smooths a conflict has made a decision nobody asked it to make.**

## One treatment, several outcomes

A treatment can work on one symptom and fail on another, in the same person at the
same time. In this household one medicine clearly reduced snoring frequency and
did not reduce throat phlegm.

Recorded as a single outcome, the finding becomes "it doesn't work much", and the
improvement vanishes. Recorded as two, both survive — and the second is evidence
the medicine *is* doing something, which is worth having.
