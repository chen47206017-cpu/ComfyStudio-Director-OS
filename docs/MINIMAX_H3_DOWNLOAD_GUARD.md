# MiniMax H3 Download Guard

This guard records readiness while the six MiniMax H3 files are being copied
by a user-managed PowerShell process. It is intentionally a **manifest-only**
check. It does not inspect the ComfyUI model directory and cannot claim that a
file exists, is complete, is authentic, or is compatible with ComfyUI.

The applicable task baseline date is **September 3, 2026**. Some local file
metadata may display **September 4, 2026** because of a machine-clock/reporting
offset; that value is untrusted and is not evidence of a later observation.

## Current state

`minimax_h3.download-state.json` contains six user-supplied source
coordinates. All six entries are `PENDING` with `verification: DEFERRED`.
Sizes and SHA-256 values are intentionally `null`. The source repositories and
filenames were transcribed from the commands supplied by the user; no network
request or Hugging Face token was used to verify them.

## Safe status check

Run from the project directory:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check_minimax_h3_download.ps1
```

The command reads only the project manifest and emits JSON. It makes no network
request, does not alter Clash Verge or any proxy setting, and does not open,
read, enumerate, hash, move, delete, or load a model file.

It also does not inspect `G:\\ComfyUI` or any other model root.

## Completion gate

When the user confirms the PowerShell transfer has stopped, a separate,
explicitly authorized audit may inspect file presence, stable size, hashes,
source metadata, and ComfyUI node compatibility. Until that gate is met, the
guard must remain `DEFERRED`; a growing or present file must not be treated as
ready for rendering.

The local H3 graph and AutoDL multi-reference workflow remain separate
implementation work. This status record does not install nodes, change
workflows, or create a paid cloud instance.
