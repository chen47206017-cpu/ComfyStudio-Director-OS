from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PROJECT_ROOT / "minimax_h3.download-state.json"
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "check_minimax_h3_download.ps1"


class MiniMaxH3DownloadGuardTest(unittest.TestCase):
    def test_manifest_is_deferred_only_and_contains_six_user_coordinates(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(manifest["observed_at"], "2026-09-03")
        self.assertEqual(manifest["timestamp_policy"]["task_baseline_date"], "2026-09-03")
        self.assertIn("untrusted", manifest["timestamp_policy"]["filesystem_timestamp_anomaly"])
        self.assertEqual(manifest["state"], "PENDING_USER_DOWNLOAD")
        self.assertEqual(manifest["inspection_policy"]["filesystem_access"], "MANIFEST_ONLY")
        self.assertEqual(manifest["inspection_policy"]["network_access"], "NONE")
        self.assertEqual(manifest["source_verification"]["status"], "UNVERIFIED_USER_SUPPLIED")
        artifacts = manifest["artifacts"]
        self.assertEqual(len(artifacts), 6)
        self.assertEqual({item["status"] for item in artifacts}, {"PENDING"})
        for item in artifacts:
            self.assertEqual(item["verification"], "DEFERRED")
            self.assertIsNone(item["size_bytes"])
            self.assertIsNone(item["sha256"])
            self.assertTrue(item["repository"])
            self.assertTrue(item["source_path"])
            self.assertTrue(item["target_relative_path"])

    def test_script_has_no_model_access_or_network_primitives(self) -> None:
        source = SCRIPT_PATH.read_text(encoding="utf-8")
        forbidden = (
            "G:\\ComfyUI",
            "Get-ChildItem",
            "Get-Item",
            "Get-FileHash",
            "Invoke-WebRequest",
            "Invoke-RestMethod",
            "Start-BitsTransfer",
            "curl.exe",
            "[IO.File]::ReadAllBytes",
        )
        for token in forbidden:
            self.assertNotIn(token.lower(), source.lower())
        self.assertEqual(source.lower().count("get-content"), 1)

    @unittest.skipUnless(shutil.which("powershell"), "Windows PowerShell is required")
    def test_script_outputs_deferred_json_without_touching_model_root(self) -> None:
        completed = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(SCRIPT_PATH),
            ],
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["inspection"], "DEFERRED")
        self.assertEqual(payload["filesystem_access"], "MANIFEST_ONLY")
        self.assertEqual(payload["artifact_count"], 6)
        self.assertEqual(payload["pending_count"], 6)
        self.assertNotIn("hf_", completed.stdout.lower())


if __name__ == "__main__":
    unittest.main()
