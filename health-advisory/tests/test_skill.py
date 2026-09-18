"""Self-contained checks on SKILL.md and its metadata. Run directly; no pytest."""
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
FAILURES = []


def check(name, fn):
    try:
        fn()
        print(f"PASS  {name}")
    except AssertionError as exc:
        print(f"FAIL  {name} :: {exc}")
        FAILURES.append(name)


def skill_text():
    return (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")


def frontmatter():
    text = skill_text()
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert match, "SKILL.md has no frontmatter block"
    fields = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    return fields


def test_name_matches_the_folder():
    assert frontmatter().get("name") == SKILL_DIR.name, frontmatter().get("name")


def test_the_description_states_the_boundary_early():
    description = frontmatter().get("description", "")
    first_clause = description.split(".")[0].lower()
    assert "never" in first_clause, f"the boundary is not in the first clause: {first_clause!r}"
    for word in ("diagnosis", "dosing", "triage"):
        assert word in description.lower(), f"the description never mentions {word}"


def test_the_description_routes_away():
    description = frontmatter().get("description", "").lower()
    assert "not for" in description, "the description does not say what it is not for"
    assert "research" in description, "the description does not hand evidence appraisal to research"


def test_the_gate_is_stated_as_running_first():
    text = skill_text().lower()
    assert "emergency gate" in text, "SKILL.md does not name the emergency gate"
    assert "before" in text, "SKILL.md does not say the gate runs before anything else"


def test_every_reference_file_is_named():
    missing = []
    for path in sorted((SKILL_DIR / "references").glob("*")):
        if path.is_file() and path.name not in skill_text():
            missing.append(path.name)
    assert not missing, f"SKILL.md never names: {missing}"


def test_every_script_is_named():
    missing = []
    for path in sorted((SKILL_DIR / "scripts").glob("*.py")):
        if path.name not in skill_text():
            missing.append(path.name)
    assert not missing, f"SKILL.md never names: {missing}"


def test_the_openai_yaml_exists_and_is_named():
    yaml_path = SKILL_DIR / "agents" / "openai.yaml"
    assert yaml_path.is_file(), "agents/openai.yaml is missing"
    assert "display_name" in yaml_path.read_text(encoding="utf-8")


check("the name matches the folder", test_name_matches_the_folder)
check("the description states the boundary early", test_the_description_states_the_boundary_early)
check("the description routes away", test_the_description_routes_away)
check("the gate is stated as running first", test_the_gate_is_stated_as_running_first)
check("every reference file is named", test_every_reference_file_is_named)
check("every script is named", test_every_script_is_named)
check("agents/openai.yaml exists", test_the_openai_yaml_exists_and_is_named)

if FAILURES:
    print(f"\n{len(FAILURES)} check(s) failed")
    sys.exit(1)
print("\nall skill checks passed")
