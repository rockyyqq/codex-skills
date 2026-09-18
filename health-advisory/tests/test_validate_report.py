"""Self-contained checks for validate_report.py. Run directly; no pytest."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import validate_report as vr

FAILURES = []

CLEAN = """# Household review

## Evidence
**Reviews** — nothing fits this question (search logged 2026-09-18).
**Last 12 months** — nothing since 2024-03-01.

**Sources**
- https://www.moh.gov.sg/ (verified 2026-09-18)
"""

CLEAN_REVIEW = """# Household review — 2026-09-18

**Status: DUE**

## Facts

- child-a / SB708H: pre-operative step outstanding, planned 2027-02-01

## Assumption-dependent — questions for a clinician

- nothing to raise

## Cannot judge

- nothing outstanding

## What this is not

These checks being up to date does **not** mean anyone is healthy.
"""


def check(name, fn):
    try:
        fn()
        print(f"PASS  {name}")
    except AssertionError as exc:
        print(f"FAIL  {name} :: {exc}")
        FAILURES.append(name)


def test_a_clean_report_passes():
    assert vr.check(CLEAN) == []


def test_a_national_id_is_rejected():
    found = vr.check(CLEAN + "\nS1234567D\n")
    assert any("national ID" in problem for problem in found), found


def test_an_email_is_rejected():
    found = vr.check(CLEAN + "\nreach me at a@b.com\n")
    assert any("email" in problem for problem in found), found


def test_a_diagnostic_assertion_is_rejected():
    found = vr.check(CLEAN + "\nyou likely have influenza\n")
    assert any("diagnostic assertion" in problem for problem in found), found


def test_a_dose_instruction_is_rejected():
    found = vr.check(CLEAN + "\ntake 500 mg twice a day\n")
    assert any("dose instruction" in problem for problem in found), found


def test_a_missing_recency_block_is_rejected():
    found = vr.check(CLEAN.replace("**Last 12 months** — nothing since 2024-03-01.", ""))
    assert any("recency" in problem for problem in found), found


def test_a_missing_evidence_section_is_rejected():
    found = vr.check("# Household review\n\nnothing here\n")
    assert any("Evidence section" in problem for problem in found), found


def test_a_correct_review_passes():
    assert vr.check(CLEAN_REVIEW) == []


def test_a_review_is_detected_as_a_review():
    assert vr.detect_kind(CLEAN_REVIEW) == "review"


def test_an_evidence_report_is_detected_as_evidence():
    assert vr.detect_kind(CLEAN) == "evidence"


def test_a_kind_stamp_beats_inference():
    stamped = "<!-- kind: review -->\n# Household review\n\n## Evidence\n"
    assert vr.detect_kind(stamped) == "review"


def test_a_review_missing_the_cannot_judge_section_is_rejected():
    found = vr.check(CLEAN_REVIEW.replace("## Cannot judge", "## Notes"))
    assert any("Cannot-judge" in problem for problem in found), found


def test_a_national_id_in_a_review_is_filtered_not_ignored():
    found = vr.check(CLEAN_REVIEW + "\nS1234567D\n")
    assert any("national ID" in problem for problem in found), found


check("a clean report passes", test_a_clean_report_passes)
check("a national ID is rejected", test_a_national_id_is_rejected)
check("an email is rejected", test_an_email_is_rejected)
check("a diagnostic assertion is rejected", test_a_diagnostic_assertion_is_rejected)
check("a dose instruction is rejected", test_a_dose_instruction_is_rejected)
check("a missing recency block is rejected", test_a_missing_recency_block_is_rejected)
check("a missing Evidence section is rejected", test_a_missing_evidence_section_is_rejected)
check("a correct review passes", test_a_correct_review_passes)
check("a review is detected as a review", test_a_review_is_detected_as_a_review)
check("an evidence report is detected as evidence", test_an_evidence_report_is_detected_as_evidence)
check("a kind stamp beats inference", test_a_kind_stamp_beats_inference)
check("a review missing Cannot-judge is rejected", test_a_review_missing_the_cannot_judge_section_is_rejected)
check("identifiers are filtered in a review too", test_a_national_id_in_a_review_is_filtered_not_ignored)

if FAILURES:
    print(f"\n{len(FAILURES)} check(s) failed")
    sys.exit(1)
print("\nall report-validator checks passed")
