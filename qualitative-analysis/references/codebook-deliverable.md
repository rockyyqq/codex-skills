# The codebook deliverable

Read this when the thing being delivered is a codebook document rather than an
analysis report - typically a Word file that defines every code in the frame.

## Format is inherited, not invented

If the group already has a codebook from an earlier study, its per-code fields
and layout are the authority. Match them, including the terms it uses for each
field, and say in the front section that it follows that format. Where the frame
needs a field the earlier codebook does not have - a fourth level folded into a
parent, for instance - add it and record the addition in the issues log rather
than altering the shared shape.

## What each code entry carries

One heading per code, nested in the frame's own levels, then a two-column table:

| Field | Contents |
|---|---|
| Mnemonic | The short handle, unique across the codebook; a digit suffix if two labels collide |
| Short Description | One or two lines: what the code is for |
| Detailed Description | What it covers, including any labels folded in from a deeper level |
| Inclusion Criteria | The operational test for applying it, written from how the material actually landed |
| Exclusion Criteria | The neighbouring codes by identifier that must not absorb the same material |
| Typical Exemplar | A clear case, with its source |
| Atypical Exemplar | A boundary, unexpected or disconfirming case - or `None in this material` |

The exclusion row is what makes a codebook usable by a second coder: naming the
code that *would* have taken the segment is more informative than a prose
definition, and the confusable pairs are discoverable from the borderline calls
in the mapping, not from intuition.

Exemplars are injected from the register by identifier (see
`claims-and-audit-trail.md`), never typed. Each carries the participant, the
document, the anchor and the segment id. Where no atypical case exists, write
`None in this material` - a plausible-looking substitute destroys the value of
the row.

**Give a short exemplar its context.** A coded anchor is often a fragment -
"The pace is good", "I think it's hard" - which tells a reader nothing on its
own. Where the anchor is shorter than a sentence, quote the surrounding text
from the same passage instead, taken from the same contiguous source text so it
stays verbatim, and mark the coded anchor in bold inside it. Say in the source
line that context was added. Leave long anchors alone; they already stand up.
Verify the longer quotation byte-identically and check the anchor still sits at
the position recorded for it.

**"No exemplar" has to be earned.** Before writing it, search the coded material
for the code's own vocabulary, and record what you searched. Usually the answer
is one of three: the material exists but is filed under a neighbouring code
(name it); the code is a residual that nothing reaches; or the topic genuinely
never came up. Then say which, in the entry itself - a bare "none" reads as an
oversight, and a reader cannot tell it apart from a search that was never run.
Do the same for a missing atypical exemplar: check first whether the code has a
second coded segment at all, and say so when it does not.

**Quote the scope, not just the point.** When a code is bounded by time or
setting - "before the intervention", "since diagnosis", "at follow-up" - a short
quotation rarely shows which side of the boundary it sits on. Start the
quotation at the marker that establishes the scope and stop before the pivot
into the other side, even when that means quoting several hundred characters.
One real exemplar grew from 173 to 767 characters to open with "for the whole
year right..." and end before "But when I attended this course right...". Where
no marker exists inside the passage, say in the note how the scope is known -
which section of the interview it came from.

**Check that the exemplar is coded to the code it illustrates.** After merges
and re-filing this is easy to get wrong, and a mismatch is invisible on the
page. Assert it in the build: the exemplar's primary code equals the entry's
code, and it is a counted coding rather than a borderline or nested row.

## Front section

Short, and it earns its place by making the document auditable:

- purpose, and that the codebook follows the earlier study's format;
- status, stated plainly: provisional or final, which documents are coded, which
  are not, and that no saturation is claimed;
- what it was built from, with the counts (documents, segments, participants);
- the analytic question, and where it came from - the study's own interview
  guide rather than a question invented for the document;
- how to use it: mnemonic plus criteria, and the note that exclusion criteria
  name the neighbouring codes;
- the rule fixed before coding: unit of analysis, inclusion, exclusion, boundary.

## Appendices that make it checkable

Four, each answering a question a reviewer will ask:

- **Coverage** - every code with its mnemonic, the participants behind it and its
  segment count, so an empty or single-segment code is visible at a glance.
- **Label and framework issues** - the source tree's defects preserved and
  listed: misspellings, broken apostrophes, a column heading that lies, uneven
  depth, near-synonym code pairs, residual codes, and recurring meanings that no
  code reaches.
- **Segments the frame does not reach** - the gaps, with their quotations and the
  reason each was logged rather than filed.
- **Verification** - what was checked and how many rows passed, plus the sentence
  that this proves fidelity and consistency, not that the coding is right.

## Building it

- **Generate the document from data.** Keep per-code text in one content module
  (keyed by code id) and the quotations in the register; a builder assembles the
  document. Hand-editing the finished file makes the next revision a
  transcription exercise.
- **Take the code count from the framework file**, not from the plan, and let the
  builder fail if any code is missing its text.
- **Keep each table row unsplittable** (`w:cantSplit`) so a field never breaks
  across a page, and keep headings with what follows them.
- **Insert a real contents field and update it before exporting.** An unupdated
  field exports with stale or placeholder page numbers. Set page numbers in a
  footer.
- **Tell the builder to leave quotations alone.** Normalise punctuation in your
  own prose if house style requires it; never touch a quotation, a code label, or
  a mnemonic taken from the framework.

## Rendering and inspecting it

The render gate applies to a codebook exactly as to any other document: export
to PDF, rasterise every page, and look at every page before delivering.
If a general document skill is available it owns the docx workflow, including
its renderer; use it, and treat what follows as the fallback for the case where
its renderer is not installed.

Where LibreOffice is unavailable - the usual case on a Windows machine with
Office installed - Word can do the export headlessly through COM, invisibly, and
Poppler can rasterise the result:

```powershell
$word = New-Object -ComObject Word.Application
$word.Visible = $false; $word.DisplayAlerts = 0
$doc = $word.Documents.Open($docx, $false, $false)
$doc.Fields.Update() | Out-Null
foreach ($toc in $doc.TablesOfContents) { $toc.Update() | Out-Null }
$doc.Save(); $doc.ExportAsFixedFormat($pdf, 17); $doc.Close(0); $word.Quit()
```

Then `pdftoppm -png -r 100 <pdf> page` and read the pages. Check for rows split
across pages, headings stranded at the foot of a page, missing glyphs in
quotations that carry typographic characters, and stale contents page numbers.
Confirm the delivered file's hash matches the file that was inspected.

## The companion workbook

The codebook states the frame; it cannot show how the material was assigned. A
mapping workbook alongside it carries that, and the sheets that earned their
place in a real build were: a front sheet with the frozen rule and provenance; a
code framework with counts and participants; every coded segment with its
verbatim span, assigned code, decision and reason; a screening log; coverage of
every node in the source tree; the revision log against the previous mapping; and
the quote register with its verification status.

That workbook is a record of this pass. It is not the hierarchy QC workbook: when
the task is to build or audit a multi-level code hierarchy held in a spreadsheet,
`qualitative-codebook-qc` owns that artifact and its gates.

## When the team marks up the codebook

A returned codebook is an instruction set, and it arrives in two forms that are
easy to read one of and miss the other: comments (`word/comments.xml`) and
tracked changes (`w:ins` and `w:del`). Extract both, and treat every item as a
row to be answered.

- **Bind each item to its location**: the code, the field, the anchored text, the
  author and the date. A comment on a *heading* often carries a rule for the
  whole section - "this domain should hold only what happened before the
  training" - so read the anchor, not just the comment text. Then print that rule
  where it binds: in the section, and as a Scope row at the top of every entry it
  governs, in identical wording. One sentence in the front matter is not enough,
  and neither is burying it inside exclusion criteria, where it reads as a local
  caveat rather than a rule for the section.
- **Answer every row.** Deliver a response log with what was asked, what was
  done, and where it landed. An unanswered comment looks exactly like a missed
  one.
- **A merge is a schema change, not a rename.** Keep a retire map from old code
  to new, re-file every segment through it, publish a crosswalk that accounts
  for each retired code, and re-decide any borderline call whose code changed
  shape. Renumber only with the crosswalk in hand.
- **A renumbering sweeps cross-references.** The entries cite each other by
  identifier, so every merge and every collapsed number leaves stale references
  behind - "belongs to impact of caregiving (1.3.1)" pointing at a code that no
  longer exists. Do the sweep programmatically and then assert that no
  identifier in the deliverable is missing from the frame. One project hit this
  at five separate citations in a single revision.
- **Write the seam rule down once.** Where two codes sit on a seam - what the
  subject costs against what changed in the person's life, a value held against
  a value clarified, a difficulty someone else creates against the person's own
  response to it - state the rule in both entries: the primary follows the
  segment's point, and the other code is carried as a secondary. That resolves
  the pair without merging it, and it keeps the counts honest because each
  coding is counted once.
- **If the previous deliverable is locked, publish a new version.** A file open
  on the team's own machine cannot be overwritten, and fighting the lock wastes
  the session. Issue the revision as the next version number, keep a copy of the
  superseded one in your own workspace, and say in the manifest which file
  supersedes which.
- **A strand needs a stated rule.** When the team asks for one code to be
  double-coded across the frame, write down when the secondary applies, apply it
  mechanically, and report primary and any-mention counts separately so nothing
  is silently double-counted.
- **Tidy their edits, and say so.** Hand edits leave dangling clauses, orphaned
  conjunctions and doubled spaces. Fix them, and list each fix in the response
  log rather than changing their wording quietly.
- **A residual code is allowed, a hidden residue is not.** If the team wants one
  `Others` at the end, keep it, and report its count and internal clusters
  alongside the codebook so blind spots stay visible.
- **Regenerate; do not edit their file.** Build the next version from the
  updated frame, keep their annotated copy untouched as the record, and let the
  workbook carry the change log.

## The revision sequence, end to end

A worked order of work for taking a marked-up codebook to the next version. It
comes from a real pass that took a 52-code frame to 34 over four versions in one
day; the stages are ordered so that each one is checkable before the next starts.

1. **Extract the instruction set.** Comments and tracked changes from the marked-up
   file, each bound to its code, field, anchor, author and date. Anything the
   extractor reports as an overlap - identical anchors, nested anchors - is part
   of the instruction set too, even though no comment mentions it.
2. **Look for rules, not just requests.** A comment anchored to a heading is often
   a rule for the whole section ("this domain holds only what happened before the
   intervention"). Write those into the frame first; they change what every other
   decision means.
3. **Re-fit before restructuring.** Re-read every coding against the current
   definitions and record the misfits. Doing this before the merges means the
   merges are applied to a frame that already carries the material correctly.
4. **Settle the counting artefacts.** Decide each identical anchor, each nested
   anchor and each overlapping pair - collapse, facet, or keep and flag - so the
   numbers about to be published are the numbers the reader will assume.
5. **Apply the frame changes with a retire map.** Re-file every coding through it,
   renumber, sweep the cross-references, and assert no identifier points at a code
   that is not in the frame.
6. **Re-choose exemplars for every changed code**, quoting the scope marker where
   the code is bounded, and assert each exemplar is a counted coding of the code
   it illustrates.
7. **Rebuild the workbook** with the crosswalk, the revision log verified against
   the previous file, the response log answering every comment, the anchor-overlap
   sheet and the quote register.
8. **Verify and deliver** as the next version: exemplars byte-identical with the
   anchor inside, workbook opens without repair, every page rendered and
   inspected, delivered files hashed, source file timestamps unchanged, and the
   superseded file named in the manifest.
