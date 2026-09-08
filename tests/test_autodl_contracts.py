from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from comfyui_production.autodl import AutoDLApiError, AutoDLComfyWorkflowClient, AutoDLProvider
from comfyui_production.client import provider_from_settings


_TOKEN = "test-token-not-real"


class _Response:
    def __init__(self, chunks: list[bytes | BaseException]):
        self._chunks = list(chunks)

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> bool:
        return False

    def read(self, _size: int = -1) -> bytes:
        if not self._chunks:
            return b""
        value = self._chunks.pop(0)
        if isinstance(value, BaseException):
            raise value
        return value


class _Opener:
    def __init__(self, response: _Response):
        self.response = response
        self.requests = []

    def open(self, request: object, timeout: float) -> _Response:
        self.requests.append((request, timeout))
        return self.response


class AutoDLContractsTest(unittest.TestCase):
    def test_submit_uses_documented_envelope_and_raw_authorization_value(self) -> None:
        client = AutoDLComfyWorkflowClient(token=_TOKEN)
        observed: dict[str, object] = {}

        def fake_request(method: str, path: str, payload: object = None) -> object:
            observed.update(method=method, path=path, payload=payload)
            return {
                "code": "Success",
                "data": {"task_id": "task-123", "status": "QUEUED", "client_id": "client-123"},
            }

        client._request = fake_request  # type: ignore[method-assign]
        result = client.submit("minimax_h3_lightx2v_v5", {"prompt": "test", "duration": 5})

        self.assertEqual(result["task_id"], "task-123")
        self.assertEqual(observed["method"], "POST")
        self.assertEqual(
            observed["path"],
            "/api/v1/comfyui/comfyui_workflow/minimax_h3_lightx2v_v5",
        )
        self.assertEqual(client._headers()["Authorization"], _TOKEN)
        self.assertNotEqual(client._headers()["Authorization"], f"Bearer {_TOKEN}")

    def test_result_requires_success_code_known_status_and_matching_task_id(self) -> None:
        client = AutoDLComfyWorkflowClient(token=_TOKEN)
        client._request = lambda *_args, **_kwargs: {
            "code": "Success",
            "data": {"task_id": "task-123", "status": "SUCCESS", "results": ["https://example.test/a.mp4"]},
        }  # type: ignore[method-assign]
        result = client.result("task-123")
        self.assertEqual(result["status"], "SUCCESS")

        client._request = lambda *_args, **_kwargs: {
            "code": "Success",
            "data": {"task_id": "task-123", "status": "MYSTERY"},
        }  # type: ignore[method-assign]
        with self.assertRaisesRegex(AutoDLApiError, "unknown status"):
            client.result("task-123")

        client._request = lambda *_args, **_kwargs: {
            "code": "Success",
            "data": {"task_id": "other-task", "status": "RUNNING"},
        }  # type: ignore[method-assign]
        with self.assertRaisesRegex(AutoDLApiError, "does not match"):
            client.result("task-123")

    def test_result_normalizes_documented_completed_terminal_status(self) -> None:
        client = AutoDLComfyWorkflowClient(token=_TOKEN)
        client._request = lambda *_args, **_kwargs: {
            "code": "Success",
            "data": {"task_id": "task-123", "status": "cOmPlEtEd", "results": []},
        }  # type: ignore[method-assign]

        result = client.result("task-123")

        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(list(client.wait("task-123", poll_interval=0.1)), [result])

    def test_error_body_redacts_configured_token(self) -> None:
        client = AutoDLComfyWorkflowClient(token=_TOKEN)
        client._request = lambda *_args, **_kwargs: {
            "code": "Failed",
            "data": {},
            "msg": f"authorization={_TOKEN}",
        }  # type: ignore[method-assign]

        with self.assertRaises(AutoDLApiError) as raised:
            client.submit("minimax_h3_lightx2v_v5", {"prompt": "test"})

        self.assertNotIn(_TOKEN, raised.exception.body)
        self.assertIn("[REDACTED]", raised.exception.body)
        self.assertNotIn(_TOKEN, str(raised.exception))

    def test_provider_from_settings_selects_autodl_and_requires_a_token(self) -> None:
        settings = SimpleNamespace(
            provider="AUTODL_COMFYUI",
            autodl_api_base_url="https://autodl.art",
            autodl_api_token=_TOKEN,
            client_timeout_seconds=12,
        )
        provider = provider_from_settings(settings)

        self.assertIsInstance(provider, AutoDLProvider)
        self.assertEqual(provider.client.base_url, "https://autodl.art")
        self.assertEqual(provider.client.token, _TOKEN)
        self.assertEqual(provider.client.timeout, 12.0)

        settings.autodl_api_token = ""
        with self.assertRaisesRegex(ValueError, "AUTODL_API_TOKEN"):
            provider_from_settings(settings)

    def test_download_streams_directly_to_an_atomic_artifact(self) -> None:
        client = AutoDLComfyWorkflowClient(token=_TOKEN)
        opener = _Opener(_Response([b"video-", b"bytes", b""]))

        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "result.mp4"
            with patch("comfyui_production.autodl.build_opener", return_value=opener) as build:
                output = client.download_result("https://results.example.test/video.mp4", target)

            self.assertEqual(output, target)
            self.assertEqual(target.read_bytes(), b"video-bytes")
            self.assertEqual(list(target.parent.glob("*.part")), [])
            self.assertEqual(opener.requests[0][0].get_full_url(), "https://results.example.test/video.mp4")
            self.assertEqual(build.call_args.args[0].proxies, {})

    def test_download_failure_removes_partial_file_and_preserves_existing_output(self) -> None:
        client = AutoDLComfyWorkflowClient(token=_TOKEN)
        opener = _Opener(_Response([b"partial", OSError("connection reset")]))

        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "result.mp4"
            target.write_bytes(b"previous-complete-output")
            with patch("comfyui_production.autodl.build_opener", return_value=opener):
                with self.assertRaisesRegex(AutoDLApiError, "download failed"):
                    client.download_result("https://results.example.test/video.mp4", target)

            self.assertEqual(target.read_bytes(), b"previous-complete-output")
            self.assertEqual(list(target.parent.glob("*.part")), [])


if __name__ == "__main__":
    unittest.main()
