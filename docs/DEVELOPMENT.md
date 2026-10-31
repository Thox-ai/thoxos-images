# thoxos-images — Development

## Architecture

Two definition families. `device/` mirrors the thoxos-core `images/`
and `ota/` trees byte-for-byte at release time (the validator is the
shared consistency gate). `desktop/` carries the operative Debian 13 +
COSMIC build definitions, byte-identical to the desktop build tree's
definition files (hashes in the programme release manifest).

## Tests

```sh
python3 device/images/validate.py    # 27/27
```

Any change to a class definition must keep the validator green,
including its regression guards (portal enablement, RAUC A/B slots).

## Conventions

- Default branch `main`. DCO sign-off (`Signed-off-by`) on every
  commit. AI-generated contributions must be disclosed in the PR
  description.
- Definitions never claim a built state they do not have; the state
  table in the user guide is updated in the same change that changes
  a class's state.

## Known limitations (v0.1.0)

- No image of any class has been built from these definitions.
- The desktop RC built from these definitions is internal, carries
  four named open defects, and is not attached to this release.

## Work log

- 2026-10-31: Public release v0.1.0 (definitions) under programme
  decision D10, assembled from the thoxos-core image trees and the
  desktop build tree with per-file hash verification.
