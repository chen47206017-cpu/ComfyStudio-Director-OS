import sys
import tempfile
import unittest
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

import v10_core  # noqa: E402
from app import create_app  # noqa: E402
from services.job_service import JobStore  # noqa: E402


class FakeComfy:
    def __init__(self):
        self.submissions = []

    def health(self):
        return {"connected": True, "status": 200}

    def object_info(self):
        return {"connected": True, "nodes": {"Test": {}}}

    def queue(self):
        return {"connected": True, "queue_running": [], "queue_pending": []}

    def history(self, prompt_id=None):
        return {"connected": True, "history": {}, "prompt_id": prompt_id}

    def submit(self, workflow, client_id=None, dry_run=False):
        self.submissions.append(workflow)
        return {"submitted": False, "dry_run": True, "prompt": workflow, "prompt_id": "fake-prompt-1"}

    def cancel(self, prompt_id=None):
        return {"connected": True, "status": 200, "cancelled": True, "prompt_id": prompt_id}


class FakeRegistry:
    def __init__(self):
        self.worker = {
            "id": "fake-8189",
            "name": "Fake H3 Worker",
            "base_url": "http://fake:8189",
            "lane": "local_h3",
            "priority": 10,
            "status": "READY",
            "node_classes": ["MiniMaxH3ReferenceToVideo", "MiniMaxH3MotionContextRAM", "MiniMaxH3Extender", "LoadImage", "SaveVideo"],
            "model_inventory": [
                "minimax_h3_ref2va_pruned_int8_convrot.safetensors",
                "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors",
                "minimax_h3_video_vae_fp16.safetensors",
                "minimax_h3_audio_vae_fp32.safetensors",
            ],
            "capabilities": {"h3": True, "motion_context": True, "extender": True},
        }

    def discover(self):
        return [self.worker]

    def select(self, lane=None):
        return self.worker if lane in (None, "local_h3") else None


class BackendV10Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_canvas = v10_core.CANVAS_PATH
        self.old_memory = v10_core.MEMORY_PATH
        v10_core.CANVAS_PATH = Path(self.tmp.name) / "canvas.json"
        v10_core.MEMORY_PATH = Path(self.tmp.name) / "memory.json"
        self.fake_comfy = FakeComfy()
        self.client = create_app(self.fake_comfy).test_client()
        self.job_store = JobStore(Path(self.tmp.name) / "jobs.sqlite3")

    def tearDown(self):
        v10_core.CANVAS_PATH = self.old_canvas
        v10_core.MEMORY_PATH = self.old_memory
        self.tmp.cleanup()

    def test_director_and_health(self):
        self.assertEqual(self.client.get("/director/").status_code, 200)
        home = self.client.get("/")
        self.assertEqual(home.status_code, 200)
        self.assertIn(b"root", home.data)
        html = home.get_data(as_text=True)
        bundle_paths = re.findall(r'(?:src|href)="(/assets/[^\"]+)"', html)
        self.assertGreaterEqual(len(bundle_paths), 2)
        for bundle_path in bundle_paths:
            self.assertEqual(self.client.get(bundle_path).status_code, 200)
        response = self.client.get("/api/v10/health")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["ok"])
        self.assertEqual(response.get_json()["comfy"]["status"], 200)
        self.assertRegex(response.get_json()["now"], r"\+08:00$")

    def test_production_assets_route_uses_registry(self):
        response = self.client.get("/api/v10/assets")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertGreaterEqual(payload["total"], 1)
        self.assertTrue(any(item.get("id") == "SCENE_2006_STUDIO" for item in payload["assets"]))

    def test_workers_capabilities_capsule_and_jobs(self):
        app = create_app(self.fake_comfy, FakeRegistry(), job_store=self.job_store)
        client = app.test_client()
        workers = client.get("/api/v10/workers").get_json()
        self.assertEqual(workers["status"], "READY")
        self.assertEqual(workers["workers"][0]["id"], "fake-8189")
        capabilities = client.get("/api/v10/capabilities").get_json()
        self.assertIn(capabilities["status"], {"READY", "DEGRADED"})
        self.assertTrue(any(item["id"] == "comfy.h3" and item["status"] == "READY" for item in capabilities["checks"]))
        capsule = client.get("/api/v10/workflows/capsules/h3_reference_to_video")
        self.assertEqual(capsule.status_code, 200)
        preflight = client.post("/api/v10/workflows/capsules/h3_reference_to_video/preflight?lane=local_h3")
        self.assertEqual(preflight.status_code, 200)
        first = client.post("/api/v10/jobs", json={"idempotency_key": "same-job", "lane": "local_h3"})
        replay = client.post("/api/v10/jobs", json={"idempotency_key": "same-job", "lane": "local_h3"})
        self.assertEqual(first.status_code, 201)
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(replay.get_json()["status"], "IDEMPOTENT_REPLAY")
        job_id = first.get_json()["job"]["id"]
        cancelled = client.post(f"/api/v10/jobs/{job_id}/cancel")
        self.assertEqual(cancelled.status_code, 200)
        self.assertEqual(cancelled.get_json()["job"]["status"], "CANCELLED")

    def test_canvas_revision_cas(self):
        initial = self.client.get("/api/v10/canvas").get_json()
        self.assertEqual(initial["revision"], 0)
        saved = self.client.post(
            "/api/v10/canvas",
            json={"expected_revision": 0, "canvas": {"nodes": [{"id": "n1"}], "edges": []}},
        )
        self.assertEqual(saved.status_code, 200)
        self.assertEqual(saved.get_json()["revision"], 1)
        conflict = self.client.post(
            "/api/v10/canvas",
            json={"expected_revision": 0, "canvas": {"nodes": [], "edges": []}},
        )
        self.assertEqual(conflict.status_code, 409)
        self.assertEqual(conflict.get_json()["error"], "revision_conflict")

    def test_gate_prompt_and_dry_run(self):
        blocked = self.client.post(
            "/api/v10/gates/canon", json={"shot": {"year": 2006, "props": ["smartphone"]}}
        )
        self.assertEqual(blocked.status_code, 422)
        self.assertFalse(blocked.get_json()["pass"])
        prompt_blocked = self.client.post(
            "/api/v10/prompts/compile", json={"shot": {"year": 2006, "props": ["smartphone"]}}
        )
        self.assertEqual(prompt_blocked.status_code, 422)
        comfy_blocked = self.client.post(
            "/api/v10/comfy/submit",
            json={"dry_run": True, "shot": {"year": 2006, "props": ["smartphone"]}, "workflow": {"1": {}}},
        )
        self.assertEqual(comfy_blocked.status_code, 422)
        self.assertEqual(self.fake_comfy.submissions, [])
        self.assertEqual(
            self.client.post("/api/v8/prompt/build", json={"shot": {"year": 2006, "props": ["smartphone"]}}).status_code,
            422,
        )
        phone_blocked = self.client.post(
            "/api/v10/gates/canon", json={"shot": {"year": "2006年", "requires_phone": True, "props": ["telephone"]}}
        )
        self.assertEqual(phone_blocked.status_code, 422)
        self.assertTrue(any(item["rule_id"] == "PROP_001" for item in phone_blocked.get_json()["errors"]))
        prompt = self.client.post(
            "/api/v10/prompts/compile",
            json={"shot": {"scene": "2006设计工作室", "action": "接电话"}, "negative": ["水印"]},
        )
        self.assertEqual(prompt.status_code, 200)
        self.assertIn("2006设计工作室", prompt.get_json()["positive"])
        self.assertIn("水印", prompt.get_json()["negative"])
        self.assertIn("negative_categories", prompt.get_json())
        self.assertIn("canon", prompt.get_json()["negative_categories"])
        dry_run = self.client.post("/api/v10/comfy/submit", json={"dry_run": True, "workflow": {"1": {}}})
        self.assertEqual(dry_run.status_code, 200)
        self.assertTrue(dry_run.get_json()["dry_run"])

    def test_legacy_shots_route_is_unique(self):
        rules = [rule for rule in self.client.application.url_map.iter_rules() if rule.rule == "/api/shots"]
        self.assertEqual(len(rules), 1)
        self.assertEqual(self.client.get("/api/shots").status_code, 200)

    def test_bom_json_reader(self):
        path = Path(self.tmp.name) / "bom.json"
        path.write_text("\ufeff{\"ok\": true}", encoding="utf-8")
        self.assertEqual(v10_core.read_json(path), {"ok": True})


if __name__ == "__main__":
    unittest.main()
