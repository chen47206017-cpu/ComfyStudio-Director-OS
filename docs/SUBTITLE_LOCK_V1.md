# SUBTITLE_LOCK_V1

This is the locked primary-subtitle style for the vertical live-action drama
export. Its reference canvas is 1080 x 1920 and it is intended for one line,
with two lines only when necessary.

| Setting | Locked value |
| --- | --- |
| Font | Source Han Sans CN Medium; Source Han Sans CN SemiBold for complex backgrounds |
| Current-machine fallback | Microsoft YaHei (Source Han is not installed) |
| Font size | 60 px; acceptable range 56-64 px |
| Text | #FFFFFF |
| Outline | #000000, 4 px, about 85% opacity |
| Shadow | Black, 1 px, deliberately weak |
| Letter spacing | 0 |
| Alignment | bottom center |
| Safe margins | 70 px left/right; 390 px from the bottom |
| Approximate baseline zone | Y 1420-1500 |
| Animation | none; cut on and off directly |

`sample_assets/subtitles/SUBTITLE_LOCK_V1.ass` contains the actual ASS style.
It is a style template and intentionally has no active dialogue event. Copy it
into an authored ASS file, add timed `Dialogue:` rows, and preserve `Primary`
or `PrimarySemibold`. `SUBTITLE_LOCK_V1_preview.ass` is the visible smoke-test
sample.
For ordinary dialogue, use `Primary`. Use `PrimarySemibold` only when a complex
background makes the standard weight insufficient. Keep each line to roughly
8-16 Chinese characters and do not use character-color coding or keyword
highlighting in regular drama subtitles.

Run the read-only preflight before burning an authored file:

```powershell
python scripts/validate_subtitles.py <authored.ass> --json
```

The preflight checks the 1080x1920 canvas, locked styles, event timing, line
count, and visual/position overrides. It does not replace a post-burn media
probe or visual frame review. Use `--allow-empty` only for the style template;
use `--require-source-han` when the machine font installation itself must be a
hard requirement.

Burn an authored ASS file into a video with:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\burn_subtitles.ps1 `
  -Video <input.mp4> -Subtitle <input.ass> -Output <output.mp4>
```

The burn script runs the validator before FFmpeg and refuses the empty style
template or any unsafe override. It renders to a sibling partial MP4 and
publishes it only after FFmpeg reports success and a non-empty file exists, so
an interrupted export cannot replace a previous output. It uses NVENC by
default and preserves an existing audio track. Use `-VideoCodec libx264` only
when the NVENC encoder is unavailable.

This is still only the subtitle/burn stage. The final 1080x1920, 24fps,
approximately five-second delivery gate must separately probe the media,
confirm audio and duration, extract QA frames, and record the output hash.
