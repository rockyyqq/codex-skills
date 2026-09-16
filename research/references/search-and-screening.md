# Search and screening

A search is a method, and a method has to be reproducible. The test: could
someone else run what you ran, on the same day, and land on the same record set?

## 1. Frame the question

Express it as population, intervention, comparator, outcome, and study design
where design matters. For economic evaluation, add perspective and time horizon,
because those change which studies are eligible at all.

Write the frame down before searching. A question that shifts while you search
produces a record set that answers nothing in particular, and the shift is
invisible in the final write-up.

Also decide, before searching, whether you are doing a systematic search (fixed
protocol, exhaustive, reported as a flow) or a targeted one (enough to support a
specific claim). Both are legitimate. Presenting the second as the first is not.

## 2. Where to search

Free and scriptable, in the order that usually pays:

| Source | Endpoint | Best for |
|---|---|---|
| PubMed | `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=<query>&retmode=json` | Clinical and biomedical literature; MeSH-indexed |
| Europe PMC | `https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=<query>&format=json` | PubMed plus preprints, patents, open full text |
| Crossref | `https://api.crossref.org/works?query.bibliographic=<text>&rows=5` | Resolving and verifying a citation's metadata |
| OpenAlex | `https://api.openalex.org/works?search=<text>&per-page=10` | Citation graphs, forward snowballing, no key needed |
| Semantic Scholar | `https://api.semanticscholar.org/graph/v1/paper/search?query=<text>&fields=title,year,externalIds` | Citation counts and contexts |
| Unpaywall | `https://api.unpaywall.org/v2/<doi>?email=<you>` | Finding a legal open-access copy |
| ClinicalTrials.gov | `https://clinicaltrials.gov/api/v2/studies?query.term=<text>` | Registered but unpublished trials |

Then, depending on the question: Cochrane CENTRAL and CDSR for trials and
reviews, the Tufts CEA Registry for published cost-effectiveness analyses, INAHTA
for health technology assessment reports, WHO ICTRP for international trial
registries, and Scopus or Web of Science if you have access.

Google Scholar is a supplement for finding things you did not think to search
for, not a primary source. It cannot be searched reproducibly and its citation
counts are inflated by non-citing material.

**One database is never enough.** Where the completeness of the record set
matters, the benchmark is unambiguous: a MEDLINE search alone retrieves
somewhere between 30% and 80% of the known published randomised trials on a
question, depending on the area (Dickersin 1994, reported in the Cochrane
Handbook), and relying on it alone can also bias *which* of the trials you find.
For an intervention review the minimum set is CENTRAL, MEDLINE and EMBASE (or a
review group's specialised register), plus the trial and results registries -
and a search of a registry returns studies, not reports of studies, which is a
different kind of record to hold.

Build for **high sensitivity and accept low precision**. A record you never
retrieved cannot be recovered by any later stage of the review; an irrelevant
record costs a few seconds at screening. Precision is recovered in screening,
not in the query.

## 3. Build the query

- Combine controlled vocabulary (MeSH) with free text, because indexing lags
  publication by months and misses new terminology entirely.
- Search title and abstract fields for precision, and add broader fields
  deliberately rather than by default.
- Spell out synonyms explicitly: the intervention in your question has at least
  three names in the literature, and any one of them alone loses studies.
- Use a published, validated filter where one exists - the Cochrane Highly
  Sensitive Search Strategy for randomised trials in MEDLINE is the reference
  example - rather than writing your own. Do not apply a trial filter inside a
  database that already contains only trials: it can only lose records.
- Record filters as part of the query. A date limit, language limit or
  publication-type limit is a decision, and it belongs in the log.

## 4. Keep the log

One line per search: database, interface, date run, exact query string, number of
records, and anything you did to the results. This is what makes the search a
method rather than a habit, and it is the first thing a reviewer or an examiner
will ask for.

Then the flow, at minimum: records identified, duplicates removed, screened on
title and abstract, full texts assessed, excluded with a reason each, included.
Report counts at each step and keep the reasons specific - "not relevant" is not
a reason.

## 5. Snowball, and know when to stop

Backward snowballing reads the reference lists of included studies; forward
snowballing finds who has since cited them. Forward direction via OpenAlex is
free and usually finds more than a database query does, because it follows the
field's own vocabulary.

Stop when a full round of snowballing adds no new included study. Record that you
did the round - "we searched until saturation" without the round counts is an
assertion, not a stopping rule.

## 6. Screening is a decision log, not a filter

Screen against pre-stated criteria and write down which criterion excluded each
record. Where you are uncertain about an inclusion decision, say so and say how
you resolved it.

Two habits worth keeping: never exclude a study for a reason you would not
defend to its authors, and never exclude one because it complicates the story.
Screening on the direction of a result is the failure mode that makes a review
look rigorous while being worthless.
