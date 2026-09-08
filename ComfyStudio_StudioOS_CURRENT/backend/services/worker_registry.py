"""HTTP-only discovery for local ComfyUI execution workers."""

from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


try:
    BEIJING = ZoneInfo("Asia/Shanghai")
except Exception:
    BEIJING = timezone(timedelta(hours=8), name="Asia/Shanghai")


PUBLIC_LANES: dict[str, dict[str, str | None]] = {
    "local_comfy": {
        "internal_lane": "local_h3",
        "label_zh": "本机 ComfyUI 8189",
        "blocked_reason": None,
        "blocked_message": None,
    },
    "autodl5090": {
        "internal_lane": None,
        "label_zh": "AutoDL 5090",
        "blocked_reason": "AUTODL5090_NOT_CONFIGURED",
        "blocked_message": "AutoDL 5090 尚未配置，系统不会回退到本机或发起外部调用。",
    },
    "api": {
        "internal_lane": None,
        "label_zh": "API",
        "blocked_reason": "API_NOT_CONFIGURED",
        "blocked_message": "API 执行通道尚未配置，系统不会发送外部或付费请求。",
    },
}


def now_beijing() -> str:
    return datetime.now(timezone.utc).astimezone(BEIJING).isoformat(timespec="seconds")


def normalize_public_lane(lane: str | None) -> str:
    value = str(lane or "local_comfy").strip().lower()
    # local_h3 remains accepted for old V10 clients, but the public UI and API
    # contract expose the understandable local_comfy lane going forward.
    return "local_comfy" if value in {"", "local_h3", "local_comfy"} else value


def lane_definition(lane: str | None) -> dict[str, str | None]:
    normalized = normalize_public_lane(lane)
    fallback = {
        "internal_lane": None,
        "label_zh": normalized,
        "blocked_reason": "LANE_UNKNOWN",
        "blocked_message": "未知执行通道，未发起任何执行请求。",
    }
    return {"id": normalized, **PUBLIC_LANES.get(normalized, fallback)}


def _ports() -> list[int]:
    raw = os.environ.get("COMFYSTUDIO_WORKER_PORTS", "8188,8189")
    ports: list[int] = []
    for item in raw.split(","):
        try:
            port = int(item.strip())
        except ValueError:
            continue
        if 1 <= port <= 65535 and port not in ports:
            ports.append(port)
    return ports or [8188, 8189]


def _request(base_url: str, path: str, timeout: float) -> tuple[dict[str, Any] | None, float, str | None]:
    started = time.perf_counter()
    try:
        request = Request(f"{base_url.rstrip('/')}/{path.lstrip('/')}", headers={"Accept": "application/json"})
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return (payload if isinstance(payload, dict) else {"data": payload}, (time.perf_counter() - started) * 1000, None)
    except Exception as exc:
        return None, (time.perf_counter() - started) * 1000, str(exc)


def _digest(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _model_names(value: Any) -> list[str]:
    """Extract model choices already advertised by ``/object_info`` only."""
    found: set[str] = set()
    if isinstance(value, Mapping):
        for item in value.values():
            found.update(_model_names(item))
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            found.update(_model_names(item))
    elif isinstance(value, str) and value.lower().endswith((".safetensors", ".ckpt", ".pt", ".pth", ".bin")):
        found.add(value)
    return sorted(found)


class WorkerRegistry:
    """Discover only HTTP-visible worker facts; never inspect runtime files."""

    def __init__(self, timeout: float = 2.5):
        self.timeout = timeout

    def discover(self) -> list[dict[str, Any]]:
        workers: list[dict[str, Any]] = []
        for port in _ports():
            base_url = f"http://127.0.0.1:{port}"
            stats, probe_ms, stats_error = _request(base_url, "/system_stats", self.timeout)
            info, _, info_error = _request(base_url, "/object_info", self.timeout) if stats is not None else (None, 0.0, "health unavailable")
            connected = stats is not None and info is not None
            system = stats.get("system", {}) if isinstance(stats, Mapping) else {}
            devices = stats.get("devices", []) if isinstance(stats, Mapping) else []
            device = devices[0] if devices and isinstance(devices[0], Mapping) else {}
            node_classes = sorted(str(name) for name in info.keys()) if isinstance(info, Mapping) else []
            model_inventory = _model_names(info)
            public_lane = "local_comfy" if port == 8189 else "local_default"
            internal_lane = "local_h3" if port == 8189 else "local_default"
            workers.append({
                "id": f"local-{port}",
                "name": f"本机 ComfyUI {port}",
                "base_url": base_url,
                "enabled": True,
                "lane": public_lane,
                "internal_lane": internal_lane,
                "priority": 10 if port == 8189 else 20,
                "runtime_evidence": "http://127.0.0.1 worker API",
                "comfy_version": system.get("comfyui_version"),
                "python_version": system.get("python_version"),
                "torch_version": system.get("pytorch_version"),
                "cuda_version": system.get("cuda_version"),
                "gpu_name": device.get("name"),
                "vram_total": device.get("vram_total"),
                "vram_free": device.get("vram_free"),
                "node_classes_hash": _digest(node_classes) if info is not None else None,
                "model_inventory_hash": _digest(model_inventory) if model_inventory else None,
                "model_inventory_source": "/object_info" if info is not None else None,
                "model_inventory_status": "HTTP_OBSERVED" if info is not None else "UNVERIFIED",
                "last_seen_at": now_beijing() if connected else None,
                "last_probe_ms": round(probe_ms, 2),
                "status": "READY" if connected else "BLOCKED",
                "status_reason": None if connected else "COMFY_UNREACHABLE",
                "error": None if connected else (stats_error or info_error),
                "node_classes": node_classes,
                "model_inventory": model_inventory,
                "capabilities": {
                    "h3": any("MiniMaxH3" in name or "MinimaxH3" in name for name in node_classes),
                    "motion_context": any("MotionContext" in name for name in node_classes),
                    "extender": any("Extender" in name for name in node_classes),
                },
            })
        return workers

    def select(self, lane: str | None = None) -> dict[str, Any] | None:
        normalized = normalize_public_lane(lane)
        definition = lane_definition(normalized)
        internal_lane = definition.get("internal_lane")
        if not internal_lane:
            return None
        candidates = [
            item
            for item in self.discover()
            if item.get("status") == "READY"
            and (item.get("lane") == normalized or item.get("internal_lane") == internal_lane)
        ]
        return sorted(candidates, key=lambda item: int(item.get("priority", 100)))[0] if candidates else None


__all__ = ["PUBLIC_LANES", "WorkerRegistry", "lane_definition", "normalize_public_lane", "now_beijing"]
