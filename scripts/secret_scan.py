"""Scan project text files for likely committed credentials without echoing them."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


TEXT_SUFFIXES = {".env", ".example", ".json", ".md", ".ps1", ".py", ".txt", ".yaml", ".yml"}
SKIP_PARTS = {".git", "__pycache__", "artifacts"}
ENV_ASSIGN_RE = re.compile(
    r"^\s*(?:export\s+)?([A-Z][A-Z0-9_]*(?:TOKEN|SECRET|PASSWORD|PASSWD|API_KEY)[A-Z0-9_]*)\s*[:=]\s*(.+?)\s*$"
)
QUOTED_SECRET_RE = re.compile(
    r"(?i)[\"'](?:api[_-]?key|token|secret|password|passwd|authorization)[\"']\s*[:=]\s*[\"']([^\"']+)[\"']"
)
TOKEN_RE = re.compile(r"(?i)\b(?:bearer\s+[a-z0-9._~-]{16,}|hf_[a-z0-9]{20,}|sk-[a-z0-9_-]{20,})\b")
PLACEHOLDER_VALUES = {"", "[redacted]", "<token>", "your_token", "your-token", "changeme", "example"}


def should_scan(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    if any(part in SKIP_PARTS for part in relative.parts):
        return False
    if path.name == ".env":
        return False
    # The scanner's own regular expressions necessarily contain words such as
    # ``token`` and ``secret``; inspecting that source would report itself.
    if path.name == "secret_scan.py":
        return False
    return path.suffix.lower() in TEXT_SUFFIXES or path.name.endswith(".env.example")


def findings_for(path: Path) -> list[tuple[int, str]]:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    findings: list[tuple[int, str]] = []
    for number, line in enumerate(lines, start=1):
        value_match = ENV_ASSIGN_RE.match(line) or QUOTED_SECRET_RE.search(line)
        if value_match:
            value = value_match.group(value_match.lastindex or 1).strip().strip("\"'").lower()
            if value not in PLACEHOLDER_VALUES and not value.startswith("${"):
                findings.append((number, "credential-like key has a non-placeholder value"))
                continue
        if TOKEN_RE.search(line):
            findings.append((number, "token-like literal"))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report likely project secrets without printing values")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]), help="project root to inspect")
    args = parser.parse_args(argv)
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print("error: scan root is not a directory")
        return 2

    scanned = 0
    findings: list[tuple[Path, int, str]] = []
    for path in root.rglob("*"):
        if not path.is_file() or not should_scan(path, root):
            continue
        scanned += 1
        for line, reason in findings_for(path):
            findings.append((path.relative_to(root), line, reason))
    if findings:
        for path, line, reason in findings:
            print(f"{path}:{line}: {reason}")
        print(f"Potential secrets found in {len(findings)} location(s); values were not printed.")
        return 1
    print(f"No potential secrets found in {scanned} text file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
