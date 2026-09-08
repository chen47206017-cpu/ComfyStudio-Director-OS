# H3 Upgrade Audit

## Scope and result

This is a read-only compatibility audit for the existing production instance at G:\ComfyUI. No ComfyUI core, model, custom node, workflow, input, output, cache, or Infinite-Canvas asset was changed. The installation gate is **BLOCKED**.

The audit separates three things that must not be conflated:

1. The ComfyUI API is healthy.
2. Motion Context source exists upstream.
3. A runnable local H3 continuity chain exists.

Only item 1 is currently proven.

## Live runtime evidence

| Field | Observed value |
| --- | --- |
| ComfyUI path | G:\ComfyUI reported by the existing environment; current process working directory was not re-inspected |
| Service | http://127.0.0.1:8188 |
| Listener | 127.0.0.1 only |
| ComfyUI version | 0.27.0 |
| Python | 3.12.10 from the live system-stats response |
| Torch / CUDA build | 2.11.0+cu128 |
| GPU | NVIDIA GeForce RTX 5060 Ti 16GB |
| Process evidence | A future-dated reference record names PID 40436; it is not current-process proof |
| API checks | /system_stats and /object_info both returned HTTP 200 during this iteration |
| Existing object-info baseline | A future-dated reference record reports 1,136 nodes; current named-node absence is independently rechecked |
| C drive free space | 6,102,892,544 bytes at audit time |
| F drive free space | 116,669,534,208 bytes at audit time |

The existing reference files carry 2026-09-07T01:16-01:17+08:00 timestamps, which are future-dated relative to this 2026-09-06 iteration. Their hashes and paths are preserved for provenance, but they are not treated as current process evidence. The current iteration independently rechecked that both endpoints answered and the named H3 classes remained absent; process reinspection was denied by the sandbox. The process was not stopped or restarted.

The source records and SHA-256 values are in reports/h3/runtime_baseline_summary.json. Existing source files remain under F:\AI短剧\H3_UPGRADE_TEST and were not changed.

## H3 node gate

The current read-only object-info endpoint probe does **not** register any of the following classes. The future-dated object-info file is reference material only:

- MiniMaxH3ReferenceToVideo
- MiniMaxH3MotionContext
- MiniMaxH3MotionContextTrim
- MiniMaxH3MotionContextSaveLatent
- MiniMaxH3MotionContextLoadLatent
- MiniMaxH3MotionContextChain
- MiniMaxH3MotionContextSeamProbe
- MiniMaxH3Extender

This means the service is reachable but neither the preserved H3 Ref2VA graph nor a Motion Context chain can be submitted as a runnable local H3 job.

## Upstream compatibility gate

The upstream audit is recorded verbatim as structured evidence in reports/h3/upstream_motion_context_audit.json. The source and timestamp boundaries for runtime observations are in reports/h3/runtime-subject.json.

| Candidate | Version evidence | Decision on this host |
| --- | --- | --- |
| Motion Context current release | v0.6.1, commit d6fb99813863ce7c3cf3bdd09cd43cd9bfdc3e0a, GPL-3.0, declares ComfyUI >=0.34.0 | Do not install: the live core is 0.27.0. |
| Motion Context legacy path | v0.3.1, commit 725a731e644c669601799da1eb63f4e7497c628f; the current upstream README directs 0.33.4 or older to it | Do not install: regardless of whether it can import on 0.27.0, the required native H3 node is absent and no local import test was possible. |
| MiniMax H3 Extender | Audit-only alternative, not installed or enabled | Excluded by the active single-owner rule. |

The direct Git/raw source fetch did not complete because Windows Schannel returned SEC_E_NO_CREDENTIALS. A plugin source checkout, dependency installation, and import test were deliberately not substituted with guessed results.

## Existing custom-node and model observations

The locked custom-node inventory contains VideoHelperSuite, Manager, Upscale, DepthAnything, ControlNet auxiliary, IPAdapter, and Impact packages; it contains no H3 Motion Context or Extender package. VideoHelperSuite can support later media work but does not provide an H3 continuity implementation.

The preserved local H3 candidate workflow is F:\AI短剧\Infinite-Canvas-hero8152\workflows\MiniMax_H3.json. It is a single-clip Ref2VA-style graph, not a continuity workflow. Its remaining model, input, and discovery blockers are documented in H3_MODEL_INVENTORY.md.

## Error classification

| Code | Status | Evidence |
| --- | --- | --- |
| H3_COMFYUI_VERSION_CONFLICT | BLOCKED | The current v0.6.1 release requires a newer core than 0.27.0. |
| H3_NODE_MISSING | BLOCKED | Native MiniMaxH3ReferenceToVideo and all Motion Context classes are absent from /object_info. |
| H3_MODEL_MISSING | BLOCKED | The preserved graph references a text encoder not found by the prior audit; FL2VA downloads are incomplete. |
| H3_CACHE_ERROR | NOT_TESTED | No compatible plugin is installed, so no H3 cache was created. |
| H3_ASSEMBLY_ERROR | NOT_TESTED | No H3 clips were generated; FFmpeg version could not be verified in this sandbox. |

## Safe stop point

No production installation is justified until a separately approved compatibility path can prove all of the following: a compatible ComfyUI core, native H3 node registration, discoverable complete model files, and a single H3 chaining owner. Upgrading ComfyUI, installing a custom node, changing model paths, or downloading models is outside this iteration and was not performed.
