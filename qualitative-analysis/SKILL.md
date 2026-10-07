---
name: qualitative-analysis
description: Run the analytic layer of a qualitative study over its own transcripts and study documents - auditing whether the corpus is ready for machine-assisted work, writing code definitions and memos that function as coding rules, coding with the rule frozen before the codes, comparing overlapping codes, hunting the disconfirming case, judging saturation, and delivering findings in which every claim traces to a verbatim quotation. Use for "analyse these interviews", "what themes are in this data", "code these transcripts", "is this code saturated", "does my codebook hold up", and for checking a qualitative analysis before it is written up. Not for building or quality-checking a multi-level code hierarchy held in a spreadsheet (use qualitative-codebook-qc), not for finding or appraising literature (use research), and not for peer-reviewing a manuscript as a journal reviewer (use peer-review).
---

# Qualitative analysis

The analytic layer over a study's own material: transcripts, field notes, open
responses, and the memos that give the codes their meaning. It works on files as
they are, and it does not require, open, or write a QDA application's project
file.

The value here is not producing plausible themes. It is producing claims a
reviewer can trace back to the data, and keeping what the data says separate
from what you concluded about it.

## Non-negotiables

**Source data is read-only.** Never edit a transcript, a codebook, or a study
database. Deliver new artifacts alongside the source. A later pass that changes
an earlier one is a new version with a logged change, not an edit in place.

**The rule comes before the codes.** State the inclusion, exclusion and boundary
rules and show them before assigning a single code. A framework assembled first
and justified afterwards cannot be audited - the reader cannot tell which
material was never considered.

**Label the rung of every claim.** An *observation* is what a participant said.
An *interpretation* is what you read it as. A *hypothesis* is a pattern you
expect to hold beyond this material. Most inflated qualitative claims are
interpretations written in the grammar of observations. Label them in the
deliverable, not only in conversation.

**Every claim carries a quotation and a location.** A claim with no verbatim
quotation and no findable source position is a hypothesis. Either find the
evidence or relabel the claim.

**Quotes are byte-identical or they are nothing.** Do not paraphrase into a
quotation, tidy punctuation, translate silently, or repair encoding. Check it in
code - `scripts/corpus_check.py verify` - not by eye. **Never retype a quotation
into a deliverable**: give every segment an identifier in the register and have
whatever builds the deliverable inject the text, so a quotation cannot drift
from its source because it was never written twice.

**Never pool two constructs in one count.** Reflective engagement with an
intervention is not application of it; perceived applicability is not enactment;
intention is not behaviour. Carry the distinction into the count, or the theme
will overstate itself in the summary.

**Code the disconfirming case.** Actively look for the participant who says the
content does not apply, the change that happened without the intervention, the
case that breaks the boundary. A theme reporting only confirming evidence has
discarded its most useful output.

**One case is not a finding.** A pattern in a single interview is a candidate
dimension to test, and it must be labelled that way in the deliverable. Report
case counts next to segment counts: 20 segments across 2 of 30 participants is a
different claim from 20 segments across 18.

**Participants are not the audience.** Use the study's own pseudonyms, keep
direct identifiers out of every deliverable, and quote only what consent and the
material's sensitivity label allow. Corpora labelled "Restricted; Sensitive
High" carry that label for a reason, and it binds what you may print.

## Workflow

Work in this order; the order is the safeguard.

1. **Locate the material and audit it.** Inventory the corpus before analysing
   it: which formats, what is missing, what cannot be read as text, what exists
   only as a cloud placeholder, and whether the coding lives in the transcript
   text or in Word comments. See `references/corpus-and-readiness.md`.
2. **Freeze the analytic frame.** The question (how or what - never *why*,
   *affect*, *influence*, *impact*), the unit of analysis, and the screening
   rule. All three go into the deliverable before any coding.
3. **Write each code's definition and memo.** The memo *is* the coding rule: it
   is what lets a second coder, or a later pass, apply the code the same way. A
   code with no definition is a label, not a code.
4. **Code, with a quotation on every coding and a memo on every code.**
5. **Run the analytic moves the question needs** - choose from the table below,
   not all of them.
6. **Attack the result.** Disconfirming case, code boundary, saturation
   judgement, blind spots.
7. **Re-fit after any change to the frame.** Merging, splitting, renaming or
   rewriting a definition invalidates the old assignments. Re-read every coding
   against the new text, record what moved, and state the seam rule where two
   codes meet.
8. **Verify, then deliver.** Run the gates at the end of this file.

## Analytic moves

`references/analytic-moves.md` carries the method, output shape, failure mode
and source for each.

| Move | Answers |
|---|---|
| Thematic summary | What is in this material, on this code? |
| Themes generation | What are the recurring themes across the whole corpus? |
| Expected versus unexpected | What is surprising, against what this phenomenon usually looks like? |
| Differences between cases | How do cases or documents differ - and is there a real difference? |
| Code profile and blind spots | What does this lens reveal, and what does it hide? |
| Code comparison | Where is the boundary between two overlapping codes, and which segments are miscoded? |
| Saturation | Does this material already hold the relevant variants of the phenomenon? |
| Reconstructive interpretation | How do participants handle a topic, beyond what they say about it? |

Two of these are borrowed methods and must be credited when used: themes
generation (Friese 2024) and reconstructive interpretation (Lieder & Schäffer
2024). Attribution is in the reference.

Every move produces *claims*, not prose. A move that returns only a summary of
the material has not done its job.

## Working with qualitative-codebook-qc

That skill owns the spreadsheet layer; this one owns the material layer. Hand
off rather than rebuild.

- **Use `qualitative-codebook-qc`** when the task is to build, extend or
  quality-check a multi-level code hierarchy held in a workbook, to screen a flat
  code list through an analytic lens, or to produce a screening log, a construct
  flag, a revision log and the XLSX mechanics around them. Its gates and its
  `scripts/check_coding.py` are the authority there - do not re-implement them
  here.
- **Use this skill** for anything upstream or downstream of the workbook:
  reading transcripts, auditing corpus readiness, writing code definitions,
  producing analytic claims, judging saturation, and testing whether a set of
  codes actually describes the material.
- **When both apply** - a full codebook review, say - run this skill first to
  freeze the rule and settle the leaf codes against the material, then hand the
  frozen rule and the code list to `qualitative-codebook-qc` for the hierarchy
  and its audit trail. Never let the workbook's structure decide the rule.

## Deliverables

Produce artifacts, not analysis-in-chat, and say which ones you produced and
where they are.

- **Readiness audit** - read-only. Whether the corpus can carry machine-assisted
  analysis, what is missing, what cannot be assessed.
- **Codebook** - per code: mnemonic, short and detailed description, inclusion
  and exclusion criteria, a typical and an atypical exemplar with locations, and
  the case and segment counts behind it. Where the group already has a codebook,
  its fields and layout are the authority. See
  `references/codebook-deliverable.md`.
- **Analytic report** - the claims, each labelled with its rung and carrying its
  quotation and location, with disconfirming evidence in its own section.
- **Quote register** - a TSV of every quotation used, with source document and
  location, machine-verified against the corpus.

Leave the source files untouched. Deliver alongside, never over.

## Verification gates

Run these; do not assert them. `scripts/corpus_check.py` implements the first
three.

*Evidence and quotation*

- Every quotation in the deliverable appears in the register, and every register
  row verifies against the corpus file it names.
- No quotation reaches a deliverable that fails verification - including one
  that matches only after whitespace normalisation, which is reported as a
  weaker result, never silently passed.
- A quotation masked for confidentiality is logged as masked with its fragments
  verified in order; masking is the only permitted alteration, and it is
  recorded.

*Corpus and counts*

- Every corpus document is accounted for: coded, screened out with a reason, or
  declared out of scope.
- Anchors that overlap are settled rather than left in the totals: an anchor
  repeated exactly is counted once, an anchor nested inside a longer one with
  the same code becomes a facet, and two different codes on overlapping text are
  both kept and flagged.
- Counts are stated as what they are - anchors, counted codings, borderline,
  facets, duplicates, overlapping - and every anchor appears in the workbook
  with its decision.

*Codes, claims and revision*

- Every exemplar is a counted coding of the code it illustrates.
- No identifier anywhere in the deliverable points at a code that is not in the
  frame.
- Every code has a definition, a memo and at least one quotation, and every code
  named in the report appears in the codebook.
- Every code in the frame carries a status, including `no material in this pass`.
  An empty code is reported as a finding, never filled by stretching a
  neighbouring segment into it.
- The number of documented codes is derived from the source structure, not from
  the plan, and any difference is explained.
- Every claim carries its rung and its location, and no unlabelled
  interpretation appears in the grammar of an observation.
- Case counts and segment counts are reported together; any code resting on a
  single case is marked as a candidate dimension.
- Disconfirming evidence has its own section, or the deliverable states what was
  searched and that none was found.
- A pass that revises an earlier one has its revision log verified against the
  previous *file*, not against memory.

## What verification cannot do

These gates prove the deliverable is internally consistent and faithful to the
source text. They cannot prove the coding is right, that the codes are the best
reading of the material, or that saturation has been reached - those are reading
judgements. Say which is which when reporting: "all gates pass" is not "the
analysis is correct", and conflating the two is how a verification pass gives
false comfort.

## References

- `references/corpus-and-readiness.md` - corpus inventory and format limits, the
  readiness audit and its report format, the memo as the interface to the data,
  and the transcription boundary.
- `references/analytic-moves.md` - the eight moves: method, when to use, output,
  failure mode, attribution.
- `references/claims-and-audit-trail.md` - the claim ladder, source references
  and locations, the quote register, coverage and counts, masking, revision logs
  against a prior artifact, and the handoff boundary to the workbook skill.
- `references/codebook-deliverable.md` - the codebook document: the fields each
  entry carries, the front section, the appendices that make it checkable, and
  how to build and render it.

## Scripts

`scripts/corpus_check.py`:

```
python scripts/corpus_check.py inventory --corpus transcripts
python scripts/corpus_check.py extract --deliverable findings.md --out quotes.tsv
python scripts/corpus_check.py verify --register quotes.tsv --corpus transcripts
```

Standard library only. `inventory` reports formats, read failures, duplicates and
cloud placeholders; `extract` pulls candidate quotations out of a delivered
report into a register; `verify` checks the register against the corpus and
exits non-zero on any failure.

`extract` recognises quotations written as Markdown blockquotes and as
double-quoted spans. Write quotations in a delivered report that way, or they
will not enter the register and so will never be checked.

`scripts/extract_coded_segments.py` recovers coding held in Word comments: one
row per anchored comment, with the code label, the verbatim anchored span, its
document and its position. Use it when `word/comments.xml` is present in a
transcript; it reports unclosed anchors, empty anchors, cross-paragraph anchors
and duplicate labels, and it writes spans in the escaping the register expects.

```
python scripts/extract_coded_segments.py --corpus transcripts \
  --doc P03:ACT03:ACT03_QC_Qi.docx --out segments.tsv --json
```
