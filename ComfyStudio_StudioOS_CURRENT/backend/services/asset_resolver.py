from __future__ import annotations

import re
from typing import Any, Mapping


RULES = [
    (re.compile(r"设计工作室|工作室|2006"), {"id": "SCENE_2006_STUDIO", "type": "scene", "name": "2006设计工作室"}),
    (re.compile(r"设计院门口|北城设计院|设计院"), {"id": "SCENE_BEICHENG_DESIGN_INSTITUTE", "type": "scene", "name": "北城设计院门口"}),
    (re.compile(r"米黄色有线电话|米黄色有线座机|有线电话|座机"), {"id": "PROP_PHONE_2006", "type": "prop", "name": "米黄色有线座机"}),
    (re.compile(r"建筑设计原稿|设计原稿|原稿"), {"id": "PROP_ARCHIVE_DESIGN", "type": "prop", "name": "建筑设计原稿"}),
    (re.compile(r"25岁苏晚晴|苏晚晴25岁|25岁的苏晚晴"), {"id": "CHAR_SW25_MASTER", "type": "character", "name": "苏晚晴25岁"}),
    (re.compile(r"未来女儿|陈念|陈念40岁"), {"id": "CHAR_CN40_MASTER", "type": "character", "name": "陈念40岁"}),
]


def resolve_assets(text: str, declared: Mapping[str, Any] | None = None) -> dict[str, Any]:
    source = str(text or "")
    found: list[dict[str, Any]] = []
    seen: set[str] = set()
    for pattern, asset in RULES:
        if pattern.search(source) and asset["id"] not in seen:
            found.append(dict(asset, match=pattern.pattern))
            seen.add(asset["id"])
    for item in (declared or {}).get("assets", []) if isinstance(declared, Mapping) else []:
        if isinstance(item, Mapping) and item.get("id") and item["id"] not in seen:
            found.append(dict(item, match="declared"))
            seen.add(str(item["id"]))
    return {"assets": found, "asset_ids": [item["id"] for item in found], "missing": []}


def bind_shot(shot: Mapping[str, Any]) -> dict[str, Any]:
    # The declared/current scene is authoritative.  The full script is still
    # useful for characters and props, but previous-scene mentions must not
    # leak into the current shot's scene reference list.
    scene_source = str(shot.get("scene_text") or shot.get("scene") or shot.get("title") or "")
    detail_source = " ".join(str(shot.get(key, "")) for key in ("title", "script"))
    scene_assets = resolve_assets(scene_source)["assets"]
    detail_assets = [item for item in resolve_assets(detail_source)["assets"] if item.get("type") != "scene"]
    by_id = {item["id"]: item for item in [*scene_assets, *detail_assets]}
    for asset_id in list(shot.get("characters", [])) + list(shot.get("props", [])) + [shot.get("scene")]:
        if asset_id and asset_id not in by_id:
            by_id[asset_id] = {"id": asset_id, "type": "declared", "name": asset_id, "match": "shot_contract"}
    return {"assets": list(by_id.values()), "asset_ids": list(by_id), "missing": []}
