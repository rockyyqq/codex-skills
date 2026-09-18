"""Self-contained checks for check_sources.py. Run directly; no pytest."""
import contextlib
import io
import sys
import tempfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import check_sources as cs

TODAY = date(2026, 9, 18)
FAILURES = []


def entry(**overrides):
    base = {
        "id": "SG-EXAMPLE-1",
        "title": "Example source",
        "url": "https://example.org/guidance",
        "class": "guideline",
        "verified_on": "2026-09-18",
        "review_by": "2027-09-18",
    }
    base.update(overrides)
    return base


def check(name, fn):
    try:
        fn()
        print(f"PASS  {name}")
    except AssertionError as exc:
        print(f"FAIL  {name} :: {exc}")
        FAILURES.append(name)


def quiet(fn, *args):
    """Run fn with its stdout swallowed, so an expected failure is not noise."""
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*args)


def test_valid_entry_has_no_problems():
    assert cs.problems([entry()], TODAY) == []


def test_unverified_status_is_a_problem():
    found = cs.problems([entry(status="unverified")], TODAY)
    assert any("unverified" in msg for _, msg in found), found


def test_past_review_date_is_a_problem():
    found = cs.problems([entry(review_by="2026-01-01")], TODAY)
    assert any("passed" in msg for _, msg in found), found


def test_missing_url_is_a_problem():
    found = cs.problems([entry(url="")], TODAY)
    assert any("missing url" in msg for _, msg in found), found


def test_unparseable_date_is_a_problem():
    found = cs.problems([entry(verified_on="September 2026")], TODAY)
    assert any("not an ISO date" in msg for _, msg in found), found


def test_missing_ledger_exits_nonzero():
    missing = Path(tempfile.gettempdir()) / "hv-nope-does-not-exist.json"
    assert quiet(cs.main, ["--ledger", str(missing)]) == 1


def test_invalid_json_exits_nonzero():
    bad = Path(tempfile.gettempdir()) / "hv-bad-ledger.json"
    bad.write_text("{not json", encoding="utf-8")
    assert quiet(cs.main, ["--ledger", str(bad)]) == 1


check("a valid entry has no problems", test_valid_entry_has_no_problems)
check("an unverified entry is a problem", test_unverified_status_is_a_problem)
check("a past review date is a problem", test_past_review_date_is_a_problem)
check("a missing url is a problem", test_missing_url_is_a_problem)
check("an unparseable date is a problem", test_unparseable_date_is_a_problem)
check("a missing ledger exits non-zero", test_missing_ledger_exits_nonzero)
check("invalid JSON exits non-zero", test_invalid_json_exits_nonzero)

if FAILURES:
    print(f"\n{len(FAILURES)} check(s) failed")
    sys.exit(1)
print("\nall source-ledger checks passed")
