# Benchmark Report

## Local Wan2.1 I2V smoke render

| Field | Result |
| --- | --- |
| Status | ComfyUI history success |
| GPU | RTX 5060 Ti 16GB |
| Rendered media | 432x768, 24 fps, 121 frames, 5.04 seconds |
| Encoder | H.264 NVENC |
| Steps | 24 |
| Seed | 20260903 |
| Reported render time | approximately 46 minutes |
| Observed GPU load | 100 percent during sampling |
| Observed VRAM | approximately 12GB |
| Model download | none |
| Paid cloud use | none |

Artifact:

F:\一人公司\comfyui-production\artifacts\wan2.1_i2v_suwanqing_5s\wanvideo_suwanqing_ref_5s_local_00001.mp4

SHA-256:

0E7C41318A7EBC27BDCF88F4A057073B66213D429AEFFD2BCED8797218F04AB6

## Quality gate

Technical execution passed. The manual frame review identified visible grain,
facial distortion, and identity drift, therefore:

technical_pass_visual_quality_not_accepted

The metadata generated_at is 2026-09-04T00:17:22+08:00, a future
machine-generated timestamp relative to the 2026-09-03 delivery date. The
report preserves it verbatim but does not rely on it as the current task time.

## Not benchmarked

No cloud 5090 benchmark exists yet. No claim is made for Qwen Image Edit,
LTX 2.5, Wan2.2 Fun Control, Wan2.2 Animate, multi-character binding, audio
lipsync, upscale, or interpolation because no runnable validated graph and no
authorized cloud task exists for those paths.

