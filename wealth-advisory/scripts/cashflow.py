#!/usr/bin/env python3
"""Cash flow, savings rate, the emergency buffer, and idle cash.

Answers three questions the rest of the suite assumes have been answered: what is
the household actually saving, how many months would the buffer cover, and how
much cash is sitting above the buffer doing nothing.

Config keys
-----------
Required:
  income                      [{name, monthly, stability?}]
  expenses                    [{name, monthly, essential?}]
Optional:
  currency                    default "SGD"
  cash                        [{name, value, access}]  access: instant | days | locked
  buffer_months               months of spending to hold, default 12
  buffer_basis                "total" (default) or "essential"
  savings_target              target savings rate as a fraction, e.g. 0.25

Usage:
  python cashflow.py --config household.json [--out report.md] [--json out.json]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import die, emit, load_json, money, pct, section, table, today  # noqa: E402

ACCESS_RANK = {"instant": 0, "days": 1, "locked": 2}


def main() -> int:
    parser = argparse.ArgumentParser(description="Savings rate, buffer and idle cash.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--out")
    parser.add_argument("--json", dest="json_out")
    args = parser.parse_args()

    cfg = load_json(args.config)
    income_rows = cfg.get("income")
    expense_rows = cfg.get("expenses")
    if not isinstance(income_rows, list) or not income_rows:
        die("Config needs a non-empty 'income' list.")
    if not isinstance(expense_rows, list) or not expense_rows:
        die("Config needs a non-empty 'expenses' list.")

    currency = cfg.get("currency", "SGD")
    income_total = sum(float(r.get("monthly", 0) or 0) for r in income_rows)
    expense_total = sum(float(r.get("monthly", 0) or 0) for r in expense_rows)
    essential_total = sum(
        float(r.get("monthly", 0) or 0) for r in expense_rows if r.get("essential", False)
    )
    surplus = income_total - expense_total
    savings_rate = (surplus / income_total) if income_total else None

    cash_rows = cfg.get("cash") or []
    instant = sum(float(r.get("value", 0) or 0) for r in cash_rows
                  if r.get("access", "instant") == "instant")
    near = sum(float(r.get("value", 0) or 0) for r in cash_rows
               if r.get("access") in ("instant", "days"))

    basis = str(cfg.get("buffer_basis", "total")).lower()
    basis_monthly = essential_total if basis == "essential" else expense_total
    buffer_months = float(cfg.get("buffer_months", 12))
    buffer_target = basis_monthly * buffer_months

    covered_instant = (instant / basis_monthly) if basis_monthly else None
    covered_near = (near / basis_monthly) if basis_monthly else None
    excess = max(0.0, near - buffer_target)
    shortfall = max(0.0, buffer_target - near)

    target_rate = cfg.get("savings_target")
    lines = ["# Cash flow and buffer", ""]
    lines.append("Basis: monthly figures in {}, prepared {}. Spending is what the household "
                 "stated, not an estimate by this skill.".format(currency, today()))
    lines.append("")
    lines.append(section("Monthly position"))
    lines.append("")
    lines.append(table(
        ["Item", "Monthly"],
        [["Income - {}".format(r["name"]), money(float(r.get("monthly", 0) or 0))]
         for r in income_rows]
        + [["**Total income**", "**{}**".format(money(income_total))]]
        + [["Expense - {}".format(r["name"]),
            "{}{}".format(money(float(r.get("monthly", 0) or 0)),
                          "" if r.get("essential", False) else " (discretionary)")]
           for r in expense_rows]
        + [["**Total expenses**", "**{}**".format(money(expense_total))],
           ["**Surplus**", "**{}**".format(money(surplus))]],
    ))
    lines.append("")
    if surplus < 0:
        lines.append(
            "**The household is spending {} a month more than it receives.** Nothing else in "
            "the plan is funded until this is resolved, and no investment return fixes it.".format(
                money(-surplus))
        )
    else:
        lines.append(
            "Savings rate is {} of income{}.".format(
                pct(savings_rate) if savings_rate is not None else "n/a",
                "" if target_rate is None else ", against a stated target of {}".format(
                    pct(float(target_rate))),
            )
        )
    lines.append("")
    lines.append(section("Emergency buffer"))
    lines.append("")
    lines.append(
        "Buffer measured on {} spending of {} a month, held for {} months: {}.".format(
            basis, money(basis_monthly), buffer_months, money(buffer_target))
    )
    lines.append("")
    lines.append(table(
        ["Capacity", "Amount", "Covers"],
        [["Cash available instantly", money(instant),
          "{} months".format(round(covered_instant, 1)) if covered_instant is not None else "-"],
         ["Cash available within days", money(near),
          "{} months".format(round(covered_near, 1)) if covered_near is not None else "-"],
         ["Buffer target", money(buffer_target), "{} months".format(buffer_months)]],
    ))
    lines.append("")
    if shortfall > 0:
        lines.append(
            "- **The buffer is short by {}.** A household that has to sell assets in a bad "
            "market to fund ordinary spending has turned a temporary fall into a permanent "
            "one.".format(money(shortfall))
        )
    if excess > 0:
        lines.append(
            "- **{} sits above the buffer.** It is not invested, so it earns the deposit rate "
            "while carrying the household's inflation risk. The decision is where it belongs "
            "- buffer top-up, debt repayment, or the portfolio - and that decision belongs to "
            "the household.".format(money(excess))
        )
    if shortfall == 0 and excess == 0:
        lines.append("- The buffer is funded to its stated target, with no excess cash.")
    lines.append("")
    locked = sum(float(r.get("value", 0) or 0) for r in cash_rows if r.get("access") == "locked")
    if locked:
        lines.append(
            "{} is recorded as locked and is excluded from every buffer figure above: it "
            "cannot be spent on the day it is needed.".format(money(locked))
        )
        lines.append("")
    lines.append(section("What this does not say"))
    lines.append("")
    lines.append(
        "It does not say the surplus should be invested, and it does not rank the goals that "
        "compete for it. It also takes the income figure as stated: variable or bonus income "
        "should be entered at a level the household would rely on in a bad year, and the "
        "difference treated as upside."
    )
    lines.append("")

    raw = {
        "as_of": today(),
        "currency": currency,
        "income_monthly": income_total,
        "expenses_monthly": expense_total,
        "essential_monthly": essential_total,
        "surplus_monthly": surplus,
        "savings_rate": savings_rate,
        "cash_instant": instant,
        "cash_within_days": near,
        "buffer_target": buffer_target,
        "buffer_shortfall": shortfall,
        "excess_cash": excess,
        "buffer_months_basis": basis,
    }
    emit("\n".join(lines), out_path=args.out, raw=raw, json_path=args.json_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
