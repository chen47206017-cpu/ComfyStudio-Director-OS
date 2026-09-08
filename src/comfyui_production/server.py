"""Loopback-only HTTP API for the ComfyUI production integration.

The module intentionally uses the Python standard library.  It is suitable
for the existing web management page to call from the same machine without
opening a public ComfyUI port.  Long-running provider work is dispatched to a
daemon thread and its redacted request/status is kept in :class:`JobStore`.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import ipaddress
import json
import mimetypes
import re
import socket
import threading
import time
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs, quote, unquote, urlsplit

from .autodl import AutoDLComfyWorkflowClient, AutoDLProvider
from .client import ComfyUIClient, LocalComfyProvider, RemoteComfyProvider
from .config import Settings
from .h3 import ENGINE_ID, MiniMaxH3PlanError, h3_catalog, is_minimax_h3_workflow_id, plan_autodl_dry_run
from .media import MediaError, MediaResolver
from .store import JobStore, TERMINAL
from .workflow import WorkflowError, WorkflowRegistry, substitute_workflow, workflow_hash


JOB_PATH_RE = re.compile(r"^/api/comfyui/jobs/([A-Za-z0-9_-]+)(?:/(cancel|retry))?/?$")
OUTPUT_LIST_RE = re.compile(r"^/api/comfyui/jobs/([A-Za-z0-9_-]+)/outputs$")
OUTPUT_PATH_RE = re.compile(r"^/api/comfyui/jobs/([A-Za-z0-9_-]+)/outputs/(.+)$")
WORKFLOW_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
# ``ThreadingHTTPServer`` uses an IPv4 socket by default.  Accept only hosts
# it can actually bind instead of advertising an IPv6 configuration that will
# fail at startup.
LOOPBACK_HOSTS = {"127.0.0.1", "localhost"}
SENSITIVE_KEY_RE = re.compile(r"(?:token|secret|password|passwd|api[_-]?key|authorization|cookie)", re.I)
HTTP_URL_RE = re.compile(r"^https?://[^\s<>\x00-\x1f]+$", re.I)
HTTP_URL_ANY_RE = re.compile(r"https?://[^\s<>\x00-\x1f]+", re.I)


class ApiError(ValueError):
    """An expected request/provider error with an HTTP status code."""

    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def _redact(value: Any, key: str = "") -> Any:
    """Return JSON-safe request data without credentials or huge payloads."""
    if SENSITIVE_KEY_RE.search(key):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {str(k): _redact(v, str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact(v, key) for v in value[:200]]
    if isinstance(value, str):
        # Signed AutoDL URLs can contain credentials in the query string.
        # Persist a marker only; callers must download while the URL is live.
        return HTTP_URL_ANY_RE.sub("[REMOTE_URL_REDACTED]", value)
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return str(value)


def _safe_metadata(value: Any, key: str = "", depth: int = 0) -> Any:
    """Bound provider metadata before saving it in the durable job store."""
    if SENSITIVE_KEY_RE.search(key):
        return "[REDACTED]"
    if depth >= 8:
        return "[TRUNCATED]"
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for index, (nested_key, nested_value) in enumerate(value.items()):
            if index >= 100:
                result["_truncated"] = True
                break
            safe_key = str(nested_key)[:200]
            result[safe_key] = _safe_metadata(nested_value, safe_key, depth + 1)
        return result
    if isinstance(value, list):
        result = [_safe_metadata(item, key, depth + 1) for item in value[:100]]
        if len(value) > 100:
            result.append("[TRUNCATED]")
        return result
    if isinstance(value, str):
        redacted = HTTP_URL_ANY_RE.sub("[REMOTE_URL_REDACTED]", value)
        return redacted[:4096] + ("[TRUNCATED]" if len(redacted) > 4096 else "")
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return str(value)[:4096]


def _request_requires_resubmission(value: Any) -> bool:
    """Whether durable redaction removed data required for a safe retry."""
    if isinstance(value, str):
        return "[REDACTED]" in value or "[REMOTE_URL_REDACTED]" in value
    if isinstance(value, dict):
        return any(_request_requires_resubmission(item) for item in value.values())
    if isinstance(value, list):
        return any(_request_requires_resubmission(item) for item in value)
    return False


def _json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _provider_name(value: Any) -> str:
    name = str(value or "LOCAL").strip().upper()
    aliases = {"AUTODL": "AUTODL_COMFYUI", "CLOUD": "AUTODL_COMFYUI"}
    return aliases.get(name, name)


def _is_terminal(status: Any) -> bool:
    return str(status or "").upper() in TERMINAL


def _sha256_file(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            size += len(block)
            digest.update(block)
    return size, digest.hexdigest()


def _safe_artifact_name(value: Any, fallback: str = "artifact.bin") -> str:
    """Normalize a provider filename without trusting remote path segments."""
    raw = unquote(str(value or "")).replace("\\", "/")
    parts = [part for part in raw.split("/") if part]
    if not parts or any(part in {".", ".."} for part in parts):
        raw = fallback
    else:
        raw = parts[-1]
    raw = "".join(c if c.isascii() and (c.isalnum() or c in "._-") else "_" for c in raw).strip(" .")
    if not raw:
        raw = fallback
    # Keep filesystem and response headers bounded while retaining the suffix.
    if len(raw) > 180:
        stem, suffix = Path(raw).stem, Path(raw).suffix
        raw = stem[: max(1, 180 - len(suffix))] + suffix
    if raw.upper().split(".", 1)[0] in {"CON", "PRN", "AUX", "NUL", "COM1", "LPT1"}:
        raw = "_" + raw
    return raw


def _collect_http_urls(value: Any, found: list[str] | None = None) -> list[str]:
    """Find result URLs for immediate download without retaining their values."""
    found = found if found is not None else []
    if isinstance(value, str) and HTTP_URL_RE.fullmatch(value.strip()):
        url = value.strip()
        if url not in found:
            parsed = urlsplit(url)
            if _safe_result_url(parsed):
                found.append(url)
    elif isinstance(value, dict):
        for nested in value.values():
            _collect_http_urls(nested, found)
    elif isinstance(value, list):
        for nested in value:
            _collect_http_urls(nested, found)
    return found


def _safe_result_url(parsed: Any) -> bool:
    """Reject credentials, loopback, private and malformed result URLs."""
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        return False
    if parsed.username or parsed.password or parsed.fragment:
        return False
    try:
        port = parsed.port
    except ValueError:
        return False
    if port not in (None, 80, 443):
        return False
    host = parsed.hostname.strip("[]").lower()
    if host in {"localhost", "localhost.localdomain"}:
        return False
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return True
    return not (address.is_private or address.is_loopback or address.is_link_local or address.is_reserved)


def _safe_provider_path(value: Any) -> str | None:
    """Accept a relative ComfyUI filename/subfolder, never an OS path."""
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.replace("\\", "/").strip()
    if normalized.startswith("/") or re.match(r"^[A-Za-z]:", normalized):
        return None
    parts = [part for part in normalized.split("/") if part]
    if not parts or any(part in {".", ".."} for part in parts):
        return None
    return "/".join(parts)


@dataclass(frozen=True)
class ProviderBundle:
    name: str
    provider: Any


class ApiApplication:
    """Request router and job coordinator, independent of the HTTP server."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        store: JobStore | None = None,
        registry: WorkflowRegistry | None = None,
        resolver: MediaResolver | None = None,
        provider_factory: Callable[[str], Any] | None = None,
    ):
        self.settings = settings or Settings.from_env()
        self.store = store or JobStore(self.settings.job_store)
        self.registry = registry or WorkflowRegistry(self.settings.workflow_dir)
        self.resolver = resolver or MediaResolver(self.settings.allowed_media_roots, self.settings.max_upload_mb)
        self._provider_factory = provider_factory or self._default_provider
        self._providers: dict[str, Any] = {}
        self._threads: dict[str, threading.Thread] = {}
        # Original request data may contain signed media URLs.  Keep it only
        # long enough to submit the current in-process job; JobStore always
        # receives the redacted copy below.
        self._runtime_requests: dict[str, dict[str, Any]] = {}
        self._lock = threading.RLock()

    def _default_provider(self, name: str) -> Any:
        if name == "AUTODL_COMFYUI":
            if not self.settings.autodl_api_token.strip():
                raise ApiError("AUTODL_API_TOKEN is required for AUTODL_COMFYUI", 503)
            parsed = urlsplit(self.settings.autodl_api_base_url)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                raise ApiError("AUTODL_API_BASE_URL must be an http(s) URL", 503)
            return AutoDLProvider(
                AutoDLComfyWorkflowClient(
                    self.settings.autodl_api_base_url,
                    self.settings.autodl_api_token,
                    self.settings.client_timeout_seconds,
                )
            )
        if name == "LOCAL":
            return LocalComfyProvider(
                ComfyUIClient(
                    self.settings.local_url,
                    timeout=self.settings.client_timeout_seconds,
                )
            )
        if name == "REMOTE_STATIC":
            if not self.settings.remote_url:
                raise ApiError("COMFY_REMOTE_URL is required for REMOTE_STATIC", 503)
            return RemoteComfyProvider(
                ComfyUIClient(
                    self.settings.remote_url,
                    token=self.settings.remote_token,
                    timeout=self.settings.client_timeout_seconds,
                )
            )
        raise ApiError(f"unsupported provider: {name}", 400)

    def provider(self, name: str | None = None) -> ProviderBundle:
        selected = _provider_name(name or self.settings.provider)
        with self._lock:
            provider = self._providers.get(selected)
            if provider is None:
                provider = self._provider_factory(selected)
                self._providers[selected] = provider
        return ProviderBundle(selected, provider)

    def dispatch(self, method: str, path: str, payload: Any | None = None) -> tuple[int, dict[str, Any]]:
        """Dispatch one JSON request and return ``(status, object)``.

        This method is deliberately public so tests and an existing web server
        can exercise the API without binding a socket.
        """
        method = method.upper()
        parsed = urlsplit(path)
        route = parsed.path.rstrip("/") or "/"
        if method == "GET" and route == "/api/comfyui/health":
            return self._health()
        if method == "GET" and route == "/api/comfyui/workflows":
            return 200, {"workflows": self._workflow_summaries()}
        if method == "GET" and route == "/api/comfyui/presets":
            return 200, {"presets": self._presets()}
        if method == "GET" and route == "/api/comfyui/engines":
            return 200, {"engines": [h3_catalog()]}
        if method == "POST" and route == "/api/comfyui/h3/dry-run":
            return self._h3_dry_run(payload)
        if method == "GET" and route == "/api/comfyui/jobs":
            limit = _query_limit(parsed.query)
            return 200, {"jobs": self.store.list(limit)}
        if method == "POST" and route == "/api/comfyui/jobs":
            return self._create_job(payload)

        output_list_match = OUTPUT_LIST_RE.match(route)
        if method == "GET" and output_list_match:
            job_id = output_list_match.group(1)
            row = self.store.get(job_id)
            if row is None:
                raise ApiError("job not found", 404)
            return 200, {"job_id": job_id, "artifacts": row.get("artifacts", [])}

        output_match = OUTPUT_PATH_RE.match(route)
        if method == "GET" and output_match:
            # The HTTP handler streams the actual file.  The dispatch surface
            # remains JSON-only for embedders that do not bind a socket.
            job_id, filename = output_match.groups()
            target, content_type = self.resolve_output(job_id, filename)
            return 200, {
                "job_id": job_id,
                "filename": target.name,
                "content_type": content_type,
                "size_bytes": target.stat().st_size,
            }

        match = JOB_PATH_RE.match(route)
        if match:
            job_id, action = match.groups()
            if method == "GET" and action is None:
                return self._get_job(job_id)
            if method == "POST" and action == "cancel":
                return self._cancel_job(job_id)
            if method == "POST" and action == "retry":
                return self._retry_job(job_id)
        raise ApiError("route not found", 404)

    def _workflow_summaries(self) -> list[dict[str, Any]]:
        rows = []
        for row in self.registry.list():
            rows.append({"id": row["id"], "hash": row["hash"], "path": row["path"]})
        return rows

    @staticmethod
    def _presets() -> list[dict[str, Any]]:
        return [
            {
                "id": "LOCAL_DRAFT",
                "provider": "LOCAL",
                "width": 432,
                "height": 768,
                "fps": 24,
                "frames": 81,
                "duration_seconds": 3.38,
                "aspect_ratio": "9:16",
                "quality": "draft",
                "delivery_stage": "technical_smoke_only",
            },
            {
                "id": "CLOUD_5090_QUALITY",
                "provider": "AUTODL_COMFYUI",
                "width": 1080,
                "height": 1920,
                "fps": 24,
                "frames": 121,
                "duration_seconds": 5.04,
                "aspect_ratio": "9:16",
                "resolution_label": "1080p竖",
                "quality": "quality",
                "gpu": "RTX 5090 32GB",
                "delivery_stage": "final_delivery_target",
                "render_strategy": "verified_direct_renderer_or_validated_upscale",
                "h3_source_resolution": "UNVERIFIED_PER_WORKFLOW_DRAWER",
                "subtitle_style": "SUBTITLE_LOCK_V1",
                "requires_burned_subtitles": True,
            },
        ]

    @staticmethod
    def _h3_dry_run(payload: Any) -> tuple[int, dict[str, Any]]:
        try:
            plan = plan_autodl_dry_run(payload)
        except MiniMaxH3PlanError as exc:
            raise ApiError(str(exc), 422) from exc
        return 200, _redact(plan)

    def _health(self) -> tuple[int, dict[str, Any]]:
        selected = _provider_name(self.settings.provider)
        result: dict[str, Any] = {
            "ok": True,
            "service": "comfyui-production",
            "provider": selected,
            "api_host": self.settings.api_host,
            "api_port": self.settings.api_port,
        }
        try:
            bundle = self.provider(selected)
            health_fn = getattr(bundle.provider, "health", None)
            if callable(health_fn):
                provider_health = health_fn()
            elif selected == "AUTODL_COMFYUI":
                # AutoDL exposes task endpoints rather than a ComfyUI
                # /system_stats endpoint.  Presence of a configured client is
                # still useful service health, while a real task proves remote
                # reachability during submission.
                provider_health = {
                    "configured": bool(self.settings.autodl_api_token),
                    "base_url": self.settings.autodl_api_base_url,
                    "reachability": "deferred_until_submit",
                }
            else:
                provider_health = {"configured": True}
            result["provider_ok"] = True
            if isinstance(provider_health, dict):
                result["provider_health"] = _redact(provider_health)
            else:
                result["provider_health"] = {"raw": _redact(provider_health)}
            return 200, result
        except Exception as exc:
            result.update({"ok": False, "provider_ok": False, "error": _redact(str(exc))[:500]})
            return 503, result

    def _create_job(self, payload: Any) -> tuple[int, dict[str, Any]]:
        if not isinstance(payload, dict):
            raise ApiError("request body must be a JSON object")
        engine = payload.get("engine")
        if isinstance(engine, str) and engine.strip().upper() == ENGINE_ID:
            raise ApiError("MiniMax H3 is dry-run only; use POST /api/comfyui/h3/dry-run", 409)
        workflow_id = payload.get("workflow_id")
        if not isinstance(workflow_id, str) or not WORKFLOW_ID_RE.fullmatch(workflow_id):
            raise ApiError("workflow_id is required and must be a safe identifier")
        if is_minimax_h3_workflow_id(workflow_id):
            raise ApiError("MiniMax H3 cloud submission is disabled; use POST /api/comfyui/h3/dry-run", 409)
        provider_name = _provider_name(payload.get("provider") or self.settings.provider)
        if provider_name == "AUTODL_COMFYUI":
            if not self.settings.autodl_allow_paid_submit:
                raise ApiError(
                    "AutoDL paid submission is disabled; set AUTODL_ALLOW_PAID_SUBMIT=1 only after explicit authorization",
                    409,
                )
            if "body" not in payload or not isinstance(payload.get("body"), dict):
                raise ApiError(
                    "AUTODL_COMFYUI requires body to be a JSON object containing the exact vendor workflow payload",
                    422,
                )
        # Validate provider before writing a durable job row.
        self.provider(provider_name)
        inputs = payload.get("inputs") or {}
        if not isinstance(inputs, dict):
            raise ApiError("inputs must be an object")
        media = payload.get("media") or []
        self._validate_media_specs(media)
        runtime_request = {
            "provider": provider_name,
            "workflow_id": workflow_id,
            "inputs": inputs,
            "media": media,
            "options": payload.get("options") or {},
            "body": payload.get("body") if provider_name == "AUTODL_COMFYUI" else None,
        }
        request = _redact(runtime_request)
        row = self.store.create({
            "provider": provider_name,
            "workflow_id": workflow_id,
            "request": request,
            "workflow_hash": None,
        })
        thread = threading.Thread(target=self._run_job, args=(row["job_id"],), daemon=True)
        with self._lock:
            self._runtime_requests[row["job_id"]] = copy.deepcopy(runtime_request)
            self._threads[row["job_id"]] = thread
        thread.start()
        return 202, row

    def _validate_media_specs(self, media: Any) -> None:
        if media in (None, [], {}):
            return
        for _slot, spec in self._media_specs(media):
            raw_path = spec["path"]
            expected = spec.get("media_type")
            try:
                self.resolver.resolve(raw_path, expected_type=expected)
            except MediaError as exc:
                raise ApiError(str(exc), 422) from exc

    @staticmethod
    def _media_specs(media: Any) -> list[tuple[str | None, dict[str, Any]]]:
        """Normalize the compact media forms accepted by ``POST /jobs``.

        An object key or an item ``key``/``input`` is an optional workflow
        token name.  After a successful upload its value becomes the uploaded
        ComfyUI filename, so ``{{character_a_image}}`` can be used directly in
        an API workflow.  Plain path entries remain valid for workflows whose
        input does not need a placeholder.
        """
        if isinstance(media, dict):
            source = [(str(key), value) for key, value in media.items()]
        elif isinstance(media, list):
            source = [(None, value) for value in media]
        else:
            raise ApiError("media must be an array or object")

        normalized: list[tuple[str | None, dict[str, Any]]] = []
        for object_key, value in source:
            if isinstance(value, str):
                spec: dict[str, Any] = {"path": value}
            elif isinstance(value, dict):
                spec = dict(value)
            else:
                raise ApiError("each media item needs a path")
            raw_path = spec.get("path")
            if not isinstance(raw_path, str):
                raise ApiError("each media item needs a path")
            slot = spec.get("key") or spec.get("input") or object_key
            if slot is not None:
                if not isinstance(slot, str) or not WORKFLOW_ID_RE.fullmatch(slot):
                    raise ApiError("media key/input must be a safe workflow token name")
            media_type = spec.get("media_type")
            if media_type is not None and media_type not in {"image", "video", "audio", "document"}:
                raise ApiError("media_type must be image, video, audio, or document")
            normalized.append((slot, {"path": raw_path, "media_type": media_type}))
        return normalized

    def _get_job(self, job_id: str) -> tuple[int, dict[str, Any]]:
        row = self.store.get(job_id)
        if row is None:
            raise ApiError("job not found", 404)
        return 200, row

    def _cancel_job(self, job_id: str) -> tuple[int, dict[str, Any]]:
        row = self.store.get(job_id)
        if row is None:
            raise ApiError("job not found", 404)
        if _is_terminal(row.get("status")):
            return 200, row
        provider_name = _provider_name(row.get("provider"))
        if provider_name == "AUTODL_COMFYUI":
            # AutoDL's documented wrapped-workflow API has no task-cancel
            # endpoint.  Do not claim a remote render stopped or abandon
            # polling while it may still incur cloud cost.
            raise ApiError(
                "AutoDL workflow cancellation is not supported by the documented API; remote work may continue",
                409,
            )
        provider = self.provider(provider_name).provider
        prompt_id = row.get("prompt_id")
        if prompt_id:
            client = getattr(provider, "client", None)
            if client is not None:
                try:
                    client.delete_queue(str(prompt_id))
                except Exception:
                    try:
                        client.interrupt()
                    except Exception:
                        pass
        updated = self.store.update(job_id, status="CANCELLED", cancel_requested=True)
        return 200, updated

    def _cancel_requested(self, job_id: str) -> bool:
        row = self.store.get(job_id)
        return bool(row and (row.get("cancel_requested") or row.get("status") == "CANCELLED"))

    def _retry_job(self, job_id: str) -> tuple[int, dict[str, Any]]:
        row = self.store.get(job_id)
        if row is None:
            raise ApiError("job not found", 404)
        if not _is_terminal(row.get("status")):
            raise ApiError("only terminal jobs can be retried", 409)
        request = row.get("request")
        if not isinstance(request, dict):
            raise ApiError("job has no retryable request", 409)
        if _provider_name(row.get("provider")) == "AUTODL_COMFYUI" and _request_requires_resubmission(request):
            raise ApiError(
                "AutoDL request includes redacted URL or sensitive data; resubmit it with the original body",
                409,
            )
        payload = {
            "provider": row.get("provider"),
            "workflow_id": row.get("workflow_id"),
            "inputs": request.get("inputs") or {},
            "media": request.get("media") or [],
            "options": request.get("options") or {},
            "body": request.get("body"),
        }
        status, new_row = self._create_job(payload)
        self.store.update(new_row["job_id"], retry_of=job_id)
        return status, self.store.get(new_row["job_id"]) or new_row

    def _run_job(self, job_id: str) -> None:
        row = self.store.get(job_id)
        if not row:
            return
        if self._cancel_requested(job_id):
            return
        provider_name = _provider_name(row.get("provider"))
        try:
            self.store.update(job_id, status="RUNNING")
            with self._lock:
                runtime_request = self._runtime_requests.get(job_id)
            if runtime_request is not None:
                request = runtime_request
            else:
                request = row.get("request") if isinstance(row.get("request"), dict) else {}
                if provider_name == "AUTODL_COMFYUI" and _request_requires_resubmission(request):
                    self.store.update(
                        job_id,
                        status="NEEDS_REVIEW",
                        error="AutoDL request data was redacted after restart; resubmit with the original body",
                    )
                    return
            provider = self.provider(provider_name).provider
            if provider_name == "AUTODL_COMFYUI":
                self._run_autodl(job_id, provider, row, request)
            else:
                self._run_local(job_id, provider, row, request)
        except Exception as exc:
            # A user cancellation wins a late provider/network exception; do
            # not turn an intentional CANCELLED result into FAILED.
            current = self.store.get(job_id) or {}
            if not current.get("cancel_requested") and current.get("status") != "CANCELLED":
                self.store.update(job_id, status="FAILED", error=_redact(str(exc))[:1000])
        finally:
            with self._lock:
                self._threads.pop(job_id, None)
                self._runtime_requests.pop(job_id, None)

    def _run_autodl(self, job_id: str, provider: Any, row: dict[str, Any], request: dict[str, Any]) -> None:
        if self._cancel_requested(job_id):
            return
        if not self.settings.autodl_allow_paid_submit:
            self.store.update(
                job_id,
                status="NEEDS_REVIEW",
                error="AutoDL paid submission is disabled before provider execution",
            )
            return
        body = request.get("body")
        if not isinstance(body, dict):
            self.store.update(
                job_id,
                status="NEEDS_REVIEW",
                error="AutoDL request body is missing or not a JSON object; no vendor call was made",
            )
            return
        # Keep the vendor envelope exact; never leak internal provider/job/media
        # control fields into a wrapped workflow request.
        body = copy.deepcopy(body)
        result = provider.submit(str(row["workflow_id"]), body)
        task_id = result.get("task_id") if isinstance(result, dict) else None
        if not task_id:
            raise ApiError("AutoDL response has no task_id", 502)
        self.store.update(job_id, task_id=str(task_id), provider_result=_redact(result))
        client = getattr(provider, "client", None)
        if client is None or not hasattr(client, "wait"):
            self.store.update(job_id, status="NEEDS_REVIEW", error="AutoDL provider has no result polling client")
            return
        last: dict[str, Any] = {}
        timeout_seconds = self.settings.autodl_poll_timeout_seconds
        for last in client.wait(
            str(task_id), self.settings.poll_interval_seconds, timeout=timeout_seconds
        ):
            if self._cancel_requested(job_id):
                return
            self.store.update(job_id, progress=_safe_metadata(last))
            status = str(last.get("status", "")).upper()
            if status in {"FAILED", "CANCELLED", "CANCELED"}:
                stored_status = "CANCELLED" if status == "CANCELED" else status
                self.store.update(job_id, status=stored_status, provider_result=_safe_metadata(last))
                return
            if status == "SUCCESS":
                self._complete_autodl_success(client, job_id, last)
                return
        if last and str(last.get("status", "")).upper() == "SUCCESS":
            self._complete_autodl_success(client, job_id, last)
        elif not _is_terminal((self.store.get(job_id) or {}).get("status")):
            self.store.update(
                job_id,
                status="NEEDS_REVIEW",
                provider_result=_safe_metadata(last),
                poll_timed_out=True,
                poll_timeout_seconds=timeout_seconds,
                remote_may_continue=True,
                error=(
                    "AutoDL polling reached its deadline; the remote task may still be running "
                    "and cannot be assumed cancelled or safely retried"
                ),
            )

    def _complete_autodl_success(self, client: Any, job_id: str, result: dict[str, Any]) -> None:
        artifacts, errors = self._download_autodl_outputs(client, job_id, result)
        if not artifacts and not errors:
            errors.append("AutoDL reported SUCCESS without downloadable HTTP(S) result URLs")
        changes: dict[str, Any] = {"provider_result": _safe_metadata(result)}
        if artifacts:
            changes["artifacts"] = artifacts
        if errors:
            changes.update({"status": "NEEDS_REVIEW", "artifact_errors": errors})
        else:
            changes["status"] = "SUCCEEDED"
        self.store.update(job_id, **changes)

    def _run_local(self, job_id: str, provider: Any, row: dict[str, Any], request: dict[str, Any]) -> None:
        if self._cancel_requested(job_id):
            return
        workflow_id = str(row["workflow_id"])
        workflow = self.registry.get(workflow_id)
        graph = workflow.get("prompt") if isinstance(workflow.get("prompt"), dict) else workflow
        if not isinstance(graph, dict):
            raise WorkflowError("workflow prompt graph must be an object")
        # Upload before substitution: an image/video item with key
        # ``character_a_image`` supplies the value for
        # ``{{character_a_image}}`` in the API workflow.
        uploaded, media_inputs = self._upload_media(provider, request.get("media"))
        if uploaded:
            self.store.update(job_id, uploaded_media=_redact(uploaded))
        inputs = dict(request.get("inputs") or {}) if isinstance(request.get("inputs"), dict) else {}
        for key, value in media_inputs.items():
            if key in inputs and inputs[key] != value:
                raise ApiError(f"media input conflicts with inputs.{key}")
            inputs[key] = value
        graph = substitute_workflow(graph, inputs)
        row_hash = workflow_hash(graph)
        self.store.update(job_id, workflow_hash=row_hash)
        result = provider.submit(graph)
        prompt_id = result.get("prompt_id") if isinstance(result, dict) else None
        if prompt_id:
            self.store.update(job_id, prompt_id=str(prompt_id), provider_result=_redact(result))
        client = getattr(provider, "client", None)
        if not prompt_id or client is None or not hasattr(client, "iter_progress"):
            self.store.update(job_id, status="NEEDS_REVIEW", provider_result=_redact(result),
                              error="ComfyUI returned no progress client; output was not verified")
            return
        finished = False
        for event in client.iter_progress(str(prompt_id), self.settings.poll_interval_seconds):
            if self._cancel_requested(job_id):
                return
            self.store.update(job_id, progress=_safe_metadata(event))
            kind = event.get("type") if isinstance(event, dict) else None
            if kind == "execution_error":
                self.store.update(job_id, status="FAILED", error="ComfyUI execution error", provider_result=_safe_metadata(event))
                return
            if kind == "history" and self._history_finished(event):
                entry = event.get("entry")
                self._complete_local_history(client, job_id, entry)
                return
            if kind == "executing" and event.get("node") is None:
                finished = True
        if finished and not _is_terminal((self.store.get(job_id) or {}).get("status")):
            # A websocket completion event may arrive before history.  Fetch
            # history once more so output files are mirrored before claiming
            # success.
            try:
                history = client.history(str(prompt_id))
                entry = history.get(str(prompt_id)) if isinstance(history, dict) else None
                self._complete_local_history(client, job_id, entry)
            except Exception as exc:
                self.store.update(job_id, status="NEEDS_REVIEW", artifact_errors=[_redact(str(exc))[:500]])
        elif not _is_terminal((self.store.get(job_id) or {}).get("status")):
            self.store.update(job_id, status="NEEDS_REVIEW")

    def _upload_media(self, provider: Any, media: Any) -> tuple[list[dict[str, Any]], dict[str, str]]:
        if not media:
            return [], {}
        client = getattr(provider, "client", None)
        if client is None or not hasattr(client, "upload_file"):
            raise ApiError("selected provider does not support local media uploads", 503)
        uploaded: list[dict[str, Any]] = []
        token_values: dict[str, str] = {}
        for slot, spec in self._media_specs(media):
            ref = self.resolver.resolve(spec["path"], expected_type=spec.get("media_type"))
            # ComfyUI's standard /upload/image endpoint uses the multipart
            # field name ``image`` for all supported input asset types.
            result = client.upload_file(ref.path, field_name="image", upload_type="input", overwrite=True)
            filename = self._uploaded_filename(result, ref.path.name)
            if slot:
                if slot in token_values:
                    raise ApiError(f"duplicate media input: {slot}")
                token_values[slot] = filename
            uploaded.append({
                "input": slot,
                "path": str(ref.path),
                "filename": filename,
                "media_type": ref.media_type,
                "size_bytes": ref.size_bytes,
                "sha256": ref.sha256,
                "response": _redact(result),
            })
        return uploaded, token_values

    @staticmethod
    def _history_finished(event: dict[str, Any]) -> bool:
        if event.get("completed"):
            return True
        entry = event.get("entry")
        if not isinstance(entry, dict):
            return False
        status = entry.get("status") if isinstance(entry.get("status"), dict) else {}
        status_str = str(status.get("status_str", "")).strip().lower()
        return bool(entry.get("outputs")) or status_str in {"success", "error", "failed", "cancelled", "canceled"}

    def _complete_local_history(self, client: Any, job_id: str, entry: Any) -> None:
        if not isinstance(entry, dict):
            self.store.update(job_id, status="NEEDS_REVIEW", error="ComfyUI completed without a history entry")
            return
        status = entry.get("status") if isinstance(entry.get("status"), dict) else {}
        status_str = str(status.get("status_str", "")).strip().lower()
        history_metadata = _safe_metadata(entry)
        if status_str in {"error", "failed"}:
            self.store.update(
                job_id,
                status="FAILED",
                error="ComfyUI history reported execution failure",
                provider_result=history_metadata,
            )
            return
        if status_str in {"cancelled", "canceled"}:
            self.store.update(job_id, status="CANCELLED", provider_result=history_metadata)
            return
        outputs = entry.get("outputs", {})
        artifacts, errors = self._mirror_local_outputs(client, job_id, outputs)
        changes: dict[str, Any] = {"outputs": _safe_metadata(outputs), "provider_result": history_metadata}
        if artifacts:
            changes["artifacts"] = artifacts
        if not artifacts and not errors:
            errors.append("ComfyUI completed without downloadable output files")
        if errors:
            changes.update({"status": "NEEDS_REVIEW", "artifact_errors": errors})
        else:
            changes["status"] = "SUCCEEDED"
        self.store.update(job_id, **changes)

    def _artifact_dir(self, job_id: str, *, create: bool = True) -> Path:
        if not re.fullmatch(r"[A-Za-z0-9_-]+", job_id):
            raise ApiError("invalid job id", 400)
        target = (self.settings.job_store.parent / "artifacts" / job_id).resolve()
        if create:
            target.mkdir(parents=True, exist_ok=True)
        return target

    @staticmethod
    def _artifact_record(job_id: str, path: Path, *, source: str, content_type: str | None = None) -> dict[str, Any]:
        size, digest = _sha256_file(path)
        return {
            "name": path.name,
            "source": source,
            "size_bytes": size,
            "sha256": digest,
            "content_type": content_type or mimetypes.guess_type(path.name)[0] or "application/octet-stream",
            "url": f"/api/comfyui/jobs/{job_id}/outputs/{quote(path.name, safe='._-')}",
        }

    def _mirror_local_outputs(self, client: Any, job_id: str, outputs: Any) -> tuple[list[dict[str, Any]], list[str]]:
        artifacts: list[dict[str, Any]] = []
        errors: list[str] = []
        if not isinstance(outputs, dict):
            return artifacts, errors
        artifact_dir = self._artifact_dir(job_id)
        seen: set[tuple[str, str, str]] = set()
        for node_id, node_output in outputs.items():
            if not isinstance(node_output, dict):
                continue
            for output_key in ("gifs", "images", "videos", "audio"):
                entries = node_output.get(output_key)
                if not isinstance(entries, list):
                    continue
                for index, item in enumerate(entries):
                    if not isinstance(item, dict):
                        continue
                    filename = _safe_provider_path(item.get("filename"))
                    subfolder = _safe_provider_path(item.get("subfolder")) or ""
                    file_type = _safe_provider_path(item.get("type")) or "output"
                    if not filename:
                        errors.append(f"node {node_id} {output_key}[{index}] has no safe filename")
                        continue
                    marker = (filename, subfolder, file_type)
                    if marker in seen:
                        continue
                    seen.add(marker)
                    target_name = _safe_artifact_name(filename)
                    target = artifact_dir / target_name
                    suffix = 1
                    while target.exists():
                        target = artifact_dir / f"{Path(target_name).stem}_{suffix}{Path(target_name).suffix}"
                        suffix += 1
                    try:
                        client.download_view(filename, subfolder=subfolder, file_type=file_type, destination=target)
                        artifacts.append(self._artifact_record(job_id, target, source=f"node:{node_id}/{output_key}"))
                    except Exception as exc:
                        errors.append(f"{filename}: {_redact(str(exc))[:240]}")
        return artifacts, errors

    def _download_autodl_outputs(self, client: Any, job_id: str, result: Any) -> tuple[list[dict[str, Any]], list[str]]:
        artifacts: list[dict[str, Any]] = []
        errors: list[str] = []
        # AutoDL documents generated files under ``data.results``.  Do not
        # walk arbitrary response metadata: it can echo input-media URLs.
        results = result.get("results", []) if isinstance(result, dict) else []
        urls = _collect_http_urls(results)
        if not urls:
            return artifacts, errors
        artifact_dir = self._artifact_dir(job_id)
        used: set[str] = set()
        for index, url in enumerate(urls):
            parsed = urlsplit(url)
            candidate = _safe_artifact_name(Path(parsed.path).name, f"result_{index + 1}.bin")
            if candidate in used:
                stem, suffix = Path(candidate).stem, Path(candidate).suffix
                candidate = f"{stem}_{index + 1}{suffix}"
            used.add(candidate)
            target = artifact_dir / candidate
            try:
                client.download_result(url, target)
                artifacts.append(self._artifact_record(job_id, target, source="autodl_result"))
            except Exception as exc:
                errors.append(f"result_{index + 1}: {_redact(str(exc))[:240]}")
        return artifacts, errors

    def resolve_output(self, job_id: str, filename: str) -> tuple[Path, str]:
        row = self.store.get(job_id)
        if row is None:
            raise ApiError("job not found", 404)
        if not isinstance(filename, str) or not filename:
            raise ApiError("invalid output filename", 400)
        decoded_name = unquote(filename)
        # Decode exactly once, then reject all path syntax.  Artifacts are
        # deliberately flattened to safe ASCII names when they are mirrored.
        if "/" in decoded_name or "\\" in decoded_name or decoded_name in {".", ".."}:
            raise ApiError("invalid output filename", 400)
        safe_name = _safe_artifact_name(decoded_name)
        if decoded_name != safe_name:
            raise ApiError("invalid output filename", 400)
        artifacts = row.get("artifacts") if isinstance(row.get("artifacts"), list) else []
        names = {item.get("name") for item in artifacts if isinstance(item, dict)}
        if safe_name not in names:
            raise ApiError("output not found", 404)
        artifact_dir = self._artifact_dir(job_id, create=False)
        target = (artifact_dir / safe_name).resolve()
        if target.parent != artifact_dir or not target.is_file():
            raise ApiError("output not found", 404)
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        return target, content_type

    def read_output(self, job_id: str, filename: str) -> tuple[int, bytes, str]:
        """Compatibility helper for in-process callers; HTTP streams files."""
        target, content_type = self.resolve_output(job_id, filename)
        return 200, target.read_bytes(), content_type

    @staticmethod
    def _uploaded_filename(response: Any, fallback: str) -> str:
        if not isinstance(response, dict):
            return fallback
        name = response.get("name") or response.get("filename") or fallback
        subfolder = response.get("subfolder") or ""
        if not isinstance(name, str) or not isinstance(subfolder, str):
            raise ApiError("ComfyUI upload response has an invalid filename", 502)
        name = name.replace("\\", "/").strip("/")
        subfolder = subfolder.replace("\\", "/").strip("/")
        segments = [part for part in (subfolder.split("/") + name.split("/")) if part]
        if not segments or any(part in {".", ".."} for part in segments):
            raise ApiError("ComfyUI upload response has an unsafe filename", 502)
        return "/".join(segments)


class _JsonHandler(BaseHTTPRequestHandler):
    server: "ApiHTTPServer"

    def do_GET(self) -> None:  # noqa: N802
        output_match = OUTPUT_PATH_RE.match(urlsplit(self.path).path)
        if output_match:
            self._send_output(*output_match.groups())
            return
        self._handle("GET")

    def do_POST(self) -> None:  # noqa: N802
        self._handle("POST")

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self._send_cors()
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _handle(self, method: str) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            max_bytes = self.server.app.settings.max_upload_mb * 1024 * 1024
            if length > max_bytes:
                raise ApiError("request body is too large", 413)
            payload = None
            if method == "POST" and length:
                raw = self.rfile.read(length)
                try:
                    payload = json.loads(raw.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise ApiError("request body must be valid JSON") from exc
            status, body = self.server.app.dispatch(method, self.path, payload)
        except ApiError as exc:
            status, body = exc.status, {"error": str(exc)}
        except Exception as exc:  # keep internal details bounded and JSON-safe
            status, body = 500, {"error": "internal server error", "detail": _redact(str(exc))[:500]}
        self._send_json(status, body)

    def _send_json(self, status: int, body: dict[str, Any]) -> None:
        raw = _json_bytes(body)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self._send_cors()
        self.end_headers()
        self.wfile.write(raw)

    def _send_output(self, job_id: str, filename: str) -> None:
        try:
            target, content_type = self.server.app.resolve_output(job_id, filename)
            size = target.stat().st_size
        except ApiError as exc:
            self._send_json(exc.status, {"error": str(exc)})
            return
        except Exception as exc:
            self._send_json(500, {"error": "internal server error", "detail": _redact(str(exc))[:500]})
            return

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(size))
        self.send_header("Content-Disposition", f'attachment; filename="{target.name}"')
        self.send_header("Cache-Control", "private, no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self._send_cors()
        self.end_headers()
        try:
            with target.open("rb") as handle:
                for block in iter(lambda: handle.read(1024 * 1024), b""):
                    self.wfile.write(block)
        except (BrokenPipeError, ConnectionResetError):
            return

    def _send_cors(self) -> None:
        origin = self.headers.get("Origin", "")
        if origin:
            parsed = urlsplit(origin)
            if parsed.scheme in {"http", "https"} and parsed.hostname in LOOPBACK_HOSTS:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")
                return
        # Same-origin callers do not require the header; a conservative local
        # default keeps simple file/localhost integrations working.
        self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1")

    def log_message(self, fmt: str, *args: Any) -> None:
        # Avoid writing request bodies or Authorization values to the console.
        return


class ApiHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    # Windows treats SO_REUSEADDR differently from Unix and can permit
    # multiple Python processes to bind the same loopback API port.
    allow_reuse_address = False

    def server_bind(self) -> None:
        exclusive = getattr(socket, "SO_EXCLUSIVEADDRUSE", None)
        if exclusive is not None:
            self.socket.setsockopt(socket.SOL_SOCKET, exclusive, 1)
        super().server_bind()

    def __init__(self, address: tuple[str, int], app: ApiApplication):
        host, _ = address
        if host not in LOOPBACK_HOSTS:
            raise ValueError("local API must bind to a loopback host (127.0.0.1 or localhost)")
        self.app = app
        super().__init__(address, _JsonHandler)


def create_server(settings: Settings | None = None, **kwargs: Any) -> ApiHTTPServer:
    app = ApiApplication(settings, **kwargs)
    if app.settings.api_host not in LOOPBACK_HOSTS:
        raise ValueError("COMFY_API_HOST must be loopback-only")
    return ApiHTTPServer((app.settings.api_host, app.settings.api_port), app)


def serve(settings: Settings | None = None) -> None:
    server = create_server(settings)
    print(f"ComfyUI production API listening on http://{server.server_address[0]}:{server.server_address[1]}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def _query_limit(query: str) -> int:
    try:
        return max(1, min(500, int(parse_qs(query).get("limit", [100])[0])))
    except (TypeError, ValueError):
        return 100


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Loopback-only ComfyUI production API")
    parser.add_argument("--host", default=None, help="loopback host override")
    parser.add_argument("--port", type=int, default=None, help="port override")
    args = parser.parse_args(argv)
    settings = Settings.from_env()
    if args.host is not None or args.port is not None:
        values = settings.__dict__.copy()
        if args.host is not None:
            values["api_host"] = args.host
        if args.port is not None:
            values["api_port"] = args.port
        settings = Settings(**values)
    serve(settings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
