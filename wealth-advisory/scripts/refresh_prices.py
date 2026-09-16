#!/usr/bin/env python3
"""Refresh the prices of every holding that can be priced from a public quote.

Writes a price overlay only. It never edits the household config, so the values you
typed stay exactly as you typed them and the overlay stays auditable.

The fetching itself lives in `market_data.py`, which owns the provider chain, the
retry and throttle rules, and the checks that tell a failed fetch from a flat
market. This script's job is the household side: which holdings have a quote, what
that does to their weight, and what to do with the ones that do not.

Config keys
-----------
Required:
  portfolio.holdings          [{name, asset_class, value, ...}]
Optional:
  currency                    reporting currency, default "SGD"
  portfolio.as_of             date the holdings were last confirmed, YYYY-MM-DD

holding: {name, asset_class, value, region, ..., quantity?, price_symbol?, price_currency?}
  quantity        units held. With quantity AND a working quote, the position is
                  revalued as quantity x close x fx. Without it the value is left alone.
  price_symbol    Yahoo or Eastmoney symbol: 0700.HK, 600519.SS, 000001.SZ, ES3.SI,
                  AAPL. Prefix a Chinese unit trust with FUND: to price it by NAV.
  price_currency  the currency the quote is denominated in, e.g. HKD. Defaults to the
                  currency the quote itself reports.

A holding with no price_symbol keeps its statement value and is listed as unpriced.
CPF, SRS, property and anything unlisted belong there - they have no market quote, and
inventing one would defeat the purpose of the check.

Every quote is written with its provider, quote date, granularity, adjustment basis and
age, because two providers can disagree and both be right on different dates.

Usage:
  python refresh_prices.py --config household.json [--prices prices.json] [--offline]

Exit codes:
  0  every requested symbol was refreshed and is inside the freshness limit
  2  at least one symbol failed, or a quote is past the limit; the previous value is
     carried forward and marked stale, and the mandate check refuses to report a pass
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import market_data  # noqa: E402
from common import die, load_json, today  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Refresh market prices for the holdings that can be priced."
    )
    parser.add_argument("--config", required=True, help="Household config JSON.")
    parser.add_argument("--prices", help="Overlay path. Default prices.json beside the config.")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Do not call the network; carry the existing overlay forward and show its age.",
    )
    parser.add_argument(
        "--max-age-trading-days", type=int, default=market_data.MAX_QUOTE_AGE_TRADING_DAYS,
        help="Quotes older than this are marked stale. Default 5, from data-provenance.md.",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    cfg = load_json(config_path)
    reporting = cfg.get("currency", "SGD")
    portfolio = cfg.get("portfolio") or {}
    holdings = portfolio.get("holdings") or []
    if not holdings:
        die("Config has no portfolio.holdings to price.")

    prices_path = Path(args.prices) if args.prices else config_path.with_name("prices.json")
    previous = load_json(prices_path, required=False) or {}
    previous_quotes = previous.get("quotes") or {}

    targets = [h for h in holdings if h.get("price_symbol")]
    quotes: dict[str, dict] = {}
    errors: list[str] = []
    currencies: set[str] = set()

    for holding in targets:
        symbol = holding["price_symbol"]
        name = holding.get("name", symbol)
        if args.offline:
            carried = previous_quotes.get(symbol)
            if carried:
                carried = dict(carried)
                carried["age_trading_days"] = market_data.trading_days_since(carried.get("date"))
                carried["stale"] = (
                    carried["age_trading_days"] is None
                    or carried["age_trading_days"] > args.max_age_trading_days
                )
                carried.setdefault("notes", []).append(
                    "Carried forward from the previous overlay in offline mode; not re-fetched."
                )
                quotes[symbol] = carried
                if carried.get("currency"):
                    currencies.add(carried["currency"])
            else:
                errors.append(
                    "{} ({}): no previous quote to carry forward".format(name, symbol)
                )
            continue

        quote = market_data.fetch_quote(symbol, max_age_days=args.max_age_trading_days)
        if not quote.get("ok"):
            carried = previous_quotes.get(symbol)
            if carried:
                stale = dict(carried)
                stale["stale"] = True
                stale["age_trading_days"] = market_data.trading_days_since(stale.get("date"))
                stale.setdefault("notes", []).append(
                    "Fetch failed; this is the previous value, and it is stale."
                )
                quotes[symbol] = stale
            errors.append(
                "{} ({}): {}".format(name, symbol, "; ".join(quote.get("errors", [])))
            )
            continue
        quotes[symbol] = quote
        if quote.get("currency"):
            currencies.add(quote["currency"])
        if quote.get("stale"):
            errors.append(
                "{} ({}): quote dated {} is {} trading day(s) old".format(
                    name, symbol, quote.get("date"), quote.get("age_trading_days"))
            )

    fx: dict[str, dict] = {}
    for currency in sorted(currencies):
        if currency == reporting:
            continue
        key = "{}/{}".format(currency, reporting)
        rate = market_data.fetch_fx(currency, reporting)
        if not rate.get("ok"):
            errors.append("FX {}: {}".format(key, "; ".join(rate.get("errors", []))))
            continue
        fx[key] = rate

    unpriced = [h.get("name", "?") for h in holdings if not h.get("price_symbol")]

    output = {
        "as_of": today(),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "reporting_currency": reporting,
        "source": (
            "Provider chain per symbol, recorded on each quote. Daily closes, not intraday. "
            "Source catalogue: technical-analysis skill, references/data-sources.md."
        ),
        "max_age_trading_days": args.max_age_trading_days,
        "quotes": quotes,
        "fx": fx,
        "priced_symbols": sorted(quotes),
        "unpriced_holdings": unpriced,
        "unrefreshed": errors,
        "complete": not errors,
        "note": (
            "A holding with no price_symbol keeps its value from the config. Those positions "
            "are not marked to market by this script, by design."
        ),
    }

    with open(prices_path, "w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2)
        handle.write("\n")

    print(
        "{} of {} priced holding(s) refreshed; {} unpriced; {} problem(s). Overlay written "
        "to {}.".format(len(quotes), len(targets), len(unpriced), len(errors), prices_path)
    )
    for problem in errors:
        print("  - {}".format(problem))
    stale = [s for s, q in quotes.items() if q.get("stale")]
    if stale:
        print(
            "  {} quote(s) are past the {}-trading-day limit. A stale quote is reported, "
            "never presented as current.".format(len(stale), args.max_age_trading_days)
        )
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
