#!/usr/bin/env python3
"""Index valuation from the China Securities Index Company - PE and dividend yield.

The endpoint is the official one AKShare uses, called directly:

    https://oss-ch.csindex.com.cn/static/html/csindex/public/uploads/file/
        autofile/indicator/{index_code}indicator.xls

It returns roughly a month of daily rows with the index price-earnings ratio and
dividend yield under two share-capital conventions: total share capital and
calculation share capital. Both are reported, because they are not the same
number and mixing them silently changes the answer.

Requires pandas and xlrd (`pip install xlrd`). It reads only; nothing is written
except the optional JSON.

Usage
-----
    python valuation.py
    python valuation.py --indices 000300,930955,H30269 --json out.json
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

SOURCE = ("https://oss-ch.csindex.com.cn/static/html/csindex/public/uploads/"
          "file/autofile/indicator/{}indicator.xls")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# The indices this household actually holds or is building toward, plus the
# broad mainland benchmark.
DEFAULT = ["000300", "930955", "H30269", "000905"]


def fetch(code: str):
    request = urllib.request.Request(SOURCE.format(code), headers=UA)
    with urllib.request.urlopen(request, timeout=40) as response:
        return response.read()


def parse(raw: bytes):
    import pandas as pd
    frame = pd.read_excel(io.BytesIO(raw))
    # The header is bilingual; match on the Chinese stem, which is stable.
    def col(stem):
        for name in frame.columns:
            if stem in str(name):
                return name
        return None

    date_col = col("日期")
    pe1, pe2 = col("市盈率1"), col("市盈率2")
    dy1, dy2 = col("股息率1"), col("股息率2")
    name_col = col("指数中文简称") or col("指数中文全称")
    frame = frame.sort_values(date_col)
    last = frame.iloc[-1]
    return {
        "code": str(last.get(col("指数代码"))),
        "name": str(last.get(name_col)),
        "date": str(last.get(date_col)),
        "pe_total_capital": float(last.get(pe1)),
        "pe_calculation_capital": float(last.get(pe2)),
        "dividend_yield_total_capital": float(last.get(dy1)),
        "dividend_yield_calculation_capital": float(last.get(dy2)),
        "rows": int(len(frame)),
        "range": "{} to {}".format(frame.iloc[0][date_col],
                                   frame.iloc[-1][date_col]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--indices", default=",".join(DEFAULT),
                        help="CSI index codes, comma-separated")
    parser.add_argument("--bond-yield", type=float, default=None,
                        help="optional 10-year government bond yield in percent, "
                             "for the earnings-yield comparison")
    parser.add_argument("--json", dest="json_out")
    args = parser.parse_args()

    results, failures = [], []
    for code in [c.strip() for c in args.indices.split(",") if c.strip()]:
        try:
            results.append(parse(fetch(code)))
        except urllib.error.HTTPError as exc:
            failures.append((code, "HTTP {}".format(exc.code)))
        except Exception as exc:  # noqa: BLE001
            failures.append((code, "{}: {}".format(type(exc).__name__,
                                                   str(exc)[:70])))

    if not results:
        print("No index returned data. Failures:", file=sys.stderr)
        for code, why in failures:
            print("  {}  {}".format(code, why), file=sys.stderr)
        return 2

    print("Source: China Securities Index Company, official indicator files.")
    print("Valuation date is the index's own, not the date of the request.")
    print()
    print("| Index | Date | P/E (total capital) | P/E (calc capital) | "
          "Dividend yield (total) | Dividend yield (calc) | Earnings yield |")
    print("|---|---|---:|---:|---:|---:|---:|")
    for r in results:
        earnings = 100 / r["pe_total_capital"]
        print("| {} {} | {} | {:.2f} | {:.2f} | {:.2f}% | {:.2f}% | {:.2f}% |".format(
            r["code"], r["name"], r["date"], r["pe_total_capital"],
            r["pe_calculation_capital"], r["dividend_yield_total_capital"],
            r["dividend_yield_calculation_capital"], earnings))
    print()
    print("Earnings yield is the inverse of the P/E: what the index earns per unit "
          "of price. It is the figure to compare with a bond yield, not the P/E itself.")

    if args.bond_yield is not None:
        print()
        print("Against a 10-year bond yield of {:.2f}%:".format(args.bond_yield))
        for r in results:
            earnings = 100 / r["pe_total_capital"]
            print("  {}: earnings yield {:.2f}% vs bond {:.2f}% = {:+.2f} points; "
                  "dividend yield {:.2f}% vs bond = {:+.2f} points".format(
                      r["code"], earnings, args.bond_yield,
                      earnings - args.bond_yield,
                      r["dividend_yield_total_capital"],
                      r["dividend_yield_total_capital"] - args.bond_yield))
    else:
        print()
        print("Supply --bond-yield to complete the comparison. Without the bond rate "
              "the earnings yield has nothing to be measured against.")

    for code, why in failures:
        print("\nFAILED {}: {}".format(code, why), file=sys.stderr)

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps({"results": results, "failures": failures}, indent=2),
            encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
