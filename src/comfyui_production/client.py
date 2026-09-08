from __future__ import annotations

import json
import mimetypes
import os
import socket
import time
import uuid
from pathlib import Path
from typing import Any, Iterator
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen


class ComfyApiError(RuntimeError):
    """A safe, user-facing ComfyUI API failure (never includes auth headers)."""

    def __init__(self, message: str, status: int | None = None, body: str = ""):
        self.status = status
        self.body = body[:1000]
        super().__init__(message)


class ComfyUIClient:
    """Small ComfyUI HTTP client with optional websocket progress support."""

    def __init__(self, base_url: str, token: str = "", timeout: float = 30.0, client_id: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.token = token.strip()
        self.timeout = timeout
        self.client_id = client_id or uuid.uuid4().hex

    def _url(self, path: str) -> str:
        return urljoin(self.base_url + "/", path.lstrip("/"))

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if extra:
            headers.update(extra)
        return headers

    def request(self, method: str, path: str, body: bytes | None = None,
                content_type: str | None = None, timeout: float | None = None) -> tuple[int, bytes, dict[str, str]]:
        headers = self._headers()
        if content_type:
            headers["Content-Type"] = content_type
        req = Request(self._url(path), data=body, headers=headers, method=method.upper())
        try:
            with urlopen(req, timeout=timeout or self.timeout) as response:
                return response.status, response.read(), dict(response.headers.items())
        except HTTPError as exc:
            try:
                raw = exc.read().decode("utf-8", errors="replace")
            except Exception:
                raw = ""
            raise ComfyApiError(f"ComfyUI returned HTTP {exc.code} for {method} {path}", exc.code, raw) from exc
        except (URLError, TimeoutError, socket.timeout, OSError) as exc:
            raise ComfyApiError(f"ComfyUI is unreachable at {self.base_url}") from exc

    def json_request(self, method: str, path: str, payload: Any | None = None,
                     timeout: float | None = None) -> Any:
        body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        _, raw, _ = self.request(method, path, body, "application/json; charset=utf-8", timeout)
        if not raw:
            return None
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ComfyApiError(f"ComfyUI returned invalid JSON for {method} {path}") from exc

    def health(self) -> dict[str, Any]:
        data = self.json_request("GET", "/system_stats")
        return data if isinstance(data, dict) else {"ok": True, "raw": data}

    def queue_prompt(self, prompt: dict[str, Any], extra: dict[str, Any] | None = None) -> dict[str, Any]:
        if not isinstance(prompt, dict):
            raise ValueError("prompt must be an object")
        payload = {"prompt": prompt, "client_id": self.client_id}
        if extra:
            payload.update(extra)
        data = self.json_request("POST", "/prompt", payload)
        if not isinstance(data, dict):
            raise ComfyApiError("ComfyUI /prompt response is not an object")
        if data.get("error"):
            raise ComfyApiError(f"ComfyUI rejected prompt: {data.get('error')}", body=json.dumps(data, ensure_ascii=False))
        prompt_id = data.get("prompt_id")
        if not prompt_id:
            raise ComfyApiError("ComfyUI /prompt response has no prompt_id", body=json.dumps(data, ensure_ascii=False))
        return data

    def history(self, prompt_id: str | None = None) -> dict[str, Any]:
        path = "/history" if not prompt_id else f"/history/{prompt_id}"
        data = self.json_request("GET", path)
        return data if isinstance(data, dict) else {}

    def interrupt(self) -> Any:
        return self.json_request("POST", "/interrupt", {})

    def delete_queue(self, prompt_id: str) -> Any:
        # Newer ComfyUI builds accept DELETE /queue with a list of IDs; older
        # builds only expose /interrupt. Callers can fall back gracefully.
        return self.json_request("DELETE", "/queue", {"delete": [prompt_id]})

    def upload_file(self, path: str | Path, field_name: str = "image", upload_type: str = "input",
                    overwrite: bool = False) -> dict[str, Any]:
        file_path = Path(path)
        data = file_path.read_bytes()
        boundary = "----ComfyUIBoundary" + uuid.uuid4().hex
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        fields = {
            "type": upload_type,
            "overwrite": "true" if overwrite else "false",
        }
        chunks: list[bytes] = []
        for key, value in fields.items():
            chunks.extend([
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode(),
                str(value).encode(), b"\r\n",
            ])
        chunks.extend([
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="{field_name}"; filename="{file_path.name}"\r\n'.encode(),
            f"Content-Type: {content_type}\r\n\r\n".encode(),
            data, b"\r\n",
            f"--{boundary}--\r\n".encode(),
        ])
        _, raw, _ = self.request("POST", "/upload/image", b"".join(chunks), f"multipart/form-data; boundary={boundary}")
        try:
            result = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ComfyApiError("ComfyUI upload returned invalid JSON") from exc
        if not isinstance(result, dict):
            raise ComfyApiError("ComfyUI upload response is not an object")
        return result

    def download_view(self, filename: str, subfolder: str = "", file_type: str = "output",
                      destination: str | Path | None = None) -> bytes | Path:
        query = urlencode({"filename": filename, "subfolder": subfolder, "type": file_type})
        _, raw, _ = self.request("GET", f"/view?{query}")
        if destination is None:
            return raw
        target = Path(destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        return target

    def iter_progress(self, prompt_id: str, poll_interval: float = 1.0,
                      timeout: float | None = None) -> Iterator[dict[str, Any]]:
        """Yield websocket progress when websocket-client is installed, else poll history.

        The fallback is intentionally deterministic for headless deployments and
        still exposes the same event shape to the API layer.
        """
        deadline = None if timeout is None else time.monotonic() + timeout
        try:
            import websocket  # type: ignore
        except ImportError:
            websocket = None
        if websocket is not None and self.base_url.startswith(("http://", "https://")):
            ws_url = self.base_url.replace("https://", "wss://", 1).replace("http://", "ws://", 1)
            ws_url += f"/ws?clientId={self.client_id}"
            headers = [f"Authorization: Bearer {self.token}"] if self.token else None
            try:
                ws = websocket.create_connection(ws_url, timeout=min(self.timeout, 10), header=headers)
                try:
                    while True:
                        if deadline is not None and time.monotonic() >= deadline:
                            break
                        raw = ws.recv()
                        if not raw:
                            break
                        if isinstance(raw, bytes):
                            continue
                        try:
                            message = json.loads(raw)
                        except json.JSONDecodeError:
                            continue
                        if message.get("type") == "progress":
                            value = message.get("data") or {}
                            if value.get("prompt_id") in (None, prompt_id):
                                yield {"type": "progress", **value}
                        elif message.get("type") == "executing":
                            value = message.get("data") or {}
                            if value.get("prompt_id") == prompt_id:
                                yield {"type": "executing", **value}
                                if value.get("node") is None:
                                    break
                        elif message.get("type") == "execution_error":
                            value = message.get("data") or {}
                            if value.get("prompt_id") == prompt_id:
                                yield {"type": "execution_error", **value}
                                break
                finally:
                    ws.close()
                return
            except Exception:
                # A server may disable websockets behind a proxy; use history.
                pass

        while True:
            history = self.history(prompt_id)
            row = history.get(prompt_id) if isinstance(history, dict) else None
            if isinstance(row, dict):
                status = row.get("status") or {}
                completed = bool(status.get("completed"))
                yield {"type": "history", "prompt_id": prompt_id, "completed": completed, "entry": row}
                if completed or row.get("outputs") or status.get("status_str") in {"error", "success"}:
                    break
            if deadline is not None and time.monotonic() >= deadline:
                break
            time.sleep(max(0.1, poll_interval))


class ComfyProvider:
    name = "BASE"

    def __init__(self, client: ComfyUIClient):
        self.client = client

    def health(self) -> dict[str, Any]:
        return self.client.health()

    def submit(self, workflow: dict[str, Any]) -> dict[str, Any]:
        return self.client.queue_prompt(workflow)


class LocalComfyProvider(ComfyProvider):
    name = "LOCAL"


class RemoteComfyProvider(ComfyProvider):
    name = "REMOTE_STATIC"


def provider_from_settings(settings: Any) -> Any:
    """Build the configured provider without importing optional transports eagerly.

    AutoDL is intentionally kept as a separate transport because its wrapped
    workflow API is not the same contract as a native ComfyUI ``/prompt``
    server.  Importing it lazily also keeps local-only deployments independent
    from the hosted provider implementation.
    """
    provider = str(getattr(settings, "provider", "LOCAL")).upper()
    if provider == "AUTODL_COMFYUI":
        from .autodl import AutoDLComfyWorkflowClient, AutoDLProvider

        base_url = str(getattr(settings, "autodl_api_base_url", "https://autodl.art")).strip()
        token = str(getattr(settings, "autodl_api_token", "")).strip()
        if not base_url:
            raise ValueError("AUTODL_API_BASE_URL is required for AUTODL_COMFYUI")
        if not token:
            raise ValueError("AUTODL_API_TOKEN is required for AUTODL_COMFYUI")
        timeout = float(getattr(settings, "client_timeout_seconds", 30.0))
        return AutoDLProvider(AutoDLComfyWorkflowClient(base_url, token, timeout))
    if provider == "REMOTE_STATIC":
        url = getattr(settings, "remote_url", "")
        if not url:
            raise ValueError("COMFY_REMOTE_URL is required for REMOTE_STATIC")
        return RemoteComfyProvider(ComfyUIClient(url, getattr(settings, "remote_token", ""), settings.client_timeout_seconds))
    return LocalComfyProvider(ComfyUIClient(settings.local_url, timeout=settings.client_timeout_seconds))
