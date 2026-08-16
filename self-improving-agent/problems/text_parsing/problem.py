"""The ``text_parsing`` demo problem: incrementally correct CSV line splitting.

The seed candidate is deliberately naive (``line.split(",")``), which is
correct only for plain, unquoted fields. Each :class:`MutationRule` below
is a complete replacement body -- not a diff -- for
``split_csv_line``'s function body, each one strictly more capable than
the last:

1. ``strip_whitespace`` -- strips whitespace around each field.
2. ``handle_quoted_fields`` -- tracks quote state so commas inside a
   quoted field aren't treated as separators.
3. ``handle_escaped_quotes`` -- treats a doubled quote inside a quoted
   field (``""``) as an escaped literal quote, the standard CSV
   convention.

Every later rule's body still handles everything the rules before it
handled, so :meth:`~self_improving_agent.archive.Archive.try_add`'s
strict-superset requirement is satisfiable at every generation.
"""

from __future__ import annotations

from pathlib import Path

from self_improving_agent.problem import MutationRule, Problem

SEED_SOURCE = '''\
def split_csv_line(line: str) -> list[str]:
    return line.split(",")
'''

_STRIP_WHITESPACE = """\
fields = line.split(",")
return [field.strip() for field in fields]
"""

_HANDLE_QUOTED_FIELDS = '''\
fields = []
current = []
in_quotes = False
for ch in line:
    if in_quotes:
        if ch == \'"\':
            in_quotes = False
        else:
            current.append(ch)
    else:
        if ch == \'"\':
            in_quotes = True
        elif ch == ",":
            fields.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
fields.append("".join(current).strip())
return fields
'''

_HANDLE_ESCAPED_QUOTES = '''\
fields = []
current = []
in_quotes = False
i = 0
n = len(line)
while i < n:
    ch = line[i]
    if in_quotes:
        if ch == \'"\':
            if i + 1 < n and line[i + 1] == \'"\':
                current.append(\'"\')
                i += 2
                continue
            in_quotes = False
        else:
            current.append(ch)
    else:
        if ch == \'"\':
            in_quotes = True
        elif ch == ",":
            fields.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    i += 1
fields.append("".join(current).strip())
return fields
'''

MUTATION_RULES = (
    MutationRule(
        name="strip_whitespace",
        description="Strip leading/trailing whitespace from each field.",
        new_body_source=_STRIP_WHITESPACE,
    ),
    MutationRule(
        name="handle_quoted_fields",
        description="Track quote state so commas inside quoted fields aren't split on.",
        new_body_source=_HANDLE_QUOTED_FIELDS,
    ),
    MutationRule(
        name="handle_escaped_quotes",
        description="Treat a doubled quote inside a quoted field as an escaped literal quote.",
        new_body_source=_HANDLE_ESCAPED_QUOTES,
    ),
)

PROBLEM = Problem(
    name="text_parsing",
    module_name="text_parsing",
    function_name="split_csv_line",
    seed_source=SEED_SOURCE,
    test_file=Path(__file__).parent / "test_text_parsing.py",
    mutation_rules=MUTATION_RULES,
)
