import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from v10_core import ComfyClient  # noqa: E402
from services.job_service import JobStore  # noqa: E402
from services.workflow_capsule import WorkflowCapsuleStore  # noqa: E402
from services import worker_registry  # noqa: E402


class FakeResultClient(ComfyClient):
    def __init__(self):
        super().__init__("http://fake", timeout=0.01)

    def history(self, prompt_id=None):
        return {
            "connected": True,
            "history": {
                prompt_id: {
                    "outputs": {
                        "92": {"gifs": [{"filename": "video.mp4", "subfolder": "", "type": "output"}]}
                    }
                }
            },
        }


class ComfyExecutionTests(unittest.TestCase):
    def test_history_output_descriptors_are_normalized(self):
        client = FakeResultClient()
        descriptors = client.collect_output_descriptors(client.history("p1"))
        self.assertEqual(len(descriptors), 1)
        self.assertEqual(descriptors[0]["filename"], "video.mp4")
        self.assertEqual(descriptors[0]["node_id"], "92")

    def test_wait_for_result_reports_completed(self):
        client = FakeResultClient()
        result = client.wait_for_result("p1", timeout=0.1, interval=0.01)
        self.assertEqual(result["status"], "COMPLETED")

    def test_job_events_and_outputs_are_durable(self):
        with tempfile.TemporaryDirectory() as folder:
            store = JobStore(Path(folder) / "jobs.sqlite3")
            job, duplicate = store.create({"idempotency_key": "k1", "lane": "local_h3"})
            self.assertFalse(duplicate)
            store.transition(job["id"], "QUEUED", {"prompt_id": "p1"}, prompt_id="p1")
            store.add_output(job["id"], str(Path(folder) / "video.mp4"), "abc", "video/mp4", True)
            self.assertEqual(store.events(job["id"])[-1]["status"], "QUEUED")
            self.assertTrue(store.outputs(job["id"])[0]["verified"])


class HttpOnlyWorkerEvidenceTests(unittest.TestCase):
    def test_worker_registry_reports_http_observed_inventory(self):
        model_name = "minimax_h3_ref2va_pruned_int8_convrot.safetensors"
        stats = {"system": {"comfyui_version": "0.34.0"}, "devices": []}
        object_info = {
            "MiniMaxH3ReferenceToVideo": {
                "input": {"required": {"model": [[model_name]]}}
            }
        }
        with patch.object(worker_registry, "_ports", return_value=[8189]), patch.object(
            worker_registry,
            "_request",
            side_effect=[(stats, 1.0, None), (object_info, 1.0, None)],
        ):
            worker = worker_registry.WorkerRegistry().discover()[0]

        self.assertEqual(worker["model_inventory_source"], "/object_info")
        self.assertEqual(worker["model_inventory_status"], "HTTP_OBSERVED")
        self.assertIn(model_name, worker["model_inventory"])
        self.assertNotIn("model_roots", worker)
        self.assertFalse(hasattr(worker_registry, "_model_roots"))

    def test_capsule_preflight_keeps_http_model_evidence_unverified_as_files(self):
        store = WorkflowCapsuleStore(PROJECT_ROOT)
        capsule = store.get("h3_reference_to_video")
        self.assertIsNotNone(capsule)
        assert capsule is not None
        worker = {
            "id": "fake-8189",
            "node_classes": capsule["required_node_classes"],
            "model_inventory": capsule["required_models"],
            "model_inventory_source": "/object_info",
        }
        ready = store.preflight("h3_reference_to_video", worker)
        self.assertEqual(ready["status"], "READY")
        self.assertFalse(ready["model_inventory_verified"])
        self.assertEqual(ready["model_inventory_status"], "HTTP_OBSERVED")
        self.assertTrue(all(item["status"] == "HTTP_OBSERVED" for item in ready["model_availability"]))
        self.assertTrue(
            all(item["file_integrity"] == "UNVERIFIED_NOT_PERMITTED_HTTP_ONLY" for item in ready["model_availability"])
        )

        unverified = store.preflight("h3_reference_to_video", {**worker, "model_inventory": []})
        self.assertEqual(unverified["status"], "UNVERIFIED")
        self.assertEqual(unverified["model_inventory_status"], "UNVERIFIED")
        self.assertTrue(all(item["status"] == "UNVERIFIED" for item in unverified["model_availability"]))


if __name__ == "__main__":
    unittest.main()
