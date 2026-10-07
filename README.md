# Personal Codex skills

My own skills for the Codex app. Private for now - these encode working preferences and
method, not shared team standards.

## What is here

| Skill | Invoke with | What it does |
|---|---|---|
| `health-advisory` | ask a health question, or name it | Answers household health questions from dated, graded sources and keeps a family health record: an emergency gate that runs before anything else, a source ledger that fails closed on a stale source, a DPAPI-encrypted vault that scripts read and the agent cannot print, a periodic review that reports OK / DUE / CANNOT JUDGE, specialty lenses for preparing an appointment, and a passphrase backup that proves itself by restoring. Information and preparation only: never diagnosis, dosing, triage or prognosis. |
| `evidence-first-app-maintenance` | automatic when keeping an existing app working, or name it | Holds the evidence loop for work on something that already exists: know the state before touching it, make the slice small enough to prove it, prove the checks can fail, read the built artefact back rather than trusting the build log, and leave a page the next session can act on. Defers to `test-driven-development` for a new test, `verification-before-completion` before claiming done, and `systematic-debugging` when a cause is unclear. |
| `investment-review` | "is X worth holding", "should I buy X", "would you change your answer on X", or name it | Reviews one investment end to end: what the instrument is, what the case claims, whether the claim is checkable, whether it addresses the price, what the price history shows, how the valuation compares with the alternative, and whether the household already owns the exposure. The case reading and the price reading are reported in separate sections and never combined into a verdict - where they disagree, the disagreement is the finding. Ships `appraise.py`. |
| `poster-review` | automatic on poster work, or name it | Standing requirements for conference, scientific and competition posters: PowerPoint output built from native objects, section order (Background, Methods, Participants, Results, Discussion), prose-versus-bullets rules, chart and data checks, event compliance, and independent verification of the finished deck. |
| `reproducing-charts-from-images` | "make me this same graph", or name it | Rebuilds a chart from a reference image by measuring pixels rather than reading values off the axis, then recovers the design from the same image. Keeps one row order and one data source across the figure, the workbook and the table, and hands the recovered values to an independent verifier with the author's own numbers withheld. Ships `digitize_chart.py`. |
| `research` | ask for a literature review, an evidence table or a citation check, or name it | Sources, appraises and cites evidence for health and mental health services research: framing a searchable question, logging a reproducible search, screening and extracting into evidence tables, appraising design and independence, reading or running a meta-analysis, checking a measure before comparing scores, and formatting references to the journal's style. Ships `check_citations.py`. |
| `role-split` | `$role-split` | Splits a task into independent roles - builder plus at least one verifier who falsifies the result against a source the author did not write - and adds a design reviewer for visual work. Tiers: `$role-split no split` (one self-check pass), `$role-split simple` (2 roles), `$role-split complex` (up to 4). For high-stakes, externally presented work. |
| `technical-analysis` | ask about a chart, a level or an indicator, or name it | Reads a listed security's price and volume history - trend, support and resistance, moving averages, momentum and volatility, chart patterns, and the arithmetic that turns an entry and a stop into a position size. States the limits before the reading: an indicator transforms past price rather than informing, and "will it hold" has no answer. Ships `analyse.py`, `valuation.py` and an OpenD probe. |
| `wealth-advisory` | ask a planning question, or name it | Household financial planning for a Singapore-based family with Greater China exposure and a possible relocation: retirement and multi-currency projections, portfolio risk and mandate checks, CPF/SRS relief planning, protection and continuity review, and monthly mandate monitoring. Ships seventeen Python tools that take a JSON config and refuse to invent a missing number. |
| `trading-advisory` | ask for the separate trading stream, or name it | Runs the household's separate trading stream: an independent, attributed note on one listed security produced with outside tools and logged before the outcome, with the decision left to the household. |
| `qualitative-analysis` | "analyse these interviews", "code these transcripts", or name it | The analytic layer over a study's own transcripts: auditing whether the corpus is ready, writing code definitions that act as coding rules, coding with the rule frozen first, comparing overlapping codes, hunting the disconfirming case, judging saturation, and delivering findings where every claim traces to a verbatim quotation. Ships `corpus_check.py` and `extract_coded_segments.py`. |
| `qualitative-codebook-qc` | "give me parent and grandparent codes", or name it | Builds or quality-checks a multi-level code hierarchy over a flat code list in a spreadsheet: deriving grandparent and parent codes, applying an analytic lens to select what a question actually reaches, and delivering a workbook where every coding decision carries a written reason with full screening and revision logs verified against the previous artifact. Ships `check_coding.py` and `xlsx_io.py`. |
| `photo-composite-editing` | "add X to my photo", "remove Y", or name it | Edits one region of a photograph and leaves the rest of the frame untouched: capability checks before promising a result, a known-good source kept aside, exact-composite versus generative techniques, isolating the target region by connected-component labelling, tone matching, numerical boundary verification, and the Windows image-manipulation traps. |
| `officecli` | Office file work that must be seen, or name it | A second Office toolchain for `.docx` / `.xlsx` / `.pptx`: renders per-page PNG for layout QA, reports text overflow, missing alt text and formula errors, turns mermaid into native editable shapes and LaTeX into a native equation, merges `{{key}}` templates, and drives files headlessly with structured JSON. Routes to the bundled `office-*` skills for ordinary authoring. |

## Layout

Each skill is a folder whose name matches the `name` field in its `SKILL.md` frontmatter:

```
<skill-name>/
  SKILL.md              always present, carries the name and the trigger description
  agents/openai.yaml    display name, short description and default prompt for the UI
  references/           the detail files SKILL.md points to
  scripts/              only in the eight skills that carry code
```

The eight skills that carry code:

- `health-advisory/scripts/` - `vault.ps1` is the only component that touches
  ciphertext; `vault_backup.ps1` is the passphrase backup, verify and restore;
  `validate_record.ps1`, `record_view.ps1`, `record_gaps.ps1` and `due_report.ps1`
  read the vault; `check_sources.py`, `build_query.py` and `validate_report.py`
  never touch it
- `investment-review/scripts/` - `appraise.py`
- `reproducing-charts-from-images/scripts/` - `digitize_chart.py`
- `research/scripts/` - `check_citations.py`
- `qualitative-analysis/scripts/` - `corpus_check.py` (inventory, extract and verify)
  and `extract_coded_segments.py`, which recovers the verbatim quotation a Word comment
  is anchored to
- `qualitative-codebook-qc/scripts/` - `check_coding.py` runs the artifact gates;
  `xlsx_io.py` is a standard-library XLSX reader and writer for machines with no
  spreadsheet library and no working pip
- `technical-analysis/scripts/` - `analyse.py`, `valuation.py`, `opend_probe.py`
- `wealth-advisory/scripts/` - `market_data.py` and `common.py` are shared by the rest;
  `portfolio_risk.py`, `plan_projection.py`, `rebalance.py`, `sg_relief.py`, `srs_drawdown.py`,
  `insurance_compare.py`, `insurance_needs.py`, `refresh_prices.py`, `check_mandate.py`,
  `check_params.py`, `validate_deliverable.py`, `cashflow.py`, `debt.py`, `goal_funding.py`
  and `risk_register.py` sit on top of them

The `description` line in each `SKILL.md` is what decides when the skill fires, so edit it
carefully - it is the trigger, not a summary.

## Installing on another machine

Either copy the skill folders into `%USERPROFILE%\.codex\skills\`, or ask Codex to install them
with the skill-installer skill and this repository:

```
Use $skill-installer to install the skill at <repo-url>/tree/main/role-split
```

Installed skills become available on the next turn. Private repositories work with existing git
credentials or a `GITHUB_TOKEN`.

For personal plugin packaging (so the skills appear on the app's Plugins page and can be shared
as a bundle), see `$plugin-creator` - a plugin is a manifest plus a `skills/` folder.

## Installed, but not authored here

`peer-review` sits in this folder but is not part of this repository. It is the
`peer-review` skill from Scientific Agent Skills by K-Dense (MIT), installed with
`$skill-installer` and ignored by `.gitignore` so it stays updatable from upstream. Its
premise is different from the skills above - it supports an *accountable human reviewer* of
someone else's manuscript, under a mandatory authorization and confidentiality gate, and it
refuses to write an accept/reject recommendation at all.

`photo-composite-editing` and `officecli` came in from the DeepSeek Harness on
7 October 2026 rather than being authored here: the first lived as a single
`photo-composite-editing.md` in the Harness skills folder and was converted to the folder
layout, the second was copied with its `references/` from the Harness workspace. Neither
ships `scripts/`.

## What must never be committed here

- Household configs, statement values, account numbers, holdings or net-worth figures.
- Generated overlays such as `prices.json`, risk reports or projection output. Keep real data
  outside the repository; the skills are methods, not data.
- Any API key, token or credentials file.

The parameter file `wealth-advisory/references/sg-parameters-2026.json` is deliberately included:
it holds published Singapore tax and CPF figures with verification status, not personal data.
