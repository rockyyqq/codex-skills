# Specialty lenses

A lens turns a question the record cannot answer into an appointment that can.
It gives three things and refuses a fourth:

- **who owns the question** — which specialty can answer it at all
- **what to bring** — assembled from the record, not remembered on the day
- **what to ask** — the questions, phrased as questions
- and it never answers them

The lens exists because the household's own file holds detail that a short
appointment will not otherwise recover, and because a question carried to the
wrong specialty wastes the appointment rather than the question.

## The boundary inside a lens

A lens is preparation, so the prohibitions in `boundary-and-privacy.md` apply
unchanged, and one of them bites hardest here:

- No diagnosis, no naming a likely condition, no dose, no prognosis, no
  treatment change, and no answer to whether an insurer will pay.
- **May escalate. Never de-escalate.** A lens never says a finding is
  unimportant, and it never talks a household out of an appointment.
- **Naming a specialty is not a referral.** The lens says who owns a question.
  Whether and how to refer belongs to the treating clinician, and the clinician
  outranks this file. Where a lens and a clinician disagree, the disagreement
  becomes a question and never a correction.
- The emergency gate runs first, before any lens. A pack never restates the red
  flags; it points at `urgency.json`, so the gate stays in one place.

## Applying a lens

1. **Read the artifact first** — `validate_record.ps1`, `record_view.ps1`,
   `due_report.ps1`, `check_sources.py`. A lens applied from memory is a lens
   applied to a record nobody checked.
2. **Select the lenses the record drives.** A lens fires on a recorded signal —
   a condition, a test result, a planned procedure, a documented attribution —
   and never on a symptom nobody has reported. A textbook list of specialties
   is deliberately not used: the record decides, the same way the review decides
   what is due.
3. **Assemble the pack** in the shape below, per person, one block per lens.
4. **Write it to `reports/<date>-consultation-pack.md`.**
5. **Validate it** — `validate_report.py` against the `pack` kind, and
   `check_sources.py` too.

## The pack's shape

Per person, per lens, three blocks. The three marker strings are the ones
`validate_report.py` looks for, so they are part of the contract:

### Who to see

The specialty that owns the question, and the specific clinician where the
record already names one, with the reason this lens fired.

### What to bring

Assembled from the record, each item with its date and its source class:

- the timeline, dated
- medications as recorded, including `dose_text` **as identification and not as
  an instruction**, and each one's source — `label`, `pharmacy` or `memory`
- allergies with the reaction type, never just the substance
- relevant past history
- what has been tried and what happened, in the informant's own words
- the plan from last time and whether it happened
- the documents, named, and anything still to fetch

### Questions to ask

The questions only that specialty can answer, as questions. No differential goes
into the pack: a list of possibilities anchors the consultation and wastes the
appointment.

## The lenses

Each lens names the source IDs from `sources.json` that answer its terminology
and guideline side. **The dates live in the ledger, not here** — one copy of a
review date is one place for it to rot.

### GP — the record-holder and the schedule

**Fires on:** a screening or vaccination entry with no date or no sourced
interval; a member whose screening and vaccination sections are unrecorded; a
record whose age band is missing, because a schedule runs on age.

**Questions it carries:** what screening schedule applies at this age band, given
what the record shows; what the entries recorded as "not done" mean for that
schedule; which undated entries need dating; where a recorded value came from
when its source is not stated.

**Sources:** `SG-HEALTHIER-SG-SCREENING`, `SG-MOH-CPG`.

### Allergy

**Fires on:** a test result whose grade is not recorded; a household with nasal
symptoms in more than one member; an allergy section that is unrecorded, or that
rests on a form wording limited to one class of allergen; a statement in the
record that testing has never been done.

**Questions it carries:** what the existing test result showed, in its own words;
whether testing is indicated and what it would change; whether several members'
nasal findings should be assessed together or separately.

**Sources:** `SG-HEALTHHUB-CONDITIONS`, `INT-MEDLINEPLUS`, `INT-NICE-GUIDANCE`.

### Dermatology

**Fires on:** a skin condition whose label differs between the household's word
and a summary's word; a skin condition reported by a proxy with no clinical
confirmation; a recorded morphology with no biopsy, blood test or allergy
testing; a second skin condition in the same household with a contrasting
distribution.

**Questions it carries:** which label is the clinician's own wording; whether two
descriptions are one condition or two; what the earlier treatment courses
changed; whether the absence of testing so far is deliberate or pending.

**Sources:** `SG-HEALTHHUB-CONDITIONS`, `INT-MEDLINEPLUS`, `INT-NICE-GUIDANCE`.

### ENT, and sleep where breathing at night is involved

**Fires on:** nasal symptoms recorded alongside throat symptoms; snoring observed
by someone other than the person; a night-time symptom with a next-morning
consequence; an attribution already recorded by a doctor that names the nose.

**Questions it carries:** whether the nose and throat findings are one problem or
two; which of two conflicting descriptions the clinician wants recorded; what
would be worth measuring at home and under what conditions, where the current
record has no arm, position or rest before the reading.

**Sources:** `SG-HEALTHHUB-CONDITIONS`, `INT-NICE-GUIDANCE`.

### Gastroenterology

**Fires on:** an acid-suppression medication whose stated reason is a doctor's
attribution; a symptom a doctor has attributed to reflux; a long unnamed period
of medication in the record.

**Questions it carries:** what the attribution was based on, and which test; how
one medicine producing two different outcomes should be read; what from an
unnamed period is worth recovering.

**Sources:** `SG-MOH-CPG`, `INT-NICE-GUIDANCE`.

### Breast imaging review

**Fires on:** a screening finding recorded as "not significant" from recollection
because the report is not to hand; a screening entry with year precision only.

**Questions it carries:** what the report said in its own words; what its
findings mean for the schedule; what to fetch so the entry stops being
recollection.

**Sources:** `SG-HEALTHIER-SG-SCREENING`, `SG-MOH-CPG`.

### Paediatric day surgery

**Fires on:** a booked procedure with an outstanding pre-operative step; a
pre-operative rule with a time window attached; a proxy-recorded history
standing behind a consent form.

**Questions it carries:** what the window means in practice for this household;
which number to call outside the clinic's stated hours, where the sheet gives
none; whether a history nobody assessed — splinting, for example — matters to
the operation; whether the recorded weight is still the one used on the day.

**Sources:** `SG-MOH-CPG`, `SG-HEALTHHUB-CHILD-EMERGENCY`.

## What a lens must not become

- **Not a differential.** A list of possibilities anchors the appointment.
- **Not a referral letter.** It names an owner and carries questions.
- **Not an evidence review.** A lens gathers what is known and what to ask. If
  the question is whether something works, that is the `research` skill and the
  evidence route in the skill body.
- **Not a substitute for the emergency gate.** The gate runs first, always.
