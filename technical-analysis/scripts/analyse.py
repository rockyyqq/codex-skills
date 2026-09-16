#!/usr/bin/env python3
"""Read one symbol's price history and report what it shows.

Fetches daily OHLCV, then computes the structural readings (trend, moving averages,
recent swing levels, volume against its average) and the standard indicator set (RSI,
MACD, ATR, Bollinger position).

What it does not do
-------------------
It does not rank, score, recommend, or predict. It prints measurements and the levels
those measurements imply. Every figure carries its as-of date, because a price without a
date is not a fact about anything.

Usage
-----
    python analyse.py --symbol 1211.HK
    python analyse.py --symbol AAPL --range 2y --json out.json
    python analyse.py --symbol HK.800700 --source opend

--source opend reads through the broker's OpenD gateway instead of Yahoo. It
needs OpenD running and logged in, the SDK installed, and normal permissions
rather than a sandbox. Symbols use the broker's form: HK.01211, US.QQQ.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

CHART = ("https://query1.finance.yahoo.com/v8/finance/chart/{}"
         "?range={}&interval=1d")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def fetch_opend(symbol: str, bars: int = 1000):
    """Read daily bars through the broker's OpenD gateway.

    request_history_kline, not get_cur_kline: the latter needs an active
    subscription. And note that max_count takes bars FORWARD from the start
    date, so the whole window is requested and the newest bars taken from the
    end - asking for a small count returns the oldest bars, which look current
    and are not.
    """
    sdk = None
    for name in ("futu", "moomoo"):
        try:
            sdk = __import__(name)
            break
        except ImportError:
            continue
    if sdk is None:
        raise RuntimeError("no OpenD SDK installed (pip install futu-api)")

    ctx = sdk.OpenQuoteContext(host="127.0.0.1", port=11111)
    try:
        ret, data, _ = ctx.request_history_kline(
            symbol, start=None, end=None, ktype=sdk.KLType.K_DAY,
            max_count=bars)
        if ret != 0:
            raise RuntimeError(str(data)[:160])
        if data is None or not len(data):
            raise RuntimeError("no bars returned - check entitlement for this symbol")
        data = data.sort_values("time_key")
        rows = []
        for _, row in data.iterrows():
            rows.append({
                "date": str(row["time_key"])[:10],
                "open": float(row["open"]), "high": float(row["high"]),
                "low": float(row["low"]), "close": float(row["close"]),
                "volume": float(row.get("volume") or 0),
            })
        meta = {"currency": str(row.get("currency", ""))}
        return rows, meta
    finally:
        ctx.close()


def fetch(symbol: str, window: str):
    url = CHART.format(urllib.parse.quote(symbol), window)
    request = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8", "replace"))
    result = payload["chart"]["result"][0]
    stamps = result["timestamp"]
    quote = result["indicators"]["quote"][0]
    rows = []
    for i, stamp in enumerate(stamps):
        o, h, l, c = (quote["open"][i], quote["high"][i],
                      quote["low"][i], quote["close"][i])
        v = quote["volume"][i]
        if None in (o, h, l, c):
            continue
        rows.append({
            "date": datetime.fromtimestamp(stamp, tz=timezone.utc).date().isoformat(),
            "open": float(o), "high": float(h), "low": float(l),
            "close": float(c), "volume": float(v or 0),
        })
    meta = result.get("meta", {})
    return rows, meta


def sma(values, n):
    return statistics.mean(values[-n:]) if len(values) >= n else None


def ema_series(values, n):
    if len(values) < n:
        return []
    k = 2 / (n + 1)
    out = [statistics.mean(values[:n])]
    for v in values[n:]:
        out.append(v * k + out[-1] * (1 - k))
    return out


def rsi(values, n=14):
    if len(values) <= n:
        return None
    gains, losses = [], []
    for a, b in zip(values[-n - 1:-1], values[-n:]):
        change = b - a
        gains.append(max(change, 0.0))
        losses.append(max(-change, 0.0))
    avg_gain, avg_loss = statistics.mean(gains), statistics.mean(losses)
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def macd(values, fast=12, slow=26, signal=9):
    if len(values) < slow + signal:
        return None, None, None
    ef, es = ema_series(values, fast), ema_series(values, slow)
    offset = len(ef) - len(es)
    line = [f - s for f, s in zip(ef[offset:], es)]
    sig = ema_series(line, signal)
    if not sig:
        return line[-1], None, None
    return line[-1], sig[-1], line[-1] - sig[-1]


def atr(rows, n=14):
    if len(rows) <= n:
        return None
    trs = []
    for prev, cur in zip(rows[-n - 1:-1], rows[-n:]):
        trs.append(max(cur["high"] - cur["low"],
                       abs(cur["high"] - prev["close"]),
                       abs(cur["low"] - prev["close"])))
    return statistics.mean(trs)


def bollinger(values, n=20, k=2.0):
    if len(values) < n:
        return None, None, None
    window = values[-n:]
    mid = statistics.mean(window)
    sd = statistics.pstdev(window)
    return mid - k * sd, mid, mid + k * sd


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--symbol", required=True, help="Yahoo symbol, e.g. 1211.HK")
    parser.add_argument("--range", dest="window", default="1y",
                        help="1y, 2y, 5y - not max, which returns monthly bars")
    parser.add_argument("--source", choices=("yahoo", "opend"), default="yahoo",
                        help="yahoo (default) or opend for the broker gateway")
    parser.add_argument("--json", dest="json_out", help="also write the figures as JSON")
    args = parser.parse_args()

    try:
        if args.source == "opend":
            rows, meta = fetch_opend(args.symbol)
            source_label = ("OpenD gateway (broker feed), daily bars, "
                            "12 months")
        else:
            rows, meta = fetch(args.symbol, args.window)
            source_label = "Yahoo Finance chart API, {} range".format(args.window)
    except urllib.error.HTTPError as exc:
        print("Fetch failed: HTTP {} for {}".format(exc.code, args.symbol),
              file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print("Fetch failed: {}: {}".format(type(exc).__name__, str(exc)[:120]),
              file=sys.stderr)
        return 2
    if len(rows) < 30:
        print("Only {} rows returned - not enough to read. Check the symbol, or that "
              "the range was not silently downgraded to monthly bars.".format(len(rows)),
              file=sys.stderr)
        return 2

    closes = [r["close"] for r in rows]
    volumes = [r["volume"] for r in rows]
    last = rows[-1]
    currency = meta.get("currency", "")

    ma20, ma50, ma200 = sma(closes, 20), sma(closes, 50), sma(closes, 200)
    year = rows[-252:] if len(rows) >= 252 else rows
    hi52 = max(r["high"] for r in year)
    lo52 = min(r["low"] for r in year)
    avg_vol = sma([v for v in volumes if v], 20)
    rsi14 = rsi(closes)
    macd_line, macd_sig, macd_hist = macd(closes)
    atr14 = atr(rows)
    bb_lo, bb_mid, bb_hi = bollinger(closes)

    def pct(a, b):
        return None if not a or not b else (a / b - 1) * 100

    # Trend, from the moving-average stack. Comparing the highest high and lowest
    # low of each half of a window is too crude - a single spike in either half
    # flips the answer - so the stacked averages are used instead, with the swing
    # sequence reported separately as a supporting observation.
    recent = rows[-60:] if len(rows) >= 60 else rows
    mid = len(recent) // 2
    first_low = min(r["low"] for r in recent[:mid])
    second_low = min(r["low"] for r in recent[mid:])
    first_high = max(r["high"] for r in recent[:mid])
    second_high = max(r["high"] for r in recent[mid:])
    if second_high > first_high and second_low > first_low:
        swings = "a higher high and a higher low"
    elif second_high < first_high and second_low < first_low:
        swings = "a lower high and a lower low"
    else:
        swings = "no clean sequence - range or transition"

    if ma20 and ma50 and ma200:
        if last["close"] > ma20 > ma50 > ma200:
            trend = "stacked up - price above the 20-day, above the 50, above the 200"
        elif last["close"] < ma20 < ma50 < ma200:
            trend = "stacked down - price below the 20-day, below the 50, below the 200"
        elif last["close"] > ma200:
            trend = "above the 200-day but the shorter averages are not aligned"
        else:
            trend = "below the 200-day but the shorter averages are not aligned"
    else:
        trend = "not enough history for a 200-day average"

    print("# {}".format(args.symbol))
    print()
    print("Source: {}.  As of {} (last close).  {} observations.".format(
        source_label, last["date"], len(rows)))
    print()
    print("**This is a description of past prices, not a forecast. No recommendation is "
          "made or implied.**")
    print()
    print("| Measure | Value |")
    print("|---|---:|")
    print("| Last close | {:,.2f} {} |".format(last["close"], currency))
    print("| 20-day average | {} |".format(
        "{:,.2f}".format(ma20) if ma20 else "n/a"))
    print("| 50-day average | {} |".format(
        "{:,.2f}".format(ma50) if ma50 else "n/a"))
    print("| 200-day average | {} |".format(
        "{:,.2f}".format(ma200) if ma200 else "n/a"))
    if ma200:
        print("| Price vs 200-day | {:+.1f}% |".format(pct(last["close"], ma200)))
    print("| 52-week high | {:,.2f} ({:+.1f}%) |".format(
        hi52, pct(last["close"], hi52)))
    print("| 52-week low | {:,.2f} ({:+.1f}%) |".format(
        lo52, pct(last["close"], lo52)))
    if avg_vol:
        print("| Volume vs 20-day average | {:.2f}x |".format(last["volume"] / avg_vol))
    print("| Trend | {} |".format(trend))
    print("| Last 60 sessions | {} |".format(swings))
    print()
    print("## Indicators")
    print()
    print("| Indicator | Reading | What it says |")
    print("|---|---:|---|")
    if rsi14 is not None:
        note = "extreme" if rsi14 >= 70 or rsi14 <= 30 else "mid-range"
        print("| RSI(14) | {:.1f} | {} - proportion of recent movement that was up |".format(
            rsi14, note))
    if macd_line is not None:
        state = ("above" if macd_hist and macd_hist > 0 else "below")
        print("| MACD | line {:,.3f}, signal {} | momentum {} its signal line |".format(
            macd_line,
            "{:,.3f}".format(macd_sig) if macd_sig is not None else "n/a",
            state))
    if atr14 is not None:
        print("| ATR(14) | {:,.2f} ({:.1f}% of price) | average daily travel, "
              "used for stop distance |".format(atr14, atr14 / last["close"] * 100))
    if bb_lo is not None:
        width = (bb_hi - bb_lo) / bb_mid * 100
        position = (last["close"] - bb_lo) / (bb_hi - bb_lo) * 100
        if position < 0:
            where = "price is BELOW the lower band - a close outside the recent range"
        elif position > 100:
            where = "price is ABOVE the upper band - a close outside the recent range"
        else:
            where = "{:.0f}% of band".format(position)
        print("| Bollinger(20,2) | {}, width {:.1f}% | where price sits in its recent "
              "distribution |".format(where, width))
    print()
    print("## Levels implied by the data")
    print()
    print("- 60-session high: {:,.2f}".format(max(r["high"] for r in recent)))
    print("- 60-session low: {:,.2f}".format(min(r["low"] for r in recent)))
    if atr14:
        print("- One ATR below the last close: {:,.2f} (a stop here sits inside "
              "ordinary noise)".format(last["close"] - atr14))
        print("- Three ATR below the last close: {:,.2f} (a level rather than a "
              "noise stop)".format(last["close"] - 3 * atr14))
    print()
    print("To turn any of these into a position, the stop distance and the account's risk "
          "per trade are both required. See `references/risk-and-sizing.md`; without them "
          "a level is not actionable.")

    if args.json_out:
        from pathlib import Path
        Path(args.json_out).write_text(json.dumps({
            "symbol": args.symbol, "as_of": last["date"], "observations": len(rows),
            "last_close": last["close"], "currency": currency,
            "ma20": ma20, "ma50": ma50, "ma200": ma200,
            "high_52w": hi52, "low_52w": lo52,
            "rsi14": rsi14, "macd_line": macd_line, "macd_signal": macd_sig,
            "macd_histogram": macd_hist, "atr14": atr14,
            "bollinger": [bb_lo, bb_mid, bb_hi], "trend_60": trend,
        }, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
