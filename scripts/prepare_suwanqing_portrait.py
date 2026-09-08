"""Create a traceable, pixel-only portrait crop from the supplied character sheet."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image


# Central portrait panel on the supplied 1024x1536 character sheet.  The box
# deliberately excludes the surrounding labels and layout borders.
CROP_BOX = (276, 23, 546, 503)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_portrait(source: Path, output: Path, manifest: Path) -> dict[str, object]:
    source = source.resolve(strict=True)
    if source.suffix.lower() != ".png":
        raise ValueError("source must be a PNG character sheet")

    with Image.open(source) as image:
        width, height = image.size
        left, top, right, bottom = CROP_BOX
        if not (0 <= left < right <= width and 0 <= top < bottom <= height):
            raise ValueError("crop box is outside the supplied character sheet")
        # PIL's crop is a pixel selection only.  Saving as PNG keeps the crop
        # lossless while making no edit to the user-owned source image.
        portrait = image.crop(CROP_BOX)
        output.parent.mkdir(parents=True, exist_ok=True)
        portrait.save(output, format="PNG", optimize=False)

    result: dict[str, object] = {
        "schema_version": 1,
        "asset_id": "SW45_PRIMARY_PORTRAIT_V1",
        "source": {
            "path": str(source),
            "sha256": sha256(source),
            "dimensions": {"width": width, "height": height},
        },
        "derivative": {
            "path": str(output.resolve()),
            "sha256": sha256(output),
            "dimensions": {"width": portrait.width, "height": portrait.height},
            "operation": "pixel_crop_only",
            "crop_box_left_top_right_bottom": list(CROP_BOX),
            "text_policy": "central portrait panel only; surrounding character-sheet text excluded",
        },
        "usage": {
            "character_id": "SW45",
            "allowed_use": "local technical validation",
            "cloud_upload": "requires separate user approval and a user-managed public media URL",
        },
    }
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def create_neutral_control_video(
    portrait: Path,
    output: Path,
    manifest: Path,
    comfy_url: str,
) -> dict[str, object]:
    """Create a 121-frame neutral control MP4 through existing ComfyUI nodes.

    This uses only image scaling, batch repetition, and VideoHelperSuite's
    encoder. It does not select or load a diffusion model.
    """
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "src"))
    from comfyui_production.client import ComfyUIClient  # noqa: PLC0415

    portrait = portrait.resolve(strict=True)
    client = ComfyUIClient(comfy_url, timeout=30.0)
    uploaded = client.upload_file(portrait, overwrite=True)
    filename = uploaded.get("name") or uploaded.get("filename")
    subfolder = uploaded.get("subfolder") or ""
    if not isinstance(filename, str) or not filename:
        raise ValueError("ComfyUI upload did not return a filename")
    uploaded_path = "/".join(part for part in (str(subfolder).strip("/"), filename.strip("/")) if part)
    graph = {
        "1": {"class_type": "LoadImage", "inputs": {"image": uploaded_path}},
        "2": {
            "class_type": "ImageScale",
            "inputs": {
                "image": ["1", 0],
                "upscale_method": "lanczos",
                "width": 432,
                "height": 768,
                "crop": "center",
            },
        },
        "3": {"class_type": "RepeatImageBatch", "inputs": {"image": ["2", 0], "amount": 121}},
        "4": {
            "class_type": "VHS_VideoCombine",
            "inputs": {
                "images": ["3", 0],
                "frame_rate": 24,
                "loop_count": 0,
                "filename_prefix": "suwanqing45_neutral_control",
                "format": "video/nvenc_h264-mp4",
                "pingpong": False,
                "save_output": True,
                "save_metadata": True,
                "trim_to_audio": False,
                "use_audio": False,
                "batch_manager": None,
            },
        },
    }
    queued = client.queue_prompt(graph)
    prompt_id = str(queued["prompt_id"])
    history: dict[str, object] = {}
    for event in client.iter_progress(prompt_id, poll_interval=0.5, timeout=120.0):
        entry = event.get("entry") if isinstance(event, dict) else None
        if isinstance(entry, dict):
            history = entry
    if not history:
        history = client.history(prompt_id).get(prompt_id, {})
    outputs = history.get("outputs", {}) if isinstance(history, dict) else {}
    video: dict[str, object] | None = None
    for node in outputs.values() if isinstance(outputs, dict) else []:
        for item in node.get("gifs", []) if isinstance(node, dict) else []:
            if isinstance(item, dict) and str(item.get("filename", "")).lower().endswith(".mp4"):
                video = item
                break
        if video:
            break
    if not video:
        raise ValueError("ComfyUI did not produce a neutral control MP4")
    target_filename = str(video["filename"])
    target_subfolder = str(video.get("subfolder") or "")
    target_type = str(video.get("type") or "output")
    output.parent.mkdir(parents=True, exist_ok=True)
    client.download_view(target_filename, target_subfolder, target_type, output)
    result: dict[str, object] = {
        "schema_version": 1,
        "asset_id": "SW45_NEUTRAL_CONTROL_VIDEO_V1",
        "source_portrait": {"path": str(portrait), "sha256": sha256(portrait)},
        "output": {"path": str(output.resolve()), "sha256": sha256(output)},
        "execution": {
            "comfy_url": comfy_url,
            "prompt_id": prompt_id,
            "graph": "LoadImage -> ImageScale -> RepeatImageBatch(121) -> VHS_VideoCombine(24fps)",
            "model_loading": "none",
        },
    }
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Prepare traceable SW45 local input assets")
    subparsers = parser.add_subparsers(dest="command", required=True)
    portrait_parser = subparsers.add_parser("portrait", help="create the lossless single-person PNG crop")
    portrait_parser.add_argument("--source", type=Path, required=True, help="user-owned PNG character sheet")
    portrait_parser.add_argument(
        "--output",
        type=Path,
        default=root / "sample_assets" / "normalized" / "suwanqing45_primary_portrait.png",
    )
    portrait_parser.add_argument(
        "--manifest",
        type=Path,
        default=root / "sample_assets" / "manifests" / "suwanqing45_primary_portrait.json",
    )
    control_parser = subparsers.add_parser("neutral-control", help="make a self-derived static control MP4")
    control_parser.add_argument(
        "--portrait",
        type=Path,
        default=root / "sample_assets" / "normalized" / "suwanqing45_primary_portrait.png",
    )
    control_parser.add_argument(
        "--output",
        type=Path,
        default=root / "sample_assets" / "normalized" / "suwanqing45_neutral_control.mp4",
    )
    control_parser.add_argument(
        "--manifest",
        type=Path,
        default=root / "sample_assets" / "manifests" / "suwanqing45_neutral_control.json",
    )
    control_parser.add_argument("--comfy-url", default="http://127.0.0.1:8188")
    args = parser.parse_args(argv)
    try:
        if args.command == "portrait":
            result = build_portrait(args.source, args.output, args.manifest)
        else:
            result = create_neutral_control_video(args.portrait, args.output, args.manifest, args.comfy_url)
    except (OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2
    output_key = "derivative" if "derivative" in result else "output"
    print(json.dumps({"ok": True, "asset_id": result["asset_id"], "output": result[output_key]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
