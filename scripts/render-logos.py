"""Render the Avior Studio identity from its Spritesmith source.

Usage: python scripts/render-logos.py /path/to/spritesmith-checkout
Run with a Python environment that has CairoSVG and Pillow (Spritesmith's own .venv works).

The mark is the `mark` animation of art/avior_round.py: a white ibis and its reflection cradled by a
brush sweep, outline smoothed, ends rounded. It is written transparent (for dark surfaces) and on a black
rounded tile (the site mark, favicon and share image).
"""
import re
import subprocess
import sys
from pathlib import Path

import cairosvg

root = Path(__file__).resolve().parents[1]
spritesmith = Path(sys.argv[1]).resolve() / 'py/spritesmith.py'
identity = root / 'public/art/identity'
identity.mkdir(parents=True, exist_ok=True)

mark = identity / 'enso-cradle.svg'
subprocess.run([sys.executable, str(spritesmith), 'svg', str(root / 'art/avior_round.py'),
                '--anim', 'mark', '--style', 'cozy', '--cell', '256', '--out', str(mark)], check=True)

# The tile: the same drawing over a black rounded square, in one SVG.
inner = re.sub(r'^<svg[^>]*>', '', mark.read_text(encoding='utf-8').strip())[:-len('</svg>')]
inner = re.sub(r'<title>.*?</title>', '', inner, count=1)
tile = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><title>Avior Studio</title>'
        '<rect width="128" height="128" rx="26" fill="#000000"/>' + inner + '</svg>')
(root / 'public/logo-mark.svg').write_text(tile, encoding='utf-8')
(identity / 'enso-cradle-tile.svg').write_text(tile, encoding='utf-8')

# The share image is a plain black square, like the studio's first mark.
square = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128"><title>Avior Studio</title>'
          '<rect width="128" height="128" fill="#000000"/>' + inner + '</svg>')

for destination, source, size in [('public/logo-mark.png', tile, 256), ('public/favicon.png', tile, 64),
                                  ('public/logo.png', square, 1024), ('src/assets/aviorstudio-logo.png', square, 1024),
                                  ('public/art/identity/enso-cradle.png', mark.read_text(encoding='utf-8'), 512)]:
    cairosvg.svg2png(bytestring=source.encode(), write_to=str(root / destination), output_width=size, output_height=size)
    print('wrote', destination)
