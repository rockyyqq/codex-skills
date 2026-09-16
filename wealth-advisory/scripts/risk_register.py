#!/usr/bin/env python3
"""The risk register: probability, impact, and what is actually being carried.

The checklist this skill is measured against asks for risks ranked by
probability x impact rather than listed. This does that ranking, and keeps the
`status` separate from the arithmetic so an unmitigated risk cannot look handled
because its expected loss happens to be small.

Config keys
-----------
Required:
  risks                       [{name, probability, impact, status?, mitigation?}]
Optional:
  currency                    default "SGD"
  material_expected_loss      the level above which a risk must be dealt with,
                              default 1000 a year

probability is a fraction between 0 and 1 per year - 1 in 50 years is 0.02.
impact is the cost in the reporting currency if the event happens.
status is one of: covered, partial, uncovered, accepted.

Usage:
  python risk_register.py --config risks.json [--out report.md] [--json out.json]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import die, emit, load_json, money, pct, require, section, table, today  # noqa: E402

VALID_STATUS = {"covered", "partial", "uncovered", "accepted"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Rank the risks that could derail the plan.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--out")
    parser.add_argument("--json", dest="json_out")
    args = parser.parse_args()

    cfg = load_json(args.config)
    risks = cfg.get("risks")
    if not isinstance(risks, list) or not risks:
        die("Config needs a non-empty 'risks' list.")
    currency = cfg.get("currency", "SGD")
    material = float(cfg.get("material_expected_loss", 1000))

    rows = []
    for risk in risks:
        require(risk, ["name", "probability", "impact"], where="risk block")
        probability = float(risk["probability"])
        if not 0 <= probability <= 1:
            die(
                "Risk {!r} has probability {}. Give a fraction between 0 and 1 per year - "
                "1 in 50 years is 0.02. A percentage here would overstate the loss by 100x.".format(
                    risk["name"], risk["probability"])
            )
        status = str(risk.get("status", "uncovered")).lower()
        if status not in VALID_STATUS:
            die("Risk {!r} has status {!r}; use one of {}.".format(
                risk["name"], risk.get("status"), ", ".join(sorted(VALID_STATUS))))
        impact = float(risk["impact"])
        rows.append({
            "name": risk["name"],
            "probability": probability,
            "impact": impact,
            "expected_loss": probability * impact,
            "status": status,
            "mitigation": risk.get("mitigation"),
            "owner": risk.get("owner"),
        })

    rows.sort(key=lambda r: -r["expected_loss"])
    total_expected = sum(r["expected_loss"] for r in rows)
    carried = [r for r in rows if r["status"] in ("uncovered", "partial")
               and r["expected_loss"] >= material]

    lines = ["# Risk register", ""]
    lines.append(
        "Expected loss = probability x impact, per year, in {}. Ranking risks this way is a "
        "way of comparing them, not a forecast: the household does not experience an average "
        "year, it experiences one outcome. Prepared {}.".format(currency, today())
    )
    lines.append("")
    lines.append(section("Ranked by expected loss"))
    lines.append("")
    lines.append(table(
        ["Risk", "Probability", "Impact if it happens", "Expected loss / year", "Status", "Mitigation"],
        [[r["name"], pct(r["probability"]), money(r["impact"]), money(r["expected_loss"]),
          r["status"], r["mitigation"] or "-"] for r in rows],
    ))
    lines.append("")
    lines.append("Total expected loss across the register: {} a year, before any mitigation "
                 "in the status column is counted.".format(money(total_expected)))
    lines.append("")
    if carried:
        lines.append(section("Being carried, not covered"))
        lines.append("")
        for r in carried:
            lines.append(
                "- **{}** - {} a year expected loss, status **{}**. {} This one is materially "
                "larger than the price of transferring it, which is the test: compare the "
                "expected loss with the cost of the cover, not the premium with zero.".format(
                    r["name"], money(r["expected_loss"]), r["status"],
                    r["mitigation"] or "No mitigation is recorded.")
            )
        lines.append("")
    else:
        lines.append(
            "No materially-sized risk is recorded as uncovered or only partly covered. "
            "Re-run this when income, dependants, debt or health changes."
        )
        lines.append("")
    lines.append(section("The order the family risks are worked in"))
    lines.append("")
    lines.append(
        "Expected loss alone can rank a rare catastrophe below a frequent annoyance. The "
        "household's own order, from references/risk-mandate.md, stays: death of a "
        "breadwinner, then disability, then job loss, then long-term care, then market "
        "losses. A risk that is small in expectation but permanent in effect sits above a "
        "larger one that is recoverable."
    )
    lines.append("")
    lines.append(
        "Every probability in this register is an assumption. Where the household cannot "
        "state one, record the range and say so in the deliverable rather than choosing a "
        "midpoint to make the table look finished."
    )
    lines.append("")

    raw = {
        "as_of": today(),
        "currency": currency,
        "risks": rows,
        "total_expected_loss": total_expected,
        "carried_above_materiality": [r["name"] for r in carried],
    }
    emit("\n".join(lines), out_path=args.out, raw=raw, json_path=args.json_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
