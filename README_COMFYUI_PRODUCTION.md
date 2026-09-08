# ComfyUI Production Integration

This directory is a local-first integration layer for the existing
G:\ComfyUI installation. It does not replace the existing Seedance service
or modify the ComfyUI application and its model directories.

## Delivered baseline

- ComfyUI is used at http://127.0.0.1:8188.
- The production integration API defaults to the managed H3-capable loopback
  listener at http://127.0.0.1:8092. The port audit found a second health-only
  listener at 8091; keep both untouched and do not treat health alone as route
  parity. Use `COMFY_API_PORT` or `-Port` only when deliberately selecting a
  listener, and require the catalog plus dry-run capability check.
- LOCAL, REMOTE_STATIC, and AUTODL_COMFYUI are selected through one provider
  interface.
- A historical Wan2.1 API validation completed a real 5.04-second 432x768 MP4
  using F:\AI短剧\苏晚晴45.png. That artifact is a technical baseline only;
  visual review found grain, facial distortion, and identity drift, so it is
  not accepted as a final drama shot.
- The tokenized local Wan retry completed as `SUCCEEDED` (`job_id`
  `d14f40680fe241b6a91a2258d5cccaab`, ComfyUI `prompt_id`
  `d6f31d60-bee3-47a7-8f51-357c0c2739a1`). Its mirrored output is 121 frames,
  24 fps, 5.04 seconds, and 432x768 with SHA-256
  `f148c6a6bf1bee170f70d04960622fbc456630b4a7a0622fba373cacd6a2b0ae`.
  The execution is `SMOKE_ONLY` and `REJECTED_FOR_DELIVERY`: it is below
  1080x1920, has visible overprocessed/grainy facial detail, little motion,
  and no burned subtitle evidence. See its per-job `qa.json`.
- MiniMax H3 remains `BLOCKED_LOCAL_H3` locally and `DRY_RUN_ONLY` for AutoDL.
  The user-managed Ref2VA transfer is still deferred; it is not evidence that
  the complete H3 model, nodes, encoders, VAEs, or LoRA are installed.

The machine-written render metadata says 2026-09-04T00:17:22+08:00, which
is in the future relative to this delivery's 2026-09-03 task date. Treat it
as a machine clock/report timestamp, not evidence that the render occurred
after this delivery.

## Start and check

1. Start the existing local ComfyUI server with its dedicated loopback launch
   script.
2. Start the integration API. Omitting `-Port` uses `COMFY_API_PORT` from the
   process or project `.env` (8092 by default). The launcher first verifies the
   selected listener's H3 catalog and no-I/O dry-run route; it refuses to
   replace a health-only listener:

~~~powershell
powershell -ExecutionPolicy Bypass -File F:\一人公司\comfyui-production\scripts\start_comfyui_api.ps1 -Port 8092 -Wait
~~~

3. Check the selected integration API port. A successful check proves health,
   the `MINIMAX_H3` catalog entry, and a `DRY_RUN_ONLY` plan with no vendor
   task ID:

~~~powershell
powershell -ExecutionPolicy Bypass -File F:\一人公司\comfyui-production\scripts\check_comfyui_api.ps1 -Port 8092
~~~

The API accepts POST /api/comfyui/jobs, exposes job progress at
GET /api/comfyui/jobs/{job_id}, and supports local cancel/retry plus output
download. AutoDL jobs cannot be remotely cancelled through the documented
workflow API. MiniMax H3 is exposed through GET /api/comfyui/engines and
POST /api/comfyui/h3/dry-run only; it does not submit a paid cloud request.
See docs/WORKFLOW_CATALOG.md, docs/H3_WORKFLOW.md, and
docs/AUTODL_COMFYUI_API.md.

The preset catalog is served by the running API process, not read directly
from this source file. If a previously started 8092 process still reports an
older resolution such as 576x1024, treat that response as stale runtime
evidence; reload that managed process in an explicitly approved maintenance
window, then rerun the capability and preset checks before claiming the
1080x1920 contract is active.

## Configuration

Copy the safe placeholders in .env.example to a local `.env`, or set
equivalent process environment variables. The project reads `.env` as a
fallback and gives process environment variables priority. Keep real cloud
tokens only in your local environment or credential store. Do not put them in
workflows, source files, task JSON, screenshots, or logs.

The control layer did not download, move, or delete model files. At handoff,
the user reported a PowerShell process writing the H3 Ref2VA weight under
`G:\ComfyUI\models`; until the user confirms that transfer has naturally
ended, it must not be stopped, restarted, read, hashed, moved, renamed, or
loaded. The H3 download manifest therefore remains `PENDING` / `DEFERRED`.
The other H3 components and nodes still require separate source, integrity,
compatibility, and inference checks.

The API preset `CLOUD_5090_QUALITY` is a final-delivery target of 1080x1920,
24 fps, 121 frames (about 5.04 seconds), 9:16, with `SUBTITLE_LOCK_V1`
burning required. It is a target contract, not evidence that a cloud render
has already run. `LOCAL_DRAFT` remains a low-resolution technical smoke mode.
The installed Wan2.1 baseline is recorded in models.manifest.json; planned
final-quality models remain unverified.

## Key documents

- docs/COMFYUI_AUDIT.md
- docs/DISK_AND_RUNTIME_PLAN.md
- docs/WORKFLOW_CATALOG.md
- docs/ASSET_PREPARATION.md
- docs/CLOUD_5090.md
- docs/TROUBLESHOOTING.md
- docs/BENCHMARK_REPORT.md
- docs/LOCAL_WAN21_I2V_VALIDATION.md
