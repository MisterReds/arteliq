import os
import socket
import subprocess
import sys


def test_web_on_a_busy_port_says_so_in_russian_and_exits_nonzero(tmp_path):
    env = {**os.environ, "ARTEL_HOME": str(tmp_path / "home"), "HOME": str(tmp_path), "PYTHONIOENCODING": "utf-8"}
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        s.listen()
        port = s.getsockname()[1]
        r = subprocess.run([sys.executable, "-c",
                            "import sys; from artel.cli import main; sys.exit(main(sys.argv[1:]))",
                            "web", "--port", str(port)], env=env, text=True,
                           capture_output=True, timeout=60, encoding="utf-8")
    assert r.returncode != 0
    assert f"Порт {port} уже занят" in r.stderr and f"arteliq web --port {port + 1}" in r.stderr
    assert "Traceback" not in r.stderr and "http://" not in r.stdout


def test_bind_returns_a_server_on_a_free_port_and_reraises_other_errors():
    import pytest

    from artel.web import server

    httpd = server._bind("127.0.0.1", 0)
    try:
        assert httpd.server_port > 0
    finally:
        httpd.server_close()
    with pytest.raises(OSError):
        server._bind("203.0.113.1", 0)  # not an address of this machine: not a "port busy" case


def test_bind_in_process_reports_busy_port():
    import pytest

    from artel.web import server

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        s.listen()
        port = s.getsockname()[1]
        with pytest.raises(SystemExit) as e:
            server._bind("127.0.0.1", port)
    assert str(port) in str(e.value) and f"--port {port + 1}" in str(e.value)


def test_start_background_starts_loop_supervisor_and_telegram(monkeypatch, tmp_path, capsys):
    from types import SimpleNamespace

    from artel import telegram
    from artel.evolve import supervisor
    from artel.web import server

    monkeypatch.setenv("ARTEL_HOME", str(tmp_path))
    calls = []
    runner = SimpleNamespace(start_update_loop=lambda: calls.append("loop"))
    monkeypatch.setattr(supervisor.Supervisor, "__init__", lambda self, root: calls.append("sup"))
    monkeypatch.setattr(supervisor.Supervisor, "start", lambda self: self)
    monkeypatch.setattr(telegram, "token", lambda: "t")
    pair = {"pair": {"code": "1234"}}
    monkeypatch.setattr(telegram, "TelegramBot", lambda r: SimpleNamespace(
        start=lambda: SimpleNamespace(store=SimpleNamespace(data=pair))))
    server._start_background(runner, {})
    assert calls == ["loop", "sup"] and runner.telegram.store.data == pair
    assert "/pair 1234" in capsys.readouterr().out
    monkeypatch.setattr(telegram, "token", lambda: "")
    runner2 = SimpleNamespace(start_update_loop=lambda: None)
    server._start_background(runner2, {"evolve": {"auto_resume": False}})
    assert not hasattr(runner2, "telegram") and not hasattr(runner2, "supervisor")
