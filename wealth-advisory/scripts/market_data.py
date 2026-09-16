#!/usr/bin/env python3
"""The market data layer: one place that fetches a price, a currency rate or an index value.

Every script in this skill that needs a quote imports from here, so a retry rule,
a throttle rule and a fallback provider are implemented once rather than per script.

The catalogue of which sources work, what each covers and what each does not is
maintained by the `technical-analysis` skill in `references/data-sources.md`. This
module implements the parts of that catalogue this skill depends on, and records
which provider actually answered, at what granularity and on what adjustment basis.

What this module refuses to do:

  * return a number when the fetch failed - a failure raises, it is never a zero
  * accept a series at the wrong granularity - the chart API returns monthly bars
    for very long ranges regardless of the interval asked for, which produces a
    wrong answer rather than no answer
  * hide which provider answered, because two providers can disagree and both be
    right on different dates

Usage:
  python market_data.py --symbol 1211.HK
  python market_data.py --symbol ES3.SI --symbol 600519.SS --json quotes.json
  python market_data.py --fx HKD/SGD
  python market_data.py --selftest
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import die, emit, money, today  # noqa: E402

try:
    import requests
except ImportError:  # pragma: no cover - reported at run time
    requests = None


USER_AGENT = "Mozilla/5.0 (compatible; wealth-advisory-market-data/1.0)"
TIMEOUT_SECONDS = 25
MIN_SECONDS_BETWEEN_CALLS = 1.0
RETRIES = 2
BACKOFF_SECONDS = 2.0

# references/data-provenance.md: market prices are stale after 5 trading days.
MAX_QUOTE_AGE_TRADING_DAYS = 5

YAHOO_CHART = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range={window}&interval=1d"
EASTMONEY_KLINE = (
    "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={market}.{code}"
    "&fields1=f1&fields2=f51,f53&klt=101&fqt=1&beg={beg}&end={end}"
)
EASTMONEY_FUND = (
    "https://api.fund.eastmoney.com/f10/lsjz?fundCode={code}&pageIndex=1&pageSize=20"
)

_last_call_at = 0.0


class MarketDataError(RuntimeError):
    """A fetch that did not produce a usable number. Never caught to invent a value."""


def _throttle() -> None:
    """Space calls out. Yahoo throttles after roughly twenty rapid requests."""
    global _last_call_at
    elapsed = time.time() - _last_call_at
    if elapsed < MIN_SECONDS_BETWEEN_CALLS:
        time.sleep(MIN_SECONDS_BETWEEN_CALLS - elapsed)
    _last_call_at = time.time()


def _get_json(url: str, headers: dict | None = None) -> dict:
    if requests is None:
        raise MarketDataError(
            "the requests package is not available, so no quote can be fetched"
        )
    merged = {"User-Agent": USER_AGENT}
    merged.update(headers or {})
    last_error: Exception | None = None
    for attempt in range(1, RETRIES + 2):
        _throttle()
        try:
            response = requests.get(url, headers=merged, timeout=TIMEOUT_SECONDS)
            if response.status_code in (429, 503):
                raise MarketDataError("HTTP {} (throttled)".format(response.status_code))
            response.raise_for_status()
            return response.json()
        except Exception as exc:  # noqa: BLE001 - retried, then reported
            last_error = exc
            if attempt <= RETRIES:
                time.sleep(BACKOFF_SECONDS * attempt)
    raise MarketDataError(str(last_error))


def trading_days_since(iso_date: str, reference: date | None = None) -> int | None:
    """Weekdays between a quote date and today. An approximation, and labelled as one."""
    if not iso_date:
        return None
    try:
        start = date.fromisoformat(iso_date)
    except ValueError:
        return None
    end = reference or date.today()
    if start >= end:
        return 0
    days = 0
    cursor = start
    while cursor < end:
        cursor += timedelta(days=1)
        if cursor.weekday() < 5:
            days += 1
    return days


def _parse_yahoo(payload: dict, symbol: str, window: str) -> dict:
    chart = payload.get("chart") or {}
    results = chart.get("result") or []
    if not results:
        raise MarketDataError(
            "the quote service returned no result ({})".format(chart.get("error"))
        )
    node = results[0]
    meta = node.get("meta") or {}

    granularity = meta.get("dataGranularity")
    if granularity and granularity != "1d":
        raise MarketDataError(
            "asked for daily bars over range={} and got {}. The chart API returns "
            "monthly bars for very long ranges, which would give a wrong answer "
            "rather than no answer. Ask for a bounded window.".format(window, granularity)
        )

    closes = ((node.get("indicators") or {}).get("quote") or [{}])[0].get("close") or []
    stamps = node.get("timestamp") or []
    for index in range(len(closes) - 1, -1, -1):
        value = closes[index]
        if value is None:
            continue
        when = stamps[index] if index < len(stamps) else meta.get("regularMarketTime")
        observed = (
            datetime.fromtimestamp(int(when), tz=timezone.utc).date().isoformat()
            if when
            else None
        )
        return {
            "close": float(value),
            "currency": meta.get("currency"),
            "date": observed,
            "granularity": granularity or "1d",
            "adjusted": "unadjusted",
            "exchange": meta.get("fullExchangeName") or meta.get("exchangeName"),
            "session": meta.get("marketState"),
            "notes": [
                "Yahoo chart API close is unadjusted; a split shows as a price gap "
                "that did not happen economically."
            ],
        }

    if meta.get("regularMarketPrice") is not None:
        when = meta.get("regularMarketTime")
        return {
            "close": float(meta["regularMarketPrice"]),
            "currency": meta.get("currency"),
            "date": (
                datetime.fromtimestamp(int(when), tz=timezone.utc).date().isoformat()
                if when
                else None
            ),
            "granularity": granularity or "unknown",
            "adjusted": "unadjusted",
            "exchange": meta.get("fullExchangeName") or meta.get("exchangeName"),
            "session": meta.get("marketState"),
            "notes": ["Last daily close was null; fell back to the regular market price."],
        }
    raise MarketDataError("the quote service returned no close price")


def _eastmoney_secid(symbol: str) -> tuple[str, str] | None:
    s = symbol.upper()
    if s.endswith(".HK"):
        return "116", s[:-3].zfill(5)
    if s.endswith(".SS"):
        return "1", s[:-3]
    if s.endswith(".SZ"):
        return "0", s[:-3]
    return None


def _fetch_eastmoney_kline(symbol: str) -> dict:
    secid = _eastmoney_secid(symbol)
    if not secid:
        raise MarketDataError("{} is not a Hong Kong or mainland symbol".format(symbol))
    market, code = secid
    end = date.today().strftime("%Y%m%d")
    beg = (date.today() - timedelta(days=40)).strftime("%Y%m%d")
    payload = _get_json(
        EASTMONEY_KLINE.format(market=market, code=code, beg=beg, end=end),
        headers={"Referer": "https://quote.eastmoney.com/"},
    )
    data = payload.get("data") or {}
    klines = data.get("klines") or []
    if not klines:
        raise MarketDataError("Eastmoney returned no bars for {}".format(symbol))
    last = klines[-1].split(",")
    if len(last) < 2:
        raise MarketDataError("Eastmoney bar was not in the expected shape")
    return {
        "close": float(last[1]),
        "currency": "HKD" if market == "116" else "CNY",
        "date": last[0],
        "granularity": "1d",
        "adjusted": "forward-adjusted (fqt=1)",
        "exchange": "HKEX" if market == "116" else "SSE/SZSE",
        "session": "CLOSED",
        "notes": [
            "Eastmoney bars are forward-adjusted, so this close is not comparable "
            "with an unadjusted close from another provider."
        ],
    }


def _fetch_eastmoney_fund(code: str) -> dict:
    payload = _get_json(
        EASTMONEY_FUND.format(code=code),
        headers={"Referer": "https://fundf10.eastmoney.com/"},
    )
    rows = ((payload.get("Data") or {}).get("LSJZList")) or []
    if not rows:
        raise MarketDataError("Eastmoney fund API returned no NAV history")
    row = rows[0]
    return {
        "close": float(row["DWJZ"]),
        "currency": "CNY",
        "date": row["FSRQ"],
        "granularity": "1d",
        "adjusted": "NAV, net of fees",
        "exchange": "CN open-ended fund",
        "session": "CLOSED",
        "notes": ["Fund NAV, not a traded price. No intraday value exists."],
    }


def route(symbol: str) -> list[str]:
    """Providers to try, in order of blocking risk rather than convenience."""
    s = symbol.upper()
    if s.startswith("FUND:"):
        return ["eastmoney_fund"]
    if s.endswith(".HK"):
        return ["yahoo", "eastmoney_kline"]
    if s.endswith(".SS") or s.endswith(".SZ"):
        return ["eastmoney_kline", "yahoo"]
    return ["yahoo"]


def fetch_quote(symbol: str, window: str = "1mo", max_age_days: int | None = None) -> dict:
    """Fetch one close, with the provider chain, freshness and basis recorded."""
    providers = route(symbol)
    errors: list[str] = []
    for provider in providers:
        try:
            if provider == "yahoo":
                payload = _get_json(YAHOO_CHART.format(symbol=symbol, window=window))
                result = _parse_yahoo(payload, symbol, window)
            elif provider == "eastmoney_kline":
                result = _fetch_eastmoney_kline(symbol)
            else:
                result = _fetch_eastmoney_fund(symbol.split(":", 1)[1])
        except Exception as exc:  # noqa: BLE001 - next provider, then reported
            errors.append("{}: {}".format(provider, exc))
            continue

        age = trading_days_since(result.get("date"))
        limit = MAX_QUOTE_AGE_TRADING_DAYS if max_age_days is None else max_age_days
        stale = age is None or age > limit
        if stale:
            result.setdefault("notes", []).append(
                "Quote date {} is {} trading day(s) old, past the {} day limit. "
                "The market may simply have been closed; that is not evidence the "
                "price is unchanged.".format(result.get("date"), age, limit)
            )
        return {
            "ok": True,
            "symbol": symbol,
            "provider": provider,
            "providers_tried": providers,
            "providers_failed": errors,
            "age_trading_days": age,
            "stale": stale,
            "max_age_trading_days": limit,
            **result,
        }

    return {
        "ok": False,
        "symbol": symbol,
        "providers_tried": providers,
        "errors": errors,
        "stale": True,
        "note": "Every provider failed. This is a gap, not a zero.",
    }


def fetch_fx(base: str, quote: str) -> dict:
    base, quote = base.upper(), quote.upper()
    if base == quote:
        return {
            "ok": True,
            "pair": "{}/{}".format(base, quote),
            "rate": 1.0,
            "date": None,
            "provider": "identity",
            "age_trading_days": 0,
            "stale": False,
            "granularity": "n/a",
            "adjusted": "n/a",
        }
    symbol = "{}{}=X".format(base, quote)
    errors = []
    try:
        payload = _get_json(YAHOO_CHART.format(symbol=symbol, window="1mo"))
        result = _parse_yahoo(payload, symbol, "1mo")
    except Exception as exc:  # noqa: BLE001
        errors.append("yahoo: {}".format(exc))
        return {
            "ok": False,
            "pair": "{}/{}".format(base, quote),
            "errors": errors,
            "stale": True,
            "note": "No FX rate available. A conversion without its own date is not usable.",
        }
    age = trading_days_since(result.get("date"))
    return {
        "ok": True,
        "pair": "{}/{}".format(base, quote),
        "rate": result["close"],
        "date": result["date"],
        "provider": "yahoo",
        "age_trading_days": age,
        "stale": age is None or age > MAX_QUOTE_AGE_TRADING_DAYS,
        "granularity": result.get("granularity"),
        "adjusted": "n/a",
    }


def render(quotes: list[dict], fx: list[dict]) -> str:
    lines = ["# Market data pull", "", "Pulled {}. Source rules: see the data-sources catalogue in the "
             "technical-analysis skill; freshness limits: references/data-provenance.md.".format(stamp_line())]
    lines.append("")
    if quotes:
        lines.append("| Symbol | Close | Ccy | Quote date | Age (trading days) | Provider | Basis | Exchange / session |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for q in quotes:
            if not q.get("ok"):
                lines.append("| {} | - | - | - | - | - | **FETCH FAILED** | {} |".format(
                    q["symbol"], "; ".join(q.get("errors", []))))
                continue
            lines.append("| {} | {:,.4g} | {} | {} | {} | {} | {} | {} / {} |".format(
                q["symbol"], q["close"], q.get("currency") or "?",
                q.get("date") or "unknown", q.get("age_trading_days"),
                q.get("provider"), q.get("adjusted"),
                q.get("exchange") or "?", q.get("session") or "?"))
        lines.append("")
    if fx:
        lines.append("| Pair | Rate | Date | Provider |")
        lines.append("|---|---|---|---|")
        for f in fx:
            if not f.get("ok"):
                lines.append("| {} | - | - | **FETCH FAILED** |".format(f["pair"]))
                continue
            lines.append("| {} | {:,.6g} | {} | {} |".format(
                f["pair"], f["rate"], f.get("date") or "n/a", f.get("provider")))
        lines.append("")
    failed = [q for q in quotes if not q.get("ok")] + [f for f in fx if not f.get("ok")]
    stale = [q for q in quotes + fx if q.get("ok") and q.get("stale")]
    if failed:
        lines.append("**{} fetch(es) failed.** Nothing is substituted for a failed fetch; "
                     "the affected holding keeps its statement value and the check reports "
                     "CANNOT JUDGE.".format(len(failed)))
        lines.append("")
    if stale:
        lines.append("**{} quote(s) are past the freshness limit.** Report the date with the "
                     "figure; do not present a stale quote as current.".format(len(stale)))
        lines.append("")
    return "\n".join(lines)


def stamp_line() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")


def selftest() -> int:
    """Checks that hold without a network, so a broken rule fails fast."""
    problems = []
    if trading_days_since("2026-09-11", reference=date(2026, 9, 14)) != 1:
        problems.append("trading-day arithmetic is wrong")
    if trading_days_since("2026-09-04", reference=date(2026, 9, 14)) != 6:
        problems.append("trading-day arithmetic is wrong over a weekend")
    if route("0700.HK") != ["yahoo", "eastmoney_kline"]:
        problems.append("Hong Kong symbols should try Yahoo, then Eastmoney")
    if route("600519.SS") != ["eastmoney_kline", "yahoo"]:
        problems.append("mainland symbols should try Eastmoney first")
    if _eastmoney_secid("000001.SZ") != ("0", "000001"):
        problems.append("Shenzhen secid mapping is wrong")
    if _eastmoney_secid("0700.HK") != ("116", "00700"):
        problems.append("Hong Kong secid mapping is wrong")
    if problems:
        for problem in problems:
            sys.stderr.write("FAIL {}\n".format(problem))
        return 1
    print("OK market_data.py self-test: arithmetic, routing and symbol mapping")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch quotes and FX with provenance.")
    parser.add_argument("--symbol", action="append", default=[], help="Repeatable.")
    parser.add_argument("--fx", action="append", default=[], help="Pair, e.g. HKD/SGD.")
    parser.add_argument("--window", default="1mo", help="Yahoo range window. Default 1mo.")
    parser.add_argument("--max-age-trading-days", type=int, default=MAX_QUOTE_AGE_TRADING_DAYS)
    parser.add_argument("--json", dest="json_out")
    parser.add_argument("--out")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    if args.selftest:
        return selftest()
    if not args.symbol and not args.fx:
        die("Give at least one --symbol or --fx, or run --selftest.")

    quotes = [
        fetch_quote(s, window=args.window, max_age_days=args.max_age_trading_days)
        for s in args.symbol
    ]
    fx = []
    for pair in args.fx:
        if "/" not in pair:
            die("--fx expects BASE/QUOTE, for example HKD/SGD")
        base, quote = pair.split("/", 1)
        fx.append(fetch_fx(base, quote))

    raw = {"as_of": today(), "quotes": quotes, "fx": fx}
    emit(render(quotes, fx), out_path=args.out, raw=raw, json_path=args.json_out)
    failed = any(not q.get("ok") for q in quotes) or any(not f.get("ok") for f in fx)
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
