"""Turn a household question into a de-identified search string.

This refuses rather than sanitises: if personal detail would leave the machine,
the query is rejected and the caller is told what to rewrite.

Exit codes: 0 a query was printed; 2 refused.
"""
import argparse
import re
import sys

PERSONAL_PATTERNS = (
    (re.compile(r"\b(?:my|our|his|her|their)\s+(?:son|daughter|wife|husband|mother|father|child|kid|baby)\b", re.I), "relationship"),
    (re.compile(r"\b\d{1,3}\s*(?:-|\s)?(?:year|yr|month|week|day)s?[-\s]?old\b", re.I), "age"),
    (re.compile(r"\b(?:i am|aged|age)\s*\d{1,3}\b", re.I), "age"),
    (re.compile(r"\b(?:19|20)\d{2}-\d{2}-\d{2}\b"), "date of birth"),
    (re.compile(r"\b[STFG]\d{7}[A-Z]\b"), "national ID"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"), "email"),
    (re.compile(r"\b(?:\+65|65)?\s?[689]\d{3}\s?\d{4}\b"), "phone"),
    (re.compile(r"\b(?:singapore|hong kong|shanghai|beijing|taipei)\b", re.I), "location"),
)


def find_personal(text):
    """Return (label, matched text) for every personal marker found."""
    hits = []
    for pattern, label in PERSONAL_PATTERNS:
        for match in pattern.finditer(text):
            hits.append((label, match.group(0)))
    return hits


def build_query(terms):
    return " AND ".join(term.strip() for term in terms if term.strip())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--question", required=True)
    parser.add_argument("--term", action="append", default=[],
                        help="a clinical term; repeat for more")
    args = parser.parse_args(argv)

    hits = find_personal(args.question)
    if hits:
        print("REFUSED: the question contains personal detail that must not leave the machine:")
        for label, text in hits:
            print(f"  {label}: {text!r}")
        print("Rewrite using clinical terms only, and pass them with --term.")
        return 2

    query = build_query(args.term) if args.term else args.question.strip()
    if not query:
        print("REFUSED: nothing to search.")
        return 2

    print(query)
    return 0


if __name__ == "__main__":
    sys.exit(main())
