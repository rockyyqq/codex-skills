# Reference formatting

Distilled from the *Publication Manual of the American Psychological Association*
(6th ed., 2010), the edition most journals in this field still specify. Two
caveats before anything else:

- **The journal wins.** Read the instructions to authors before formatting a
  single reference. A correctly formatted APA 7 list submitted to an APA
  6 journal is still wrong.
- **This file is the 6th edition.** Where a target uses APA 7, apply the deltas
  at the end. Those deltas come from the 7th edition, not from the source used
  here, so confirm an individual rule against the current manual before relying
  on it.

Correct formatting does not make a source real. Everything here sits *after*
`citation-verification.md`: retrieve the record, then format it.

## The two-place rule

Every in-text citation has exactly one reference-list entry, and every entry is
cited at least once. The spelling of the author name and the year must be
identical in both places - a mismatch is the failure a reader notices first, and
`scripts/check_citations.py` reports it mechanically.

## In-text citations

| Source | Parenthetical | Narrative |
|---|---|---|
| One author | (Kessler, 2003) | Kessler (2003) |
| Two authors | (Smith & Jones, 2007) | Smith and Jones (2007) |
| Three to five authors, first citation | (Kisangau, Lyaruu, Hosea, & Joseph, 2007) | Kisangau, Lyaruu, Hosea, and Joseph (2007) |
| Three to five authors, later | (Kisangau et al., 2007) | Kisangau et al. (2007) |
| Six or more authors | (Kosslyn et al., 1996) from the first citation | Kosslyn et al. (1996) |
| Group author | (National Institute of Mental Health [NIMH], 2008), then (NIMH, 2008) | NIMH (2008) |
| No author | Short title in quotes: ("Six Sites Meet," 2006) | the report *Six Sites Meet* (2006) |
| Two works, same author, same year | (Kessler, 2003a, 2003b) | Kessler (2003a) |

- Join names with **and** in running text, **&** inside parentheses, tables,
  captions and the reference list.
- Multiple works in one parenthesis: alphabetical order, separated by
  semicolons.
- The year is repeated in each new paragraph's first citation. Within one
  paragraph after a narrative first mention, the year may be omitted - the one
  place where APA is relaxed about repeating itself.
- Cite the specific page or paragraph for **every** quotation, and for a
  paraphrase of a specific passage where locating it matters. No page number on
  a quotation is a fatal detail, not a style slip.
- **Secondary sources.** APA permits "(Allport's diary, as cited in Nicholson,
  2003)" sparingly, listing only Nicholson. This skill does not: retrieve
  Allport, or attribute the claim to Nicholson openly and say so in the text.
  Where the original genuinely cannot be obtained, say which source you are
  relying on and why.
- Personal communications (email, interview) are cited in text only, with a
  date, and never appear in the reference list.

## Building the reference list

- Start on a new page, with the word **References** centred at the top.
- Alphabetical by the first author's surname. One-author entries precede
  multiple-author entries with the same surname; works by the same authors are
  ordered by year, then by title with **a, b, c** added to the year.
- Hanging indent of 0.5 inch. Sentence case for article, chapter and book
  titles; title case and italics for journal and book titles.
- Author as *Surname, F. M.*, separated by commas, with **&** before the final
  author. Give up to **seven** authors; with **eight or more**, list the first
  six, insert an ellipsis, then the final author.
- When no author exists, the title moves to the author position and the entry is
  alphabetised by its first significant word.
- Journal titles are given in full, italicised, with the volume italicised and
  the issue number in parentheses *not* italicised. Dropping the issue number
  when the journal is paginated by issue makes the article unfindable.

## Templates

**Journal article with a DOI** (the default case):

> Herbst-Damm, K. L., & Kulik, J. A. (2005). Volunteer support, marital status,
> and the survival times of terminally ill patients. *Health Psychology, 24,*
> 225-229. doi:10.1037/0278-6133.24.2.225

**Journal article with no DOI, retrieved online:** same form, then
`Retrieved from http://journal-homepage` - the journal's home page, not the
article's session-specific URL, and no retrieval date.

**Advance online publication:** `Journal Name. Advance online publication.
doi:...`

**Book:** `Author, A. A. (year). Title of work: Capital letter also for
subtitle. Location: Publisher.`

**Chapter in an edited book:** `Author, A. A. (year). Title of chapter. In
A. A. Editor & B. B. Editor (Eds.), Title of book (pp. xx-xx). Location:
Publisher.`

**Technical report:** `Author, A. A. (year). Title of report (Report No. xxx).
Location: Publisher.`

**Thesis or dissertation, from an institutional repository or database:**
`Author, A. A. (year). Title (Doctoral dissertation). Retrieved from
Database Name. (Accession or Order No. xxx)`

**Unpublished thesis:** `Author, A. A. (year). Title (Unpublished doctoral
dissertation). Institution, Location.`

**Conference paper:** `Author, A. A. (year, Month). Title. Paper presented at
the meeting of Organization, Location.`

**Dataset or software:** `Author, A. A. (year). Title [Data file and code book]
or [Computer software]. Retrieved from http://...`

**Preprint or in-press manuscript in a repository:** `Author, A. A. (in press).
Title. Journal Name. Retrieved from http://...` - and see
`citation-verification.md` on labelling preprints.

Publisher location follows APA's own rules - city and state abbreviation for US
locations, city and country elsewhere - and they are fiddly enough that the
manual's examples, rather than a guess, are the place to check each one.

## Numbers, statistics and quotation mechanics

- Italicise statistical symbols: *M*, *SD*, *N*, *n*, *p*, *t*, *F*, *r*, *d*,
  and the Greek letters that are conventionally italicised.
- No leading zero on values that cannot exceed 1 (*p* = .03, *r* = .45,
  α = .05); leading zero on values that can (*M* = 0.75 kg, *d* = 1.20).
- Report the exact *p* value where the software gives one; `< .001` is the floor,
  not a habit. Every *p* is meaningless without an effect size and a confidence
  interval - see `evidence-appraisal.md`.
- Numerals for 10 and above, words for below, with the standard exceptions
  (numbers beginning a sentence, units, statistics, time, and exact
  measurements).
- **Fewer than 40 words:** run into the text, in double quotation marks, with a
  page number. **40 words or more:** block quotation, indented 0.5 inch, no
  quotation marks, page number after the final punctuation. Quotations must be
  verbatim, whatever the surrounding style says.

## Tables and figures

- Number consecutively in the order of first mention, and refer to each by
  number in the text - never "the table below".
- Table: number, then an italic title in title case, rules only at the top,
  below the header row, and at the foot. Figure: number, italic title, image,
  then caption.
- Notes go below in the order *Note.* (general), superscript letters
  (specific), asterisks (probability). Explain every abbreviation and every
  symbol in the note, because the table must stand alone if it is reproduced
  elsewhere.

## Headings

| Level | Format |
|---|---|
| 1 | Centred, bold, title case |
| 2 | Flush left, bold, title case |
| 3 | Indented, bold, sentence case, ending with a period |
| 4 | Indented, bold italic, sentence case, ending with a period |
| 5 | Indented, italic, sentence case, ending with a period |

The introduction carries no heading. Start at Level 1 and add levels without
skipping. Never number headings in a manuscript; the manual's own numbered
sections exist only for cross-referencing.

## Language about people

APA's bias-free language rules are of the same status as its formatting rules,
and reviewers do enforce them:

- Person-first where the condition is not the person's chosen identity:
  *people with schizophrenia*, not *schizophrenics*; *participants with
  dementia*, not *demented participants*.
- Group descriptors are adjectives, not nouns: *older adults*, not *the
  elderly*; *people with disabilities*, not *the disabled*.
- Name the demographic variable that mattered rather than a proxy for it, and
  report the descriptors you collected. A sample described only as "Asians" or
  only as "caregivers" cannot support a comparison between groups.
- Describe the level and the comparison, not a value judgement: *low income*,
  not *the poor*.

## If the target uses APA 7

Confirm each against the current manual; these are the changes that alter a
manuscript rather than its cosmetics.

- **In-text:** three or more authors shorten to *et al.* from the first
  citation.
- **Reference list:** list up to 20 authors; with 21 or more, give the first 19,
  an ellipsis, then the final author.
- **Links:** DOIs and URLs as live hyperlinks, `https://doi.org/10.xxxx/...`,
  with no `doi:` prefix.
- **Library-style data removed:** no place of publication for books; no
  "Retrieved from" unless the content is designed to change, in which case give
  the retrieval date.
- **Journal articles:** always give the issue number where one exists.
- **Headings:** Level 3 becomes flush left, bold italic, title case; Levels 4
  and 5 are indented, bold, and bold italic respectively, in title case, each
  ending with a period.
- **Running head:** required only for manuscripts being submitted for
  publication, not for student papers.
- **Singular *they*** is endorsed where the person's pronoun is unknown or
  where that is the person's pronoun.
