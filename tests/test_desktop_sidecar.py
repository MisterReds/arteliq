import ast
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "desktop" / "sidecar" / "arteliq.spec"


def _spec_data_dirs() -> list[str]:
    tree = ast.parse(SPEC.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "DATA_DIRS":
            return list(ast.literal_eval(node.value))
    raise AssertionError("DATA_DIRS is not defined in the PyInstaller spec")


def test_sidecar_spec_lists_only_existing_data_dirs():
    dirs = _spec_data_dirs()
    assert dirs, "the sidecar would ship without the dashboard files"
    for d in dirs:
        assert (ROOT / d).is_dir(), f"{d} listed in arteliq.spec does not exist: renamed data dir?"


def test_sidecar_spec_covers_every_package_data_dir_of_the_wheel():
    pkg_data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["setuptools"]["package-data"]
    covered = set(_spec_data_dirs())
    for package in pkg_data:
        assert package.replace(".", "/") in covered, f"{package} has package data but the sidecar spec does not ship it"


def test_sidecar_entry_point_is_the_arteliq_script():
    scripts = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["scripts"]
    module, func = scripts["arteliq"].split(":")
    entry = (ROOT / "desktop" / "sidecar" / "entry.py").read_text(encoding="utf-8")
    assert re.search(rf"from {re.escape(module)} import {func}\b", entry)
