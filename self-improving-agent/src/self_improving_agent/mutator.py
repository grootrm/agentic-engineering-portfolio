"""AST-level function-body replacement.

This is the mechanical core of the default rule-based proposer: given a
candidate's source and the name of the function under test, splice in a
new function body while leaving the signature (name, arguments, return
annotation, decorators) untouched. Operating through the ``ast`` module
rather than string-splicing means the result is always re-parsed and
re-generated as syntactically valid Python before it is ever handed to
the evaluator -- a malformed mutation rule fails fast with a
``SyntaxError`` at proposal time, not as a mysterious test failure.
"""

from __future__ import annotations

import ast
import textwrap


class _BodyReplacer(ast.NodeTransformer):
    def __init__(self, function_name: str, new_body: list[ast.stmt]):
        self.function_name = function_name
        self.new_body = new_body
        self.found = False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        if node.name == self.function_name:
            node.body = self.new_body
            self.found = True
            return node
        return node


def replace_function_body(source: str, function_name: str, new_body_source: str) -> str:
    """Return ``source`` with ``function_name``'s body replaced.

    Args:
        source: Full module source containing a ``def function_name(...):``.
        function_name: Name of the function whose body should be replaced.
        new_body_source: Python statements (as source text) to use as the
            new function body.

    Raises:
        SyntaxError: if ``source`` or ``new_body_source`` is not valid Python.
        LookupError: if no top-level function named ``function_name`` exists
            in ``source``.
    """
    tree = ast.parse(textwrap.dedent(source))
    new_body = ast.parse(textwrap.dedent(new_body_source)).body

    replacer = _BodyReplacer(function_name, new_body)
    transformed = replacer.visit(tree)

    if not replacer.found:
        raise LookupError(f"no function named '{function_name}' found in source")

    ast.fix_missing_locations(transformed)
    return ast.unparse(transformed)
