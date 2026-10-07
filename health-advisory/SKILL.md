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

A **consultation pack** is the bring-to-clinician output written down. When the
household asks what to bring to an appointment, or the record raises a question
no household member can answer, read `references/specialty-lenses.md` and write
the pack to `reports/<date>-consultation-pack.md`. A lens names which specialty
owns a question; it is not a referral, and the questions leave as questions.

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
- `scripts/record_view.ps1` prints a derived view: structure, counts, flags and
  gaps. Fields that can hold prose, such as a severity grade or a pre-operative
  rule, report only whether they are **present**; a boolean reports true or
  false. It printed those sentences verbatim until 2026-09-18 while its own
  header claimed otherwise, which is the exact defect it exists to prevent.
  **Analyse from this, not from memory of having written the record.** Recalling
  what you wrote is not reading the artifact back, and a dropped or renamed key
  would go unnoticed. When a task genuinely needs the text, such as writing a
  family analysis, read the record deliberately for it and put the result in a
  report file rather than in the conversation.
- `scripts/record_gaps.ps1` holds the single definition of what counts as a gap.
  Both the view and the review use it, because two implementations of one rule
  drift — and they did, disagreeing about whether a missing allergy list was a gap.
- **A family analysis has a fixed structure.** When the household asks for one,
  read `references/analysis-template.md` and follow its nine sections in order.
  The informant column is the part easiest to drop and the part that matters
  most: gap counts track who was interviewed, not who is unwell.
- **Scripts print counts and IDs, never record content.** Everything read into a
  conversation is written to the local session store in plaintext and persists.
  This is the load-bearing privacy rule; encryption does not substitute for it.
- **Provenance is asked for, never inferred from appearance.** A clinic letter, a
  screenshot, a prescription photo and an AI-generated summary all *look* like
  documents, and they carry different weight. A summary of the household's own
  account is the household's account at one remove — it can contain detail no
  clinician said, and it can silently change a label. **Establish what something
  is before recording it as sourced**, and ask rather than assume: the price of
  getting this wrong is a record that overstates its own evidence.
- **A record's gaps track who was asked, not who is unwell.** In this household
  the two members interviewed directly had 2 and 4 gaps; the two answered for by
  a proxy had 5 and 8. The member with the most gaps held the only clinically
  tested finding in the household. **Never read detail as severity** — read it as
  evidence of who was interviewed, and ask the people nobody has asked.
- `scripts/due_report.ps1` writes the periodic review to a file and prints counts.
  It reports **OK**, **DUE** or **CANNOT JUDGE** — the third is not a pass.
- Facts and assumption-dependent items never merge. A due screening is a fact; a
  family-history criterion met is a question for a clinician.
- The review computes a **next review date** from the earliest sourced interval,
  rather than pinning it to a calendar month, and the report states a
  **retention**. `validate_report.py` requires that retention for every kind.
- The review has exactly one cross-check: a **word match** between a recorded
  allergy and a recorded medication. It is deliberately literal, so a match is
  reported as a fact and nothing more. It is not an interaction check (that is a
  label question), and finding no match clears nothing. A placeholder such as
  "no known drug allergies" reduces to no substance and is never matched.
- A clean review says "these checks are up to date" and **never** "you are
  healthy".

## The backup

DPAPI is bound to this Windows account, so a DPAPI-encrypted file will not open
after a profile rebuild or on another machine — which is exactly the situation a
backup exists for. `scripts/vault_backup.ps1` is the portable half: it decrypts
the record in memory and re-encrypts it under a passphrase
(PBKDF2-SHA256 → AES-256-GCM), so the container restores anywhere.

- `export` writes the container and then **decrypts it again and compares** before
  reporting success, so a backup is never declared good without a restore.
- `export` writes two companion files first and stops if either cannot be
  written: the optional passphrase copy, and `RESTORE-HOWTO.txt` beside the
  container, which says what the file is, that restoring needs PowerShell 7, and
  what to type. `-passnote "<text>"` records where the passphrase is kept.
- `verify` reports counts and writes nothing. `restore` refuses to overwrite a
  record that is already there unless `-Force` is given.
- The passphrase is typed at a prompt. It is never passed on the command line,
  never committed, and never written into a report or a chat. `-passfile <path>`
  optionally writes a local copy for the household, readable by the current user
  only — and that copy must not be the **only** copy, because it dies with the
  machine the backup is meant to survive. **If the passphrase is lost the backup
  is unrecoverable**; that is the trade for not needing this Windows account.
- The destination may be synced, since the design's working assumption is
  encrypt-then-sync. The vault itself is never synced: checked 2026-09-18, the
  vault sits on a Desktop that is not redirected into OneDrive.
- OneDrive's own version history is the rotation. Because that is a Microsoft-side
  feature, copy one container somewhere independent occasionally.

## Before any search leaves the machine

Run `scripts/build_query.py`. It refuses rather than sanitises: a question
containing a relationship, an age, a date of birth, an identifier, a contact
detail or a place is rejected, with what to rewrite. Search the clinical term.

## Before delivering a report

Run `scripts/validate_report.py`. It rejects identifiers and unsourced claims and
requires the report's kind, whether evidence, review or pack, to carry its own
blocks **and a retention statement**. A new report type adds a kind; it never
relaxes an existing kind's list. Run `scripts/check_sources.py` too: it fails the
whole report on any source past its review date.

## References

Read only what the task needs.

- `references/boundary-and-privacy.md` — the prohibitions and the privacy protocol
- `references/urgency.json` and `references/urgency.md` — the gate, and why it is data
- `references/routing.json` — question class to process
- `references/source-ladder.md` — which source class answers which question
- `references/record-fields.md` — the record schema and its five rules
- `references/writing-the-record.md` — the four traps that make a write fail quietly
- `references/analysis-template.md` — the nine-section structure for a family analysis, and what it excludes
- `references/specialty-lenses.md` — which specialty owns a question, what to bring, and what only they can answer
- `references/sources.json` — verified sources with review dates, local and international

## What this skill is not

Not a research-evidence appraiser — use `research`. Not a poster or deck tool —
use `poster-review`. Not a substitute for a clinician, ever.
