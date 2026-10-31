#!/usr/bin/env python3
"""ThoxOS Core image-tree validator (staging).

Validates the images/ class definitions and the ota/ RAUC template in this
repository. Stdlib only.

Usage:
    python3 images/validate.py [ROOT]

ROOT defaults to the repository root (the parent directory of the images/
directory this script lives in). Tests pass an explicit ROOT to validate a
copied tree.

Checks (one PASS/FAIL line each):
  1. Every class directory (e2, p4, p6, qemu) contains
     buildroot.config.fragment, units.txt and class.json.
  2. Every class.json parses as JSON and carries name + ram_gb_floor.
  3. RAM floors are monotonically sane across device classes:
     e2 <= p4 <= p6.
  4. Every units.txt lists thoxos-portal.service.
  5. REGRESSION GUARD (historical ThoxAir defect: the portal unit shipped
     without its multi-user.target.wants symlink and never started):
     in EVERY class, the thoxos-portal.service line in units.txt carries
     the enablement marker " (enabled: multi-user.target)".
  6. The RAUC template ota/rauc/system.conf.template defines both
     [slot.rootfs.0] and [slot.rootfs.1].

Exit code is 0 only if every check passes.
"""

import json
import sys
from pathlib import Path

CLASSES = ["e2", "p4", "p6", "qemu"]
MONOTONIC_CLASSES = ["e2", "p4", "p6"]
REQUIRED_FILES = ["buildroot.config.fragment", "units.txt", "class.json"]
PORTAL_UNIT = "thoxos-portal.service"
ENABLEMENT_MARKER = " (enabled: multi-user.target)"

results = []  # (ok: bool, label: str)


def check(ok, label):
    results.append((bool(ok), label))
    print(f"{'PASS' if ok else 'FAIL'}: {label}")


def unit_lines(units_path):
    """Non-comment, non-blank lines of a units.txt file."""
    lines = []
    for raw in units_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            lines.append(line)
    return lines


def validate(root: Path) -> int:
    images = root / "images"
    ram_floors = {}

    for cls in CLASSES:
        cdir = images / cls
        for fname in REQUIRED_FILES:
            check((cdir / fname).is_file(),
                  f"{cls}: {fname} present")

        class_json = cdir / "class.json"
        if class_json.is_file():
            try:
                data = json.loads(class_json.read_text(encoding="utf-8"))
                floor = data.get("ram_gb_floor")
                ok = isinstance(floor, (int, float)) and "name" in data
                check(ok, f"{cls}: class.json parses with name + ram_gb_floor")
                if isinstance(floor, (int, float)):
                    ram_floors[cls] = floor
            except (json.JSONDecodeError, OSError) as exc:
                check(False, f"{cls}: class.json parses ({exc})")

        units_path = cdir / "units.txt"
        if units_path.is_file():
            lines = unit_lines(units_path)
            portal_lines = [ln for ln in lines
                            if ln.startswith(PORTAL_UNIT)]
            check(len(portal_lines) > 0,
                  f"{cls}: units.txt lists {PORTAL_UNIT}")
            check(any(ln.endswith(ENABLEMENT_MARKER) for ln in portal_lines),
                  f"{cls}: {PORTAL_UNIT} carries enablement marker"
                  f"'{ENABLEMENT_MARKER.strip()}' (portal regression guard)")

    if all(c in ram_floors for c in MONOTONIC_CLASSES):
        floors = [ram_floors[c] for c in MONOTONIC_CLASSES]
        check(floors == sorted(floors),
              f"RAM floors monotonic e2 <= p4 <= p6 (got {floors})")
    else:
        check(False, "RAM floors monotonic e2 <= p4 <= p6 "
                     "(missing class.json data)")

    rauc_template = root / "ota" / "rauc" / "system.conf.template"
    if rauc_template.is_file():
        text = rauc_template.read_text(encoding="utf-8")
        check("[slot.rootfs.0]" in text,
              "rauc template defines [slot.rootfs.0]")
        check("[slot.rootfs.1]" in text,
              "rauc template defines [slot.rootfs.1]")
    else:
        check(False, "rauc template ota/rauc/system.conf.template present")

    failed = [label for ok, label in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    if failed:
        print("FAILED checks:")
        for label in failed:
            print(f"  - {label}")
    return 1 if failed else 0


def main(argv):
    if len(argv) > 1:
        root = Path(argv[1]).resolve()
    else:
        root = Path(__file__).resolve().parent.parent
    return validate(root)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
