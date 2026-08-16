"""Frozen acceptance suite for the ``text_parsing`` demo problem.

This file is ``Problem.test_file`` -- the Evaluator copies it, unmodified,
next to each candidate's source and runs it as-is. It is not collected by
this project's own top-level ``pytest`` run (``testpaths = ["tests"]`` in
``pyproject.toml`` excludes it); it only runs inside the Evaluator's
isolated temp directory, against whichever candidate is under test.

Cases are grouped by the failure mode they exercise, in the order the
demo's mutation rules fix them: the naive seed (``line.split(",")``)
passes only the plain-field cases; each later rule adds a graduated
capability (whitespace stripping, then quote-aware splitting, then
escaped-quote handling) without regressing any earlier case.
"""

from text_parsing import split_csv_line


# -- passes at the seed: plain, unquoted fields -----------------------------


def test_simple_two_fields():
    assert split_csv_line("a,b") == ["a", "b"]


def test_simple_three_fields():
    assert split_csv_line("1,2,3") == ["1", "2", "3"]


def test_single_field_no_comma():
    assert split_csv_line("solo") == ["solo"]


def test_empty_field_at_end():
    assert split_csv_line("a,b,") == ["a", "b", ""]


# -- needs the "strip_whitespace" mutation -----------------------------------


def test_strips_leading_trailing_whitespace():
    assert split_csv_line(" a , b , c ") == ["a", "b", "c"]


def test_strips_whitespace_around_empty_field():
    assert split_csv_line("a, ,c") == ["a", "", "c"]


# -- needs the "handle_quoted_fields" mutation -------------------------------


def test_quoted_field_with_comma():
    assert split_csv_line('"a,b",c') == ["a,b", "c"]


def test_quoted_field_with_multiple_commas():
    assert split_csv_line('"a,b,c",d') == ["a,b,c", "d"]


def test_quoted_field_with_surrounding_whitespace():
    assert split_csv_line(' "a,b" , c ') == ["a,b", "c"]


# -- needs the "handle_escaped_quotes" mutation ------------------------------


def test_quoted_field_with_escaped_quotes():
    assert split_csv_line('"say ""hi""",bye') == ['say "hi"', "bye"]


def test_quoted_field_only_escaped_quotes():
    assert split_csv_line('"""hello"""') == ['"hello"']
