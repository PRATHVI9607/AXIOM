"""Unit tests for the AST parser (works with tree-sitter or the regex fallback)."""
from axiom.services.ast_service import content_hash, detect_language, function_id, get_parser

PY_SOURCE = '''
def add(a, b):
    return a + b

def process_payment(user, amount):
    db.execute(f"SELECT * FROM accounts WHERE id={user}")
    return charge(amount)
'''


def test_detect_language():
    assert detect_language("x.py") == "python"
    assert detect_language("x.ts") == "typescript"
    assert detect_language("x.go") == "go"
    assert detect_language("README.md") is None


def test_parse_python_functions():
    parser = get_parser()
    functions = parser.parse_file("sample.py", PY_SOURCE)
    names = {f.function_name for f in functions}
    assert "add" in names
    assert "process_payment" in names


def test_function_id_is_stable_and_prefixed():
    a = function_id("f.py", "foo", 10)
    b = function_id("f.py", "foo", 10)
    assert a == b and a.startswith("sha256:")


def test_calls_extracted():
    parser = get_parser()
    functions = parser.parse_file("sample.py", PY_SOURCE)
    pay = next(f for f in functions if f.function_name == "process_payment")
    assert "charge" in pay.calls


def test_content_hash_changes_with_text():
    assert content_hash("a") != content_hash("b")


def test_empty_and_unknown_files():
    parser = get_parser()
    assert parser.parse_file("empty.py", "") == []
    assert parser.parse_file("notes.txt", "hello") == []
