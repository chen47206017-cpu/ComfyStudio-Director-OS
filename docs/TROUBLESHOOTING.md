# Troubleshooting

## Integration API is not reachable

Run (use the live port when it differs from the default):

~~~powershell
powershell -ExecutionPolicy Bypass -File F:\一人公司\comfyui-production\scripts\check_comfyui_api.ps1
~~~

If it fails, inspect:

- F:\一人公司\comfyui-production\runtime\comfyui-api.log
- F:\一人公司\comfyui-production\runtime\comfyui-api.err.log

The configured default is port 8092, the listener with the H3 catalog and
no-I/O dry-run route. The observed 8091 listener is health-only and is
rejected by the normal capability check. Use
`check_comfyui_api.ps1 -Port 8092`, or set `COMFY_API_PORT` consistently for
the start and check commands. Do not stop, replace, or mutate either listener
based on this observation. The integration server intentionally rejects
non-loopback bindings.

## ComfyUI health fails

Confirm http://127.0.0.1:8188/system_stats responds locally. Do not change
the binding to 0.0.0.0 as a workaround. Use the ComfyUI launch script that
binds only 127.0.0.1.

## Workflow rejects a node or model

Use custom_nodes.lock.json, models.manifest.json, and comfyui.snapshot.json
to compare node class, model filename, and runtime version.
Wan22FunControlToVideo is not valid in the observed Wan2.1 runtime, so do not
substitute it into the verified graph.

## MiniMax H3 is not installed yet

`MINIMAX_H3` is intentionally split into `BLOCKED_LOCAL_H3` and
`DRY_RUN_ONLY`. Use `GET /api/comfyui/engines` and
`POST /api/comfyui/h3/dry-run` to inspect/select the AutoDL wrapper. A direct
`POST /api/comfyui/jobs` request using `MINIMAX_H3` or a `minimax_h3_*` ID is
expected to return HTTP 409; this is a paid-call guard, not a node failure.

At handoff, the user reported the user-managed Ref2VA download as
active/deferred. Until the user confirms that its PowerShell prompt returned,
do not stop it, change Clash Verge, inspect the growing file, compute a hash,
or infer full H3 installation from its presence. After that confirmation, run
the guarded status check and then separately verify every H3 component and
node.

## AutoDL paid-call guard and timeout

`POST /api/comfyui/h3/dry-run` is always a no-I/O planner. Real
`AUTODL_COMFYUI` jobs are disabled unless the server environment explicitly
sets `AUTODL_ALLOW_PAID_SUBMIT=1`; a missing or non-object `body` returns HTTP
422 and cannot be replaced by the integration request envelope. AutoDL polling
is bounded by `AUTODL_POLL_TIMEOUT_SECONDS` (default 1800). A timeout is stored
as `NEEDS_REVIEW` with `task_id` because the remote task may still be running;
do not treat local cancel or retry as remote cancellation.

## Distinguish Wan history from the completed smoke retry

The 5.04-second 432x768 MP4 in `docs/LOCAL_WAN21_I2V_VALIDATION.md` is a
historical technical pass. The later tokenized job
`d14f40680fe241b6a91a2258d5cccaab` (prompt
`d6f31d60-bee3-47a7-8f51-357c0c2739a1`) is `SUCCEEDED` with a mirrored MP4
and per-job QA record; do not submit another copy automatically. The earlier job
`b339fe04a2f34875bf9743fad8727d39` failed from CPU memory pressure on
`dpmpp_3m_sde`; its failure must not be confused with the active retry.
The completed smoke output is 432x768, has no burned subtitles, and failed its
visual/delivery gate. It remains smoke-only rather than final 1080x1920
delivery.

## A job remains NEEDS_REVIEW

NEEDS_REVIEW means the provider completed ambiguously, an artifact failed to
mirror locally, or visual/identity quality needs a person to decide. It is not
a successful final render. Review job progress, output metadata, and extracted
frames before retrying.

## Cloud transfer seems proxied or fails

The AutoDL client creates an explicit no-proxy opener. Check that the network
can directly reach the configured cloud host. Do not enable a proxy as a
workaround for a secret-bearing cloud request without reviewing the security
boundary first.
