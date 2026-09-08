"""Workflow capsule discovery, HTTP-evidence preflight, and safe slot injection."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class WorkflowCapsuleStore:
    def __init__(self, root: Path):
        self.root = root
        self.capsules = root / "workflows" / "capsules"

    def _folder(self, capsule_id: str) -> Path | None:
        candidate = self.capsules / capsule_id
        return candidate if candidate.is_dir() else None

    def _read_capsule(self, folder: Path) -> dict[str, Any] | None:
        capsule_path = folder / "capsule.json"
        try:
            data = json.loads(capsule_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            return None
        return dict(data) if isinstance(data, Mapping) else None

    def _with_hashes(self, folder: Path, data: Mapping[str, Any]) -> dict[str, Any]:
        return {
            **dict(data),
            "capsule_sha256": _sha256(folder / "capsule.json"),
            "ui_sha256": data.get("ui_sha256") or _sha256(folder / "workflow.ui.json"),
            "api_sha256": data.get("api_sha256") or _sha256(folder / "workflow.api.json"),
        }

    def list(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        if not self.capsules.exists():
            return result
        for folder in sorted(item for item in self.capsules.iterdir() if item.is_dir()):
            data = self._read_capsule(folder)
            if data is not None:
                result.append(self._with_hashes(folder, data))
        return result

    def get(self, capsule_id: str) -> dict[str, Any] | None:
        folder = self._folder(capsule_id)
        data = self._read_capsule(folder) if folder else None
        return self._with_hashes(folder, data) if folder and data else None

    def preflight(self, capsule_id: str, worker: Mapping[str, Any] | None) -> dict[str, Any]:
        """Preflight only HTTP-advertised Worker facts; no model-file probing."""
        capsule = self.get(capsule_id)
        errors: list[dict[str, str]] = []
        if capsule is None:
            errors.append({"code": "CAPSULE_NOT_FOUND", "message_zh": "找不到工作流胶囊"})
            return {"status": "BLOCKED", "capsule_id": capsule_id, "errors": errors, "warnings": []}
        if worker is None:
            errors.append({"code": "WORKER_UNAVAILABLE", "message_zh": "没有可用的 ComfyUI Worker"})
        required_nodes = [str(item) for item in (capsule.get("required_node_classes") or [])]
        available_nodes = set(str(item) for item in ((worker or {}).get("node_classes") or []))
        for node_class in required_nodes:
            if node_class not in available_nodes:
                errors.append({"code": "NODE_MISSING", "node_class": node_class, "message_zh": f"缺少节点：{node_class}"})

        required_models = {str(item) for item in (capsule.get("required_models") or [])}
        available_models = {str(item) for item in ((worker or {}).get("model_inventory") or [])}
        model_source = str((worker or {}).get("model_inventory_source") or "/object_info")
        model_availability = [
            {
                "model": model,
                "status": "HTTP_OBSERVED" if model in available_models else "UNVERIFIED",
                "source": model_source,
                "file_integrity": "UNVERIFIED_NOT_PERMITTED_HTTP_ONLY",
            }
            for model in sorted(required_models)
        ]
        model_warnings = [
            {"code": "MODEL_UNVERIFIED", "model": model, "message_zh": f"模型尚未在 /object_info 中确认：{model}"}
            for model in sorted(required_models - available_models)
        ]
        if errors:
            status = "BLOCKED"
        elif model_warnings:
            # Node classes alone cannot prove a usable H3 model installation.
            status = "UNVERIFIED"
        else:
            status = "READY"
        worker_snapshot = {
            key: (worker or {}).get(key)
            for key in (
                "id", "base_url", "lane", "internal_lane", "status", "comfy_version",
                "python_version", "torch_version", "gpu_name", "vram_total", "vram_free",
                "node_classes_hash", "model_inventory_hash", "last_seen_at",
            )
        }
        return {
            "status": status,
            "capsule": capsule,
            "worker_id": (worker or {}).get("id"),
            "worker_snapshot": worker_snapshot,
            "errors": errors,
            "warnings": model_warnings,
            # Names exposed by /object_info are HTTP capability observations,
            # not local model-file integrity evidence.
            "model_inventory_verified": False,
            "model_inventory_status": "HTTP_OBSERVED" if not model_warnings else "UNVERIFIED",
            "model_availability": model_availability,
            "verification_scope": "HTTP /system_stats + /object_info only",
        }

    def compile_workflow(self, capsule_id: str, slot_values: Mapping[str, Any]) -> dict[str, Any]:
        """Deep-copy the API workflow and inject only declared capsule slots."""
        folder = self._folder(capsule_id)
        data = self._read_capsule(folder) if folder else None
        if folder is None or data is None:
            return {"status": "BLOCKED", "reason_code": "CAPSULE_NOT_FOUND", "message_zh": "找不到工作流胶囊"}
        api_path = folder / "workflow.api.json"
        try:
            source = json.loads(api_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            return {"status": "BLOCKED", "reason_code": "WORKFLOW_API_UNREADABLE", "message_zh": "工作流 API JSON 无法读取", "error": str(exc)}
        if not isinstance(source, Mapping):
            return {"status": "BLOCKED", "reason_code": "WORKFLOW_API_INVALID", "message_zh": "工作流 API JSON 格式无效"}

        workflow = copy.deepcopy(dict(source))
        errors: list[dict[str, Any]] = []
        applied: list[dict[str, Any]] = []
        declared = {str(slot.get("id")): slot for slot in data.get("slots", []) if isinstance(slot, Mapping) and slot.get("id")}
        for slot_id, value in dict(slot_values).items():
            slot = declared.get(str(slot_id))
            if slot is None:
                errors.append({"code": "WORKFLOW_SLOT_UNDECLARED", "slot": str(slot_id), "message_zh": f"工作流未声明槽位：{slot_id}"})
                continue
            node_id = str(slot.get("node") or "")
            input_name = str(slot.get("input") or "")
            node = workflow.get(node_id)
            inputs = node.get("inputs") if isinstance(node, Mapping) else None
            if not isinstance(inputs, dict) or not input_name:
                errors.append({"code": "WORKFLOW_SLOT_MISSING", "slot": str(slot_id), "node": node_id, "input": input_name, "message_zh": f"工作流槽位无效：{slot_id}"})
                continue
            inputs[input_name] = value
            applied.append({"slot": str(slot_id), "node": node_id, "input": input_name})
        if errors:
            return {"status": "BLOCKED", "reason_code": "WORKFLOW_SLOT_INJECTION_FAILED", "message_zh": "工作流槽位注入失败", "errors": errors}
        return {
            "status": "READY",
            "workflow": workflow,
            "applied_slots": applied,
            "evidence": {
                "capsule_id": capsule_id,
                "capsule_sha256": _sha256(folder / "capsule.json"),
                "workflow_api_sha256": _sha256(api_path),
            },
        }


__all__ = ["WorkflowCapsuleStore"]
