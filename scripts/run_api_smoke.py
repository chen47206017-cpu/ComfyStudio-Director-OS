"""Run the local API smoke suite without requiring pytest."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    source = str(root / "src")
    env["PYTHONPATH"] = source + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    completed = subprocess.run([sys.executable, "tests/api_smoke.py"], cwd=root, env=env)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
