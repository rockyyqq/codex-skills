#!/usr/bin/env python3
"""Size the protection gap: death, disability and long-term care.

The rest of this skill says protection comes before projection. This is the
script that makes that sentence arithmetic instead of an assertion.

It sizes the need against what the family would actually have to fund - income
replacement, debt, education still to come - then subtracts what already exists.
It does not price products and it does not recommend a policy: what cover costs
depends on underwriting, and recommending a specific product is licensed activity
in Singapore.

Config keys
-----------
Required:
  lives                       one block per adult whose death is being insured
Optional:
  currency                    reporting currency, default "SGD"
  disability                  {annual_income_gap, years_to_cover, existing_cover, liquid_assets}
  long_term_care              {monthly_cost, monthly_scheme_payout, years, existing_cover}

life: {name, annual_income, income_years_to_replace, outstanding_debt,
       education_costs_remaining, existing_life_cover, cpf_available,
       survivor_benefits, survivor_annual_spending}

Usage:
  python insurance_needs.py --config protection.json [--out report.md] [--json out.json]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import die, emit, money, require, section, table, today  # noqa: E402


def death_need(life: dict, currency: str) -> dict:
    require(
        life,
        ["name", "annual_income", "income_years_to_replace"],
        where="life block",
    )
    income_years = float(life.get("income_years_to_replace", 0))
    income_need = float(life["annual_income"]) * income_years
    debt = float(life.get("outstanding_debt", 0))
    education = float(life.get("education_costs_remaining", 0))
    gross_need = income_need + debt + education
    existing = (
        float(life.get("existing_life_cover", 0))
        + float(life.get("cpf_available", 0))
        + float(life.get("survivor_benefits", 0))
    )
    gap = gross_need - existing
    survivor_spending = float(life.get("survivor_annual_spending", 0))
    # What the gap means in income terms: the capital needed to fund the survivor's
    # spending, shown as a multiple rather than a product.
    years_covered_by_gap = (gap / survivor_spending) if survivor_spending > 0 else None
    return {
        "name": life["name"],
        "income_need": income_need,
        "debt": debt,
        "education": education,
        "gross_need": gross_need,
        "existing_cover": existing,
        "gap": gap,
        "survivor_annual_spending": survivor_spending,
        "gap_in_years_of_survivor_spending": years_covered_by_gap,
    }


def disability_gap(cfg: dict) -> dict | None:
    block = cfg.get("disability")
    if not block:
        return None
    require(block, ["annual_income_gap", "years_to_cover"], where="disability block")
    need = float(block["annual_income_gap"]) * float(block["years_to_cover"])
    existing = float(block.get("existing_cover", 0)) + float(block.get("liquid_assets", 0))
    return {
        "need": need,
        "existing_cover": existing,
        "gap": need - existing,
        "years_to_cover": float(block["years_to_cover"]),
        "annual_income_gap": float(block["annual_income_gap"]),
    }


def care_gap(cfg: dict) -> dict | None:
    block = cfg.get("long_term_care")
    if not block:
        return None
    require(block, ["monthly_cost", "years"], where="long_term_care block")
    monthly_net = float(block["monthly_cost"]) - float(block.get("monthly_scheme_payout", 0))
    need = monthly_net * 12 * float(block["years"])
    existing = float(block.get("existing_cover", 0))
    return {
        "monthly_net_cost": monthly_net,
        "monthly_cost": float(block["monthly_cost"]),
        "monthly_scheme_payout": float(block.get("monthly_scheme_payout", 0)),
        "need": need,
        "existing_cover": existing,
        "gap": need - existing,
        "years": float(block["years"]),
    }


def build_report(cfg: dict, result: dict) -> str:
    lines = ["# Protection gap", ""]
    lines.append(
        "Need is sized against what the family would have to fund, then reduced by what "
        "already exists. This is not a product recommendation and no premium is estimated: "
        "cost depends on underwriting. Basis: {}.".format(result["currency"])
    )
    lines.append("")
    lines.append(section("Death of a breadwinner"))
    lines.append("")
    lines.append(table(
        ["Life", "Income replacement", "Debt", "Education", "Gross need", "Existing cover", "Gap"],
        [
            [d["name"], money(d["income_need"]), money(d["debt"]), money(d["education"]),
             money(d["gross_need"]), money(d["existing_cover"]),
             ("**{}**".format(money(d["gap"])) if d["gap"] > 0 else money(d["gap"]))]
            for d in result["lives"]
        ],
    ))
    lines.append("")
    for d in result["lives"]:
        if d["gap"] > 0:
            extra = ""
            if d["gap_in_years_of_survivor_spending"] is not None:
                extra = (
                    " That gap is about {:.1f} years of the survivor's stated spending of "
                    "{}.".format(d["gap_in_years_of_survivor_spending"],
                                 money(d["survivor_annual_spending"]))
                )
            lines.append(
                "- **{} is short by {}.** Every other line in the plan assumes this gap is "
                "closed or that nothing happens; it outranks the investment section.{}".format(
                    d["name"], money(d["gap"]), extra
                )
            )
        else:
            lines.append(
                "- {} is covered on the stated figures, with {} of headroom. Re-test when "
                "income, debt or the children's schooling changes.".format(
                    d["name"], money(-d["gap"])
                )
            )
    lines.append("")
    if result["disability"]:
        d = result["disability"]
        lines.append(section("Disability - the person lives, the income stops"))
        lines.append("")
        lines.append(
            "{} a year for {} year(s) is {}, against {} of existing cover and liquid "
            "assets, leaving a gap of **{}**. This is the most commonly under-insured "
            "risk: it removes income and creates costs at the same time, and savings "
            "become the policy.".format(
                money(d["annual_income_gap"]), d["years_to_cover"], money(d["need"]),
                money(d["existing_cover"]), money(d["gap"]),
            )
        )
        lines.append("")
    if result["long_term_care"]:
        c = result["long_term_care"]
        lines.append(section("Long-term care"))
        lines.append("")
        lines.append(
            "{} a month of care against {} a month of scheme payout leaves {} a month "
            "net for {} years: {} in total, against {} of existing cover, leaving a gap "
            "of **{}**.".format(
                money(c["monthly_cost"]), money(c["monthly_scheme_payout"]),
                money(c["monthly_net_cost"]), c["years"], money(c["need"]),
                money(c["existing_cover"]), money(c["gap"]),
            )
        )
        lines.append("")
    lines.append(section("What this means for the rest of the plan"))
    lines.append("")
    lines.append(
        "If any line above shows a gap, close it or record deliberately that it is being "
        "carried. Cover is sized on need, so re-run this whenever income, debt, the number "
        "of dependants or their ages changes - and note that a policy's premium is not the "
        "need; the need is the sum assured."
    )
    lines.append("")
    lines.append("Prepared {}. Sums assured are stated in {}, not converted.".format(
        today(), result["currency"]))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Size the death, disability and care gaps.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--out")
    parser.add_argument("--json", dest="json_out")
    args = parser.parse_args()

    from common import load_json

    cfg = load_json(args.config)
    lives = cfg.get("lives")
    if not isinstance(lives, list) or not lives:
        die("Config needs a non-empty 'lives' list - one block per adult insured.")
    currency = cfg.get("currency", "SGD")
    result = {
        "currency": currency,
        "as_of": today(),
        "lives": [death_need(life, currency) for life in lives],
        "disability": disability_gap(cfg),
        "long_term_care": care_gap(cfg),
    }
    gaps = [d["gap"] for d in result["lives"] if d["gap"] > 0]
    result["any_gap"] = bool(gaps) or (
        (result["disability"] or {}).get("gap", 0) > 0
    ) or ((result["long_term_care"] or {}).get("gap", 0) > 0)
    emit(build_report(cfg, result), out_path=args.out, raw=result, json_path=args.json_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
