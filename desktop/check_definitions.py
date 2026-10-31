#!/usr/bin/env python3
"""Consistency checks for the Desktop Edition (Debian 13) build definitions.

Stdlib only. Run from the repository root or anywhere:

    python3 desktop/check_definitions.py            # human output, exit 1 on failure
    python3 desktop/check_definitions.py --json     # machine-readable result

What it checks (cross-file consistency only; it builds and boots nothing):

  D1  variants.json parses and carries schema_version 1 + variants.
  D2  every desktop-debian variant names a repart layout directory that exists.
  D3  cmdline / cmdline_safe root=PARTLABEL=<label> resolves to a root
      partition Label in that layout.
  D4  cmdline_safe carries nomodeset (the safe-graphics recovery entry).
  D5  the layout has exactly one ESP, labelled THOXESP, formatted vfat.
  D6  every nvidia-open-* package the registry names is in the variant's
      mkosi Packages list (registry/config drift guard).
  D7  mkosi Distribution/Release/Architecture match the registry entry.
  D8  the display-manager stack the variant needs is in its Packages list
      (COSMIC: greetd + cosmic-greeter; Plasma: sddm).
  D9  the registry's "$schema" reference resolves to a file in this tree.
  D10 thoxd.service orders after thox-firstboot and installs into
      multi-user.target.
  D11 the fixed-size layout total matches the RC raw image size recorded in
      desktop/README.md within GPT overhead (<= 2 MiB). Also prints the
      minimum target disk size testers need for a raw write.

Known drift: a failure listed in KNOWN_DRIFT below is reported as KNOWN
(not a pass) and does not fail the run, so the gate stays usable while the
drift is owned elsewhere. If a KNOWN item stops failing, the run FAILS with
"stale known-drift entry" so the list cannot rot silently.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# variant id -> mkosi config file (relative to desktop/)
MKOSI_FOR = {
    "x86_64-desktop-debian": "mkosi.conf",
    "x86_64-desktop-debian-cosmic": "mkosi-cosmic.conf",
}
DM_PACKAGES = {
    "x86_64-desktop-debian": ["sddm"],
    "x86_64-desktop-debian-cosmic": ["greetd", "cosmic-greeter"],
}
ARCH_MAP = {"x86_64": "x86-64", "aarch64": "arm64"}
ROOT_TYPE_FOR = {"x86_64": "root-x86-64", "aarch64": "root-arm64"}
GPT_SLACK = 2 * 1024 * 1024

# (check id, variant or "*") -> reason. Owned by the desktop build tree,
# where these files are authored; this repo carries byte-identical copies.
KNOWN_DRIFT = {
    ("D6", "x86_64-desktop-debian"): (
        "registry packages_extra names nvidia-open-570 while mkosi.conf installs "
        "nvidia-open-580 (570 open module does not build on trixie 6.12, per the "
        "mkosi.conf header). Fix belongs in the desktop build tree's variants.json."
    ),
    ("D9", "*"): (
        "variants.json references ./variants.schema.json, which is not shipped in "
        "this package; the upstream schema in the Vibe Rust tree only admits the "
        "arch/fedora variants, so the Debian entries have no schema yet."
    ),
}


def parse_ini_multi(path: Path) -> dict[str, dict[str, list[str]]]:
    """Parse mkosi / repart style INI: repeated keys and indented continuation
    lines accumulate into lists; full-line comments are ignored anywhere."""
    out: dict[str, dict[str, list[str]]] = {}
    section = None
    key = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped[1:-1]
            out.setdefault(section, {})
            key = None
            continue
        if section is None:
            continue
        if raw[:1].isspace() and key is not None:
            out[section][key].append(stripped)
            continue
        if "=" in stripped:
            k, v = stripped.split("=", 1)
            key = k.strip()
            out[section].setdefault(key, [])
            if v.strip():
                out[section][key].append(v.strip())
    return out


def root_label(cmdline: str) -> str | None:
    m = re.search(r"root=PARTLABEL=(\S+)", cmdline)
    return m.group(1) if m else None


def run(root: Path = HERE) -> list[dict]:
    results: list[dict] = []

    def rec(cid: str, variant: str, ok: bool, msg: str) -> None:
        results.append({"id": cid, "variant": variant, "ok": ok, "msg": msg})

    vpath = root / "variants.json"
    try:
        reg = json.loads(vpath.read_text(encoding="utf-8"))
        ok = reg.get("schema_version") == 1 and isinstance(reg.get("variants"), dict)
        rec("D1", "*", ok, "variants.json parses, schema_version 1")
    except Exception as exc:  # noqa: BLE001
        rec("D1", "*", False, f"variants.json does not parse: {exc}")
        return results

    schema_ref = reg.get("$schema")
    if schema_ref:
        present = (root / schema_ref).is_file()
        rec("D9", "*", present, f"$schema {schema_ref} present in tree: {present}")

    service = root / "thoxd.service"
    if service.is_file():
        unit = parse_ini_multi(service)
        after = " ".join(unit.get("Unit", {}).get("After", []))
        wanted = " ".join(unit.get("Install", {}).get("WantedBy", []))
        rec("D10", "*", "thox-firstboot.service" in after and "multi-user.target" in wanted,
            "thoxd.service After=thox-firstboot, WantedBy=multi-user.target")
    else:
        rec("D10", "*", False, "thoxd.service missing")

    readme = (root / "README.md").read_text(encoding="utf-8") if (root / "README.md").is_file() else ""

    for vid, v in reg["variants"].items():
        if v.get("profile") != "desktop-debian":
            continue
        layout_dir = root / "repart.d" / v.get("layout", "")
        if not layout_dir.is_dir():
            rec("D2", vid, False, f"layout dir {layout_dir.name} missing")
            continue
        rec("D2", vid, True, f"layout {layout_dir.name} present")
        parts = [(p.name, parse_ini_multi(p).get("Partition", {})) for p in sorted(layout_dir.glob("*.conf"))]

        def one(p: dict, k: str) -> str:
            return (p.get(k) or [""])[0]

        roots = {one(p, "Label") for _, p in parts if one(p, "Type") == ROOT_TYPE_FOR.get(v.get("arch"), "")}
        for field in ("cmdline", "cmdline_safe"):
            lab = root_label(v.get(field, ""))
            rec("D3", vid, lab in roots, f"{field} root=PARTLABEL={lab} in layout roots {sorted(roots)}")
        rec("D4", vid, "nomodeset" in v.get("cmdline_safe", ""), "cmdline_safe carries nomodeset")
        esps = [p for _, p in parts if one(p, "Type") == "esp"]
        rec("D5", vid, len(esps) == 1 and one(esps[0], "Label") == "THOXESP" and one(esps[0], "Format") == "vfat",
            "single ESP labelled THOXESP (vfat)")

        mk_name = MKOSI_FOR.get(vid)
        if mk_name and (root / mk_name).is_file():
            mk = parse_ini_multi(root / mk_name)
            pkgs = set(mk.get("Content", {}).get("Packages", []))
            want_nv = [p for p in v.get("packages_extra", []) if p.startswith("nvidia-open-")]
            missing = [p for p in want_nv if p not in pkgs]
            have_nv = sorted(p for p in pkgs if p.startswith("nvidia-open-"))
            rec("D6", vid, not missing, f"registry {want_nv} vs {mk_name} {have_nv}")
            dist = mk.get("Distribution", {})
            match = (one(dist, "Distribution") == v.get("distribution")
                     and one(dist, "Release") == v.get("release")
                     and one(dist, "Architecture") == ARCH_MAP.get(v.get("arch")))
            rec("D7", vid, match, f"{mk_name} distribution/release/arch match registry")
            dm_missing = [p for p in DM_PACKAGES.get(vid, []) if p not in pkgs]
            rec("D8", vid, not dm_missing, f"display-manager packages present (missing: {dm_missing})")
        else:
            rec("D6", vid, False, f"no mkosi config mapped for {vid}")

        fixed = 0
        all_fixed = True
        for _, p in parts:
            lo, hi = one(p, "SizeMinBytes"), one(p, "SizeMaxBytes")
            if not lo or lo != hi:
                all_fixed = False
                break
            fixed += parse_size(lo)
        sizes = re.findall(rf"{re.escape(v['image_file'].split('{')[0])}[^\n]*?\.img`?\s*(?:—|-)\s*\n?\s*([\d,]+) B", readme)
        if vid == "x86_64-desktop-debian":
            sizes = re.findall(r"Plasma RC artifacts: `\.img` ([\d,]+) B", readme) or sizes
        if all_fixed and sizes:
            rc = int(sizes[0].replace(",", ""))
            rec("D11", vid, 0 <= rc - fixed <= GPT_SLACK,
                f"layout {fixed} B ({fixed / 2**30:.1f} GiB) vs RC .img {rc} B; "
                f"raw write needs a target disk >= {rc} B ({rc / 1e9:.2f} GB)")
        else:
            rec("D11", vid, all_fixed, f"layout fixed={all_fixed}, RC size recorded={bool(sizes)}")

    return results


def parse_size(s: str) -> int:
    m = re.fullmatch(r"(\d+)([KMGT]?)", s.strip())
    if not m:
        raise ValueError(f"bad size {s!r}")
    return int(m.group(1)) * {"": 1, "K": 2**10, "M": 2**20, "G": 2**30, "T": 2**40}[m.group(2)]


def classify(results: list[dict]) -> tuple[list[dict], int]:
    failures = 0
    seen_known = set()
    for r in results:
        key = (r["id"], r["variant"])
        if not r["ok"] and key in KNOWN_DRIFT:
            r["status"] = "KNOWN"
            r["known_reason"] = KNOWN_DRIFT[key]
            seen_known.add(key)
        elif r["ok"]:
            r["status"] = "PASS"
        else:
            r["status"] = "FAIL"
            failures += 1
    for key in KNOWN_DRIFT:
        if key not in seen_known:
            results.append({"id": key[0], "variant": key[1], "ok": False, "status": "FAIL",
                            "msg": "stale known-drift entry: check now passes or no longer runs; remove it"})
            failures += 1
    return results, failures


def main(argv: list[str]) -> int:
    results, failures = classify(run())
    if "--json" in argv:
        print(json.dumps({"failures": failures, "results": results}, indent=2))
    else:
        for r in results:
            print(f"{r['status']}: {r['id']} [{r['variant']}] {r['msg']}")
            if r["status"] == "KNOWN":
                print(f"       known drift: {r['known_reason']}")
        n = len(results)
        known = sum(r["status"] == "KNOWN" for r in results)
        print(f"\n{n - failures - known}/{n} pass, {known} known drift, {failures} fail")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
