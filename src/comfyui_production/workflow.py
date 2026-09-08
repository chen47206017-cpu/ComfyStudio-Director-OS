from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any


TOKEN_RE = re.compile(r"\{\{\s*([A-Za-z0-9_.-]+)\s*\}\}")


class WorkflowError(ValueError):
    pass


def _replace(value: Any, mapping: dict[str, Any], seen: set[str]) -> Any:
    if isinstance(value, dict):
        return {k: _replace(v, mapping, seen) for k, v in value.items()}
    if isinstance(value, list):
        return [_replace(v, mapping, seen) for v in value]
    if not isinstance(value, str):
        return value

    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in mapping:
            raise WorkflowError(f"missing workflow input: {key}")
        seen.add(key)
        replacement = mapping[key]
        if not isinstance(replacement, (str, int, float, bool)) and replacement is not None:
            raise WorkflowError(f"workflow token {key} must resolve to a scalar")
        return "" if replacement is None else str(replacement)

    return TOKEN_RE.sub(repl, value)


def substitute_workflow(workflow: dict[str, Any], inputs: dict[str, Any]) -> dict[str, Any]:
    """Deep-copy and replace {{token}} strings without mutating the registry."""
    if not isinstance(workflow, dict):
        raise WorkflowError("workflow must be an object")
    used: set[str] = set()
    result = _replace(copy.deepcopy(workflow), inputs, used)
    return result


def workflow_hash(workflow: dict[str, Any]) -> str:
    raw = json.dumps(workflow, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


class WorkflowRegistry:
    def __init__(self, directory: Path):
        self.directory = directory

    def list(self) -> list[dict[str, Any]]:
        self.directory.mkdir(parents=True, exist_ok=True)
        rows: list[dict[str, Any]] = []
        for path in sorted(self.directory.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(data, dict):
                continue
            rows.append({
                "id": path.stem,
                "path": str(path),
                "hash": workflow_hash(data),
                "workflow": data,
            })
        return rows

    def get(self, workflow_id: str) -> dict[str, Any]:
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", workflow_id):
            raise WorkflowError("invalid workflow id")
        path = (self.directory / f"{workflow_id}.json").resolve()
        if path.parent != self.directory.resolve():
            raise WorkflowError("workflow path escaped registry")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise WorkflowError(f"workflow not found: {workflow_id}") from exc
        except json.JSONDecodeError as exc:
            raise WorkflowError(f"workflow is invalid JSON: {workflow_id}") from exc
        if not isinstance(data, dict):
            raise WorkflowError("workflow root must be an object")
        return data

