from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TERMINAL = {"SUCCEEDED", "FAILED", "CANCELLED", "NEEDS_REVIEW"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class JobStore:
    """Small durable JSON store; writes are atomic and serialized."""

    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.RLock()
        self._jobs: dict[str, dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            data = {}
        if isinstance(data, dict):
            self._jobs = {str(k): v for k, v in data.items() if isinstance(v, dict)}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(self._jobs, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            job_id = uuid.uuid4().hex
            row = {
                "job_id": job_id,
                "status": "QUEUED",
                "created_at": utc_now(),
                "updated_at": utc_now(),
                **payload,
            }
            self._jobs[job_id] = row
            self._save()
            return dict(row)

    def get(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._jobs.get(job_id)
            return dict(row) if row else None

    def update(self, job_id: str, **changes: Any) -> dict[str, Any]:
        with self._lock:
            if job_id not in self._jobs:
                raise KeyError(job_id)
            self._jobs[job_id].update(changes, updated_at=utc_now())
            self._save()
            return dict(self._jobs[job_id])

    def list(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._lock:
            rows = sorted(self._jobs.values(), key=lambda x: x.get("created_at", ""), reverse=True)
            return [dict(x) for x in rows[: max(1, min(limit, 500))]]

