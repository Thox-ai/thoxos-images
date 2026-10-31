# thoxos-images

[![License](https://img.shields.io/badge/license-Apache--2.0-blue?style=flat-square)](LICENSE)
[![THOX.ai](https://img.shields.io/badge/THOX.ai-portfolio-05A451?style=flat-square)](https://thox.ai)

ThoxOS image build definitions: device-class definitions (E2, P4, P6, QEMU) with the RAUC A/B OTA template, and the Debian 13 + COSMIC Desktop Edition build definitions.

**Status:** v0.1.0 (2026-10-31). Definitions are not images: read the
state column before promising anyone a download.

| Class | Directory | Definition | State (2026-10-31) |
| --- | --- | --- | --- |
| E2 entry devices | `device/images/e2/` | Buildroot config fragment + expected unit list + class facts | Fragment only; no image built from this tree yet |
| P4 performance devices | `device/images/p4/` | Same shape | Fragment only |
| P6 performance+ devices | `device/images/p6/` | Same shape | Fragment only |
| QEMU virtual lab | `device/images/qemu/` | Same shape; mirrors the E2 unit set | Fragment only |
| Device OTA | `device/ota/` | RAUC A/B system.conf template + update/health-gate/rollback rules | Template only; rendered per class at image build time |
| Desktop (Debian 13 + COSMIC) | `desktop/` | mkosi configs (COSMIC + Plasma fallback), variant registry, builder Dockerfile, repart layout, thoxd unit | **Built**: internal RC `1.0.0-rc.1+20261025` exists and is VM-gated (see `desktop/README.md`); not a public release |

## Device classes

The device tree is validated, not built: `device/images/validate.py`
checks every class definition (required files, class-fact sanity, RAM
floor ordering, the portal enablement regression guard, the RAUC A/B
slots) — 27/27 checks pass, and the validator's failure modes were
exercised against deliberately broken copies during packaging.

Building a device image requires a Buildroot tree and the pinned
external toolchain the fragments name; neither is vendored here. The
fragments are merged over a pinned Buildroot defconfig at build time;
THOX package recipes (`BR2_PACKAGE_THOXD` and friends) land with the
`thoxd/` work in thoxos-core and are commented selections until then.

## Desktop

See [`desktop/README.md`](desktop/README.md). The desktop line is the
one class with built artifacts today: they were produced on a fleet
build host from the full build tree, and they are internal release
candidates, not public downloads. The full desktop build tree
publishes as its own repository in a separate pass.

## Quick start

```sh
git clone https://github.com/Thox-ai/thoxos-images.git
cd thoxos-images
python3 device/images/validate.py    # 27/27 checks
```

## Documentation

- [User Guide](docs/USER_GUIDE.md)
- [Quickstart](docs/QUICKSTART.md)
- [Development](docs/DEVELOPMENT.md)
- [Previews](docs/previews/)
- Agent handoff: [.agents/HANDOFF.md](.agents/HANDOFF.md)

## Releases

Formal releases live on the
[Releases page](https://github.com/Thox-ai/thoxos-images/releases).
v0.1.0 is the definitions release; its tarball and SHA-256 sidecar are
attached there.

## Governance

THOX.ai LLC is the steward of this repository. Changes to public
contracts (ABIs, local APIs, the free/paid line) require an RFC. The
THOX trademark policy applies: the license covers the code, not the
THOX marks. Publishing and announcement decisions for THOX programmes
are made by the THOX.ai founders.

## Licensing

Device definitions and the OTA template: Apache-2.0 (thoxos-core).
Desktop definitions in `desktop/`: from the ThoxOS desktop build tree;
TXF theme assets referenced by that tree carry their own provenance
notes. Upstream components (Debian, COSMIC, Plasma, NVIDIA drivers)
retain their own licenses. See [LICENSE](LICENSE) and
[NOTICE.md](NOTICE.md).
