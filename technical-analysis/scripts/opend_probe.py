#!/usr/bin/env python3
"""Test whether Futu / moomoo OpenD is reachable, and read from it if it is.

OpenD is a separate desktop application - a local gateway that holds the broker
session and serves quotes and history to the SDK over 127.0.0.1:11111. Neither
the futu nor the moomoo Python SDK can fetch anything without it running and
logged in.

This script checks the port first, because that answers the question in under a
second and without loading the SDK. If the port is open it connects, pulls a
snapshot and daily bars, and reports what came back.

Running this needs normal (unsandboxed) permissions: the SDK creates its log
directory under AppData\\Roaming on import.

Usage
-----
    python opend_probe.py
    python opend_probe.py --symbols HK.01211,SH.000300,US.QQQ
"""

from __future__ import annotations

import argparse
import socket
import sys

DEFAULT_SYMBOLS = ["HK.01211", "SH.000300", "US.QQQ", "SG.ES3"]

INSTALL_STEPS = """
OpenD is not reachable, so no data can be read yet. To fix that:

  1. Download OpenD - a separate desktop application, not the trading client:
       moomoo accounts   -> moomoo.com  -> OpenAPI -> OpenD
       Futu accounts     -> futunn.com -> OpenAPI -> OpenD
     Pick the build that matches the account you will log in with.

  2. Launch it and log in. OpenD holds the session, so quotes come through
     your account and your quote entitlements.

  3. Leave it running. It listens on 127.0.0.1:11111 by default.

  4. Re-run this script.

One caveat worth knowing before trusting the output: real-time quotes are
entitled per market. Without a quote right you get delayed or snapshot-only
data. Historical daily bars are usually available more freely than live ticks.
"""


def port_open(host: str, port: int, timeout: float = 2.0) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        return sock.connect_ex((host, port)) == 0


def load_sdk():
    for name, label in (("futu", "futu-api"), ("moomoo", "moomoo-api")):
        try:
            return __import__(name), label
        except ImportError:
            continue
    return None, None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--symbols", default=",".join(DEFAULT_SYMBOLS),
                        help="comma-separated, e.g. HK.01211,SH.000300")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=11111)
    parser.add_argument("--bars", type=int, default=30,
                        help="daily bars to fetch per symbol")
    args = parser.parse_args()

    print("OpenD check - {}:{}".format(args.host, args.port))
    if not port_open(args.host, args.port):
        print("  port CLOSED - nothing is listening")
        print(INSTALL_STEPS)
        return 1
    print("  port OPEN - OpenD appears to be running")

    sdk, label = load_sdk()
    if sdk is None:
        print("  no SDK installed. Run:  pip install futu-api   (or moomoo-api)")
        return 2
    print("  using {}".format(label))

    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    ctx = sdk.OpenQuoteContext(host=args.host, port=args.port)
    try:
        # One symbol at a time. A batch fails as a whole if any single symbol
        # lacks a quote entitlement, which hides which one is the problem.
        print("\n  Snapshots (one call per symbol):")
        for symbol in symbols:
            ret, snapshot = ctx.get_market_snapshot([symbol])
            if ret != 0:
                print("    {:12} FAILED  {}".format(symbol, str(snapshot)[:120]))
                continue
            row = snapshot.iloc[0]
            last = row.get("last_price")
            prev = row.get("prev_close_price")
            # Compute the change rather than reading a field whose name varies
            # between SDK versions.
            try:
                change = (float(last) / float(prev) - 1) * 100
                change_text = "{:+.2f}%".format(change)
            except (TypeError, ValueError, ZeroDivisionError):
                change_text = "n/a"
            print("    {:12} last {:>10}  prev {:>10}  {:>8}  vol {:>14}".format(
                symbol, last, prev, change_text, row.get("volume")))

        # get_cur_kline requires an active subscription; request_history_kline
        # does not, so it is tried first and the subscribed call as a fallback.
        #
        # The trap: max_count takes bars FORWARD from the start date. Asking for
        # max_count=30 with start=None therefore returns the OLDEST thirty bars of
        # the default window - about a year stale - and looks like current data.
        # So the full window is requested and the most recent bars taken from the
        # end. With start=None the default window is the last twelve months.
        print("\n  Daily bars:")
        for symbol in symbols:
            kline = None
            if hasattr(ctx, "request_history_kline"):
                ret, data, _ = ctx.request_history_kline(
                    symbol, start=None, end=None, ktype=sdk.KLType.K_DAY,
                    max_count=1000)
                if ret == 0 and data is not None and len(data):
                    kline = data.sort_values("time_key").tail(args.bars)
            if kline is None:
                ret, _ = ctx.subscribe(symbol, [sdk.SubType.K_DAY],
                                       subscribe_push=False)
                ret, data = ctx.get_cur_kline(symbol, num=args.bars,
                                              ktype=sdk.KLType.K_DAY)
                if ret == 0:
                    kline = data
                else:
                    print("    {:12} FAILED  {}".format(symbol, str(data)[:120]))
                    continue
            print("    {} - {} bars; most recent:".format(symbol, len(kline)))
            for _, row in kline.tail(3).iterrows():
                print("       {}  O {:>9}  H {:>9}  L {:>9}  C {:>9}".format(
                    row.get("time_key"), row.get("open"), row.get("high"),
                    row.get("low"), row.get("close")))
    finally:
        ctx.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
