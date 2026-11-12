"""Liveness for the dashboard's user mode: what a running agent is doing in plain Russian, step counts, and the
per-run activity endpoint (same auth as the other project APIs)."""
import json
import threading
import urllib.error
import urllib.request

import pytest

from artel.analytics import active_agents, run_activity
from artel.httpd import LocalHTTPServer
from artel.humanize import action_text, localize_view
from artel.project import DEFAULT_CONFIG, Project, deep_merge
from artel.web.auth import COOKIE, Auth
from artel.web.server import Runner, make_handler


def test_action_text_is_plain_russian_and_never_leaks_long_commands():
    assert action_text("Read", {"file_path": "/work/proj/README.md"}) == ("читает файл README.md", "README.md")
    assert action_text("Write", {"file_path": "/a/b/styles.css"})[0] == "пишет файл styles.css"
    assert action_text("Edit", {"file_path": "/a/b/app.js"})[0] == "правит файл app.js"
    assert action_text("Grep", {"pattern": "TODO"})[0] == "ищет в файлах"
    assert action_text("Glob", {"pattern": "*.py"})[0] == "ищет файлы"
    assert action_text("WebFetch", {"url": "https://x.y"})[0] == "открывает страницу"
    assert action_text("unknown_tool", {})[0] == "выполняет шаг"
    text, detail = action_text("Bash", {"command": "echo hi"})
    assert (text, detail) == ("выполняет команду", "echo hi")
    long = "make build && " + "x" * 300
    assert len(action_text("shell", {"command": long})[1]) <= 80
    cmd = "curl -H 'Authorization: Bearer abcdefghijklmnopqrstuvwxyz0123456789' u"
    secret = action_text("Bash", {"command": cmd})
    assert "abcdefghijklmnopqrstuvwxyz0123456789" not in secret[1]


EV = [{"seq": 1, "kind": "agent/start", "ts": 100, "actor": "planner", "role": "planner", "purpose": "plan",
       "model": "claude-code:sonnet"},
      {"seq": 2, "kind": "tool/call", "ts": 101, "actor": "planner", "tool": "Read", "call_id": "c1",
       "input": {"file_path": "/p/README.md"}},
      {"seq": 3, "kind": "tool/result", "ts": 102, "actor": "planner", "tool": "Read", "call_id": "c1",
       "is_error": False, "output": "# hello"},
      {"seq": 4, "kind": "tool/call", "ts": 110, "actor": "planner", "tool": "Bash", "call_id": "c2",
       "input": {"command": "ls"}},
      {"seq": 5, "kind": "tool/call", "ts": 111, "actor": "other", "tool": "Read", "call_id": "x",
       "input": {"file_path": "/p/zzz"}}]


def test_active_agents_count_steps_and_describe_the_last_action():
    a = active_agents(EV)
    p = next(x for x in a if x["actor"] == "planner")
    assert p["steps"] == 2 and p["last_action"] == "выполняет команду" and p["last"] == "Bash" and p["last_ts"] == 110


def test_run_activity_lists_this_runs_steps_with_results_and_pages_back():
    r = run_activity(EV, actor="planner", task_id=None, purpose="plan", user=True)
    assert r["open"] is True and r["more"] is False
    assert [i["text"] for i in r["items"]] == ["читает файл README.md", "выполняет команду"]
    assert r["items"][0]["state"] == "ok" and r["items"][1]["state"] == "running"
    assert all("tool" not in i for i in r["items"])  # user mode: no tool names
    d = run_activity(EV, actor="planner", task_id=None, purpose="plan", user=False)
    assert d["items"][0]["tool"] == "Read"
    many = [EV[0], *({"seq": 10 + i, "kind": "tool/call", "ts": 200 + i, "actor": "planner", "tool": "Bash",
                       "call_id": f"k{i}", "input": {"command": f"c{i}"}} for i in range(60))]
    page = run_activity(many, actor="planner", task_id=None, purpose="plan", user=True, limit=50)
    assert len(page["items"]) == 50 and page["more"] is True and page["items"][-1]["seq"] == 69
    older = run_activity(many, actor="planner", task_id=None, purpose="plan", user=True, limit=50,
                         before=page["items"][0]["seq"])
    assert len(older["items"]) == 10 and older["more"] is False


def test_run_activity_marks_errors_and_a_finished_run_and_takes_only_the_latest_run():
    ev = [*EV[:3], {"seq": 6, "kind": "agent/end", "ts": 120, "actor": "planner", "purpose": "plan"},
                   {"seq": 7, "kind": "agent/start", "ts": 130, "actor": "planner", "role": "planner",
                    "purpose": "plan", "model": "m"},
                   {"seq": 8, "kind": "tool/call", "ts": 131, "actor": "planner", "tool": "Bash", "call_id": "z",
                    "input": {"command": "false"}},
                   {"seq": 9, "kind": "tool/result", "ts": 132, "actor": "planner", "tool": "Bash", "call_id": "z",
                    "is_error": True, "output": "boom\nsecond line"}]
    r = run_activity(ev, actor="planner", task_id=None, purpose="plan", user=True)
    assert [i["seq"] for i in r["items"]] == [8] and r["items"][0]["state"] == "error"
    assert "boom" in r["items"][0]["result"] and "second line" not in r["items"][0]["result"]
    ev.append({"seq": 10, "kind": "agent/end", "ts": 140, "actor": "planner", "purpose": "plan"})
    assert run_activity(ev, actor="planner", task_id=None, purpose="plan", user=True)["open"] is False


def test_localize_view_gives_the_running_agent_a_russian_name():
    v = localize_view({"active": [{"actor": "planner", "role": "planner"}, {"actor": "Анна", "role": "worker"}]})
    assert [a["who"] for a in v["active"]] == ["планировщик", "Анна"] and v["active"][0]["actor"] == "planner"


@pytest.fixture
def served(tmp_path, monkeypatch):
    monkeypatch.setenv("ARTEL_HOME", str(tmp_path))
    cfg = deep_merge(DEFAULT_CONFIG, {"provider": "scripted"})
    project = Project.create("goal", cfg, home=tmp_path)
    for e in EV[:4]:
        kw = {k: v for k, v in e.items() if k not in ("seq", "ts", "kind")}
        project.log.append(e["kind"], **kw)
    auth = Auth(home=tmp_path, session_days=30)
    token = auth.rotate()
    httpd = LocalHTTPServer(("127.0.0.1", 0), make_handler(Runner(cfg), auth))
    httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}", project, auth, token
    httpd.shutdown()
    httpd.server_close()


def _get(url, cookie=None):
    r = urllib.request.Request(url, headers={"Cookie": f"{COOKIE}={cookie}"} if cookie else {})  # noqa: S310
    try:
        with urllib.request.urlopen(r, timeout=5) as resp:  # noqa: S310
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def test_activity_endpoint_needs_login_and_returns_the_humanised_run(served):
    base, project, auth, token = served
    url = f"{base}/api/projects/{project.slug}/activity?actor=planner&purpose=plan&mode=user"
    assert _get(url)[0] == 401
    sid = auth.login(token, "127.0.0.1")
    code, body = _get(url, sid)
    assert code == 200 and [i["text"] for i in body["items"]] == ["читает файл README.md", "выполняет команду"]
    code, body = _get(url + "&limit=1", sid)
    assert len(body["items"]) == 1 and body["more"] is True
    assert _get(f"{base}/api/projects/nope/activity?actor=planner", sid)[0] == 404
    code, body = _get(f"{base}/api/projects/{project.slug}/activity?actor=planner&purpose=plan&limit=99999", sid)
    assert code == 200  # capped, not refused
