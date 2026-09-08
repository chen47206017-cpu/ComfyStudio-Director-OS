# H3 Resume Test

## Status

**BLOCKED; not executed.**

No compatible H3 chaining node is installed, no Clip 1 has been generated or validated, no H3 latent/context cache exists, and ComfyUI was not stopped or restarted. A resume claim would therefore be fabricated.

## Preconditions that failed

| Required precondition | Result |
| --- | --- |
| Native H3 runtime node registered | Missing |
| One compatible Motion Context owner registered | Missing |
| Validated Clip 1 output | Missing |
| Persistent H3 latent/context cache | Missing |
| Compatible H3 workflow import | Missing |

## Test record

| Step | Result |
| --- | --- |
| Generate and Validate Clip 1 | Not run |
| Close existing ComfyUI safely | Not run |
| Restart the same production instance | Not run |
| Reload project/cache state | Not run |
| Generate Clip 2 from validated Clip 1 | Not run |
| Check that Clip 1 is not recomputed | Not run |

## Required future acceptance evidence

The later test must record the exact plugin version, graph export, cache location, Clip 1/Clip 2 SHA-256 values, process restart timestamps, output paths, and the UI/API state showing that Clip 1 remained validated. If Clip 2 is changed, only its downstream clips may be invalidated; the test must demonstrate that rule rather than assert it.

No cache path was configured in this iteration. The intended F:\AI短剧\ComfyUI_H3_Cache location remains a future configuration decision, not an active setting.
