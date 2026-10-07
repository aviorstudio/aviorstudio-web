"""Render Avior identity candidates using a Spritesmith checkout and CairoSVG/Pillow.

Usage: python scripts/render-logos.py /path/to/spritesmith-be/spritesmith
Run with the Python environment containing Spritesmith's rendering dependencies.
"""
from io import BytesIO
from pathlib import Path
import subprocess
import sys
import cairosvg
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parents[1]
out = root / 'public/art/identity'
out.mkdir(parents=True, exist_ok=True)
sheet = Image.new('RGB', (1440, 660), '#f4efe4')
draw = ImageDraw.Draw(sheet)
font = ImageFont.truetype('DejaVuSans.ttf', 24)
small = ImageFont.truetype('DejaVuSans.ttf', 16)
for index, (key, label, style) in enumerate([
    ('badge', '01 · Game badge', 'cozy'),
    ('pond', '02 · Pond emblem', 'cozy'),
    ('seal', '03 · Studio seal', 'flat'),
]):
    svg = out / f'ibis-{key}.svg'
    subprocess.run([sys.executable, str(Path(sys.argv[1]).resolve().parent / 'py/spritesmith.py'),
                    'svg', str(root / 'art/avior_ibis.py'), '--anim', key,
                    '--style', style, '--cell', '256', '--out', str(svg)], check=True)
    png = cairosvg.svg2png(url=str(svg), output_width=400, output_height=400)
    (out / f'ibis-{key}.png').write_bytes(png)
    image = Image.open(BytesIO(png))
    x = index * 480 + 40
    sheet.paste(image, (x, 65), image)
    draw.text((x, 490), label, font=font, fill='#203c42')
    draw.text((x, 530), 'AVIOR STUDIO', font=small, fill='#203c42')
    tiny = image.resize((48, 48), Image.Resampling.LANCZOS)
    sheet.paste(tiny, (x, 570), tiny)
    draw.text((x + 68, 584), '48px mark', font=small, fill='#203c42')
sheet.save(out / 'logo-directions.png')
