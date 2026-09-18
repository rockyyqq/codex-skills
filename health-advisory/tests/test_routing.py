"""Self-contained checks for routing.json. Run directly; no pytest."""
import json
import sys
from pathlib import Path

ROUTING = Path(__file__).resolve().parent.parent / "references" / "routing.json"
FAILURES = []


def check(name, fn):
    try:
        fn()
        print(f"PASS  {name}")
    except AssertionError as exc:
        print(f"FAIL  {name} :: {exc}")
        FAILURES.append(name)


def data():
    return json.loads(ROUTING.read_text(encoding="utf-8"))


def test_every_class_has_a_process():
    for klass in data()["classes"]:
        assert klass.get("process"), f"{klass.get('id')} has no process"


def test_every_class_has_a_boolean_evidence_sweep():
    for klass in data()["classes"]:
        assert isinstance(klass.get("evidence_sweep"), bool), f"{klass.get('id')} evidence_sweep is not boolean"


def test_every_class_names_at_least_one_source():
    for klass in data()["classes"]:
        assert klass.get("sources"), f"{klass.get('id')} names no source"


def test_class_ids_are_unique():
    ids = [klass["id"] for klass in data()["classes"]]
    assert len(ids) == len(set(ids)), f"duplicate class id in {ids}"


def test_the_gate_runs_before_everything():
    assert data()["gate"]["runs_before"] == "all"


def test_routing_is_announced():
    assert data()["announce"] is True


def test_only_effectiveness_questions_get_a_literature_sweep():
    sweeping = [k["id"] for k in data()["classes"] if k["evidence_sweep"]]
    assert sweeping == ["effectiveness"], f"unexpected sweep classes: {sweeping}"


check("every class has a process", test_every_class_has_a_process)
check("every class has a boolean evidence_sweep", test_every_class_has_a_boolean_evidence_sweep)
check("every class names a source", test_every_class_names_at_least_one_source)
check("class ids are unique", test_class_ids_are_unique)
check("the gate runs before everything", test_the_gate_runs_before_everything)
check("routing is announced", test_routing_is_announced)
check("only effectiveness gets a literature sweep", test_only_effectiveness_questions_get_a_literature_sweep)

if FAILURES:
    print(f"\n{len(FAILURES)} check(s) failed")
    sys.exit(1)
print("\nall routing checks passed")
