"""Read-only validator for authored SUBTITLE_LOCK_V1 ASS files."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any


EXPECTED_FONTS = {
    "Primary": "Source Han Sans CN Medium",
    "PrimarySemibold": "Source Han Sans CN SemiBold",
}
STYLE_FIELDS = [
    "Name", "Fontname", "Fontsize", "PrimaryColour", "SecondaryColour",
    "OutlineColour", "BackColour", "Bold", "Italic", "Underline", "StrikeOut",
    "ScaleX", "ScaleY", "Spacing", "Angle", "BorderStyle", "Outline", "Shadow",
    "Alignment", "MarginL", "MarginR", "MarginV", "Encoding",
]
EVENT_FIELDS = ["Layer", "Start", "End", "Style", "Name", "MarginL", "MarginR", "MarginV", "Effect", "Text"]
TIME_RE = re.compile(r"^(\d+):(\d{1,2}):(\d{2})\.(\d{2})$")
TAG_RE = re.compile(r"\{[^}]*\}")
FORBIDDEN_OVERRIDE_RE = re.compile(
    r"\\(?:1c|2c|3c|4c|c|alpha|1a|2a|3a|4a|a|t|fad|fade|move|pos|org|clip|iclip|"
    r"an|fs|fn|bord|xbord|ybord|shad|xshad|yshad|blur|be|b|i|u|s|q|r|p|K|k|kf|ko)",
    re.IGNORECASE,
)


def _sections(lines: list[str]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    section = ""
    for raw in lines:
        line = raw.strip("\ufeff\r\n")
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip().lower()
            result.setdefault(section, [])
        elif section:
            result[section].append(line)
    return result


def _format(lines: list[str], fallback: list[str]) -> list[str]:
    for line in lines:
        if line.lower().startswith("format:"):
            return [part.strip() for part in line.split(":", 1)[1].split(",")]
    return fallback


def _color(value: str) -> tuple[int, int, int, float] | None:
    match = re.fullmatch(r"&H([0-9A-Fa-f]{8})", value.strip())
    if not match:
        return None
    raw = match.group(1)
    alpha, blue, green, red = (int(raw[i : i + 2], 16) for i in range(0, 8, 2))
    return red, green, blue, 1.0 - alpha / 255.0


def _time(value: str) -> float | None:
    match = TIME_RE.fullmatch(value.strip())
    if not match:
        return None
    hours, minutes, seconds, centiseconds = (int(item) for item in match.groups())
    if minutes >= 60 or seconds >= 60:
        return None
    return hours * 3600 + minutes * 60 + seconds + centiseconds / 100


def _font_dirs() -> list[Path]:
    result: list[Path] = []
    root = os.environ.get("WINDIR") or os.environ.get("SystemRoot")
    if root:
        result.append(Path(root) / "Fonts")
    local = os.environ.get("LOCALAPPDATA")
    if local:
        result.append(Path(local) / "Microsoft" / "Windows" / "Fonts")
    return result


def _source_han_present() -> bool:
    needles = ("sourcehan", "source han", "思源")
    for directory in _font_dirs():
        try:
            if any(any(needle in item.name.lower() for needle in needles) for item in directory.iterdir()):
                return True
        except OSError:
            continue
    return False


def _visible_lines(text: str) -> list[str]:
    return re.split(r"\\[Nn]", TAG_RE.sub("", text))


def validate(
    path: Path,
    *,
    allow_empty: bool = False,
    require_source_han: bool = False,
    max_line_chars: int = 16,
    video_width: int | None = None,
    video_height: int | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings = [
        "ASS v4+ has no dedicated line-spacing field; verify 8-12 px visually after burn.",
        "ASS Shadow is an offset, not a blurred-shadow layer; verify the weak shadow visually.",
    ]
    report: dict[str, Any] = {
        "ok": False, "path": str(path.expanduser().resolve()), "errors": errors,
        "warnings": warnings, "playres": None, "styles": {}, "dialogue_count": 0,
        "font_check": "not_requested",
    }
    try:
        text = path.expanduser().resolve(strict=True).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        errors.append(f"cannot read ASS file: {exc}")
        return report
    sections = _sections(text.splitlines())
    info = sections.get("script info", [])
    style_lines = sections.get("v4+ styles", [])
    event_lines = sections.get("events", [])
    if not info:
        errors.append("missing [Script Info] section")
    if not style_lines:
        errors.append("missing [V4+ Styles] section")
    if not event_lines:
        errors.append("missing [Events] section")
    info_values: dict[str, str] = {}
    for line in info:
        if ":" in line and not line.startswith(";"):
            key, value = line.split(":", 1)
            info_values[key.strip().lower()] = value.strip()
    try:
        width, height = int(info_values["playresx"]), int(info_values["playresy"])
        report["playres"] = {"width": width, "height": height}
        if (width, height) != (1080, 1920):
            errors.append(f"PlayRes must be 1080x1920, got {width}x{height}")
        if video_width is not None and video_height is not None and (width, height) != (video_width, video_height):
            errors.append(f"video dimensions must match ASS PlayRes {width}x{height}, got {video_width}x{video_height}")
    except (KeyError, ValueError):
        errors.append("PlayResX and PlayResY must be integer values")
    if info_values.get("wrapstyle") != "2":
        errors.append("WrapStyle must be 2 so only deliberate \\N breaks create a second line")

    styles: dict[str, dict[str, str]] = {}
    fields = _format(style_lines, STYLE_FIELDS)
    if [item.lower() for item in fields] != [item.lower() for item in STYLE_FIELDS]:
        errors.append("[V4+ Styles] Format does not match ASS v4+ fields")
    for line in style_lines:
        if not line.lower().startswith("style:"):
            continue
        values = [item.strip() for item in line.split(":", 1)[1].split(",")]
        if len(values) != len(fields):
            errors.append("style row has the wrong number of fields")
            continue
        row = dict(zip(fields, values))
        name = row.get("Name", "")
        if name in styles:
            errors.append(f"duplicate style: {name}")
        styles[name] = row
    report["styles"] = styles
    for name, font in EXPECTED_FONTS.items():
        row = styles.get(name)
        if row is None:
            errors.append(f"missing required style: {name}")
            continue
        if row.get("Fontname") != font:
            errors.append(f"{name}.Fontname must be {font!r}")
        try:
            size = float(row.get("Fontsize", ""))
            if not 56 <= size <= 64:
                errors.append(f"{name}.Fontsize must be between 56 and 64")
        except ValueError:
            errors.append(f"{name}.Fontsize must be numeric")
        if row.get("PrimaryColour", "").upper() != "&H00FFFFFF":
            errors.append(f"{name}.PrimaryColour must be opaque white (&H00FFFFFF)")
        outline = _color(row.get("OutlineColour", ""))
        if outline is None or outline[:3] != (0, 0, 0) or not 0.80 <= outline[3] <= 0.90:
            errors.append(f"{name}.OutlineColour must be black with 80-90% opacity")
        shadow = _color(row.get("BackColour", ""))
        if shadow is None or shadow[:3] != (0, 0, 0) or not 0.20 <= shadow[3] <= 0.30:
            errors.append(f"{name}.BackColour must be black with 20-30% opacity")
        required = {
            "Italic": "0", "Underline": "0", "StrikeOut": "0", "ScaleX": "100", "ScaleY": "100",
            "Spacing": "0", "Angle": "0", "BorderStyle": "1", "Outline": "4", "Shadow": "1",
            "Alignment": "2", "MarginL": "70", "MarginR": "70", "MarginV": "390",
        }
        for field, expected in required.items():
            if row.get(field) != expected:
                errors.append(f"{name}.{field} must be {expected}")
    if require_source_han:
        report["font_check"] = "source_han_present" if _source_han_present() else "source_han_missing"
        if report["font_check"] == "source_han_missing":
            errors.append("Source Han font files were not found in known Windows font directories")

    event_fields = _format(event_lines, EVENT_FIELDS)
    if [item.lower() for item in event_fields] != [item.lower() for item in EVENT_FIELDS]:
        errors.append("[Events] Format does not match ASS event fields")
    for line_number, line in enumerate(event_lines, start=1):
        if not line.lower().startswith("dialogue:"):
            continue
        values = [item.strip() for item in line.split(":", 1)[1].split(",", 9)]
        if len(values) != 10:
            errors.append(f"Dialogue row {line_number} has the wrong number of fields")
            continue
        report["dialogue_count"] += 1
        _layer, start, end, style, _name, margin_l, margin_r, margin_v, effect, subtitle_text = values
        if _time(start) is None or _time(end) is None or _time(end) <= _time(start):
            errors.append(f"Dialogue row {line_number} has invalid or non-increasing times")
        if style not in EXPECTED_FONTS:
            errors.append(f"Dialogue row {line_number} must use Primary or PrimarySemibold")
        if (margin_l, margin_r, margin_v) != ("0", "0", "0"):
            errors.append(f"Dialogue row {line_number} must keep event margins at 0 to preserve the locked style position")
        if effect:
            errors.append(f"Dialogue row {line_number} must not use an animated/scrolling Effect")
        if FORBIDDEN_OVERRIDE_RE.search(subtitle_text):
            errors.append(f"Dialogue row {line_number} contains a visual/position/animation override")
        visible_lines = _visible_lines(subtitle_text)
        if not TAG_RE.sub("", subtitle_text).strip():
            errors.append(f"Dialogue row {line_number} has empty text")
        if len(visible_lines) > 2:
            errors.append(f"Dialogue row {line_number} exceeds the two-line limit")
        for line_index, visible_line in enumerate(visible_lines, start=1):
            count = sum(1 for char in visible_line if not char.isspace())
            if count > max_line_chars:
                errors.append(f"Dialogue row {line_number} line {line_index} exceeds {max_line_chars} characters")
    if report["dialogue_count"] == 0 and not allow_empty:
        errors.append("authored ASS must contain at least one active Dialogue row")
    report["ok"] = not errors
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a SUBTITLE_LOCK_V1 ASS file without rendering")
    parser.add_argument("subtitle", type=Path)
    parser.add_argument("--allow-empty", action="store_true")
    parser.add_argument("--require-source-han", action="store_true")
    parser.add_argument("--max-line-chars", type=int, default=16)
    parser.add_argument("--video-width", type=int)
    parser.add_argument("--video-height", type=int)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.max_line_chars < 1:
        parser.error("--max-line-chars must be positive")
    if (args.video_width is None) != (args.video_height is None):
        parser.error("--video-width and --video-height must be provided together")
    if args.video_width is not None and (args.video_width < 1 or args.video_height < 1):
        parser.error("video dimensions must be positive")
    report = validate(
        args.subtitle,
        allow_empty=args.allow_empty,
        require_source_han=args.require_source_han,
        max_line_chars=args.max_line_chars,
        video_width=args.video_width,
        video_height=args.video_height,
    )
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(("PASS" if report["ok"] else "FAIL") + ": " + report["path"])
        for message in report["errors"]:
            print("error: " + message)
        for message in report["warnings"]:
            print("warning: " + message)
        print(f"dialogue_count={report['dialogue_count']}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
