from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from comfyui_production.config import Settings, _read_dotenv
from comfyui_production.media import MediaError, MediaResolver, clean_path_text
from comfyui_production.server import ApiApplication
from comfyui_production.store import JobStore
from comfyui_production.workflow import WorkflowError, substitute_workflow, workflow_hash


class CoreContractsTest(unittest.TestCase):
    def test_settings_default_api_port_targets_managed_h3_control_plane(self) -> None:
        with patch("comfyui_production.config._read_dotenv", return_value={}):
            settings = Settings.from_env({})
        self.assertEqual(settings.api_port, 8092)

    def test_api_scripts_require_h3_capability_routes(self) -> None:
        root = Path(__file__).resolve().parents[1]
        env_example = (root / ".env.example").read_text(encoding="utf-8")
        checker = (root / "scripts" / "check_comfyui_api.ps1").read_text(encoding="utf-8")
        launcher = (root / "scripts" / "start_comfyui_api.ps1").read_text(encoding="utf-8")
        documents = [
            root / "README_COMFYUI_PRODUCTION.md",
            root / "docs" / "WEB_INTEGRATION.md",
            root / "docs" / "INSTALL_WINDOWS.md",
            root / "docs" / "TROUBLESHOOTING.md",
            root / "docs" / "DISK_AND_RUNTIME_PLAN.md",
            root / "handoff" / "current_state.md",
        ]
        self.assertIn("COMFY_API_PORT=8092", env_example)
        self.assertIn("COMFY_LOCAL_URL=http://127.0.0.1:8188", env_example)
        self.assertIn("AUTODL_ALLOW_PAID_SUBMIT=0", env_example)
        self.assertIn("AUTODL_POLL_TIMEOUT_SECONDS=1800", env_example)
        self.assertNotIn("COMFY_LOCAL_HOST=", env_example)
        self.assertNotIn("COMFY_LOCAL_PORT=", env_example)
        self.assertIn("DefaultPort = 8092", checker)
        self.assertIn("DefaultPort = 8092", launcher)
        for source in (checker, launcher):
            self.assertIn("/engines", source)
            self.assertIn("/h3/dry-run", source)
            self.assertIn("DRY_RUN_ONLY", source)
            self.assertIn("BLOCKED_LOCAL_H3", source)
        for document in documents:
            text = document.read_text(encoding="utf-8")
            self.assertIn("8092", text, document.name)
            self.assertIn("health-only", text, document.name)
        install_doc = (root / "docs" / "INSTALL_WINDOWS.md").read_text(encoding="utf-8")
        self.assertIn("-Port", install_doc)
        self.assertIn("COMFY_LOCAL_HOST", install_doc)
        self.assertIn("COMFY_LOCAL_PORT", install_doc)

    def test_autodl_guard_defaults_and_rejects_invalid_timeout_or_boolean(self) -> None:
        with patch("comfyui_production.config._read_dotenv", return_value={}):
            defaults = Settings.from_env({})
            self.assertFalse(defaults.autodl_allow_paid_submit)
            self.assertEqual(defaults.autodl_poll_timeout_seconds, 1800.0)

            enabled = Settings.from_env({
                "AUTODL_ALLOW_PAID_SUBMIT": "yes",
                "AUTODL_POLL_TIMEOUT_SECONDS": "42.5",
            })
            self.assertTrue(enabled.autodl_allow_paid_submit)
            self.assertEqual(enabled.autodl_poll_timeout_seconds, 42.5)

            with self.assertRaisesRegex(ValueError, "boolean setting"):
                Settings.from_env({"AUTODL_ALLOW_PAID_SUBMIT": "maybe"})
            with self.assertRaisesRegex(ValueError, "between 1 and 86400"):
                Settings.from_env({"AUTODL_POLL_TIMEOUT_SECONDS": "0"})
            with self.assertRaisesRegex(ValueError, "finite"):
                Settings.from_env({"AUTODL_POLL_TIMEOUT_SECONDS": "nan"})

    def test_final_preset_and_local_auto_open_contract_are_explicit(self) -> None:
        root = Path(__file__).resolve().parents[1]
        source = (root / "src" / "comfyui_production" / "server.py").read_text(encoding="utf-8")
        launcher = (root / "scripts" / "start_comfyui_local.ps1").read_text(encoding="utf-8")
        presets = {item["id"]: item for item in ApiApplication._presets()}
        final = presets["CLOUD_5090_QUALITY"]
        self.assertEqual(
            {key: final[key] for key in ("width", "height", "fps", "frames", "duration_seconds", "aspect_ratio", "resolution_label")},
            {
                "width": 1080,
                "height": 1920,
                "fps": 24,
                "frames": 121,
                "duration_seconds": 5.04,
                "aspect_ratio": "9:16",
                "resolution_label": "1080p竖",
            },
        )
        self.assertEqual(final["subtitle_style"], "SUBTITLE_LOCK_V1")
        self.assertTrue(final["requires_burned_subtitles"])
        self.assertEqual(final["render_strategy"], "verified_direct_renderer_or_validated_upscale")
        self.assertEqual(final["h3_source_resolution"], "UNVERIFIED_PER_WORKFLOW_DRAWER")
        self.assertEqual(presets["LOCAL_DRAFT"]["delivery_stage"], "technical_smoke_only")
        self.assertIn('"CLOUD_5090_QUALITY"', source)
        self.assertIn('"width": 1080', source)
        self.assertIn('"height": 1920', source)
        self.assertIn('"frames": 121', source)
        self.assertIn('"subtitle_style": "SUBTITLE_LOCK_V1"', source)
        self.assertIn('"requires_burned_subtitles": True', source)
        self.assertIn("function Resolve-AutoOpen", launcher)
        self.assertIn("[switch]$NoBrowser", launcher)
        self.assertIn("COMFY_AUTO_OPEN", launcher)

    def test_h3_docs_do_not_promote_unverified_legacy_vendor_fields(self) -> None:
        root = Path(__file__).resolve().parents[1]
        h3_source = (root / "src" / "comfyui_production" / "h3.py").read_text(encoding="utf-8")
        api_doc = (root / "docs" / "AUTODL_COMFYUI_API.md").read_text(encoding="utf-8")
        h3_doc = (root / "docs" / "H3_WORKFLOW.md").read_text(encoding="utf-8")
        cloud_doc = (root / "docs" / "CLOUD_5090.md").read_text(encoding="utf-8")
        web_doc = (root / "docs" / "WEB_INTEGRATION.md").read_text(encoding="utf-8")

        self.assertIn("USER_SUPPLIED_UNVERIFIED", h3_source)
        self.assertIn("BLOCKED_PENDING_SCHEMA_EVIDENCE", h3_source)
        for document in (api_doc, h3_doc, cloud_doc, web_doc):
            self.assertIn("USER_SUPPLIED_UNVERIFIED", document)
        self.assertNotIn("ref_image_0", api_doc)
        self.assertNotIn("ref_audio_0", api_doc)
        self.assertNotIn("direct_1080p_or_validated_upscale", h3_source)

    def test_snapshot_and_blocked_specs_use_current_final_target(self) -> None:
        root = Path(__file__).resolve().parents[1]
        snapshot = json.loads((root / "comfyui.snapshot.json").read_text(encoding="utf-8"))
        self.assertEqual(snapshot["network"]["integration_api_url"], "http://127.0.0.1:8092")
        self.assertIn("live process reload", snapshot["network"]["integration_api_status"])
        for name in (
            "01_three_images_masterframe_i2v.json",
            "02_two_images_one_video_dual_character_control.json",
        ):
            spec = json.loads((root / "workflows" / "specs" / name).read_text(encoding="utf-8"))
            self.assertIn("1080x1920", spec["presets"]["CLOUD_5090_QUALITY"])
            self.assertIn("unverified", spec["presets"]["CLOUD_5090_QUALITY"])
        export_spec = json.loads(
            (root / "workflows" / "specs" / "06_upscale_interpolate_export.json").read_text(encoding="utf-8")
        )
        self.assertIn("1080x1920", export_spec["quality_gates"][0])
        self.assertIn("BLOCKED", export_spec["quality_gates"][0])

    def test_settings_from_env_resolves_relative_paths_and_provider(self) -> None:
        settings = Settings.from_env(
            {
                "COMFY_PROVIDER": " remote_static ",
                "COMFY_REMOTE_URL": "https://example.invalid/comfy/",
                "COMFY_API_PORT": "8123",
                "COMFY_ALLOWED_MEDIA_ROOTS": r"F:\\AI短剧;sample_assets",
                "COMFY_JOB_STORE": "runtime/test-jobs.json",
            }
        )
        self.assertEqual(settings.provider, "REMOTE_STATIC")
        self.assertEqual(settings.base_url, "https://example.invalid/comfy")
        self.assertEqual(settings.api_port, 8123)
        self.assertTrue(settings.job_store.is_absolute())
        self.assertEqual(settings.allowed_media_roots[0], Path(r"F:\AI短剧"))
        self.assertTrue(settings.allowed_media_roots[1].is_absolute())

    def test_project_dotenv_is_a_fallback_and_explicit_environment_wins(self) -> None:
        dotenv_values = {
            "COMFY_PROVIDER": "AUTODL_COMFYUI",
            "AUTODL_API_TOKEN": "dotenv-token",
            "COMFY_API_PORT": "8199",
            "COMFY_LOCAL_URL": "http://127.0.0.1:8198",
        }
        with patch("comfyui_production.config._read_dotenv", return_value=dotenv_values) as read_dotenv:
            settings = Settings.from_env(
                {
                    "COMFY_PROVIDER": "LOCAL",
                    "AUTODL_API_TOKEN": "",
                    "COMFY_API_PORT": "8123",
                }
            )

        self.assertEqual(settings.provider, "LOCAL")
        self.assertEqual(settings.autodl_api_token, "")
        self.assertEqual(settings.api_port, 8123)
        self.assertEqual(settings.local_url, "http://127.0.0.1:8198")
        self.assertEqual(read_dotenv.call_args.args[0].name, ".env")

    def test_dotenv_parser_supports_quotes_and_ignores_invalid_or_example_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            dotenv = directory / ".env"
            dotenv.write_text(
                "\n# comment\nA=plain\nB='single quoted'\nC=\"double quoted\"\n"
                "export D=exported\nMALFORMED\n1INVALID=value\nBROKEN='quote\n",
                encoding="utf-8",
            )
            example = directory / ".env.example"
            example.write_text("SHOULD_NOT_LOAD=value\n", encoding="utf-8")

            self.assertEqual(
                _read_dotenv(dotenv),
                {"A": "plain", "B": "single quoted", "C": "double quoted", "D": "exported"},
            )
            self.assertEqual(_read_dotenv(example), {})

    @unittest.skipUnless(shutil.which("powershell"), "Windows PowerShell is required")
    def test_api_check_script_uses_dotenv_port_when_process_env_is_absent(self) -> None:
        source = Path(__file__).resolve().parents[1] / "scripts" / "check_comfyui_api.ps1"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            scripts = root / "scripts"
            scripts.mkdir()
            target = scripts / source.name
            shutil.copy2(source, target)
            (root / ".env").write_text("COMFY_API_PORT='58191'\n", encoding="utf-8")
            env = os.environ.copy()
            env.pop("COMFY_API_PORT", None)
            dotenv_completed = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(target)],
                cwd=root,
                env=env,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            env["COMFY_API_PORT"] = "58192"
            environment_completed = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(target)],
                cwd=root,
                env=env,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            env["COMFY_API_PORT"] = " 58193 "
            whitespace_completed = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(target)],
                cwd=root,
                env=env,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

        self.assertNotEqual(dotenv_completed.returncode, 0)
        self.assertIn("127.0.0.1:58191", dotenv_completed.stderr)
        self.assertNotEqual(environment_completed.returncode, 0)
        self.assertIn("127.0.0.1:58192", environment_completed.stderr)
        self.assertNotEqual(whitespace_completed.returncode, 0)
        self.assertIn("127.0.0.1:58193", whitespace_completed.stderr)

    def test_clean_path_text_removes_directional_controls(self) -> None:
        self.assertEqual(clean_path_text("\u202aF:\\AI短剧\\苏晚晴45.png\u202c"), r"F:\AI短剧\苏晚晴45.png")

    def test_media_resolver_rejects_outside_root_and_accepts_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            allowed = root / "allowed"
            allowed.mkdir()
            image = allowed / "ref.png"
            image.write_bytes(b"png-placeholder")
            resolver = MediaResolver((allowed,), max_upload_mb=1)

            ref = resolver.resolve(str(image), expected_type="image")
            self.assertEqual(ref.path, image.resolve())
            self.assertEqual(ref.media_type, "image")
            self.assertEqual(len(ref.sha256), 64)

            outside = root / "outside.png"
            outside.write_bytes(b"x")
            with self.assertRaisesRegex(MediaError, "outside"):
                resolver.resolve(str(outside))

    def test_workflow_substitution_is_deep_and_does_not_mutate(self) -> None:
        source = {"prompt": "{{scene.prompt}}", "frames": ["{{frames}}", 4], "nested": {"seed": "{{seed}}"}}
        result = substitute_workflow(source, {"scene.prompt": "人物走向窗边", "frames": 81, "seed": 42})
        self.assertEqual(result, {"prompt": "人物走向窗边", "frames": ["81", 4], "nested": {"seed": "42"}})
        self.assertEqual(source["prompt"], "{{scene.prompt}}")
        self.assertNotEqual(workflow_hash(source), workflow_hash(result))
        with self.assertRaisesRegex(WorkflowError, "missing workflow input"):
            substitute_workflow({"x": "{{missing}}"}, {})

    def test_job_store_round_trip_is_durable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "jobs.json"
            store = JobStore(path)
            created = store.create({"workflow_id": "wan21_i2v", "status_hint": "local"})
            self.assertEqual(created["status"], "QUEUED")
            updated = store.update(created["job_id"], status="RUNNING", prompt_id="abc")
            self.assertEqual(updated["status"], "RUNNING")
            self.assertEqual(store.get(created["job_id"])["prompt_id"], "abc")
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))[created["job_id"]]["status"], "RUNNING")


if __name__ == "__main__":
    unittest.main()
