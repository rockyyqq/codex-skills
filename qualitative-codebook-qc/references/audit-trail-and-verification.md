# Audit trail and verification

The coding is only half the deliverable. This is the half that decides whether
anyone can check it.

## The screening log

One row per source item - **every** item, not only the coded ones. Columns: item
ID, leaf code, decision, reason.

Requirements:

- Coverage is exact: `set(log ids) == set(source ids)`, no duplicates, no gaps.
- Every row carries a non-empty reason, including every exclusion.
- The set of rows marked Include equals the coded sheet in **both** directions.
  A one-directional check hides either an orphan code or a missing row.
- The decision vocabulary is closed: Include / Borderline / Exclude, nothing else.

Report the three counts and the total in the deliverable, so the denominator is
visible next to the numerator.

## The revision log

When the deliverable revises an earlier pass, the log records each change with
four things: what it was before, what it is now, what type of change it is
(newly included, newly excluded, reclassified, moved), and why.

**Verify the log against the previous artifact, not against your memory.** The
log asserts what the old file said. That is a factual claim about a file, and it
is checkable:

1. Open the previous deliverable.
2. Rebuild its decision map from its own screening log.
3. Assert every logged "before" value matches it.
4. Assert the current decision matches the logged "after" value.
5. **Assert there is no decision change absent from the log.** This is the one
   that catches real errors: an undocumented change is invisible otherwise.
6. Assert which items left the coded set, and that each is logged.

Step 5 is worth writing carefully. Comparing logged rows to the file only proves
the log is not wrong; comparing the *whole* set proves it is not incomplete.

If the previous file cannot be opened - see `xlsx-mechanics.md` - say so plainly
and verify against a copy you can demonstrate is the same artifact. Never narrate
what the old version said from memory and present it as verified.

## Reclassification is the log's most important output

The decision changes (included, excluded) are the easy part. The valuable entries
are the **reclassifications** - items that stayed coded but moved between strata -
because that is where the analytic argument actually changed. When a set of items
moves out of "finding" and into "mechanism", say so once per item, with the
reason, and check afterwards that the stratum the flag points at really is the
only stratum carrying those items.

## Quote fidelity

The delivered sheet carries the source quotation and the source leaf code
**byte-identical**. Not "equivalent", not "with the encoding fixed".

- Compare in code, never by eye. `src[i].text == out[i].text`, exact.
- Do not strip trailing spaces, normalise dashes, or repair mojibake. If the
  source really is damaged, report it - do not silently fix it in a quotation.
- Watch for a comparison that passes because both sides were read through the
  same lossy path. Read the source and the deliverable through the same reader,
  but keep the reader faithful: decode as UTF-8 and do not round-trip through a
  console.
- Check the long quotations especially. The longest cells are the ones most
  likely to have been truncated by a write step, and they are the ones a reader
  will check first.

## The construct flag

If the framework separates a construct (for example enactment versus mechanism),
carry a flag column on every row and check its exclusivity as a gate:

- every row under the enactment stratum carries the "counts as" value;
- no row under the mechanism stratum carries it;
- the "does not count" value appears **nowhere else** in the sheet.

That last assertion is what stops a later summary from quietly pooling the two.
Without it, the split survives only as long as everyone remembers it.

## Coverage assertions

Assert, in code, before delivery:

- every source item is mapped or screened exactly once;
- the framework's member list equals the coded sheet's ID set;
- the framework's per-parent counts sum to the coded total;
- every coded item appears under exactly one parent.

Also print the totals on success. A verification run that reports only "PASSED"
gives the reader no way to notice that it checked four rows instead of four
hundred.

## What verification cannot do

Mechanical checks confirm the artifact is internally consistent and faithful to
the source. They cannot confirm the coding is *right*. That is a reading task.
Say which is which when you report: "all gates pass" is not "the coding is
correct", and conflating them is how a QC pass gives false comfort.
