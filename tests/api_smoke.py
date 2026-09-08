"""Runnable standard-library smoke tests for the local ComfyUI API.

Run with:
    PYTHONPATH=src python tests/api_smoke.py
"""

from __future__ import annotations

import http.client
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from typing import Any

from comfyui_production.config import Settings
from comfyui_production.server import ApiApplication, ApiError, ApiHTTPServer, create_server
from comfyui_production.store import JobStore
from comfyui_production.workflow import WorkflowRegistry


class FakeLocalClient:
    def __init__(self, status: str = "success") -> None:
        self.status = status
        self.deleted: list[str] = []

    def iter_progress(self, prompt_id: str, _poll_interval: float) -> Any:
        yield {
            "type": "history",
            "prompt_id": prompt_id,
            "completed": True,
            "entry": self.history(prompt_id)[prompt_id],
        }

    def history(self, prompt_id: str) -> dict[str, Any]:
        return {
            prompt_id: {
                "status": {"status_str": self.status},
                "outputs": {
                    "40": {
                        "gifs": [{
                            "filename": "clip.mp4",
                            "subfolder": "",
                            "type": "output",
                        }]
                    }
                },
            }
        }

    def download_view(
        self,
        filename: str,
        subfolder: str = "",
        file_type: str = "output",
        destination: str | Path | None = None,
    ) -> Path:
        del subfolder, file_type
        if filename != "clip.mp4" or destination is None:
            raise AssertionError("unexpected local output request")
        target = Path(destination)
        target.write_bytes(b"LOCAL-MP4")
        return target

    def delete_queue(self, prompt_id: str) -> None:
        self.deleted.append(prompt_id)

    def interrupt(self) -> None:
        return None


class BlockingLocalClient(FakeLocalClient):
    def __init__(self) -> None:
        super().__init__()
        self.release = threading.Event()

    def iter_progress(self, prompt_id: str, _poll_interval: float) -> Any:
        self.release.wait(2)
        yield from super().iter_progress(prompt_id, _poll_interval)


class FakeLocalProvider:
    def __init__(self, client: FakeLocalClient | None = None) -> None:
        self.client = client or FakeLocalClient()
        self.submitted: list[dict[str, Any]] = []

    def health(self) -> dict[str, Any]:
        return {"ok": True, "device": "fake"}

    def submit(self, graph: dict[str, Any]) -> dict[str, Any]:
        self.submitted.append(graph)
        return {"prompt_id": "local-prompt"}


class FakeAutoDLClient:
    def __init__(self, result: dict[str, Any]) -> None:
        self.result = result
        self.downloaded_urls: list[str] = []
        self.wait_timeouts: list[float | None] = []

    def wait(self, task_id: str, _poll_interval: float, *, timeout: float | None = None) -> Any:
        if task_id != "autodl-task":
            raise AssertionError("unexpected task id")
        self.wait_timeouts.append(timeout)
        yield self.result

    def download_result(self, url: str, destination: str | Path) -> Path:
        self.downloaded_urls.append(url)
        target = Path(destination)
        target.write_bytes(b"AUTODL-MP4")
        return target


class FakeAutoDLProvider:
    def __init__(self, client: FakeAutoDLClient) -> None:
        self.client = client
        self.submitted: list[tuple[str, dict[str, Any]]] = []

    def submit(self, workflow_id: str, body: dict[str, Any]) -> dict[str, Any]:
        self.submitted.append((workflow_id, dict(body)))
        return {"task_id": "autodl-task", "status": "QUEUED"}


def wait_for_terminal(app: ApiApplication, job_id: str) -> dict[str, Any]:
    for _ in range(300):
        row = app.store.get(job_id)
        if row and row.get("status") in {"SUCCEEDED", "FAILED", "CANCELLED", "NEEDS_REVIEW"}:
            return row
        time.sleep(0.01)
    raise AssertionError("job did not reach a terminal state")


def make_local_app(root: Path, provider: FakeLocalProvider | None = None) -> tuple[ApiApplication, FakeLocalProvider]:
    workflows = root / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "demo.json").write_text(
        json.dumps({"prompt": {"1": {"class_type": "Test", "inputs": {"text": "{{prompt}}"}}}}),
        encoding="utf-8",
    )
    provider = provider or FakeLocalProvider()
    settings = Settings(
        provider="LOCAL",
        api_host="127.0.0.1",
        api_port=0,
        workflow_dir=workflows,
        job_store=root / "runtime" / "jobs.json",
        allowed_media_roots=(root,),
        poll_interval_seconds=0.01,
    )
    app = ApiApplication(
        settings,
        store=JobStore(settings.job_store),
        registry=WorkflowRegistry(workflows),
        provider_factory=lambda _name: provider,
    )
    return app, provider


def make_autodl_app(
    root: Path,
    provider: FakeAutoDLProvider,
    *,
    allow_paid: bool = True,
    poll_timeout: float = 1800.0,
) -> ApiApplication:
    settings = Settings(
        provider="AUTODL_COMFYUI",
        api_host="127.0.0.1",
        api_port=0,
        workflow_dir=root / "workflows",
        job_store=root / "runtime" / "jobs.json",
        allowed_media_roots=(root,),
        poll_interval_seconds=0.01,
        autodl_allow_paid_submit=allow_paid,
        autodl_poll_timeout_seconds=poll_timeout,
    )
    return ApiApplication(
        settings,
        store=JobStore(settings.job_store),
        registry=WorkflowRegistry(settings.workflow_dir),
        provider_factory=lambda _name: provider,
    )


class ApiSmokeTests(unittest.TestCase):
    def test_local_job_mirrors_output_and_streams_it(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            app, provider = make_local_app(Path(temporary))
            status, health = app.dispatch("GET", "/api/comfyui/health")
            self.assertEqual(status, 200)
            self.assertTrue(health["provider_ok"])
            self.assertEqual(app.dispatch("GET", "/api/comfyui/workflows")[1]["workflows"][0]["id"], "demo")
            self.assertEqual(len(app.dispatch("GET", "/api/comfyui/presets")[1]["presets"]), 2)

            status, accepted = app.dispatch(
                "POST",
                "/api/comfyui/jobs",
                {"workflow_id": "demo", "inputs": {"prompt": "test prompt"}},
            )
            self.assertEqual(status, 202)
            row = wait_for_terminal(app, accepted["job_id"])
            self.assertEqual(row["status"], "SUCCEEDED")
            self.assertEqual(provider.submitted[0]["1"]["inputs"]["text"], "test prompt")
            artifact = row["artifacts"][0]
            self.assertEqual(artifact["url"], f"/api/comfyui/jobs/{row['job_id']}/outputs/clip.mp4")
            self.assertNotIn("fullpath", json.dumps(row))

            server = ApiHTTPServer(("127.0.0.1", 0), app)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
                connection.request("GET", artifact["url"])
                response = connection.getresponse()
                self.assertEqual(response.status, 200)
                self.assertEqual(response.read(), b"LOCAL-MP4")
                self.assertEqual(response.getheader("Content-Disposition"), 'attachment; filename="clip.mp4"')
                connection.close()

                connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
                connection.request("GET", f"/api/comfyui/jobs/{row['job_id']}/outputs/%2e%2e%2fjobs.json")
                response = connection.getresponse()
                self.assertEqual(response.status, 400)
                self.assertEqual(json.loads(response.read().decode("utf-8"))["error"], "invalid output filename")
                connection.close()
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)

    def test_local_history_failure_is_failed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            provider = FakeLocalProvider(FakeLocalClient(status="error"))
            app, _ = make_local_app(Path(temporary), provider)
            _, accepted = app.dispatch(
                "POST",
                "/api/comfyui/jobs",
                {"workflow_id": "demo", "inputs": {"prompt": "test prompt"}},
            )
            row = wait_for_terminal(app, accepted["job_id"])
            self.assertEqual(row["status"], "FAILED")
            self.assertNotIn("artifacts", row)

    def test_cancel_and_retry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            client = BlockingLocalClient()
            provider = FakeLocalProvider(client)
            app, _ = make_local_app(Path(temporary), provider)
            _, accepted = app.dispatch(
                "POST",
                "/api/comfyui/jobs",
                {"workflow_id": "demo", "inputs": {"prompt": "test prompt"}},
            )
            for _ in range(100):
                current = app.store.get(accepted["job_id"])
                if current and current.get("prompt_id") == "local-prompt":
                    break
                time.sleep(0.01)
            self.assertEqual((app.store.get(accepted["job_id"]) or {}).get("prompt_id"), "local-prompt")
            status, cancelled = app.dispatch("POST", f"/api/comfyui/jobs/{accepted['job_id']}/cancel", {})
            self.assertEqual(status, 200)
            self.assertEqual(cancelled["status"], "CANCELLED")
            self.assertEqual(client.deleted, ["local-prompt"])
            client.release.set()
            self.assertEqual(wait_for_terminal(app, accepted["job_id"])["status"], "CANCELLED")
            for _ in range(100):
                with app._lock:
                    running = accepted["job_id"] in app._threads
                if not running:
                    break
                time.sleep(0.01)

            fast_provider = FakeLocalProvider()
            retry_app, _ = make_local_app(Path(temporary) / "retry", fast_provider)
            _, first = retry_app.dispatch(
                "POST",
                "/api/comfyui/jobs",
                {"workflow_id": "demo", "inputs": {"prompt": "retry me"}},
            )
            wait_for_terminal(retry_app, first["job_id"])
            status, retry = retry_app.dispatch("POST", f"/api/comfyui/jobs/{first['job_id']}/retry", {})
            self.assertEqual(status, 202)
            self.assertEqual(wait_for_terminal(retry_app, retry["job_id"])["retry_of"], first["job_id"])

    def test_autodl_uses_in_memory_body_and_redacts_durable_data(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            input_url = "https://media.example.test/input.png?signature=input-secret"
            output_url = "https://cdn.example.test/render.mp4?signature=output-secret"
            client = FakeAutoDLClient({
                "task_id": "autodl-task",
                "status": "SUCCESS",
                "request": {"ref_image_0": input_url},
                "results": [{"url": output_url, "type": "video"}],
            })
            provider = FakeAutoDLProvider(client)
            app = make_autodl_app(Path(temporary), provider)
            status, accepted = app.dispatch(
                "POST",
                "/api/comfyui/jobs",
                {
                    "provider": "AUTODL_COMFYUI",
                    "workflow_id": "fake_autodl_workflow",
                    "body": {"image": input_url, "prompt": "test prompt"},
                },
            )
            self.assertEqual(status, 202)
            row = wait_for_terminal(app, accepted["job_id"])
            self.assertEqual(row["status"], "SUCCEEDED")
            self.assertEqual(provider.submitted[0][1]["image"], input_url)
            self.assertEqual(provider.submitted[0][1], {"image": input_url, "prompt": "test prompt"})
            self.assertEqual(client.downloaded_urls, [output_url])
            self.assertEqual(client.wait_timeouts, [1800.0])
            self.assertEqual(row["artifacts"][0]["url"], f"/api/comfyui/jobs/{row['job_id']}/outputs/render.mp4")
            persisted = json.dumps(row)
            self.assertNotIn(input_url, persisted)
            self.assertNotIn(output_url, persisted)
            self.assertNotIn("input-secret", persisted)
            self.assertNotIn("output-secret", persisted)
            self.assertIn("[REMOTE_URL_REDACTED]", persisted)
            with self.assertRaises(ApiError) as retry_error:
                app.dispatch("POST", f"/api/comfyui/jobs/{row['job_id']}/retry", {})
            self.assertEqual(retry_error.exception.status, 409)

    def test_autodl_success_without_downloadable_url_needs_review(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            client = FakeAutoDLClient({"task_id": "autodl-task", "status": "SUCCESS", "results": []})
            app = make_autodl_app(Path(temporary), FakeAutoDLProvider(client))
            _, accepted = app.dispatch(
                "POST",
                "/api/comfyui/jobs",
                {"workflow_id": "fake_autodl_workflow", "body": {"prompt": "test prompt"}},
            )
            row = wait_for_terminal(app, accepted["job_id"])
            self.assertEqual(row["status"], "NEEDS_REVIEW")
            self.assertIn("without downloadable", row["artifact_errors"][0])

    def test_autodl_rejects_ambiguous_body_before_side_effects(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            provider = FakeAutoDLProvider(FakeAutoDLClient({"task_id": "autodl-task", "status": "SUCCESS", "results": []}))
            app = make_autodl_app(Path(temporary), provider)
            before = app.store.list()
            for bad_body in (None, [], "vendor-body"):
                with self.subTest(body=bad_body):
                    with self.assertRaises(ApiError) as raised:
                        app.dispatch(
                            "POST",
                            "/api/comfyui/jobs",
                            {
                                "provider": "AUTODL_COMFYUI",
                                "workflow_id": "fake_autodl_workflow",
                                "body": bad_body,
                            },
                        )
                    self.assertEqual(raised.exception.status, 422)
                    self.assertEqual(provider.submitted, [])
                    self.assertEqual(app.store.list(), before)

    def test_autodl_paid_gate_rejects_before_provider_or_job(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            provider = FakeAutoDLProvider(FakeAutoDLClient({"task_id": "autodl-task", "status": "SUCCESS", "results": []}))
            factory_calls: list[str] = []
            settings = Settings(
                provider="AUTODL_COMFYUI",
                api_host="127.0.0.1",
                api_port=0,
                workflow_dir=Path(temporary) / "workflows",
                job_store=Path(temporary) / "runtime" / "jobs.json",
                allowed_media_roots=(Path(temporary),),
                autodl_allow_paid_submit=False,
            )
            app = ApiApplication(
                settings,
                store=JobStore(settings.job_store),
                registry=WorkflowRegistry(settings.workflow_dir),
                provider_factory=lambda name: (factory_calls.append(name) or provider),
            )
            with self.assertRaises(ApiError) as raised:
                app.dispatch(
                    "POST",
                    "/api/comfyui/jobs",
                    {
                        "provider": "AUTODL_COMFYUI",
                        "workflow_id": "fake_autodl_workflow",
                        "body": {"prompt": "test"},
                    },
                )
            self.assertEqual(raised.exception.status, 409)
            self.assertEqual(factory_calls, [])
            self.assertEqual(app.store.list(), [])

    def test_autodl_poll_deadline_needs_review_and_retains_task_id(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            class RunningClient(FakeAutoDLClient):
                def wait(self, task_id: str, _poll_interval: float, *, timeout: float | None = None) -> Any:
                    if task_id != "autodl-task":
                        raise AssertionError("unexpected task id")
                    self.wait_timeouts.append(timeout)
                    yield {"task_id": task_id, "status": "RUNNING", "progress": 0.5}

            client = RunningClient({})
            provider = FakeAutoDLProvider(client)
            app = make_autodl_app(Path(temporary), provider, poll_timeout=1.0)
            _, accepted = app.dispatch(
                "POST",
                "/api/comfyui/jobs",
                {"workflow_id": "fake_autodl_workflow", "body": {"prompt": "test"}},
            )
            row = wait_for_terminal(app, accepted["job_id"])
            self.assertEqual(row["status"], "NEEDS_REVIEW")
            self.assertEqual(row["task_id"], "autodl-task")
            self.assertTrue(row["poll_timed_out"])
            self.assertEqual(row["poll_timeout_seconds"], 1.0)
            self.assertTrue(row["remote_may_continue"])
            self.assertIn("may still be running", row["error"])
            self.assertEqual(client.wait_timeouts, [1.0])

    def test_autodl_cancel_does_not_claim_remote_cancellation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            client = FakeAutoDLClient({"task_id": "autodl-task", "status": "SUCCESS", "results": []})
            app = make_autodl_app(Path(temporary), FakeAutoDLProvider(client))
            row = app.store.create({
                "provider": "AUTODL_COMFYUI",
                "workflow_id": "minimax_h3_lightx2v_v5",
                "request": {},
                "workflow_hash": None,
            })

            with self.assertRaises(ApiError) as raised:
                app.dispatch("POST", f"/api/comfyui/jobs/{row['job_id']}/cancel", {})

            self.assertEqual(raised.exception.status, 409)
            self.assertEqual((app.store.get(row["job_id"]) or {})["status"], "QUEUED")

    def test_loopback_guard_rejects_public_bind(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            app, _ = make_local_app(Path(temporary))
            with self.assertRaises(ValueError):
                ApiHTTPServer(("0.0.0.0", 0), app)
            settings = Settings(api_host="0.0.0.0", api_port=0, workflow_dir=Path(temporary), job_store=Path(temporary) / "jobs.json")
            with self.assertRaises(ValueError):
                create_server(settings)


if __name__ == "__main__":
    unittest.main(verbosity=2)
