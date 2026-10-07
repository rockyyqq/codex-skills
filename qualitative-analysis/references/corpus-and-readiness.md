# Corpus and readiness

Nothing downstream is better than the material going in. This is what to check
before a single code is written.

## What can and cannot be analysed directly

| Material | How to handle it |
|---|---|
| `.txt`, `.md`, plain text pasted in chat | Read directly |
| `.docx` | Extract the text and check for Word comments; a script can do both without Office installed. See below |
| `.rtf`, `.odt`, `.htm`, `.epub`, `.pdf` | Convert to text first, and check the conversion before citing it |
| Audio, video, images | Not analysable from the file itself. Transcription is upstream of this skill |

A PDF conversion loses line breaks, hyphenation, page furniture and sometimes
column order. Read the converted text against the original before quoting from
it, and do not cite a page number the conversion cannot support.

If a source cannot be read, say so and stop. Do not analyse a summary of a
transcript as though it were the transcript, and do not reconstruct a document
you could not open.

## Coding held in Word comments

Plenty of studies are coded in Word rather than in a QDA package: the code sits
in a comment, the comment is anchored to the passage it applies to, and the
transcript text itself carries no visible code at all. A reader that extracts
only the document text will report that nothing is coded, and will be wrong.

Check for it before planning anything: if `word/comments.xml` exists in the
document, that is where the coding lives.

The anchor is worth more than the label. Each comment's anchored range gives the
verbatim quotation that the code was applied to, with its position, at no extra
cost - which is exactly the evidence a codebook needs. Extract both:

```
python scripts/extract_coded_segments.py --corpus transcripts \
  --doc P03:ACT03:ACT03_QC_Qi.docx --out segments.tsv --json
```

The script reports, per document, how many comments exist, how many are anchored,
how many anchors are byte-identical to the document text, how many span more
than one paragraph, and which code labels repeat. Four things to know about the
result:

- **A range must be closed.** `commentRangeEnd` closes it. If the extraction does
  not close ranges, every span silently runs on to the end of the document, and
  the spans look plausible while matching nothing. The script checks for
  unclosed anchors and fails loudly.
- **Anchors can cross paragraphs.** In one real corpus 17 of 343 did, usually
  where a comment covers an interviewer turn and the reply that follows. Spans
  are joined with `\n`, which is what the corpus reader produces too, so they
  still verify exactly. Do not quietly collapse the paragraph break.
- **The comment text is the coder's label, not a definition.** It is written for
  the coder's own recall. Treat it as the raw code list, not as the coding rule.
- **Some anchors sit on interviewer turns.** A comment can be anchored to the
  question rather than the answer. The screening rule decides those, and they
  should be visible in the screening log rather than dropped.
- **Anchors overlap, and the totals hide it.** A coder working in Word often
  anchors one comment to a whole answer and another to a passage inside it, or
  anchors the same passage twice under two different labels. Neither shows up in
  the counts: the same words simply get coded twice. The extraction reports both
  - identical anchor pairs and anchors nested inside a longer one - so they can
  be settled before counting. In one corpus of 343 anchors, 24 pairs overlapped,
  which moved the counted total by more than five per cent. What to do with them
  is in `claims-and-audit-trail.md`. The report lists every overlap, including
  anchors already logged as borderline; only the counted ones need a decision,
  because the borderline ones are outside the totals already.

## Inventory before analysis

Run `scripts/corpus_check.py inventory --corpus <dir>` first. It reports, per
file, the format, whether the text is readable, character and word counts,
duplicate content, and cloud-placeholder status.

What to look for:

- **Formats present.** Especially the ones that are not readable, which
  otherwise quietly vanish from the analysis.
- **Empty or near-empty documents.** A transcript of 200 characters is not a
  short interview, it is a failed export.
- **Duplicates.** The same content under two names double-counts the evidence.
- **Cloud placeholders.** In a OneDrive or Dropbox folder a file can exist with
  a name, size and timestamp while not being on disk. Reads fail with
  `PermissionError: [Errno 13]`, identically from Python, PowerShell and any
  application. It is easy to misread as a permissions or sandbox problem; it is
  neither, and raising the sandbox level does not fix it. Diagnose with
  `Get-ChildItem <file> | Select-Object Name, Length, Attributes` - `ReparsePoint`
  alongside `Archive` is the tell. Fix by copying the file to force hydration,
  then read the copy, confirm the copy is the same artifact, and say in the
  deliverable that a copy was used.
- **Filenames.** See below.

## Filenames are citations

Document names become source references in every deliverable, so a name that
only makes sense to the person who created it produces an unciteable claim.

Desirable: unique, descriptive, consistent, and meaningful without a private
legend - `P07 interview 2024-03-11.txt` rather than `int7b FINAL v2(1).txt`.

Source data is read-only, so **map, do not rename**. Build a small table from the
file's name to the participant or case it holds, keep that table with the
deliverable, and cite the original name exactly. An arbitrary rename breaks the
link to whatever else in the study refers to the file.

## Corpus structure and readability

- One interview or case per document where the study's practice allows it;
  boundaries that make analytic sense make every count downstream meaningful.
- Speaker labels consistent across the whole corpus, with the interviewer or
  moderator distinguished from participants, and participants distinguished from
  each other. Where labels are inconsistent, that is a finding - and it limits
  what can be said about who said what.
- Transcription symbols consistent and explained somewhere. Unexplained symbols
  are not readable as data by anyone else.
- Languages and any translations documented. Machine translations in particular
  must be marked as such before a quotation is analysed in the target language.
- Headers, footers, timestamps, page markers and export furniture not swamping
  the content.
- Absent documents listed explicitly. The missing interview is part of the
  study's description, not a gap to be quietly stepped over.

## The memo is the interface

The agent has no access to what happened in the room. Three kinds of memo carry
it, and each has a job:

- **Study memo** - research question and aims, object of study, context and
  boundaries, sample and sampling logic, data types and how they were collected,
  methodological framework, and the theory that actually guides interpretation.
  Theory too remote from an analytic decision is noise; note it as such rather
  than treating it as binding.
- **Document memo** - what the transcript does not contain: setting, who was
  present, when and why, whether it is a follow-up, what happened before.
- **Code memo** - *the coding rule*. Definition, inclusion criteria, exclusion
  criteria, the boundary against neighbouring codes, and a positive and a
  negative example. This is what makes coding reproducible by a second coder or
  a later pass.

When a memo is missing, ask for it, or record its absence as unknown and mark
the affected analysis as provisional. **Never infer the rule from the code's
name** - the name is a label, and a rule reconstructed after the fact cannot be
audited because the reader cannot tell what it screened out.

## Reading a supplied framework as data

A code tree handed over as a spreadsheet is a document with claims in it, and
its column headings are not always true. Parse it structurally before you
document it:

- **Read every level, not just the leaves.** Forward-fill the merged cells, then
  count the nodes at each level. In one real tree the column headed `Examples`
  held twelve code labels - a fourth level that the header denied - and one
  domain carried its leaves in the category column with no grandchild level at
  all. Both facts changed what the deliverable had to contain.
- **Derive the count from the structure.** The number of entries to document
  comes from the tree, not from the plan you wrote before reading it. If it
  differs, say why: an extra leaf, a duplicated label, a level that does not
  exist everywhere.
- **Decide what a node at an unusual level is, and say so.** A leaf sitting in
  the category column is still a code; give it an identifier that cannot be
  confused with a real category, and record the anomaly in the deliverable's
  issues log rather than silently normalising the tree.
- **Preserve labels exactly and list their defects.** Misspellings, broken
  apostrophes and near-duplicate labels are the team's to fix. Correcting them
  quietly breaks the link between the deliverable and the file everyone else is
  reading.
- **Check whether the framework already has a format.** Where an earlier
  codebook from the same group exists, its per-code fields and layout are the
  authority, not your preference. See `references/codebook-deliverable.md`.

## Readiness audit

Read-only. Inspect; change nothing. Judge each criterion against the study's own
design, method and stage - a missing code system is not a defect in a study that
has not started coding.

Assess four areas:

1. **Analytic orientation** - does the study memo give enough for methodologically
   sound collaboration: question, aims, object, boundaries, sample, data types,
   method? Is the theory connected to analytic decisions, or distanced from
   them? Is provisional thinking marked as provisional, or presented as settled?
2. **Corpus organisation and technical readability** - filenames, document
   boundaries, emptiness, duplication, conversion damage, speaker identification,
   transcription symbols, languages and translations, context available in memos.
3. **Cases, attributes and structure** - do cases represent the intended units of
   analysis, are documents linked to the right ones, are names and values
   consistent, are memos and attributes free of unexplained shorthand?
4. **Privacy and analytical risk** - direct identifiers in the material or the
   metadata, unclear separation between data, researcher interpretation and
   personal notes, and sample limitations the analysis must not overgeneralise
   past.

Report it as: overall assessment with a short rationale; strengths; a findings
table with columns `Priority`, `Area`, `Finding`, `Evidence`, `Why it matters`,
`Concrete action`; and an assessment-coverage section stating what was inspected,
whether sampling was used, and what could not be assessed.

Rules for the audit:

- Translate priority labels into the user's language, and use them sparingly.
- Do not recommend adding cases, attributes or codes merely for completeness.
  Every action must tie to the research design or a plausible analysis workflow.
- Do not treat an unassessed criterion as failed. When the evidence is mixed, say
  the evidence is mixed.
- This is not a legal, ethical or privacy audit. Report only what the material
  supports, and say that is what you are doing.

## Transcription boundary

Audio and video are transcribed before this skill can use them. Dedicated tools
do that job; do not attempt to analyse a recording directly.

Before treating a machine transcript as data, check a sample of it against the
recording, and record the tool and its settings in the study memo. Anything
quoted from a machine transcript in a publication is a claim about the
transcription as well as about the participant.

## Attribution

The readiness criteria above are adapted from QualCoder 4.0's project
AI-readiness check (Curtain, Dröge, Missaghieh--Poncet & Salomón, QualCoder 4.0,
LGPLv3), retrieved 2026-09-24, and restated for a corpus held as ordinary files.
Citing the source is appropriate when the audit itself is delivered to a
reviewer.
