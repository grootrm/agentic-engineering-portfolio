"""Tests for the AST-level function-body replacement used by the proposer."""

import pytest

from self_improving_agent.mutator import replace_function_body


def test_replaces_body_of_named_function():
    source = """
def solve(line):
    return line.split(",")
"""
    new_body = 'return ["mutated"]'

    result = replace_function_body(source, "solve", new_body)

    namespace: dict = {}
    exec(result, namespace)
    assert namespace["solve"]("a,b,c") == ["mutated"]


def test_preserves_function_signature():
    source = """
def solve(line: str) -> list:
    return line.split(",")
"""
    new_body = "return []"

    result = replace_function_body(source, "solve", new_body)

    assert "def solve(line: str) -> list:" in result


def test_leaves_other_functions_untouched():
    source = """
def helper(x):
    return x * 2


def solve(line):
    return line.split(",")
"""
    new_body = "return []"

    result = replace_function_body(source, "solve", new_body)

    namespace: dict = {}
    exec(result, namespace)
    assert namespace["helper"](3) == 6
    assert namespace["solve"]("anything") == []


def test_result_is_syntactically_valid_python():
    source = """
def solve(line):
    return line.split(",")
"""
    new_body = """
fields = []
for part in line.split(","):
    fields.append(part.strip())
return fields
"""

    result = replace_function_body(source, "solve", new_body)

    compile(result, "<mutated>", "exec")  # raises SyntaxError if invalid


def test_raises_lookup_error_when_function_name_is_missing():
    source = """
def other(line):
    return line
"""

    with pytest.raises(LookupError, match="solve"):
        replace_function_body(source, "solve", "return []")


def test_raises_syntax_error_for_malformed_new_body():
    source = """
def solve(line):
    return line
"""

    with pytest.raises(SyntaxError):
        replace_function_body(source, "solve", "this is not : valid python (")
