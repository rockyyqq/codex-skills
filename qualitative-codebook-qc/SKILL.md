---
name: qualitative-codebook-qc
description: Build, extend or quality-check a multi-level code hierarchy over a qualitative code list held in a spreadsheet - deriving grandparent and parent codes from flat leaf codes, applying an analytic lens to select the items a question actually reaches, and delivering a workbook where every coding decision carries a written reason, a full screening log, and a revision log verified against the previous artifact. Use for "give me parent and grandparent codes", coding a subset "through the lens of X", reviewing or redoing an earlier coding pass, and any qualitative QC where the audit trail matters as much as the codes. Not for finding or appraising literature (use research), not for the analysis that produces the leaf codes in the first place - transcripts, code definitions, coding and saturation are qualitative-analysis - and not for survey or scale measurement.
---

# Qualitative codebook QC

Turn a flat list of qualitative codes into a hierarchy a second coder can audit.
The value of this skill is not assigning plausible labels - it is making every
decision traceable, so a reviewer can see what was excluded and why, and can
tell mechanism from finding.

## Working with qualitative-analysis

This skill starts from a code list that already exists. It does not decide what
the codes mean against the material, and it should not be used to produce the
leaf codes in the first place.

- **`qualitative-analysis` owns the material layer** - reading transcripts and
  study documents, auditing corpus readiness, writing code definitions and memos
  that function as coding rules, producing analytic claims, judging saturation,
  and testing whether a set of codes describes the data.
- **This skill owns the spreadsheet layer** - the multi-level hierarchy, the
  three-way screening log, the construct flag, the revision log, the workbook
  deliverable and its XLSX mechanics.
- **When both apply** - a full codebook review, say - run `qualitative-analysis`
  first to freeze the rule and settle the leaf codes against the material, then
  bring the frozen rule and the code list here. Never let the workbook's
  structure decide the rule.

Quotation checking splits along the same line: `qualitative-analysis` verifies
quotations against the source corpus through its quote register, while
`scripts/check_coding.py` here verifies that the workbook's quotations match the
source sheet it was given. Use each on its own input rather than re-implementing
either.

## Non-negotiables

**The rule comes before the codes.** Write the inclusion rule down and show it
before assigning a single code. A hierarchy assembled first and justified
afterwards cannot be audited, because the reader cannot tell which items were
never considered.

**Never pool two constructs in one count.** Reflective engagement with an
intervention is not application of it; perceived applicability is not enactment.
Keep them in separate strata and carry a machine-checkable flag ("counts as X?
Yes/No") on every row, so the split cannot be quietly undone by a later summary.
This is the single most common way a qualitative theme overstates itself.

**Every item gets a decision and a written reason.** Screen the *whole* list -
not only the items you intend to keep. An item that is excluded without a stated
reason is indistinguishable from an item that was missed.

**Code the disconfirming case.** Actively look for the item that contradicts the
emerging theme - the participant who says the content does not apply, the
success that happened without the intervention - and give it a home in the
framework. Unstated disconfirming evidence is the failure this skill exists to
prevent.

**A revision log is a claim about an artifact.** When you revise a previous pass,
verify the log against the previous *file*, not against your memory of it. If the
prior artifact cannot be opened, say so and use a verified copy - never narrate
what the old version said.

**Quotes are byte-identical or they are nothing.** The delivered sheet carries the
source quotation unchanged. Never paraphrase into a quotation column, and never
"tidy" punctuation or encoding. Check it programmatically, not by eye.

**Say when the unit is one case.** A pattern from one interview is a candidate
dimension and a coding frame to test, not a finding. Label it as such in the
deliverable itself, not only in conversation.

## Workflow

1. **Read the list as data.** Load the source sheet and treat the leaf-code
   column and its quotation as the unit of analysis. Record how many codes there
   are; that number is the denominator for everything that follows and belongs in
   the deliverable.
2. **Freeze the screening rule.** State the inclusion rule, the exclusion rule
   and the boundary rule before coding. See `references/hierarchy-and-screening.md`.
3. **Build the hierarchy.** Grandparent (domain) > parent (category) > grandchild
   (the existing leaf code). Prefer meaning over symmetry; a parent with one
   member is fine if it carries a distinct idea. Give every level a stable code
   and a short definition.
4. **Screen and code in one pass.** Three-way: Include / Borderline / Exclude,
   with a reason on every row. Borderline items are logged but not coded, so the
   reviewer can promote them in one step rather than re-deriving the call.
5. **Verify mechanically.** Run the gates below before delivery.
6. **Deliver.**

## Deliverable shape

A single workbook. The sheets that earn their place:

| Sheet | Contents |
|---|---|
| Coded items | Source columns unchanged, then the lens/hierarchy codes, the construct flag, the rationale, the prior mapping, and a QC note on contestable calls |
| Analytic frame | The question, the inclusion and exclusion rules, the boundary rule, and the counts - including the ratio that carries the argument |
| Framework | Grandparent > parent with member IDs and a definition per parent |
| Screening log | Every source item with decision and reason - the audit trail |
| Revision log | What changed from the previous pass and why, verified against it |

Keep the source columns byte-identical and in their original order. Add columns;
never rewrite the ones you were given.

## Verification gates

Run these; do not assert them. `scripts/check_coding.py` implements all of them.

- Every source item is screened exactly once, with a non-empty reason.
- Every coded item appears in the screening log as Include, and the two sets are
  equal in both directions.
- No duplicate code IDs on the coded sheet.
- Every parent code nests under the grandparent it is filed with.
- Framework membership equals the coded set, and the framework counts sum to the
  coded total.
- Quotation and leaf-code text match the source exactly.
- The "not X" flag appears only inside the stratum it belongs to.
- Any decision change from the previous pass is documented in the revision log,
  and no change is undocumented.
- The analytic question, if one is stated, is open-ended and free of directional
  verbs (*affect, influence, impact, determine, cause*).
- The workbook opens in the target application without a repair prompt.

## Mechanics

Spreadsheet plumbing trips this work more often than the analysis does. The
traps - writing XLSX without a library, cloud-placeholder files that refuse to
open, and how to verify the file that was actually delivered - are in
`references/xlsx-mechanics.md`. Read it before writing any output file.

## References

- `references/hierarchy-and-screening.md` - level design, naming, the screening
  rule, the three-way decision, the disconfirming-case rule, and how to frame an
  analytic question that can be answered.
- `references/audit-trail-and-verification.md` - what the screening and revision
  logs must contain, how to verify a revision against the prior artifact, quote
  fidelity, and the coverage assertions.
- `references/xlsx-mechanics.md` - the stdlib XLSX reader and writer, dehydrated
  cloud placeholders, Excel COM verification, and console-encoding false alarms.

## Scripts

- `scripts/xlsx_io.py` - read any sheet of an .xlsx, and write a multi-sheet
  workbook with frozen headers and autofilter, using only the standard library.
- `scripts/check_coding.py` - the verification gates above, as a CLI.

```
python scripts/check_coding.py --source codes.xlsx --deliverable coded.xlsx
```
