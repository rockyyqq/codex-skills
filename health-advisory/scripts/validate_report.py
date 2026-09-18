"""Reject a generated report that carries identifiers or unsourced claims.

Exit codes: 0 the report passes; 1 problems found.
"""
import argparse
import re
import sys
from pathlib import Path

IDENTIFIERS = (
    (re.compile(r"\b[STFG]\d{7}[A-Z]\b"), "national ID"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "email"),
    (re.compile(r"\b(?:\+65|65)?\s?[689]\d{3}\s?\d{4}\b"), "phone"),
    (re.compile(r"\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(?:19|20)\d{2}\b"), "exact date of birth"),
)

ASSERTIONS = (
    (re.compile(r"\b(?:you|he|she|they)\s+(?:likely\s+)?(?:has|have)\b", re.I), "diagnostic assertion"),
    (re.compile(r"\bthe diagnosis is\b", re.I), "diagnostic assertion"),
    (re.compile(r"\bstop taking\b", re.I), "treatment instruction"),
    (re.compile(r"\btake\s+\d+(?:\.\d+)?\s?mg\b", re.I), "dose instruction"),
    (re.compile(r"\bincrease the dose\b", re.I), "dose instruction"),
)

REQUIRED = (
    ("## Evidence", "no Evidence section"),
    ("Last 12 months", "no recency block"),
    ("Sources", "no Sources block"),
    ("http", "no resolvable source link"),
)


def check(text):
    """Return a list of problems. An empty list means the report passes."""
    found = []
    for needle, message in REQUIRED:
        if needle not in text:
            found.append(message)
    for pattern, label in IDENTIFIERS + ASSERTIONS:
        for match in pattern.finditer(text):
            found.append(f"{label}: {match.group(0)!r}")
    return found


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report")
    args = parser.parse_args(argv)

    path = Path(args.report)
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"FAIL: report not found: {path}")
        return 1

    found = check(text)
    if found:
        print(f"FAIL: {len(found)} problem(s) in {path.name}")
        for problem in found:
            print(f"  {problem}")
        return 1
    print(f"OK: {path.name} carries no identifiers and no unsourced claims")
    return 0


if __name__ == "__main__":
    sys.exit(main())
