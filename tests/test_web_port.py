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
