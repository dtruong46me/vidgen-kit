# assets/

Local media pool for the examples in `examples/`. Not committed to git
(see `.gitignore` — `/assets` is ignored) since it's just downloaded
sample content, not project source.

```
assets/
├── fetch_assets.sh   # re-downloads everything below
├── video/
│   ├── flower.mp4            5.06s  960x540   CC0 (MDN sample media)
│   └── big_buck_bunny.mp4   10.00s  640x360   CC-BY (Blender Foundation),
│                                               10s/1MB re-encode via test-videos.co.uk
├── audio/
│   └── sample.mp3            19.2s             samplelib.com test tone
└── image/
    └── sample.jpg          1280x720             picsum.photos placeholder photo
```

Run `bash assets/fetch_assets.sh` to (re)download. It skips files that
already exist, so it's safe to re-run.

`src/vidgen/assets.py`'s `AssetManager.import_asset()` probes video/audio
duration from these files automatically via `ffprobe` — no need to pass
`duration=` by hand like the older `demo_simple_cut.py` example does.
