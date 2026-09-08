"""Provider compatibility exports for the local integration package.

The implementation is split by transport: :mod:`client` handles a local or
static remote ComfyUI HTTP server, while :mod:`autodl` handles AutoDL's
wrapped workflow API.  Keeping these exports in one module gives the web
layer a stable provider import without coupling it to a vendor.
"""

from .autodl import AutoDLComfyWorkflowClient, AutoDLProvider
from .client import (
    ComfyApiError,
    ComfyProvider,
    ComfyUIClient,
    LocalComfyProvider,
    RemoteComfyProvider,
    provider_from_settings,
)

__all__ = [
    "AutoDLComfyWorkflowClient",
    "AutoDLProvider",
    "ComfyApiError",
    "ComfyProvider",
    "ComfyUIClient",
    "LocalComfyProvider",
    "RemoteComfyProvider",
    "provider_from_settings",
]
