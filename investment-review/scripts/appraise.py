#!/usr/bin/env python3
"""Build the valuation-spread table and run the look-through for one instrument.

Section 6 of an investment review, plus section 7. It does arithmetic and text
search. It does not judge, rank or recommend, and it carries no entry, stop,
target or position size.

Config: a JSON file. Required keys: subject, hurdle. Optional: peers, household,
holdings_file, look_for.

    {
      "as_of": "2026-09-17",
      "hurdle":  { "name": "US 10-year", "rate": 0.05, "source": "...", "date": "..." },
      "subject": { "name": "...", "pe": 12.018, "dividend_yield": 0.0645 },
      "peers":   [ { "name": "...", "pe": 11.3, "dividend_yield": 0.0685 } ],
      "household": [ { "name": "...", "pe": 8.97, "dividend_yield": 0.0428 } ],
      "holdings_file": "household_holdings.json",
      "look_for": ["中国电信", "601728", "00728"]
    }

A missing required key exits 2 and names it. Nothing is defaulted into a report.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REQUIRED = ("subject", "hurdle")


def earnings_yield(pe: float | None) -> float | None:
    if pe is None:
        return None
    try:
        pe = float(pe)
    except (TypeError, ValueError):
        return None
    return 1.0 / pe if pe > 0 else None


def row(item: dict, hurdle: float) -> str:
    ey = earnings_yield(item.get("pe"))
    dy = item.get("dividend_yield")
    spread = (ey - hurdle) if ey is not None else None
    return "| {} | {} | {} | {} | {} |".format(
        item.get("name", "?"),
        "{:.2f}".format(float(item["pe"])) if item.get("pe") else "-",
        "{:.2f}%".format(ey * 100) if ey is not None else "-",
        "{:.2f}%".format(float(dy) * 100) if dy else "-",
        ("**{:+.2f}**".format(spread * 100) if spread is not None else "-"),
    )


def look_through(path: Path, needles: list[str]) -> list[str]:
    """Search a holdings or config file for the instrument, by name or code."""
    if not path.exists():
        return ["Holdings file not found: {}".format(path)]
    text = path.read_text(encoding="utf-8", errors="replace")
    hits = [n for n in needles if n and n in text]
    if not hits:
        return ["No match for any of: {}".format(", ".join(needles))]
    out = []
    for n in hits:
        count = text.count(n)
        out.append("Found **{}** ({} occurrence{})".format(
            n, count, "" if count == 1 else "s"))
    out.append("")
    out.append("A name match is not proof of exposure. Check the wrapper, the "
               "weight and the report date before concluding.")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--out", type=Path, help="Write the report here instead of stdout.")
    args = ap.parse_args()

    if not args.config.exists():
        print("ERROR: config not found: {}".format(args.config), file=sys.stderr)
        return 2

    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    missing = [k for k in REQUIRED if k not in cfg]
    if missing:
        print("ERROR: config is missing required keys: {}".format(", ".join(missing)),
              file=sys.stderr)
        return 2

    hurdle = float(cfg["hurdle"]["rate"])
    lines: list[str] = []
    lines.append("# Valuation spread")
    lines.append("")
    lines.append("As of {}. Hurdle: **{}** at **{:.2f}%**{}.".format(
        cfg.get("as_of", "date not given"),
        cfg["hurdle"].get("name", "unnamed"),
        hurdle * 100,
        ", source " + str(cfg["hurdle"]["source"]) if cfg["hurdle"].get("source") else "",
    ))
    lines.append("")
    lines.append("A positive spread means the price buys more earnings than the "
                 "safe alternative. It is a statement about today's relative "
                 "pricing, not a forecast.")
    lines.append("")
    lines.append("| | P/E | Earnings yield | Dividend yield | Spread vs hurdle |")
    lines.append("|---|---:|---:|---:|---:|")
    lines.append(row(cfg["subject"], hurdle))
    for p in cfg.get("peers", []):
        lines.append(row(p, hurdle))
    for h in cfg.get("household", []):
        lines.append(row(h, hurdle))

    if cfg.get("look_for"):
        lines.append("")
        lines.append("## Look-through")
        lines.append("")
        target = Path(cfg["holdings_file"]) if cfg.get("holdings_file") else None
        if target is None:
            lines.append("No holdings file given.")
        else:
            for l in look_through(target, cfg["look_for"]):
                lines.append(l)

    lines.append("")
    lines.append("## What this does not do")
    lines.append("")
    lines.append("It does not say whether to buy, hold or sell. It does not read "
                 "the price history - that belongs to technical-analysis. It "
                 "does not size a position. Peers must be supplied, because a "
                 "multiple quoted from memory is not evidence.")
    report = "\n".join(lines) + "\n"

    if args.out:
        args.out.write_text(report, encoding="utf-8")
        print("Written to {}".format(args.out))
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
