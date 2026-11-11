import errno
import os
from http.server import BaseHTTPRequestHandler
from types import SimpleNamespace

import pytest

from artel import brand
from artel.web import auth as auth_mod
from artel.web import server

BUSY = "Порт {p} уже занят другой программой, панель не запущена. Запустите на другом порту: arteliq web --port {q}"
ANY = "0.0.0.0"  # noqa: S104 (the value under test)


def test_listen_host_defaults_and_refusal():
    assert server._listen_host({}, None, True) == ANY
    assert server._listen_host({"host": "10.1.2.3"}, None, True) == "10.1.2.3"
    assert server._listen_host({"host": "10.1.2.3"}, "192.168.0.5", True) == "192.168.0.5"
    assert server._listen_host({"host": "10.1.2.3"}, None, False) == "127.0.0.1"
    assert server._listen_host({}, "localhost", False) == "localhost"
    with pytest.raises(SystemExit) as e:
        server._listen_host({}, ANY, False)
    assert str(e.value) == ("arteliq web: 0.0.0.0 is beyond localhost; that needs login - use `arteliq web --remote`"
                            " (see docs/REMOTE.md)")


def test_bind_listens_on_the_address_without_a_handler_yet():
    httpd = server._bind("127.0.0.1", 0)
    try:
        assert httpd.server_address[0] == "127.0.0.1"
        assert httpd.RequestHandlerClass is BaseHTTPRequestHandler
    finally:
        httpd.server_close()


def _failing_server(monkeypatch, code):
    def boom(*a, **k):
        raise OSError(code, "x")
    monkeypatch.setattr(server, "_DashboardServer", boom)


@pytest.mark.parametrize("code", [errno.EADDRINUSE, 10048])
def test_bind_busy_message_is_exact(monkeypatch, code):
    _failing_server(monkeypatch, code)
    with pytest.raises(SystemExit) as e:
        server._bind("127.0.0.1", 8765)
    assert str(e.value) == BUSY.format(p=8765, q=8766)
    assert e.value.__cause__ is None and e.value.__suppress_context__


@pytest.mark.parametrize("name,code,busy", [("nt", errno.EACCES, True), ("posix", errno.EACCES, False),
                                            ("nt", errno.ENOENT, False), ("posix", errno.ENOENT, False)])
def test_bind_other_errors_pass_through(monkeypatch, name, code, busy):
    _failing_server(monkeypatch, code)
    monkeypatch.setattr(os, "name", name)
    if busy:
        with pytest.raises(SystemExit):
            server._bind("127.0.0.1", 1)
    else:
        with pytest.raises(OSError) as e:
            server._bind("127.0.0.1", 1)
        assert e.value.errno == code


def test_announce_local_and_remote(capsys):
    banner_local = brand.banner("дашборд http://127.0.0.1:9")
    server._announce("127.0.0.1", 9, False, None)
    assert capsys.readouterr().out == banner_local + "\n"
    banner_remote = brand.banner(f"дашборд http://{ANY}:9 (удалённый режим, вход по токену)")
    server._announce(ANY, 9, True, "SECRET")
    out = capsys.readouterr().out
    assert out == (banner_remote + "\nТокен доступа (показывается один раз, сохраните его; хранится только хэш):\n"
                   "  SECRET\nБез HTTPS токен и сессия идут по сети открытым текстом - см. docs/REMOTE.md\n")
    server._announce(ANY, 9, True, None)
    out = capsys.readouterr().out
    assert "SECRET" not in out and "arteliq web token --new" in out and "Вход по ранее выпущенному токену" in out
    assert out.endswith("см. docs/REMOTE.md\n")


class FakeHttpd:
    def __init__(self, interrupt=False, log=None):
        self.interrupt, self.log = interrupt, log if log is not None else []
        self.daemon_threads = False

    def serve_forever(self):
        self.log.append(("serve", self.daemon_threads, self.RequestHandlerClass, self.runner))
        if self.interrupt:
            raise KeyboardInterrupt

    def server_close(self):
        self.log.append("close")


def _setup(monkeypatch, *, interrupt=False, active=None, remote_auth=None):
    log = []
    httpd = FakeHttpd(interrupt, log)
    runner = SimpleNamespace(active=active or {}, results=SimpleNamespace(stop_all=lambda: log.append("stop_all")),
                             kernel=SimpleNamespace(shutdown=lambda reason: log.append(("shutdown", reason))))
    seen = {}
    monkeypatch.setattr(server, "_bind", lambda h, p: seen.update(bind=(h, p)) or httpd)
    monkeypatch.setattr(server, "Runner", lambda cfg: seen.update(runner_cfg=cfg) or runner)
    monkeypatch.setattr(server, "make_handler", lambda r, a: seen.update(handler=(r, a)) or "HANDLER")
    monkeypatch.setattr(server, "_start_background", lambda r, c: log.append(("bg", c)))
    monkeypatch.setattr(server, "_announce", lambda *a: log.append(("announce", *a)))

    class FakeAuth:
        def __init__(self, session_days):
            seen["session_days"] = session_days

        def ensure_token(self):
            return "TOK"
    monkeypatch.setattr(auth_mod, "Auth", FakeAuth)
    return log, runner, seen


def test_serve_local_wires_everything_in_order(monkeypatch):
    log, runner, seen = _setup(monkeypatch)
    cfg = {"web": {"session_days": 3}}
    server.serve(port=1234, config=cfg)
    assert seen["bind"] == ("127.0.0.1", 1234) and seen["runner_cfg"] is cfg
    assert seen["handler"] == (runner, None) and "session_days" not in seen
    assert log == [("bg", cfg), ("announce", "127.0.0.1", 1234, False, None), ("serve", True, "HANDLER", runner),
                   "close", "stop_all", ("shutdown", "server_stop")]


def test_serve_remote_issues_a_token_after_the_bind(monkeypatch):
    log, _, seen = _setup(monkeypatch)
    server.serve(port=5, config={"web": {"remote": True, "session_days": 7, "host": "1.2.3.4"}})
    assert seen["bind"] == ("1.2.3.4", 5) and seen["session_days"] == 7
    assert seen["handler"][1].__class__.__name__ == "FakeAuth"
    assert ("announce", "1.2.3.4", 5, True, "TOK") in log
    seen.clear()
    server.serve(port=5, config={"web": {}}, remote=True)
    assert seen["session_days"] == 30


def test_serve_remote_flag_overrides_config_and_none_reads_it(monkeypatch):
    log, _, seen = _setup(monkeypatch)
    server.serve(config={"web": {"remote": True}}, remote=False)
    assert seen["bind"] == ("127.0.0.1", 8765) and ("announce", "127.0.0.1", 8765, False, None) in log


def test_serve_without_config_loads_it(monkeypatch):
    from artel import project

    _, _, seen = _setup(monkeypatch)
    loaded = {"web": {}}
    monkeypatch.setattr(project, "load_config", lambda: loaded)
    server.serve()
    assert seen["runner_cfg"] is loaded


def test_serve_busy_port_stops_before_anything_starts(monkeypatch):
    log, _, seen = _setup(monkeypatch)

    def busy(h, p):
        raise SystemExit("busy")
    monkeypatch.setattr(server, "_bind", busy)
    with pytest.raises(SystemExit):
        server.serve(config={"web": {"remote": True}})
    assert log == [] and "runner_cfg" not in seen and "session_days" not in seen


def test_serve_ctrl_c_message_and_cleanup(monkeypatch, capsys):
    log, _, _ = _setup(monkeypatch, interrupt=True)
    server.serve(config={})
    assert capsys.readouterr().out == "\nArteliq остановлен.\n"
    assert log[-3:] == ["close", "stop_all", ("shutdown", "server_stop")]
    log, _, _ = _setup(monkeypatch, interrupt=True, active={"b": 1, "a": 2})
    server.serve(config={})
    assert capsys.readouterr().out == ("\nArteliq остановлен. Незавершённые проекты (2) продолжатся кнопкой "
                                       "«Продолжить» после следующего `arteliq web`.\n")


def test_announce_flushes_every_line_so_the_token_shows_at_once(monkeypatch):
    calls = []
    monkeypatch.setattr("builtins.print", lambda *a, **k: calls.append((a, k)))
    for token in ("T", None):
        calls.clear()
        server._announce("127.0.0.1", 9, True, token)
        assert len(calls) == 4 and all(k == {"flush": True} for _, k in calls)
    calls.clear()
    server._announce("127.0.0.1", 9, False, None)
    assert len(calls) == 1 and calls[0][1] == {"flush": True}
