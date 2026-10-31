# thoxos-images — User Guide

The build definitions for every ThoxOS image class, in one package.
**Definitions are not images.** v0.1.0 contains no downloadable OS
image; it contains the definitions from which images are built, with
each class's state stated plainly.

Your AI. Your Data. Your Rules.™

## Classes

| Class | Directory | State (2026-10-31) |
| --- | --- | --- |
| E2 entry devices | `device/images/e2/` | Buildroot config fragment + expected unit list + class facts. Fragment only; no image built from this tree yet. |
| P4 performance devices | `device/images/p4/` | Same shape. Fragment only. |
| P6 performance+ devices | `device/images/p6/` | Same shape. Fragment only. |
| QEMU virtual lab | `device/images/qemu/` | Same shape; mirrors the E2 unit set. Fragment only. |
| Device OTA | `device/ota/` | RAUC A/B `system.conf` template + update/health-gate/rollback rules. Template only; rendered per class at image build time. |
| Desktop (Debian 13 + COSMIC) | `desktop/` | mkosi configs (COSMIC + Plasma fallback), variant registry, builder Dockerfile, repart layout, thoxd unit. An internal RC (`1.0.0-rc.1+20261025`) was built from these definitions and VM-gated; it is not a public release. |

## Validating the device definitions

```sh
python3 device/images/validate.py    # 27/27 checks
```

The validator checks required files, class-fact sanity, RAM floor
ordering, the portal-enablement regression guard, and the RAUC A/B
slots. Its failure modes were exercised against deliberately broken
copies during packaging and fire correctly.

## Building

Building a device image requires a Buildroot tree and the pinned
external toolchain the fragments name; neither is vendored here. The
fragments merge over a pinned Buildroot defconfig at build time; THOX
package recipes land with the `thoxd` work in thoxos-core.

The desktop definitions are operative build definitions; the full
desktop build tree (postinst scripts, theme generation, gate harness)
publishes as its own repository in a separate pass. See
`desktop/README.md` for the definition files, the RC artifact hashes,
and the RC's four named open defects: the cosmic-greeter
shipped-configuration failure, the ThoxOS Shell glibc floor, the
launcher result list, and the unproven porcelain light switch.
Bare-metal and dual-boot installs of the RC have not been exercised.

## Install guides

End-user install routes (with their current evidence state) live in
the thoxos-core repository under `docs/install/`.

License: Apache-2.0. See [LICENSE](../LICENSE) and
[NOTICE.md](../NOTICE.md).
