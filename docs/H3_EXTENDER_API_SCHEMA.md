# H3 API Schema Status

## Scope

The filename is retained because it is a required delivery artifact. It is **not** an implemented MiniMax H3 Extender API schema: Extender is not installed or activated, and the active contract prohibits enabling it alongside Motion Context.

## Current verified API surface

The existing ComfyUI service at http://127.0.0.1:8188 responds to /system_stats and /object_info. That proves service availability only.

The local project endpoint /api/comfyui/h3/dry-run is planning-only. It selects project metadata and does not prove a vendor H3 request format, a native ComfyUI H3 graph, a submission, or an H3 render.

## Native H3 API readiness

| Requirement | Current result |
| --- | --- |
| MiniMaxH3ReferenceToVideo in /object_info | Missing |
| Motion Context node classes in /object_info | Missing |
| Extender node classes in /object_info | Missing |
| Official runnable Motion Context graph locally imported | Not performed |
| H3 workflow API payload captured from a registered graph | Not available |
| /prompt submission with a valid H3 graph | Not performed |
| Dynamic H3 parameter validation | Not performed |

**H3 API status: BLOCKED.**

## Future dynamic inputs, not a payload contract

After the native H3 node and a single compatible continuity extension are truly registered, the integration should capture the exact API-format workflow exported by that installed version. The following are intended integration variables, but are not validated field names or accepted node inputs today:

- prompt
- seed
- duration
- resolution
- reference_images
- reference_videos
- reference_audio
- previous_clip
- previous_end_frame
- output_prefix

No hand-authored workflow JSON or guessed /prompt request was created. That avoids presenting an unregistered node graph as an API-compatible production entry point.

## Required capture before enabling Infinite-Canvas

1. Export the working graph from the verified installed ComfyUI UI.
2. Obtain the graph API JSON from that exact runtime version.
3. Map only actual node input keys to external parameters.
4. Submit one low-cost graph and record prompt ID, history result, output paths, and SHA-256.
5. Re-run with a preceding validated clip to establish the continuity input, then document the invalidation and resume behavior.

Until those steps occur, Infinite-Canvas must treat H3 continuity as unavailable rather than as an API feature.
