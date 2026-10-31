#!/usr/bin/env python3
"""Tests for images/validate.py.

- The real tree in this repository must validate clean (exit 0).
- A deliberately broken copy (thoxos-portal enablement marker removed from
  one class) must FAIL (non-zero exit), proving the regression guard for the
  historical missing multi-user.target.wants portal defect actually fires.

Run:  python3 -m unittest images/test_validate.py
  or: python3 images/test_validate.py
"""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

IMAGES_DIR = Path(__file__).resolve().parent
REPO_ROOT = IMAGES_DIR.parent
VALIDATOR = IMAGES_DIR / "validate.py"
ENABLEMENT_MARKER = " (enabled: multi-user.target)"


def run_validator(root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(root)],
        capture_output=True, text=True, timeout=60,
    )


class TestRealTree(unittest.TestCase):
    def test_real_tree_passes(self):
        proc = run_validator(REPO_ROOT)
        self.assertEqual(
            proc.returncode, 0,
            f"validator must PASS on the real tree\n{proc.stdout}\n{proc.stderr}")
        self.assertIn("PASS", proc.stdout)
        self.assertNotIn("FAIL:", proc.stdout)


class TestBrokenTree(unittest.TestCase):
    def test_missing_portal_enablement_marker_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            broken_root = Path(tmp) / "thoxos-core"
            shutil.copytree(REPO_ROOT / "images", broken_root / "images")
            shutil.copytree(REPO_ROOT / "ota", broken_root / "ota")

            # Break it the historical way: portal unit present, but its
            # multi-user.target enablement marker is gone (the symlink
            # defect, expressed in our units.txt convention).
            units = broken_root / "images" / "e2" / "units.txt"
            text = units.read_text(encoding="utf-8")
            self.assertIn(ENABLEMENT_MARKER, text)
            broken = text.replace(
                f"thoxos-portal.service{ENABLEMENT_MARKER}",
                "thoxos-portal.service")
            self.assertNotEqual(broken, text)
            units.write_text(broken, encoding="utf-8")

            proc = run_validator(broken_root)
            self.assertNotEqual(
                proc.returncode, 0,
                f"validator must FAIL when the portal enablement marker is "
                f"missing\n{proc.stdout}\n{proc.stderr}")
            self.assertIn("FAIL:", proc.stdout)
            self.assertIn("thoxos-portal", proc.stdout)

    def test_missing_rauc_slot_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            broken_root = Path(tmp) / "thoxos-core"
            shutil.copytree(REPO_ROOT / "images", broken_root / "images")
            shutil.copytree(REPO_ROOT / "ota", broken_root / "ota")

            template = broken_root / "ota" / "rauc" / "system.conf.template"
            text = template.read_text(encoding="utf-8")
            template.write_text(text.replace("[slot.rootfs.1]",
                                             "[slot.rootfs.DISABLED]"),
                                encoding="utf-8")

            proc = run_validator(broken_root)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("slot.rootfs.1", proc.stdout)


if __name__ == "__main__":
    unittest.main()
