#!/usr/bin/env python3
"""Unit tests for desktop/check_definitions.py (stdlib unittest).

The real tree must pass (known drift allowed); deliberately broken copies
must fail, proving each guard fires; and fixing a known drift without
removing its allowlist entry must fail, proving the list cannot rot.
"""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import check_definitions as cd  # noqa: E402


def failures_in(root: Path) -> list[dict]:
    results, _ = cd.classify(cd.run(root))
    return [r for r in results if r["status"] == "FAIL"]


class DesktopDefinitionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "desktop"
        shutil.copytree(HERE, self.root, ignore=shutil.ignore_patterns("__pycache__"))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def edit(self, rel, old, new):
        p = self.root / rel
        text = p.read_text(encoding="utf-8")
        self.assertIn(old, text, f"fixture text not found in {rel}")
        p.write_text(text.replace(old, new), encoding="utf-8")

    def test_real_tree_passes(self):
        self.assertEqual(failures_in(HERE), [])

    def test_wrong_root_label_fails(self):
        self.edit("repart.d/dual-debian/20-root-x86.conf", "Label=THOXOS-X86", "Label=THOXOS-ROOT")
        ids = {r["id"] for r in failures_in(self.root)}
        self.assertIn("D3", ids)

    def test_missing_greeter_fails(self):
        self.edit("mkosi-cosmic.conf", "    cosmic-greeter\n", "")
        ids = {(r["id"], r["variant"]) for r in failures_in(self.root)}
        self.assertIn(("D8", "x86_64-desktop-debian-cosmic"), ids)

    def test_safe_cmdline_without_nomodeset_fails(self):
        reg = json.loads((self.root / "variants.json").read_text())
        v = reg["variants"]["x86_64-desktop-debian-cosmic"]
        v["cmdline_safe"] = v["cmdline_safe"].replace(" nomodeset", "")
        (self.root / "variants.json").write_text(json.dumps(reg))
        ids = {r["id"] for r in failures_in(self.root)}
        self.assertIn("D4", ids)

    def test_layout_size_drift_fails(self):
        self.edit("repart.d/dual-debian/40-root-arm.conf", "SizeMinBytes=8G\nSizeMaxBytes=8G",
                  "SizeMinBytes=9G\nSizeMaxBytes=9G")
        ids = {r["id"] for r in failures_in(self.root)}
        self.assertIn("D11", ids)

    def test_fixed_known_drift_without_allowlist_update_fails(self):
        reg = json.loads((self.root / "variants.json").read_text())
        pe = reg["variants"]["x86_64-desktop-debian"]["packages_extra"]
        pe[pe.index("nvidia-open-570")] = "nvidia-open-580"
        (self.root / "variants.json").write_text(json.dumps(reg))
        msgs = [r["msg"] for r in failures_in(self.root)]
        self.assertTrue(any("stale known-drift" in m for m in msgs), msgs)


if __name__ == "__main__":
    unittest.main(verbosity=2)
