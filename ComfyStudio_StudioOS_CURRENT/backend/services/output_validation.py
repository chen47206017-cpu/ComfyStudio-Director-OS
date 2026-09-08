"""Strict, local validation for StudioOS video job outputs.

Network success and a filename extension are not production evidence.  This
module validates the downloaded copy only after it is inside the controlled
StudioOS output root, and it never invokes a shell to inspect media.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _under_root(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _failure(reason_code: str, message_zh: str, path: Path | None = None, **details: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "verified": False,
        "reason_code": reason_code,
        "message_zh": message_zh,
    }
    if path is not None:
        payload["path"] = str(path)
    payload.update(details)
    return payload


def _float_or_none(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def validate_mp4_output(
    path: str | Path,
    controlled_root: str | Path,
    *,
    ffprobe_binary: str = "ffprobe",
    timeout_seconds: float = 20.0,
) -> dict[str, Any]:
    """Return verification evidence for one controlled MP4, or a reason code.

    A successful result requires every gate: output-root ownership, a nonempty
    ``.mp4`` file, ISO BMFF ``ftyp`` signature, successful ffprobe JSON, a
    positive duration, at least one video stream, and a recorded SHA-256.
    """

    source = Path(path)
    root = Path(controlled_root)
    if not _under_root(source, root):
        return _failure("OUTPUT_PATH_OUTSIDE_CONTROLLED_ROOT", "输出不在 StudioOS 受控目录内", source)
    if not source.is_file():
        return _failure("OUTPUT_FILE_MISSING", "输出文件不存在或不可读取", source)
    if source.suffix.lower() != ".mp4":
        return _failure("OUTPUT_NOT_MP4", "输出不是 MP4 文件", source)

    try:
        size = source.stat().st_size
    except OSError as exc:
        return _failure("OUTPUT_FILE_UNREADABLE", "输出文件无法读取", source, error=str(exc))
    if size <= 0:
        return _failure("OUTPUT_EMPTY", "输出 MP4 文件为空", source, size=size)

    try:
        with source.open("rb") as handle:
            header = handle.read(16)
    except OSError as exc:
        return _failure("OUTPUT_FILE_UNREADABLE", "输出文件无法读取", source, error=str(exc))
    if len(header) < 8 or header[4:8] != b"ftyp":
        return _failure("OUTPUT_MP4_FTYP_MISSING", "输出缺少 MP4 ftyp 容器标识", source, size=size)

    command = [
        ffprobe_binary,
        "-v",
        "error",
        "-show_entries",
        "format=format_name,format_long_name,duration:stream=codec_type,codec_name,width,height,avg_frame_rate,r_frame_rate,duration",
        "-of",
        "json",
        str(source),
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=max(1.0, timeout_seconds),
        )
    except FileNotFoundError:
        return _failure("FFPROBE_NOT_AVAILABLE", "系统未找到 ffprobe，不能把输出标记为完成", source)
    except subprocess.TimeoutExpired:
        return _failure("FFPROBE_TIMEOUT", "ffprobe 校验超时，输出未通过验收", source)
    except OSError as exc:
        return _failure("FFPROBE_EXECUTION_FAILED", "ffprobe 无法执行，输出未通过验收", source, error=str(exc))

    if completed.returncode != 0:
        return _failure(
            "FFPROBE_FAILED",
            "ffprobe 无法解析该 MP4，输出未通过验收",
            source,
            stderr=(completed.stderr or "").strip()[:1000],
        )
    try:
        probe = json.loads(completed.stdout or "{}")
    except json.JSONDecodeError:
        return _failure("FFPROBE_INVALID_JSON", "ffprobe 未返回可用媒体信息", source)
    if not isinstance(probe, dict):
        return _failure("FFPROBE_INVALID_JSON", "ffprobe 未返回可用媒体信息", source)

    streams = probe.get("streams") if isinstance(probe.get("streams"), list) else []
    video_streams = [stream for stream in streams if isinstance(stream, dict) and stream.get("codec_type") == "video"]
    if not video_streams:
        return _failure("OUTPUT_VIDEO_STREAM_MISSING", "MP4 中没有可用视频流", source, ffprobe=probe)
    format_info = probe.get("format") if isinstance(probe.get("format"), dict) else {}
    duration = _float_or_none(format_info.get("duration"))
    if duration is None:
        duration = next((_float_or_none(stream.get("duration")) for stream in video_streams if _float_or_none(stream.get("duration")) is not None), None)
    if duration is None:
        return _failure("OUTPUT_DURATION_INVALID", "MP4 时长无效或为零", source, ffprobe=probe)

    try:
        digest = _sha256(source)
    except OSError as exc:
        return _failure("OUTPUT_HASH_FAILED", "无法计算输出文件 SHA-256", source, error=str(exc))
    return {
        "verified": True,
        "path": str(source.resolve()),
        "mime": "video/mp4",
        "size": size,
        "sha256": digest,
        "duration_s": duration,
        "ffprobe": {
            "format_name": format_info.get("format_name"),
            "format_long_name": format_info.get("format_long_name"),
            "duration": duration,
            "video_streams": [
                {
                    "codec_name": stream.get("codec_name"),
                    "width": stream.get("width"),
                    "height": stream.get("height"),
                    "avg_frame_rate": stream.get("avg_frame_rate"),
                    "r_frame_rate": stream.get("r_frame_rate"),
                }
                for stream in video_streams
            ],
        },
    }


__all__ = ["validate_mp4_output"]
