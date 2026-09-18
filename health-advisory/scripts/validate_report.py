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

EVIDENCE_REQUIRED = (
    ("## Evidence", "no Evidence section"),
    ("Last 12 months", "no recency block"),
    ("Sources", "no Sources block"),
    ("http", "no resolvable source link"),
)

# A household review is a different document from an evidence report, and
# demanding an Evidence section of it fails a correct report. A gate that
# fires falsely teaches the operator to bypass it, which is worse than no gate.
REVIEW_REQUIRED = (
    ("## Facts", "no Facts section"),
    ("## Assumption-dependent", "no assumption-dependent section"),
    ("## Cannot judge", "no Cannot-judge section"),
    ("status:", "no status line"),
)


def detect_kind(text):
    """Evidence if it says so; review if it carries either review marker.

    A document with neither falls through to evidence, which has the stricter
    required list - an unrecognised report fails closed rather than passing.
    """
    stamped = re.search(r"<!--\s*kind:\s*(evidence|review)\s*-->", text)
    if stamped:
        return stamped.group(1)
    lowered = text.lower()
    if "## evidence" in lowered:
        return "evidence"
    if "## facts" in lowered or "## cannot judge" in lowered:
        return "review"
    return "evidence"


def check(text, kind=None):
    """Return a list of problems. An empty list means the report passes."""
    kind = kind or detect_kind(text)
    required = REVIEW_REQUIRED if kind == "review" else EVIDENCE_REQUIRED
    found = []
    # Case-insensitive: a section heading or a status line may be capitalised,
    # and a gate that fails on capitalisation is a gate people learn to bypass.
    lowered = text.lower()
    for needle, message in required:
        if needle.lower() not in lowered:
            found.append(message)
    for pattern, label in IDENTIFIERS + ASSERTIONS:
        for match in pattern.finditer(text):
            found.append(f"{label}: {match.group(0)!r}")
    return found


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report")
    parser.add_argument("--kind", choices=("evidence", "review"), default=None,
                        help="override the detected report kind")
    args = parser.parse_args(argv)

    path = Path(args.report)
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"FAIL: report not found: {path}")
        return 1

    kind = args.kind or detect_kind(text)
    found = check(text, kind)
    if found:
        print(f"FAIL: {len(found)} problem(s) in {path.name} ({kind})")
        for problem in found:
            print(f"  {problem}")
        return 1
    print(f"OK: {path.name} ({kind}) carries no identifiers and no unsourced claims")
    return 0


if __name__ == "__main__":
    sys.exit(main())
