#!/usr/bin/env python3
"""Check a finished deliverable against the rules that make it defensible.

deliverables.md says every document the skill produces carries six things. Until now
that was prose, enforced by whoever assembled the document remembering it. This script
reads the finished file and fails it instead.

It checks structure and disclosure, not arithmetic. A document can pass this and still
be wrong; it cannot pass this and be missing its assumptions.

Profiles
--------
  full        The default. The six universals from deliverables.md:
              assumptions, parameter verification status, basis note, scope and
              not-licensed-advice statement, risk mandate, protection status.
  continuity  The continuity pack is explicitly not an investment document in
              deliverables.md, so the investment checks are replaced by that pack's own
              requirements: who to contact, where accounts are held, cover and how to
              claim, nominations, the will and named guardian, Lasting Power of
              Attorney, property and guarantees, and what the survivor should do first.
              It also fails the document if it contains a password, which the pack is
              explicit about.

Usage:
  python validate_deliverable.py <deliverable.md> [--profile full|continuity]

Exit codes:
  0  OK
  1  FAIL, with a named reason for every missing item
  2  the file could not be read
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


MIN_CHARACTERS = 500

COMMON_CHECKS = [
    (
        "assumptions",
        r"^#{1,6}[^\n]*\bassumptions?\b",
        "No assumptions section. Every material assumption, its value and where it came from.",
    ),
    (
        "verification",
        r"(?i)(parameter verification|verification status|unverified|confirmed against)",
        "No parameter-verification status. State which dated parameters were confirmed and which remain unconfirmed.",
    ),
    (
        "basis",
        r"(?is)(today'?s dollars|nominal dollars|real terms|in nominal terms).{0,400}?\b(SGD|USD|HKD|CNY|CNH|RMB|EUR|GBP|JPY|AUD|CHF)\b"
        r"|\b(SGD|USD|HKD|CNY|CNH|RMB|EUR|GBP|JPY|AUD|CHF)\b.{0,400}?(today'?s dollars|nominal dollars|real terms|in nominal terms)",
        "No basis note tying the figures to today's dollars or nominal dollars and naming the reporting currency.",
    ),
    (
        "scope",
        r"(?i)(not licensed|does not constitute|not (?:financial|investment) advice|for the household to decide|a draft .{0,40}decide|scope and status)",
        "No scope and status statement. Say that this is a draft for the household to decide on, not licensed advice.",
    ),
    (
        "mandate",
        r"^#{1,6}[^\n]*\bmandate\b|\brisk mandate\b",
        "No risk mandate. The limits the portfolio is measured against, in the household's own words.",
    ),
    (
        "protection",
        r"^#{1,6}[^\n]*\bprotection\b|\bprotection (?:status|review|layer)\b",
        "No protection status. What the death, disability, illness and care layers cover, and where the gaps are.",
    ),
]

CONTINUITY_CHECKS = [
    ("contacts", r"(?i)\bcontacts?\b", "No contacts section - adviser, lawyer, accountant, agent, employer."),
    ("accounts", r"(?i)\baccounts?\b", "No list of where the accounts are held, and in whose name."),
    ("cover", r"(?is)\b(cover|policy|policies)\b.{0,300}?\bclaim", "No cover section explaining how to claim, with policy numbers."),
    ("nominations", r"(?i)\bnominations?\b", "No CPF and SRS nominations, and where the originals are kept."),
    ("will", r"(?is)\bwill\b.{0,300}?\bguardian", "No will and named guardian."),
    ("lpa", r"(?i)(lasting power of attorney|\bLPA\b)", "No Lasting Power of Attorney, or no statement of what it does and does not cover."),
    ("property", r"(?i)\b(property|properties|loans?|guarantees?)\b", "No property, loans or guarantees given."),
    ("first_steps", r"(?is)(what to do|should and should not do|first steps?|in plain language)", "No plain-language statement of what the surviving spouse should do first."),
]


def validate(text: str, profile: str) -> list[str]:
    issues: list[str] = []

    if len(text.strip()) < MIN_CHARACTERS:
        issues.append(
            "The document is only {} characters. That is too short to carry the required "
            "sections - check you are validating the finished deliverable.".format(
                len(text.strip())
            )
        )

    checks = CONTINUITY_CHECKS if profile == "continuity" else COMMON_CHECKS
    flags = re.MULTILINE | re.IGNORECASE
    for _key, pattern, message in checks:
        if not re.search(pattern, text, flags=flags):
            issues.append(message)

    if profile == "continuity":
        # Only an actual credential is a failure. A statement that the pack holds no
        # passwords, or that says where they are kept, is exactly what it should say.
        if re.search(r"(?im)^.{0,80}\b(passwords?|passcodes?|pins?)\b\s*[:=]", text):
            issues.append(
                "The continuity pack appears to contain an actual password or PIN. "
                "deliverables.md is explicit that it must not. Remove the value and say "
                "where the credentials are held instead."
            )

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("deliverable", type=Path, help="The finished markdown deliverable.")
    parser.add_argument(
        "--profile",
        choices=("full", "continuity"),
        default="full",
        help="Which set of requirements to apply. Default full.",
    )
    args = parser.parse_args()

    try:
        text = args.deliverable.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        print("ERROR: file not found: {}".format(args.deliverable), file=sys.stderr)
        return 2
    except OSError as exc:
        print("ERROR: could not read {}: {}".format(args.deliverable, exc), file=sys.stderr)
        return 2

    issues = validate(text, args.profile)
    if issues:
        print("FAIL")
        for issue in issues:
            print("- {}".format(issue))
        return 1

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
