from __future__ import annotations

import http.client
import json
import threading
import time
import unittest
from pathlib import Path

from comfyui_production.config import Settings
from comfyui_production.server import ApiApplication, ApiError, ApiHTTPServer, create_server
from comfyui_production.store import JobStore
from comfyui_production.workflow import WorkflowRegistry


class FakeProvider:
    def __init__(self) -> None:
        self.submitted: list[dict] = []
        self.client = FakeClient()

    def health(self) -> dict:
        return {"device": "fake", "ok": True}

    def submit(self, graph: dict) -> dict:
        self.submitted.append(graph)
        return {"prompt_id": "fake-prompt"}


class FakeClient:
    def __init__(self) -> None:
        self.uploaded: list[dict] = []

    def upload_file(self, path: Path, *, field_name: str, upload_type: str, overwrite: bool) -> dict:
        self.uploaded.append({
            "path": Path(path),
            "field_name": field_name,
            "upload_type": upload_type,
            "overwrite": overwrite,
        })
        return {"name": f"uploaded_{Path(path).name}"}

    def iter_progress(self, prompt_id: str, _poll_interval: float):
        yield {
            "type": "history",
            "prompt_id": prompt_id,
            "completed": True,
            "entry": self.history(prompt_id)[prompt_id],
        }

    @staticmethod
    def history(prompt_id: str) -> dict:
        return {
            prompt_id: {
                "status": {"status_str": "success"},
                "outputs": {"1": {"gifs": [{"filename": "fake.mp4", "subfolder": "", "type": "output"}]}},
            }
        }

    @staticmethod
    def download_view(_filename: str, subfolder: str = "", file_type: str = "output", destination=None):
        del subfolder, file_type
        target = Path(destination)
        target.write_bytes(b"fake-mp4")
        return target


def _app(tmp_path: Path, provider: FakeProvider | None = None) -> tuple[ApiApplication, FakeProvider]:
    workflow_dir = tmp_path / "workflows"
    workflow_dir.mkdir()
    (workflow_dir / "demo.json").write_text(
        json.dumps({"prompt": {"1": {"class_type": "Test", "inputs": {"text": "{{prompt}}"}}}}),
        encoding="utf-8",
    )
    fake = provider or FakeProvider()
    settings = Settings(
        provider="LOCAL",
        api_host="127.0.0.1",
        api_port=0,
        workflow_dir=workflow_dir,
        job_store=tmp_path / "jobs.json",
        allowed_media_roots=(tmp_path,),
        poll_interval_seconds=0.01,
    )
    app = ApiApplication(
        settings,
        store=JobStore(settings.job_store),
        registry=WorkflowRegistry(workflow_dir),
        provider_factory=lambda _name: fake,
    )
    return app, fake


def _wait_for(app: ApiApplication, job_id: str) -> dict:
    for _ in range(100):
        row = app.store.get(job_id)
        if row and row.get("status") in {"SUCCEEDED", "FAILED", "CANCELLED", "NEEDS_REVIEW"}:
            return row
        time.sleep(0.01)
    raise AssertionError("job did not reach a terminal state")


class ServerContractsTest(unittest.TestCase):
    def test_dispatch_lists_workflows_and_runs_local_job(self) -> None:
        with self.subTest("local job"):
            import tempfile
            with tempfile.TemporaryDirectory() as directory:
                app, fake = _app(Path(directory))

                status, response = app.dispatch("GET", "/api/comfyui/workflows")
                self.assertEqual(status, 200)
                self.assertEqual(response["workflows"][0]["id"], "demo")

                status, response = app.dispatch(
                    "POST",
                    "/api/comfyui/jobs",
                    {"workflow_id": "demo", "inputs": {"prompt": "苏晚晴走向窗边"}},
                )
                self.assertEqual(status, 202)
                row = _wait_for(app, response["job_id"])
                self.assertEqual(row["status"], "SUCCEEDED")
                self.assertEqual(fake.submitted[0]["1"]["inputs"]["text"], "苏晚晴走向窗边")
                self.assertIn("prompt_id", row)

    def test_local_wan_media_tokens_are_uploaded_and_substituted(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workflow_dir = root / "workflows"
            workflow_dir.mkdir()
            source_workflow = Path(__file__).resolve().parents[1] / "workflows" / "wan2.1_i2v_ref_5s_local.json"
            workflow_id = "wan2.1_i2v_ref_5s_local"
            (workflow_dir / f"{workflow_id}.json").write_text(source_workflow.read_text(encoding="utf-8"), encoding="utf-8")

            image = root / "character.png"
            video = root / "driving.mp4"
            image.write_bytes(b"fake-image")
            video.write_bytes(b"fake-video")

            fake = FakeProvider()
            settings = Settings(
                provider="LOCAL",
                api_host="127.0.0.1",
                api_port=0,
                workflow_dir=workflow_dir,
                job_store=root / "jobs.json",
                allowed_media_roots=(root,),
                poll_interval_seconds=0.01,
            )
            app = ApiApplication(
                settings,
                store=JobStore(settings.job_store),
                registry=WorkflowRegistry(workflow_dir),
                provider_factory=lambda _name: fake,
            )

            status, response = app.dispatch(
                "POST",
                "/api/comfyui/jobs",
                {
                    "workflow_id": workflow_id,
                    "media": {
                        "character_a_image": {"path": str(image), "media_type": "image"},
                        "driving_video": {"path": str(video), "media_type": "video"},
                    },
                },
            )
            self.assertEqual(status, 202)
            row = _wait_for(app, response["job_id"])
            self.assertEqual(row["status"], "SUCCEEDED")
            self.assertEqual([item["path"] for item in fake.client.uploaded], [image, video])
            self.assertEqual(fake.submitted[0]["4"]["inputs"]["image"], "uploaded_character.png")
            self.assertEqual(fake.submitted[0]["1"]["inputs"]["video"], "uploaded_driving.mp4")
            self.assertEqual(len(row["uploaded_media"]), 2)
            self.assertTrue(all(len(item["sha256"]) == 64 for item in row["uploaded_media"]))
            self.assertTrue(all(item["size_bytes"] > 0 for item in row["uploaded_media"]))


    def test_http_server_is_loopback_only_and_health_is_json(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            app, _ = _app(Path(directory))
            server = ApiHTTPServer(("127.0.0.1", 0), app)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
                conn.request("GET", "/api/comfyui/health")
                response = conn.getresponse()
                body = json.loads(response.read().decode("utf-8"))
                self.assertEqual(response.status, 200)
                self.assertTrue(body["ok"])
                self.assertTrue(body["provider_ok"])
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)


    def test_non_loopback_bind_is_rejected(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            app, _ = _app(root)
            with self.assertRaisesRegex(ValueError, "loopback"):
                ApiHTTPServer(("0.0.0.0", 0), app)

            bad = Settings(api_host="0.0.0.0", api_port=0, workflow_dir=root, job_store=root / "jobs.json")
            with self.assertRaisesRegex(ValueError, "loopback"):
                create_server(bad)

    def test_second_loopback_listener_is_rejected(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            app, _ = _app(Path(directory))
            first = ApiHTTPServer(("127.0.0.1", 0), app)
            try:
                with self.assertRaises(OSError):
                    ApiHTTPServer(("127.0.0.1", first.server_port), app)
            finally:
                first.server_close()


    def test_job_request_is_redacted_before_persistence(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            app, _ = _app(Path(directory))
            status, response = app.dispatch(
                "POST",
                "/api/comfyui/jobs",
                {
                    "workflow_id": "demo",
                    "inputs": {"prompt": "ok", "api_token": "do-not-store"},
                },
            )
            self.assertEqual(status, 202)
            row = _wait_for(app, response["job_id"])
            serialized = json.dumps(row, ensure_ascii=False)
            self.assertNotIn("do-not-store", serialized)
            self.assertIn("[REDACTED]", serialized)


    def test_unknown_route_is_404(self) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            app, _ = _app(Path(directory))
            with self.assertRaises(ApiError) as exc_info:
                app.dispatch("GET", "/nope")
            self.assertEqual(exc_info.exception.status, 404)


if __name__ == "__main__":
    unittest.main()
