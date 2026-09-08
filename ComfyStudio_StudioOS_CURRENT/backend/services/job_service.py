from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping
from zoneinfo import ZoneInfo


try:
    BEIJING = ZoneInfo("Asia/Shanghai")
except Exception:
    BEIJING = timezone(timedelta(hours=8), name="Asia/Shanghai")


def now_beijing() -> str:
    return datetime.now(timezone.utc).astimezone(BEIJING).isoformat(timespec="seconds")


class JobStore:
    """Small transactional job store; it never mutates the protected JSON databases."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_schema(self) -> None:
        with closing(self._connect()) as connection:
            with connection:
                connection.executescript(
                    """
                    PRAGMA journal_mode=WAL;
                    CREATE TABLE IF NOT EXISTS schema_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                    INSERT OR IGNORE INTO schema_meta(key, value) VALUES ('version', '1');
                    CREATE TABLE IF NOT EXISTS jobs (
                        id TEXT PRIMARY KEY,
                        idempotency_key TEXT NOT NULL UNIQUE,
                        status TEXT NOT NULL,
                        lane TEXT NOT NULL,
                        capsule_id TEXT,
                        worker_id TEXT,
                        prompt_id TEXT,
                        payload_json TEXT NOT NULL,
                        error_json TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS job_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        job_id TEXT NOT NULL,
                        status TEXT NOT NULL,
                        detail_json TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS job_outputs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        job_id TEXT NOT NULL,
                        path TEXT,
                        sha256 TEXT,
                        mime TEXT,
                        verified INTEGER NOT NULL DEFAULT 0,
                        created_at TEXT NOT NULL
                    );
                    """
                )

    @staticmethod
    def _row(row: sqlite3.Row | None) -> dict[str, Any] | None:
        if row is None:
            return None
        item = dict(row)
        for key in ("payload_json", "error_json"):
            raw = item.pop(key, None)
            item[key.removesuffix("_json")] = json.loads(raw) if raw else None
        return item

    def get(self, job_id: str) -> dict[str, Any] | None:
        with closing(self._connect()) as connection:
            return self._row(connection.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone())

    def list(self, limit: int = 100) -> list[dict[str, Any]]:
        with closing(self._connect()) as connection:
            return [self._row(row) for row in connection.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()]

    def active(self) -> list[dict[str, Any]]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT * FROM jobs WHERE status IN ('QUEUED', 'RUNNING', 'COLLECTING', 'ORPHANED') ORDER BY created_at ASC"
            ).fetchall()
            return [self._row(row) for row in rows]

    def events(self, job_id: str) -> list[dict[str, Any]]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT id, job_id, status, detail_json, created_at FROM job_events WHERE job_id = ? ORDER BY id ASC",
                (job_id,),
            ).fetchall()
            result = []
            for row in rows:
                item = dict(row)
                item["detail"] = json.loads(item.pop("detail_json") or "{}")
                result.append(item)
            return result

    def outputs(self, job_id: str) -> list[dict[str, Any]]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT id, job_id, path, sha256, mime, verified, created_at FROM job_outputs WHERE job_id = ? ORDER BY id ASC",
                (job_id,),
            ).fetchall()
            return [{**dict(row), "verified": bool(row["verified"])} for row in rows]

    def get_output(self, job_id: str, output_id: int | str) -> dict[str, Any] | None:
        """Resolve one JobStore-owned output; callers must not accept raw paths."""
        try:
            identifier = int(output_id)
        except (TypeError, ValueError):
            return None
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT id, job_id, path, sha256, mime, verified, created_at FROM job_outputs WHERE job_id = ? AND id = ?",
                (job_id, identifier),
            ).fetchone()
            return ({**dict(row), "verified": bool(row["verified"])} if row is not None else None)

    def create(self, payload: Mapping[str, Any]) -> tuple[dict[str, Any], bool]:
        idempotency_key = str(payload.get("idempotency_key") or uuid.uuid4())
        now = now_beijing()
        job_id = str(payload.get("id") or f"job-{uuid.uuid4().hex[:12]}")
        lane = str(payload.get("lane") or "local_h3")
        capsule_id = payload.get("capsule_id")
        with closing(self._connect()) as connection:
            existing = connection.execute("SELECT * FROM jobs WHERE idempotency_key = ?", (idempotency_key,)).fetchone()
            if existing is not None:
                return self._row(existing), True
            connection.execute(
                "INSERT INTO jobs(id, idempotency_key, status, lane, capsule_id, worker_id, prompt_id, payload_json, error_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, NULL, NULL, ?, NULL, ?, ?)",
                (job_id, idempotency_key, "DRAFT", lane, capsule_id, json.dumps(dict(payload), ensure_ascii=False), now, now),
            )
            connection.execute("INSERT INTO job_events(job_id, status, detail_json, created_at) VALUES (?, ?, ?, ?)", (job_id, "DRAFT", "{}", now))
            connection.commit()
            row = connection.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            return self._row(row), False

    def transition(self, job_id: str, status: str, detail: Mapping[str, Any] | None = None, **fields: Any) -> dict[str, Any] | None:
        now = now_beijing()
        allowed = {"worker_id", "prompt_id", "error_json"}
        assignments = ["status = ?", "updated_at = ?"]
        values: list[Any] = [status, now]
        for key, value in fields.items():
            if key not in allowed:
                continue
            assignments.append(f"{key} = ?")
            values.append(json.dumps(value, ensure_ascii=False) if key == "error_json" else value)
        values.append(job_id)
        with closing(self._connect()) as connection:
            connection.execute(f"UPDATE jobs SET {', '.join(assignments)} WHERE id = ?", values)
            connection.execute("INSERT INTO job_events(job_id, status, detail_json, created_at) VALUES (?, ?, ?, ?)", (job_id, status, json.dumps(dict(detail or {}), ensure_ascii=False), now))
            connection.commit()
            return self._row(connection.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone())

    def add_output(self, job_id: str, path: str, sha256: str, mime: str, verified: bool) -> dict[str, Any] | None:
        now = now_beijing()
        with closing(self._connect()) as connection:
            existing = connection.execute(
                "SELECT id FROM job_outputs WHERE job_id = ? AND path = ? AND sha256 = ?",
                (job_id, path, sha256),
            ).fetchone()
            if existing is None:
                connection.execute(
                    "INSERT INTO job_outputs(job_id, path, sha256, mime, verified, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (job_id, path, sha256, mime, int(verified), now),
                )
            connection.commit()
            return self._row(connection.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone())
