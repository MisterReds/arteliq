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


# ---- exact behaviour of the pieces (each assertion pins one decision) ----

def _ev(seq, kind, ts=1.0, **kw):
    return {"seq": seq, "kind": kind, "ts": ts, **kw}


def test_action_text_exact_sentences_details_and_edges():
    assert action_text("READ", {"file_path": "/a/b.md"}) == ("читает файл b.md", "b.md")
    assert action_text("read", {"path": "/a/c.md"}) == ("читает файл c.md", "c.md")
    assert action_text("NotebookEdit", {"notebook_path": "/a/n.ipynb"}) == ("правит файл n.ipynb", "n.ipynb")
    assert action_text("MultiEdit", {"file_path": "x.py"}) == ("правит файл x.py", "x.py")
    assert action_text("Write", {}) == ("пишет файл", "")  # no name: no trailing space
    assert action_text("Read", "not a dict") == ("читает файл", "")
    assert action_text("Read", {"file_path": "/a/long/" + "n" * 100}) == (
        "читает файл " + "n" * 100, "n" * 79 + "…")
    assert action_text(None, None) == ("выполняет шаг", "")
    assert action_text("Bash", {"command": "  a   b\n c "}) == ("выполняет команду", "a b c")
    assert action_text("Bash", {}) == ("выполняет команду", "")
    assert action_text("Bash", {"command": "x" * 80})[1] == "x" * 80
    assert action_text("Bash", {"command": "x" * 81})[1] == "x" * 79 + "…"
    assert action_text("shell", {"command": "ab " * 40})[1] == ("ab " * 26 + "a")[:79].rstrip() + "…"
    for tool, text in [("Glob", "ищет файлы"), ("Grep", "ищет в файлах"), ("LS", "смотрит папку"),
                       ("WebFetch", "открывает страницу"), ("WebSearch", "ищет в интернете"),
                       ("web_search", "ищет в интернете"), ("TodoWrite", "обновляет список дел"),
                       ("apply_patch", "правит файлы"), ("Task", "поручает подзадачу")]:
        assert action_text(tool, {"command": "ignored"}) == (text, "")


def test_localize_view_translates_roles_and_names_the_agent():
    v = localize_view({"workers": [{"role": "engineer"}],
                       "active": [{"actor": "Ann", "role": "engineer"}, {"actor": "auditor", "role": "auditor"}]})
    assert v["workers"][0]["role"] == "инженер"
    assert v["active"] == [{"actor": "Ann", "role": "инженер", "who": "Ann"},
                           {"actor": "auditor", "role": "аудитор", "who": "аудитор"}]
    assert localize_view({}) == {}


def test_active_agent_record_runtime_steps_and_last_action_exactly():
    ev = [_ev(1, "agent/start", 10, actor="a", role="worker", purpose="work", task_id="t1", model="codex:x"),
          _ev(2, "agent/start", 11, actor="b", role="planner", purpose="plan", model="claude-code:s"),
          _ev(3, "agent/start", 12, actor="c", role="worker", purpose="work", model="mine"),
          _ev(4, "agent/start", 9, actor="d", role="worker", purpose="work", model="x", runtime="custom"),
          _ev(5, "tool/call", 20, actor="a", task_id="t1", tool="Read", input={"file_path": "/q/z.md"}),
          _ev(6, "tool/call", 21, actor="a", task_id="t2", tool="Bash", input={"command": "ls"}),  # other task: not a's
          _ev(7, "tool/call", 22, actor="b", name="submit", input={}),
          _ev(8, "llm/error", 23, actor="c", error="e" * 300),
          _ev(9, "provider/limited", 24, actor="d"),
          _ev(10, "agent/end", 25, actor="a", task_id="t1", purpose="review")]  # other purpose: a stays
    a = {x["actor"]: x for x in active_agents(ev)}
    assert [x["actor"] for x in active_agents(ev)] == ["d", "a", "b", "c"]  # by start time
    assert a["a"] == {"actor": "a", "role": "worker", "task_id": "t1", "purpose": "work", "runtime": "codex",
                      "model": "codex:x", "since": 10, "last": "Read", "last_ts": 20, "steps": 1,
                      "last_action": "читает файл z.md"}
    assert (a["b"]["runtime"], a["b"]["last"], a["b"]["last_action"], a["b"]["steps"]) == (
        "claude_code", "submit", "выполняет шаг", 1)
    assert (a["c"]["runtime"], a["c"]["last"], a["c"]["last_action"], a["c"]["steps"], a["c"]["last_ts"]) == (
        "native", "ошибка: " + "e" * 160, "ошибка", 0, 23)
    assert (a["d"]["runtime"], a["d"]["last"], a["d"]["last_ts"], a["d"]["task_id"]) == ("custom", "ошибка: ", 24, None)
    ended = [*ev, _ev(11, "agent/end", 26, actor="a", task_id="t1", purpose="work")]
    assert [x["actor"] for x in active_agents(ended)] == ["d", "b", "c"]
    assert active_agents(ev[:1], live=False) == []


def _run(extra=(), **kw):
    base = [_ev(1, "agent/start", 1, actor="p", purpose="plan", task_id=None)]
    return run_activity(base + list(extra), actor="p", task_id=None, purpose="plan", **kw)


def test_run_activity_exact_items_in_both_modes():
    ev = [_ev(2, "tool/call", 2, actor="p", tool="Bash", call_id="c", input={"command": "ls"}),
          _ev(3, "tool/result", 3, actor="p", tool="Bash", call_id="c", is_error=False, output="\n\nfile1\nfile2"),
          _ev(4, "tool/result", 4, actor="p", tool="Bash", call_id="nope", is_error=True, output="stray"),
          _ev(5, "tool/call", 5, actor="p", tool="Read", input={"file_path": "/q/r.md"}),  # no call_id: seq is the key
          _ev(6, "llm/error", 6, actor="p", error="  rate   limit " + "x" * 100),
          _ev(7, "tool/call", 7, actor="other", tool="Read", call_id="o", input={}),
          _ev(8, "tool/call", 8, actor="p", task_id="t9", tool="Read", call_id="t", input={}),
          _ev(9, "agent/start", 9, actor="p", purpose="work", task_id=None, model="m"),  # another purpose: not ours
          _ev(10, "agent/end", 10, actor="p", purpose="work")]
    user = _run(ev, user=True)
    assert user["open"] is True and user["more"] is False
    assert user["items"][:2] == [
        {"seq": 2, "ts": 2, "text": "выполняет команду", "detail": "ls", "state": "ok", "result": ""},
        {"seq": 5, "ts": 5, "text": "читает файл r.md", "detail": "r.md", "state": "running", "result": ""}]
    assert user["items"][2]["text"] == "модель ответила ошибкой" and user["items"][2]["state"] == "error"
    assert [i["seq"] for i in user["items"]] == [2, 5, 6, 8]
    dev = _run(ev, user=False)
    assert dev["items"][0] == {"seq": 2, "ts": 2, "text": "выполняет команду", "detail": "ls", "state": "ok",
                               "result": "file1", "tool": "Bash"}
    assert "tool" not in dev["items"][2]
    assert user["items"][2]["result"] == "rate limit " + "x" * 68 + "…" and len(user["items"][2]["result"]) == 80
    assert user["items"][3]["state"] == "running"  # t9 event has a task_id but the run has none: it still belongs


def test_run_activity_limit_cap_before_and_run_selection():
    many = [_ev(10 + i, "tool/call", 10 + i, actor="p", tool="Bash", call_id=f"k{i}", input={"command": "c"})
            for i in range(250)]
    assert len(_run(many)["items"]) == 50
    big = _run(many, limit=9999)
    assert len(big["items"]) == 200 and big["more"] is True and big["items"][-1]["seq"] == 259
    assert len(_run(many, limit=0)["items"]) == 1
    exact = _run(many[:50], limit=50)
    assert len(exact["items"]) == 50 and exact["more"] is False
    assert [i["seq"] for i in _run(many, limit=3, before=15)["items"]] == [12, 13, 14]
    assert _run(many, limit=3, before=13)["more"] is False
    assert _run(many, limit=2, before=15)["more"] is True
    # unknown run: nothing, closed
    assert run_activity([], "p", None, "plan") == {"items": [], "more": False, "open": False}
    assert run_activity([_ev(1, "agent/start", actor="p", purpose="work", task_id="t")], "p", None, "work") == \
        {"items": [], "more": False, "open": False}
    # latest start of THIS key wins; an end of another purpose or actor does not close it
    ev = [_ev(1, "agent/start", actor="p", purpose="plan", task_id=None),
          _ev(2, "tool/call", actor="p", tool="Read", call_id="a", input={}),
          _ev(3, "agent/start", actor="p", purpose="plan", task_id=None),
          _ev(4, "agent/end", actor="q", purpose="plan"),
          _ev(5, "agent/end", actor="p", purpose="work"),
          _ev(6, "tool/call", actor="p", tool="Read", call_id="b", input={}),
          _ev(7, "agent/start", actor="q", purpose="plan", task_id=None)]
    r = run_activity(ev, "p", None, "plan")
    assert r["open"] is True and [i["seq"] for i in r["items"]] == [6]
    task_run = run_activity([_ev(1, "agent/start", actor="p", purpose="work", task_id="t1"),
                             _ev(2, "tool/call", actor="p", task_id="t1", tool="Read", call_id="x", input={}),
                             _ev(3, "tool/call", actor="p", task_id="t2", tool="Read", call_id="y", input={}),
                             _ev(4, "tool/call", actor="p", tool="Read", call_id="z", input={})],
                            "p", "t1", "work")
    assert [i["seq"] for i in task_run["items"]] == [2, 4]


def test_a_fresh_agent_record_and_odd_events():
    fresh = active_agents([_ev(1, "agent/start", 5, actor="a", role="r", purpose="plan")])
    assert fresh == [{"actor": "a", "role": "r", "task_id": None, "purpose": "plan", "runtime": "native", "model": "",
                      "since": 5, "last": "", "last_ts": 5, "steps": 0, "last_action": ""}]
    both = active_agents([_ev(1, "agent/start", 5, actor="a", purpose="plan"),
                          _ev(2, "tool/call", 6, actor="a"), _ev(3, "llm/error", 7, actor="a")])
    assert (both[0]["last"], both[0]["steps"], both[0]["last_action"]) == ("ошибка: ", 1, "ошибка")
    nameless = active_agents([_ev(1, "agent/start", 5, actor="a", purpose="plan"), _ev(2, "tool/call", 6, actor="a")])
    assert (nameless[0]["last"], nameless[0]["last_action"]) == ("", "выполняет шаг")


def test_run_results_and_error_items_are_exact():
    ev = [_ev(2, "tool/call", 2, actor="p", tool="Bash", call_id="a", input={}),
          _ev(3, "tool/result", 3, actor="p", call_id="a", is_error=True, output="\n \n  first   line \nsecond"),
          _ev(4, "tool/call", 4, actor="p", tool="Bash", call_id="b", input={}),
          _ev(5, "tool/result", 5, actor="p", call_id="b", is_error=False, output=None),
          _ev(6, "tool/call", 6, actor="p", tool="Bash", call_id="c", input={}),
          _ev(7, "tool/result", 7, actor="p", call_id="c", is_error=False, output=" \n "),
          _ev(8, "llm/error", 8, actor="p", error="a" * 78 + " " + "b" * 20),
          _ev(9, "llm/error", 9, actor="p")]
    u = _run(ev, user=True)["items"]
    assert (u[0]["state"], u[0]["result"]) == ("error", "first line")
    assert (u[1]["state"], u[1]["result"], u[2]["state"], u[2]["result"]) == ("ok", "", "ok", "")
    d = _run(ev, user=False)["items"]
    assert (d[1]["result"], d[2]["result"]) == ("", "")
    assert u[3] == {"seq": 8, "ts": 8, "text": "модель ответила ошибкой", "detail": "", "state": "error",
                    "result": "a" * 78 + "…"}
    assert u[4] == {"seq": 9, "ts": 9, "text": "модель ответила ошибкой", "detail": "", "state": "error", "result": ""}
    assert "tool" not in _run(ev)["items"][0]  # user mode is the default
    assert d[0]["tool"] == "Bash"
    ok_dev = _run([_ev(2, "tool/call", 2, actor="p", tool="Bash", call_id="a", input={}),
                   _ev(3, "tool/result", 3, actor="p", call_id="a", is_error=False, output="one\ntwo")], user=False)
    assert ok_dev["items"][0]["result"] == "one"
    exact = _run([_ev(2, "llm/error", 2, actor="p", error="y" * 80)])["items"][0]["result"]
    assert exact == "y" * 80
    assert _run([_ev(2, "llm/error", 2, actor="p", error="y" * 81)])["items"][0]["result"] == "y" * 79 + "…"
    assert action_text("Bash", {"command": "q" * 78 + " " + "z" * 9})[1] == "q" * 78 + "…"
