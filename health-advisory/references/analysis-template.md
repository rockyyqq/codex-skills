# Family analysis — the output structure

Use this whenever the household asks for an analysis of the family health
record.

**The order is the argument.** It moves from what was checked, to what is in the
record, to what the record supports, to what it cannot, to what to do. Never
reorder it to lead with a conclusion: the reader has to see the basis before any
reading of it.

## Read the artifact first

| Command | Why |
|---|---|
| `scripts/validate_record.ps1` | If the record does not match the schema, stop and fix it. An analysis of an invalid record is fiction |
| `scripts/record_view.ps1` | Per-person structure, flags, and gaps |
| `scripts/due_report.ps1` | The review: its status and its action items |
| `scripts/check_sources.py` | Whether the source ledger is stale |

**Analysing from memory of having written the record is not analysis.** A dropped
or renamed key is invisible that way, and the view exists precisely so the
analysis is read rather than recalled.

## The nine sections

**1. What was checked.** One line each: the record validates · how many people ·
how many sources verified and whether any is past review · the review's status.
A reader must see the basis before the content.

**2. The household, and who answered for whom.** One row per person:
relationship, counts by section, and gaps. **The informant column is not
optional.** The most reliable finding this skill has produced is that gap counts
track who was interviewed rather than who is unwell — and that is invisible
unless it is shown. If the household is reading detail as severity, this table is
where it gets corrected.

**3. The dated items, or none.** Every action item the review produced, with its
date. If there are none, say so and say why — the review runs on dates, so a
household with no pending dates produces no actions, and that is a property of
the mechanism, not good news.

**4. What the record supports.** Documented facts with their sources and dates.
No interpretation.

**5. Patterns no single record shows.** The reason a household file exists. State
them as observations about the records, never as conclusions about the people.

**6. Cross-record inconsistencies.** A fact recorded in one member's file and
absent from, or different in, another's.

**7. Gaps, ranked by what they would change.** Not by count and not alphabetically.
The gap that unblocks the most goes first.

**8. What this analysis cannot do.** One short block: nobody was examined, no
threshold is sourced, nothing here is a conclusion.

**9. What to do next — operational only.** Book it, fetch it, ask it, interview
them. **Never a treatment, a dose, a referral, or a reading.** Where the next step
is clinical, the output carries the question to put to a clinician rather than the
answer.

## What the structure deliberately excludes

- **No differential.** A list of possibilities is decision support, not analysis,
  and it anchors whoever reads it.
- **No ranking of people by health.** Not the sickest, not the healthiest.
- **No risk score.** A score travels without its caveats.
- **No reading of what a pattern means.** Whether four people with rhinitis is
  relevant is a clinician's question; the analysis can pose it and cannot answer
  it.

## Where the output goes

An analysis holds content about several people at once, so it is a report: write
it to `reports/<date>-family-analysis.md` and put the operational items in the
chat. The household may ask to see the whole thing — that is their call, and the
cost is that the content enters the session store, which is not encrypted.
