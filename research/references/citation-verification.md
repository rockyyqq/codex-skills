# Citation verification

This is the gate between a draft and a delivery. Nothing goes out with a citation
that has not been checked, because a reader who finds one wrong reference stops
believing the rest - correctly, since a wrong reference is evidence that the
verification did not happen.

`scripts/check_citations.py` runs the mechanical checks. Everything below that
requires reading is still yours to do.

Retrieval and formatting are two separate checks and they fail in different
ways. This file is the first; `reference-formatting.md` is the second. A record
that exists but is formatted so that no reader can find it is a citation that
has not been delivered.

## 1. Retrieve the record

For each reference, confirm against the publisher, PubMed or Crossref: authors,
year, title, journal, volume, pages, DOI. Check the details, not just the
existence - a DOI that resolves to a different paper is a common failure of
reference managers, and a correct DOI with the wrong year is a common failure of
memory.

Never cite a citation. "As cited in" means you have not read the original, and
the summary you are relying on may misrepresent it. Retrieve the original, or
attribute the claim to the source that made it.

Then check the reference against the manuscript, not against your memory of it:
every in-text citation has exactly one entry, every entry is cited, and the
author names and the year match character for character in both places.
Reference-manager output is a draft, not a finished list - it inserts duplicates,
carries stale metadata, and applies whichever style file it was last given.

## 2. Every reference carries a link that still works

A citation the reader cannot follow is not a citation. Each reference entry carries
a persistent identifier, and the delivered document carries it as a live link.

Preference order, and why:

1. **DOI**, written as `https://doi.org/10.xxxx/...`. Registered, permanent, and
   it resolves even when the publisher rearranges its website.
2. **PMID or PMC ID** for biomedical work without a DOI.
3. **The publisher's own article page**, where no identifier exists.
4. **An archived copy** for grey literature and pages that may disappear, with
   the archive date.

Never use as the citation link:

- a URL shortener, whose target cannot be seen or verified
- a search-results URL, which will not return the same set later
- a Google Scholar or ResearchGate page, which is a record of a source rather
  than the source
- a link that works only from a logged-in session or an institutional network

Links rot. `scripts/check_citations.py --verify-links` resolves every DOI against
Crossref and reports the ones that fail, which is the fastest way to catch a
transposed digit. A DOI that does not resolve is a blocking problem: either the
identifier is wrong or the reference is.

Where a link cannot be permanent - a government page, a report, a dataset - say
where it lives and when it was accessed, so a reader can tell the difference
between a page that moved and one that never existed.

## 3. Quote integrity

Every quotation must exist character for character in the retrieved text. Check
the words, and check the context: a sentence lifted from a limitations paragraph
as though it were a result is accurate quotation and a false claim.

If you hold only the abstract, you may quote the abstract and must not quote the
paper. Paraphrase the rest and say the full text was not retrieved.

Watch for quotation drift during editing - a phrase edited for flow and left
inside quotation marks is no longer a quotation.

## 4. Number traceability

Every number in the draft should be traceable to a table, figure or page. For
each one, be able to answer: which source, which table, which row.

Percentages, sample sizes, effect estimates, confidence intervals, costs and
utility weights are the figures most likely to drift during drafting. Check them
against the source rather than against an earlier version of your own draft.

Where a number is your own calculation, say so, and state the inputs. A derived
figure presented as sourced is worse than an unsourced one.

## 5. Retraction and correction sweep

Before delivery, check that none of the cited works has been retracted, and that
no correction or erratum changes a figure you rely on. Crossref carries
retraction data for most publishers; Retraction Watch is the other reference.

This applies to sources carried forward from previous work, not only newly added
ones. A source that was sound when you first used it may not be now, and a
retraction published last month will not appear in an old draft.

Where a cited work has been retracted and you still need the point, find other
evidence for it. Citing a retraction with a note is acceptable only when the
retraction itself is the subject.

## 6. Independence recount

Recount studies rather than references, using the signals in
`evidence-appraisal.md`. Report both numbers where they differ, and cite the
primary report for shared results.

## 7. Preprints and grey literature

Label preprints as preprints, name the server, and say whether the work has since
been published. A preprint that was later published with different results must
be cited in its published form.

For reports and grey literature, record the issuing body, the date, and where it
can be retrieved. A citation to a document that no reader can obtain is not a
citation.

## 8. When a check fails

Fix it, or state it. The failure modes to avoid are the quiet ones: dropping a
reference that does not support its sentence without noticing that the sentence
now has no support, and keeping a sentence while weakening it until it says
nothing.

If a check cannot be completed - the source is paywalled, the registry is
unreachable - say which check did not run. An unchecked citation reported as
checked is the one outcome worse than a wrong citation.
