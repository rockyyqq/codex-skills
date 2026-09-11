#!/usr/bin/env python3
"""Portfolio risk, concentration and mandate checks.

Answers three questions the rest of the toolkit cannot:
  1. What risk does this portfolio actually carry, and where does it come from?
  2. What is the true regional exposure once you look through the wrappers?
  3. Does the portfolio obey the household's stated risk limits?

Returns, volatilities and correlations are ASSUMPTIONS, not facts. They are
required in the config and are echoed into the report so nobody mistakes them
for measurements.

Config keys
-----------
Required:
  portfolio.holdings          [{name, asset_class, value, region, ...}]
  assumptions.expected        {asset_class: {return, volatility, is_equity?, is_cash?}}
  assumptions.correlations    {"Class A|Class B": rho, ...}
Optional:
  currency                    default "SGD"
  label
  assumptions.as_of
  assumptions.drawdown_multiple  default 2.0 (a heuristic, stated in the report)
  mandate.*                   limits: max_volatility, max_drawdown_tolerance,
                              max_equity, max_asset_class, max_region, max_holding,
                              min_cash_buffer_years, annual_household_spending, max_theme
                              region_cap_exempt (default ["Global"]) - region labels that
                              describe a spread rather than one country, so a country-level
                              cap does not fire on them. They are still reported.

holding: {name, asset_class, value, region, domicile, venue, look_through, diversified,
          theme, theme_look_through}
  look_through: {region: fraction} - the true underlying exposure. Defaults to
  {region: 1.0} when omitted. Use it for funds that hold something other than
  their listing venue suggests.
  theme: an optional label for what the holding is really a bet on, e.g.
  "China growth", "Singapore income". Two holdings in different asset classes can
  share a theme, which is the point: a regional cap cannot see that nine positions
  are one bet. theme_look_through: {theme: fraction} does the same for themes.
  max_theme caps any single theme, and fires only when a holding carries one, so
  configs without themes behave exactly as before.
  diversified: true for a fund holding many names, which exempts it from the
  single-company limit. Anything not marked is treated as a single name, so a
  forgotten flag fails safe.

Usage:
  python portfolio_risk.py --config portfolio.json [--out report.md] [--json out.json]
"""

import argparse
import json
import math
import sys
from pathlib import Path

DEFAULT_DRAWDOWN_MULTIPLE = 2.0


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


def pct(value):
    return "{:.1f}%".format(value * 100.0)


def correlation(correlations, cls_a, cls_b):
    if cls_a == cls_b:
        return 1.0
    for key in ("{}|{}".format(cls_a, cls_b), "{}|{}".format(cls_b, cls_a)):
        if key in correlations:
            return float(correlations[key])
    die(
        "Correlation missing for {!r} and {!r}. Add \"{}|{}\" to "
        "assumptions.correlations. The tool will not invent a correlation, because "
        "diversification benefit is exactly what a guessed number would overstate.".format(
            cls_a, cls_b, cls_a, cls_b
        )
    )


def build(cfg):
    if "portfolio" not in cfg or "holdings" not in cfg["portfolio"]:
        die("Config needs portfolio.holdings.")
    if "assumptions" not in cfg or "expected" not in cfg["assumptions"]:
        die("Config needs assumptions.expected.")
    holdings = cfg["portfolio"]["holdings"]
    if not holdings:
        die("portfolio.holdings is empty.")

    expected = cfg["assumptions"]["expected"]
    correlations = cfg["assumptions"].get("correlations", {})
    multiple = float(cfg["assumptions"].get("drawdown_multiple", DEFAULT_DRAWDOWN_MULTIPLE))
    currency = cfg.get("currency", "SGD")
    mandate = cfg.get("mandate", {})

    classes = sorted({h["asset_class"] for h in holdings})
    for h in holdings:
        if h["asset_class"] not in expected:
            die(
                "Asset class {!r} has no assumption entry. Add it to "
                "assumptions.expected.".format(h["asset_class"])
            )

    total = sum(float(h["value"]) for h in holdings)
    if total <= 0:
        die("Total portfolio value must be positive.")

    weights = {c: 0.0 for c in classes}
    for h in holdings:
        weights[h["asset_class"]] += float(h["value"]) / total

    means = {c: float(expected[c]["return"]) for c in classes}
    vols = {c: float(expected[c]["volatility"]) for c in classes}

    port_return = sum(weights[c] * means[c] for c in classes)
    variance = 0.0
    for a in classes:
        for b in classes:
            variance += weights[a] * weights[b] * vols[a] * vols[b] * correlation(correlations, a, b)
    port_vol = math.sqrt(max(variance, 0.0))

    # Each class's share of total volatility, versus its share of the money.
    risk_contribution = {}
    for a in classes:
        cov = sum(
            weights[b] * vols[a] * vols[b] * correlation(correlations, a, b) for b in classes
        )
        contribution = weights[a] * cov
        risk_contribution[a] = (contribution / variance) if variance > 0 else 0.0

    regions = {}
    for h in holdings:
        look = h.get("look_through") or {h.get("region", "Unclassified"): 1.0}
        for region, fraction in look.items():
            regions[region] = regions.get(region, 0.0) + float(fraction) * float(h["value"])
    region_share = {r: v / total for r, v in regions.items()}

    # Theme look-through. Optional, and deliberately separate from region: a region
    # cap answers "which country", a theme cap answers "how many ways am I making the
    # same bet". Nine funds in one country can be one theme, and the region check
    # cannot see that.
    themes = {}
    for h in holdings:
        look = h.get("theme_look_through")
        if not look and h.get("theme"):
            look = {h["theme"]: 1.0}
        for theme, fraction in (look or {}).items():
            themes[theme] = themes.get(theme, 0.0) + float(fraction) * float(h["value"])
    theme_share = {t: v / total for t, v in themes.items()}

    equity_share = sum(
        weights[c] for c in classes if expected[c].get("is_equity", False)
    )
    cash_value = sum(
        float(h["value"]) for h in holdings if expected[h["asset_class"]].get("is_cash", False)
    )
    largest = max(holdings, key=lambda h: float(h["value"]))
    single_names = [h for h in holdings if not h.get("diversified", False)]

    checks = []

    def check(label, actual, limit, comparator, unit="percent"):
        if limit is None:
            return
        ok = comparator(actual, limit)
        checks.append(
            {"check": label, "actual": actual, "limit": limit, "ok": ok, "unit": unit}
        )

    check("Portfolio volatility", port_vol, mandate.get("max_volatility"), lambda a, b: a <= b)
    check(
        "Estimated worst-case fall",
        port_vol * multiple,
        mandate.get("max_drawdown_tolerance"),
        lambda a, b: a <= b,
    )
    check("Equity share", equity_share, mandate.get("max_equity"), lambda a, b: a <= b)
    for c in classes:
        check("Single asset class: {}".format(c), weights[c], mandate.get("max_asset_class"), lambda a, b: a <= b)
    exempt_regions = set(mandate.get("region_cap_exempt", ["Global"]))
    for r, share in sorted(region_share.items()):
        if r in exempt_regions:
            continue
        check("Region: {}".format(r), share, mandate.get("max_region"), lambda a, b: a <= b)
    for t, share in sorted(theme_share.items()):
        check("Theme: {}".format(t), share, mandate.get("max_theme"), lambda a, b: a <= b)
    if single_names:
        biggest = max(single_names, key=lambda h: float(h["value"]))
        check(
            "Largest single-company holding: {}".format(biggest["name"]),
            float(biggest["value"]) / total,
            mandate.get("max_holding"),
            lambda a, b: a <= b,
        )
    spending = mandate.get("annual_household_spending")
    if spending:
        check(
            "Cash buffer (years of spending)",
            cash_value / spending,
            mandate.get("min_cash_buffer_years"),
            lambda a, b: a >= b,
            unit="years",
        )

    return {
        "currency": currency,
        "total": total,
        "weights": weights,
        "means": means,
        "vols": vols,
        "port_return": port_return,
        "port_vol": port_vol,
        "drawdown_multiple": multiple,
        "estimated_drawdown": port_vol * multiple,
        "risk_contribution": risk_contribution,
        "region_share": region_share,
        "theme_share": theme_share,
        "equity_share": equity_share,
        "cash_value": cash_value,
        "greatest_china": sum(
            share
            for region, share in region_share.items()
            if region in ("Hong Kong", "Mainland China", "Greater China")
        ),
        "region_cap_exempt": sorted(
            r for r in region_share if r in set(mandate.get("region_cap_exempt", ["Global"]))
        ),
        "largest": {"name": largest["name"], "share": float(largest["value"]) / total},
        "single_name_count": len(single_names),
        "largest_single_name": (
            max(single_names, key=lambda h: float(h["value"]))["name"] if single_names else None
        ),
        "checks": checks,
        "failures": [c for c in checks if not c["ok"]],
        "assumptions_as_of": cfg["assumptions"].get("as_of"),
    }


def format_check(value, unit):
    if unit == "years":
        return "{:.1f} years".format(value)
    return pct(value)


def build_report(cfg, result):
    currency = result["currency"]
    lines = []
    add = lines.append

    add("# Portfolio risk and mandate check")
    if cfg.get("label"):
        add("")
        add("**{}**".format(cfg["label"]))
    add("")
    add(
        "Total portfolio {}. Returns, volatilities and correlations are **assumptions "
        "supplied in the config, not measurements** - the output is only as good as "
        "those inputs.".format(money(result["total"], currency))
    )
    add("")

    add("## What the portfolio carries")
    add("")
    add("| Metric | Value |")
    add("|---|---|")
    add("| Expected annual return (assumption) | {} |".format(pct(result["port_return"])))
    add("| Portfolio volatility (assumption) | {} |".format(pct(result["port_vol"])))
    add(
        "| Estimated worst-case fall ({} x volatility) | {} |".format(
            result["drawdown_multiple"], pct(result["estimated_drawdown"])
        )
    )
    add("| Equity share | {} |".format(pct(result["equity_share"])))
    add("| Cash and near-cash | {} |".format(money(result["cash_value"], currency)))
    add("| Greater China exposure, look-through | {} |".format(pct(result["greatest_china"])))
    add("| Largest holding: {} | {} |".format(result["largest"]["name"], pct(result["largest"]["share"])))
    add("")
    add(
        "The worst-case figure is a heuristic, not a forecast. It scales volatility, so it "
        "understates a genuine crisis, when correlations rise and diversifiers stop "
        "diversifying. Treat it as a floor for the fall, not a ceiling."
    )
    add("")

    add("## Where the risk actually comes from")
    add("")
    add("| Asset class | Share of money | Share of risk | Difference |")
    add("|---|---|---|---|")
    for cls in sorted(result["weights"], key=lambda c: -result["risk_contribution"][c]):
        capital = result["weights"][cls]
        risk = result["risk_contribution"][cls]
        add(
            "| {} | {} | {} | {}{:.1f}% |".format(
                cls, pct(capital), pct(risk), "+" if risk >= capital else "", (risk - capital) * 100.0
            )
        )
    add("")
    add(
        "A class carrying a much larger share of risk than of money is doing more to "
        "determine your outcome than its position suggests. That is usually where to look "
        "first when the mandate fails."
    )
    add("")

    add("## True regional exposure (look-through)")
    add("")
    add("| Region | Share of portfolio |")
    add("|---|---|")
    for region, share in sorted(result["region_share"].items(), key=lambda kv: -kv[1]):
        add("| {} | {} |".format(region, pct(share)))
    add("")

    if result.get("theme_share"):
        add("## Exposure by theme")
        add("")
        add(
            "Which country a holding sits in and what it is a bet on are different "
            "questions. Positions spread across several asset classes and regions can "
            "still be one theme, and a regional cap cannot see that."
        )
        add("")
        add("| Theme | Share of portfolio |")
        add("|---|---|")
        for theme, share in sorted(result["theme_share"].items(), key=lambda kv: -kv[1]):
            add("| {} | {} |".format(theme, pct(share)))
        add("")
    if result["greatest_china"] > 0:
        add(
            "Greater China totals {}. This is measured on the underlying businesses, not on "
            "where the funds are listed, so Hong Kong-listed China funds are counted here "
            "rather than under Hong Kong.".format(pct(result["greatest_china"]))
        )
        add("")
    if result["region_cap_exempt"]:
        add(
            "Excluded from the country cap because the label describes a spread rather than a "
            "single country: {}. Add or remove labels with mandate.region_cap_exempt.".format(
                ", ".join(result["region_cap_exempt"])
            )
        )
        add("")

    add("## Mandate check")
    add("")
    if not result["checks"]:
        add("No mandate limits supplied, so nothing could be checked. Set them in the config - an unchecked portfolio is an unmanaged one.")
    else:
        add("| Limit | Actual | Limit | Result |")
        add("|---|---|---|---|")
        for check in result["checks"]:
            add(
                "| {} | {} | {} | {} |".format(
                    check["check"],
                    format_check(check["actual"], check["unit"]),
                    format_check(check["limit"], check["unit"]),
                    "PASS" if check["ok"] else "**FAIL**",
                )
            )
        add("")
        if result["failures"]:
            add("### Breaches")
            add("")
            for check in result["failures"]:
                add("- **{}** - at {}, against a limit of {}".format(
                    check["check"],
                    format_check(check["actual"], check["unit"]),
                    format_check(check["limit"], check["unit"]),
                ))
            add("")
            add(
                "Decide which gives way: the target allocation, or the limit. Do not quietly "
                "relax the limit to make the allocation fit - that is how a mandate stops "
                "meaning anything."
            )
        else:
            add("Every limit is satisfied.")
    add("")

    if result["single_name_count"] == 0:
        add(
            "No holding is marked as a single company, so the single-company limit applied to "
            "nothing. If any position is a direct share rather than a fund, remove its "
            "`diversified` flag so the limit can see it."
        )
        add("")

    if result["assumptions_as_of"]:
        add("Assumption set dated {}.".format(result["assumptions_as_of"]))
        add("")
    add(
        "Before acting on this, check that the assumption set still reflects your view of "
        "the future. Changing the return assumption changes the answer; changing the "
        "correlation assumption changes how much the diversification is really worth."
    )
    add("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Portfolio risk, concentration and mandate checks.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--out", help="Write the markdown report here instead of stdout.")
    parser.add_argument("--json", dest="json_out", help="Also write raw results as JSON here.")
    args = parser.parse_args()

    cfg = load_config(args.config)
    result = build(cfg)
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
