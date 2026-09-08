import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app import create_app  # noqa: E402
from services.asset_resolver import bind_shot  # noqa: E402
from services.job_service import JobStore  # noqa: E402


class DemoV101Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.job_store = JobStore(Path(self.tmp.name) / "jobs.sqlite3")
        self.client = create_app(job_store=self.job_store).test_client()

    def tearDown(self):
        self.tmp.cleanup()

    def test_demo_project_is_defaultable(self):
        response = self.client.get("/api/v10/demo/project")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["project"]["id"], "demo_time_phone")
        self.assertEqual(payload["project"]["default_shot_id"], "SHOT001")
        self.assertEqual([shot["id"] for shot in payload["shots"]], ["SHOT001", "SHOT002"])

    def test_shot_prepare_resolves_assets_voice_and_continuity(self):
        first = self.client.get("/api/v10/demo/shots/SHOT001/prepare")
        self.assertEqual(first.status_code, 200)
        first_payload = first.get_json()
        self.assertEqual(first_payload["status"], "READY")
        self.assertTrue(first_payload["canon_gate"]["pass"])
        self.assertIn("PROP_PHONE_2006", first_payload["resolved_assets"]["asset_ids"])
        self.assertEqual(first_payload["voice_bindings"][0]["id"], "SW25_VOICE_01")

        second = self.client.get("/api/v10/demo/shots/SHOT002/prepare")
        self.assertEqual(second.status_code, 200)
        second_payload = second.get_json()
        self.assertEqual(second_payload["status"], "READY")
        self.assertEqual(second_payload["continuity"]["status"], "READY")
        self.assertEqual(second_payload["continuity"]["changes"][0]["field"], "scene")
        self.assertIn("SCENE_BEICHENG_DESIGN_INSTITUTE", second_payload["resolved_assets"]["asset_ids"])

    def test_unknown_demo_shot_is_404(self):
        self.assertEqual(self.client.get("/api/v10/demo/shots/NOPE/prepare").status_code, 404)

    def test_current_scene_precedes_previous_scene_mentions(self):
        resolved = bind_shot({
            "title": "苏晚晴前往北城设计院提交设计稿",
            "scene_text": "北城设计院门口",
            "script": "她离开设计工作室，来到北城设计院门口。",
            "scene": "SCENE_BEICHENG_DESIGN_INSTITUTE",
            "characters": ["CHAR_SW25_MASTER"],
            "props": ["PROP_ARCHIVE_DESIGN"],
        })
        self.assertIn("SCENE_BEICHENG_DESIGN_INSTITUTE", resolved["asset_ids"])
        self.assertNotIn("SCENE_2006_STUDIO", resolved["asset_ids"])


if __name__ == "__main__":
    unittest.main()
