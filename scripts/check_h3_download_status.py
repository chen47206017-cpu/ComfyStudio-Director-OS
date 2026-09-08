"""Print the manifest-only H3 download state; never inspects G:\\ComfyUI."""

from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    manifest_path = root / "minimax_h3.download-state.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = manifest.get("artifacts", [])
    counts: dict[str, int] = {}
    for artifact in artifacts:
        status = str(artifact.get("status", "UNKNOWN"))
        counts[status] = counts.get(status, 0) + 1
    print(json.dumps({
        "manifest": str(manifest_path),
        "source_verification": manifest.get("source_verification", {}).get("status"),
        "artifacts": len(artifacts),
        "status_counts": counts,
        "inspection": "manifest_only",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
