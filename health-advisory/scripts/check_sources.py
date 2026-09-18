"""Fail on any source entry that is unverified or past its review date.

Exit codes: 0 all entries valid; 1 problems found or the ledger is unreadable.
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

REQUIRED = ("id", "title", "url", "class", "verified_on", "review_by")
DEFAULT_LEDGER = Path(__file__).resolve().parent.parent / "references" / "sources.json"


def load(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def parse_day(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def problems(entries, today):
    """Return (id, message) for every entry that cannot be trusted."""
    found = []
    for index, source in enumerate(entries):
        identifier = source.get("id") or f"entry #{index + 1}"
        for key in REQUIRED:
            if not source.get(key):
                found.append((identifier, f"missing {key}"))
        for key in ("verified_on", "review_by"):
            value = source.get(key)
            if value and parse_day(value) is None:
                found.append((identifier, f"{key} is not an ISO date: {value!r}"))
        if source.get("status") == "unverified":
            found.append((identifier, "status is unverified"))
        review = parse_day(source.get("review_by"))
        if review and review < today:
            found.append((identifier, f"review date {review.isoformat()} has passed"))
    return found


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    parser.add_argument("--today", default=None, help="override today's date, for testing")
    args = parser.parse_args(argv)

    today = date.fromisoformat(args.today) if args.today else date.today()
    try:
        data = load(args.ledger)
    except FileNotFoundError:
        print(f"FAIL: ledger not found: {args.ledger}")
        return 1
    except json.JSONDecodeError as exc:
        print(f"FAIL: ledger is not valid JSON: {exc}")
        return 1

    entries = data.get("sources", [])
    found = problems(entries, today)
    if found:
        print(f"FAIL: {len(found)} problem(s) across {len(entries)} entr(ies)")
        for identifier, message in found:
            print(f"  {identifier}: {message}")
        return 1
    print(f"OK: {len(entries)} source(s) verified, none past review")
    return 0


if __name__ == "__main__":
    sys.exit(main())
