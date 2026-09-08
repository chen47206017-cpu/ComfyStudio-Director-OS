# Workflow Catalog

## Historical verified local workflow

wan2.1_i2v_ref_5s_local.json is an API graph with a historical successful
execution on the current workstation. That record is separate from the later
tokenized retry in `runtime/jobs.json`.

| Field | Value |
| --- | --- |
| Input image | suwanqing45_ref.png in ComfyUI input |
| Driving video | 10000.mp4 in ComfyUI input |
| Resolution | 432x768 |
| Frame count | 121 |
| Frame rate | 24 |
| Output duration | 5.04 seconds |
| Seed | 20260903 |
| Steps | 24 |
| Output | H.264 NVENC MP4 |

It is a one-image Wan2.1 technical validation graph. It is not a
dual-character identity-binding pipeline and does not satisfy final quality
requirements. The historical artifact must not be used to mark the current
retry as complete.

## Completed tokenized local smoke run

| Field | Value |
| --- | --- |
| Job | `d14f40680fe241b6a91a2258d5cccaab` |
| ComfyUI prompt | `d6f31d60-bee3-47a7-8f51-357c0c2739a1` |
| Status | `SUCCEEDED`, but `SMOKE_ONLY` / `REJECTED_FOR_DELIVERY` |
| Graph | `wan2.1_i2v_ref_5s_local` |
| Output | `wanvideo_suwanqing_ref_5s_local_00002.mp4` |
| Output hash | `f148c6a6bf1bee170f70d04960622fbc456630b4a7a0622fba373cacd6a2b0ae` |
| Media | 432x768, 121 frames, 24 fps, 5.04 seconds, H.264 Main |
| Sampling change | `euler` / `simple` / 16 steps to avoid the prior CPU-memory failure |

The retry reached a terminal ComfyUI history state and has project-local
output metadata, input lineage, checksum, and visual QA in
`runtime/artifacts/d14f40680fe241b6a91a2258d5cccaab/qa.json`. It must not be
automatically retried: despite technical completion, it misses the 1080x1920
delivery requirement, has visible overprocessed/grainy facial detail, shows
very limited motion, and contains no burned subtitle evidence. The earlier
retry `b339fe04a2f34875bf9743fad8727d39` failed at KSampler because the
selected `dpmpp_3m_sde` path exhausted CPU memory; it remains distinct
historical failure evidence.

## Requested final pipelines

The following pipelines are specified for the future production design but are
not included as runnable graphs because their required models/nodes are not
installed and have not been tested here:

| ID | Inputs | Intended engine | Current status |
| --- | --- | --- | --- |
| 01_three_images_masterframe_i2v | two characters plus scene/layout | Qwen Image Edit plus LTX 2.5 | blocked by uninstalled models |
| 02_two_images_one_video_dual_character_control | two characters plus driving video | Wan2.2 Fun Control | blocked by uninstalled model and unverified node graph |
| 03_single_character_wan_animate | one character plus driving video | Wan2.2 Animate | blocked by uninstalled model |
| 04_ltx25_first_last_frame | clean first and last frame | LTX 2.5 | blocked by uninstalled model |
| 05_dialogue_and_audio | image plus dialogue/audio | speech/lipsync pipeline | no validated local graph |
| 06_upscale_interpolate_export | generated video plus optional audio | video post-process stack | no validated local graph |

Creating JSON that names unavailable node classes would be a misleading
placeholder, so the catalog intentionally records those pipelines as blocked.
Their input and output contracts are stored as non-runnable JSON
specifications under workflows/specs. The live workflow registry intentionally
does not load that subdirectory.

## MiniMax H3 selector

`workflows/specs/07_minimax_h3_unified.json` records one logical
`MINIMAX_H3` selector for multi-image H3 planning. It is not a runnable local
prompt graph. The local state is `BLOCKED_LOCAL_H3`; the AutoDL state is
`DRY_RUN_ONLY`. The selector is exposed by `GET /api/comfyui/engines`; submit
validation through `POST /api/comfyui/h3/dry-run`. Direct job submission of
the H3 workflow IDs is rejected with HTTP 409 until a future, explicitly
authorized cloud enablement is verified. See `docs/H3_WORKFLOW.md` for the
wrapper mapping and URL-only reference rules.

## API input mapping for the verified graph

The generic job API uploads each media item first. A media key becomes the
workflow token value:

~~~json
{
  "provider": "LOCAL",
  "workflow_id": "wan2.1_i2v_ref_5s_local",
  "inputs": {
    "prompt": "..."
  },
  "media": {
    "character_a_image": {
      "path": "F:\\AI短剧\\reference.png",
      "media_type": "image"
    }
  }
}
~~~

The tokenized smoke run proved the upload mapping with
`suwanqing45_primary_portrait.png` and `suwanqing45_neutral_control.mp4` in
the submitted graph. That validates the mapping at smoke resolution only; it
does not validate final production quality or the H3 graph.
