#!/usr/bin/env python3
"""Debt: the amortisation, the cost of carrying it, and pay-down versus invest.

Debt is the one lever that beats the portfolio on a risk-adjusted basis when its
rate is high, and it is the input most often left as a sentence in a plan. This
script makes the arithmetic explicit.

Two rules it enforces rather than assumes:

  * A payment below the monthly interest does not amortise. It is reported, not
    projected silently into a 100-year schedule.
  * Repaying debt is a guaranteed, after-tax saving at the loan rate. Investing
    the same money is an uncertain return at the assumed rate. The comparison
    states both, and names the rate at which they break even.

Config keys
-----------
Required:
  loans                       [{name, balance, annual_rate, monthly_payment}]
Optional:
  currency                    default "SGD"
  extra_monthly               extra applied to the highest-rate loan, default 0
  invest_expected_return      expected annual return on the money instead, e.g. 0.05
  invest_tax_rate             tax on that return, default 0
  horizon_years               comparison horizon, default the loan's own life

Usage:
  python debt.py --config household.json [--out report.md] [--json out.json]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import die, emit, load_json, money, money2, pct, require, section, table, today  # noqa: E402

MAX_MONTHS = 1200


def amortise(balance: float, annual_rate: float, payment: float, extra: float = 0.0) -> dict:
    """Month-by-month amortisation. Never projects past MAX_MONTHS to hide a bad input."""
    monthly_rate = annual_rate / 12.0
    total_payment = payment + extra
    if total_payment <= balance * monthly_rate:
        return {
            "amortises": False,
            "reason": (
                "a payment of {} does not cover the {} of monthly interest on {}, so the "
                "balance never falls".format(money2(total_payment),
                                             money2(balance * monthly_rate), money(balance))
            ),
        }
    remaining = balance
    interest_paid = 0.0
    months = 0
    first_year_interest = 0.0
    while remaining > 0 and months < MAX_MONTHS:
        interest = remaining * monthly_rate
        principal = min(total_payment - interest, remaining)
        remaining -= principal
        interest_paid += interest
        months += 1
        if months <= 12:
            first_year_interest += interest
    return {
        "amortises": True,
        "months": months,
        "years": round(months / 12.0, 1),
        "interest_paid": interest_paid,
        "first_year_interest": first_year_interest,
        "monthly_payment": total_payment,
        "total_paid": balance + interest_paid,
        "capped": months >= MAX_MONTHS,
    }


def future_value_of_series(monthly: float, annual_return: float, months: int) -> float:
    monthly_rate = annual_return / 12.0
    if monthly_rate == 0:
        return monthly * months
    return monthly * (((1 + monthly_rate) ** months - 1) / monthly_rate)


def main() -> int:
    parser = argparse.ArgumentParser(description="Amortisation and pay-down versus invest.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--out")
    parser.add_argument("--json", dest="json_out")
    args = parser.parse_args()

    cfg = load_json(args.config)
    currency = cfg.get("currency", "SGD")
    loans = cfg.get("loans") or (cfg.get("portfolio") or {}).get("loans")
    if not isinstance(loans, list) or not loans:
        die("Config needs a non-empty 'loans' list: name, balance, annual_rate, monthly_payment.")
    for loan in loans:
        require(loan, ["name", "balance", "annual_rate", "monthly_payment"], where="loan block")

    extra = float(cfg.get("extra_monthly", 0) or 0)
    ordered = sorted(loans, key=lambda l: -float(l["annual_rate"]))
    results = []
    for index, loan in enumerate(ordered):
        base = amortise(float(loan["balance"]), float(loan["annual_rate"]), float(loan["monthly_payment"]))
        with_extra = (
            amortise(float(loan["balance"]), float(loan["annual_rate"]),
                     float(loan["monthly_payment"]), extra if index == 0 else 0.0)
            if extra else None
        )
        results.append({"loan": loan, "base": base, "with_extra": with_extra})

    invest_return = cfg.get("invest_expected_return")
    tax_rate = float(cfg.get("invest_tax_rate", 0) or 0)
    comparison = None
    if invest_return is not None and extra:
        top = results[0]
        months = (top["with_extra"] or top["base"]).get("months") or 0
        base_months = top["base"].get("months") or months
        horizon = int(float(cfg.get("horizon_years", 0)) * 12) or base_months
        after_tax = float(invest_return) * (1 - tax_rate)
        invested = future_value_of_series(extra, after_tax, horizon)
        interest_saved = top["base"]["interest_paid"] - top["with_extra"]["interest_paid"]
        comparison = {
            "loan": top["loan"]["name"],
            "extra_monthly": extra,
            "horizon_months": horizon,
            "loan_rate": float(top["loan"]["annual_rate"]),
            "after_tax_invest_return": after_tax,
            "interest_saved_by_repaying": interest_saved,
            "value_if_invested": invested,
            "advantage": invested - interest_saved,
            "invest_wins_on_expectation": invested > interest_saved,
            "breakeven_return": float(top["loan"]["annual_rate"]) / (1 - tax_rate)
            if tax_rate < 1
            else None,
        }

    lines = ["# Debt position", ""]
    lines.append(
        "Basis: {} nominal, payments as given, no early-repayment penalty modelled. "
        "Prepared {}.".format(currency, today())
    )
    lines.append("")
    lines.append(section("Loans, highest rate first"))
    lines.append("")
    rows = []
    for item in results:
        loan, base = item["loan"], item["base"]
        if not base.get("amortises"):
            rows.append([loan["name"], money(loan["balance"]), pct(float(loan["annual_rate"])),
                         money(loan["monthly_payment"]), "**does not amortise**", "-"])
            continue
        rows.append([
            loan["name"], money(loan["balance"]), pct(float(loan["annual_rate"])),
            money(loan["monthly_payment"]), "{} yr".format(base["years"]),
            money(base["interest_paid"]),
        ])
    lines.append(table(["Loan", "Balance", "Rate", "Monthly payment", "Paid off in", "Interest paid"], rows))
    lines.append("")
    for item in results:
        if not item["base"].get("amortises"):
            lines.append("- **{}: {}.** Fix the payment before planning anything with this "
                         "loan in it.".format(item["loan"]["name"], item["base"]["reason"]))
    lines.append("")
    if extra:
        lines.append(section("Extra {} a month, applied to the highest-rate loan".format(money(extra))))
        lines.append("")
        rows = []
        for item in results:
            if not item["base"].get("amortises") or not item["with_extra"]:
                continue
            rows.append([
                item["loan"]["name"],
                "{} -> {}".format(item["base"]["years"], item["with_extra"]["years"]),
                money(item["base"]["interest_paid"] - item["with_extra"]["interest_paid"]),
            ])
        lines.append(table(["Loan", "Years to clear", "Interest saved"], rows))
        lines.append("")
    if comparison:
        lines.append(section("Repay or invest the same {}?".format(money(extra))))
        lines.append("")
        lines.append(
            "Over {} months, repaying {} at {} saves {} of interest **with certainty** - it is "
            "a guaranteed, after-tax return at the loan rate. Investing the same amount at an "
            "assumed {:.2f}% after tax grows to {} on expectation, a difference of {}. The "
            "hurdle the investment must beat is {:.2f}%: the loan rate, not zero.".format(
                comparison["horizon_months"], comparison["loan"],
                pct(comparison["loan_rate"]),
                money(comparison["interest_saved_by_repaying"]),
                comparison["after_tax_invest_return"] * 100,
                money(comparison["value_if_invested"]),
                money(comparison["advantage"]),
                (comparison["breakeven_return"] or 0) * 100,
            )
        )
        lines.append("")
        lines.append(
            "The two are not equally risky. The repayment is a certain saving; the "
            "investment is an assumption with a range. Where the assumed return is close to "
            "the loan rate, the repayment is the better trade even when the arithmetic "
            "favours investing."
        )
        lines.append("")
    lines.append(section("Before this goes into the plan"))
    lines.append("")
    lines.append(
        "Check the rate type (fixed or floating), the lock-in and any early-repayment "
        "penalty, and whether any loan is secured against an asset already counted "
        "elsewhere. A guarantee given for someone else's debt belongs in the plan as a "
        "contingent liability, not as a footnote."
    )
    lines.append("")

    raw = {"as_of": today(), "currency": currency, "loans": results, "comparison": comparison}
    emit("\n".join(lines), out_path=args.out, raw=raw, json_path=args.json_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
