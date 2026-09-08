# Disk And Runtime Plan

## Storage boundary

G: was read-only audited as exFAT. It is appropriate for large model weights
that are treated as read-mostly, but it is a poor home for Git metadata,
Python virtual environments, caches, or source changes.

The system denied this task's filesystem probe for F:. Therefore the expected
NTFS status of F: is not asserted as a runtime fact in this delivery. The
project already lives on F:\一人公司\comfyui-production; confirm NTFS in an
administrator or normal desktop session before relocating an environment.

## Current layout

| Area | Path | Role |
| --- | --- | --- |
| Existing ComfyUI program | G:\ComfyUI | Existing local runtime, left unchanged |
| Existing model weights | G:\ComfyUI\models | Existing read-mostly weights |
| Integration source and artifacts | F:\一人公司\comfyui-production | API, configs, docs, task records |
| Allowed user media | F:\AI短剧 | Reference images, driving videos, audio |

## Recommended future layout

When F: is confirmed NTFS, keep the Python virtual environment, Git clone,
custom nodes, job store, uploads, cache, and logs on F:. Keep large read-only
model weights on G: and reference them through extra_model_paths.yaml. Do not
move current weights until there is a verified rollback plan.

## Network boundary

Both local services must remain loopback-only:

- ComfyUI: 127.0.0.1:8188
- Integration API default: 127.0.0.1:8092 (the H3-capable managed listener)
- A separate health-only responder was observed at 127.0.0.1:8091; both
  listeners remain untouched and health-only responses are not route parity.

The responding ports are runtime facts for this delivery, not public bindings
or authorization to remove a listener. Keep the API on loopback and pass the
selected port consistently to the start/check scripts; do not expose either
service to `0.0.0.0`.

For a cloud instance, use an authenticated provider endpoint, SSH tunnel,
Tailscale, or an authenticated reverse proxy. Do not expose a raw ComfyUI
port publicly.

## H3 transfer boundary

At handoff, the user reported a MiniMax H3 Ref2VA file being written below
`G:\ComfyUI\models`. Until the user confirms that its PowerShell process
returned to a prompt, the file is outside the inspection scope: do not read,
hash, move, rename, load, replace, or restart the transfer, and do not change
Clash Verge or proxy settings. The project manifest remains `PENDING` /
`DEFERRED`; the other H3 weights and nodes are not implied to be installed.
After the completion gate, perform a separate integrity/source/compatibility
audit before refreshing ComfyUI's model list.

## Runtime evidence boundary

The historical Wan2.1 5.04-second 432x768 artifact is retained as a technical
baseline. The later tokenized retry is job
`d14f40680fe241b6a91a2258d5cccaab` with prompt
`d6f31d60-bee3-47a7-8f51-357c0c2739a1`; it completed with a 6,783,311-byte
mirrored MP4 and per-job QA. Keep these records separate when calculating
storage, cleanup, or delivery readiness. The retry is still smoke-only and
rejected for final delivery because it is 432x768, lacks subtitle proof, and
did not pass visual quality review.
