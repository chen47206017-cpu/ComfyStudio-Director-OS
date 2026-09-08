from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from comfyui_production.config import Settings
from comfyui_production.h3 import (
    AUTODL_IMAGE_AUDIO_WORKFLOW,
    AUTODL_LIGHT_WORKFLOW,
    ENGINE_ID,
    LOCAL_STATUS,
    MiniMaxH3PlanError,
    h3_catalog,
    plan_autodl_dry_run,
)
from comfyui_production.server import ApiApplication, ApiError
from comfyui_production.store import JobStore
from comfyui_production.workflow import WorkflowRegistry


IMAGE_URL = "https://media.example.test/reference.png"
AUDIO_URL = "https://media.example.test/voice.wav"


class H3ContractsTest(unittest.TestCase):
    def test_catalog_exposes_one_blocked_local_dry_run_engine(self) -> None:
        catalog = h3_catalog()
        self.assertEqual(catalog["id"], ENGINE_ID)
        self.assertEqual(catalog["status"], LOCAL_STATUS)
        self.assertEqual(catalog["autodl"]["status"], "DRY_RUN_ONLY")
        self.assertEqual(catalog["autodl"]["vendor_schema_status"], "USER_SUPPLIED_UNVERIFIED")
        self.assertFalse(catalog["autodl"]["submit_allowed"])
        self.assertIsNone(catalog["autodl"]["workflows"][0]["schema_evidence"])
        self.assertEqual(catalog["selector"]["path"], "/api/comfyui/h3/dry-run")
        self.assertFalse(catalog["schema"]["additionalProperties"])
        self.assertEqual(catalog["schema"]["properties"]["reference_images"]["maxItems"], 9)

    def test_image_only_dry_run_selects_light_workflow(self) -> None:
        plan = plan_autodl_dry_run({
            "engine": ENGINE_ID,
            "prompt": "stable live-action identity",
            "duration": 5,
            "resolution": "768p\u7ad6",
            "reference_images": [IMAGE_URL, "https://media.example.test/clothes.png"],
            "seed": 7,
        })
        self.assertEqual(plan["workflow_id"], AUTODL_LIGHT_WORKFLOW)
        self.assertEqual(plan["execution"], "DRY_RUN_ONLY")
        self.assertEqual(plan["planning_input"]["reference_images"][0], IMAGE_URL)
        self.assertEqual(plan["planning_input"]["reference_images"][1], "https://media.example.test/clothes.png")
        self.assertEqual(plan["planning_input"]["seed"], 7)
        self.assertNotIn("body", plan)
        self.assertEqual(plan["vendor_submission"]["status"], "BLOCKED_PENDING_SCHEMA_EVIDENCE")
        self.assertFalse(plan["vendor_submission"]["submit_allowed"])
        self.assertIsNone(plan["vendor_submission"]["schema_evidence"])

    def test_image_audio_dry_run_selects_audio_workflow(self) -> None:
        plan = plan_autodl_dry_run({
            "prompt": "a close-up with dialogue",
            "reference_images": [IMAGE_URL],
            "reference_audios": [AUDIO_URL],
        })
        self.assertEqual(plan["workflow_id"], AUTODL_IMAGE_AUDIO_WORKFLOW)
        self.assertEqual(plan["planning_input"]["reference_audios"], [AUDIO_URL])
        self.assertNotIn("seed", plan["planning_input"])
        self.assertEqual(plan["vendor_submission"]["schema_status"], "USER_SUPPLIED_UNVERIFIED")

    def test_unsupported_or_unsafe_h3_input_fails_closed(self) -> None:
        base = {"prompt": "ok", "reference_images": [IMAGE_URL]}
        cases = [
            ({"reference_images": [r"F:\\AI\reference.png"]}, "AutoDL-reachable"),
            ({"reference_images": ["http://127.0.0.1/reference.png"]}, "private address"),
            ({"reference_images": [IMAGE_URL] * 10}, "1 to 9"),
            ({"reference_videos": ["https://media.example.test/reference.mp4"]}, "reference_videos"),
            ({"resolution": "1080p\u7ad6"}, "project dry-run planner"),
            ({"negative_prompt": "not part of the planner"}, "unsupported planner field"),
        ]
        for changes, message in cases:
            with self.subTest(changes=changes):
                payload = dict(base)
                payload.update(changes)
                with self.assertRaisesRegex(MiniMaxH3PlanError, message):
                    plan_autodl_dry_run(payload)

    def test_spec_records_the_same_blocked_dry_run_scope(self) -> None:
        spec_path = Path(__file__).resolve().parents[1] / "workflows" / "specs" / "07_minimax_h3_unified.json"
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        self.assertEqual(spec["engine"], ENGINE_ID)
        self.assertEqual(spec["status"], LOCAL_STATUS)
        autodl = spec["providers"]["AUTODL_COMFYUI"]
        self.assertEqual(autodl["status"], "DRY_RUN_ONLY")
        self.assertEqual(autodl["workflow_schema_status"], "USER_SUPPLIED_UNVERIFIED")
        self.assertFalse(autodl["submit_allowed"])
        self.assertEqual(spec["vendor_submission"]["status"], "BLOCKED_PENDING_SCHEMA_EVIDENCE")

    def test_api_exposes_plan_without_provider_or_job_side_effects(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            settings = Settings(
                workflow_dir=root / "workflows",
                job_store=root / "jobs.json",
                allowed_media_roots=(root,),
            )

            def unexpected_provider(_name: str):
                raise AssertionError("H3 dry run must not create a provider")

            app = ApiApplication(
                settings,
                store=JobStore(settings.job_store),
                registry=WorkflowRegistry(settings.workflow_dir),
                provider_factory=unexpected_provider,
            )
            status, catalog = app.dispatch("GET", "/api/comfyui/engines")
            self.assertEqual(status, 200)
            self.assertEqual(catalog["engines"][0]["id"], ENGINE_ID)

            status, plan = app.dispatch("POST", "/api/comfyui/h3/dry-run", {
                "prompt": "stable identity",
                "reference_images": [IMAGE_URL],
            })
            self.assertEqual(status, 200)
            self.assertEqual(plan["workflow_id"], AUTODL_LIGHT_WORKFLOW)
            self.assertEqual(plan["planning_input"]["reference_images"], ["[REMOTE_URL_REDACTED]"])
            self.assertNotIn("body", plan)
            self.assertFalse(plan["vendor_submission"]["submit_allowed"])
            self.assertEqual(app.store.list(), [])

            with self.assertRaisesRegex(ApiError, "dry-run only") as engine_error:
                app.dispatch("POST", "/api/comfyui/jobs", {"engine": ENGINE_ID})
            self.assertEqual(engine_error.exception.status, 409)
            with self.assertRaisesRegex(ApiError, "submission is disabled") as workflow_error:
                app.dispatch("POST", "/api/comfyui/jobs", {"workflow_id": AUTODL_LIGHT_WORKFLOW})
            self.assertEqual(workflow_error.exception.status, 409)


if __name__ == "__main__":
    unittest.main()
