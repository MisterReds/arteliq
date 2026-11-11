"""Plan lint: what code can tell about a plan before work starts, enforced inside the planner's own run."""
import pytest

from artel import routing
from artel.manager import run_goal
from artel.planlint import lint_plan
from artel.project import DEFAULT_CONFIG, Project, deep_merge

WORKERS = [{"name": "Ada"}, {"name": "Linus"}]


def _lint(tasks, missing=lambda checks: []):
    return [(f["rule"], f["task"]) for f in lint_plan(WORKERS, tasks, missing)]


def test_a_task_without_a_check_is_reported():
    assert _lint([{"key": "a", "criteria": ["x"], "checks": []}, {"key": "b", "criteria": ["y"]}]) == [
        ("no_checks", "a"), ("no_checks", "b")]


def test_a_check_that_cannot_fail_is_reported():
    tasks = [{"key": "a", "criteria": ["x"], "checks": ["true", "echo done", ": ok", "  "]},
             {"key": "b", "criteria": ["y"],
              "checks": ["test -s out.md", "echo hi | grep -q hi", "echo x > f && test -s f"]}]
    assert _lint(tasks) == [("trivial_check", "a")] * 4


def test_an_unknown_assignee_and_a_missing_program_are_reported():
    tasks = [{"key": "a", "criteria": ["x"], "checks": ["nope-tool x"], "assignee": "Grace"},
             {"key": "b", "criteria": ["y"], "checks": ["test -s f"], "assignee": "Ada"}]
    found = lint_plan(WORKERS, tasks, lambda checks: ["nope-tool"] if "nope-tool x" in checks else [])
    assert [(f["rule"], f["task"], f["detail"]) for f in found] == [
        ("unknown_assignee", "a", "Grace"), ("missing_program", "a", "nope-tool")]


def test_a_clean_plan_has_no_findings():
    assert _lint([{"key": "a", "criteria": ["x"], "checks": ["python3 -m pytest -q"], "assignee": "Linus"}]) == []


@pytest.fixture
def cfg(tmp_path, monkeypatch):
    monkeypatch.setenv("ARTEL_HOME", str(tmp_path / "home"))
    return deep_merge(DEFAULT_CONFIG, {"provider": "scripted", "sandbox": {"mode": "off"}})


def _planner_runs(project):
    return [e for e in project.log.read() if e["kind"] == "agent/start" and e.get("role") == "planner"]


def test_a_plan_with_a_missing_program_is_fixed_inside_the_same_planner_run(cfg):
    cfg = deep_merge(cfg, {"scripted": {"bad_check_tool": "nonexistent_tool_xyz"}})
    project, status = run_goal("Write a guide", cfg)
    assert status == "done"
    events = project.log.read()
    lint = [e for e in events if e["kind"] == "manager/plan_lint"]
    assert len(lint) == 1 and lint[0]["rejected"] is True
    assert ("missing_program", "nonexistent_tool_xyz") in [(f["rule"], f["detail"]) for f in lint[0]["findings"]]
    assert len(_planner_runs(project)) == 1                      # no second planner run: the fix costs one turn
    assert all("nonexistent_tool_xyz" not in c for t in project.board.list() for c in t["checks"])
    assert "manager/plan_lint_unresolved" not in [e["kind"] for e in events]


def test_a_plan_the_planner_will_not_fix_is_accepted_after_two_rejections_and_marked(cfg):
    cfg = deep_merge(cfg, {"scripted": {"bad_check_tool": "nonexistent_tool_xyz", "bad_check_persists": True}})
    project = Project.create("Write a guide", cfg)
    from artel.manager import Manager, new_kernel

    kernel = new_kernel(cfg)
    try:
        Manager(kernel, project).plan()
    finally:
        kernel.shutdown(reason="run_end")
    events = project.log.read()
    lint = [e for e in events if e["kind"] == "manager/plan_lint"]
    assert [e["rejected"] for e in lint] == [True, True, False]
    assert len(_planner_runs(project)) == 1
    unresolved = [e for e in events if e["kind"] == "manager/plan_lint_unresolved"]
    assert len(unresolved) == 1 and unresolved[0]["findings"][0]["rule"] == "missing_program"
    assert project.board.list()                                  # the plan was applied; gates deal with the rest


def test_an_ordinary_goal_is_planned_and_audited_on_the_medium_profile(cfg):
    project = Project.create("Сделай CLI-утилиту для учёта расходов", cfg)
    project.set_meta(contract={"complexity": "medium", "deliverables": ["a", "b", "c", "d"], "success_criteria": ["x"]})
    assert routing.tier_for(cfg, "planner", project) == "medium"
    assert routing.tier_for(cfg, "auditor", project) == "medium"
    assert routing.tier_for(cfg, "manager", project) == "expensive"   # decisions on stuck tasks stay strong
    project.set_meta(contract={"complexity": "high", "deliverables": ["a"], "success_criteria": ["x"]})
    assert routing.tier_for(cfg, "planner", project) == "expensive"   # a complex goal keeps the architect
    project.set_meta(contract=None)
    assert routing.tier_for(cfg, "planner", project) == "expensive"   # no contract: nothing says it is ordinary
