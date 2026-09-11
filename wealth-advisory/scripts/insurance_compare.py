#!/usr/bin/env python3
"""Compare insurance options on cost over a chosen horizon.

Two products with different premium structures cannot be compared by looking at
the first-year premium. This computes what each one actually costs to the age
you expect to stop paying, on both a total and a present-value basis, and finds
the age at which the cheaper option changes.

It compares COST only. It does not judge whether the cover is any good, and it
does not know what you need - sum assured and need sizing sit outside this tool.

Config keys
-----------
Required:
  entry_age              your age today
  compare_to_age         the age you expect to stop paying
  options                list of at least two, each with:
                           name, sum_assured, premium
Optional:
  currency               default "SGD"
  discount_rate          default 0.03 - used for present value; an assumption
  options[].conditions   condition count, for context only
  options[].payment_term_age      defaults to compare_to_age
  options[].total_premium_floor   true if the plan pays the higher of sum assured
                                  or total premiums paid

premium is one of:
  {"type": "level", "annual": 3600}
      fixed annual premium
  {"type": "increasing", "first_year_annual": 1200, "annual_increase": 0.05}
      premium grows every year - typical of plans whose premiums rise with age
  {"type": "schedule", "amounts": [1200, 1260, ...]}
      an explicit list of annual premiums starting at entry_age

Usage:
  python insurance_compare.py --config quote_compare.json [--out report.md]
"""

import argparse
import json
import sys
from pathlib import Path


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


def money(value, currency):
    return "{} {:,.0f}".format(currency, value)


def premium_at(option, age, entry_age):
    spec = option["premium"]
    kind = spec.get("type")
    if kind == "level":
        return float(spec["annual"])
    if kind == "increasing":
        years = age - entry_age
        return float(spec["first_year_annual"]) * (1.0 + float(spec["annual_increase"])) ** years
    if kind == "schedule":
        index = age - entry_age
        amounts = spec["amounts"]
        if index >= len(amounts):
            die(
                "Option {!r} has a schedule of {} years but the horizon needs {}.".format(
                    option.get("name", "?"), len(amounts), index + 1
                )
            )
        return float(amounts[index])
    die(
        "Option {!r} needs a premium type of 'level', 'increasing' or "
        "'schedule'.".format(option.get("name", "?"))
    )


def build(cfg):
    for key in ("entry_age", "compare_to_age", "options"):
        if key not in cfg:
            die("Config needs {}.".format(key))
    if len(cfg["options"]) < 2:
        die("Provide at least two options to compare.")
    if cfg["compare_to_age"] <= cfg["entry_age"]:
        die("compare_to_age must be after entry_age.")

    entry = int(cfg["entry_age"])
    horizon = int(cfg["compare_to_age"])
    currency = cfg.get("currency", "SGD")
    discount = float(cfg.get("discount_rate", 0.03))

    results = []
    for option in cfg["options"]:
        for key in ("name", "sum_assured", "premium"):
            if key not in option:
                die("Every option needs name, sum_assured and premium.")
        pay_to = int(option.get("payment_term_age", horizon))
        years = max(0, min(pay_to, horizon) - entry)
        premiums = [premium_at(option, entry + y, entry) for y in range(years)]
        total = sum(premiums)
        present = sum(p / (1.0 + discount) ** y for y, p in enumerate(premiums))
        sum_assured = float(option["sum_assured"])
        results.append(
            {
                "name": option["name"],
                "conditions": option.get("conditions"),
                "sum_assured": sum_assured,
                "pay_to": pay_to,
                "years": years,
                "first": premiums[0] if premiums else 0.0,
                "last": premiums[-1] if premiums else 0.0,
                "total": total,
                "present": present,
                "average": (total / years) if years else 0.0,
                "cost_per_100k": (total / (sum_assured / 100000.0)) if sum_assured else None,
                "premiums": premiums,
            }
        )

    # Crossover: the age at which the cheapest option changes.
    running = [0.0] * len(results)
    cheapest_by_age = []
    for y in range(max(r["years"] for r in results)):
        for i, r in enumerate(results):
            if y < r["years"]:
                running[i] += r["premiums"][y]
        live = [i for i, r in enumerate(results) if y < r["years"]]
        if live:
            cheapest_by_age.append((entry + y, results[min(live, key=lambda i: running[i])]["name"]))

    crossovers = []
    for age, name in cheapest_by_age:
        if not crossovers or crossovers[-1][1] != name:
            crossovers.append((age, name))

    return {
        "currency": currency,
        "entry_age": entry,
        "horizon": horizon,
        "discount_rate": discount,
        "results": results,
        "crossovers": crossovers,
    }


def build_report(result):
    currency = result["currency"]
    lines = []
    add = lines.append

    add("# Insurance cost comparison")
    add("")
    add(
        "Age {} to age {}, present value discounted at {:.1f}% a year. This compares "
        "cost only - whether the cover is worth having is a separate question, and so "
        "is whether the sum assured is large enough.".format(
            result["entry_age"], result["horizon"], result["discount_rate"] * 100.0
        )
    )
    add("")
    add("| | " + " | ".join(r["name"] for r in result["results"]) + " |")
    add("|---" * (len(result["results"]) + 1) + "|")

    def row(label, values):
        add("| {} | {} |".format(label, " | ".join(values)))

    row("Conditions", [str(r["conditions"]) if r["conditions"] else "not stated" for r in result["results"]])
    row("Sum assured", [money(r["sum_assured"], currency) for r in result["results"]])
    row("Premium in year one", [money(r["first"], currency) for r in result["results"]])
    row("Premium in the final year", [money(r["last"], currency) for r in result["results"]])
    row("Average annual premium", [money(r["average"], currency) for r in result["results"]])
    row(
        "**Total paid to age {}**".format(result["horizon"]),
        ["**{}**".format(money(r["total"], currency)) for r in result["results"]],
    )
    row("Present value of that cost", [money(r["present"], currency) for r in result["results"]])
    row(
        "Cost per {}100k of cover".format(currency),
        [
            money(r["cost_per_100k"], currency) if r["cost_per_100k"] is not None else "n/a"
            for r in result["results"]
        ],
    )
    add("")

    if result["crossovers"]:
        add("## Which option is cheaper as you go")
        add("")
        for age, name in result["crossovers"]:
            add("- From age {}: **{}**".format(age, name))
        add("")
        if len(result["crossovers"]) > 1:
            add(
                "The cheapest option changes partway through, which is exactly what you'd "
                "expect when one premium is level and the other rises every year. Where you "
                "stop paying decides which one wins."
            )
        else:
            add("One option is cheaper across the whole horizon.")
        add("")

    adds = []
    for r in result["results"]:
        if r["last"] > r["first"] * 1.5:
            adds.append(
                "**{}** rises from {} to {} a year between now and age {}. Ask what the "
                "premium schedule looks like at 55, 60 and 65, not just today.".format(
                    r["name"], money(r["first"], currency), money(r["last"], currency), result["horizon"]
                )
            )
    if adds:
        add("## What to check before deciding")
        add("")
        for note in adds:
            add("- {}".format(note))
        add("")
        add(
            "- Confirm the **premium payment term versus the coverage term** in writing. If "
            "premiums must be paid for the whole policy term, stopping at age {} may end the "
            "cover rather than simply stop the payments.".format(result["horizon"])
        )
        add("- Confirm whether the insurer can revise the premium, separate from any age-based increase.")
        add("- Check the sum assured against what you actually need. A cheap plan with too little cover is still the wrong plan.")
        add("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Compare insurance options on cost.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--out", help="Write the markdown report here instead of stdout.")
    parser.add_argument("--json", dest="json_out", help="Also write raw results as JSON here.")
    args = parser.parse_args()

    cfg = load_config(args.config)
    result = build(cfg)
    report = build_report(result)

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(report)
        sys.stdout.write("Report written to {}\n".format(args.out))
    else:
        sys.stdout.write(report)


if __name__ == "__main__":
    main()
