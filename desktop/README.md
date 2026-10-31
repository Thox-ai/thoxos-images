# Desktop image build definition — Debian 13 + COSMIC (D2 line)

This directory carries the operative build definition for the ThoxOS
Desktop Edition: the variant registry, both mkosi configurations, the
builder image, the disk layout, and the thoxd service unit. The full
build tree (postinst scripts, theme generation, TXF extra trees, gate
harness, vendor-apt keyrings) lives in the desktop build repository and
is published as its own repo in the release runbook; the files here are
byte-identical copies of the definition files in that tree (hashes in
the release manifest).

## The definition

| File | Role |
| --- | --- |
| `variants.json` | Variant registry for the whole image family. The release-relevant entries are `x86_64-desktop-debian-cosmic` (adopted direction, DECIDE-01 / DESIGN §12) and `x86_64-desktop-debian` (Plasma 6.3 fallback). The Arch and Asahi entries are the older engineering-preview lines, kept in the registry. |
| `mkosi-cosmic.conf` | COSMIC variant root: Debian 13 (trixie), COSMIC Epoch 1.8.0+synex1 from a build-time vendored Synex pool, greetd + cosmic-greeter, full dev stack, NVIDIA 580 production branch (the spec'd 570 open module does not compile against trixie's 6.12 headers; documented in the file header). |
| `mkosi.conf` | Plasma 6.3 fallback variant root; same base, dev stack and vendor handling. |
| `Dockerfile.builder-debian` | Builder image: debian:trixie pinned by digest, mkosi 27.1, systemd-repart/ukify tooling. |
| `repart.d/dual-debian/` | GPT layout (systemd-repart): THOXESP 1 GiB, THOXOS-X86 root 48 GiB btrfs, ARM boot/root slots for the dual image. |
| `thoxd.service` | The thoxd unit as shipped on the desktop line (loopback API, hardened sandbox). |

Build (on a Debian-capable build host with the full tree):

```sh
image/build-image.sh --variant x86_64-desktop-debian-cosmic
```

## Built state — internal RC, not a public release

Version `1.0.0-rc.1+20261025` of both Debian variants was built on
KnightHub and gated in the QEMU VM harness (records:
`docs/validation/vm-review-x86_64-desktop-debian-cosmic-2026-10-27.md`
and the Plasma record of 2026-10-25 in the desktop tree).

COSMIC RC artifacts (KnightHub build-out directory):

- `thoxos-x86_64-desktop-debian-cosmic-1.0.0-rc.1+20261025.img` —
  62,278,094,848 B, sha256 `c80ab770cda9b94702176b63b4a771ba53249b2cef074654d129beade6f4d997`
- `thoxos-x86_64-desktop-debian-cosmic-1.0.0-rc.1+20261025.img.zst` —
  6,565,644,979 B, sha256 `5072455cacd33a5540135eebc916b99d0be72ced03197bcefe18e0e0eac2c231`

Plasma RC artifacts: `.img` 62,278,094,848 B sha256
`5061768520393ff2b093619754edd0d2beeb1766444a3d0992112a9d21785b1b`;
`.img.zst` 6,419,053,676 B sha256
`3025c5da784539e1ca068db4d33dfe35e9da9bbe190cf6c0724090087f9d1026`.

Proven for the COSMIC RC: boots in the VM harness; COSMIC Wayland
session presents with TXF themes generated from the token source;
NVIDIA DKMS modules inside the initramfs; dev stack verified in-guest
(Firefox ESR, VS Code, Rust 1.85.1, Go 1.24.4, Node 20.19.2,
Python 3.13.5, Docker 26.1.5).

Named defects/gaps in the COSMIC RC (from its ship-readiness record —
these ship in the open, not in a footnote):

1. `cosmic-greeter.service` FAILED in the shipped (non-vmtest)
   configuration — the login UI is unproven on this image.
2. ThoxOS Shell cannot execute on Debian (overlay binary requires
   GLIBC_2.43; trixie has 2.41) — affects both Debian variants.
3. COSMIC launcher opens and takes the query; no result list renders
   (ASK THOX plugin unverified end to end).
4. Porcelain (V2) light switch unproven: the light theme pair ships;
   the layout switch did not take in-session.
5. Bare-metal boot, bare-metal GPU, and the dual-boot installer path
   are unexercised for both variants.

## The older KnightHub ISO asset

`~/workspace/thoxos-knighthub-iso/` is a separate, older Ubuntu
24.04-based install-image build system (stock kernel 6.8, autoinstall).
It is NOT the D2 desktop and is not part of this definition; it remains
useful as a dual-boot/installer reference. Do not conflate the two
lines in release copy.
