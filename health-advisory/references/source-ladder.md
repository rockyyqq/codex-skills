# The source ladder

| Question class | First source class | Not |
|---|---|---|
| Does X work? | `systematic-review` — Cochrane, or another systematic review | a single study |
| What is recommended? | `guideline` — NICE, WHO, MOH clinical guidelines | a health blog |
| Dose, interaction, contraindication | `label` — the approved product label | a forum |
| Safety signal | `regulator` — HSA, FDA | news coverage |
| What is X? | `patient-education` — HealthHub, MSD Manuals, MedlinePlus | a journal article |

## Which jurisdiction, for which question

Two classes, both dated, both in `sources.json`:

- **Evidence questions** — does this work, what does the guidance say — **do not
  change at a border.** Cochrane, WHO, NICE and the primary literature answer
  them. A Singapore-only ledger leaves those sources undated and unchecked, while
  the ladder above still cites them. That was a real defect: the ladder read as
  jurisdiction-neutral while the ledger was not.
- **Local care questions** — what to do at 2am, which screening programme applies,
  what is subsidised, whether a product is licensed here — only a local source
  answers. An international guideline will not tell you the emergency number.

So the rule is not "local first" or "international first". It is: **match the
source to the question**, and date every source whichever class it belongs to.

## Reviews first, with named fall-throughs

A systematic review is used when it fits. Move to `primary-study` in five cases,
and say which one fired:

1. The review is **superseded** — a large trial published after its search date
2. It **does not fit** the question — wrong population or comparator
3. It is **empty** — no studies met inclusion criteria
4. It is **inconclusive** — "insufficient evidence" is reported, then primary work
5. It **cannot answer** the question — interactions and dosing are label questions

"No reviews available" must be demonstrated by a logged search, never assumed.

## The recency lane

Recency is a **lane, not a filter**. Filtering by date would discard the oldest
and often strongest evidence, and would weight the result toward small,
unreplicated and preprint findings.

1. **Standing answer** — the best available review or guideline, of any date,
   with its date stated
2. **12-month sweep** — restricted by study type, reporting what supersedes,
   contradicts or adds. Emptiness is a finding: "**nothing since** <date>"

Verified mechanics: PubMed `datetype=edat` with `mindate`/`maxdate`, filtered by
study type — on the test query this reduced 1,610 hits to 114. Europe PMC
`FIRST_PDATE:[...]` with `sort=P_PDATE_D desc`.

## Three things the evidence section must always state

1. That absence of evidence is **not evidence of absence**
2. Where only the abstract was retrieved, rather than the full text
3. Where sources disagree, and the reason — population, comparator, setting,
   time horizon, outcome definition

## Only effectiveness questions get this

`routing.json` sends four question classes to four processes. The literature
sweep described here applies to **effectiveness** questions only. A terminology
question is answered from one `patient-education` or `guideline` source; a drug
question from the `label`; a symptom question from the consultation workflow.
