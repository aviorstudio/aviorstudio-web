# The 2026 ibis mark

- `reference/original-2025.png` is the studio's first ibis, which the new mark is based on.
- `drybrush/b2-wash.png` is the dry-brush repaint, generated on a transparent background.
- `drybrush/b2-wash-thin60.png` is the same painting with the ring narrowed to 60% of its width toward the middle of its stroke (`locked/tools/thin_ring.py`).
- `locked/` is the mark the site uses: `painting.png` (the thinned painting), `config.json`, and the spritesmith.sprite@1 `sprite.json` and idle `rig.json` cut from it.

Rebuild the sprite and the site's mark (needs NumPy, SciPy and Pillow):

```sh
cd art/ibis-2026/locked
python tools/sprite_pipeline.py config.json /tmp/ibis
cd ../../..
python scripts/build-mark.py /tmp/ibis
```

The first step reproduces `sprite.json` and `rig.json` exactly. The second writes `public/mark/`, the favicons, the share image, `src/styles/mark.css` and `src/components/AviorMark.astro`.
