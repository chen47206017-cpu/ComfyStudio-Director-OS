"""Read-only runtime evidence probe for the V10.1 Demo.

The probe never starts or stops a process.  It records the two local HTTP
surfaces, verifies the H3 node names exposed by ComfyUI, and writes a Beijing
time manifest whose claim remains PARTIAL until real MP4 evidence exists.
"""

from __future__ import annotations

import hashlib
import json
import socket
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports" / "runs" / "v101_demo_feedback_20260908"
try:
    BEIJING = ZoneInfo("Asia/Shanghai")
except ZoneInfoNotFoundError:
    # Windows Python may not ship tzdata; the business timezone is fixed UTC+8.
    BEIJING = timezone(timedelta(hours=8), name="Asia/Shanghai")
H3_NODES = {
    "MiniMaxH3ReferenceToVideo",
    "MiniMaxH3MotionContextRAM",
    "MiniMaxH3MotionContextDiskJoin",
    "MiniMaxH3MotionContextDiskFinalDecode",
    "MiniMaxH3Extender",
    "MiniMaxH3TailFromLatent",
}


def now_beijing() -> str:
    return datetime.now(timezone.utc).astimezone(BEIJING).isoformat(timespec="seconds")


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def http_json(base: str, path: str, timeout: float = 8.0) -> dict:
    url = f"{base.rstrip('/')}/{path.lstrip('/')}"
    request = Request(url, headers={"Accept": "application/json"})
    started = datetime.now(timezone.utc)
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            try:
                body = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                body = {"raw": raw[:1000]}
            return {
                "url": url,
                "status": response.status,
                "ok": 200 <= response.status < 300,
                "elapsed_ms": round((datetime.now(timezone.utc) - started).total_seconds() * 1000, 2),
                "body": body,
            }
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        try:
            body = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            body = {"raw": raw[:1000]}
        return {"url": url, "status": exc.code, "ok": False, "error": str(exc), "body": body}
    except (URLError, TimeoutError, OSError) as exc:
        return {"url": url, "status": None, "ok": False, "error": str(exc), "body": {}}


def listener(port: int) -> dict:
    result = {"port": port, "listening": False, "pids": []}
    try:
        with socket.socket() as sock:
            sock.settimeout(0.5)
            result["listening"] = sock.connect_ex(("127.0.0.1", port)) == 0
    except OSError as exc:
        result["error"] = str(exc)
    try:
        command = [
            "powershell.exe",
            "-NoProfile",
            "-Command",
            f"Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort {port} -State Listen | Select-Object -ExpandProperty OwningProcess",
        ]
        completed = subprocess.run(command, capture_output=True, text=True, timeout=10, check=False)
        result["pids"] = [int(line.strip()) for line in completed.stdout.splitlines() if line.strip().isdigit()]
    except (OSError, subprocess.SubprocessError) as exc:
        result["process_query_error"] = str(exc)
    return result


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    observed_at = now_beijing()
    comfy_stats = http_json("http://127.0.0.1:8189", "/system_stats")
    comfy_info = http_json("http://127.0.0.1:8189", "/object_info")
    studio_routes = {
        "health_live": http_json("http://127.0.0.1:8190", "/api/v10/health/live"),
        "demo_project": http_json("http://127.0.0.1:8190", "/api/v10/demo/project"),
        "shot001_prepare": http_json("http://127.0.0.1:8190", "/api/v10/demo/shots/SHOT001/prepare"),
        "shot002_prepare": http_json("http://127.0.0.1:8190", "/api/v10/demo/shots/SHOT002/prepare"),
        "director": http_json("http://127.0.0.1:8190", "/director/"),
    }
    node_classes = set(comfy_info.get("body", {}).keys()) if isinstance(comfy_info.get("body"), dict) else set()
    h3_nodes = sorted(H3_NODES & node_classes)
    demo_project = studio_routes["demo_project"].get("body", {})
    shots = demo_project.get("shots", []) if isinstance(demo_project, dict) else []
    shot_statuses = {
        str(item.get("id")): item.get("status")
        for item in shots if isinstance(item, dict) and item.get("id")
    }
    manifest = {
        "schema": "comfystudio.v101.runtime-probe.v1",
        "observed_at_beijing": observed_at,
        "business_timezone": "Asia/Shanghai",
        "claim_level": "runtime-verified",
        "status": "PASS" if all(item.get("ok") for item in studio_routes.values()) and len(h3_nodes) == len(H3_NODES) else "PARTIAL",
        "real_mp4": {
            "status": "UNVERIFIED",
            "reason": "本探针只验证服务、Demo 预检和 H3 节点；没有把队列提交当作 MP4 成功。",
        },
        "listeners": {"8189": listener(8189), "8190": listener(8190)},
        "comfy": {
            "system_stats": comfy_stats,
            "object_info": {
                "status": comfy_info.get("status"),
                "ok": comfy_info.get("ok"),
                "node_count": len(node_classes),
                "h3_nodes": h3_nodes,
                "comfyui_version": ((comfy_stats.get("body") or {}).get("system") or {}).get("comfyui_version") if isinstance(comfy_stats.get("body"), dict) else None,
            },
        },
        "studio": studio_routes,
        "demo": {
            "project_id": ((demo_project.get("project") or {}).get("id") if isinstance(demo_project, dict) else None),
            "shot_statuses": shot_statuses,
            "shot001_prepare": studio_routes["shot001_prepare"].get("body", {}).get("status"),
            "shot002_prepare": studio_routes["shot002_prepare"].get("body", {}).get("status"),
        },
        "protected_oracles": {
            "database/version.json": sha256(ROOT / "database" / "version.json"),
            "workflows/capsules/h3_reference_to_video/workflow.api.json": sha256(ROOT / "workflows" / "capsules" / "h3_reference_to_video" / "workflow.api.json"),
        },
    }
    target = REPORT_DIR / "runtime_probe.json"
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0 if manifest["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
