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
