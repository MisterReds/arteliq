"""Build the backend sidecar: python desktop/sidecar/build.py  ->  desktop/sidecar/dist/arteliq/"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--distpath", str(HERE / "dist"),
           "--workpath", str(HERE / "build"), str(HERE / "arteliq.spec")]
    rc = subprocess.run(cmd, check=False)  # noqa: S603.returncode
    exe = HERE / "dist" / "arteliq" / ("arteliq.exe" if sys.platform == "win32" else "arteliq")
    if rc == 0 and not exe.is_file():
        print(f"build finished but {exe} is missing", file=sys.stderr)
        return 1
    return rc


if __name__ == "__main__":
    sys.exit(main())
