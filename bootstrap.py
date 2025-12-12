"""
Lightweight dependency bootstrapper.

On startup we check if required third-party packages are importable; if not, we
attempt to `pip install -r requirements.txt` using the current interpreter.
This keeps the app self-contained for assessors without manual setup.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from typing import Iterable, List


def _requirements_path() -> str:
    return os.path.join(os.path.dirname(__file__), "requirements.txt")


def _pip_names_to_modules(names: Iterable[str]) -> List[str]:
    """Best-effort mapping from pip package names to importable modules."""
    module_map = {
        "pillow": "PIL",
        "python-dateutil": "dateutil",
    }
    modules: List[str] = []
    for name in names:
        base = name.strip()
        if not base or base.startswith("#"):
            continue
        pkg = base.split()[0].split("==")[0]
        modules.append(module_map.get(pkg.lower(), pkg.replace("-", "_")))
    return modules


def _missing_modules(modules: Iterable[str]) -> List[str]:
    return [m for m in modules if importlib.util.find_spec(m) is None]


def ensure_dependencies():
    """
    Ensure required third-party packages are installed.

    If anything is missing, we invoke pip install -r requirements.txt using the
    current interpreter. Errors are surfaced as warnings rather than crashes so
    the app can continue (and report missing modules) gracefully.
    """
    marker = os.environ.get("CAMPTRACK_BOOTSTRAP_DONE")
    if marker:
        return

    req_path = _requirements_path()
    if not os.path.exists(req_path):
        return

    try:
        with open(req_path, "r", encoding="utf-8") as f:
            req_lines = f.readlines()
    except Exception:
        return

    modules = _pip_names_to_modules(req_lines)
    missing = _missing_modules(modules)
    if not missing:
        os.environ["CAMPTRACK_BOOTSTRAP_DONE"] = "1"
        return

    print("Bootstrapping dependencies via pip (missing: %s)..." % ", ".join(missing))
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", req_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        os.environ["CAMPTRACK_BOOTSTRAP_DONE"] = "1"
    except Exception:
        print("Warning: automatic dependency install failed. Please run:")
        print(f"  {sys.executable} -m pip install -r {req_path}")

