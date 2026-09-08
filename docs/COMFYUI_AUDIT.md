# ComfyUI Audit

Audit date: 2026-09-03. This was a read-only audit of the user-provided
paths F:\一人公司, F:\AI短剧, and G:\ComfyUI.

## Observed runtime

| Item | Observed value |
| --- | --- |
| ComfyUI root | G:\ComfyUI |
| ComfyUI version | 0.27.0 |
| Local address | 127.0.0.1:8188 |
| GPU | NVIDIA GeForce RTX 5060 Ti |
| GPU memory | 16311 MiB |
| NVIDIA driver | 610.88 |
| ComfyUI Python | 3.12.10 |
| PyTorch | 2.11.0+cu128 |
| CUDA runtime reported by PyTorch | 12.8 |
| ComfyUI-Manager | installed, package version 3.41 |
| VideoHelperSuite | installed, version 1.7.9 |

G:\ComfyUI has an empty or otherwise unusable .git directory, so a core
ComfyUI commit could not be established. The installed version string and
runtime package snapshot are recorded in comfyui.snapshot.json instead.

## Models and nodes

The local 5-second baseline uses:

- Wan2.1 I2V 14B FP8 scaled diffusion model
- UMT5 XXL FP8 text encoder
- Wan 2.1 VAE
- CLIP Vision H
- ComfyUI core WanFunControlToVideo
- VideoHelperSuite VHS_LoadVideo and VHS_VideoCombine

Exact observed file names, sizes, and node revisions are in
models.manifest.json and custom_nodes.lock.json.

## What was not changed

- No existing ComfyUI source, model, custom node, or model path was changed.
- No model was downloaded, moved, or deleted.
- No cloud instance was created and no paid task was submitted.
- No existing 8080 Seedance service was inspected or modified.

## Remaining verification

The following target models/workflows are not currently installed and must not
be represented as runnable: Qwen Image Edit 2511, LTX 2.5, Wan2.2 Fun
Control, and Wan2.2 Animate. Their installation needs explicit model-source,
license, storage, and download authorization review.

