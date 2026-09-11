# Personal Codex skills

My own skills for the Codex app. Private for now - these encode working preferences and
method, not shared team standards.

## What is here

| Skill | Invoke with | What it does |
|---|---|---|
| `poster-review` | automatic on poster work, or name it | Standing requirements for conference, scientific and competition posters: PowerPoint output built from native objects, section order (Background, Methods, Participants, Results, Discussion), prose-versus-bullets rules, chart and data checks, event compliance, and independent verification of the finished deck. |
| `role-split` | `$role-split` | Splits a task into independent roles - builder plus at least one verifier who falsifies the result against a source the author did not write - and adds a design reviewer for visual work. Tiers: `$role-split no split` (one self-check pass), `$role-split simple` (2 roles), `$role-split complex` (up to 4). For high-stakes, externally presented work. |
| `wealth-advisory` | ask a planning question, or name it | Household financial planning for a Singapore-based family with Greater China exposure and a possible relocation: retirement and multi-currency projections, portfolio risk and mandate checks, CPF/SRS relief planning, protection and continuity review. Ships eight Python tools that take a JSON config and refuse to invent a missing number. |

## Layout

Each skill is a folder whose name matches the `name` field in its `SKILL.md` frontmatter:

```
poster-review/
  SKILL.md              always present, carries the name and the trigger description
  agents/openai.yaml    display name, short description and default prompt for the UI
  references/           the detail files SKILL.md points to
wealth-advisory/
  SKILL.md
  references/           method, parameters and provenance notes
  scripts/              portfolio_risk.py, plan_projection.py, rebalance.py,
                        sg_relief.py, insurance_compare.py, refresh_prices.py,
                        check_mandate.py, validate_deliverable.py
```

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
