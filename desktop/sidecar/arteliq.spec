# -*- mode: python ; coding: utf-8 -*-
# PyInstaller onedir build of the Arteliq backend (the sidecar of the desktop app).
# Run through build.py. DATA_DIRS must match [tool.setuptools.package-data] in pyproject.toml
# (tests/test_desktop_sidecar.py checks that).
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

HERE = Path(SPECPATH).resolve()  # noqa: F821
ROOT = HERE.parents[1]
DATA_DIRS = ["artel/web", "artel/data"]

a = Analysis(  # noqa: F821
    [str(HERE / "entry.py")],
    pathex=[str(ROOT)],
    datas=[(str(ROOT / d), d) for d in DATA_DIRS],
    hiddenimports=collect_submodules("artel"),
    excludes=["tkinter"],
)
pyz = PYZ(a.pure)  # noqa: F821
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="arteliq", console=True)  # noqa: F821
coll = COLLECT(exe, a.binaries, a.datas, name="arteliq")  # noqa: F821
