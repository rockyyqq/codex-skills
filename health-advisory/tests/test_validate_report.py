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

Retention: superseded by the next report.
"""

CLEAN_REVIEW = """# Household review — 2026-09-18

**Status: DUE**

## Facts

- child-a / SB708H: pre-operative step outstanding, planned 2027-02-01

## Assumption-dependent — questions for a clinician

- nothing to raise

## Cannot judge

- nothing outstanding

Retention: replaced by the next review.

## What this is not

These checks being up to date does **not** mean anyone is healthy.
"""

CLEAN_PACK = """<!-- kind: pack -->
# Consultation pack — 2026-09-18

## adult-a

### Who to see

An ENT, or the doctor named in the record.

### What to bring

- the timeline, dated 2026-02

### Questions to ask

- whether the nose and throat findings are one problem or two

Retention: replaced by the next pack.
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


def test_a_correct_pack_passes():
    assert vr.check(CLEAN_PACK) == []


def test_a_pack_is_detected_from_its_stamp():
    assert vr.detect_kind(CLEAN_PACK) == "pack"


def test_a_pack_missing_the_questions_block_is_rejected():
    found = vr.check(CLEAN_PACK.replace("### Questions to ask", "### Notes"))
    assert any("questions block" in problem for problem in found), found


def test_a_pack_missing_the_bring_block_is_rejected():
    found = vr.check(CLEAN_PACK.replace("### What to bring", "### Notes"))
    assert any("bring block" in problem for problem in found), found


def test_an_unstamped_pack_fails_closed_as_evidence():
    unstamped = CLEAN_PACK.replace("<!-- kind: pack -->\n", "")
    assert vr.detect_kind(unstamped) == "evidence"
    assert vr.check(unstamped) != []


def test_identifiers_are_filtered_in_a_pack_too():
    found = vr.check(CLEAN_PACK + "\nS1234567D\n")
    assert any("national ID" in problem for problem in found), found


def test_a_pack_cannot_assert_a_diagnosis():
    found = vr.check(CLEAN_PACK + "\nyou likely have influenza\n")
    assert any("diagnostic assertion" in problem for problem in found), found


def test_every_kind_requires_a_retention_statement():
    # The boundary document says reports carry a stated retention, and a rule
    # enforced for one report kind is a rule the next kind quietly escapes.
    for kind, text in (("evidence", CLEAN), ("review", CLEAN_REVIEW), ("pack", CLEAN_PACK)):
        found = vr.check(text.replace("Retention", "Note"))
        assert any("retention" in problem for problem in found), (kind, found)


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
check("a correct pack passes", test_a_correct_pack_passes)
check("a pack is detected from its stamp", test_a_pack_is_detected_from_its_stamp)
check("a pack missing Questions is rejected", test_a_pack_missing_the_questions_block_is_rejected)
check("a pack missing What to bring is rejected", test_a_pack_missing_the_bring_block_is_rejected)
check("an unstamped pack fails closed as evidence", test_an_unstamped_pack_fails_closed_as_evidence)
check("identifiers are filtered in a pack too", test_identifiers_are_filtered_in_a_pack_too)
check("a pack cannot assert a diagnosis", test_a_pack_cannot_assert_a_diagnosis)
check("every kind requires a retention statement", test_every_kind_requires_a_retention_statement)

if FAILURES:
    print(f"\n{len(FAILURES)} check(s) failed")
    sys.exit(1)
print("\nall report-validator checks passed")
