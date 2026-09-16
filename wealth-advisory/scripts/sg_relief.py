#!/usr/bin/env python3
"""Singapore income tax and relief headroom.

Computes tax payable, the marginal rate, the value of each relief, and the
headroom left in each cap. Every cap comes from references/sg-parameters-2026.json,
and any cap still marked unverified is reported in the output rather than used
silently.

Three rules the scripts must not get wrong, all from IRAS:

  * Total personal reliefs are capped at $80,000 per YA. Once the cap binds, an
    extra dollar of relief is worth nothing.
  * Life Insurance Relief is a formula, not a $5,000 allowance. It is nil once
    the individual's own CPF contributions reach $5,000.
  * A non-resident gets no personal reliefs at all, so relief planning has no
    application to a non-resident year.

Config keys
-----------
Required:
  employment_income
Optional:
  tax_residency              "resident" (default) or "non_resident"
  residency                  "citizen_pr" (default) or "foreigner" - sets the SRS cap
  age_band                   "below_55" (default), "55_to_59", "60_and_above"
  other_taxable_income       default 0
  employee_cpf_contributions default 0 - the employee's own mandatory CPF.
                             Also the figure the Life Insurance Relief test uses.
  planned_srs_contribution   default 0
  employer_srs_contribution  default 0 - taxable remuneration, and the individual
                             receives the relief, so it is in income and in the cap
  planned_cpf_topup_self     default 0
  planned_cpf_topup_family   default 0
  srs_withdrawn_in_same_year default false - a contribution withdrawn in the same
                             year loses its relief; orders of operation matter
  srs_account_suspended      default false - no relief where the account is
                             suspended at 31 December
  becoming_citizen_pr_in_year default false - the operator re-computes a
                             foreigner's cap pro rata; this reports an upper bound
  tax_residency_next_ya      "resident" (default) or "non_resident" - SRS relief
                             requires residency for the YA FOLLOWING the contribution
  relief_priority            order in which reliefs are absorbed by the $80,000 cap
  insurance_premiums         default 0 - qualifying life policy premiums only
  insurance_insured_value    required if insurance_premiums is above 0
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


def life_insurance_relief(cfg, params, used, notes):
    """IRAS Life Insurance Relief: a formula, not a flat cap.

    Lower of (a) $5,000 less own compulsory CPF contributions and (b) the lower
    of the premiums paid or 7% of the insured value. Nil once own CPF
    contributions reach $5,000.

    Returns (relief, capacity), where capacity is the CPF-side headroom that the
    premium leg can draw on. Capacity is zero once own CPF contributions reach
    the ceiling, whatever the premiums.
    """
    entry = value_of(params, "life_insurance_relief", used)
    ceiling = float(entry["cpf_contribution_ceiling"])
    own_cpf = float(cfg.get("employee_cpf_contributions", 0.0))
    capacity = max(0.0, ceiling - own_cpf)

    premiums = float(cfg.get("insurance_premiums", 0.0))
    if premiums <= 0:
        return 0.0, capacity

    if capacity <= 0:
        notes.append(
            "Life Insurance Relief is nil. Own CPF contributions of {} reach the {} "
            "ceiling, so no relief is due however much premium was paid.".format(
                money(own_cpf), money(ceiling)
            )
        )
        return 0.0, 0.0

    if cfg.get("insurance_insured_value") is None:
        die(
            "insurance_premiums of {} was given without insurance_insured_value. Life "
            "Insurance Relief is the lower of the CPF headroom to $5,000 and the smaller "
            "of the premiums paid or 7% of the insured value, so the insured value cannot "
            "be guessed. Add insurance_insured_value, or set insurance_premiums to 0.".format(
                money(premiums)
            )
        )

    seven_percent = float(entry["percent_of_insured_value"]) * float(cfg["insurance_insured_value"])
    premium_leg = min(premiums, seven_percent)
    relief = min(capacity, premium_leg)
    notes.append(
        "Life Insurance Relief is the lower of the CPF headroom ({} - {} = {}) and the "
        "premium leg (lower of {} paid and {} at 7% of insured value), giving {}.".format(
            money(ceiling), money(own_cpf), money(capacity),
            money(premiums), money(seven_percent), money(relief),
        )
    )
    return relief, capacity


def build_non_resident(cfg, params, used):
    """A non-resident gets no personal reliefs, so only the rates apply."""
    brackets = value_of(params, "income_tax_brackets_resident_individual", used)
    nr = value_of(params, "income_tax_non_resident", used)
    flat_employment = float(nr["employment_income_flat_rate"])
    flat_other = float(nr["other_income_flat_rate"])

    employment = float(cfg["employment_income"])
    other = float(cfg.get("other_taxable_income", 0.0))

    wasted = []
    for key, label in (
        ("planned_srs_contribution", "SRS contribution"),
        ("planned_cpf_topup_self", "CPF cash top-up to self"),
        ("planned_cpf_topup_family", "CPF cash top-up to family"),
    ):
        amount = float(cfg.get(key, 0.0))
        if amount > 0:
            wasted.append(
                "{} of {} is shown in the config, but a non-resident cannot claim the "
                "relief, so it would produce no tax saving.".format(label, money(amount))
            )
    if float(cfg.get("insurance_premiums", 0.0)) > 0:
        wasted.append(
            "Life insurance premiums of {} are shown in the config, but a non-resident "
            "cannot claim the relief.".format(money(float(cfg["insurance_premiums"])))
        )

    tax_employment_progressive = tax_on(employment, brackets)
    tax_employment_flat = employment * flat_employment
    tax_employment = max(tax_employment_progressive, tax_employment_flat)
    tax_other = other * flat_other

    return {
        "non_resident": True,
        "income": employment + other,
        "employment_income": employment,
        "other_taxable_income": other,
        "tax_employment": tax_employment,
        "tax_employment_flat": tax_employment_flat,
        "tax_employment_progressive": tax_employment_progressive,
        "employment_leg": (
            "15% flat" if tax_employment_flat >= tax_employment_progressive
            else "resident progressive rates (the higher of the two)"
        ),
        "tax_other": tax_other,
        "tax_before": tax_employment + tax_other,
        "tax_after": tax_employment + tax_other,
        "reliefs": {},
        "optional": {},
        "headroom": {},
        "relief_cap": None,
        "relief_cap_headroom": 0.0,
        "cap_binds": False,
        "marginal_rate": flat_other,
        "marginal_rate_after": flat_other,
        "unverified": sorted({k for k, e in used if e.get("verified_on") is None}),
        "age_band": None,
        "residency": cfg.get("residency", "citizen_pr"),
        "wasted_plans": wasted,
    }


def build(cfg, params, used):
    if cfg.get("tax_residency", "resident") == "non_resident":
        return build_non_resident(cfg, params, used)

    notes = []
    brackets = value_of(params, "income_tax_brackets_resident_individual", used)
    relief_cap = float(value_of(params, "personal_income_tax_relief_cap", used))
    residency = cfg.get("residency", "citizen_pr")
    age_band = cfg.get("age_band", "below_55")

    employer_srs = float(cfg.get("employer_srs_contribution", 0.0) or 0.0)
    income = (
        float(cfg["employment_income"])
        + float(cfg.get("other_taxable_income", 0.0))
        + employer_srs
    )
    if employer_srs:
        notes.append(
            "An employer SRS contribution of {} is included in taxable income. It is "
            "remuneration declared on Form IR8A, and the relief for it is granted to the "
            "individual - so it is not free money, and it uses the same annual cap as the "
            "employee's own contribution.".format(money(employer_srs))
        )

    srs_cap_key = (
        "srs_contribution_cap_citizen_pr" if residency == "citizen_pr" else "srs_contribution_cap_foreigner"
    )
    srs_cap = float(value_of(params, srs_cap_key, used))
    topup_self_cap = float(value_of(params, "cpf_topup_relief_cap_self", used))
    topup_family_cap = float(value_of(params, "cpf_topup_relief_cap_family", used))

    earned_cap = 0.0
    earned_relief = 0.0
    if cfg.get("apply_earned_income_relief", True):
        by_band = value_of(params, "earned_income_relief", used)
        if age_band not in by_band:
            die("Unknown age_band {!r}. Use one of: {}.".format(age_band, ", ".join(by_band)))
        earned_cap = float(by_band[age_band])
        # IRAS: where taxable earned income is below the maximum, the relief is
        # restricted to the amount of that earned income.
        earned_relief = min(earned_cap, float(cfg["employment_income"]))
        if earned_relief < earned_cap:
            notes.append(
                "Earned income relief is restricted to taxable earned income: {} rather "
                "than the {} maximum for this age band.".format(
                    money(earned_relief), money(earned_cap)
                )
            )

    insurance_relief, insurance_headroom = life_insurance_relief(cfg, params, used, notes)

    planned_srs = float(cfg.get("planned_srs_contribution", 0.0) or 0.0)
    srs_contributed = planned_srs + employer_srs
    srs_relief = min(srs_contributed, srs_cap)
    if residency == "foreigner" and cfg.get("becoming_citizen_pr_in_year"):
        notes.append(
            "The SRS cap shown is the full foreigner cap of {}. Where the member becomes a "
            "citizen or PR during the year the operator recomputes the cap pro rata, so this "
            "figure is an upper bound - confirm the operative cap with the SRS operator "
            "before relying on the relief.".format(money(srs_cap))
        )
    if cfg.get("srs_account_suspended"):
        notes.append(
            "The SRS account is recorded as suspended at 31 December, so no relief is due "
            "on contributions for this year however much was contributed."
        )
        srs_relief = 0.0
    if cfg.get("srs_withdrawn_in_same_year"):
        notes.append(
            "An amount was withdrawn from SRS in the same year it was contributed. The "
            "withdrawn portion loses its relief, and the order of the two events changes "
            "the outcome: contribute first and the relief is lost, withdraw first and the "
            "withdrawal is taxed in full and penalised. The relief below is set to nil for "
            "the contributed-and-withdrawn amount."
        )
        srs_relief = 0.0
    if str(cfg.get("tax_residency_next_ya", "resident")) == "non_resident":
        notes.append(
            "SRS relief requires tax residency for the Year of Assessment FOLLOWING the "
            "contribution. The config records a non-resident position for that year, so a "
            "contribution now may qualify for no relief with no refund. Settle this before "
            "the contribution, not after."
        )

    reliefs = {
        "Earned income relief": earned_relief,
        "CPF contributions (mandatory)": float(cfg.get("employee_cpf_contributions", 0.0)),
        "SRS contribution": srs_relief,
        "CPF cash top-up (self)": min(float(cfg.get("planned_cpf_topup_self", 0.0)), topup_self_cap),
        "CPF cash top-up (family)": min(float(cfg.get("planned_cpf_topup_family", 0.0)), topup_family_cap),
        "Life insurance premiums": insurance_relief,
        "Other reliefs": float(cfg.get("other_reliefs", 0.0)),
    }

    mandatory = ["Earned income relief", "CPF contributions (mandatory)", "Other reliefs"]
    optional = [k for k in reliefs if k not in mandatory]

    # Which reliefs the $80,000 cap actually absorbs is the household's choice, not the
    # market's: IRAS allows a relief to be given up so another claimant can use it. The
    # default order keeps the automatic and mandatory reliefs first; when the cap binds,
    # the report names what was cut rather than leaving the reader to work it out.
    default_priority = mandatory + [
        "SRS contribution",
        "CPF cash top-up (self)",
        "CPF cash top-up (family)",
        "Life insurance premiums",
    ]
    priority = [k for k in (cfg.get("relief_priority") or default_priority) if k in reliefs]
    priority += [k for k in reliefs if k not in priority]
    allocation, remaining_cap, cut = {}, relief_cap, {}
    for name in priority:
        taken = min(reliefs[name], max(0.0, remaining_cap))
        allocation[name] = taken
        cut[name] = reliefs[name] - taken
        remaining_cap -= taken

    def tax_with(subset):
        """Tax after the cap is applied to the reliefs in this subset."""
        allowed = min(sum(subset.values()), relief_cap)
        return tax_on(max(0.0, income - allowed), brackets)

    total_claimed = sum(reliefs.values())
    total_allowed = min(total_claimed, relief_cap)
    cap_binds = total_claimed > relief_cap

    chargeable_before = max(
        0.0, income - min(sum(reliefs[k] for k in mandatory), relief_cap)
    )
    chargeable_after = max(0.0, income - total_allowed)
    tax_before = tax_on(chargeable_before, brackets)
    tax_after = tax_on(chargeable_after, brackets)

    if cap_binds:
        notes.append(
            "The $80,000 personal relief cap binds. Reliefs claimed total {}, of which {} "
            "give no benefit at all. Giving up a relief now costs no tax - which is why "
            "deciding what to keep, or reallocating a shared relief to a spouse with "
            "headroom, is worth more than adding another contribution.".format(
                money(total_claimed), money(total_claimed - relief_cap)
            )
        )
        absorbed = [k for k, v in cut.items() if v > 0]
        if absorbed:
            notes.append(
                "On the priority order used here, the reliefs cut back by the cap are: {}. "
                "A different order changes which ones lose their benefit, and the household "
                "chooses that order - this is a convention, not a rule.".format(
                    ", ".join("{} ({})".format(k, money(cut[k])) for k in absorbed)
                )
            )

    optional_values = {}
    for name in optional:
        amount = reliefs[name]
        without = {k: v for k, v in reliefs.items() if k != name}
        optional_values[name] = {"amount": amount, "saved": tax_with(without) - tax_after}

    headroom = {
        "SRS contribution": max(0.0, srs_cap - srs_contributed),
        "CPF cash top-up (self)": max(0.0, topup_self_cap - float(cfg.get("planned_cpf_topup_self", 0.0))),
        "CPF cash top-up (family)": max(0.0, topup_family_cap - float(cfg.get("planned_cpf_topup_family", 0.0))),
        "Life insurance premiums": max(0.0, insurance_headroom - insurance_relief),
    }

    unverified = sorted({key for key, entry in used if entry.get("verified_on") is None})

    return {
        "non_resident": False,
        "income": income,
        "reliefs": reliefs,
        "optional": optional_values,
        "allocation": allocation,
        "cut_by_cap": cut,
        "headroom": headroom,
        "relief_cap": relief_cap,
        "relief_cap_headroom": max(0.0, relief_cap - total_claimed),
        "total_reliefs_claimed": total_claimed,
        "total_reliefs_allowed": total_allowed,
        "cap_binds": cap_binds,
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
        "notes": notes,
    }


def build_report(cfg, result):
    lines = []
    add = lines.append

    add("# Singapore income tax and relief position")
    add("")

    if result["non_resident"]:
        add("Tax residency basis: **non-resident**. Age band does not apply.")
        add("")
        add("## Position")
        add("")
        add(
            "A non-resident cannot claim the personal reliefs, so no relief planning "
            "applies to this year. The only levers are the timing and character of income."
        )
        add("")
        add("| Item | Amount |")
        add("|---|---|")
        add("| Employment income | {} |".format(money(result["employment_income"])))
        add("| Other taxable income | {} |".format(money(result["other_taxable_income"])))
        add("| Tax on employment income | {} |".format(money(result["tax_employment"])))
        add("| - 15% flat comparison | {} |".format(money(result["tax_employment_flat"])))
        add("| - resident progressive comparison | {} |".format(money(result["tax_employment_progressive"])))
        add("| Employment income taxed at | {} |".format(result["employment_leg"]))
        add("| Tax on other income at 24% | {} |".format(money(result["tax_other"])))
        add("| **Total tax payable** | **{}** |".format(money(result["tax_before"])))
        add("")
        add(
            "Note the asymmetry: employment income is taxed at 15% flat or the "
            "progressive rates, whichever is the higher tax, while rental, pension and "
            "director's fees are taxed flat at 24%."
        )
        add("")
        if result["wasted_plans"]:
            add("## Plans that would produce no relief")
            add("")
            for item in result["wasted_plans"]:
                add("- {}".format(item))
            add("")
    else:
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
        add("| Total reliefs claimed | {} |".format(money(result["total_reliefs_claimed"])))
        add("| Reliefs allowed after the $80,000 cap | {} |".format(money(result["total_reliefs_allowed"])))
        add("| Chargeable income before this year's planning | {} |".format(money(result["chargeable_before"])))
        add("| Chargeable income after planning | {} |".format(money(result["chargeable_after"])))
        add("| Tax before planning | {} |".format(money(result["tax_before"])))
        add("| Tax after planning | {} |".format(money(result["tax_after"])))
        add("| **Tax saved** | **{}** |".format(money(result["tax_saved"])))
        add("| Marginal rate before planning | {} |".format(pct(result["marginal_rate"])))
        add("| Marginal rate after planning | {} |".format(pct(result["marginal_rate_after"])))
        add("")

        add("## The $80,000 relief cap")
        add("")
        if result["cap_binds"]:
            add(
                "**The cap binds.** Reliefs claimed total {}, and are cut back to the "
                "$80,000 cap, so {} of claimed relief delivers no tax saving. Adding "
                "another contribution would also deliver nothing while still locking the "
                "money up. The productive move is to reallocate a shared relief to a "
                "spouse with cap headroom, or to give up a relief deliberately.".format(
                    money(result["total_reliefs_claimed"]),
                    money(result["total_reliefs_claimed"] - result["relief_cap"]),
                )
            )
        else:
            add(
                "The cap does not bind. Headroom under it is {}, so there is room for "
                "about that much more relief before the next dollar stops saving tax.".format(
                    money(result["relief_cap_headroom"])
                )
            )
        add("")

        add("## Value of each relief")
        add("")
        add(
            "Each figure is the tax that would return if that relief alone were given up, "
            "so the rows interact and do not add to the total saving. Under a binding cap "
            "a row will show nil, which is the honest answer."
        )
        add("")
        add("| Relief | Amount used | Tax saved | Cut by the cap |")
        add("|---|---|---|---|")
        for name, detail in result["optional"].items():
            cut_amount = (result.get("cut_by_cap") or {}).get(name, 0.0)
            add("| {} | {} | {} | {} |".format(
                name, money(detail["amount"]), money(detail["saved"]),
                money(cut_amount) if cut_amount else "-"))
        add("")

        add("## Headroom left")
        add("")
        add("| Cap | Unused capacity |")
        add("|---|---|")
        add("| Overall personal relief cap | {} |".format(money(result["relief_cap_headroom"])))
        for name, amount in result["headroom"].items():
            add("| {} | {} |".format(name, money(amount)))
        add("")

        if result["notes"]:
            add("## Notes on this computation")
            add("")
            for note in result["notes"]:
                add("- {}".format(note))
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

    if result["non_resident"]:
        add(
            "Tax residency is tested each year. A change of residency - from a relocation, "
            "a posting abroad, or a year split between two countries - moves the household "
            "between this basis and the resident basis, so the test belongs in every plan "
            "year rather than being settled once."
        )
        add("")
    else:
        add(
            "A relief reduces chargeable income, so its value is the amount multiplied by the "
            "marginal rate - not the amount itself. Check the relief cap before making any "
            "contribution: there is no refund of SRS contributions or of accepted CPF cash "
            "top-ups, and a relief that falls above the cap is money locked away for nothing."
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
