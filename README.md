# Personal Codex skills

My own skills for the Codex app. Private for now - these encode working preferences and
method, not shared team standards.

## What is here

| Skill | Invoke with | What it does |
|---|---|---|
| `poster-review` | automatic on poster work, or name it | Standing requirements for conference, scientific and competition posters: PowerPoint output built from native objects, section order (Background, Methods, Participants, Results, Discussion), prose-versus-bullets rules, chart and data checks, event compliance, and independent verification of the finished deck. |
| `research` | ask for a literature review, an evidence table or a citation check, or name it | Sources, appraises and cites evidence for health and mental health services research: framing a searchable question, logging a reproducible search, screening and extracting into evidence tables, appraising design and independence, reading or running a meta-analysis, checking a measure before comparing scores, and formatting references to the journal's style. Ships `check_citations.py`. |
| `role-split` | `$role-split` | Splits a task into independent roles - builder plus at least one verifier who falsifies the result against a source the author did not write - and adds a design reviewer for visual work. Tiers: `$role-split no split` (one self-check pass), `$role-split simple` (2 roles), `$role-split complex` (up to 4). For high-stakes, externally presented work. |
| `technical-analysis` | ask about a chart, a level or an indicator, or name it | Reads a listed security's price and volume history - trend, support and resistance, moving averages, momentum and volatility, chart patterns, and the arithmetic that turns an entry and a stop into a position size. States the limits before the reading: an indicator transforms past price rather than informing, and "will it hold" has no answer. Ships `analyse.py`, `valuation.py` and an OpenD probe. |
| `wealth-advisory` | ask a planning question, or name it | Household financial planning for a Singapore-based family with Greater China exposure and a possible relocation: retirement and multi-currency projections, portfolio risk and mandate checks, CPF/SRS relief planning, protection and continuity review, and monthly mandate monitoring. Ships seventeen Python tools that take a JSON config and refuse to invent a missing number. |

## Layout

Each skill is a folder whose name matches the `name` field in its `SKILL.md` frontmatter:

```
<skill-name>/
  SKILL.md              always present, carries the name and the trigger description
  agents/openai.yaml    display name, short description and default prompt for the UI
  references/           the detail files SKILL.md points to
  scripts/              only in research, technical-analysis and wealth-advisory
```

The three skills that carry code:

- `research/scripts/` - `check_citations.py`
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

## What must never be committed here

- Household configs, statement values, account numbers, holdings or net-worth figures.
- Generated overlays such as `prices.json`, risk reports or projection output. Keep real data
  outside the repository; the skills are methods, not data.
- Any API key, token or credentials file.

The parameter file `wealth-advisory/references/sg-parameters-2026.json` is deliberately included:
it holds published Singapore tax and CPF figures with verification status, not personal data.
