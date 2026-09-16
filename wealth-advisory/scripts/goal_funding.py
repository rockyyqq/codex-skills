#!/usr/bin/env python3
"""Per-goal funding: what each goal needs a month, and whether it is on track.

A retirement probability says nothing about whether the university fees will be
there on the date they fall due. Each goal is funded and tested on its own date.

Config keys
-----------
Required:
  goals                       one block per goal
Optional:
  as_of                       today, YYYY-MM-DD
  currency                    default "SGD"
  inflate_targets             false by default; when true the target grows with
                              each goal's inflation rate to its target date

goal: {name, target_amount, target_date, current_amount,
       monthly_contribution, expected_annual_return, inflation?}

Usage:
  python goal_funding.py --config goals.json [--out report.md] [--json out.json]
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import die, emit, load_json, money, pct, require, section, table, today  # noqa: E402

MONTHS_PER_YEAR = 12


def months_between(start: date, end: date) -> int:
    return max(0, (end.year - start.year) * MONTHS_PER_YEAR + (end.month - start.month))


def future_value(current: float, monthly: float, annual_return: float, months: int) -> float:
    rate = annual_return / MONTHS_PER_YEAR
    if months <= 0:
        return current
    grown = current * ((1 + rate) ** months) if rate else current
    if rate == 0:
        return grown + monthly * months
    return grown + monthly * (((1 + rate) ** months - 1) / rate)


def required_monthly(target: float, current: float, annual_return: float, months: int) -> float:
    """The contribution that lands exactly on target. Zero when it already does."""
    if months <= 0:
        return max(0.0, target - current)
    rate = annual_return / MONTHS_PER_YEAR
    grown = current * ((1 + rate) ** months) if rate else current
    shortfall = target - grown
    if shortfall <= 0:
        return 0.0
    if rate == 0:
        return shortfall / months
    factor = ((1 + rate) ** months - 1) / rate
    return shortfall / factor


def assess(goal: dict, as_of: date, inflate_targets: bool) -> dict:
    require(goal, ["name", "target_amount", "target_date"], where="goal block")
    try:
        target_date = date.fromisoformat(str(goal["target_date"]))
    except ValueError:
        die("Goal {!r} has target_date {!r}; use YYYY-MM-DD.".format(
            goal.get("name"), goal.get("target_date")))
    months = months_between(as_of, target_date)
    target = float(goal["target_amount"])
    inflation = float(goal.get("inflation") or 0)
    if inflate_targets and inflation:
        target *= (1 + inflation) ** (months / MONTHS_PER_YEAR)
    current = float(goal.get("current_amount", 0) or 0)
    monthly = float(goal.get("monthly_contribution", 0) or 0)
    ret = float(goal.get("expected_annual_return", 0) or 0)
    projected = future_value(current, monthly, ret, months)
    needed = required_monthly(target, current, ret, months)
    delayed = months_between(as_of, date(target_date.year + 2, target_date.month, 1))
    return {
        "name": goal["name"],
        "target_date": target_date.isoformat(),
        "months": months,
        "target": target,
        "target_stated_in": "nominal, inflated to the target date" if (inflate_targets and inflation)
        else "today's dollars",
        "current": current,
        "monthly_contribution": monthly,
        "expected_annual_return": ret,
        "projected_at_target_date": projected,
        "funded_ratio": (projected / target) if target else None,
        "required_monthly": needed,
        "monthly_gap": needed - monthly,
        "required_monthly_if_delayed_two_years": required_monthly(target, current, ret, delayed),
    }


def build_report(results: list[dict], currency: str, as_of: str) -> str:
    lines = ["# Goal funding", ""]
    lines.append(
        "Each goal is tested on its own date. Basis: {}, prepared {}. Contributions are "
        "assumed to be made monthly at the end of the month; a return assumption is an "
        "assumption, so the required contribution moves when it moves.".format(currency, as_of)
    )
    lines.append("")
    lines.append(section("On-track check"))
    lines.append("")
    rows = []
    for r in results:
        ratio = r["funded_ratio"]
        status = "on track" if ratio and ratio >= 1 else "**short**"
        rows.append([
            r["name"],
            r["target_date"],
            money(r["target"]),
            money(r["projected_at_target_date"]),
            ("{:.0%}".format(ratio) if ratio is not None else "-"),
            status,
        ])
    lines.append(table(
        ["Goal", "Target date", "Target", "Projected", "Funded", "Status"], rows))
    lines.append("")
    lines.append(section("What each goal needs a month"))
    lines.append("")
    rows = []
    for r in results:
        gap = r["monthly_gap"]
        gap_text = (
            "**{}**".format(money(gap)) if gap > 0
            else ("surplus {}".format(money(-gap)) if gap < 0 else money(0))
        )
        rows.append([
            r["name"],
            money(r["monthly_contribution"]),
            money(r["required_monthly"]),
            gap_text,
            money(r["required_monthly_if_delayed_two_years"]),
        ])
    lines.append(table(
        ["Goal", "Contributing now", "Required", "Monthly gap", "If delayed two years"], rows))
    lines.append("")
    total_gap = sum(r["monthly_gap"] for r in results if r["monthly_gap"] > 0)
    total_needed = sum(r["required_monthly"] for r in results)
    lines.append(
        "The required contributions total {} a month across every goal; the shortfall on the "
        "goals that are behind is {} a month. Both are before the emergency buffer and the "
        "retirement contribution, so the three compete for the same money. Where they do not "
        "all fit, the household decides which goal moves - this script does not rank them.".format(
            money(total_needed), money(total_gap))
    )
    lines.append("")
    behind = [r for r in results if r["monthly_gap"] > 0]
    if behind:
        lines.append(section("Notes on the goals that are behind"))
        lines.append("")
        for r in behind:
            lines.append(
                "- **{}**: {} now against {} needed. A two-year delay drops the requirement "
                "to {}. The levers are the date, the target, the contribution, or the risk "
                "taken - and taking more risk to close a dated gap is the weakest of the "
                "four.".format(
                    r["name"], money(r["monthly_contribution"]),
                    money(r["required_monthly"]),
                    money(r["required_monthly_if_delayed_two_years"]),
                )
            )
        lines.append("")
    lines.append(
        "A goal whose money is needed within three years should not be carrying equity risk "
        "to reach its target; see the glide path in references/risk-mandate.md."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fund each goal on its own date.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--out")
    parser.add_argument("--json", dest="json_out")
    args = parser.parse_args()

    cfg = load_json(args.config)
    goals = cfg.get("goals")
    if not isinstance(goals, list) or not goals:
        die("Config needs a non-empty 'goals' list.")
    as_of_raw = cfg.get("as_of") or today()
    try:
        as_of = date.fromisoformat(str(as_of_raw))
    except ValueError:
        die("as_of {!r} is not YYYY-MM-DD.".format(as_of_raw))
    inflate = bool(cfg.get("inflate_targets", False))
    results = [assess(goal, as_of, inflate) for goal in goals]
    raws = {
        "as_of": as_of.isoformat(),
        "currency": cfg.get("currency", "SGD"),
        "goals": results,
        "total_required_monthly": sum(r["required_monthly"] for r in results),
        "total_monthly_gap": sum(r["monthly_gap"] for r in results if r["monthly_gap"] > 0),
    }
    emit(build_report(results, raws["currency"], as_of.isoformat()),
         out_path=args.out, raw=raws, json_path=args.json_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
