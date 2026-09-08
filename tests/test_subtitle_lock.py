from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class SubtitleLockContractsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[1]
        cls.validator = cls.root / "scripts" / "validate_subtitles.py"
        cls.burn_script = cls.root / "scripts" / "burn_subtitles.ps1"
        cls.template = cls.root / "sample_assets" / "subtitles" / "SUBTITLE_LOCK_V1.ass"
        cls.preview = cls.root / "sample_assets" / "subtitles" / "SUBTITLE_LOCK_V1_preview.ass"

    def _run(self, path: Path, *extra: str) -> tuple[subprocess.CompletedProcess[str], dict]:
        env = os.environ.copy()
        # Windows inherits the active code page for piped child output.  The
        # fixture contains Chinese dialogue, so force the JSON stream to UTF-8.
        env["PYTHONIOENCODING"] = "utf-8"
        completed = subprocess.run(
            [sys.executable, str(self.validator), str(path), "--json", *extra],
            cwd=self.root, env=env, check=False, capture_output=True, text=True, encoding="utf-8",
        )
        return completed, json.loads(completed.stdout)

    def test_preview_matches_lock(self) -> None:
        completed, report = self._run(self.preview)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertTrue(report["ok"])
        self.assertEqual(report["playres"], {"width": 1080, "height": 1920})
        self.assertEqual(report["dialogue_count"], 1)

    def test_style_template_needs_allow_empty(self) -> None:
        completed, report = self._run(self.template)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("at least one active Dialogue", " ".join(report["errors"]))
        completed, report = self._run(self.template, "--allow-empty")
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertTrue(report["ok"])

    def test_rejects_line_limit_and_overrides(self) -> None:
        source = self.preview.read_text(encoding="utf-8").replace(
            "我一直在等你回来。", r"第一行\N第二行\N第三行{\c&HFF0000&}"
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "bad.ass"
            path.write_text(source, encoding="utf-8")
            completed, report = self._run(path)
        self.assertEqual(completed.returncode, 1)
        errors = " ".join(report["errors"])
        self.assertIn("two-line limit", errors)
        self.assertIn("visual/position/animation override", errors)

    def test_rejects_style_reset_override(self) -> None:
        source = self.preview.read_text(encoding="utf-8").replace(
            "我一直在等你回来。", r"{\rPrimarySemibold}我一直在等你回来。"
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "reset.ass"
            path.write_text(source, encoding="utf-8")
            completed, report = self._run(path)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("visual/position/animation override", " ".join(report["errors"]))

    def test_rejects_font_drift_and_long_line(self) -> None:
        source = self.preview.read_text(encoding="utf-8").replace("Source Han Sans CN Medium", "Microsoft YaHei")
        source = source.replace("我一直在等你回来。", "一二三四五六七八九十一二三四五六七")
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "drift.ass"
            path.write_text(source, encoding="utf-8")
            completed, report = self._run(path)
        self.assertEqual(completed.returncode, 1)
        errors = " ".join(report["errors"])
        self.assertIn("Primary.Fontname", errors)
        self.assertIn("exceeds 16 characters", errors)

    def test_rejects_event_position_and_effect_overrides(self) -> None:
        source = self.preview.read_text(encoding="utf-8").replace(
            "Dialogue: 0,0:00:00.00,0:00:05.04,Primary,,0,0,0,,我一直在等你回来。",
            "Dialogue: 0,0:00:00.00,0:00:05.04,Primary,,20,20,100,Scroll up,我一直在等你回来。",
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "event-drift.ass"
            path.write_text(source, encoding="utf-8")
            completed, report = self._run(path)
        self.assertEqual(completed.returncode, 1)
        errors = " ".join(report["errors"])
        self.assertIn("event margins at 0", errors)
        self.assertIn("animated/scrolling Effect", errors)

    def test_burn_script_requires_preflight_and_atomic_publish(self) -> None:
        source = self.burn_script.read_text(encoding="utf-8")
        self.assertIn("validate_subtitles.py", source)
        self.assertNotIn("--allow-empty", source)
        self.assertIn(".partial.mp4", source)
        self.assertIn("Move-Item -LiteralPath $temporaryOutput", source)
        self.assertIn("no video was written", source)


if __name__ == "__main__":
    unittest.main()
