from __future__ import annotations

from typing import Any, Mapping


def evaluate_continuity(previous: Mapping[str, Any] | None, current: Mapping[str, Any]) -> dict[str, Any]:
    if not previous:
        return {"status": "ROOT_SHOT", "inherited": {}, "changes": [], "issues": []}
    previous_characters = list(previous.get("characters", []))
    current_characters = list(current.get("characters", []))
    inherited = {
        "characters": previous_characters,
        "time_year": previous.get("year"),
        "voices": list(previous.get("voices", [])),
        "wardrobe_lock": "inherit",
        "face_lock": "inherit",
    }
    issues = []
    if previous_characters and current_characters and not set(current_characters).issubset(set(previous_characters)):
        issues.append({"code": "CHARACTER_CONTINUITY_CHANGED", "message": "角色身份发生变化，请确认是否为有意切换"})
    changes = []
    if previous.get("scene") != current.get("scene"):
        changes.append({"field": "scene", "from": previous.get("scene"), "to": current.get("scene"), "reason": "镜头地点切换"})
    if previous.get("props") != current.get("props"):
        changes.append({"field": "props", "from": previous.get("props", []), "to": current.get("props", []), "reason": "道具随剧本变化"})
    return {"status": "READY" if not issues else "HOLD", "inherited": inherited, "changes": changes, "issues": issues}

