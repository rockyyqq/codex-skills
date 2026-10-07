# Claims and audit trail

The analysis is half the deliverable. This is the half that decides whether
anyone can check it.

## The claim ladder

Every sentence that makes a claim sits on one rung, and the rung is visible to
the reader.

| Rung | Test | Grammar |
|---|---|---|
| **Observation** | A participant said or did this; the quotation proves it | "Participants described X" / "P07 said ..." |
| **Interpretation** | This is the reading you take from those observations | "This suggests X", with the observations that support it |
| **Hypothesis** | A pattern you expect to hold beyond this material | "We expect X outside this sample" - and it says so |

The common failure is an interpretation wearing an observation's grammar:
"Caregivers avoided the training" when what the material holds is three
caregivers describing something that could be read that way. The fix is not
hedging language spread over the whole report; it is putting each claim on the
right rung and showing the evidence under it.

A claim with no quotation and no location is a hypothesis by default. Either
find the evidence or label the rung.

## Source references and locations

A citation the reader cannot check is not a citation. Give, for each quotation:
the document name exactly as the file is named, a location within it (character
offset in the extracted text, line number where the text file has lines, or the
segment identifier), and the participant or case where the material supports
one.

Page numbers from a converted PDF are unreliable; a location from the conversion
is honest, a page number that may not exist is not. Where a location cannot be
given, say so rather than inventing one.

## Exemplars by reference, not by retyping

The most reliable way to keep a deliverable's quotations faithful is to never
type them. Keep one register of every segment or quotation, give each row an
identifier, and have whatever builds the deliverable name the identifier and
inject the text from the register:

```python
entry["typical_exemplar"] = exemplars["ACT11-0069"]["span"]   # injected, not typed
```

That one decision removed an entire class of error from a real codebook build:
a quotation could not drift from the transcript because it was never
transcribed twice. It also makes revision cheap - re-run the register check and
the deliverable changes with it.

The corollary: when an exemplar is chosen, record *why* it was chosen (a clear
case, a boundary case, a disconfirming one) and who it belongs to, so the choice
can be reviewed and not just the text.

## The quote register

The register is the audit trail for quotation. One row per quotation that
appears anywhere in the deliverable, as a TSV with columns:

`quote_id`, `quote`, `source_document`, `location`, `status`

Build it in two steps:

```
python scripts/corpus_check.py extract --deliverable findings.md --out quotes.tsv
python scripts/corpus_check.py verify --register quotes.tsv --corpus transcripts
```

`extract` pulls candidate quotations out of the report - Markdown blockquotes
and double-quoted spans - and leaves `source_document` and `location` for you to
fill in. `verify` then checks each row against the corpus and reports one of:

- **exact** - found byte-identically in the named file. The only full pass. The
  output shows `file @offset`, the character offset in the text as read.
- **whitespace** - matches only after whitespace normalisation. Report it as a
  weaker result and look at why: usually the quotation was re-wrapped, or the
  extractor turned a paragraph break into a space. A quotation that only matches
  this way must not be presented as verbatim. The offset is marked `~` because it
  refers to the normalised text, not to the file.
- **masked** - the row is logged as masked (see below) and each unmasked fragment
  was found in order.
- **fail** - not found. Fix the quotation or remove the claim.

Newlines inside a quotation are stored in the register as the two characters
`\n`, and unescaped on verification; that escape is the only transformation the
tool makes to the quotation itself. Line endings in the *source* are translated
to `\n` on read: CRLF is an artifact of the machine that wrote the file, not part
of what the participant said, and comparing across it would report false
mismatches. Nothing else is normalised - spacing, punctuation and encoding are
compared as they are.

**Escape once, unescape once.** A field read back out of the register is already
escaped. Escaping it again turns every newline into a literal backslash and `n`,
which is invisible in print and makes exact matches fail: in one run 17 correct
quotations were reported as failures this way. When a script verifies a register
in memory, pass the field through unchanged and let the checker do the single
unescape. If the quotations are already sitting in a script rather than a file,
import the shipped checker rather than writing a second comparison:

```python
sys.path.insert(0, str(SKILL_SCRIPTS))          # this skill's scripts/
import corpus_check
status = corpus_check.check_row(row, index, files, all_text)
```

Never edit a quotation to make it pass. If the source is genuinely damaged,
report the damage and quote the damaged text, because a quotation that has been
silently repaired is a claim about a document that does not exist.

Name the source document as the file is named. `verify` resolves an exact
relative path, a filename, a filename without its extension, or a unique prefix,
and prints the file it matched. An ambiguous prefix - `P0` against a corpus of
`P01`, `P02`, `P03` - is reported as `ambiguous-source` rather than guessed at,
because a quotation checked against the wrong interview is worse than one that
failed loudly.

The run also lists corpus documents that no row cites, and documents it could not
read. Both lists belong in the deliverable's coverage statement: an uncited
document may be legitimately out of scope, but it has to be accounted for.

## Masking, when confidentiality and fidelity collide

If a quotation that the analysis needs contains a direct identifier, the
identifier comes out and the row is logged as masked:

- replace only the identifying span, with square brackets: `[name]`,
  `[hospital]`, `[date]`;
- every unmasked fragment must still be byte-identical and in its original
  order;
- the register keeps the unmasked location, so a reader with legitimate access to
  the material can check the quotation in full.

Masking is the only permitted alteration to a quotation, and it is recorded.
Note the count of masked quotations in the deliverable, or the reader cannot
tell how much of the evidence they are seeing in part.

## Coverage and counts

**Say what is being counted.** In comment-coded corpora the anchors, the counted
codings and the evidence are three different numbers, and a report that says
"N segments" without saying which one is unreadable:

- **anchors** - one per comment. This is the raw material.
- **counted codings** - what the analysis actually rests on.
- **borderline** - plausible, but the anchor lacks the evidence the code needs.
  Logged, not counted.
- **nested facets** - an anchor sitting inside a longer anchor that carries the
  same code. The passage is counted once; the inner anchor is kept as a facet so
  no label is lost.
- **duplicates** - an anchor repeated exactly. Counted once, with the pair named.
- **overlapping codings** - two *different* codes on overlapping text. Both are
  real readings and both are counted; flag the pair so a reader knows the words
  are shared.

Never silently drop an anchor: the workbook carries every one, with its decision
and the pointer to the anchor it nests in, so the collapse can be reviewed and
reversed.

**Re-fit after every change to the frame.** Merging, splitting, renaming or
rewriting a definition invalidates the assumption that the existing assignments
still hold. Re-read every coding against the new text and record what moved.
The yield is usually small - one genuine misfit in 326 codings in one run - but
it is not zero, and the pass is also what proves the frame still carries the
material.

Report both counts, always:

- **segments** - how many coded passages support the claim;
- **cases** - how many participants or documents those segments come from.

Twenty segments from two participants out of thirty is a claim about those two
people, and it must read that way. A code resting on one case is a candidate
dimension, labelled as one in the deliverable and in the codebook.

The denominator belongs next to the numerator: how many documents or cases the
corpus holds, and how many each code reaches. State explicitly who is not
represented - and remember that an absent case is not evidence of absence. The
participants who never mentioned something are usually the least visible part of
a corpus and the easiest to over-read.

Account for every document in the corpus: coded, screened out with a reason, or
declared out of scope. A document that appears nowhere is indistinguishable from
one that was never opened.

Two coverage findings are easy to hide and are worth stating explicitly:

- **A code with no material.** A framework supplied by the team usually contains
  codes the interviews never reach. Report them as `no material in this pass`,
  with that wording, rather than stretching a neighbouring segment into them to
  fill the codebook. An empty code is a finding about the material or about the
  frame, and both readings are useful.
- **Residual codes.** A code called `Others`, `Miscellaneous` or similar cannot
  be defined positively. Define it by what it does **not** hold, keep a count,
  and treat a large residue as evidence that the frame is missing a distinction
  rather than that the material is miscellaneous.

When a segment fits nothing, three responses are available and they are not
interchangeable: assign it to the nearest code and say so in the reason; log it
as borderline when the fit is partial; log it as a gap when no code reaches it.
What must not happen is a quiet accumulation of hard cases inside a broad code.
Group the near-misses into named clusters with counts - one real run surfaced
three such clusters, each recurring across participants, none of which had a
code of its own - and report them alongside the gaps.

## Provenance of the source

Study data is read-only, and it is worth demonstrating rather than asserting:

- record a short manifest of the source files with their byte sizes and
  SHA-256 hashes, and state that checks ran against hydrated copies which are
  byte-identical to the originals;
- confirm at the end that the source files' modification times are unchanged;
- keep any working copies outside the deliverable folder, so a folder of
  restricted transcripts is never duplicated into the output, and say in the
  deliverable where the verification ran.

When the study folder is outside the writable area, writing the deliverables
into it needs one explicit approval - ask for it once, name the folder, and
leave the originals untouched.

## Revision log against a prior artifact

When a pass revises an earlier one, the log records each change with four things:
what it was before, what it is now, what type of change (newly included, newly
excluded, reclassified, moved), and why.

A revision log is a factual claim about the previous file, and it is checkable:

1. Open the previous deliverable.
2. Rebuild its decisions from its own log, not from the narrative.
3. Assert every logged "before" value matches it.
4. Assert the current state matches the logged "after" value.
5. **Assert there is no change absent from the log.** This is the step that
   catches real errors, because an undocumented change is invisible otherwise.
6. Assert which items left the coded set, and that each one is logged.

Steps 3 and 4 prove the log is not wrong; step 5 proves it is not incomplete.
If the previous file cannot be opened, say so plainly and verify against a copy
you can demonstrate is the same artifact. Never narrate what the old version
said from memory and present it as verified.

When the earlier artifact is a workbook, `qualitative-codebook-qc` owns this
discipline in its own form, including its verification script. Use its gates for
the workbook rather than re-deriving them here.

## Confidentiality sweep

Before delivery, check the deliverable, not just the transcripts:

- no direct identifiers - names, initials, exact dates, institutions, addresses,
  record numbers, rare job titles;
- pseudonyms used consistently, and the mapping table kept out of the
  deliverable;
- combinations of attributes treated as identifying. In a small sample, a
  participant may be identifiable from a role, a condition and a location
  together even with no name in sight. If a quotation is safe alone but the
  surrounding description is not, change the description;
- the material's sensitivity label respected as binding - a file marked
  restricted is restricted in what may be printed from it.

This is a hygiene check, not a data-protection review: a study with real
governance obligations needs the appropriate approval, and saying that is
sometimes the most useful thing in the report.

## What verification cannot do

The gates prove the deliverable is internally consistent and faithful to the
source text. They cannot prove the coding is right, that the codes are the best
reading of the material, that saturation has been reached, or that the sample
supports the generalisation. Say which is which when reporting: "all gates pass"
is not "the analysis is correct", and conflating the two is how a verification
pass gives false comfort.
