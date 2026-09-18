"""Self-contained checks for urgency.json. Run directly; no pytest."""
import json
import sys
from datetime import date
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


def urgency():
    return json.loads((REFS / "urgency.json").read_text(encoding="utf-8"))


def ledger_ids():
    ledger = json.loads((REFS / "singapore-sources.json").read_text(encoding="utf-8"))
    return {source["id"] for source in ledger["sources"]}


def test_there_is_at_least_one_entry():
    assert urgency()["entries"], "the gate has no entries"


def test_every_entry_has_an_action():
    for entry in urgency()["entries"]:
        assert entry.get("action"), f"{entry.get('id')} has no action"


def test_every_entry_cites_a_ledger_source():
    known = ledger_ids()
    for entry in urgency()["entries"]:
        assert entry.get("source_id") in known, f"{entry.get('id')} cites unknown source {entry.get('source_id')!r}"


def test_every_entry_has_a_future_review_date():
    today = date.today()
    for entry in urgency()["entries"]:
        review = date.fromisoformat(entry["review_by"])
        assert review >= today, f"{entry.get('id')} review date {review} has passed"


def test_entry_ids_are_unique():
    ids = [entry["id"] for entry in urgency()["entries"]]
    assert len(ids) == len(set(ids)), f"duplicate id in {ids}"


def test_the_gate_states_it_runs_first():
    assert urgency()["runs_before"] == "all"


def test_every_action_escalates_and_none_de_escalates():
    banned = ("no need", "not serious", "nothing to worry", "wait and see")
    for entry in urgency()["entries"]:
        lowered = entry["action"].lower()
        for phrase in banned:
            assert phrase not in lowered, f"{entry.get('id')} de-escalates: {entry['action']!r}"


check("there is at least one entry", test_there_is_at_least_one_entry)
check("every entry has an action", test_every_entry_has_an_action)
check("every entry cites a ledger source", test_every_entry_cites_a_ledger_source)
check("every entry has a future review date", test_every_entry_has_a_future_review_date)
check("entry ids are unique", test_entry_ids_are_unique)
check("the gate states it runs first", test_the_gate_states_it_runs_first)
check("no action de-escalates", test_every_action_escalates_and_none_de_escalates)

if FAILURES:
    print(f"\n{len(FAILURES)} check(s) failed")
    sys.exit(1)
print("\nall urgency-gate checks passed")
