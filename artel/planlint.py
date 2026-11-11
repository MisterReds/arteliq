"""Plan lint: what code can tell about a submitted plan before any work starts (docs/ORCHESTRATION.md §4).

Structure (unique keys, criteria, dependency graph) is validated when the plan is submitted. The lint adds what makes
a plan checkable: every task has a check, no check is one that cannot fail, assignees exist, check programs exist.
"""

from __future__ import annotations

import shlex
from collections.abc import Callable

CANNOT_FAIL = {"true", ":", "echo", "printf"}  # as a whole command, without an operator after them
OPERATORS = ("&&", "||", "|", ";", ">", "<", "`", "$(")


def cannot_fail(check: str) -> bool:
    """An empty check, or a lone ``true`` / ``:`` / ``echo`` / ``printf``: it passes whatever the worker did."""
    try:
        words = shlex.split(check)
    except ValueError:
        return False
    return not words or (words[0] in CANNOT_FAIL and not any(op in check for op in OPERATORS))


def lint_plan(workers: list, tasks: list, missing: Callable[[list], list]) -> list[dict]:
    """Findings ``{"rule", "task", "detail"}`` in task order. ``missing(checks)`` names the programs of those
    checks that are not installed (injected, so the function itself touches nothing)."""
    names = {w.get("name") for w in workers}
    found: list[dict] = []
    for t in tasks:
        key, checks = t.get("key"), [str(c) for c in t.get("checks") or []]
        if not checks:
            found.append({"rule": "no_checks", "task": key, "detail": "no check command"})
        found += [{"rule": "trivial_check", "task": key, "detail": c.strip()[:120]} for c in checks if cannot_fail(c)]
        if t.get("assignee") and t["assignee"] not in names:
            found.append({"rule": "unknown_assignee", "task": key, "detail": str(t["assignee"])})
        found += [{"rule": "missing_program", "task": key, "detail": prog} for prog in missing(checks)]
    return found


HINTS = {
    "no_checks": "give the task at least one shell check that fails while the work is missing (for a document: "
                 "`test -s <file>` plus a `grep` for what it must contain)",
    "trivial_check": "this check passes whatever the worker did; replace it with one that can fail",
    "unknown_assignee": "the assignee is not in `workers`; use a listed worker or add this one",
    "missing_program": "this program is not installed here; write the check with the tools listed as available",
}


def describe(findings: list[dict]) -> str:
    """The findings as text for the planner, one line each."""
    return "\n".join(f"- task {f['task']}: {f['rule']} ({f['detail']}) — {HINTS[f['rule']]}" for f in findings)
