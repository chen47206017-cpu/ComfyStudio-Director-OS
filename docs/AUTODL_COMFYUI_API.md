# AutoDL ComfyUI API integration notes

The generic transport below was checked against AutoDL's official `ComfyUI
API` and `Online Call` pages. Those pages state that the request body differs
by workflow and must be read from that workflow's current drawer or online-call
surface. They do not verify a request schema for either user-supplied legacy
H3 workflow ID in this project.

- Submit: `POST https://autodl.art/api/v1/comfyui/comfyui_workflow/{workflow_id}`
- Headers: `Authorization: <ComfyUI token>`, `Content-Type: application/json`.
  The documented authorization value is the token itself; do not add a
  `Bearer ` prefix unless AutoDL changes its contract.
- Submit response: `data.task_id`, `data.status`, `data.client_id`.
- Poll: `GET https://autodl.art/api/v1/comfyui/comfyui_workflow/result/{task_id}` with the same headers.
- The official response envelope includes `code: "Success"` and `data`.
  Poll states documented or shown in the official example are `QUEUED`,
  `RUNNING`, `SUCCESS`, and `FAILED`. The client also normalizes a defensive
  `completed` alias when a vendor response uses it; that is not proof of a
  particular legacy workflow's state list.
- On `SUCCESS`, `data.results` contains short-lived resource URLs. Download
  them immediately, do not persist signed URLs in job records, and retain only
  the local artifact path and safe metadata.
- User-supplied legacy workflow IDs are registered only as selector targets:
  - `minimax_h3_lightx2v_v5` (image-only planning)
  - `minimax_h3_image_audio_to_video_v2` (image-plus-audio planning)
  Both carry `USER_SUPPLIED_UNVERIFIED` schema status and cannot be submitted
  by this project.

The integration must never put a token in source, workflow JSON, logs, or screenshots. Configure it through the project-root `.env` using `AUTODL_API_BASE_URL` and `AUTODL_API_TOKEN`; process environment variables take precedence over `.env` values.

The server-side paid submission gate is disabled by default with
`AUTODL_ALLOW_PAID_SUBMIT=0`. The no-I/O `POST /api/comfyui/h3/dry-run` route is
not affected. A real `POST /api/comfyui/jobs` request must explicitly set that
gate to `1`, provide `body` as a JSON object, and use a separately authorized
budgeted test. Missing, null, list, or string bodies are rejected with HTTP
422 before a job row or provider call is created.

`AutoDLComfyWorkflowClient` fails closed for an invalid response envelope,
missing/unknown task status, or task ID mismatch. It sends requests through an
explicit proxy-disabled opener and downloads result files in chunks to a
temporary sibling file before atomically replacing the final artifact. This
keeps Clash Verge out of media transfers and prevents partial MP4 files from
being treated as completed output.

## H3 schema boundary

The low-level adapter accepts a caller-provided JSON object as `body` and
forwards it exactly; it never substitutes the internal `provider`,
`workflow_id`, `inputs`, `media`, or `options` envelope. This generic adapter
does not make a legacy H3 schema verified.

The unified `MINIMAX_H3` selector is `DRY_RUN_ONLY`. It selects one of the two
user-supplied IDs from the presence of reference audio, returns the redacted
project planning input, and returns `vendor_submission.status` as
`BLOCKED_PENDING_SCHEMA_EVIDENCE`. It does not generate a vendor request body
or invent image/audio field names.

| Workflow ID | Planner condition | Vendor schema status |
| --- | --- | --- |
| `minimax_h3_lightx2v_v5` | One or more reference images, no reference audio | `USER_SUPPLIED_UNVERIFIED` |
| `minimax_h3_image_audio_to_video_v2` | One or more reference images plus reference audio | `USER_SUPPLIED_UNVERIFIED` |

The planner accepts hosted HTTP(S) references and applies local planning caps:
up to 10,000 prompt characters, 1-15 seconds, up to nine images, up to three
audio references, and a 480p/768p vertical or horizontal source preference.
Those are project planner limits, not a vendor payload schema or a promise that
either legacy workflow accepts the same fields. The 1080x1920 final-delivery
target requires a separately verified direct renderer or validated upscale.

Before any H3 submission can be enabled, capture the current selected workflow
drawer schema and retain its source URL, retrieval time, version or hash, and
exact request fields. This local API cannot turn `F:` or `G:` paths into hosted
reference URLs.

The server downloads only URLs found inside the documented `results` field;
it ignores echoed input and metadata URLs. AutoDL has no documented remote
cancel endpoint, so a cancel request for an `AUTODL_COMFYUI` job returns 409
instead of falsely marking a possibly billable render as stopped.

Polling uses `AUTODL_POLL_TIMEOUT_SECONDS` (default 1800 seconds). If the
deadline expires while the task is still non-terminal, the job is marked
`NEEDS_REVIEW` with the vendor `task_id`, `poll_timed_out=true`, and
`remote_may_continue=true`. This is an observation timeout only: the remote
task may still run, cannot be assumed cancelled, and must not be blindly retried.

Example H3 planner input (not a vendor request body):

```json
{
  "prompt": "cinematic live-action close-up, stable identity",
  "duration": 5,
  "resolution": "768p竖",
  "reference_images": ["https://your-media-host.example/reference-0.png"]
}
```

This hosted API is a separate provider from local ComfyUI. The same job schema
can select `LOCAL` or `AUTODL_COMFYUI`; local jobs use actual files and the
ComfyUI `/prompt` API, while future non-H3 AutoDL jobs use an exact
workflow-specific JSON body and short-lived result URLs.
