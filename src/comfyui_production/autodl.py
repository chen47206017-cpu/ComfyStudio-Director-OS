from __future__ import annotations

import json
import os
import re
import socket
import ssl
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, Iterator
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, ProxyHandler, build_opener


class AutoDLApiError(RuntimeError):
    """Safe AutoDL error; authentication headers are never included."""

    def __init__(self, message: str, status: int | None = None, body: str = "", secret: str = ""):
        self.status = status
        # The API may echo request metadata.  Redact the configured token from
        # retained response bodies before a caller persists/logs the error.
        redacted = str(body or "")
        if secret:
            redacted = redacted.replace(secret, "[REDACTED]")
        self.body = redacted[:1000]
        super().__init__(message)


_SUCCESS_CODES = {"success", "200", "0"}
_KNOWN_STATUSES = {"QUEUED", "RUNNING", "SUCCESS", "FAILED", "CANCELLED", "CANCELED"}
_TERMINAL_STATUSES = {"SUCCESS", "FAILED", "CANCELLED", "CANCELED"}
# Public workflow drawers currently spell the successful terminal state
# ``completed``; normalize it to the generic API's ``SUCCESS`` state.
_STATUS_ALIASES = {"COMPLETED": "SUCCESS"}
_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


class AutoDLComfyWorkflowClient:
    """Client for AutoDL's two-step wrapped ComfyUI workflow API.

    AutoDL returns short-lived result URLs.  Result downloads intentionally use
    a proxy-disabled opener so a locally enabled Clash Verge route cannot
    silently proxy model or media transfers.
    """

    def __init__(self, base_url: str = "https://autodl.art", token: str = "", timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.token = token.strip()
        self.timeout = max(1.0, float(timeout))
        self.client_id = uuid.uuid4().hex

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if self.token:
            # AutoDL's docs show the token as the raw Authorization value.
            headers["Authorization"] = self.token
        return headers

    def _request(self, method: str, path: str, payload: Any | None = None) -> Any:
        body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = Request(urljoin(self.base_url + "/", path.lstrip("/")), data=body,
                      headers=self._headers(), method=method.upper())
        opener = build_opener(ProxyHandler({}))
        try:
            with opener.open(req, timeout=self.timeout) as response:
                raw = response.read()
        except HTTPError as exc:
            try:
                body_text = exc.read().decode("utf-8", errors="replace")
            except Exception:
                body_text = ""
            raise AutoDLApiError(
                f"AutoDL returned HTTP {exc.code} for {method} {path}",
                exc.code,
                body_text,
                self.token,
            ) from exc
        except (URLError, TimeoutError, socket.timeout, OSError, ssl.SSLError) as exc:
            raise AutoDLApiError("AutoDL is unreachable through direct access") from exc
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise AutoDLApiError("AutoDL returned invalid JSON") from exc

    def _unwrap(self, data: Any, operation: str) -> dict[str, Any]:
        """Validate the documented ``code``/``data`` response envelope."""
        if not isinstance(data, dict):
            raise AutoDLApiError(f"AutoDL {operation} response is not an object")
        code = data.get("code")
        if code is None or str(code).strip().lower() not in _SUCCESS_CODES:
            raise AutoDLApiError(
                f"AutoDL {operation} request was rejected",
                body=json.dumps(data, ensure_ascii=False),
                secret=self.token,
            )
        row = data.get("data")
        if not isinstance(row, dict):
            raise AutoDLApiError(
                f"AutoDL {operation} response has no data object",
                body=json.dumps(data, ensure_ascii=False),
                secret=self.token,
            )
        return row

    @staticmethod
    def _validate_status(row: dict[str, Any], operation: str) -> str:
        status = row.get("status")
        if not isinstance(status, str) or not status.strip():
            raise AutoDLApiError(f"AutoDL {operation} response has no status")
        normalized = _STATUS_ALIASES.get(status.strip().upper(), status.strip().upper())
        if normalized not in _KNOWN_STATUSES:
            raise AutoDLApiError(f"AutoDL {operation} response has unknown status")
        return normalized

    def submit(self, workflow_id: str, body: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(workflow_id, str) or not _ID_RE.fullmatch(workflow_id):
            raise ValueError("invalid AutoDL workflow id")
        if not isinstance(body, dict):
            raise ValueError("AutoDL request body must be an object")
        data = self._request("POST", f"/api/v1/comfyui/comfyui_workflow/{workflow_id}", body)
        row = self._unwrap(data, "submit")
        task_id = row.get("task_id")
        if not isinstance(task_id, str) or not task_id.strip() or not _ID_RE.fullmatch(task_id):
            raise AutoDLApiError(
                "AutoDL response has no valid task_id",
                body=json.dumps(data, ensure_ascii=False),
                secret=self.token,
            )
        row["status"] = self._validate_status(row, "submit")
        return row

    def result(self, task_id: str) -> dict[str, Any]:
        if not isinstance(task_id, str) or not _ID_RE.fullmatch(task_id):
            raise ValueError("invalid AutoDL task id")
        data = self._request("GET", f"/api/v1/comfyui/comfyui_workflow/result/{task_id}")
        row = self._unwrap(data, "result")
        row["status"] = self._validate_status(row, "result")
        returned_task_id = row.get("task_id")
        if not isinstance(returned_task_id, str) or returned_task_id != task_id:
            raise AutoDLApiError("AutoDL result task_id does not match the query")
        return row

    def wait(self, task_id: str, poll_interval: float = 1.0,
             timeout: float | None = None) -> Iterator[dict[str, Any]]:
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            row = self.result(task_id)
            yield row
            status = str(row.get("status", "")).strip().upper()
            if status in _TERMINAL_STATUSES:
                return
            if deadline is not None and time.monotonic() >= deadline:
                return
            time.sleep(max(0.1, poll_interval))

    def download_result(self, url: str, destination: str | Path) -> Path:
        if not isinstance(url, str) or not url.startswith(("https://", "http://")):
            raise ValueError("result URL must be http(s)")
        target = Path(destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        # Explicitly disable all proxy handlers for this transfer.
        opener = build_opener(ProxyHandler({}))
        temporary: Path | None = None
        try:
            with opener.open(Request(url, headers={"User-Agent": "comfyui-production/1.0"}), timeout=self.timeout) as response:
                # Stream to a sibling temp file so an interrupted transfer can
                # never leave a truncated artifact at the final destination.
                with tempfile.NamedTemporaryFile(
                    mode="wb",
                    prefix=f".{target.name}.",
                    suffix=".part",
                    dir=target.parent,
                    delete=False,
                ) as handle:
                    temporary = Path(handle.name)
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        handle.write(chunk)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, target)
        except (HTTPError, URLError, TimeoutError, socket.timeout, OSError, ssl.SSLError) as exc:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass
            raise AutoDLApiError("AutoDL result download failed through direct access") from exc
        return target


class AutoDLProvider:
    name = "AUTODL_COMFYUI"

    def __init__(self, client: AutoDLComfyWorkflowClient):
        self.client = client

    def submit(self, workflow_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return self.client.submit(workflow_id, body)

    def result(self, task_id: str) -> dict[str, Any]:
        return self.client.result(task_id)
