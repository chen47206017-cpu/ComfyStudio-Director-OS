"""Print safe, reproducible metadata for an image, audio, or video artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import struct
import subprocess
from pathlib import Path
from typing import Any


def sha256(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            size += len(block)
            digest.update(block)
    return size, digest.hexdigest()


def png_dimensions(path: Path) -> dict[str, int] | None:
    with path.open("rb") as handle:
        header = handle.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        return None
    width, height = struct.unpack(">II", header[16:24])
    return {"width": width, "height": height}


def ffprobe(path: Path) -> dict[str, Any] | None:
    executable = shutil.which("ffprobe")
    if not executable:
        return None
    completed = subprocess.run(
        [
            executable,
            "-v",
            "error",
            "-show_entries",
            "format=duration,format_name:stream=index,codec_type,codec_name,width,height,avg_frame_rate,r_frame_rate,nb_frames",
            "-of",
            "json",
            str(path),
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        return {"error": "ffprobe could not inspect this file", "returncode": completed.returncode}
    try:
        parsed = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {"error": "ffprobe returned invalid JSON"}
    return parsed if isinstance(parsed, dict) else {"error": "ffprobe returned an invalid response"}


def inspect(path: Path) -> dict[str, Any]:
    resolved = path.expanduser().resolve(strict=True)
    if not resolved.is_file():
        raise ValueError("path is not a file")
    size, digest = sha256(resolved)
    result: dict[str, Any] = {
        "path": str(resolved),
        "size_bytes": size,
        "sha256": digest,
        "suffix": resolved.suffix.lower(),
    }
    dimensions = png_dimensions(resolved) if resolved.suffix.lower() == ".png" else None
    if dimensions:
        result["image"] = dimensions
    probe = ffprobe(resolved)
    result["ffprobe"] = probe if probe is not None else {"available": False}
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect a local media artifact without changing it")
    parser.add_argument("path", help="local image, audio, or video file")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(inspect(Path(args.path)), ensure_ascii=False, indent=2))
    except (OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
