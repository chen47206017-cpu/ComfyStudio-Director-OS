# Cloud RTX 5090

No cloud instance was created and no paid cloud render was submitted in this
delivery.

## Remote static ComfyUI

For a user-managed RTX 5090 ComfyUI server, set:

~~~ini
COMFY_PROVIDER=REMOTE_STATIC
COMFY_REMOTE_URL=https://authenticated-example.invalid/comfyui
COMFY_REMOTE_TOKEN=
CLOUD_GPU_NAME=RTX 5090 32GB
CLOUD_HOURLY_PRICE=
~~~

The same local job API then uses the remote provider. The remote server must
be behind authentication and must not expose an unauthenticated ComfyUI port.

## AutoDL workflow API

For AutoDL's hosted workflow wrapper, set:

~~~ini
COMFY_PROVIDER=AUTODL_COMFYUI
AUTODL_API_BASE_URL=https://autodl.art
AUTODL_API_TOKEN=
AUTODL_ALLOW_PAID_SUBMIT=0
AUTODL_POLL_TIMEOUT_SECONDS=1800
~~~

The client uses the documented AutoDL workflow submit/result endpoints and
explicitly disables proxy handling for both API requests and short-lived
result downloads. This prevents a running Clash Verge proxy from silently
routing a transfer.

Paid AutoDL `/api/comfyui/jobs` submission is server-side disabled by default.
Keep `AUTODL_ALLOW_PAID_SUBMIT=0` during setup and dry-run work. Enabling it is
an explicit cost-bearing authorization and still requires an exact JSON `body`
object; malformed bodies are rejected with HTTP 422 before submission. The
polling deadline defaults to 1800 seconds. A deadline yields `NEEDS_REVIEW`
with the vendor task ID because AutoDL has no documented remote cancellation
endpoint and the task may continue running.

The H3 hosted workflows require an AutoDL ComfyUI token, not a Hugging Face
read token. The two legacy H3 IDs currently carry
`USER_SUPPLIED_UNVERIFIED` schema status: their active drawer-derived request
body must be captured before any submission is enabled. The selector only
accepts hosted references for no-I/O planning and does not expose local files
as public URLs. A 1080x1920 final artifact remains a delivery target, not a
claimed direct source resolution of the legacy H3 wrapper. See
`AUTODL_COMFYUI_API.md` for the verified transport and schema boundary.

A real 5090 test still requires explicit approval, a user-managed endpoint or
token, a short low-cost test, recorded cost, and a confirmed instance
shutdown. AutoDL exposes no documented remote cancellation endpoint here, so
do not treat a local job-cancel action as a cost-saving cloud cancellation.
