# Web Integration Contract

The existing Web management page can call the loopback service. The configured
default is the H3-capable listener at http://127.0.0.1:8092. A separate
health-only listener was observed at 8091; health status alone is insufficient
for management-page routing. Read `COMFY_API_PORT` (or pass the selected port
to the check script), and require the engine catalog plus no-I/O dry-run probe.
The page must not send cloud credentials to the browser.

## Routes

| Method | Route | Purpose |
| --- | --- | --- |
| GET | /api/comfyui/health | Local provider and integration health |
| GET | /api/comfyui/workflows | Registered runnable API workflows |
| GET | /api/comfyui/engines | Logical engine selectors, including MiniMax H3 availability |
| GET | /api/comfyui/presets | LOCAL_DRAFT and CLOUD_5090_QUALITY choices |
| GET | /api/comfyui/jobs | Recent jobs |
| POST | /api/comfyui/jobs | Submit a job |
| GET | /api/comfyui/jobs/{job_id} | Job status, progress, metadata, artifacts |
| POST | /api/comfyui/jobs/{job_id}/cancel | Request cancellation |
| POST | /api/comfyui/jobs/{job_id}/retry | Retry a terminal job when its redacted request is still safe to replay |
| GET | /api/comfyui/jobs/{job_id}/outputs | List output artifact metadata |
| GET | /api/comfyui/jobs/{job_id}/outputs/{filename} | Download a mirrored artifact |
| POST | /api/comfyui/h3/dry-run | Validate and select an H3 AutoDL wrapper without making an HTTP request |

The API only permits loopback origins. Output files are downloaded from a
per-job artifact directory, not exposed directly from G:\ComfyUI.

## Submission body

~~~json
{
  "provider": "LOCAL",
  "workflow_id": "wan2.1_i2v_ref_5s_local",
  "inputs": {
    "prompt": "A woman pauses in a quiet apartment hallway.",
    "negative_prompt": "face distortion",
    "seed": 20260903
  },
  "media": {
    "character_a_image": {
      "path": "F:\\AI短剧\\character_a.png",
      "media_type": "image"
    }
  },
  "options": {
    "preset": "LOCAL_DRAFT"
  }
}
~~~

For AUTODL_COMFYUI, use the body field for the exact authenticated
workflow-specific schema. The generic server does not invent vendor
image/audio field names. MiniMax H3 is currently guarded: requests using
`engine: "MINIMAX_H3"` or a `minimax_h3_*` workflow ID on
`POST /api/comfyui/jobs` return HTTP 409. Use `POST /api/comfyui/h3/dry-run`
instead. The planner selects `minimax_h3_lightx2v_v5` for reference images
and `minimax_h3_image_audio_to_video_v2` when reference audio is present; the
dry-run performs no vendor request and cannot incur cloud charges. Both IDs
are marked `USER_SUPPLIED_UNVERIFIED`; render `planning_input` as an intent
summary, not as a ready-to-submit vendor body, and show
`BLOCKED_PENDING_SCHEMA_EVIDENCE` until a current workflow drawer schema has
been captured. See `docs/H3_WORKFLOW.md` for the URL-only planner contract.

## UI behavior

Show one of these durable states: QUEUED, RUNNING, SUCCEEDED, FAILED,
CANCELLED, or NEEDS_REVIEW. Treat NEEDS_REVIEW as unresolved rather than
success. Persist the job ID, provider, workflow hash, prompt/task ID,
redacted inputs, seed, and artifact checksum supplied by the server.

Poll the job route while a job is QUEUED or RUNNING. WebSocket-like progress
from native ComfyUI is consumed by the backend; the existing page does not
need a direct public ComfyUI WebSocket connection.

The historical Wan2.1 artifact remains distinct from the tokenized retry.
Job `d14f40680fe241b6a91a2258d5cccaab` with prompt ID
`d6f31d60-bee3-47a7-8f51-357c0c2739a1` reached `SUCCEEDED` and has its own
workflow hash, input lineage, output hash, and QA file. Its API state is
technical completion only: UI must present it as `SMOKE_ONLY` /
`REJECTED_FOR_DELIVERY`, not as a final 1080x1920 subtitle-burned shot.
