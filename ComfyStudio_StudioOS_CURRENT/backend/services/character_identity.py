from __future__ import annotations

from typing import Any, Mapping


IDENTITIES = {
    "CHAR_SW25_MASTER": {
        "id": "CHAR_SW25_MASTER", "name": "苏晚晴25岁", "age": 25, "year_range": [2006, 2006],
        "face_reference": "苏晚晴25岁主参考", "clothes": "2006建筑设计师日常服装", "voice_id": "SW25_VOICE_01",
        "forbidden": ["45岁脸", "现代服装", "错误发型", "智能手机"],
    },
    "CHAR_CN40_MASTER": {
        "id": "CHAR_CN40_MASTER", "name": "陈念40岁", "age": 40, "year_range": [2040, 2099],
        "face_reference": "陈念40岁主参考", "clothes": "未来时代声音身份", "voice_id": "CN40_VOICE_01",
        "forbidden": ["25岁苏晚晴脸", "2006年现场人物"],
    },
}


def get_identity(character_id: str) -> dict[str, Any] | None:
    identity = IDENTITIES.get(character_id)
    return dict(identity) if identity else None


def build_identity_bindings(character_ids: list[str]) -> list[dict[str, Any]]:
    return [dict(identity, role="character_identity") for character_id in character_ids if (identity := get_identity(character_id))]


def voice_bindings(character_ids: list[str], declared_voice_ids: list[str] | None = None) -> list[dict[str, Any]]:
    declared = set(declared_voice_ids or [])
    result = []
    for identity in build_identity_bindings(character_ids):
        voice_id = identity["voice_id"]
        result.append({"id": voice_id, "character_id": identity["id"], "name": f"{identity['name']}声音", "required": voice_id not in declared})
    return result
