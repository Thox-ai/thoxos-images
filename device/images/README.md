# Images

Buildroot image definitions per compute class (DECIDE-01 D-C4: the existing
device image repos fold into this tree by subtree import, preserving history,
after one image per class builds from here). This directory is the staging
form of that layout: plausible Buildroot config **fragments**, the expected
systemd unit lists, and machine-readable class facts. Fragments are staging
inputs, not built image configurations.

## Layout

```
images/
  e2/      entry class        (quad-core Arm, 2 GB RAM floor)
  p4/      performance class  (8-core hybrid Arm, 4 GB RAM floor)
  p6/      performance+ class (p4 floors + 6 GB RAM floor)
  qemu/    virtual lab target (QEMU virt, mirrors the e2 unit set)
  validate.py        stdlib validator for this tree + ../ota/
  test_validate.py   unittest: real tree passes, broken tree fails
```

Every class directory contains exactly three files:

| File | Purpose |
| --- | --- |
| `buildroot.config.fragment` | Buildroot config fragment for the class: target arch, toolchain, kernel/system options, and the THOX package selections (comment-documented `BR2_PACKAGE_*` options). Merged over a pinned defconfig at build time. |
| `units.txt` | The expected systemd unit list for the class. This is the **CI assertion source**: an image build fails unless the built image's unit set matches this file. |
| `class.json` | Machine-readable class facts: `name`, `ram_gb_floor`, `storage`, `notes`. Category-level only — **no board or SoC names appear anywhere in this tree**. |

The desktop image is not here: Debian 13 + COSMIC is its own repository
(DECIDE-01). OTA configuration lives in [`../ota/`](../ota/).

## The enablement-marker convention (units.txt)

A unit that must be **enabled** in the image — i.e. its
`multi-user.target.wants` symlink must be installed by the build — is written
with a trailing marker:

```
thoxos-portal.service (enabled: multi-user.target)
```

A unit listed without the marker is expected to be present in the image but
not enabled into `multi-user.target`.

**`thoxos-portal.service` must carry the marker in every class, no
exceptions.** This is the regression guard for a historical defect: a ThoxAir
image once shipped with the portal unit present but its
`multi-user.target.wants` symlink missing, so the portal silently never
started on boot. Presence of the unit is not enough; enablement is asserted
separately, in this file, and enforced by the validator and by image CI.

## Validation

```
python3 images/validate.py            # validates this repository
python3 images/test_validate.py       # unittest suite
```

`validate.py` checks, printing PASS/FAIL per check and exiting non-zero on
any failure:

1. Every class directory has all three required files.
2. Every `class.json` parses and carries `name` + `ram_gb_floor`.
3. RAM floors are monotonically sane: e2 ≤ p4 ≤ p6.
4. Every `units.txt` lists `thoxos-portal.service`.
5. Every `thoxos-portal.service` line carries the
   ` (enabled: multi-user.target)` marker (the portal regression guard).
6. `ota/rauc/system.conf.template` defines both `[slot.rootfs.0]` and
   `[slot.rootfs.1]`.

The unittest suite runs the validator against the real tree (must pass) and
against a deliberately broken temporary copy with the portal enablement
marker removed (must fail), proving the guard fires.
