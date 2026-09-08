# MiniMax H3 Selector

`MINIMAX_H3` is a single logical selector for multi-reference H3 planning. It
does not make the local ComfyUI server execute H3 and it does not submit an
AutoDL task.

## Availability

| Target | Status | Meaning |
| --- | --- | --- |
| Local ComfyUI | `BLOCKED_LOCAL_H3` | The current local runtime has no native H3 node contract. |
| AutoDL H3 | `DRY_RUN_ONLY` | The API validates project planning input and selects a candidate wrapper ID, but performs no HTTP request or vendor field mapping. |

The catalog is available from `GET /api/comfyui/engines`, so a management page
can offer one engine selection rather than a raw workflow-id chooser. The
existing preset list is intentionally unchanged for backward compatibility.

## Dry Run

Call `POST /api/comfyui/h3/dry-run` with the unified input shape:

```json
{
  "engine": "MINIMAX_H3",
  "prompt": "live-action close-up; preserve the reference identity",
  "duration": 5,
  "resolution": "768p\u7ad6",
  "reference_images": [
    "https://media.example.invalid/character.png"
  ],
  "reference_audios": []
}
```

The planner selects `minimax_h3_lightx2v_v5` for images only and
`minimax_h3_image_audio_to_video_v2` when reference audio is present. Both
IDs have `USER_SUPPLIED_UNVERIFIED` schema status. The response contains a
redacted `planning_input` plus a `vendor_submission` block with
`BLOCKED_PENDING_SCHEMA_EVIDENCE`; it does not map arrays to vendor fields or
produce a submittable request body.

All references must be hosted HTTP(S) URLs. The dry-run rejects local `F:` and
`G:` paths, literal private addresses, and localhost; it does not perform DNS
or reachability checks. It accepts project planning values of 1-15 seconds,
480p/768p vertical or horizontal source preference, up to nine images, and up
to three audio references. These are local planning limits, not a verified
legacy AutoDL request schema. Unknown planner fields and reference video are
rejected rather than silently being discarded. A native cloud H3 R2V graph is
a separate, unverified future capability.

The production target remains 1080x1920, 24fps, about five seconds, with
`SUBTITLE_LOCK_V1` burned in. The unverified legacy H3 source wrapper must not
be represented as direct 1080p; delivery needs a separately verified direct
renderer or validated upscale after the source workflow is proven.

Requests that explicitly set `engine: "MINIMAX_H3"`, or any
`minimax_h3_*` workflow ID, on `POST /api/comfyui/jobs` are rejected with HTTP
409 and directed to the dry-run route. This API-level guard prevents an
accidental paid H3 render while the selector remains dry-run only.

## Native Cloud Follow-up

After an explicitly authorized cloud test, native H3 R2V needs a ComfyUI
version with the H3 node set, a separate audiovisual latent/decode chain, and
the correct ref2va model family. It must not be joined to the existing Wan
latent graph or advertised as a local option until a real run passes.
