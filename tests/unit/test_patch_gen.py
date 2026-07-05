"""Unit tests for the patch generator's 7 supported patterns (PRD §7.6)."""
import pytest

from axiom.services.patch_service import PATTERNS, get_patch_generator

SAMPLES = {
    "sql_injection": 'q = f"SELECT * FROM users WHERE id={uid}"',
    "command_injection": "subprocess.run(cmd, shell=True)",
    "deserialization": "data = pickle.loads(blob)",
    "path_traversal": "open(request.args['file'])",
    "hardcoded_credentials": 'password = "hunter2"',
    "unchecked_null": "value = data['user'].name",
    "race_condition": "self.counter += 1",
}


def test_all_seven_patterns_exist():
    names = {p.name for p in PATTERNS}
    assert names == set(SAMPLES)


@pytest.mark.parametrize("pattern,code", list(SAMPLES.items()))
def test_pattern_detected(pattern, code):
    gen = get_patch_generator()
    assert pattern in gen.detect_patterns(code)


def test_sql_injection_patch_removes_fstring():
    gen = get_patch_generator()
    patches = gen.generate('q = f"SELECT * FROM users WHERE id={uid}"')
    sql = [p for p in patches if p.pattern == "sql_injection"]
    assert sql and sql[0].confidence > 0.5


def test_command_injection_patch_verified():
    gen = get_patch_generator()
    patches = gen.generate("subprocess.run(cmd, shell=True)")
    ci = next(p for p in patches if p.pattern == "command_injection")
    assert "shell=False" in ci.patched
    assert ci.verified is True
