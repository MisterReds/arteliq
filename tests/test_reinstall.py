import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BASH = shutil.which("bash")
posix_only = pytest.mark.skipif(os.name == "nt" or not BASH, reason="install.sh needs bash")


def g(cwd, *args):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=cwd, check=True,
                          capture_output=True, text=True).stdout.strip()


@pytest.fixture
def box(tmp_path):
    src = tmp_path / "src"  # a local repo with the tracked files of this worktree
    src.mkdir()
    files = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout.split(b"\0")
    for f in filter(None, files):
        rel = Path(f.decode())
        if (ROOT / rel).is_file():
            (src / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / rel, src / rel)
    g(src, "init", "-q", "-b", "master")
    g(src, "add", "-A")
    g(src, "commit", "-q", "-m", "snapshot")
    home = tmp_path / "home"
    ah = home / ".artel"
    (ah / "projects" / "x").mkdir(parents=True)
    (ah / "artel.yaml").write_bytes(b"provider: scripted\n# \xd0\xb4\xd0\xb0\xd0\xbd\xd0\xbd\xd1\x8b\xd0\xb5\n")
    (ah / "projects" / "x" / "project.json").write_bytes(b'{"goal": "keep me"}\n')
    env = {**os.environ, "HOME": str(home), "ARTEL_HOME": str(ah), "ARTEL_REPO": str(src),
           "ARTEL_DIR": str(ah / "app"), "ARTEL_VENV": str(ah / "venv"), "ARTEL_BIN": str(home / "bin"),
           "ARTEL_INSTALL_NODEPS": "1", "NO_COLOR": "1",
           "ARTEL_PYTHON": sys.executable}  # the interpreter that has the dependencies (httpx, yaml)
    env.pop("ARTEL_REINSTALL", None)
    return tmp_path, ah, env


def run_sh(env, *args):
    return subprocess.run([BASH, str(ROOT / "install.sh"), *args, "--yes", "--no-start"], env=env, text=True,
                          capture_output=True, stdin=subprocess.DEVNULL, timeout=300)


def snapshot(ah):
    return {str(p.relative_to(ah)): p.read_bytes() for p in [ah / "artel.yaml", ah / "projects" / "x" / "project.json"]}


@posix_only
def test_reinstall_keeps_user_data_and_recreates_app(box):
    _, ah, env = box
    first = run_sh(env)
    assert first.returncode == 0, first.stdout + first.stderr
    before = snapshot(ah)
    marker_venv = ah / "venv" / "STALE"
    marker_venv.write_text("x")
    out = run_sh(env, "--reinstall")
    assert out.returncode == 0, out.stdout + out.stderr
    assert snapshot(ah) == before
    assert not marker_venv.exists() and (ah / "venv" / "bin" / "python").exists()
    assert (ah / "app" / ".git").is_dir() and (ah / "app" / "install.sh").exists()
    # the caches an editable install leaves (egg-info, __pycache__) do not count: the clean clone is replaced, not kept
    assert not list(ah.glob("app.bak-*"))
    r = subprocess.run([str(Path(env["ARTEL_BIN"]) / "artel"), "--help"], env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


@posix_only
def test_reinstall_moves_dirty_clone_aside(box):
    _, ah, env = box
    assert run_sh(env).returncode == 0
    (ah / "app" / "README.md").write_text("my local edit\n", encoding="utf-8")
    out = run_sh(env, "--reinstall")
    assert out.returncode == 0, out.stdout + out.stderr
    baks = list(ah.glob("app.bak-*"))
    assert len(baks) == 1 and "my local edit" in (baks[0] / "README.md").read_text(encoding="utf-8")
    assert str(baks[0]) in out.stdout
    assert "my local edit" not in (ah / "app" / "README.md").read_text(encoding="utf-8")
    assert (ah / "artel.yaml").exists() and (ah / "projects" / "x" / "project.json").exists()


@posix_only
def test_help_and_syntax_work_when_piped():
    assert subprocess.run([BASH, "-n", str(ROOT / "install.sh")]).returncode == 0
    r = subprocess.run([BASH, "-s", "--", "--help"], input=(ROOT / "install.sh").read_text(encoding="utf-8"),
                       capture_output=True, text=True)
    assert r.returncode == 0 and "--reinstall" in r.stdout


def test_reinstall_refuses_on_source_checkout(monkeypatch, capsys, tmp_path):
    from artel import cli

    monkeypatch.setenv("ARTEL_DIR", str(tmp_path / "not-this-checkout"))
    monkeypatch.setattr(os, "execve", lambda *a, **k: pytest.fail("must not exec"))
    assert cli.main(["reinstall", "--yes"]) == 2
    assert "reinstall refused" in capsys.readouterr().err


def test_install_ps1_parse_check():
    pwsh = shutil.which("pwsh")
    if not pwsh:
        pytest.skip("pwsh not available")
    code = ("$e=$null; [System.Management.Automation.Language.Parser]::ParseFile('%s',[ref]$null,[ref]$e)|Out-Null; "
            "if($e){$e|Out-String;exit 1}" % (ROOT / "install.ps1"))
    assert subprocess.run([pwsh, "-NoProfile", "-Command", code], capture_output=True).returncode == 0


def clone_to(env, dest):
    subprocess.run(["git", "clone", "-q", env["ARTEL_REPO"], str(dest)], check=True, capture_output=True)
    return dest


def baks(path):
    return sorted(path.parent.glob(path.name + ".bak-*"))


@posix_only
def test_reinstall_deletes_only_a_clean_default_clone(box):
    _, ah, env = box
    clone_to(env, ah / "app")
    out = run_sh(env, "--reinstall")
    assert out.returncode == 0, out.stdout + out.stderr
    assert not baks(ah / "app") and (ah / "app" / ".git").is_dir()


@posix_only
def test_reinstall_moves_clean_non_default_checkout_aside(box):
    tmp, ah, env = box
    mine = clone_to(env, tmp / "dev" / "checkout")
    (mine / "README.md").write_text("x", encoding="utf-8")  # then restore: clean tree
    g(mine, "checkout", "--", "README.md")
    out = run_sh({**env, "ARTEL_DIR": str(mine)}, "--reinstall")
    assert out.returncode == 0, out.stdout + out.stderr
    kept = baks(mine)
    assert len(kept) == 1 and (kept[0] / ".git").is_dir() and str(kept[0]) in out.stdout


@posix_only
def test_reinstall_moves_default_clone_with_ignored_env_aside(box):
    _, ah, env = box
    app = clone_to(env, ah / "app")
    (app / ".gitignore").write_text(".env\n", encoding="utf-8")
    g(app, "add", ".gitignore")
    g(app, "commit", "-q", "-m", "ignore env")
    g(app, "update-ref", "refs/remotes/origin/master", "HEAD")  # pretend the commit is pushed
    (app / ".env").write_text("SECRET=1\n", encoding="utf-8")
    out = run_sh(env, "--reinstall")
    assert out.returncode == 0, out.stdout + out.stderr
    kept = baks(ah / "app")
    assert len(kept) == 1 and (kept[0] / ".env").read_text(encoding="utf-8") == "SECRET=1\n"


@posix_only
def test_reinstall_fails_closed_on_git_error(box):
    _, ah, env = box
    app = clone_to(env, ah / "app")
    (app / ".git" / "HEAD").write_text("garbage\n", encoding="utf-8")
    out = run_sh(env, "--reinstall")
    assert out.returncode == 0, out.stdout + out.stderr
    assert len(baks(ah / "app")) == 1


@posix_only
def test_reinstall_moves_default_clone_with_stash_or_unpushed_commits_aside(box):
    _, ah, env = box
    app = clone_to(env, ah / "app")
    (app / "new.txt").write_text("local\n", encoding="utf-8")
    g(app, "add", "new.txt")
    g(app, "commit", "-q", "-m", "local only")
    out = run_sh(env, "--reinstall")
    assert out.returncode == 0, out.stdout + out.stderr
    kept = baks(ah / "app")
    assert len(kept) == 1 and (kept[0] / "new.txt").exists()


@posix_only
def test_reinstall_refuses_dangerous_directories(box):
    tmp, ah, env = box
    home = Path(env["HOME"])
    for key, value in (("ARTEL_DIR", str(home)), ("ARTEL_DIR", ""), ("ARTEL_DIR", "/"), ("ARTEL_DIR", str(ah)),
                       ("ARTEL_VENV", str(home)), ("ARTEL_VENV", str(ah))):
        out = run_sh({**env, key: value}, "--reinstall")
        assert out.returncode != 0 and "refusing" in out.stderr, (key, value, out.stdout, out.stderr)
    assert (ah / "artel.yaml").exists() and (ah / "projects" / "x").is_dir()
    # a directory that holds ARTEL_HOME data directly is refused too
    data_dir = tmp / "data"
    (data_dir / "projects").mkdir(parents=True)
    out = run_sh({**env, "ARTEL_DIR": str(data_dir)}, "--reinstall")
    assert out.returncode != 0 and "refusing" in out.stderr


@posix_only
def test_reinstall_moves_foreign_venv_aside(box):
    tmp, ah, env = box
    venv = tmp / "other-venv"
    venv.mkdir()
    (venv / "pyvenv.cfg").write_text("home = /usr\n", encoding="utf-8")
    (venv / "mine.txt").write_text("keep", encoding="utf-8")
    out = run_sh({**env, "ARTEL_VENV": str(venv)}, "--reinstall")
    assert out.returncode == 0, out.stdout + out.stderr
    kept = baks(venv)
    assert len(kept) == 1 and (kept[0] / "mine.txt").exists()


def test_windows_reinstall_uses_only_create_new_console(monkeypatch):
    import subprocess

    from artel import cli

    seen = {}
    monkeypatch.setattr(subprocess, "CREATE_NEW_CONSOLE", 0x10, raising=False)
    monkeypatch.setattr(subprocess, "DETACHED_PROCESS", 0x8, raising=False)
    monkeypatch.setattr(subprocess, "Popen", lambda cmd, **kw: seen.update(kw) or object())
    cli._spawn_windows_reinstall(["powershell"], {})
    assert seen["creationflags"] == 0x10


def _fake_root(tmp_path, env, **extra):
    wrapper, sudoers = tmp_path / "artel-root", tmp_path / "sudoers-artel"
    wrapper.write_text("#!/bin/sh\n")
    sudoers.write_text("rule\n")
    return wrapper, sudoers, {**env, "ARTEL_ROOT_WRAPPER": str(wrapper), "ARTEL_ROOT_SUDOERS": str(sudoers),
                              "ARTEL_SUDO": "",
                              "ARTEL_ROOT_CONF": str(tmp_path / "artel-root.conf"), **extra}


@posix_only
@pytest.mark.skipif(sys.platform != "linux", reason="the root wrapper is Linux only")
def test_reinstall_keeps_the_root_wrapper_the_owner_consented_to(box):
    tmp_path, ah, env = box
    assert run_sh(env).returncode == 0
    wrapper, sudoers, renv = _fake_root(tmp_path, env)          # no ARTEL_ALLOW_ROOT, no terminal: no new question
    out = run_sh(renv, "--reinstall")
    assert out.returncode == 0, out.stdout + out.stderr
    assert wrapper.exists() and sudoers.exists()
    conf = (tmp_path / "artel-root.conf").read_text().splitlines()     # the allowlist: apt names of tools.yaml, no more
    assert "allow=ripgrep" in conf and "allow=jq" in conf and "allow=openssh-server" not in conf
    assert all(l.startswith(("#", "allow=", "deny=")) for l in conf)
    (tmp_path / "artel-root.conf").write_text("deny=ffmpeg\nallow=evil\n")
    assert run_sh(renv, "--reinstall").returncode == 0
    again = (tmp_path / "artel-root.conf").read_text().splitlines()
    assert "deny=ffmpeg" in again and "allow=evil" not in again and "allow=ripgrep" in again


@posix_only
@pytest.mark.skipif(sys.platform != "linux", reason="the root wrapper is Linux only")
def test_reinstall_removes_the_root_wrapper_when_the_owner_says_no(box):
    tmp_path, ah, env = box
    assert run_sh(env).returncode == 0
    wrapper, sudoers, renv = _fake_root(tmp_path, env, ARTEL_ALLOW_ROOT="0")
    out = run_sh(renv, "--reinstall")
    assert out.returncode == 0, out.stdout + out.stderr
    assert not wrapper.exists() and not sudoers.exists()


def _artel(env, *args, **kw):
    return subprocess.run([str(Path(env["ARTEL_BIN"]) / "artel"), *args], env=env, capture_output=True, text=True, **kw)


@posix_only
def test_reinstall_run_from_inside_the_app_dir_leaves_a_working_install(box):
    _, ah, env = box
    assert run_sh(env).returncode == 0
    out = subprocess.run([BASH, str(ROOT / "install.sh"), "--reinstall", "--yes", "--no-start"], env=env, text=True,
                         cwd=ah / "app", capture_output=True, stdin=subprocess.DEVNULL, timeout=300)
    assert out.returncode == 0, out.stdout + out.stderr
    assert (ah / "app" / ".git").is_dir() and (ah / "venv" / "bin" / "python").exists()
    assert _artel(env, "--help").returncode == 0
    assert not list(ah.glob("*.new-*")), "temporary directories must be cleaned up"


@posix_only
def test_failed_clone_leaves_the_old_install_untouched(box):
    tmp, ah, env = box
    assert run_sh(env).returncode == 0
    (ah / "venv" / "STALE").write_text("old", encoding="utf-8")
    head = g(ah / "app", "rev-parse", "HEAD")
    broken = tmp / "not-a-repo"
    broken.mkdir()  # exists, so the access check passes; the clone itself fails
    out = run_sh({**env, "ARTEL_REPO": str(broken)}, "--reinstall")
    assert out.returncode != 0, out.stdout + out.stderr
    assert g(ah / "app", "rev-parse", "HEAD") == head
    assert (ah / "venv" / "STALE").read_text(encoding="utf-8") == "old"
    assert _artel(env, "--help").returncode == 0
    assert not list(ah.glob("*.new-*")) and not baks(ah / "app") and not baks(ah / "venv")


@posix_only
def test_no_start_does_not_claim_a_live_dashboard(box):
    _, _, env = box
    out = run_sh(env)
    assert out.returncode == 0, out.stdout + out.stderr
    assert "http://127.0.0.1" not in out.stdout
    assert "запуск: arteliq web" in out.stdout


@posix_only
def test_installer_reports_a_busy_port_and_names_the_remedy(box):
    import socket

    _, _, env = box
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        s.listen()
        port = s.getsockname()[1]
        out = subprocess.run([BASH, str(ROOT / "install.sh"), "--yes"], env={**env, "ARTEL_PORT": str(port)}, text=True,
                             capture_output=True, stdin=subprocess.DEVNULL, timeout=300)
    assert out.returncode == 0, out.stdout + out.stderr
    assert f"порт {port} занят" in out.stdout and "arteliq web --port" in out.stdout
    assert f"http://127.0.0.1:{port}" not in out.stdout
