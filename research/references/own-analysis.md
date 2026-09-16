# Your own analysis as a source

An analysis is evidence, and it is subject to the same rules as a published
study: a reader has to be able to retrieve it, see how it was produced, and
check it. The difference is that the retrieval problem is yours to solve, and it
is solved at the time of the analysis or not at all.

SAS-specific failure modes are at the end, distilled from *The Little SAS Book*
(Delwiche & Slaughter, 4th ed., 2008; SAS 9.2 era - the syntax below is stable,
but check the log behaviour against your own version, since later releases add
warnings and change some defaults).

## The provenance chain

For every result that reaches a draft, be able to produce:

1. the **raw data** as received, unmodified, with its source and the date it was
   extracted;
2. the **analysis dataset**, with the program that derived it from the raw data
   - every exclusion, recode, rename and merge;
3. the **analysis program** that produced the result, and the software version;
4. the **log or console output** for that run - and for SAS, the log is the only
   place a silently wrong merge or a missing-value cascade becomes visible;
5. the **output file** the number was read from, and the line in it;
6. the **date** it was run, who ran it, and the **seed** if anything random was
   involved.

Keep the output file, not a transcription of it. Numbers retyped into a draft
are the ones that drift, and a retyped number has no chain back to the run.

## Rules that apply whatever the software

- **Report the analysis as it was run.** Re-running to get a friendlier number,
  or selecting the specification that reached significance, is the same failure
  as citing a study that does not exist, and it is harder to detect afterwards.
  Where several specifications were tried, say so and report the one named in
  advance as primary.
- **Analyses not named in advance are exploratory.** Label them, in the text and
  in any abstract. A subgroup that only appears in the results section is a
  hypothesis.
- **State the exclusions, the missingness and the denominators.** How many
  observations entered, how many left and why, and how many were missing on each
  variable. Percentages without denominators are the commonest arithmetic
  problem in a results section.
- **A number you derived is your result, and it is labelled as one.** State the
  inputs and the method; a derived figure presented as sourced is worse than an
  unsourced one.
- **Version everything.** Software, package, module, and command syntax change
  results at the margins. A result that cannot be reproduced because the version
  is unknown is not reproducible.

## SAS: where it goes quietly wrong

The log reports the number of observations in and out of every DATA and PROC
step. **Check those counts against expectation at every step.** A silent row
loss or duplication is visible there and nowhere else - not in the printout, and
not in the results.

- **`MERGE` without a `BY` statement does not error.** SAS joins the first
  observation of each dataset to the first, the second to the second, and so on,
  producing a plausible dataset that means nothing. Always merge `BY` a key, and
  check the record count before and after.
- **Both datasets must be sorted by the `BY` variables.** If they are not, SAS
  refuses with "ERROR: BY variables are not properly sorted" - a good failure,
  because it stops. Sorting by the *wrong* variables produces no error at all.
- **Same-named variables collide.** In a merge, a variable that exists in both
  datasets is taken from the **second** dataset and the first dataset's version
  is lost without warning. Rename before merging (`RENAME=`) when the names are
  not the matching keys.
- **A duplicated key duplicates rows** in a one-to-many merge. This is how group
  means get attached to each row, and also how a dataset that was supposed to be
  one row per person quietly becomes more than one. Check for duplicate keys
  before the merge, not after.
- **Missing values compare as the smallest value.** An `IF/THEN/ELSE` chain that
  does not test for missing first assigns missing observations to the lowest
  category - the `Cost = .` row becoming "low" cost. Test for missing first,
  every time, unless the data cannot contain any.
- **Arithmetic on a missing value propagates it**, and the log notes "Missing
  values were generated as a result of performing an operation on missing
  values". The note is not an error, but it is a question to answer: which
  variable, how many rows, and why. `SUM()` of a set of arguments returns the sum
  of the non-missing ones, which is a decision - state it rather than inheriting
  it.
- **Formats are not storage.** A `FORMAT` in a DATA step is stored with the
  dataset permanently; the same statement in a PROC step applies only to that
  procedure's output. Two outputs of the same variable can therefore display
  differently - and rounding is display, not computation.
- **`PROC IMPORT` guesses** variable types and lengths from the first 20 rows.
  Where those rows are unrepresentative or blank, the variable is typed wrongly
  for the whole file. Set `GUESSINGROWS`, and inspect the variable types before
  analysing anything.
- **Reading raw files** needs the delimiters handled explicitly (`DSD`,
  `MISSOVER`) where there are consecutive or embedded delimiters, or the row
  count changes without any error being raised.
- **Dates are numbers with a format attached.** Without the format, a date is
  indistinguishable from a number; with the wrong informat, it is silently wrong
  by decades. Display a known date as a check that the informat was right.

## Reporting it

The Methods section of anything you write from your own analysis states: the
data source and extraction date; the sample and every exclusion with counts;
missingness by variable; the software and version; the specification of the
primary analysis and how it was chosen; what was exploratory; and where the
output is filed. That is the same set of facts a reader would need from someone
else's study, and they are being asked to take your word for all of it.
