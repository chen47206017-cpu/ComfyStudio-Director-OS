"""Parse every checked-in workflow JSON file without contacting a provider."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    workflow_root = root / "workflows"
    files = sorted(workflow_root.rglob("*.json"))
    errors: list[str] = []
    for path in files:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"{path.relative_to(root)}: {exc}")
            continue
        if not isinstance(value, dict):
            errors.append(f"{path.relative_to(root)}: top level must be an object")
            continue
        # API graphs use a prompt object; catalog/spec files intentionally use
        # other top-level keys and are still checked for valid JSON above.
        prompt = value.get("prompt")
        if prompt is not None and not isinstance(prompt, dict):
            errors.append(f"{path.relative_to(root)}: prompt must be an object")
    if errors:
        print("Workflow JSON errors:")
        print("\n".join(errors))
        return 1
    print(f"Validated {len(files)} workflow JSON file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
