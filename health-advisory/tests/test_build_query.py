"""Self-contained checks for build_query.py. Run directly; no pytest."""
import contextlib
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import build_query as bq

FAILURES = []


def check(name, fn):
    try:
        fn()
        print(f"PASS  {name}")
    except AssertionError as exc:
        print(f"FAIL  {name} :: {exc}")
        FAILURES.append(name)


def quiet(fn, *args):
    """Run fn with its stdout swallowed, so an expected refusal is not noise."""
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*args)


def labels(text):
    return {label for label, _ in bq.find_personal(text)}


def test_relationship_is_detected():
    assert "relationship" in labels("my son has a fever")


def test_age_is_detected():
    assert "age" in labels("a 3-year-old with a rash")


def test_date_of_birth_is_detected():
    assert "date of birth" in labels("born 2019-04-02")


def test_national_id_is_detected():
    assert "national ID" in labels("S1234567D")


def test_location_is_detected():
    assert "location" in labels("is this common in Singapore")


def test_a_clinical_question_is_clean():
    assert bq.find_personal("warfarin and aspirin interaction") == []


def test_clinical_terms_are_joined_with_and():
    assert bq.build_query(["warfarin", "aspirin"]) == "warfarin AND aspirin"


def test_a_personal_question_is_refused():
    assert quiet(bq.main, ["--question", "my son has a fever"]) == 2


def test_a_clean_question_with_no_terms_is_used_directly():
    assert quiet(bq.main, ["--question", "warfarin and aspirin interaction"]) == 0


def test_an_empty_question_is_refused():
    assert quiet(bq.main, ["--question", "   "]) == 2


check("a relationship is detected", test_relationship_is_detected)
check("an age is detected", test_age_is_detected)
check("a date of birth is detected", test_date_of_birth_is_detected)
check("a national ID is detected", test_national_id_is_detected)
check("a location is detected", test_location_is_detected)
check("a clinical question is clean", test_a_clinical_question_is_clean)
check("terms are joined with AND", test_clinical_terms_are_joined_with_and)
check("a personal question is refused", test_a_personal_question_is_refused)
check("a clean question is used directly", test_a_clean_question_with_no_terms_is_used_directly)
check("an empty question is refused", test_an_empty_question_is_refused)

if FAILURES:
    print(f"\n{len(FAILURES)} check(s) failed")
    sys.exit(1)
print("\nall query-builder checks passed")
