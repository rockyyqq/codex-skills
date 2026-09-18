# The emergency gate

This runs before anything else, for every question class. It is not a branch in
the routing; it is the first step regardless of the question.

If the question describes a presentation listed in `urgency.json`, the first line
of the answer is that entry's action. The explanation comes after, and it may be
short.

## Why it is data

The gate is the one rule that cannot be approximately right. Keeping it in
`urgency.json` means it can be read, diffed, dated and corrected. Keeping it in
prose would mean re-deriving it every time.

## Why every entry cites a source

An emergency list invented from general knowledge is exactly the artefact this
skill exists to avoid. `test_urgency.py` fails on any entry whose `source_id` is
not in `sources.json`, and on any whose `review_by` has passed.

## The asymmetry

No entry may de-escalate. A test enforces this by failing on phrases like
"no need" or "not serious". Over-referring wastes an appointment;
under-referring can kill.

## Known gap: this covers children only

The single verified source is HealthHub's *Emergency Care (Children)*, so every
entry here is a paediatric presentation. **Adult red flags are not covered yet** —
chest pain, stroke signs, severe bleeding, suicidal ideation and overdose in an
adult have no entry in this file.

That gap is deliberate rather than overlooked: no Singapore source for adult
emergency presentations has been verified. Adding entries without a source would
be inventing provenance, which is the one thing this file must not do.

To close it, verify a source that states adult emergency presentations, add it to
`sources.json` with `"class": "emergency-guidance"`, and add one entry
per presentation it names.
