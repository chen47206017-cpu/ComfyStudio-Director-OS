"""Production Core helpers for ComfyStudio StudioOS.

This module deliberately keeps the data contract small and dependency-light.  The
Flask routes in :mod:`app` use it for every new V10 operation and for the legacy
V8 compatibility endpoints.  Paths are resolved from this file instead of the
process working directory so starting the server from another drive is safe.
"""

from __future__ import annotations

import json
import hashlib
import mimetypes
import os
import re
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

from config.paths import resolve_studio_paths

BACKEND_DIR = Path(__file__).resolve().parent
STUDIO_PATHS = resolve_studio_paths(BACKEND_DIR)
ROOT = STUDIO_PATHS.app_root
DB = STUDIO_PATHS.database_dir
UI = STUDIO_PATHS.ui_dir
V8_DB = DB / "v8"
COMFY_URL = os.environ.get("COMFYSTUDIO_COMFY_URL", "http://127.0.0.1:8189").rstrip("/")
try:
    BEIJING = ZoneInfo("Asia/Shanghai")
except Exception:  # Windows Python may not ship tzdata; UTC+8 is fixed for this domain.
    BEIJING = timezone(timedelta(hours=8), name="Asia/Shanghai")


def now_beijing() -> str:
    return datetime.now(timezone.utc).astimezone(BEIJING).isoformat(timespec="seconds")


def _configured_path(name: str, default: Path) -> Path:
    value = os.environ.get(name)
    if not value:
        return default
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


CANVAS_PATH = _configured_path("COMFYSTUDIO_CANVAS_FILE", DB / "canvas.json")
MEMORY_PATH = _configured_path("COMFYSTUDIO_MEMORY_FILE", DB / "memory" / "memory.json")


def read_json(path: str | Path, default: Any = None) -> Any:
    """Read JSON with UTF-8 BOM support.

    Missing files return ``default``.  Invalid JSON is surfaced to callers: a
    corrupted production file should not be silently replaced with empty data.
    """

    target = Path(path)
    if not target.exists():
        return default
    with target.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def atomic_write_json(path: str | Path, value: Any) -> None:
    """Write JSON through a same-directory temporary file and atomic replace."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=str(target.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load_database(name: str, default: Any = None) -> Any:
    """Load a top-level database document without relying on cwd."""

    return read_json(DB / name, default)


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _flatten_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, Mapping):
        return " ".join(_flatten_text(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return " ".join(_flatten_text(item) for item in value)
    return str(value)


DEFAULT_CANVAS: dict[str, Any] = {
    "schema": "comfystudio.canvas.v10",
    "revision": 0,
    "nodes": [],
    "edges": [],
}


class CanvasConflict(RuntimeError):
    """Raised when a canvas write uses a stale revision."""

    def __init__(self, current: Mapping[str, Any]):
        super().__init__("canvas revision conflict")
        self.current = dict(current)


def normalize_canvas(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping) and isinstance(value.get("canvas"), Mapping):
        value = value["canvas"]
    if not isinstance(value, Mapping):
        value = {}
    result = dict(DEFAULT_CANVAS)
    result.update(dict(value))
    result["schema"] = str(result.get("schema") or DEFAULT_CANVAS["schema"])
    try:
        result["revision"] = max(0, int(result.get("revision", 0)))
    except (TypeError, ValueError):
        result["revision"] = 0
    result["nodes"] = list(result.get("nodes") or [])
    result["edges"] = list(result.get("edges") or [])
    return result


def load_canvas() -> dict[str, Any]:
    data = read_json(CANVAS_PATH, None)
    if data is None and CANVAS_PATH == DB / "canvas.json":
        # A prior V8 build stored the canvas in database/v8.  Read it only as a
        # fallback; new writes always use the stable top-level path.
        data = read_json(V8_DB / "canvas.json", None)
    return normalize_canvas(data)


def save_canvas(value: Any, expected_revision: int | None = None) -> dict[str, Any]:
    current = load_canvas()
    if expected_revision is not None and int(expected_revision) != int(current["revision"]):
        raise CanvasConflict(current)
    incoming = normalize_canvas(value)
    incoming["revision"] = int(current["revision"]) + 1
    incoming["updated_at"] = now_beijing()
    atomic_write_json(CANVAS_PATH, incoming)
    return incoming


def _tokens(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def canon_check(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Evaluate deterministic production Canon rules from database/canon.json."""

    body: dict[str, Any] = dict(payload or {})
    shot = body.get("shot") if isinstance(body.get("shot"), Mapping) else body
    shot = dict(shot or {})
    canon_doc = body.get("canon") if isinstance(body.get("canon"), Mapping) else load_database("canon.json", {})
    rules = canon_doc.get("rules", []) if isinstance(canon_doc, Mapping) else []
    raw_text = _tokens(_flatten_text(body))
    year = shot.get("year") or shot.get("era") or body.get("year") or body.get("era")
    year_match = re.search(r"(?:19|20)\d{2}", str(year or ""))
    year_text = year_match.group(0) if year_match else ""
    props_value = shot.get("props") or shot.get("props_required") or body.get("props")
    props_text = _tokens(_flatten_text(props_value))
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    def violation(rule_id: str, message: str) -> None:
        errors.append({"rule_id": rule_id, "message": message})

    if year_text == "2006":
        modern_terms = ("smartphone", "智能手机", "现代手机", "iphone", "安卓", "led灯", "led", "现代家具")
        if any(term in raw_text or term in props_text for term in modern_terms):
            violation("ERA_001", "2006禁止现代智能手机、LED灯、现代家具")
        if ("苏晚晴25岁" in raw_text or "25岁" in raw_text) and (
            "char_sw45" in raw_text or "苏晚晴45岁" in raw_text or "45岁造型" in raw_text
        ):
            violation("AGE_001", "25岁苏晚晴禁止使用45岁造型")
        requires_phone = bool(
            shot.get("requires_phone")
            or shot.get("phone_required")
            or any(term in props_text for term in ("phone", "电话", "座机", "telephone"))
        )
        if requires_phone:
            canonical_phone = any(token in props_text for token in ("prop_phone_2006", "phone2006"))
            if not canonical_phone and "米黄色" not in raw_text and "有线" not in raw_text:
                violation("PROP_001", "2006必须使用米黄色有线座机")

    # Explicitly supplied error lists remain useful to clients and are treated as
    # blocking findings rather than discarded.
    for item in _listify(shot.get("canon_errors") or body.get("canon_errors")):
        if item:
            violation("CLIENT", str(item))

    return {
        "pass": not errors,
        "allowed": not errors,
        "blocked": bool(errors),
        "errors": errors,
        "warnings": warnings,
        "rules_checked": [rule.get("id") for rule in rules if isinstance(rule, Mapping) and rule.get("id")],
    }


DEFAULT_NEGATIVE = [
    "年龄错误",
    "脸部漂移",
    "年代错误",
    "现代设备",
    "服装错误",
    "道具错误",
    "画面闪烁",
]

DEFAULT_NEGATIVE_CATEGORIES = {
    "canon": ["年龄错误", "年代错误", "现代设备", "服装错误", "道具错误"],
    "identity": ["脸部漂移"],
    "quality": ["画面闪烁"],
}


def _unique_text(items: Iterable[Any]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = _flatten_text(item).strip()
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result


def compile_prompt(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    body: dict[str, Any] = dict(payload or {})
    shot = body.get("shot") if isinstance(body.get("shot"), Mapping) else body
    shot = dict(shot or {})
    assets = body.get("assets")
    if assets is None:
        assets = body.get("asset")
    canon = body.get("canon") if isinstance(body.get("canon"), Mapping) else load_database("canon.json", {})
    memory = body.get("memory")
    references = body.get("references")
    if references is None:
        references = shot.get("references") or body.get("reference_list") or []

    positive_parts: list[Any] = [
        "电影级真人写实短剧",
        shot.get("description"),
        shot.get("scene"),
        shot.get("action"),
        shot.get("camera"),
        shot.get("lighting"),
        shot.get("character"),
        shot.get("characters"),
    ]
    for asset in _listify(assets):
        positive_parts.append(asset.get("name") if isinstance(asset, Mapping) else asset)
        if isinstance(asset, Mapping):
            positive_parts.append(asset.get("description"))
            positive_parts.append(asset.get("lock"))
    if isinstance(canon, Mapping):
        # Canon constraints are gates/negative context, never positive prompt text.
        positive_parts.append(canon.get("era"))
        positive_parts.append(canon.get("period"))
    positive_parts.append(memory.get("director_preference") if isinstance(memory, Mapping) else memory)
    if isinstance(memory, Mapping):
        positive_parts.extend(_listify(memory.get("successful_prompts") or memory.get("prompts")))
    positive_parts.extend(_listify(body.get("positive")))

    negative_categories: dict[str, list[str]] = {
        key: list(values) for key, values in DEFAULT_NEGATIVE_CATEGORIES.items()
    }
    negative_parts: list[Any] = list(DEFAULT_NEGATIVE)
    user_negative = _listify(body.get("negative"))
    negative_categories["user"] = _unique_text(user_negative)
    negative_parts.extend(user_negative)
    if isinstance(memory, Mapping):
        memory_negative = _listify(memory.get("negative"))
        negative_categories["memory"] = _unique_text(memory_negative)
        negative_parts.extend(memory_negative)

    if isinstance(canon, Mapping):
        canon_rules = [
            rule.get("rule")
            for rule in _listify(canon.get("rules"))
            if isinstance(rule, Mapping) and rule.get("rule")
        ]
        negative_categories["canon"] = _unique_text([*negative_categories["canon"], *canon_rules])
        negative_parts.extend(canon_rules)

    gate = canon_check(body)
    canon_findings = [item.get("message") for item in gate.get("errors", []) if isinstance(item, Mapping)]
    if canon_findings:
        negative_categories["canon"] = _unique_text([*negative_categories["canon"], *canon_findings])

    reference_list = references if isinstance(references, (list, dict)) else [references]
    return {
        "positive": "，".join(_unique_text(positive_parts)),
        "negative": "，".join(_unique_text(negative_parts)),
        "negative_categories": {
            key: _unique_text(values) for key, values in negative_categories.items() if values
        },
        "references": reference_list,
        "reference_list": reference_list,
        "shot_id": shot.get("id"),
        "model": shot.get("model") or body.get("model"),
        "canon_gate": gate,
    }


class ComfyClient:
    """Small HTTP client for the local ComfyUI API with graceful offline errors."""

    def __init__(self, base_url: str = COMFY_URL, timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _request(self, method: str, path: str, payload: Any = None, timeout: float | None = None) -> dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            import requests

            response = requests.request(method, url, json=payload, timeout=timeout or self.timeout)
            content_type = response.headers.get("content-type", "")
            if response.text:
                try:
                    data = response.json()
                except ValueError:
                    data = {"text": response.text}
            else:
                data = {}
            if not isinstance(data, Mapping):
                data = {"data": data}
            return {"connected": response.ok, "status": response.status_code, **dict(data)}
        except Exception as exc:  # network unavailable is a valid local state
            return {"connected": False, "status": None, "error": str(exc), "url": url}

    def health(self) -> dict[str, Any]:
        result = self._request("GET", "/system_stats")
        result["url"] = self.base_url
        return result

    def probe(self) -> dict[str, Any]:
        health = self.health()
        info = self.object_info() if health.get("connected") else {"connected": False}
        return {"health": health, "object_info": info, "connected": bool(health.get("connected") and info.get("connected"))}

    def object_info(self) -> dict[str, Any]:
        return self._request("GET", "/object_info")

    def queue(self) -> dict[str, Any]:
        return self._request("GET", "/queue")

    def history(self, prompt_id: str | None = None) -> dict[str, Any]:
        suffix = f"/{prompt_id}" if prompt_id else ""
        return self._request("GET", f"/history{suffix}")

    def upload_input(self, path: str | Path, subfolder: str = "studioos", image_type: str = "input") -> dict[str, Any]:
        """Upload a local input without mutating the source asset."""
        source = Path(path)
        if not source.is_file():
            return {"uploaded": False, "error": "input_not_found", "path": str(source)}
        try:
            import requests

            with source.open("rb") as handle:
                response = requests.post(
                    f"{self.base_url}/upload/image",
                    files={"image": (source.name, handle, mimetypes.guess_type(source.name)[0] or "application/octet-stream")},
                    data={"subfolder": subfolder, "type": image_type, "overwrite": "false"},
                    timeout=self.timeout,
                )
            try:
                body = response.json()
            except ValueError:
                body = {"text": response.text}
            if not isinstance(body, Mapping):
                body = {"data": body}
            return {"uploaded": response.ok, "connected": True, "status": response.status_code, "source_path": str(source), **dict(body)}
        except Exception as exc:
            return {"uploaded": False, "connected": False, "error": str(exc), "source_path": str(source)}

    def submit(self, workflow: Any, client_id: str | None = None, dry_run: bool = False) -> dict[str, Any]:
        if dry_run:
            return {"submitted": False, "dry_run": True, "prompt": workflow}
        payload = workflow if isinstance(workflow, Mapping) else {"prompt": workflow}
        if "prompt" not in payload:
            payload = {"prompt": payload}
        if client_id:
            payload = dict(payload)
            payload["client_id"] = client_id
        result = self._request("POST", "/prompt", payload)
        result.setdefault("submitted", bool(result.get("connected") and result.get("status", 500) < 300))
        result["prompt_id"] = result.get("prompt_id") or result.get("promptId")
        if result.get("node_errors"):
            result["submitted"] = False
        return result

    @staticmethod
    def _history_records(history: Mapping[str, Any]) -> list[Mapping[str, Any]]:
        raw = history.get("history") if isinstance(history, Mapping) else None
        if isinstance(raw, Mapping):
            return [item for item in raw.values() if isinstance(item, Mapping)]
        if isinstance(history, Mapping) and "outputs" in history:
            return [history]
        return []

    def collect_output_descriptors(self, history: Mapping[str, Any]) -> list[dict[str, Any]]:
        """Extract Comfy output metadata from both /history response shapes."""
        found: list[dict[str, Any]] = []
        for record in self._history_records(history):
            outputs = record.get("outputs")
            if not isinstance(outputs, Mapping):
                continue
            for node_id, node_output in outputs.items():
                if not isinstance(node_output, Mapping):
                    continue
                for field in ("gifs", "videos", "images", "audio"):
                    values = node_output.get(field) or []
                    if isinstance(values, Mapping):
                        values = [values]
                    for item in values:
                        if not isinstance(item, Mapping) or not item.get("filename"):
                            continue
                        found.append({"node_id": str(node_id), "kind": field, **dict(item)})
        return found

    def download_output(self, descriptor: Mapping[str, Any], destination_dir: str | Path) -> dict[str, Any]:
        """Download one output without treating transport success as media proof.

        ComfyUI can legitimately expose preview images, audio, or an HTML error
        body through the same endpoint.  Strict MP4/container validation happens
        in ``services.output_validation`` after this copy is inside StudioOS's
        controlled output directory.
        """
        filename = str(descriptor.get("filename") or "")
        if not filename:
            return {"verified": False, "error": "output_filename_missing"}
        query = urlencode({
            "filename": filename,
            "subfolder": str(descriptor.get("subfolder") or ""),
            "type": str(descriptor.get("type") or "output"),
        })
        target_dir = Path(destination_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        safe_name = Path(filename).name
        target = target_dir / safe_name
        temporary = target.with_suffix(target.suffix + ".part")
        url = f"{self.base_url}/view?{query}"
        try:
            import requests

            response = requests.get(url, timeout=max(self.timeout, 15.0))
            response.raise_for_status()
            temporary.write_bytes(response.content)
            size = temporary.stat().st_size
            if size <= 0:
                temporary.unlink(missing_ok=True)
                return {"verified": False, "error": "output_empty", "url": url}
            os.replace(temporary, target)
            mime = response.headers.get("content-type") or mimetypes.guess_type(target.name)[0] or "application/octet-stream"
            return {
                "downloaded": True,
                "verified": False,
                "path": str(target),
                "filename": filename,
                "mime": mime,
                "size": size,
                "url": url,
            }
        except Exception as exc:
            if temporary.exists():
                temporary.unlink(missing_ok=True)
            return {"downloaded": False, "verified": False, "error": str(exc), "url": url}

    def collect_outputs(self, history: Mapping[str, Any], destination_dir: str | Path) -> list[dict[str, Any]]:
        return [self.download_output(item, destination_dir) for item in self.collect_output_descriptors(history)]

    def wait_for_result(self, prompt_id: str, timeout: float = 30.0, interval: float = 1.0) -> dict[str, Any]:
        """Poll history; timeout is reported as UNKNOWN rather than FAILED."""
        import time

        deadline = time.monotonic() + max(0.1, timeout)
        last: dict[str, Any] = {"connected": False, "prompt_id": prompt_id}
        while time.monotonic() < deadline:
            last = self.history(prompt_id)
            records = self._history_records(last)
            if records:
                return {"status": "COMPLETED", "prompt_id": prompt_id, "history": last}
            if not last.get("connected"):
                return {"status": "UNKNOWN", "prompt_id": prompt_id, "history": last}
            time.sleep(max(0.05, interval))
        return {"status": "UNKNOWN", "prompt_id": prompt_id, "history": last, "reason_code": "HISTORY_TIMEOUT"}

    def cancel(self, prompt_id: str | None = None) -> dict[str, Any]:
        result = self._request("POST", "/interrupt", {"prompt_id": prompt_id} if prompt_id else {})
        result["cancelled"] = bool(result.get("connected") and result.get("status", 500) < 300)
        return result


def parse_script(text: str, episode: str = "E01") -> dict[str, Any]:
    """Parse plain text/Markdown into deterministic scenes and shot records."""

    scenes: list[dict[str, Any]] = []
    shots: list[dict[str, Any]] = []
    current_scene: dict[str, Any] | None = None
    shot_index = 1
    for raw in str(text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        is_scene = bool(re.match(r"^(#{1,6}\s+|场景\s*[:：]|INT\.?\s|EXT\.?\s)", line, re.I))
        if is_scene:
            current_scene = {"id": f"{episode}_SCENE{len(scenes) + 1:03}", "title": re.sub(r"^#+\s*", "", line), "shots": []}
            scenes.append(current_scene)
            continue
        shot = {
            "id": f"{episode}_SHOT{shot_index:03}",
            "episode": episode,
            "scene_id": current_scene["id"] if current_scene else None,
            "description": line,
            "status": "WAITING",
        }
        shots.append(shot)
        if current_scene is not None:
            current_scene["shots"].append(shot["id"])
        shot_index += 1
    return {"episode": episode, "scenes": scenes, "shots": shots, "total_shots": len(shots)}


def qc_html(result: Mapping[str, Any] | None) -> str:
    payload = dict(result or {})
    rows = []
    for key, value in payload.items():
        rows.append(f"<tr><th>{_escape_html(key)}</th><td>{_escape_html(value)}</td></tr>")
    return "<!doctype html><html><head><meta charset='utf-8'><title>StudioOS QC</title></head><body><h1>ComfyStudio QC</h1><table>" + "".join(rows) + "</table></body></html>"


def _escape_html(value: Any) -> str:
    text = str(value)
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


__all__ = [
    "BACKEND_DIR",
    "ROOT",
    "DB",
    "UI",
    "STUDIO_PATHS",
    "V8_DB",
    "COMFY_URL",
    "CANVAS_PATH",
    "MEMORY_PATH",
    "read_json",
    "atomic_write_json",
    "load_database",
    "CanvasConflict",
    "load_canvas",
    "save_canvas",
    "canon_check",
    "compile_prompt",
    "ComfyClient",
    "parse_script",
    "qc_html",
]
