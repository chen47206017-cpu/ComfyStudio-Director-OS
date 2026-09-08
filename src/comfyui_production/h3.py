"""MiniMax H3 planning contracts with no model or network side effects."""

from __future__ import annotations

import ipaddress
from typing import Any
from urllib.parse import urlsplit


ENGINE_ID = "MINIMAX_H3"
LOCAL_STATUS = "BLOCKED_LOCAL_H3"
AUTODL_STATUS = "DRY_RUN_ONLY"
AUTODL_LIGHT_WORKFLOW = "minimax_h3_lightx2v_v5"
AUTODL_IMAGE_AUDIO_WORKFLOW = "minimax_h3_image_audio_to_video_v2"
LEGACY_SCHEMA_STATUS = "USER_SUPPLIED_UNVERIFIED"
VENDOR_SUBMISSION_STATUS = "BLOCKED_PENDING_SCHEMA_EVIDENCE"
PLANNER_RESOLUTIONS = (
    "480p\u7ad6",
    "480p\u6a2a",
    "768p\u7ad6",
    "768p\u6a2a",
)
_PLANNER_FIELDS = frozenset({
    "engine",
    "prompt",
    "duration",
    "resolution",
    "reference_images",
    "reference_audios",
    "reference_videos",
    "seed",
})


class MiniMaxH3PlanError(ValueError):
    """A request cannot be represented by the safe H3 dry-run contract."""


def is_minimax_h3_workflow_id(value: Any) -> bool:
    return isinstance(value, str) and value.strip().lower().startswith("minimax_h3_")


def h3_catalog() -> dict[str, Any]:
    """Return the stable selector contract consumed by the management page."""
    return {
        "id": ENGINE_ID,
        "status": LOCAL_STATUS,
        "local": {
            "status": LOCAL_STATUS,
            "reason": "Native H3 nodes are not available in the current local ComfyUI runtime.",
        },
        "autodl": {
            "status": AUTODL_STATUS,
            "reason": "This selector plans a request only and never submits a cloud task.",
            "transport_contract": "VERIFIED_GENERIC_WORKFLOW_API",
            "vendor_schema_status": LEGACY_SCHEMA_STATUS,
            "submit_allowed": False,
            "workflows": [
                {
                    "id": AUTODL_LIGHT_WORKFLOW,
                    "when": "one or more reference images and no reference audio",
                    "schema_status": LEGACY_SCHEMA_STATUS,
                    "submit_allowed": False,
                    "schema_evidence": None,
                },
                {
                    "id": AUTODL_IMAGE_AUDIO_WORKFLOW,
                    "when": "one or more reference images plus one or more reference audios",
                    "schema_status": LEGACY_SCHEMA_STATUS,
                    "submit_allowed": False,
                    "schema_evidence": None,
                },
            ],
        },
        "selector": {
            "method": "POST",
            "path": "/api/comfyui/h3/dry-run",
        },
        "schema": {
            "type": "object",
            "contract_scope": "PROJECT_NO_IO_PLANNER",
            "vendor_schema_status": LEGACY_SCHEMA_STATUS,
            "additionalProperties": False,
            "required": ["prompt", "reference_images"],
            "properties": {
                "engine": {"const": ENGINE_ID},
                "prompt": {"type": "string", "minLength": 1, "maxLength": 10000},
                "duration": {"type": "integer", "minimum": 1, "maximum": 15, "default": 5},
                "resolution": {"type": "string", "enum": list(PLANNER_RESOLUTIONS), "default": "768p\u7ad6"},
                "reference_images": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 9,
                    "items": {"type": "string", "format": "uri"},
                },
                "reference_audios": {
                    "type": "array",
                    "maxItems": 3,
                    "items": {"type": "string", "format": "uri"},
                },
                "reference_videos": {
                    "type": "array",
                    "maxItems": 3,
                    "description": "Not selected by the current project dry-run planner.",
                    "items": {"type": "string", "format": "uri"},
                },
                "seed": {"type": "integer", "minimum": 0, "description": "Planning intent only; not a vendor field."},
            },
        },
    }


def _valid_public_http_url(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise MiniMaxH3PlanError(f"{field} must be a non-empty HTTP(S) URL")
    url = value.strip()
    if len(url) > 4096 or any(char.isspace() or ord(char) < 32 for char in url):
        raise MiniMaxH3PlanError(f"{field} must be a valid HTTP(S) URL")
    parsed = urlsplit(url)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise MiniMaxH3PlanError(f"{field} must be an AutoDL-reachable HTTP(S) URL")
    if parsed.username or parsed.password or parsed.fragment:
        raise MiniMaxH3PlanError(f"{field} must not include credentials or a fragment")
    host = parsed.hostname.lower().strip("[]")
    if host in {"localhost", "localhost.localdomain"}:
        raise MiniMaxH3PlanError(f"{field} must not target localhost")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return url
    if address.is_private or address.is_loopback or address.is_link_local or address.is_reserved or address.is_unspecified:
        raise MiniMaxH3PlanError(f"{field} must not target a private address")
    return url


def _url_list(payload: dict[str, Any], field: str, *, minimum: int = 0, maximum: int) -> list[str]:
    value = payload.get(field, [])
    if not isinstance(value, list):
        raise MiniMaxH3PlanError(f"{field} must be an array")
    if not minimum <= len(value) <= maximum:
        raise MiniMaxH3PlanError(f"{field} must contain {minimum} to {maximum} URLs")
    return [_valid_public_http_url(item, f"{field}[{index}]") for index, item in enumerate(value)]


def _integer(payload: dict[str, Any], field: str, *, default: int | None = None, minimum: int, maximum: int) -> int | None:
    if field not in payload:
        return default
    value = payload[field]
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise MiniMaxH3PlanError(f"{field} must be an integer from {minimum} to {maximum}")
    return value


def _reject_unknown_planner_fields(payload: dict[str, Any]) -> None:
    unknown = sorted(str(field) for field in payload if field not in _PLANNER_FIELDS)
    if unknown:
        raise MiniMaxH3PlanError("unsupported planner field(s): " + ", ".join(unknown))


def plan_autodl_dry_run(payload: Any) -> dict[str, Any]:
    """Validate unified H3 input and select an AutoDL wrapper without I/O."""
    if not isinstance(payload, dict):
        raise MiniMaxH3PlanError("request body must be a JSON object")
    _reject_unknown_planner_fields(payload)
    engine = payload.get("engine", ENGINE_ID)
    if not isinstance(engine, str) or engine.strip().upper() != ENGINE_ID:
        raise MiniMaxH3PlanError(f"engine must be {ENGINE_ID}")
    prompt = payload.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt.strip()) > 10000:
        raise MiniMaxH3PlanError("prompt must be a non-empty string up to 10000 characters")
    duration = _integer(payload, "duration", default=5, minimum=1, maximum=15)
    resolution = payload.get("resolution", "768p\u7ad6")
    if not isinstance(resolution, str) or resolution not in PLANNER_RESOLUTIONS:
        raise MiniMaxH3PlanError("resolution is not supported by the project dry-run planner")
    images = _url_list(payload, "reference_images", minimum=1, maximum=9)
    audios = _url_list(payload, "reference_audios", maximum=3)
    videos = _url_list(payload, "reference_videos", maximum=3)
    if videos:
        raise MiniMaxH3PlanError("reference_videos are not selected by the current project dry-run planner")
    seed = _integer(payload, "seed", minimum=0, maximum=18446744073709551615)

    workflow_id = AUTODL_IMAGE_AUDIO_WORKFLOW if audios else AUTODL_LIGHT_WORKFLOW
    planning_input: dict[str, Any] = {
        "prompt": prompt.strip(),
        "duration": duration,
        "resolution": resolution,
        "reference_images": images,
        "reference_audios": audios,
    }
    if seed is not None:
        planning_input["seed"] = seed

    return {
        "engine": ENGINE_ID,
        "execution": AUTODL_STATUS,
        "local_status": LOCAL_STATUS,
        "provider": "AUTODL_COMFYUI",
        "workflow_id": workflow_id,
        "planning_input": planning_input,
        "vendor_submission": {
            "status": VENDOR_SUBMISSION_STATUS,
            "submit_allowed": False,
            "schema_status": LEGACY_SCHEMA_STATUS,
            "schema_evidence": None,
            "required_before_enablement": [
                "Capture the current AutoDL workflow drawer schema for the selected workflow ID.",
                "Record its source URL, retrieval time, version or hash, and exact request body fields.",
                "Run a separately authorized, budgeted cloud test after the paid-submit gate is enabled.",
            ],
        },
        "warnings": [
            "This is a dry-run plan. No AutoDL task was submitted.",
            "Local H3 remains blocked until a compatible native ComfyUI runtime is installed and verified.",
            "The selected workflow IDs are user-supplied legacy identifiers; this planner does not construct vendor fields or a submittable request body.",
            "The 1080x1920 delivery target requires a separately verified direct renderer or validated upscale; it is not a claimed source resolution of this legacy H3 wrapper.",
            "Reference URLs are not persisted; provide original hosted URLs only after cloud execution is explicitly approved.",
        ],
    }
