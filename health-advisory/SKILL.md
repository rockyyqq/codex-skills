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
   `references/urgency.md` — including its known gap, which is that the verified
   source covers children only.
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
- `scripts/validate_record.ps1` validates the stored record against the schema
  and **fails closed on any unknown key**. A misspelled key makes a real item
  invisible — and then the review reports a false all-clear. Run it after every
  write to the vault.
- `scripts/record_view.ps1` prints a derived view: structure, flags and gaps,
  never clinical values. **Analyse from this, not from memory of having written
  the record.** Recalling what you wrote is not reading the artifact back, and a
  dropped or renamed key would go unnoticed.
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
detail or a place is rejected, with what to rewrite. Search the clinical term.

## Before delivering a report

Run `scripts/validate_report.py`. It rejects identifiers and unsourced claims.
Run `scripts/check_sources.py` too: it fails the whole report on any source past
its review date.

## References

Read only what the task needs.

- `references/boundary-and-privacy.md` — the prohibitions and the privacy protocol
- `references/urgency.json` and `references/urgency.md` — the gate, and why it is data
- `references/routing.json` — question class to process
- `references/source-ladder.md` — which source class answers which question
- `references/record-fields.md` — the record schema and its five rules
- `references/singapore-sources.json` — verified sources with review dates

## What this skill is not

Not a research-evidence appraiser — use `research`. Not a poster or deck tool —
use `poster-review`. Not a substitute for a clinician, ever.
