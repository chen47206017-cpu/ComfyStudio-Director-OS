# H3 Model Inventory

## Result

**BLOCKED.** This is an evidence inventory, not a model download or repair operation. No file in G:\ComfyUI\models was copied, moved, renamed, hashed, loaded, or deleted during this iteration.

## Preserved graph

The only located local candidate is:

F:\AI短剧\Infinite-Canvas-hero8152\workflows\MiniMax_H3.json

It is an API-format, single-clip Ref2VA graph. It includes model loading, reference input, sampling, VAE decode/audio decode, and SaveVideo nodes. It does not include Motion Context, Validate, Retry, Save/Load latent, Trim, Assembly, or Resume control. Therefore it is preserved as a baseline only; it is not evidence of continuous H3 generation.

The requested minimax_h3_lightx2v_v5 identifier was found only in this project as planner/spec metadata. No executable ComfyUI graph with that name was located.

## Model and input evidence

The project model manifest dated 2026-09-03 is a historical deferred-download record; it is not proof of current file presence. The following prior discovery observations are likewise filename/path evidence only. No candidate was integrity-verified, loaded, or altered.

| Asset | Observed path or requested name | State | Workflow impact |
| --- | --- | --- | --- |
| Ref2VA diffusion model | G:\ComfyUI\models\MiniMax-H3-INT8\diffusion_models\minimax_h3_ref2va_pruned_int8_convrot.safetensors | Prior read-only audit observed a candidate file. Runtime discovery is unproven. | Cannot prove UNETLoader can select it. |
| FL2VA diffusion model | minimax_h3_fl2va_int8_convrot.safetensors.incomplete and minimax_h3_fl2va_pruned_int8_convrot.safetensors.incomplete | Incomplete downloads. | A long FL2VA continuity chain is unavailable. |
| Text encoder expected by baseline graph | qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors | Not found by the prior audit. | The baseline graph has an unresolved loader reference. |
| Alternate local text-encoder candidate | G:\ComfyUI\models\MiniMax-H3-INT8\text_encoders\qwen3vl_32b_minimax_h3_int8_convrot.safetensors | Name differs from the graph reference; no substitution was made. | Name mismatch remains unresolved. |
| Video VAE and Audio VAE | Nested MiniMax-H3 package and standard G:\ComfyUI\models\vae locations | Candidates were previously observed, but were not loaded or verified this iteration. | Not a proof of a complete H3 inference chain. |
| Baseline reference image | 5 (1).jpg under the graph input reference | Not found in G:\ComfyUI\input by the prior audit. | The preserved graph has an unresolved local input. |

## Discovery-path blocker

The H3 candidates are nested under G:\ComfyUI\models\MiniMax-H3-INT8. The existing startup command has no --extra-model-paths-config argument, and the bundled MiniMax H3 README expects model families beneath ComfyUI standard model folders. The runtime has not been shown to discover the nested Ref2VA or text-encoder candidates.

No model-path configuration was added, and no symlink, copy, rename, or download was attempted.

## Runtime node blocker

Even a complete file set would not close the current gate. The live /object_info response does not include MiniMaxH3ReferenceToVideo. Thus there is no verified native H3 node surface that could load this graph on the running ComfyUI 0.27.0 instance.

## Duplicate and download policy

The audit did not scan, hash, or deduplicate large models. This avoids touching production weights and does not mistake a filename for a usable model. No large model download is authorized or required for this evidence-only delivery.

## Required evidence before an H3 smoke test

1. A separately approved, compatible ComfyUI/H3 node path.
2. Object-info evidence for the native H3 node and exactly one continuity owner.
3. A discoverable, complete model set whose graph filenames match actual selectable options.
4. A valid reference asset and a low-cost H3 job that completes without an import, loader, shape, or OOM failure.

Until then, Clip 1, Clip 2, Trim, Assembly, Resume, output MP4, and any output SHA-256 remain untested.
