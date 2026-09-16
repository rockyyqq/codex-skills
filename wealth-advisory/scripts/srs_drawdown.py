#!/usr/bin/env python3
"""The SRS ten-year drawdown schedule.

Every plan with an SRS balance needs this schedule, because the risk with SRS is
not withdrawing too early - it is never withdrawing. The window is a deadline:
at the end of the tenth year the balance is deemed withdrawn and half of it is
taxed in one hit.

This applies the rules from references/singapore-tax-and-accounts.md:

  * 50% of a qualifying withdrawal is taxable, spread over a ten-year window
  * the prescribed retirement age is the statutory retirement age at the time of
    the member's FIRST contribution, not today's - so it is derived from the
    first-contribution date, never read off the current value
  * a non-resident gets withholding instead of the progressive scale and no reliefs
  * the balance left at the end of the window is deemed withdrawn

Config keys
-----------
Required:
  srs_balance
Optional:
  first_withdrawal_year       default: next year
  annual_withdrawal           default: the maximum that is tax-free on the stated facts
  other_taxable_income        default 0
  other_reliefs               default 0
  tax_resident                default true
  first_contribution_date     needed to derive the prescribed retirement age
  death_or_terminal_illness_year   tests the exemption path instead of withdrawal
  params                      path to the parameter file

Usage:
  python srs_drawdown.py --config srs.json [--out report.md] [--json out.json]
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import die, emit, load_json, money, pct, section, table, today  # noqa: E402
import sg_relief  # noqa: E402  - one implementation of the tax brackets, not two

NIL_RATE_BAND = 20000.0


def prescribed_age(first_contribution: str | None, params: dict) -> dict:
    """The statutory retirement age at the member's first contribution, not today's."""
    schedule = (params.get("srs_prescribed_retirement_age_schedule") or {}).get("value")
    entry = params.get("statutory_retirement_age") or {}
    if not schedule:
        return {
            "age": entry.get("value"),
            "basis": "current statutory retirement age from the parameter file",
            "derived": False,
            "note": "The parameter file has no schedule keyed by first-contribution date; "
                    "the current value is shown, and it may not be the member's age.",
        }
    if not first_contribution:
        return {
            "age": None,
            "basis": "first_contribution_date not supplied",
            "derived": False,
            "note": "The age to plan against depends on when the first contribution was "
                    "made, so it cannot be read from the current statutory age.",
        }
    try:
        when = date.fromisoformat(str(first_contribution))
    except ValueError:
        return {"age": None, "basis": "first_contribution_date is not YYYY-MM-DD",
                "derived": False, "note": None}
    chosen = None
    for row in sorted(schedule, key=lambda r: r["from"]):
        if when >= date.fromisoformat(row["from"]):
            chosen = row
    if not chosen:
        return {"age": None, "basis": "no schedule row covers this date", "derived": False,
                "note": None}
    return {
        "age": chosen["statutory_retirement_age"],
        "basis": "first contribution on {} falls in the band from {}".format(
            when.isoformat(), chosen["from"]),
        "derived": True,
        "note": "Later increases in the statutory age do not change this member's "
                "prescribed retirement age.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="The SRS ten-year drawdown schedule.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--out")
    parser.add_argument("--json", dest="json_out")
    args = parser.parse_args()

    cfg = load_json(args.config)
    if "srs_balance" not in cfg:
        die("Config needs srs_balance.")

    params = sg_relief.load_params(cfg.get("params", sg_relief.DEFAULT_PARAMS))
    brackets = params["income_tax_brackets_resident_individual"]["value"]
    window = int(params["srs_withdrawal_window_years"]["value"])
    taxable_fraction = float(params["srs_taxable_fraction_on_qualifying_withdrawal"]["value"])
    exemption_cap = float(params["srs_full_withdrawal_exemption_terminal_illness_or_death"]["value"])

    balance = float(cfg["srs_balance"])
    other_income = float(cfg.get("other_taxable_income", 0) or 0)
    reliefs = float(cfg.get("other_reliefs", 0) or 0)
    resident = bool(cfg.get("tax_resident", True))
    start_year = int(cfg.get("first_withdrawal_year", date.today().year + 1))

    tax_free_capacity = max(
        0.0,
        (NIL_RATE_BAND + reliefs - other_income) / taxable_fraction,
    )
    annual = float(cfg.get("annual_withdrawal", tax_free_capacity))
    age = prescribed_age(cfg.get("first_contribution_date"), params)

    def tax_on_income(total_chargeable: float) -> float:
        return sg_relief.tax_on(max(0.0, total_chargeable), brackets)

    baseline = tax_on_income(other_income - reliefs)
    rows = []
    if resident:
        for year_index in range(window):
            if balance <= 0:
                break
            gross = min(annual, balance)
            taxable = gross * taxable_fraction
            tax = tax_on_income(other_income + taxable - reliefs) - baseline
            balance -= gross
            rows.append({
                "year": start_year + year_index,
                "year_index": year_index + 1,
                "withdrawal": gross,
                "taxable": taxable,
                "tax": tax,
                "balance_after": balance,
                "deemed": False,
            })
        deemed = None
        if balance > 0:
            taxable = balance * taxable_fraction
            tax = tax_on_income(other_income + taxable - reliefs) - baseline
            deemed = {
                "year": start_year + window - 1,
                "withdrawal": balance,
                "taxable": taxable,
                "tax": tax,
            }
            rows.append({
                "year": start_year + window - 1,
                "year_index": window,
                "withdrawal": balance,
                "taxable": taxable,
                "tax": tax,
                "balance_after": 0.0,
                "deemed": True,
            })
            balance = 0.0
        total_tax = sum(r["tax"] for r in rows)
        total_withdrawn = sum(r["withdrawal"] for r in rows)
    else:
        withholding = params["withholding_tax_non_resident_individuals"]["value"]
        rate = float(withholding["srs_withdrawals_by_non_singapore_srs_account_holders"])
        concession = float(withholding["srs_withdrawals_concessionary_rate"])
        applied = concession if (other_income == 0 and annual <= 200000) else rate
        total_tax = 0.0
        total_withdrawn = 0.0
        for year_index in range(window):
            if balance <= 0:
                break
            gross = min(annual, balance)
            tax = gross * applied
            balance -= gross
            total_tax += tax
            total_withdrawn += gross
            rows.append({
                "year": start_year + year_index,
                "year_index": year_index + 1,
                "withdrawal": gross,
                "taxable": gross,
                "tax": tax,
                "balance_after": balance,
                "deemed": False,
            })
        deemed = None
        if balance > 0:
            tax = balance * applied
            rows.append({
                "year": start_year + window - 1,
                "year_index": window,
                "withdrawal": balance,
                "taxable": balance,
                "tax": tax,
                "balance_after": 0.0,
                "deemed": True,
            })
            total_tax += tax
            total_withdrawn += balance
            deemed = {"year": start_year + window - 1, "withdrawal": balance,
                      "taxable": balance, "tax": tax}
            balance = 0.0

    death_test = None
    if cfg.get("death_or_terminal_illness_year"):
        prior = sum(r["withdrawal"] for r in rows
                    if r["year"] < int(cfg["death_or_terminal_illness_year"]))
        adjusted = max(0.0, exemption_cap - prior)
        excess = max(0.0, float(cfg["srs_balance"]) - adjusted)
        death_test = {
            "year": int(cfg["death_or_terminal_illness_year"]),
            "prior_penalty_free_withdrawals": prior,
            "adjusted_exemption": adjusted,
            "taxable_excess": excess * taxable_fraction,
            "tax": tax_on_income(other_income + excess * taxable_fraction - reliefs) - baseline,
            "note": "The exemption is also reduced by the years already used in the window. "
                    "That second reduction is not modelled here - confirm the current "
                    "treatment with the SRS operator before relying on this figure.",
        }

    lines = ["# SRS drawdown", ""]
    lines.append(
        "Basis: {} of SRS at the start, {} taxable on a qualifying withdrawal, a {}-year "
        "window, prepared {}. Other taxable income of {} and reliefs of {} are held constant "
        "across the schedule; changing either changes the schedule.".format(
            money(float(cfg["srs_balance"])), pct(taxable_fraction), window, today(),
            money(other_income), money(reliefs),
        )
    )
    lines.append("")
    if age["derived"]:
        lines.append(
            "Prescribed retirement age: **{}**, derived from the first contribution "
            "({}).".format(age["age"], age["basis"])
        )
    else:
        lines.append("Prescribed retirement age: **not derived**. {}".format(age["note"] or age["basis"]))
    lines.append("")
    lines.append(section("The schedule"))
    lines.append("")
    lines.append(table(
        ["Year", "Withdrawal", "Taxable (50%)", "Tax", "Balance after"],
        [[("{}{}".format(r["year"], " (deemed)" if r["deemed"] else "")),
          money(r["withdrawal"]),
          money(r["taxable"]) if resident else money(r["taxable"]),
          money(r["tax"]),
          money(r["balance_after"])] for r in rows],
    ))
    lines.append("")
    lines.append(
        "Total withdrawn {} against {} of tax, an effective rate of {}. Two years at the start "
        "and end of the window are shown as the schedule's shape, not as advice: the household "
        "decides the pace, this shows what each pace costs.".format(
            money(total_withdrawn), money(total_tax),
            pct(total_tax / total_withdrawn) if total_withdrawn else "n/a",
        )
    )
    lines.append("")
    lines.append(section("What the schedule is telling you"))
    lines.append("")
    if resident:
        lines.append(
            "- The tax-free capacity this year is about {} on the stated facts: half of the "
            "withdrawal is taxable, and the first {} of chargeable income is taxed at nil. "
            "Other income and other reliefs move this figure, so it is recomputed from the "
            "config, not assumed.".format(money(tax_free_capacity), money(NIL_RATE_BAND))
        )
    if deemed:
        lines.append(
            "- **{} is deemed withdrawn in {} and taxed in one hit.** The withdrawal pace "
            "above leaves that much in the account at the end of the window. Spreading it "
            "over the full window costs less than leaving it to be taxed at the end.".format(
                money(deemed["withdrawal"]), deemed["year"])
        )
    else:
        lines.append("- The stated pace empties the account inside the window.")
    lines.append("- Contribute-once, withdraw-once is the expensive shape: the contribution "
                 "saved tax at the marginal rate, and a late concentrated withdrawal can be "
                 "taxed at a similar rate, having locked the money up for decades.")
    lines.append("")
    if death_test:
        lines.append(section("On death or terminal illness"))
        lines.append("")
        lines.append(
            "The full withdrawal is exempt up to {} reduced by prior penalty-free withdrawals "
            "of {}, leaving {}. Half of the excess, {}, is taxable, giving {} of tax. {}".format(
                money(exemption_cap), money(death_test["prior_penalty_free_withdrawals"]),
                money(death_test["adjusted_exemption"]),
                money(death_test["taxable_excess"]), money(death_test["tax"]),
                death_test["note"],
            )
        )
        lines.append("")
    lines.append(section("Before this goes into the plan"))
    lines.append("")
    lines.append(
        "Re-derive the schedule if income, reliefs, residency or the balance changes, and "
        "check the pace against the ten-year deadline rather than against a withdrawal rate "
        "chosen for the portfolio. SRS has no beneficiary nomination: the balance forms part "
        "of the estate and the will governs it, so the drawdown schedule and the will have to "
        "agree."
    )
    lines.append("")

    raw = {
        "as_of": today(),
        "params_used": str(cfg.get("params", sg_relief.DEFAULT_PARAMS)),
        "prescribed_retirement_age": age,
        "tax_free_capacity_this_year": tax_free_capacity,
        "schedule": rows,
        "total_withdrawn": total_withdrawn,
        "total_tax": total_tax,
        "deemed_withdrawal": deemed,
        "death_or_terminal_illness": death_test,
    }
    emit("\n".join(lines), out_path=args.out, raw=raw, json_path=args.json_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
