#!/usr/bin/env python3
"""Retirement and cash-flow projection.

Deterministic accumulation and drawdown, plus a Monte Carlo estimate of whether
the money lasts, plus the maximum sustainable spending for a target confidence
level. Every assumption comes from the JSON config. A missing assumption is an
error, never a default.

Works in nominal dollars. Spending is stated in today's dollars in the config
and inflated from the current age, so the report is nominal and says so.

Config keys
-----------
Required:
  current_age, retirement_age, plan_to_age, start_balance, annual_savings,
  savings_growth, annual_spending_retirement_today_dollars, inflation,
  expected_return, volatility, fee_rate
Optional:
  label, currency, other_income, monte_carlo, stress, spending_steps, one_off_shocks

spending_steps - permanent changes in spending at a given age, e.g. a relocation
  that lowers living costs:  [{"at_age": 51, "multiplier": 0.75, "label": "Move to China"}]
savings_steps - permanent changes in the annual savings amount from a given age,
  e.g. a car that is scrapped and never replaced, freeing the instalment and
  running costs:  [{"at_age": 43, "multiplier": 1.28, "label": "Car scrapped"}]
  The multiplier applies to the escalated savings amount, so the freed money is
  assumed to grow with income. Say so in the plan.
one_off_shocks - a single-year hit to the portfolio, e.g. an adverse currency
  move or a market shock:  [{"at_age": 51, "portfolio_return": -0.12, "label": "SGD strengthens against RMB"}]
  These are applied after the year's normal return. Modelling currency this way
  keeps the projection in one reporting currency; say so in the plan.

other_income entry:
  {"name": str, "start_age": int, "annual": float,
   "amount_basis": "today_dollars" | "nominal"}
  "today_dollars" escalates with inflation from the current age; "nominal" is a
  fixed nominal amount from start_age (the usual treatment for a CPF LIFE payout
  quoted today).

Usage:
  python plan_projection.py --config case.json [--out report.md] [--json out.json]
"""

import argparse
import json
import math
import random
import sys
from pathlib import Path

REQUIRED = [
    "current_age",
    "retirement_age",
    "plan_to_age",
    "start_balance",
    "annual_savings",
    "savings_growth",
    "annual_spending_retirement_today_dollars",
    "inflation",
    "expected_return",
    "volatility",
    "fee_rate",
]

DEFAULT_RUNS = 10000
DEFAULT_TARGET_SUCCESS = 0.85
MIN_NET_RETURN = -0.999


def die(message):
    sys.stderr.write(message.rstrip() + "\n")
    sys.exit(2)


def load_config(path):
    if not Path(path).exists():
        die("Config file not found: {}".format(path))
    with open(path, "r", encoding="utf-8") as handle:
        try:
            return json.load(handle)
        except json.JSONDecodeError as exc:
            die("Config file {} is not valid JSON: {}".format(path, exc))


def require(cfg):
    missing = [k for k in REQUIRED if k not in cfg]
    if missing:
        die(
            "Missing required assumption(s):\n"
            + "".join("  - {}\n".format(k) for k in missing)
            + "\nThe projection will not substitute defaults for these. Supply them, "
            "or run the range explicitly and say so in the report."
        )
    if cfg["retirement_age"] < cfg["current_age"]:
        die("retirement_age ({}) is before current_age ({}).".format(cfg["retirement_age"], cfg["current_age"]))
    if cfg["plan_to_age"] < cfg["retirement_age"]:
        die("plan_to_age ({}) is before retirement_age ({}).".format(cfg["plan_to_age"], cfg["retirement_age"]))
    for src in cfg.get("other_income", []):
        basis = src.get("amount_basis", "")
        if basis not in ("today_dollars", "nominal"):
            die(
                "other_income entry {!r} needs amount_basis 'today_dollars' or "
                "'nominal'.".format(src.get("name", "?"))
            )
    for step in cfg.get("spending_steps", []):
        if "at_age" not in step or "multiplier" not in step:
            die("Every spending_steps entry needs at_age and multiplier.")
        if float(step["multiplier"]) <= 0:
            die("spending_steps multiplier must be positive.")
    for step in cfg.get("savings_steps", []):
        if "at_age" not in step or "multiplier" not in step:
            die("Every savings_steps entry needs at_age and multiplier.")
        if float(step["multiplier"]) <= 0:
            die("savings_steps multiplier must be positive.")
    for shock in cfg.get("one_off_shocks", []):
        if "at_age" not in shock:
            die("Every one_off_shocks entry needs at_age.")
        if float(shock.get("portfolio_return", 0.0)) <= -1.0:
            die("one_off_shocks portfolio_return cannot be -100% or worse.")


def spending_multiplier(steps, age):
    factor = 1.0
    for step in steps:
        if age >= step["at_age"]:
            factor *= float(step["multiplier"])
    return factor


def savings_multiplier(steps, age):
    """Permanent change in the annual savings amount from a given age."""
    factor = 1.0
    for step in steps:
        if age >= step["at_age"]:
            factor *= float(step["multiplier"])
    return factor


def shock_at(shocks, age):
    return sum(float(s.get("portfolio_return", 0.0)) for s in shocks if s["at_age"] == age)


def income_at(sources, age, current_age, inflation):
    total = 0.0
    for src in sources:
        if age < src["start_age"]:
            continue
        if src["amount_basis"] == "today_dollars":
            total += src["annual"] * (1.0 + inflation) ** (age - current_age)
        else:
            total += src["annual"]
    return total


def simulate(cfg, runs, seed, spending=None, inflation=None, end_age=None,
             bad_decade=None, volatility=None):
    """Return per-run outcomes. spending is the retirement spending in today's dollars."""
    cur = cfg["current_age"]
    ret = cfg["retirement_age"]
    end = cfg["plan_to_age"] if end_age is None else end_age
    savings = cfg["annual_savings"]
    growth = cfg["savings_growth"]
    spend0 = cfg["annual_spending_retirement_today_dollars"] if spending is None else spending
    inf = cfg["inflation"] if inflation is None else inflation
    mu = cfg["expected_return"]
    sig = cfg["volatility"] if volatility is None else volatility
    fee = cfg["fee_rate"]
    sources = cfg.get("other_income", [])
    steps = cfg.get("spending_steps", [])
    save_steps = cfg.get("savings_steps", [])
    shocks = cfg.get("one_off_shocks", [])

    acc_years = max(0, ret - cur)
    outcomes = []

    for run in range(runs):
        rng = random.Random(seed + run)
        balance = float(cfg["start_balance"])
        depleted_age = None

        for year in range(acc_years):
            age = cur + year
            net = mu + sig * rng.gauss(0.0, 1.0) - fee
            net = max(net, MIN_NET_RETURN)
            contribution = savings * (1.0 + growth) ** year * savings_multiplier(save_steps, age)
            balance = balance * (1.0 + net) + contribution
            balance *= 1.0 + shock_at(shocks, age)
            if balance < 0.0:
                balance = 0.0
        balance_at_retirement = balance

        for year, age in enumerate(range(ret, end + 1)):
            spend = spend0 * (1.0 + inf) ** (age - cur) * spending_multiplier(steps, age)
            need = spend - income_at(sources, age, cur, inf)
            if need > 0.0:
                balance -= need
            if balance <= 0.0:
                balance = 0.0
                depleted_age = age
                break
            net = mu + sig * rng.gauss(0.0, 1.0) - fee
            if bad_decade and year < bad_decade["years"]:
                net = bad_decade["annual_return"] - fee
            net = max(net, MIN_NET_RETURN)
            balance *= 1.0 + net
            balance *= 1.0 + shock_at(shocks, age)
            if balance < 0.0:
                balance = 0.0

        outcomes.append(
            {
                "balance_at_retirement": balance_at_retirement,
                "terminal_balance": balance,
                "depleted_age": depleted_age,
            }
        )
    return outcomes


def summarise(outcomes):
    failures = [o for o in outcomes if o["depleted_age"] is not None]
    terminals = sorted(o["terminal_balance"] for o in outcomes)
    at_retirement = sorted(o["balance_at_retirement"] for o in outcomes)
    depletion_ages = sorted(o["depleted_age"] for o in failures)
    return {
        "runs": len(outcomes),
        "success_probability": 1.0 - len(failures) / len(outcomes),
        "median_at_retirement": percentile(at_retirement, 0.5),
        "median_terminal": percentile(terminals, 0.5),
        "p5_terminal": percentile(terminals, 0.05),
        "p95_terminal": percentile(terminals, 0.95),
        "median_depletion_age": percentile([float(a) for a in depletion_ages], 0.5) if depletion_ages else None,
        "earliest_depletion_age": depletion_ages[0] if depletion_ages else None,
    }


def percentile(sorted_values, p):
    if not sorted_values:
        return None
    k = (len(sorted_values) - 1) * p
    lo = int(math.floor(k))
    hi = int(math.ceil(k))
    if lo == hi:
        return sorted_values[lo]
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (k - lo)


def sustainable_spending(cfg, runs, seed, target, end_age=None):
    """Bisect the retirement spending level that hits the target success rate."""
    lo, hi = 0.0, cfg["annual_spending_retirement_today_dollars"] * 3.0
    for _ in range(16):
        mid = (lo + hi) / 2.0
        outcomes = simulate(cfg, runs, seed, spending=mid, end_age=end_age)
        rate = 1.0 - sum(1 for o in outcomes if o["depleted_age"] is not None) / len(outcomes)
        if rate >= target:
            lo = mid
        else:
            hi = mid
    return lo


def money(value, currency):
    if value is None:
        return "n/a"
    return "{} {:,.0f}".format(currency, value)


def pct(value):
    return "n/a" if value is None else "{:.1f}%".format(value * 100.0)


def build_report(cfg, currency, mc, det, scenarios, max_spend, max_spend_rate, target):
    label = cfg.get("label", "Projection")
    lines = []
    add = lines.append

    add("# Retirement projection - {}".format(label))
    add("")
    add(
        "Nominal dollars in {}. Spending is stated in today's dollars and inflated from age {} "
        "at {}. Returns are quoted before the {:.2f}% annual cost assumption, which is deducted "
        "in every run.".format(currency, cfg["current_age"], pct(cfg["inflation"]), cfg["fee_rate"] * 100.0)
    )
    add("")
    add("## Inputs")
    add("")
    add("| Assumption | Value |")
    add("|---|---|")
    add("| Current age | {} |".format(cfg["current_age"]))
    add("| Retirement age | {} |".format(cfg["retirement_age"]))
    add("| Planning to age | {} |".format(cfg["plan_to_age"]))
    add("| Starting portfolio | {} |".format(money(cfg["start_balance"], currency)))
    add("| Annual savings until retirement | {} |".format(money(cfg["annual_savings"], currency)))
    add("| Savings growth | {} |".format(pct(cfg["savings_growth"])))
    add("| Retirement spending (today's dollars) | {} |".format(money(cfg["annual_spending_retirement_today_dollars"], currency)))
    add("| Inflation | {} |".format(pct(cfg["inflation"])))
    add("| Expected return | {} |".format(pct(cfg["expected_return"])))
    add("| Volatility | {} |".format(pct(cfg["volatility"])))
    add("| Annual cost drag | {} |".format(pct(cfg["fee_rate"])))
    for src in cfg.get("other_income", []):
        add(
            "| Income: {} from age {} | {} ({}) |".format(
                src["name"], src["start_age"], money(src["annual"], currency), src["amount_basis"]
            )
        )
    add("")

    if cfg.get("spending_steps") or cfg.get("one_off_shocks") or cfg.get("savings_steps"):
        add("## Phase changes modelled")
        add("")
        add("| Age | Change | Effect |")
        add("|---|---|---|")
        for step in cfg.get("spending_steps", []):
            add(
                "| {} | {} | Spending x{:.2f} from this age |".format(
                    step["at_age"], step.get("label", "Spending change"), float(step["multiplier"])
                )
            )
        for step in cfg.get("savings_steps", []):
            add(
                "| {} | {} | Annual savings x{:.2f} from this age |".format(
                    step["at_age"], step.get("label", "Savings change"), float(step["multiplier"])
                )
            )
        for shock in cfg.get("one_off_shocks", []):
            value = float(shock.get("portfolio_return", 0.0))
            add(
                "| {} | {} | One-off {} to the portfolio |".format(
                    shock["at_age"], shock.get("label", "Portfolio shock"), pct(value)
                )
            )
        add("")
        add(
            "A currency move is modelled as a one-off hit to the portfolio rather than as a "
            "second currency, so the projection stays in one reporting currency. State that "
            "simplification in the plan."
        )
        add("")

    add("## Deterministic path")
    add("")
    add("| Metric | Value |")
    add("|---|---|")
    add("| Portfolio at retirement | {} |".format(money(det["balance_at_retirement"], currency)))
    add("| Spending in the first retirement year | {} |".format(money(det["first_year_spending"], currency)))
    add(
        "| Income from other sources in year one | {} |".format(
            money(det["first_year_income"], currency)
        )
    )
    add(
        "| Drawn from the portfolio in year one | {} |".format(
            money(det["first_year_withdrawal"], currency)
        )
    )
    add("| First-year withdrawal rate, net of other income | {} |".format(pct(det["first_year_withdrawal_rate"])))
    add("| Portfolio at age {} | {} |".format(cfg["plan_to_age"], money(det["terminal_balance"], currency)))
    add("")
    add(
        "The deterministic path uses the expected return in every year. It is the path that "
        "never happens - its only use is as a reference point. Read the Monte Carlo section instead."
    )
    add("")

    add("## Monte Carlo - {} runs".format(mc["runs"]))
    add("")
    add("| Metric | Value |")
    add("|---|---|")
    add("| Probability the money lasts to age {} | {} |".format(cfg["plan_to_age"], pct(mc["success_probability"])))
    add("| Portfolio at retirement (median) | {} |".format(money(mc["median_at_retirement"], currency)))
    add("| Portfolio at age {} (median) | {} |".format(cfg["plan_to_age"], money(mc["median_terminal"], currency)))
    add("| Portfolio at age {} (5th percentile) | {} |".format(cfg["plan_to_age"], money(mc["p5_terminal"], currency)))
    add("| Portfolio at age {} (95th percentile) | {} |".format(cfg["plan_to_age"], money(mc["p95_terminal"], currency)))
    if mc["median_depletion_age"] is not None:
        add("| Median age at which failing paths run out | {:.0f} |".format(mc["median_depletion_age"]))
        add("| Earliest age at which any path runs out | {} |".format(mc["earliest_depletion_age"]))
    add("")
    add(
        "A probability of success is a model output conditional on the assumptions above, not a "
        "forecast. It excludes anything the model does not contain: a care event, a market that "
        "behaves unlike the assumed distribution, or a change in tax and CPF rules."
    )
    add("")

    add("## Maximum sustainable spending")
    add("")
    add(
        "Spending that would still succeed in {} of runs, all else equal.".format(pct(target))
    )
    add("")
    add("| Metric | Value |")
    add("|---|---|")
    add("| Sustainable retirement spending (today's dollars) | {} |".format(money(max_spend, currency)))
    add("| Sustainable first-year withdrawal rate | {} |".format(pct(max_spend_rate)))
    add("| Planned spending | {} |".format(money(cfg["annual_spending_retirement_today_dollars"], currency)))
    gap = cfg["annual_spending_retirement_today_dollars"] - max_spend
    add(
        "| Margin | {} ({}) |".format(
            money(abs(gap), currency), "surplus" if gap <= 0 else "shortfall"
        )
    )
    add("")

    add("## Stress scenarios")
    add("")
    add("| Scenario | Probability of success | Portfolio at end (median) | First shortfall age |")
    add("|---|---|---|---|")
    for name, result in scenarios:
        add(
            "| {} | {} | {} | {} |".format(
                name,
                pct(result["success_probability"]),
                money(result["median_terminal"], currency),
                result["earliest_depletion_age"] if result["earliest_depletion_age"] else "-",
            )
        )
    add("")
    add(
        "If the plan only works in the base case, the plan does not work. Report which single "
        "lever changes the outcome most: spending, retirement age, savings rate, or the "
        "allocation's risk and return."
    )
    add("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Retirement and cash-flow projection.")
    parser.add_argument("--config", required=True, help="Path to the JSON assumptions file.")
    parser.add_argument("--out", help="Write the markdown report here instead of stdout.")
    parser.add_argument("--json", dest="json_out", help="Also write raw results as JSON here.")
    args = parser.parse_args()

    cfg = load_config(args.config)
    require(cfg)

    mc_cfg = cfg.get("monte_carlo", {})
    runs = int(mc_cfg.get("runs", DEFAULT_RUNS))
    seed = int(mc_cfg.get("seed", 20260910))
    target = float(mc_cfg.get("target_success", DEFAULT_TARGET_SUCCESS))
    currency = cfg.get("currency", "SGD")

    det_outcomes = simulate(cfg, 1, seed, volatility=0.0)
    det_balance = det_outcomes[0]["balance_at_retirement"]
    first_year_spend = cfg["annual_spending_retirement_today_dollars"] * (
        1.0 + cfg["inflation"]
    ) ** (cfg["retirement_age"] - cfg["current_age"])
    first_year_income = income_at(
        cfg.get("other_income", []), cfg["retirement_age"], cfg["current_age"], cfg["inflation"]
    )
    first_year_withdrawal = max(0.0, first_year_spend - first_year_income)
    det = {
        "balance_at_retirement": det_balance,
        "first_year_spending": first_year_spend,
        "first_year_income": first_year_income,
        "first_year_withdrawal": first_year_withdrawal,
        "first_year_withdrawal_rate": (first_year_withdrawal / det_balance) if det_balance > 0 else None,
        "terminal_balance": det_outcomes[0]["terminal_balance"],
    }

    mc = summarise(simulate(cfg, runs, seed))

    stress_cfg = cfg.get("stress", {})
    bad_return = float(stress_cfg.get("bad_decade_return", -0.02))
    bad_years = int(stress_cfg.get("bad_decade_years", 10))
    extra_inflation = float(stress_cfg.get("extra_inflation", 0.02))
    spend_uplift = float(stress_cfg.get("spending_uplift", 0.20))
    long_life_age = int(stress_cfg.get("long_life_age", 100))

    scenario_inputs = [
        ("Base case", {}),
        (
            "Bad first {} years of retirement ({} p.a.)".format(bad_years, pct(bad_return)),
            {"bad_decade": {"years": bad_years, "annual_return": bad_return}},
        ),
        (
            "Inflation {} higher".format(pct(extra_inflation)),
            {"inflation": cfg["inflation"] + extra_inflation},
        ),
        (
            "Spending {} higher".format(pct(spend_uplift)),
            {"spending": cfg["annual_spending_retirement_today_dollars"] * (1.0 + spend_uplift)},
        ),
        ("Living to age {}".format(long_life_age), {"end_age": long_life_age}),
        (
            "Combined: bad decade, higher inflation, longer life",
            {
                "bad_decade": {"years": bad_years, "annual_return": bad_return},
                "inflation": cfg["inflation"] + extra_inflation,
                "end_age": long_life_age,
            },
        ),
    ]
    scenarios = [(name, summarise(simulate(cfg, runs, seed, **kwargs))) for name, kwargs in scenario_inputs]

    max_spend = sustainable_spending(cfg, runs, seed, target)
    max_spend_nominal = max_spend * (1.0 + cfg["inflation"]) ** (cfg["retirement_age"] - cfg["current_age"])
    max_spend_withdrawal = max(0.0, max_spend_nominal - first_year_income)
    max_spend_rate = (max_spend_withdrawal / det_balance) if det_balance > 0 else None

    report = build_report(cfg, currency, mc, det, scenarios, max_spend, max_spend_rate, target)

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "config": cfg,
                    "deterministic": det,
                    "monte_carlo": mc,
                    "scenarios": {name: result for name, result in scenarios},
                    "max_sustainable_spending_today_dollars": max_spend,
                    "max_sustainable_first_year_withdrawal_rate": max_spend_rate,
                },
                handle,
                indent=2,
            )

    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(report)
        sys.stdout.write("Report written to {}\n".format(args.out))
    else:
        sys.stdout.write(report)


if __name__ == "__main__":
    main()
