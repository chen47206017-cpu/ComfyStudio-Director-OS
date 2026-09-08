from __future__ import annotations

import base64
import binascii
import mimetypes
import os
import unicodedata
from dataclasses import dataclass
from pathlib import Path


SUPPORTED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".mp4", ".mov", ".mkv", ".webm",
    ".wav", ".mp3", ".m4a", ".flac", ".json",
}


def clean_path_text(value: str) -> str:
    """Remove direction/control formatting characters from pasted Windows paths."""
    return "".join(c for c in value.strip() if unicodedata.category(c) != "Cf")


@dataclass(frozen=True)
class MediaRef:
    path: Path
    media_type: str
    size_bytes: int
    sha256: str

    def as_dict(self) -> dict[str, object]:
        return {
            "path": str(self.path),
            "media_type": self.media_type,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
        }


class MediaError(ValueError):
    pass


class MediaResolver:
    def __init__(self, roots: tuple[Path, ...], max_upload_mb: int = 200):
        self.roots = tuple(p.expanduser().resolve() for p in roots)
        self.max_bytes = max_upload_mb * 1024 * 1024

    def resolve(self, raw_path: str, expected_type: str | None = None) -> MediaRef:
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise MediaError("media path must be a non-empty string")
        path = Path(clean_path_text(raw_path)).expanduser()
        try:
            resolved = path.resolve(strict=True)
        except OSError as exc:
            raise MediaError(f"media file is not readable: {raw_path}") from exc
        if not resolved.is_file():
            raise MediaError(f"media path is not a file: {resolved}")
        if not any(self._within(resolved, root) for root in self.roots):
            raise MediaError("media path is outside COMFY_ALLOWED_MEDIA_ROOTS")
        size = resolved.stat().st_size
        if size <= 0:
            raise MediaError("media file is empty")
        if size > self.max_bytes:
            raise MediaError(f"media file exceeds {self.max_bytes // (1024 * 1024)} MB limit")
        ext = resolved.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise MediaError(f"unsupported media extension: {ext or '<none>'}")
        media_type = expected_type or self._infer_type(ext)
        if expected_type and media_type != expected_type:
            raise MediaError(f"expected media type {expected_type}, got {media_type}")
        import hashlib
        digest = hashlib.sha256()
        with resolved.open("rb") as fh:
            for block in iter(lambda: fh.read(1024 * 1024), b""):
                digest.update(block)
        return MediaRef(resolved, media_type, size, digest.hexdigest())

    @staticmethod
    def _within(path: Path, root: Path) -> bool:
        try:
            path.relative_to(root)
            return True
        except ValueError:
            return False

    @staticmethod
    def _infer_type(ext: str) -> str:
        if ext in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}:
            return "image"
        if ext in {".mp4", ".mov", ".mkv", ".webm"}:
            return "video"
        if ext in {".wav", ".mp3", ".m4a", ".flac"}:
            return "audio"
        return "document"

    @staticmethod
    def decode_data_url(data_url: str, destination: Path) -> MediaRef:
        if not isinstance(data_url, str) or "," not in data_url or not data_url.startswith("data:"):
            raise MediaError("invalid data URL")
        header, encoded = data_url.split(",", 1)
        if ";base64" not in header:
            raise MediaError("only base64 data URLs are supported")
        try:
            data = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise MediaError("invalid base64 media payload") from exc
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        return MediaRef(destination.resolve(), MediaResolver._infer_type(destination.suffix.lower()), len(data), "")

