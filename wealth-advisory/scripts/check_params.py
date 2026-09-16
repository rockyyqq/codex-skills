#!/usr/bin/env python3
"""Gate the parameter file before any deliverable depends on it.

The skill says an unverified parameter must never pass silently. Until now only
the parameters a single script happened to read were reported, so an unverified
entry nothing used went unnoticed, and a parameter could stay past its review
date for years.

This reads the whole file and reports every entry that is unverified or past its
review date, whoever uses it.

Usage:
  python check_params.py [--params references/sg-parameters-2026.json]
                         [--max-age-days 400] [--json out.json]

Exit codes:
  0  every parameter confirmed and inside its review window
  1  at least one parameter is unverified, or past its review date
  2  the parameter file could not be read
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import die, emit, load_json, table, today  # noqa: E402

DEFAULT_PARAMS = Path(__file__).resolve().parent.parent / "references" / "sg-parameters-2026.json"
DEFAULT_MAX_AGE_DAYS = 400


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify every dated parameter.")
    parser.add_argument("--params", default=str(DEFAULT_PARAMS))
    parser.add_argument(
        "--max-age-days", type=int, default=DEFAULT_MAX_AGE_DAYS,
        help="Parameters confirmed longer ago than this are due for review. Default 400 "
             "days, because the Singapore Budget revises the tax parameters each February.",
    )
    parser.add_argument("--json", dest="json_out")
    parser.add_argument("--out")
    args = parser.parse_args()

    payload = load_json(args.params)
    params = payload.get("parameters") if isinstance(payload, dict) else None
    if not isinstance(params, dict):
        die("{} does not contain a 'parameters' object.".format(args.params))

    reference = date.today()
    unverified, overdue, confirmed = [], [], []
    for key, entry in sorted(params.items()):
        if not isinstance(entry, dict):
            continue
        verified_on = entry.get("verified_on")
        if not verified_on:
            unverified.append({"key": key, "source": entry.get("source"), "as_of": entry.get("as_of")})
            continue
        try:
            age = (reference - date.fromisoformat(str(verified_on))).days
        except ValueError:
            unverified.append({"key": key, "source": entry.get("source"), "as_of": entry.get("as_of")})
            continue
        record = {"key": key, "verified_on": str(verified_on), "age_days": age,
                  "source": entry.get("source")}
        (overdue if age > args.max_age_days else confirmed).append(record)

    problems = unverified + overdue
    lines = ["# Parameter verification", ""]
    lines.append(
        "File reviewed {}; checked {}. {} entries; {} confirmed inside the {}-day window, "
        "{} unverified, {} overdue for review. Read {}.".format(
            payload.get("last_reviewed", "unknown"), today(), len(confirmed) + len(overdue) + len(unverified),
            len(confirmed), args.max_age_days, len(unverified), len(overdue), args.params,
        )
    )
    lines.append("")
    if unverified:
        lines.append("## Unverified - do not rely on these")
        lines.append("")
        lines.append(table(
            ["Parameter", "As of", "Source"],
            [[u["key"], u["as_of"] or "-", u["source"] or "-"] for u in unverified],
        ))
        lines.append("")
        lines.append(
            "Each of these was entered without being read from its source. Confirm it, set "
            "`verified_on`, then run this again. A deliverable that depends on one of these "
            "must say so."
        )
        lines.append("")
    if overdue:
        lines.append("## Confirmed, but due for review")
        lines.append("")
        lines.append(table(
            ["Parameter", "Verified on", "Days ago", "Source"],
            [[o["key"], o["verified_on"], o["age_days"], o["source"] or "-"] for o in overdue],
        ))
        lines.append("")
        lines.append(
            "Singapore revises these at each Budget, usually in February. Past the window, "
            "re-read the source rather than carrying the figure forward."
        )
        lines.append("")
    if not problems:
        lines.append("Every parameter in the file is confirmed and inside its review window.")
        lines.append("")

    raw = {
        "as_of": today(),
        "params_path": str(args.params),
        "max_age_days": args.max_age_days,
        "unverified": unverified,
        "overdue": overdue,
        "confirmed": confirmed,
        "ok": not problems,
    }
    emit("\n".join(lines), out_path=args.out, raw=raw, json_path=args.json_out)
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
