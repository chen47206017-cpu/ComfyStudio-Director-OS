from __future__ import annotations

import math
import os
import re
from dataclasses import dataclass, field
from pathlib import Path


_DOTENV_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _parse_dotenv_line(line: str) -> tuple[str, str] | None:
    """Parse one conservative ``.env`` assignment without evaluating code."""
    text = line.strip()
    if not text or text.startswith("#"):
        return None
    if text.startswith("export "):
        text = text[7:].lstrip()
    if "=" not in text:
        return None
    key, value = text.split("=", 1)
    key = key.strip()
    if not _DOTENV_KEY_RE.fullmatch(key):
        return None
    value = value.strip()
    if value[:1] in {"'", '"'}:
        quote = value[0]
        if len(value) < 2 or value[-1] != quote:
            return None
        value = value[1:-1]
    return key, value


def _read_dotenv(path: Path) -> dict[str, str]:
    """Read a project ``.env`` file; malformed lines and examples are ignored."""
    if path.name.lower() == ".env.example" or not path.is_file():
        return {}
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError):
        return {}
    values: dict[str, str] = {}
    for line in lines:
        parsed = _parse_dotenv_line(line)
        if parsed is not None:
            key, value = parsed
            values[key] = value
    return values


def _truthy(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _strict_bool(value: str | None, default: bool = False) -> bool:
    """Parse an opt-in boolean without silently accepting a typo."""
    if value is None or not value.strip():
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError("boolean setting must be one of 0, 1, true, false, yes, no, on, or off")


def _bounded_seconds(value: str | None, default: float, *, maximum: float = 86400.0) -> float:
    """Return a finite, positive timeout suitable for a long-running job."""
    raw = default if value is None or not value.strip() else value.strip()
    try:
        seconds = float(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("timeout setting must be a finite number of seconds") from exc
    if not math.isfinite(seconds):
        raise ValueError("timeout setting must be a finite number of seconds")
    if not 1.0 <= seconds <= maximum:
        raise ValueError(f"timeout setting must be between 1 and {int(maximum)} seconds")
    return seconds


def _path_list(value: str | None) -> tuple[Path, ...]:
    if not value:
        return ()
    # On Windows os.pathsep is ';'; accepting ',' makes JSON/env editing less
    # surprising while preserving paths that contain spaces.
    parts = value.split(os.pathsep)
    return tuple(Path(p.strip()).expanduser() for p in parts if p.strip())


@dataclass(frozen=True)
class Settings:
    provider: str = "LOCAL"
    local_url: str = "http://127.0.0.1:8188"
    remote_url: str = ""
    remote_token: str = ""
    autodl_api_base_url: str = "https://autodl.art"
    autodl_api_token: str = ""
    autodl_allow_paid_submit: bool = False
    autodl_poll_timeout_seconds: float = 1800.0
    api_host: str = "127.0.0.1"
    api_port: int = 8092
    allowed_media_roots: tuple[Path, ...] = field(default_factory=tuple)
    max_upload_mb: int = 200
    job_store: Path = Path("runtime/jobs.json")
    workflow_dir: Path = Path("workflows")
    model_manifest: Path = Path("models.manifest.json")
    client_timeout_seconds: float = 30.0
    poll_interval_seconds: float = 1.0

    @classmethod
    def from_env(cls, environ: dict[str, str] | None = None) -> "Settings":
        root = Path(__file__).resolve().parents[2]
        # Load only the project-root .env as a fallback.  Explicit process
        # values, including an intentional empty value, always win.
        env = dict(environ if environ is not None else os.environ)
        for key, value in _read_dotenv(root / ".env").items():
            env.setdefault(key, value)

        def rooted(name: str, fallback: str) -> Path:
            value = env.get(name, fallback)
            p = Path(value).expanduser()
            return p if p.is_absolute() else root / p

        configured_roots = _path_list(env.get("COMFY_ALLOWED_MEDIA_ROOTS"))
        roots = tuple(path if path.is_absolute() else root / path for path in configured_roots)
        if not roots:
            roots = (Path(r"F:\AI短剧"), root / "sample_assets")
        return cls(
            provider=env.get("COMFY_PROVIDER", "LOCAL").strip().upper() or "LOCAL",
            local_url=env.get("COMFY_LOCAL_URL", "http://127.0.0.1:8188").rstrip("/"),
            remote_url=env.get("COMFY_REMOTE_URL", "").rstrip("/"),
            remote_token=env.get("COMFY_REMOTE_TOKEN", ""),
            autodl_api_base_url=env.get("AUTODL_API_BASE_URL", "https://autodl.art").rstrip("/"),
            autodl_api_token=env.get("AUTODL_API_TOKEN", ""),
            autodl_allow_paid_submit=_strict_bool(env.get("AUTODL_ALLOW_PAID_SUBMIT"), default=False),
            autodl_poll_timeout_seconds=_bounded_seconds(
                env.get("AUTODL_POLL_TIMEOUT_SECONDS"), default=1800.0
            ),
            api_host=env.get("COMFY_API_HOST", "127.0.0.1"),
            api_port=int(env.get("COMFY_API_PORT", "8092")),
            allowed_media_roots=roots,
            max_upload_mb=max(1, int(env.get("COMFY_MAX_UPLOAD_MB", "200"))),
            job_store=rooted("COMFY_JOB_STORE", "runtime/jobs.json"),
            workflow_dir=rooted("COMFY_WORKFLOW_DIR", "workflows"),
            model_manifest=rooted("COMFY_MODEL_MANIFEST", "models.manifest.json"),
            client_timeout_seconds=max(1.0, float(env.get("COMFY_CLIENT_TIMEOUT_SECONDS", "30"))),
            poll_interval_seconds=max(0.1, float(env.get("COMFY_POLL_INTERVAL_SECONDS", "1.0"))),
        )

    @property
    def base_url(self) -> str:
        if self.provider == "REMOTE_STATIC":
            return self.remote_url
        return self.local_url
