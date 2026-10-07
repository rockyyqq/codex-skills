# Analytic moves

Each move answers a different question. Run the ones the question needs, and
stop - running all eight produces a document nobody can act on.

Every move produces *claims*: a statement, the rung it sits on (observation,
interpretation, hypothesis), the evidence behind it, and the counts that qualify
it. Prose that only restates the material has done none of the work.

## 1. Thematic summary

**Does:** summarises what the coded material for one code actually contains,
using the code's name and memo as background rather than as the subject.

**When:** a code needs its evidence gathered in one place - before writing it up,
or before deciding whether it is one code or two.

**Output:** the claims the material supports, each with quotations and case
counts, plus what in the material the code did *not* reach.

**Fails when:** the response summarises the memo instead of the data, or
generalises past what the coded segments say.

## 2. Themes generation

**Does:** identifies between two and ten recurring themes across the corpus,
each with a short title and a description explaining its significance, context
and nuances.

**When:** early exploration, or a check on whether the existing frame has missed
something visible across the whole corpus.

**Output:** distinct themes, each supported by material and qualified by case
counts.

**Fails when:** the themes overlap, when a theme is a topic rather than a pattern,
or when a plausible-sounding theme has no evidence behind it. Check every theme
back against the corpus before it enters a deliverable, and treat the output as
a candidate list to test, not a result.

**Source:** Friese, S. (2024). *Prompting for Themes*. QeLudra community.
Credit this when the method is used in a delivered analysis.

## 3. Expected versus unexpected

**Does:** states what the phenomenon usually looks like, then identifies what in
this material is unexpected against that expectation.

**When:** the study needs its contribution to the field, or a check on whether an
analysis is only confirming what was already believed.

**Output:** the surprise, the expectation it departs from, and the material that
shows the departure.

**Fails when:** the expectation is treated as evidence. The expectation is an
assumption drawn from prior knowledge or the literature; label it as one, cite
the literature where it comes from, and never let it do the work of data. An
expectation stated without a source is a hypothesis of your own.

**Source:** adapted from QualCoder's "analyse the unexpected" prompts (QualCoder
4.0, LGPLv3).

## 4. Differences between cases

**Does:** compares cases, documents or groups within the material, looking for
contrasts.

**When:** the sample has structure worth exploiting - participants who did and
did not take up the intervention, sites, roles, follow-up versus baseline.

**Output:** which differences hold, how many cases on each side, and the material
that shows them.

**Fails when:** a contrast is manufactured from one vivid quotation, or from two
thin cases. **"No real difference" is a valid result** and is more useful than a
contrast built on nothing. Report it as one.

**Source:** adapted from QualCoder's "analyse differences" prompt (QualCoder 4.0,
LGPLv3).

## 5. Code profile and blind spots

**Does:** takes one code as a lens and states both what it brings into focus and
what it leaves out, including alternative readings of the same material.

**When:** before a code is written up, or when a theme has begun to look
inevitable.

**Output:** what this perspective taught about the research question; the blind
spots; the alternative interpretations and what they would change.

**Fails when:** it becomes advocacy for the code. The point is the limitation,
not the defence.

**Source:** QualCoder's "code critic" prompt (QualCoder 4.0, LGPLv3).

## 6. Code comparison

Use when two codes overlap and the boundary has stopped being clear. This is the
move that most often changes a frame, because it is where "these are two things"
or "this is really one thing" gets decided.

**Procedure:**

1. Read a broad selection from different cases for each code, not only the
   segments nearest to hand. If the material is thin, say the assessment is
   preliminary.
2. Profile each code: what does it bring into focus, what perspective does it
   offer, how does it differ from the other?
3. Classify every reviewed segment into one of three groups, with a short
   justification each, grounded in the material:
   - **Clear case** - the meaning in the code's definition is present, explicitly
     or by clear implication.
   - **Borderline** - it partly fits, and another code is also plausible; the code
     captures something relevant but not the passage's primary meaning.
   - **Likely miscoded** - the passage's central meaning lies elsewhere; the code
     is being applied too broadly or imprecisely.
4. Write the comparison: what A captures that B does not, where they overlap,
   where confusing them is a risk, which is currently narrower and which broader,
   and what is lost if only one is used.
5. State the implications: inclusion and exclusion criteria going forward,
   guidance for double-coding, and the open questions.

**Rules:** review before recoding, never recode during the comparison. Allow
double-coding only when two aspects are genuinely central at the same time.
Read meaning, not keywords. Keep empirical statement, interpretation and coding
decision visibly distinct - collapsed together, the comparison cannot be
appealed.

**Output:** a comparison report whose classifications and criteria can be handed
to `qualitative-codebook-qc` to carry into the codebook.

**Source:** adapted from QualCoder's code-comparison prompt (QualCoder 4.0,
LGPLv3).

## 7. Saturation

**Does:** assesses whether the coded material already holds the relevant
variants, dimensions, conditions or manifestations of the phenomenon, in the
sense of theoretical saturation.

**When:** deciding whether to collect more data, and when a paper claims
saturation.

**Answer four questions:**

1. Which recurring variants of the phenomenon are well represented here?
2. Are there variants, boundary cases or counterexamples not yet covered?
3. Does the material suggest the code's definition is too narrow, too broad, or
   internally heterogeneous?
4. On the available evidence: close to saturated, partially saturated, or clearly
   not saturated?

Also assess the code's memo: does it cover the dimensions the material shows,
what is missing, and does the definition need widening or narrowing?

**Verdict:** one of the three, with the evidence for it. State what was searched
and what would have counted as a new variant. Never infer saturation from the
absence of new codes in the same few cases - that is a statement about how much
was read, not about the phenomenon.

**Source:** QualCoder's theoretical-saturation prompt (QualCoder 4.0, LGPLv3),
after grounded theory.

## 8. Reconstructive interpretation

**Does:** reads a passage twice - first for what is said, then for how the
speaker handles it - to reach orientations that the speakers themselves do not
state.

**When:** the study asks about orientations, dispositions or the logic of
practice rather than about opinions, and the material is narrative.

**Two passes:**

- **Formulating interpretation** - summarise the content in plain language, pick
  the overall topic and the successive sub-topics *in the order the speaker
  produced them*, and give source references for each. Stay inside the
  participants' own relevance system: no context knowledge, no conclusions about
  what they do, every sub-topic formulated on its own terms.
- **Reflecting interpretation** - explain how the topic is handled. Narratives
  (a singular event with time and place, "and then...") and descriptions
  (recurring sequences, "always", "often") document an implicit logic of action.
  Generate hypotheses about that logic, and about similarities across speakers
  that go beyond the immediate context. Support every hypothesis with verbatim
  quotations and references.

**Fails when:** it slides into motives. The method reconstructs orientations
documented in the material; it does not read minds, and hypotheses about
orientation frameworks are labelled as hypotheses.

**Source:** Lieder, F. R. & Schäffer, B. (2024). *Reconstructive Social Research
Prompting (RSRP): Distributed Interpretation between AI and Researchers in
Qualitative Research.* https://doi.org/10.31235/osf.io/d6e9m - the documentary
method. Credit this when the method is used.

## Choosing and reporting

Two or three moves, chosen for the question, usually beat eight run in sequence.
When reporting: name the move, its rung, its counts, and its limitation. The
limitation is part of the result - a saturated-looking code that was tested
across two cases is a different finding from one tested across twenty, and the
reader needs to see which they are reading.
