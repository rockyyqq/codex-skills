#!/usr/bin/env python3
"""The monthly mandate check.

Answers one question: does the portfolio still obey the limits the household set?

It reuses portfolio_risk.build(), so the limits are evaluated by exactly the same code
that produces the full report. Nothing here re-implements a limit, because two
implementations of the same rule is how they drift apart.

Two classes of result are kept apart on purpose:

  Hard signals    Concentration, regional look-through, asset-class share, equity
                  share, cash buffer. These depend only on what the portfolio holds,
                  so a breach is a fact.
  Assumption-dependent
                  Portfolio volatility and the estimated worst-case fall. These depend
                  on the return, volatility and correlation assumptions in the config,
                  so a breach means "these assumptions imply a breach" - not a
                  measurement. Moving an assumption moves the answer.

It will not report a pass on data it could not verify. If the holdings file is stale, a
price could not be refreshed, or the config is incomplete, the status is CANNOT JUDGE
and the exit code says so. A watchdog that quietly reports "fine" on month-old data is
worse than no watchdog.

Config keys
-----------
Everything portfolio_risk.py needs, plus:
  portfolio.as_of    YYYY-MM-DD, the date the holdings and quantities were last
                     confirmed by the household. This is not the price date.

Errors are reported in full rather than filtered to a headline count. If two limits
fail, both are named.

Usage:
  python check_mandate.py --config household.json [--prices prices.json]
                          [--reports-dir reports] [--stale-days 90]
                          [--out report.md] [--json out.json] [--today YYYY-MM-DD]

Exit codes:
  0  PASS           every limit satisfied, on data fresh enough to trust
  1  BREACH         at least one limit failed
  2  CANNOT JUDGE   stale holdings, unrefreshed prices, or an incomplete config

The report file is written only when the status is BREACH or CANNOT JUDGE, and then to
reports/YYYY-MM-DD-mandate-check.md unless --out says otherwise. A passing month leaves
nothing behind.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import portfolio_risk  # noqa: E402  (imported after sys.path is extended)


ASSUMPTION_DEPENDENT = ("Portfolio volatility", "Estimated worst-case fall")


def load_json(path: Path, required: bool = True):
    if not path.exists():
        if required:
            raise FileNotFoundError("File not found: {}".format(path))
        return None
    with open(path, "r", encoding="utf-8") as handle:
        try:
            return json.load(handle)
        except json.JSONDecodeError as exc:
            raise ValueError("{} is not valid JSON: {}".format(path, exc)) from exc


def pct(value: float) -> str:
    return "{:.1f}%".format(value * 100.0)


def format_check(value: float, unit: str) -> str:
    if unit == "years":
        return "{:.1f} years".format(value)
    return pct(value)


def days_since(iso_date: str | None, today: date) -> int | None:
    if not iso_date:
        return None
    try:
        return (today - date.fromisoformat(iso_date)).days
    except ValueError:
        return None


def revalue(cfg: dict, prices: dict | None):
    """Return a copy of the config with market prices applied, plus the notes."""
    holdings = (cfg.get("portfolio") or {}).get("holdings") or []
    reporting = cfg.get("currency", "SGD")
    quotes = (prices or {}).get("quotes") or {}
    fx = (prices or {}).get("fx") or {}

    effective = []
    priced, manual, problems = [], [], []

    for holding in holdings:
        entry = dict(holding)
        name = holding.get("name", "?")
        symbol = holding.get("price_symbol")
        quantity = holding.get("quantity")
        quote = quotes.get(symbol) if symbol else None

        if not symbol:
            manual.append(name)
            effective.append(entry)
            continue

        if quote is None:
            problems.append("{} ({}): no price available".format(name, symbol))
            effective.append(entry)
            continue

        if quantity is None:
            manual.append(name)
            effective.append(entry)
            continue

        quote_currency = holding.get("price_currency") or quote.get("currency") or reporting
        rate = 1.0
        if quote_currency != reporting:
            key = "{}/{}".format(quote_currency, reporting)
            if key not in fx:
                problems.append(
                    "{} ({}): priced in {} and no {}/{} rate is available".format(
                        name, symbol, quote_currency, quote_currency, reporting
                    )
                )
                effective.append(entry)
                continue
            rate = float(fx[key]["rate"])

        entry["value"] = float(quantity) * float(quote["close"]) * rate
        entry["_pricing"] = {
            "symbol": symbol,
            "close": float(quote["close"]),
            "close_date": quote.get("date"),
            "quote_currency": quote_currency,
            "fx_rate": rate,
            "fx_date": (fx.get("{}/{}".format(quote_currency, reporting)) or {}).get("date"),
            "stale": bool(quote.get("stale")),
        }
        priced.append(name)
        if quote.get("stale"):
            problems.append(
                "{} ({}): carried forward from {} because the quote could not be "
                "refreshed".format(name, symbol, quote.get("date"))
            )
        effective.append(entry)

    new_cfg = dict(cfg)
    new_cfg["portfolio"] = dict(cfg.get("portfolio") or {})
    new_cfg["portfolio"]["holdings"] = effective
    return new_cfg, priced, manual, problems


def build_report(
    status: str,
    today: date,
    cfg: dict,
    result: dict | None,
    reasons: list[str],
    priced: list[str],
    manual: list[str],
    holding_age: int | None,
) -> str:
    currency = cfg.get("currency", "SGD")
    lines: list[str] = []
    add = lines.append

    add("# Mandate check - {}".format(today.isoformat()))
    add("")
    add("**Status: {}**".format(status))
    add("")
    if cfg.get("label"):
        add("{}".format(cfg["label"]))
        add("")

    if status == "CANNOT JUDGE":
        add(
            "The limits were **not** checked. Reporting a pass on this data would be a "
            "guess, and a guess in a monitoring report is worse than an obvious gap."
        )
        add("")
        add("## Why this run could not judge")
        add("")
        for reason in reasons:
            add("- {}".format(reason))
        add("")

    if result is not None:
        hard = [c for c in result["checks"] if c["check"] not in ASSUMPTION_DEPENDENT]
        soft = [c for c in result["checks"] if c["check"] in ASSUMPTION_DEPENDENT]

        add("## Hard signals - these depend only on what the portfolio holds")
        add("")
        if hard:
            add("| Limit | Actual | Limit | Result |")
            add("|---|---|---|---|")
            for check in hard:
                add(
                    "| {} | {} | {} | {} |".format(
                        check["check"],
                        format_check(check["actual"], check["unit"]),
                        format_check(check["limit"], check["unit"]),
                        "PASS" if check["ok"] else "**FAIL**",
                    )
                )
        else:
            add("No value-based limits are set in the config, so nothing here was checked.")
        add("")

        add("## Assumption-dependent - these move when the assumptions move")
        add("")
        if soft:
            add("| Limit | Actual | Limit | Result |")
            add("|---|---|---|---|")
            for check in soft:
                add(
                    "| {} | {} | {} | {} |".format(
                        check["check"],
                        format_check(check["actual"], check["unit"]),
                        format_check(check["limit"], check["unit"]),
                        "PASS" if check["ok"] else "**FAIL**",
                    )
                )
            add("")
            add(
                "These two inherit the return, volatility and correlation assumptions in "
                "the config. A failure here means the assumptions imply a breach, not that "
                "the market has been measured. Before acting, check the assumptions still "
                "reflect your view."
            )
        else:
            add("No volatility or drawdown limit is set, so nothing here was checked.")
        add("")

        add("## Exposure")
        add("")
        add("| Measure | Value |")
        add("|---|---|")
        add("| Total portfolio | {} {:,.0f} |".format(currency, result["total"]))
        add("| Equity share | {} |".format(pct(result["equity_share"])))
        add("| Greater China, look-through | {} |".format(pct(result["greatest_china"])))
        add("| Largest holding ({}) | {} |".format(result["largest"]["name"], pct(result["largest"]["share"])))
        add("")
        for region, share in sorted(result["region_share"].items(), key=lambda kv: -kv[1]):
            add("- {}: {}".format(region, pct(share)))
        add("")

        if result["failures"]:
            add("## What failed, in full")
            add("")
            for check in result["failures"]:
                add(
                    "- **{}** - at {}, against a limit of {}".format(
                        check["check"],
                        format_check(check["actual"], check["unit"]),
                        format_check(check["limit"], check["unit"]),
                    )
                )
            add("")
            add(
                "Decide which gives way: the target allocation, or the limit. Do not relax "
                "the limit to make the allocation fit."
            )
            add("")

    add("## What this check used")
    add("")
    if holding_age is None:
        add("- Holdings: no confirmation date recorded (portfolio.as_of is missing).")
    else:
        add("- Holdings last confirmed by the household {} day(s) ago.".format(holding_age))
    add("- Priced from a market quote: {}".format(", ".join(priced) if priced else "none"))
    add(
        "- Held at statement value, not marked to market: {}".format(
            ", ".join(manual) if manual else "none"
        )
    )
    add(
        "- Prices are latest daily closes, not intraday. A position held at statement "
        "value can drift without this check seeing it."
    )
    add("")
    add(
        "This is a monitoring note, not licensed financial advice. See the skill's "
        "deliverables for the full disclosure that belongs in a planning document."
    )
    add("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Monthly mandate check.")
    parser.add_argument("--config", required=True, help="Household config JSON.")
    parser.add_argument("--prices", help="Price overlay. Defaults to prices.json beside the config.")
    parser.add_argument("--reports-dir", help="Where to write a report when one is needed.")
    parser.add_argument("--stale-days", type=int, default=90, help="Holdings older than this cannot be judged. Default 90.")
    parser.add_argument("--out", help="Write the report here instead of the reports directory.")
    parser.add_argument("--json", dest="json_out", help="Also write the raw result as JSON here.")
    parser.add_argument("--today", help="Override today's date, for testing.")
    args = parser.parse_args()

    today = date.fromisoformat(args.today) if args.today else date.today()

    config_path = Path(args.config)
    try:
        cfg = load_json(config_path)
    except (FileNotFoundError, ValueError) as exc:
        print("CANNOT JUDGE - {}".format(exc))
        return 2

    prices_path = Path(args.prices) if args.prices else config_path.with_name("prices.json")
    try:
        prices = load_json(prices_path, required=False)
    except ValueError as exc:
        print("CANNOT JUDGE - {}".format(exc))
        return 2

    holdings = (cfg.get("portfolio") or {}).get("holdings") or []
    targets = [h for h in holdings if h.get("price_symbol") and h.get("quantity") is not None]

    reasons: list[str] = []

    holding_as_of = (cfg.get("portfolio") or {}).get("as_of")
    holding_age = days_since(holding_as_of, today)
    if holding_age is None:
        reasons.append(
            "The holdings have no confirmation date. Set portfolio.as_of to the date you "
            "last checked the positions and quantities."
        )
    elif holding_age > args.stale_days:
        reasons.append(
            "The holdings were last confirmed {} days ago ({}, limit {} days). Positions "
            "may have changed since.".format(holding_age, holding_as_of, args.stale_days)
        )

    if targets and prices is None:
        reasons.append(
            "No price overlay at {}. Run refresh_prices.py first - the market values "
            "cannot be checked without it.".format(prices_path)
        )

    effective_cfg, priced, manual, problems = revalue(cfg, prices)
    # Every pricing problem becomes a reason, because a limit evaluated on a value we
    # could not verify is not a limit that was checked.
    reasons.extend(problems)

    result = None
    try:
        result = portfolio_risk.build(effective_cfg)
    except SystemExit as exc:
        reasons.append(
            "The config is incomplete, so the limits could not be evaluated (exit {}). "
            "portfolio_risk.py names the missing field.".format(exc.code)
        )
    except Exception as exc:  # noqa: BLE001
        reasons.append("The limits could not be evaluated: {}".format(exc))

    failures = result["failures"] if result else []

    if reasons:
        status = "CANNOT JUDGE"
        code = 2
    elif failures:
        status = "BREACH"
        code = 1
    else:
        status = "PASS"
        code = 0

    report = build_report(status, today, cfg, result, reasons, priced, manual, holding_age)

    if status != "PASS":
        if args.out:
            out_path = Path(args.out)
        else:
            reports_dir = (
                Path(args.reports_dir)
                if args.reports_dir
                else config_path.parent / "reports"
            )
            reports_dir.mkdir(parents=True, exist_ok=True)
            out_path = reports_dir / "{}-mandate-check.md".format(today.isoformat())
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as handle:
            handle.write(report)
        written = str(out_path)
    else:
        written = None

    if args.json_out:
        payload = {
            "date": today.isoformat(),
            "status": status,
            "exit_code": code,
            "reasons": reasons,
            "hard_failures": [
                c["check"] for c in failures if c["check"] not in ASSUMPTION_DEPENDENT
            ],
            "assumption_dependent_failures": [
                c["check"] for c in failures if c["check"] in ASSUMPTION_DEPENDENT
            ],
            "holding_age_days": holding_age,
            "priced": priced,
            "manual": manual,
            "report": written,
            "result": result,
        }
        with open(args.json_out, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")

    if status == "PASS":
        print("PASS - every limit satisfied, on data fresh enough to trust.")
    else:
        print("{} - {} issue(s).".format(status, len(reasons) or len(failures)))
        for reason in reasons:
            print("  ! {}".format(reason))
        for check in failures:
            print(
                "  ! {} at {}, limit {}".format(
                    check["check"],
                    format_check(check["actual"], check["unit"]),
                    format_check(check["limit"], check["unit"]),
                )
            )
        if written:
            print("  Report: {}".format(written))

    return code


if __name__ == "__main__":
    raise SystemExit(main())
