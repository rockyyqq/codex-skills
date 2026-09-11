#!/usr/bin/env python3
"""Refresh the prices of every holding that can be priced from a public quote.

Writes a price overlay only. It never edits household.json, so the values you typed
stay exactly as you typed them, and the overlay stays auditable.

Config keys
-----------
Required:
  portfolio.holdings          [{name, asset_class, value, ...}]
Optional:
  currency                    reporting currency, default "SGD"
  portfolio.as_of             date the holdings were last confirmed, YYYY-MM-DD

holding: {name, asset_class, value, region, ..., quantity?, price_symbol?, price_currency?}
  quantity        units held. With quantity AND a working price, the position is
                  revalued as quantity x close x fx. Without it the value is left alone.
  price_symbol    a Yahoo Finance symbol: 0700.HK, 600519.SS, 000001.SZ, ES3.SI, AAPL
  price_currency  the currency the quote is denominated in, e.g. HKD. Defaults to the
                  currency the quote itself reports.

A holding with no price_symbol keeps its statement value and is listed as unpriced.
CPF, SRS, property and anything unlisted belong there - they do not have a market quote,
and inventing one would defeat the purpose of the check.

Quotes are the latest daily close, not intraday. A monthly check does not need a live
price, and a close is a number that can be pointed at.

Usage:
  python refresh_prices.py --config household.json [--prices prices.json] [--offline]

Exit codes:
  0  every requested symbol was refreshed
  2  at least one symbol could not be refreshed; the previous value is carried forward
     and marked stale, and the mandate check will refuse to report a pass
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:  # pragma: no cover - reported at run time
    requests = None


CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1mo&interval=1d"
USER_AGENT = "Mozilla/5.0 (compatible; wealth-advisory-price-refresh/1.0)"
TIMEOUT_SECONDS = 25


def die(message: str) -> None:
    sys.stderr.write(message.rstrip() + "\n")
    sys.exit(2)


def load_json(path: Path, required: bool = True):
    if not path.exists():
        if required:
            die("File not found: {}".format(path))
        return None
    with open(path, "r", encoding="utf-8") as handle:
        try:
            return json.load(handle)
        except json.JSONDecodeError as exc:
            die("{} is not valid JSON: {}".format(path, exc))


def fetch_json(url: str) -> dict:
    if requests is None:
        raise RuntimeError(
            "The requests package is not available, so no quote can be fetched."
        )
    response = requests.get(
        url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_SECONDS
    )
    response.raise_for_status()
    return response.json()


def parse_chart(payload: dict) -> tuple[float, str | None, str | None]:
    """Return (close, observation_date, quote_currency) from a Yahoo chart payload."""
    chart = payload.get("chart") or {}
    results = chart.get("result") or []
    if not results:
        raise RuntimeError("the quote service returned no result ({})".format(chart.get("error")))

    node = results[0]
    meta = node.get("meta") or {}
    currency = meta.get("currency")

    quote_blocks = ((node.get("indicators") or {}).get("quote")) or [{}]
    closes = quote_blocks[0].get("close") or []
    stamps = node.get("timestamp") or []

    for index in range(len(closes) - 1, -1, -1):
        value = closes[index]
        if value is None:
            continue
        when = stamps[index] if index < len(stamps) else meta.get("regularMarketTime")
        observed = None
        if when:
            observed = datetime.fromtimestamp(int(when), tz=timezone.utc).date().isoformat()
        return float(value), observed, currency

    if meta.get("regularMarketPrice") is not None:
        when = meta.get("regularMarketTime")
        observed = None
        if when:
            observed = datetime.fromtimestamp(int(when), tz=timezone.utc).date().isoformat()
        return float(meta["regularMarketPrice"]), observed, currency

    raise RuntimeError("the quote service returned no close price")


def fetch_quote(symbol: str) -> dict:
    close, observed, currency = parse_chart(fetch_json(CHART_URL.format(symbol=symbol)))
    return {
        "close": close,
        "currency": currency,
        "date": observed,
        "symbol": symbol,
        "source": "Yahoo Finance chart API, latest daily close",
        "stale": False,
    }


def fetch_fx(base: str, quoted_in: str) -> dict:
    if base == quoted_in:
        return {"rate": 1.0, "date": None, "source": "identity"}
    symbol = "{}{}=X".format(base, quoted_in)
    close, observed, _ = parse_chart(fetch_json(CHART_URL.format(symbol=symbol)))
    return {
        "rate": close,
        "date": observed,
        "symbol": symbol,
        "source": "Yahoo Finance chart API, latest daily close",
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Refresh market prices for the holdings that can be priced."
    )
    parser.add_argument("--config", required=True, help="Household config JSON.")
    parser.add_argument(
        "--prices",
        help="Where to write the overlay. Defaults to prices.json beside the config.",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Do not call the network; re-date the existing overlay instead.",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    cfg = load_json(config_path)
    reporting = cfg.get("currency", "SGD")
    holdings = (cfg.get("portfolio") or {}).get("holdings") or []

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
                quotes[symbol] = dict(carried)
                if carried.get("currency"):
                    currencies.add(carried["currency"])
            else:
                errors.append("{} ({}): no previous price to carry forward".format(name, symbol))
            continue

        try:
            quote = fetch_quote(symbol)
        except Exception as exc:  # noqa: BLE001 - every failure degrades the same way
            carried = previous_quotes.get(symbol)
            if carried:
                stale = dict(carried)
                stale["stale"] = True
                quotes[symbol] = stale
            errors.append("{} ({}): {}".format(name, symbol, exc))
            continue

        quotes[symbol] = quote
        if quote.get("currency"):
            currencies.add(quote["currency"])

    fx: dict[str, dict] = {}
    for currency in sorted(currencies):
        if currency == reporting:
            continue
        key = "{}/{}".format(currency, reporting)
        try:
            fx[key] = fetch_fx(currency, reporting)
        except Exception as exc:  # noqa: BLE001
            errors.append("FX {}: {}".format(key, exc))

    unpriced = [h.get("name", "?") for h in holdings if not h.get("price_symbol")]

    output = {
        "as_of": date.today().isoformat(),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "reporting_currency": reporting,
        "source": "Yahoo Finance chart API, latest daily close. Not intraday.",
        "quotes": quotes,
        "fx": fx,
        "priced_symbols": sorted(quotes),
        "unpriced_holdings": unpriced,
        "unrefreshed": errors,
        "complete": not errors,
        "note": (
            "A holding with no price_symbol keeps its value from the config. Those "
            "positions are not marked to market by this script, by design."
        ),
    }

    with open(prices_path, "w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2)
        handle.write("\n")

    print(
        "{} of {} priced holding(s) refreshed; {} unpriced; {} problem(s). "
        "Overlay written to {}.".format(
            len(quotes), len(targets), len(unpriced), len(errors), prices_path
        )
    )
    for problem in errors:
        print("  - {}".format(problem))

    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
