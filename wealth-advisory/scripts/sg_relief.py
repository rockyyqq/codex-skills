#!/usr/bin/env python3
"""Singapore income tax and relief headroom.

Computes tax payable, the marginal rate, the value of each relief, and the
headroom left in each cap. Every cap comes from references/sg-parameters-2026.json,
and any cap still marked unverified is reported in the output rather than used
silently.

Config keys
-----------
Required:
  employment_income
Optional:
  residency                  "citizen_pr" (default) or "foreigner"
  age_band                   "below_55" (default), "55_to_59", "60_and_above"
  other_taxable_income       default 0
  employee_cpf_contributions default 0 - the employee's own mandatory CPF, already relief
  planned_srs_contribution   default 0
  planned_cpf_topup_self     default 0
  planned_cpf_topup_family   default 0
  insurance_premiums         default 0
  other_reliefs              default 0
  apply_earned_income_relief default true
  params                     path to the parameter file

Usage:
  python sg_relief.py --config client.json [--out report.md] [--json out.json]
"""

import argparse
import json
import sys
from pathlib import Path

DEFAULT_PARAMS = Path(__file__).resolve().parent.parent / "references" / "sg-parameters-2026.json"


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


def money(value):
    return "SGD {:,.0f}".format(value)


def pct(value):
    return "{:.2f}%".format(value * 100.0)


def load_params(path):
    if not Path(path).exists():
        die("Parameter file not found: {}".format(path))
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)["parameters"]


def value_of(params, key, used):
    entry = params.get(key)
    if entry is None:
        die("Parameter {!r} is missing from the parameter file.".format(key))
    used.append((key, entry))
    if entry.get("value") is None:
        die(
            "Parameter {!r} has no value. Source: {}".format(key, entry.get("source", "unknown"))
        )
    return entry["value"]


def tax_on(chargeable, brackets):
    tax = 0.0
    for band in brackets:
        upper = band["max"] if band["max"] is not None else float("inf")
        if chargeable > band["min"]:
            amount = min(chargeable, upper) - band["min"]
            if amount > 0:
                tax += amount * band["rate"]
    return tax


def marginal_rate(chargeable, brackets):
    for band in brackets:
        upper = band["max"] if band["max"] is not None else float("inf")
        if chargeable <= upper:
            return band["rate"]
    return brackets[-1]["rate"]


def build(cfg, params, used):
    brackets = value_of(params, "income_tax_brackets_resident_individual", used)
    residency = cfg.get("residency", "citizen_pr")
    age_band = cfg.get("age_band", "below_55")

    income = float(cfg["employment_income"]) + float(cfg.get("other_taxable_income", 0.0))

    srs_cap_key = (
        "srs_contribution_cap_citizen_pr" if residency == "citizen_pr" else "srs_contribution_cap_foreigner"
    )
    srs_cap = value_of(params, srs_cap_key, used)
    topup_self_cap = value_of(params, "cpf_topup_relief_cap_self", used)
    topup_family_cap = value_of(params, "cpf_topup_relief_cap_family", used)
    insurance_cap = value_of(params, "insurance_relief_cap_self", used)

    earned_relief = 0.0
    if cfg.get("apply_earned_income_relief", True):
        by_band = value_of(params, "earned_income_relief", used)
        if age_band not in by_band:
            die("Unknown age_band {!r}. Use one of: {}.".format(age_band, ", ".join(by_band)))
        earned_relief = float(by_band[age_band])

    reliefs = {
        "Earned income relief": earned_relief,
        "CPF contributions (mandatory)": float(cfg.get("employee_cpf_contributions", 0.0)),
        "SRS contribution": min(float(cfg.get("planned_srs_contribution", 0.0)), srs_cap),
        "CPF cash top-up (self)": min(float(cfg.get("planned_cpf_topup_self", 0.0)), topup_self_cap),
        "CPF cash top-up (family)": min(float(cfg.get("planned_cpf_topup_family", 0.0)), topup_family_cap),
        "Life insurance premiums": min(float(cfg.get("insurance_premiums", 0.0)), insurance_cap),
        "Other reliefs": float(cfg.get("other_reliefs", 0.0)),
    }

    mandatory = reliefs["Earned income relief"] + reliefs["CPF contributions (mandatory)"] + reliefs["Other reliefs"]
    optional = {k: v for k, v in reliefs.items() if k not in
                ("Earned income relief", "CPF contributions (mandatory)", "Other reliefs")}

    chargeable_before = max(0.0, income - mandatory)
    chargeable_after = max(0.0, income - sum(reliefs.values()))
    tax_before = tax_on(chargeable_before, brackets)
    tax_after = tax_on(chargeable_after, brackets)

    for name, amount in optional.items():
        without = max(0.0, chargeable_after + amount)
        optional[name] = {"amount": amount, "saved": tax_on(without, brackets) - tax_after}

    headroom = {
        "SRS contribution": max(0.0, srs_cap - float(cfg.get("planned_srs_contribution", 0.0))),
        "CPF cash top-up (self)": max(0.0, topup_self_cap - float(cfg.get("planned_cpf_topup_self", 0.0))),
        "CPF cash top-up (family)": max(0.0, topup_family_cap - float(cfg.get("planned_cpf_topup_family", 0.0))),
        "Life insurance premiums": max(0.0, insurance_cap - float(cfg.get("insurance_premiums", 0.0))),
    }

    unverified = sorted(
        {
            key
            for key, entry in used
            if entry.get("verified_on") is None
        }
    )

    return {
        "income": income,
        "reliefs": reliefs,
        "optional": optional,
        "headroom": headroom,
        "chargeable_before": chargeable_before,
        "chargeable_after": chargeable_after,
        "tax_before": tax_before,
        "tax_after": tax_after,
        "tax_saved": tax_before - tax_after,
        "marginal_rate": marginal_rate(chargeable_before, brackets),
        "marginal_rate_after": marginal_rate(chargeable_after, brackets),
        "unverified": unverified,
        "age_band": age_band,
        "residency": residency,
    }


def build_report(cfg, result):
    lines = []
    add = lines.append

    add("# Singapore income tax and relief position")
    add("")
    add(
        "Residency basis: **{}**. Age band: **{}**.".format(
            result["residency"], result["age_band"]
        )
    )
    add("")

    add("## Position")
    add("")
    add("| Item | Amount |")
    add("|---|---|")
    add("| Total taxable income | {} |".format(money(result["income"])))
    add("| Total reliefs claimed | {} |".format(money(sum(result["reliefs"].values()))))
    add("| Chargeable income before this year's planning | {} |".format(money(result["chargeable_before"])))
    add("| Chargeable income after planning | {} |".format(money(result["chargeable_after"])))
    add("| Tax before planning | {} |".format(money(result["tax_before"])))
    add("| Tax after planning | {} |".format(money(result["tax_after"])))
    add("| **Tax saved** | **{}** |".format(money(result["tax_saved"])))
    add("| Marginal rate before planning | {} |".format(pct(result["marginal_rate"])))
    add("| Marginal rate after planning | {} |".format(pct(result["marginal_rate_after"])))
    add("")

    add("## Value of each relief")
    add("")
    add(
        "Each figure is the tax that would return if that relief alone were given up, so the "
        "rows interact and do not add to the total saving."
    )
    add("")
    add("| Relief | Amount used | Tax saved |")
    add("|---|---|---|")
    for name, detail in result["optional"].items():
        add("| {} | {} | {} |".format(name, money(detail["amount"]), money(detail["saved"])))
    add("")

    add("## Headroom left")
    add("")
    add("| Relief | Unused capacity |")
    add("|---|---|")
    for name, amount in result["headroom"].items():
        add("| {} | {} |".format(name, money(amount)))
    add("")

    if result["unverified"]:
        add("## Parameters that need confirming")
        add("")
        add(
            "The following parameters were used but have not been confirmed against their "
            "official source. Check each one before this reaches a client."
        )
        add("")
        for key in result["unverified"]:
            add("- `{}`".format(key))
        add("")

    add(
        "A relief reduces chargeable income, so its value is the amount multiplied by the "
        "marginal rate - not the amount itself. Describing a top-up as \"saving {} of tax\" "
        "would overstate it by roughly {} times.".format(
            money(sum(result["reliefs"].values())),
            int(round(1 / result["marginal_rate"])) if result["marginal_rate"] > 0.01 else 0,
        )
    )
    add("")
    add(
        "Amounts moved into SRS and CPF are not lost, but they are locked. Judge the tax "
        "saving against the loss of access, not on its own."
    )
    add("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Singapore tax and relief position.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--out", help="Write the markdown report here instead of stdout.")
    parser.add_argument("--json", dest="json_out", help="Also write raw results as JSON here.")
    args = parser.parse_args()

    cfg = load_config(args.config)
    if "employment_income" not in cfg:
        die("Config needs employment_income.")

    used = []
    params = load_params(cfg.get("params", DEFAULT_PARAMS))
    result = build(cfg, params, used)
    report = build_report(cfg, result)

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
