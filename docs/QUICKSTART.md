# thoxos-images — Quickstart

```sh
git clone https://github.com/Thox-ai/thoxos-images.git
cd thoxos-images
python3 device/images/validate.py    # expect 27/27 checks pass
```

That validates every device-class definition in the package. There is
no image to download or flash in v0.1.0 — the package is definitions,
and each class's build state is tabled in
[USER_GUIDE.md](USER_GUIDE.md). Desktop build definitions are in
`desktop/` (see `desktop/README.md`).
