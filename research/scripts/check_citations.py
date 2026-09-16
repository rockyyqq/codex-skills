#!/usr/bin/env python3
"""Mechanical citation checks between a draft and a BibTeX bibliography.

What this catches
-----------------
  - citations in the draft with no matching bibliography entry
  - bibliography entries the draft never cites
  - duplicate DOIs, and near-duplicate titles
  - entries sharing a trial registration identifier, which usually means one
    study reported several times rather than several studies
  - missing DOI or year
  - numeric citation markers that fall outside the bibliography
  - references with no link at all, so a reader cannot get to them
  - links that will not last: shorteners, search URLs, and profile pages
  - with --verify-links, DOIs that do not resolve against Crossref

What this cannot catch
----------------------
Whether a source actually supports the sentence citing it, whether a quotation is
verbatim, and whether a work has been retracted. Those require reading and a
network lookup. They are covered in references/citation-verification.md and are
the reason this script is a gate, not the whole check.

Assumptions
-----------
  - Pandoc citations ([@key], [@a; @b]) are matched by key. A bare @key is only
    treated as a citation when it matches an existing key, so email addresses and
    handles are ignored.
  - LaTeX \\cite-family commands are matched by key.
  - Numeric markers like [3] or [4-6] are assumed to index the bibliography in
    file order. The script reports out-of-range markers only; it does not attempt
    to confirm that entry 4 is the work the author meant.
  - A .docx draft must be converted to text first.

Usage
-----
    python check_citations.py --draft manuscript.md --bib refs.bib
    python check_citations.py --draft manuscript.md --bib refs.bib --json out.json
    python check_citations.py --draft manuscript.md --bib refs.bib --verify-links

--verify-links contacts Crossref and therefore needs network access. Without it
the script is entirely offline.

Exit codes
----------
  0  nothing blocking found
  1  a structural problem: a citation with no bibliography entry, an
     out-of-range numeric marker, or a reference with no DOI and no URL
  2  the draft or bibliography could not be read
  3  the only blocking problem is a DOI that does not resolve

The most fundamental problem is reported, so a run with both a missing citation
and a dead DOI exits 1. The report always lists both.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

CROSSREF = "https://api.crossref.org/works/{}"

# Links that a reader will not be able to follow later. A reference has to be
# trackable, so a link that decays is worse than no link only in that it looks
# like one.
UNSTABLE_LINKS = [
    (r"bit\.ly|tinyurl\.com|goo\.gl|t\.co/|ow\.ly|buff\.ly|is\.gd|shorturl\.|amzn\.to",
     "URL shortener - the target cannot be verified or cited"),
    (r"scholar\.google\.", "Google Scholar link - not a source link"),
    (r"(?:google|bing)\.com/search", "search result URL - not a stable page"),
    (r"researchgate\.net", "ResearchGate URL - unstable and often withdrawn"),
    (r"^http://", "not https"),
]

REGISTRATION_PATTERNS = [
    ("NCT", re.compile(r"\bNCT\d{8}\b", re.I)),
    ("ISRCTN", re.compile(r"\bISRCTN\d{8}\b", re.I)),
    ("ACTRN", re.compile(r"\bACTRN\d{14}\b", re.I)),
    ("ChiCTR", re.compile(r"\bChiCTR[\w\-]{6,}\b", re.I)),
    ("ANZCTR", re.compile(r"\bACTRN\d{14}\b", re.I)),
    ("DRKS", re.compile(r"\bDRKS\d{8}\b", re.I)),
    ("EudraCT", re.compile(r"\b\d{4}-\d{6}-\d{2}\b")),
]

PROTOCOL_FIELD_HINTS = ("note", "annote", "keywords", "url", "howpublished",
                        "abstract", "eprint", "comment")


def strip_braces(text: str) -> str:
    """Remove one layer of grouping braces and collapse whitespace."""
    text = text.replace("\n", " ")
    while text.startswith("{") and text.endswith("}") and len(text) > 1:
        text = text[1:-1]
    return re.sub(r"\s+", " ", text).strip()


def parse_bib(text: str) -> list[dict]:
    """Minimal BibTeX reader. Returns a list of {key, type, fields} dicts."""
    entries: list[dict] = []
    index = 0
    length = len(text)
    while index < length:
        at = text.find("@", index)
        if at < 0:
            break
        brace = text.find("{", at)
        if brace < 0:
            break
        entry_type = text[at + 1:brace].strip().lower()
        if entry_type in ("comment", "preamble", "string"):
            index = brace + 1
            continue
        # Walk to the matching close brace, tracking nesting.
        depth = 0
        position = brace
        while position < length:
            char = text[position]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    break
            position += 1
        body = text[brace + 1:position]
        index = position + 1

        comma = body.find(",")
        if comma < 0:
            continue
        key = body[:comma].strip()
        fields: dict[str, str] = {}
        for name, value in re.findall(
                r"(\w+)\s*=\s*(\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}|\"[^\"]*\"|[^,\n]+)",
                body[comma + 1:]):
            fields[name.lower()] = strip_braces(
                value.strip().rstrip(",").strip().strip('"'))
        entries.append({"key": key, "type": entry_type, "fields": fields})
    return entries


def normalise_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]", "", title.lower())


def normalise_doi(doi: str) -> str:
    doi = doi.strip().lower()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)
    return doi.rstrip(".")


def extract_key_citations(draft: str, known_keys: set[str]) -> dict[str, int]:
    counts: dict[str, int] = {}

    def record(key: str) -> None:
        key = key.strip().rstrip(".,;:")
        if key:
            counts[key] = counts.get(key, 0) + 1

    # Pandoc bracket citations: [@key] or [@a; @b; @c]
    bracket_groups = re.findall(r"\[[^\]]*@[^\]]*\]", draft)
    for group in bracket_groups:
        for key in re.findall(r"@([A-Za-z0-9_:.\-]+)", group):
            record(key)

    # LaTeX \cite family
    latex = (r"\\(?:cite|citep|citet|citealp|citeauthor|citeyear|autocite"
             r"|parencite|textcite)\*?(?:\[[^\]]*\])*\{([^}]*)\}")
    for group in re.findall(latex, draft):
        for key in group.split(","):
            record(key)

    # Bare pandoc @key, only when it matches a known key. Bracket groups are
    # removed first so a [@key] citation is not also counted as a bare one.
    remainder = re.sub(r"\[[^\]]*@[^\]]*\]", " ", draft)
    for match in re.finditer(r"(?:^|[\s(\[])(@[A-Za-z0-9_:.\-]+)", remainder):
        key = match.group(1)[1:]
        if key in known_keys:
            record(key)

    return counts


def extract_numeric_citations(draft: str) -> set[int]:
    found: set[int] = set()
    for group in re.findall(r"\[(\d+(?:\s*[,\-]\s*\d+)*)\]", draft):
        for part in group.split(","):
            part = part.strip()
            if "-" in part:
                low, _, high = part.partition("-")
                try:
                    found.update(range(int(low), int(high) + 1))
                except ValueError:
                    continue
            elif part.isdigit():
                found.add(int(part))
    return found


def registrations(entry: dict) -> set[str]:
    found: set[str] = set()
    for name, value in entry["fields"].items():
        if name in ("doi", "title", "author", "journal", "booktitle"):
            continue
        for label, pattern in REGISTRATION_PATTERNS:
            for match in pattern.findall(value):
                found.add(label_match(label, match))
    # Identifiers are often pasted into any field; sweep the rest as a fallback.
    if not found:
        blob = " ".join(entry["fields"].values())
        for label, pattern in REGISTRATION_PATTERNS:
            for match in pattern.findall(blob):
                found.add(label_match(label, match))
    return found


def label_match(label: str, match: str) -> str:
    """Prefix the registry name unless the identifier already carries it."""
    upper = match.upper()
    if upper.startswith(label.upper()):
        return upper
    return "{}:{}".format(label, upper)


def verify_dois(pairs: list[tuple[str, str]], timeout: float = 20.0,
                pause: float = 0.4, limit: int = 200) -> dict[str, list]:
    """Resolve DOIs against Crossref. Needs network access."""
    resolved: list[str] = []
    unresolved: list[tuple[str, str]] = []
    errors: list[tuple[str, str]] = []
    for key, doi in pairs[:limit]:
        url = CROSSREF.format(urllib.parse.quote(doi))
        request = urllib.request.Request(url, headers={
            "User-Agent": "check_citations/1.0 (mailto:research@example.org)",
            "Accept": "application/json",
        })
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                if response.status == 200:
                    resolved.append(key)
                else:
                    unresolved.append((key, doi))
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                unresolved.append((key, doi))
            elif exc.code == 429:
                errors.append((key, "rate limited by Crossref - rerun later"))
            else:
                errors.append((key, "HTTP {}".format(exc.code)))
        except Exception as exc:  # noqa: BLE001
            errors.append((key, "{}: {}".format(type(exc).__name__, str(exc)[:60])))
        time.sleep(pause)
    return {"resolved": resolved, "unresolved": unresolved, "errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--draft", required=True,
                        help="manuscript, abstract or report (.md, .txt, .tex)")
    parser.add_argument("--bib", required=True, help="BibTeX bibliography")
    parser.add_argument("--json", dest="json_out", help="also write results as JSON")
    parser.add_argument("--verify-links", action="store_true",
                        help="resolve each DOI against Crossref (needs network)")
    args = parser.parse_args()

    draft_path = Path(args.draft)
    bib_path = Path(args.bib)
    for path in (draft_path, bib_path):
        if not path.is_file():
            print("ERROR: not found: {}".format(path), file=sys.stderr)
            return 2

    draft = draft_path.read_text(encoding="utf-8", errors="replace")
    entries = parse_bib(bib_path.read_text(encoding="utf-8", errors="replace"))
    known_keys = {entry["key"] for entry in entries}

    cited = extract_key_citations(draft, known_keys)
    numeric = extract_numeric_citations(draft)

    dangling = sorted(key for key in cited if key not in known_keys)
    uncited = sorted(key for key in known_keys if key not in cited)

    doi_map: dict[str, list[str]] = {}
    title_map: dict[str, list[str]] = {}
    registration_map: dict[str, list[str]] = {}
    missing_doi: list[str] = []
    missing_year: list[str] = []
    untrackable: list[str] = []
    unstable: list[tuple[str, str, str]] = []
    doi_pairs: list[tuple[str, str]] = []

    for entry in entries:
        fields = entry["fields"]
        key = entry["key"]
        doi = normalise_doi(fields.get("doi", ""))
        url = (fields.get("url") or "").strip()
        if doi:
            doi_map.setdefault(doi, []).append(key)
            doi_pairs.append((key, doi))
        else:
            missing_doi.append(key)
        if not doi and not url:
            untrackable.append(key)
        if url:
            for pattern, reason in UNSTABLE_LINKS:
                if re.search(pattern, url, re.I):
                    unstable.append((key, url, reason))
                    break
        if not fields.get("year"):
            missing_year.append(key)
        title = normalise_title(fields.get("title", ""))
        if title and len(title) > 15:
            title_map.setdefault(title, []).append(key)
        for identifier in registrations(entry):
            registration_map.setdefault(identifier, []).append(key)

    duplicate_dois = {doi: keys for doi, keys in doi_map.items() if len(keys) > 1}
    duplicate_titles = {t: keys for t, keys in title_map.items() if len(keys) > 1}
    shared_registrations = {reg: keys for reg, keys in registration_map.items()
                            if len(set(keys)) > 1}
    out_of_range = sorted(n for n in numeric if n < 1 or n > len(entries))
    numeric_uncited = sorted(set(range(1, len(entries) + 1)) - numeric) if numeric else []

    link_check = None
    if args.verify_links and doi_pairs:
        print("Resolving {} DOI(s) against Crossref...\n".format(len(doi_pairs)),
              file=sys.stderr)
        link_check = verify_dois(doi_pairs)

    lines: list[str] = []
    lines.append("# Citation check")
    lines.append("")
    lines.append("Draft: `{}`  ".format(draft_path.name))
    lines.append("Bibliography: `{}` - {} entries  ".format(bib_path.name, len(entries)))
    lines.append("Key citations found: {}   Numeric markers found: {}"
                 .format(sum(cited.values()), len(numeric)))
    lines.append("")

    lines.append("## Citations with no bibliography entry")
    lines.append("")
    if dangling:
        lines.append("**BLOCKING** - each of these is cited but missing from the "
                     "bibliography:")
        lines.append("")
        for key in dangling:
            lines.append("- `{}` (cited {}x)".format(key, cited[key]))
    else:
        lines.append("None. Every key citation resolved.")
    lines.append("")

    lines.append("## Bibliography entries never cited")
    lines.append("")
    if uncited:
        for key in uncited:
            lines.append("- `{}`".format(key))
    else:
        lines.append("None.")
    lines.append("")

    lines.append("## Possible duplicate records")
    lines.append("")
    if duplicate_dois or duplicate_titles:
        for doi, keys in sorted(duplicate_dois.items()):
            lines.append("- DOI `{}` in: {}".format(
                doi, ", ".join("`{}`".format(k) for k in keys)))
        for title, keys in sorted(duplicate_titles.items()):
            lines.append("- Same title in: {}".format(
                ", ".join("`{}`".format(k) for k in keys)))
    else:
        lines.append("None detected by DOI or title.")
    lines.append("")

    lines.append("## Entries that may report one study")
    lines.append("")
    if shared_registrations:
        lines.append("These share a trial registration, so they are usually one "
                     "study reported more than once. Count the study once:")
        lines.append("")
        for reg, keys in sorted(shared_registrations.items()):
            unique = sorted(set(keys))
            lines.append("- `{}` -> {}".format(
                reg, ", ".join("`{}`".format(k) for k in unique)))
    else:
        lines.append("No shared registration identifiers found. This is not proof "
                     "of independence - check sample sizes, recruitment periods and "
                     "author overlap as well.")
    lines.append("")

    lines.append("## Missing metadata")
    lines.append("")
    lines.append("- No DOI: {}".format(
        ", ".join("`{}`".format(k) for k in missing_doi) if missing_doi else "none"))
    lines.append("- No year: {}".format(
        ", ".join("`{}`".format(k) for k in missing_year) if missing_year else "none"))
    lines.append("")

    if numeric:
        lines.append("## Numeric markers")
        lines.append("")
        if out_of_range:
            lines.append("**BLOCKING** - these fall outside the {} bibliography "
                         "entries: {}".format(
                             len(entries),
                             ", ".join("[{}]".format(n) for n in out_of_range)))
        else:
            lines.append("All numeric markers fall within range (assuming the "
                         "bibliography is numbered in file order).")
        if numeric_uncited:
            lines.append("")
            if len(numeric_uncited) == len(entries):
                lines.append("No entry is referenced by number - the draft cites "
                             "by key while numeric markers appear elsewhere. Check "
                             "that the two styles are not meant to match.")
            else:
                preview = ", ".join(str(n) for n in numeric_uncited[:20])
                lines.append("Entries never referenced by number: {}".format(preview))
        lines.append("")

    lines.append("## Trackability")
    lines.append("")
    if untrackable:
        lines.append("**BLOCKING** - no DOI and no URL, so a reader cannot retrieve "
                     "these:")
        lines.append("")
        for key in untrackable:
            lines.append("- `{}`".format(key))
        lines.append("")
    else:
        lines.append("Every entry carries a DOI or a URL.")
        lines.append("")
    if unstable:
        lines.append("Links that will not last:")
        lines.append("")
        for key, url, reason in unstable:
            lines.append("- `{}`: {} - {}".format(key, url[:70], reason))
        lines.append("")

    if link_check is not None:
        lines.append("## DOI resolution")
        lines.append("")
        lines.append("Checked {} DOI(s) against Crossref.".format(
            len(link_check["resolved"]) + len(link_check["unresolved"])
            + len(link_check["errors"])))
        lines.append("")
        if link_check["unresolved"]:
            lines.append("**BLOCKING** - these DOIs do not resolve, so either the "
                         "identifier or the entry is wrong:")
            lines.append("")
            for key, doi in link_check["unresolved"]:
                lines.append("- `{}` -> `{}`".format(key, doi))
            lines.append("")
        if link_check["errors"]:
            lines.append("Not checked - these are not evidence that the DOI is "
                         "wrong, only that the check did not complete:")
            lines.append("")
            for key, reason in link_check["errors"]:
                lines.append("- `{}`: {}".format(key, reason))
            lines.append("")
        if not link_check["unresolved"] and not link_check["errors"]:
            lines.append("All DOIs resolved.")
            lines.append("")

    lines.append("## Still to do by hand")
    lines.append("")
    lines.append("- Confirm each source actually supports its sentence.")
    lines.append("- Confirm every quotation is verbatim in the retrieved text.")
    lines.append("- Check the cited works for retractions and corrections.")
    lines.append("- Recount studies rather than references.")
    lines.append("- Match the draft to the author's own writing conventions "
                 "(references/writing-style.md).")

    report = "\n".join(lines)
    print(report)

    if args.json_out:
        Path(args.json_out).write_text(json.dumps({
            "draft": str(draft_path),
            "bib": str(bib_path),
            "entries": len(entries),
            "dangling_citations": dangling,
            "uncited_entries": uncited,
            "duplicate_dois": duplicate_dois,
            "duplicate_titles": duplicate_titles,
            "shared_registrations": shared_registrations,
            "missing_doi": missing_doi,
            "missing_year": missing_year,
            "numeric_out_of_range": out_of_range,
            "untrackable_entries": untrackable,
            "unstable_links": [{"key": k, "url": u, "reason": r}
                               for k, u, r in unstable],
            "doi_resolution": None if link_check is None else {
                "resolved": link_check["resolved"],
                "unresolved": [{"key": k, "doi": d}
                               for k, d in link_check["unresolved"]],
                "errors": [{"key": k, "reason": r}
                           for k, r in link_check["errors"]],
            },
        }, indent=2), encoding="utf-8")

    if dangling or out_of_range or untrackable:
        return 1
    if link_check is not None and link_check["unresolved"]:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
