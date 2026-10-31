# OTA — RAUC A/B updates with health gates and automatic rollback

ThoxOS Core devices update with **RAUC** in an A/B slot layout. This is part
of free Core: security patches are never paywalled, and a lapsed subscription
never blocks or breaks an update — entitlement is verified locally and only
gates THOX-hosted services, never the device's own update path.

## Layout

- Two rootfs slots, `rootfs.0` (bootname **A**) and `rootfs.1` (bootname
  **B**), plus a persistent data partition that updates never touch.
- The running system is always one slot; an update is always written to the
  **other** slot. The slot a user is running is never modified in place.
- Configuration template: [`rauc/system.conf.template`](rauc/system.conf.template),
  rendered per compute class at image build time.
- Every bundle is **signed**; RAUC verifies the bundle signature against the
  on-device keyring and verifies the **hash of every image** against the
  signed manifest before writing anything. A hash or signature mismatch is a
  hard reject, not a warning.

## Update flow

1. **Download.** The bundle is fetched (hosted relay, LAN peer, or local
   file/USB) into the data partition and staged.
2. **Verify.** Signature + image hashes are verified (see above).
3. **Install to the inactive slot.** RAUC writes the new rootfs to the idle
   slot and runs the post-install handler.
4. **Arm and reboot.** The bootloader environment marks the new slot as the
   next boot, with the previous slot retained as the fallback and a boot
   attempt counter set.
5. **Health gate (first boot of the new slot).** Early in boot, and again
   when the system reaches `multi-user.target`, the health gate checks:
   - `thoxd` is running and its local API answers;
   - `thoxos-portal` is running (this is the service the historical missing
     `multi-user.target.wants` symlink once silently disabled — the image CI
     assertion in `images/` exists so this class of failure is caught before
     an image ships, and the health gate catches it at runtime too);
   - `meshstack-local` is running and discovery is up;
   - networking reaches its configured targets;
   - the RAUC slot reports itself bootable.
6. **Mark good or roll back.**
   - If every check passes inside the health-gate window, the slot is marked
     **good** (`rauc status mark-good`) and becomes the standing system.
   - **If any check fails, or the device fails to boot the new slot, or the
     boot attempt counter is exhausted, the rollback is automatic:** the
     bootloader falls back to the previous slot, the failed slot is marked
     **bad**, and the device returns to the last known-good system with user
     data intact. No user action is required and no partial state is kept.

## Rules that do not bend

- A failed health check **always** rolls back automatically. There is no
  "keep the broken slot and warn" path.
- An update never writes to the running slot or the data partition.
- A bundle that fails signature or hash verification is never installed.
- Rollback is not a downgrade path for users: slots are only ever selected
  by the bootloader/health-gate machinery, not by a settings toggle.
- Staged/fleet rollouts (paid fleet console) only change *when* devices are
  offered a bundle. The on-device verify → install → health-gate → mark-good
  or rollback flow above is identical for every device, free or paid.
