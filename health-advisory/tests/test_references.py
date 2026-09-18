"""Cross-checks that the reference prose agrees with the data files."""
import json
import sys
from pathlib import Path

REFS = Path(__file__).resolve().parent.parent / "references"
FAILURES = []


def check(name, fn):
    try:
        fn()
        print(f"PASS  {name}")
    except AssertionError as exc:
        print(f"FAIL  {name} :: {exc}")
        FAILURES.append(name)


def ladder_text():
    return (REFS / "source-ladder.md").read_text(encoding="utf-8")


def fields_text():
    return (REFS / "record-fields.md").read_text(encoding="utf-8")


def test_every_routed_source_class_is_in_the_ladder():
    routing = json.loads((REFS / "routing.json").read_text(encoding="utf-8"))
    wanted = {name for klass in routing["classes"] for name in klass["sources"]}
    text = ladder_text()
    missing = sorted(name for name in wanted if name not in text)
    assert not missing, f"routing names source classes absent from the ladder: {missing}"


def test_the_five_fall_throughs_are_documented():
    text = ladder_text().lower()
    for phrase in ("superseded", "does not fit", "empty", "inconclusive", "cannot answer"):
        assert phrase in text, f"the ladder does not mention the {phrase!r} fall-through"


def test_the_recency_lane_is_not_a_filter():
    text = ladder_text().lower()
    assert "lane, not a filter" in text, "the ladder does not state that recency is a lane"
    assert "nothing since" in text, "the ladder does not say emptiness is a finding"


def test_absence_of_evidence_is_stated():
    assert "not evidence of absence" in ladder_text().lower()


def test_blank_is_not_none():
    assert "blank" in fields_text().lower(), "record-fields does not rule on blank values"


def test_confirmation_dates_are_required():
    text = fields_text().lower()
    assert "confirmation date" in text or "last_confirmed" in text


def test_no_dose_field_exists():
    text = fields_text().lower().replace("no dose field", "")
    assert "dose field" not in text, "record-fields mentions a dose field; the schema must not have one"


check("every routed source class is in the ladder", test_every_routed_source_class_is_in_the_ladder)
check("the five fall-throughs are documented", test_the_five_fall_throughs_are_documented)
check("recency is a lane, not a filter", test_the_recency_lane_is_not_a_filter)
check("absence of evidence is stated", test_absence_of_evidence_is_stated)
check("blank is not none", test_blank_is_not_none)
check("confirmation dates are required", test_confirmation_dates_are_required)
check("no dose field exists", test_no_dose_field_exists)

if FAILURES:
    print(f"\n{len(FAILURES)} check(s) failed")
    sys.exit(1)
print("\nall reference checks passed")
