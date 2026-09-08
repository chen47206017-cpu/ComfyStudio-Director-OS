"""Bounded root resolution for the portable StudioOS production project."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


MARKER_NAME = "studioos.root.json"
MAX_PARENT_STEPS = 5


class StudioRootResolutionError(RuntimeError):
    """Raised with a Chinese repair action when the project root is ambiguous."""


@dataclass(frozen=True)
class StudioPaths:
    app_root: Path
    data_root: Path
    database_dir: Path
    reports_dir: Path
    workflows_dir: Path
    ui_dir: Path
    timezone: str
    marker_path: Path | None


def _read_marker(marker: Path) -> dict[str, object] | None:
    try:
        data = json.loads(marker.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _parents(start: Path) -> Iterable[Path]:
    current = start.resolve()
    if current.is_file():
        current = current.parent
    yield current
    for _ in range(MAX_PARENT_STEPS):
        parent = current.parent
        if parent == current:
            break
        current = parent
        yield current


def _root_from_marker(marker: Path) -> tuple[Path, dict[str, object]] | None:
    payload = _read_marker(marker)
    if payload is None:
        return None
    marker_root = marker.parent.resolve()
    current_name = str(payload.get("current_root") or "").strip()
    if (marker_root / "backend").is_dir():
        return marker_root, payload
    if current_name and (marker_root / current_name / "backend").is_dir():
        return (marker_root / current_name).resolve(), payload
    return None


def _candidate_from_path(path: Path) -> tuple[Path, dict[str, object], Path] | None:
    for folder in _parents(path):
        marker = folder / MARKER_NAME
        result = _root_from_marker(marker) if marker.is_file() else None
        if result is not None:
            root, marker_data = result
            return root, marker_data, marker
    return None


def resolve_studio_paths(anchor: Path | None = None) -> StudioPaths:
    """Resolve StudioOS without scanning disks or embedding a user-specific path.

    The environment variable is deliberately first so a launcher can point to a
    moved production checkout.  Marker searches are bounded to the current
    working directory and code anchor; no drive-wide discovery is performed.
    """

    configured = os.environ.get("STUDIOOS_ROOT", "").strip()
    if configured:
        root = Path(configured).expanduser().resolve()
        if not (root / "backend").is_dir():
            raise StudioRootResolutionError("STUDIOOS_ROOT 无效：目录中缺少 backend；请指向 StudioOS_CURRENT 根目录。")
        marker = root / MARKER_NAME
        marker_data = _read_marker(marker) or {}
        marker_path: Path | None = marker if marker.is_file() else None
    else:
        selected = _candidate_from_path(Path.cwd())
        if selected is None and anchor is not None:
            selected = _candidate_from_path(anchor)
        if selected is None:
            # Local source fallback is intentionally narrow: this module's
            # backend parent is valid only when it looks like the project root.
            local_root = Path(__file__).resolve().parents[2]
            if (local_root / "backend").is_dir() and (local_root / "ui").is_dir():
                root, marker_data, marker_path = local_root, {}, None
            else:
                raise StudioRootResolutionError(
                    "无法定位 StudioOS 根目录；请设置 STUDIOOS_ROOT 或在根目录放置 studioos.root.json。"
                )
        else:
            root, marker_data, marker_path = selected

    data_root_value = str(marker_data.get("data_root") or os.environ.get("STUDIOOS_DATA_ROOT") or (root / "data"))
    data_root = Path(data_root_value).expanduser()
    if not data_root.is_absolute():
        data_root = root / data_root
    return StudioPaths(
        app_root=root,
        data_root=data_root,
        database_dir=root / "database",
        reports_dir=root / "reports",
        workflows_dir=root / "workflows",
        ui_dir=root / "ui",
        timezone=str(marker_data.get("timezone") or "Asia/Shanghai"),
        marker_path=marker_path,
    )
