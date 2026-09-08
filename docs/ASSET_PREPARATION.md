# Asset Preparation

## Accepted source media

- Images: PNG, JPG/JPEG, WEBP, BMP
- Driving video: MP4, MOV, MKV, WEBM
- Audio: WAV, MP3, M4A, FLAC

The local API restricts file paths to COMFY_ALLOWED_MEDIA_ROOTS and rejects
empty files, unsupported extensions, oversize uploads, and paths outside those
roots. It strips invisible directional formatting characters from pasted
Windows paths, including the leading mark in ‪F:\AI短剧\苏晚晴45.png.

## Reference image guidance

Use a single subject portrait or clean full-body source for a character
reference. Do not feed a contact sheet, split-screen, three-panel design, or
editor screenshot into an identity encoder. The supplied 苏晚晴45.png is a
useful character design reference, but its multi-panel composition is likely
one cause of the local baseline's identity drift.

For a two-character shot, prepare:

1. One clean image for SW45.
2. One clean image for SW25.
3. One clean scene/layout image, or a short driving video.

Keep age, hair, clothing, and framing distinct in the character source files.
This reduces face blending, age swapping, and costume swapping but does not
guarantee identity binding.

## Current asset record

The source image F:\AI短剧\苏晚晴45.png was copied to
G:\ComfyUI\input\suwanqing45_ref.png for the verified local run. The recorded
SHA-256 for both source and copy is:

51037BBABF74BE953B5EF633D3749D16022D0648BAB27566FEE0E0607EC13182

The source remains user-owned local material and is not uploaded by this
integration unless a configured remote provider receives an explicit job.

