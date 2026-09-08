# Windows Installation And Launch

This delivery keeps the existing G:\ComfyUI installation intact. It adds a
separate integration layer under F:\一人公司\comfyui-production.

## Start locally

Start or reuse the loopback-only ComfyUI server and open its UI:

    powershell -ExecutionPolicy Bypass -File F:\一人公司\comfyui-production\scripts\start_comfyui_local.ps1 -Port 8188 -OpenBrowser -Wait

For repeatable startup, set `COMFY_AUTO_OPEN=1` in the project `.env`; the
launcher reads the process environment first and then `.env`. Use
`-NoBrowser` for a one-run suppression. The example file keeps this switch at
`0` so unattended runs do not open a window by surprise.

The local launcher accepts the ComfyUI server port through `-Port` (8188 by
default). `COMFY_LOCAL_URL` configures the integration client's target URL;
`COMFY_LOCAL_HOST` and `COMFY_LOCAL_PORT` are not supported settings and are
intentionally absent from `.env.example`. The API listener remains the separate
`COMFY_API_PORT` setting, defaulting to 8092.

Start the management-page API:

    powershell -ExecutionPolicy Bypass -File F:\一人公司\comfyui-production\scripts\start_comfyui_api.ps1 -Wait

The command above uses `COMFY_API_PORT` from the process or project `.env`, or
its default of 8092. The launcher verifies the H3 catalog and no-I/O dry-run
route before reusing a listener; a health-only listener is rejected rather than
replaced:

    powershell -ExecutionPolicy Bypass -File F:\一人公司\comfyui-production\scripts\start_comfyui_api.ps1 -Port 8092 -Wait

Check both:

    powershell -ExecutionPolicy Bypass -File F:\一人公司\comfyui-production\scripts\check_comfyui_local.ps1
    powershell -ExecutionPolicy Bypass -File F:\一人公司\comfyui-production\scripts\check_comfyui_api.ps1

The ComfyUI UI stays at http://127.0.0.1:8188. The integration API defaults to
http://127.0.0.1:8092. The observed 8091 listener is health-only; neither 8091
nor 8092 should be stopped or replaced by these checks. Neither script opens a
public binding. To check the managed listener, use:

    powershell -ExecutionPolicy Bypass -File F:\一人公司\comfyui-production\scripts\check_comfyui_api.ps1 -Port 8092

## Stop only managed processes

    powershell -ExecutionPolicy Bypass -File F:\一人公司\comfyui-production\scripts\stop_comfyui_api.ps1
    powershell -ExecutionPolicy Bypass -File F:\一人公司\comfyui-production\scripts\stop_comfyui_local.ps1

The local stop script only stops a Python PID recorded by this delivery. It
does not kill an existing ComfyUI process it did not start.

## Models And Credentials

The .env.example file contains safe placeholders. Put real AutoDL or Hugging
Face credentials only in your process environment or a credential store; never
put them in workflow JSON, logs, screenshots, or the example file.

The control layer does not download model files. At handoff, the user reported
a PowerShell transfer of the MiniMax H3 Ref2VA weight under
`G:\ComfyUI\models`; until the user confirms that PowerShell window naturally
returned to its prompt, do not stop, restart, replace, move, rename, read,
hash, load, or duplicate the transfer, and do not change Clash Verge or proxy
settings. The H3 download state remains `PENDING` / `DEFERRED` and H3 must not
be called installed. The other H3 files, node package, text encoder,
video/audio VAEs, and LoRA are not confirmed by the presence of this one file.

After the user confirms the transfer has ended, run the guarded status check,
then perform a separate authorized size/mtime/SHA-256/source audit and refresh
ComfyUI's model list. Do not execute historical commands with empty or
unverified URLs. Use a direct, no-proxy download path only when an authorized
source has been checked.

AutoDL H3 is registered for `DRY_RUN_ONLY` only. The integration API can
validate the two wrapper IDs without a token or network request; real cloud
submission remains disabled until the user fills `.env` and explicitly
authorizes a budgeted test.
