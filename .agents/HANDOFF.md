# Handoff — thoxos-images

Status: PUBLIC v0.1.0 released 2026-10-31 (programme decision D10).
Repository: https://github.com/Thox-ai/thoxos-images — release:
https://github.com/Thox-ai/thoxos-images/releases/tag/v0.1.0

Done:
- Device-class definitions (E2/P4/P6/QEMU) + OTA template, validated
  27/27, byte-identical to the thoxos-core trees at release.
- Desktop (Debian 13 + COSMIC) build definitions, byte-identical to
  the desktop build tree's definition files.
- Internal desktop RC 1.0.0-rc.1+20261025 recorded with hashes and its
  four open defects (in desktop/README.md). The RC image itself is
  NOT a release asset (CAO call under D10).

Next:
- First built device image per class (needs Buildroot tree + pinned
  toolchain on a fleet build host).
- Desktop build tree publishes as its own repository in a separate
  pass.
- Bare-metal and dual-boot proof for the desktop line.

Key files: device/images/validate.py, desktop/README.md,
desktop/variants.json.

Conventions: validator stays green; state table honesty (see
docs/DEVELOPMENT.md).

Last verified: 2026-10-31, publish pass.
