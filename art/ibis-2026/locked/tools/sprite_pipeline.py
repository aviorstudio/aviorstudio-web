"""Cut a white-on-charcoal logo painting into parts, write a spritesmith.sprite@1 document with an idle rig,
and render its frames for review.

Usage: python -I sprite_pipeline.py CONFIG.json OUT_DIR

The painting is the original: parts are cut from it (alpha from brightness over the sampled background), so the
rest pose matches it exactly. Each part is saved twice: a document asset at canvas scale (<= 256 px a side, as
spritesmith.sprite@1 requires) and a 4x image of the same part for crisp display.
"""
import base64
import io
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

cfg = json.loads(Path(sys.argv[1]).read_text())
out = Path(sys.argv[2])
(out / 'parts').mkdir(parents=True, exist_ok=True)
(out / 'parts@4x').mkdir(parents=True, exist_ok=True)
(out / 'frames').mkdir(parents=True, exist_ok=True)

SRC = 1024          # painting size
CANVAS = 256        # document canvas
K = SRC // CANVAS   # 4x

raw = Image.open(cfg['original'])
TRANSPARENT = raw.mode in ('RGBA', 'LA') and np.asarray(raw.convert('RGBA'))[..., 3].min() == 0
if TRANSPARENT:
    # Real transparency from the image model: fit the art into the square canvas and use its own alpha.
    rgba_src = raw.convert('RGBA')
    side = max(rgba_src.size)
    sq = Image.new('RGBA', (side, side), (0, 0, 0, 0))
    sq.paste(rgba_src, ((side - rgba_src.width) // 2, (side - rgba_src.height) // 2))
    sq = sq.resize((SRC, SRC), Image.LANCZOS)
    arr = np.asarray(sq).astype(np.float32)
    px = arr[..., :3]
    # The model leaves a faint haze (alpha under ~7%) across empty areas; zero it and rescale the rest.
    floor = cfg.get('alpha_floor', 20) / 255
    alpha = np.clip((arr[..., 3] / 255 - floor) / (1 - floor), 0, 1)
    colour = px
    bg = np.array([0x25, 0x24, 0x24], np.float32)   # display background only; never baked into a part
else:
    img = raw.convert('RGB').resize((SRC, SRC), Image.LANCZOS)
    px = np.asarray(img).astype(np.float32)
lum = px @ np.array([0.2126, 0.7152, 0.0722], np.float32)

if not TRANSPARENT:
    # Background: the median of a border band.
  band = np.concatenate([px[:24].reshape(-1, 3), px[-24:].reshape(-1, 3), px[:, :24].reshape(-1, 3), px[:, -24:].reshape(-1, 3)])
  bg = np.median(band, axis=0)
  bg_l = float(bg @ np.array([0.2126, 0.7152, 0.0722]))
  top = float(np.percentile(lum, 99.7))
  alpha = np.clip((lum - bg_l - cfg.get('floor', 6)) / max(1.0, top - bg_l - cfg.get('floor', 6)), 0, 1)
  # Un-mix the background so a part keeps its own colour at partial alpha.
  safe = np.maximum(alpha, 1e-3)[..., None]
  colour = np.clip((px - bg * (1 - alpha[..., None])) / safe, 0, 255)


# ---- Find the parts ----------------------------------------------------------------------------------------------
# Brush strokes: connected paint whose box is large or that sits out on the ring. Everything else is the bird
# (above the waterline) or its reflection (below). The head and neck are cut from the body along a line through the
# base of the neck; the reflection's head is cut along the same line mirrored (and squashed) across the waterline.
yy, xx = np.mgrid[0:SRC, 0:SRC]
solid = ndimage.binary_dilation(alpha > 0.12, iterations=3)
lab, n = ndimage.label(solid)
cx0, cy0 = cfg.get('circle_px', (512, 512))
sweep_ids = []
for i, sl in enumerate(ndimage.find_objects(lab), start=1):
    h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
    comp = lab[sl] == i
    pts = np.argwhere(comp) + (sl[0].start, sl[1].start)
    mean_r = float(np.hypot(pts[:, 1] - cx0, pts[:, 0] - cy0).mean())
    if mean_r > cfg.get('ring_r', 290):
        sweep_ids.append(i)
is_sweep = np.isin(lab, sweep_ids)
wl = cfg['waterline']
p0, p1 = np.array(cfg.get('neck_cut', [[530, 335], [578, 385]]), float)
d = p1 - p0
normal = np.array([d[1], -d[0]])          # points to the head side


def side(px_, py_, a0, a1):
    dd = a1 - a0
    return (px_ - a0[0]) * dd[1] - (py_ - a0[1]) * dd[0]


head_top = cfg.get('head_top', 240)
labelled = solid & (lab > 0)
nonsweep_rows = np.nonzero((labelled & ~is_sweep).any(axis=1))[0]
refl_bottom = nonsweep_rows.max()
f = (refl_bottom - wl) / (wl - head_top)          # how much the reflection is squashed
m0 = np.array([p0[0], wl + f * (wl - p0[1])]); m1 = np.array([p1[0], wl + f * (wl - p1[1])])
head_side = side(xx, yy, p0, p1) > 0
refl_head_side = side(xx, yy, m0, m1) < 0
seed = np.zeros((SRC, SRC), np.int8)
lab_ok = labelled
seed[lab_ok & is_sweep] = 1
seed[lab_ok & ~is_sweep & (yy < wl)] = 2                                              # body
seed[lab_ok & ~is_sweep & (yy < wl) & head_side & ((xx > p0[0] - 2) | (yy < p0[1] - 8))] = 3   # head: past the neck cut, or above the back of the neck
seed[lab_ok & ~is_sweep & (yy >= wl)] = 4                                             # reflection
seed[lab_ok & ~is_sweep & (yy >= wl) & refl_head_side & ((xx > m0[0] - 2) | (yy > m0[1] + 8 * f))] = 5   # reflected head, mirrored
# Paint right of the neck (a reflected beak tip) joins the reflected head only when it connects to the head side more
# than to the body side; wide reflections reach that far right too, and those streaks stay with the body.
right = lab_ok & ~is_sweep & (yy >= wl) & (xx > p1[0] + 12) & (seed == 4)
rl, rn = ndimage.label(right)
for i in range(1, rn + 1):
    comp = rl == i
    ring = ndimage.binary_dilation(comp, iterations=2) & ~comp & lab_ok & (yy >= wl)
    if (ring & (seed == 5)).sum() > (ring & (seed == 4) & ~right).sum():
        seed[comp] = 5
# Water lines: long thin horizontal strokes near or below the waterline become their own part.
line_len = cfg.get('line_len', 200)
if line_len:
    strokes = ndimage.binary_opening(alpha > 0.35, structure=np.ones((1, line_len), bool))
    strokes = ndimage.binary_dilation(strokes, structure=np.ones((5, 9), bool)) & ~is_sweep & (yy > wl - 12)
    if cfg.get('line_band'):
        strokes &= np.abs(yy - wl) < cfg['line_band']      # only the surface strokes at the waterline
    seed[lab_ok & strokes] = 6
# Faint paint outside every component (glow, dry-brush dust) goes to the nearest part.
_, (iy, ix) = ndimage.distance_transform_edt(seed == 0, return_indices=True)
owner = seed[iy, ix]
CONNECTED = cfg.get('connected', False)
if CONNECTED:
    # The bird stays one piece and so does its reflection: no neck cut.
    owner[owner == 3] = 2
    owner[owner == 5] = 4
def smooth(v):
    v = np.clip(v, 0, 1)
    return v * v * (3 - 2 * v)


MIRROR = cfg.get('mirror_reflection')
refl_alpha = refl_rgb = None
if MIRROR:
    # The reflection is the standing bird itself (legs already faded), flipped across the waterline, squashed and
    # dimmed; the painted reflection is dropped. Sampled row by row so it lines up with the bird pixel for pixel.
    lf_ = cfg.get('leg_fade') or {}
    body_a = alpha * (owner == 2)
    if lf_:
        body_a = body_a * smooth((wl - lf_.get('gap', 6) - yy) / lf_.get('above', 50))
    sq = MIRROR.get('squash', 0.75)
    src_y = wl - (yy - wl) / sq
    below = yy > wl
    ra = ndimage.map_coordinates(body_a, [src_y, xx], order=1, cval=0) * below
    prem = [ndimage.map_coordinates(colour[..., c] * body_a, [src_y, xx], order=1, cval=0) * below for c in range(3)]
    refl_rgb = np.dstack([pc / np.maximum(ra, 1e-4) for pc in prem]).clip(0, 255)
    refl_alpha = ra * MIRROR.get('opacity', 0.45)
names = {1: 'sweep', 2: 'body', 3: 'head', 4: 'refl_body', 5: 'refl_head', 6: 'ripples'}
z = {'refl_head': 0, 'refl_body': 1, 'ripples': 2, 'head': 3, 'body': 4, 'sweep': 5}
# The head reaches a little under the body across the cut, so turning it never opens a gap at the neck.
dist_cut = side(xx, yy, p0, p1) / np.linalg.norm(d)
along = ((xx - p0[0]) * d[0] + (yy - p0[1]) * d[1]) / np.linalg.norm(d)
near_neck = (along > -10) & (along < np.linalg.norm(d) + 10)
head_overlap = (owner == 2) & (dist_cut > -cfg.get('overlap_px', 14)) & near_neck
mdist = side(xx, yy, m0, m1) / np.linalg.norm(m1 - m0)
ralong = ((xx - m0[0]) * (m1 - m0)[0] + (yy - m0[1]) * (m1 - m0)[1]) / np.linalg.norm(m1 - m0)
refl_overlap = (owner == 4) & (mdist < (1 if TRANSPARENT else cfg.get('overlap_px', 14) * f)) & (ralong > -10) & (ralong < np.linalg.norm(m1 - m0) + 10)
claimed = owner > 0
# Translucent reflection pieces cross-fade over a few pixels at their seam instead of overlapping, so the join
# neither brightens (double paint) nor drops out (a hairline gap).
seam_w = cfg.get('seam_px', 10)
seam_band = np.zeros_like(claimed) if CONNECTED else (np.abs(mdist) < seam_w) & (ralong > -10) & (ralong < np.linalg.norm(m1 - m0) + 10) & ((owner == 4) | (owner == 5)) if TRANSPARENT else np.zeros_like(claimed)
seam_ramp = np.clip(0.5 - mdist / (2 * seam_w), 0, 1)        # 1 on the head side, 0 on the body side
cut_specs = []
for k, name in names.items():
    mask = owner == k
    if not mask.any():
        continue
    if name == 'head':
        mask = mask | head_overlap
    weight = None
    if name == 'refl_head':
        mask = (mask | refl_overlap) if not TRANSPARENT else (mask | seam_band)
        # The body is drawn over the head, so the head's share is solved so the two stack to exactly alpha:
        # a_body + a_head * (1 - a_body) = a, with a_body = a * (1 - r)  =>  a_head = a * r / (1 - a * (1 - r)).
        weight = np.where(seam_band, seam_ramp / np.maximum(1e-6, 1 - alpha * (1 - seam_ramp)), 1.0) if TRANSPARENT else None
    if name == 'refl_body' and TRANSPARENT and not CONNECTED:
        mask = mask | seam_band
        weight = np.where(seam_band, 1 - seam_ramp, 1.0)
    n_bands = cfg.get('refl_bands', 0)
    band_alpha = alpha
    if name == 'refl_body' and MIRROR:
        mask = refl_alpha > 0.002
        band_alpha = refl_alpha
    if name == 'refl_body' and n_bands:
        # The reflection as horizontal bands that sway out of step, so a wave runs down the water. Neighbouring bands
        # cross-fade over a few pixels; the upper band is drawn first and its share is solved so the two stack to alpha.
        rows = np.nonzero(mask.any(axis=1))[0]
        top_, bot_ = rows.min(), rows.max() + 1
        if cfg.get('leg_fade'):
            top_ = max(top_, wl + cfg['leg_fade'].get('gap', 6))   # nothing to carry inside the faded gap
        edges = np.linspace(top_, bot_, n_bands + 1)
        bw = cfg.get('band_seam_px', 6)
        for j in range(n_bands):
            wgt = np.zeros((SRC, SRC), np.float32)
            inside = (yy >= edges[j]) & (yy < edges[j + 1])
            wgt[inside] = 1
            if j > 0:                       # seam above: this band is drawn over the one above, plain ramp
                b_ = edges[j]; r_ = np.clip(0.5 - (yy - b_) / (2 * bw), 0, 1); band = np.abs(yy - b_) < bw
                wgt = np.where(band, 1 - r_, wgt)
            if j < n_bands - 1:             # seam below: the band below is drawn over this one, solved share
                b_ = edges[j + 1]; r_ = np.clip(0.5 - (yy - b_) / (2 * bw), 0, 1); band = np.abs(yy - b_) < bw
                wgt = np.where(band, r_ / np.maximum(1e-6, 1 - band_alpha * (1 - r_)), wgt)
            cut_specs.append({'layer': f'refl_{j}', 'mask': mask & (wgt > 0), 'z': 1 + j * 0.01, 'weight': wgt,
                              **({'alpha_src': refl_alpha, 'rgb_src': refl_rgb} if MIRROR else {})})
        continue
    rd = cfg.get('ring_draw')
    if name == 'sweep' and rd:
        # The ring as short arcs along the brush stroke, so it can be drawn on. Position along the stroke runs from
        # the end beside the gap (the thin start), clockwise on screen, to the other end. Neighbouring arcs cross-fade;
        # the earlier arc is drawn first and its share is solved so the stack matches the painting at rest.
        cxr, cyr = cfg.get('circle_px', (512, 512))
        theta = np.arctan2(yy - cyr, xx - cxr)                 # screen angle, clockwise positive
        hist = np.histogram(theta[mask & (alpha > 0.05)], bins=360, range=(-np.pi, np.pi))[0]
        empty = hist == 0
        best, run, best_end = 0, 0, 0
        for i in range(720):                                    # longest circular run of empty bins = the gap
            run = run + 1 if empty[i % 360] else 0
            if run > best:
                best, best_end = run, i % 360
        start = -np.pi + (best_end + 1) * (2 * np.pi / 360)     # first bin after the gap
        span = 2 * np.pi - best * (2 * np.pi / 360)
        u = np.clip(((theta - start) % (2 * np.pi)) / span, 0, 1)
        if rd.get('reverse'):
            u = 1 - u
        NA = rd.get('segments', 36)
        NR = rd.get('rows', 1)
        sw = rd.get('seam', 0.35) / NA
        # Position across the stroke: 0 at its inner edge, 1 at its outer edge, measured per angle so the rows follow
        # the stroke's own varying width.
        rr = np.hypot(xx - cxr, yy - cyr)
        ink = mask & (alpha > 0.15)
        bins = ((theta + np.pi) / (2 * np.pi) * 360).astype(int) % 360
        r_in = np.full(360, np.nan); r_out = np.full(360, np.nan)
        for bi in range(360):
            sel = rr[ink & (bins == bi)]
            if sel.size > 4:
                r_in[bi], r_out[bi] = np.percentile(sel, 3), np.percentile(sel, 97)
        idx = np.arange(360)
        okb = ~np.isnan(r_in)
        r_in = np.interp(idx, idx[okb], r_in[okb], period=360); r_out = np.interp(idx, idx[okb], r_out[okb], period=360)
        kern = np.ones(9) / 9
        r_in = np.convolve(np.r_[r_in[-4:], r_in, r_in[:4]], kern, 'valid'); r_out = np.convolve(np.r_[r_out[-4:], r_out, r_out[:4]], kern, 'valid')
        v = np.clip((rr - r_in[bins]) / np.maximum(1, r_out[bins] - r_in[bins]), 0, 1)
        rsw = rd.get('row_seam', 0.5) / NR

        def shares(coord, n, seam, k):
            """Share of piece k of n along coord in [0,1]: piece k is drawn over piece k+1; seams cross-fade, with the
            under piece's share solved so the stack matches the painting at rest."""
            lo_, hi_ = k / n, (k + 1) / n
            w = ((coord >= lo_) & (coord < hi_) | ((k == n - 1) & (coord >= hi_)) | ((k == 0) & (coord < lo_))).astype(np.float32)
            if k > 0:
                r_ = np.clip(0.5 - (coord - lo_) / (2 * seam), 0, 1); band = np.abs(coord - lo_) < seam
                w = np.where(band, (1 - r_) / np.maximum(1e-6, 1 - alpha * r_), w)
            if k < n - 1:
                r_ = np.clip(0.5 - (coord - hi_) / (2 * seam), 0, 1); band = np.abs(coord - hi_) < seam
                w = np.where(band, r_, w)
            return w
        for j in range(NA):
            wa = shares(u, NA, sw, j)
            for b in range(NR):
                wgt = wa * (shares(v, NR, rsw, b) if NR > 1 else 1.0)
                name_ = f'sweep_{j:02d}' if NR == 1 else f'sweep_{j:02d}_{b}'
                cut_specs.append({'layer': name_, 'mask': mask & (wgt > 0), 'z': z[name] + (NA - j) * 0.01 + (NR - b) * 0.001, 'weight': wgt})
        if rd.get('fade') == 'opacity':
            # The whole ring as one image: the pieces hand over to it once drawn, and it fades evenly (pieces fading
            # together would show their seams, since their shares only add up exactly at full opacity).
            cut_specs.append({'layer': 'ringwhole', 'mask': mask, 'z': z[name], 'weight': None})
        continue
    if name == 'ripples' and cfg.get('split_ripples'):
        # One part per surface stroke (grouped by height), so neighbouring strokes can slide against each other.
        lab_r, n_r = ndimage.label(ndimage.binary_dilation(mask & (alpha > 0.1), structure=np.ones((3, 25), bool)))
        groups = {}
        for i in range(1, n_r + 1):
            cy_ = float(np.nonzero(lab_r == i)[0].mean())
            groups.setdefault(round(cy_ / 6), []).append(i)
        rows_sorted = sorted(groups)
        owner_r = np.zeros_like(lab_r)
        for j, key in enumerate(rows_sorted):
            owner_r[np.isin(lab_r, groups[key])] = j + 1
        _, (ry, rx) = ndimage.distance_transform_edt(owner_r == 0, return_indices=True)
        nearest = owner_r[ry, rx]
        for j in range(len(rows_sorted)):
            cut_specs.append({'layer': f'ripples_{j}', 'mask': mask & (nearest == j + 1), 'z': z[name] + j * 0.01, 'weight': weight})
        continue
    cut_specs.append({'layer': name, 'mask': mask, 'z': z[name], 'weight': weight})
geom = {'background': '#%02x%02x%02x' % tuple(int(round(c)) for c in bg), 'waterline': wl, 'squash': round(float(f), 3), 'refl_bottom': int(refl_bottom),
        'neck_pivot_px': (p0 + 0.15 * (p1 - p0)).tolist(), 'refl_pivot_px': (m0 + (0.5 if TRANSPARENT else 0.15) * (m1 - m0)).tolist()}

parts = []
for p in cut_specs:
    mask = p['mask']
    a = p.get('alpha_src', alpha) * mask
    if p.get('weight') is not None:
        a = a * p['weight']
    lf = cfg.get('leg_fade')
    if lf:
        # The legs fade out before the waterline and the reflected legs fade in after it, leaving a clear gap, so the
        # bird and its reflection never meet in a hard joint.
        gap = lf.get('gap', 6)
        if p['layer'] == 'body':
            a = a * smooth((wl - gap - yy) / lf.get('above', 50))
        if (p['layer'] == 'refl_body' or p['layer'].startswith('refl_')) and not MIRROR:
            a = a * smooth((yy - wl - gap) / lf.get('below', 40))
        if p['layer'].startswith('ripples'):
            # Where a leg crosses a surface stroke the paint is brighter; fill those columns from the stroke on
            # either side so the stroke runs straight through and no leg shows at the water.
            probe = alpha[int(wl - 40):int(wl - 20)].mean(axis=0)
            legs_x = np.nonzero(ndimage.binary_dilation(probe > 0.4, iterations=3))[0]
            for x in legs_x:
                lx, rx = max(0, x - 8), min(SRC - 1, x + 8)
                while lx > 0 and lx in legs_x: lx -= 1
                while rx < SRC - 1 and rx in legs_x: rx += 1
                a[:, x] = np.minimum(a[:, lx], a[:, rx]) * mask[:, x]
    rgb = p.get('rgb_src', colour)
    if p['layer'].startswith('refl') and not TRANSPARENT:
        # The reflection is translucent paint. Two translucent pieces brighten where they meet, so the reflection
        # pieces are opaque inside their outline, carrying the painting's own pixels (grey over the background).
        sil = ndimage.binary_fill_holes(ndimage.binary_closing(alpha > 0.04, iterations=3)) & mask
        a = ndimage.gaussian_filter(sil.astype(np.float32), 0.8) * mask
        rgb = px
    ys, xs = np.nonzero(a > 0.02)
    if not len(xs):
        print(f"skipping {p['layer']}: no paint left in it", file=sys.stderr)
        continue
    pad = 4
    x0, x1 = max(0, xs.min() - pad), min(SRC, xs.max() + pad + 1)
    y0, y1 = max(0, ys.min() - pad), min(SRC, ys.max() + pad + 1)
    # Snap the box to multiples of K so the 1x asset and 4x image share exact geometry.
    x0, y0 = x0 // K * K, y0 // K * K
    x1, y1 = -(-x1 // K) * K, -(-y1 // K) * K
    rgba = np.dstack([rgb[y0:y1, x0:x1], a[y0:y1, x0:x1] * 255]).astype(np.uint8)
    hi = Image.fromarray(rgba, 'RGBA')
    hi.save(out / 'parts@4x' / f"{p['layer']}.png", optimize=True)
    lo = hi.resize(((x1 - x0) // K, (y1 - y0) // K), Image.LANCZOS)
    lo.save(out / 'parts' / f"{p['layer']}.png", optimize=True)
    parts.append(dict(layer=p['layer'], box=(x0, y0, x1, y1), lo=lo, hi=hi, z=p.get('z', 0)))

# Paint no part covers (should be none: every bright pixel belongs to some part).
uncovered = float((alpha * ~claimed).sum() / max(1e-6, alpha.sum()))
if MIRROR:
    print('note: the painted reflection is replaced by the mirrored bird', file=sys.stderr)

# Rest pose, bottom to top by z then config order.
parts.sort(key=lambda q: q['z'])
assets, rest = [], []
for q in parts:
    x0, y0, x1, y1 = q['box']
    buf = io.BytesIO(); q['lo'].save(buf, 'PNG', optimize=True)
    assets.append({'id': q['layer'], 'name': q['layer'].replace('_', ' '), 'width': q['lo'].width, 'height': q['lo'].height,
                   'png': base64.b64encode(buf.getvalue()).decode()})
    rest.append({'layer': q['layer'], 'asset': q['layer'], 'x': round((x0 + x1) / 2 / K, 3), 'y': round((y0 + y1) / 2 / K, 3),
                 'w': (x1 - x0) / K, 'h': (y1 - y0) / K})
# Composition: the bird, its reflection and the surface strokes move together inside the ring (canvas px).
sox, soy = cfg.get('scene_offset', (0, 0))
for l in rest:
    if not (l['layer'].startswith('sweep') or l['layer'] == 'ringwhole'):
        l['x'] = round(l['x'] + sox, 3); l['y'] = round(l['y'] + soy, 3)
rest_by = {l['layer']: l for l in rest}


# ---- The idle rig ----------------------------------------------------------------------------------------------
# One loop of N frames. Every motion is a whole number of sine cycles per loop, so the last frame flows into the first.
m = dict(cfg['motion'])
N, MS = m.get('frames', 32), m.get('ms', 110)
m['neck_pivot'] = [v / K for v in geom['neck_pivot_px']]
m['waterline'] = wl / K
m['circle_centre'] = [v / K for v in cfg.get('circle_px', (512, 512))]


def turn_about(layer, pivot, deg):
    """dx, dy, da that turn a layer by deg (clockwise, canvas y down) about a pivot in canvas pixels."""
    l = rest_by[layer]
    cx, cy = l['x'], l['y']
    px_, py_ = pivot
    r = math.radians(deg)
    nx = px_ + (cx - px_) * math.cos(r) - (cy - py_) * math.sin(r)
    ny = py_ + (cx - px_) * math.sin(r) + (cy - py_) * math.cos(r)
    return nx - cx, ny - cy, deg


def ease(t):          # 0 → 1 → 0 over one loop, lingering at both ends
    return (1 - math.cos(2 * math.pi * t)) / 2


frames = []
for f in range(N):
    t = f / N
    steps = []
    # Head and beak dip toward the water and lift again, about the base of the neck.
    dip = m['dip_deg'] * ease(t)
    if 'head' in rest_by:
        dx, dy, da = turn_about('head', m['neck_pivot'], dip)
        steps.append({'slot': 'head', 'dx': round(dx, 3), 'dy': round(dy, 3), 'da': round(da, 3)})
    # The body settles a touch as the head goes down.
    if 'body' in rest_by:
        steps.append({'slot': 'body', 'dy': round(m.get('body_dy', 0.35) * ease(t), 3)})
    # The reflection mirrors the head across the waterline and ripples: a sideways sway, water_cycles times per loop.
    WC = m.get('water_cycles', 2)
    sway = math.sin(2 * math.pi * WC * t)
    if 'refl_head' in rest_by:
        mirror_pivot = [v / K for v in geom['refl_pivot_px']]
        dx, dy, da = turn_about('refl_head', mirror_pivot, -dip * geom['squash'])
        steps.append({'slot': 'refl_head', 'dx': round(dx + m['ripple_px'] * 0.6 * sway, 3), 'dy': round(dy, 3), 'da': round(da, 3),
                      'o': round(1 - m.get('ripple_fade', 0.08) * (0.5 + 0.5 * math.sin(2 * math.pi * WC * t)), 3)})
    if 'refl_body' in rest_by:
        steps.append({'slot': 'refl_body', 'dx': round(m['ripple_px'] * sway, 3),
                      'sx': round(1 + m.get('ripple_stretch', 0.012) * math.sin(2 * math.pi * WC * t + 0.9), 4),
                      'sy': round(1 - m.get('ripple_stretch', 0.012) * 0.5 * math.sin(2 * math.pi * WC * t + 0.9), 4),
                      'o': round(1 - m.get('ripple_fade', 0.08) * (0.5 + 0.5 * math.sin(2 * math.pi * WC * t)), 3)})
    bands = sorted((l for l in rest_by if l.startswith('refl_') and l[5:].isdigit()), key=lambda l: int(l[5:]))
    if bands:
        # Every band stretches about one shared vertical axis through the reflection, so stretching can't push
        # neighbouring bands' edges apart (each layer would otherwise scale about its own box centre).
        lefts = [rest_by[l]['x'] - rest_by[l]['w'] / 2 for l in bands]
        rights = [rest_by[l]['x'] + rest_by[l]['w'] / 2 for l in bands]
        axis = (min(lefts) + max(rights)) / 2
    for j, layer in enumerate(bands):
        depth = j / max(1, len(bands) - 1)                     # 0 at the feet, 1 at the bottom
        ph = j * m.get('band_phase', 0.9)
        wave = math.sin(2 * math.pi * WC * t - ph)
        sx = 1 + m.get('ripple_stretch', 0.012) * depth * math.sin(2 * math.pi * WC * t - ph + 0.9)
        about_axis = (rest_by[layer]['x'] - axis) * (sx - 1)
        steps.append({'slot': layer, 'dx': round(m['ripple_px'] * (0.4 + 1.1 * depth) * wave + about_axis, 3),
                      'sx': round(sx, 4),
                      'o': round(1 - m.get('ripple_fade', 0.08) * (0.5 + 0.5 * math.sin(2 * math.pi * WC * t)), 3)})
    strokes_ = sorted((l for l in rest_by if l.startswith('ripples_')), key=lambda l: int(l.split('_')[1]))
    for j, layer in enumerate(strokes_):
        direction = 1 if j % 2 == 0 else -1                    # neighbouring strokes slide opposite ways
        steps.append({'slot': layer, 'dx': round(direction * m.get('stroke_px', 1.6) * sway, 3),
                      'sx': round(1 + 0.025 * math.sin(2 * math.pi * WC * t + j * math.pi), 4)})
    if 'ripples' in rest_by:
        steps.append({'slot': 'ripples', 'dx': round(-m['ripple_px'] * 0.8 * sway, 3),
                      'sx': round(1 + 0.03 * math.sin(2 * math.pi * WC * t), 4)})
    # The brush stroke drifts around its circle and breathes, once per loop.
    rd = cfg.get('ring_draw')
    arcs = sorted(l for l in rest_by if l.startswith('sweep_'))
    if rd and arcs:
        # Draw on, hold, fade: the arcs appear in order along the stroke with a soft leading edge.
        def ease_io(v):
            v = min(max(v, 0.0), 1.0)
            return v * v * (3 - 2 * v)
        def smoother(v):
            v = min(max(v, 0.0), 1.0)
            return v * v * v * (v * (6 * v - 15) + 10)

        def jitter(j, b, seed):
            x = math.sin(j * 12.9898 + b * 78.233 + seed * 37.719) * 43758.5453
            return x - math.floor(x)
        draw_end, fade_start, soft = rd.get('draw', 0.32), rd.get('fade_start', 0.82), rd.get('soft', 0.05)
        NA, NR = rd.get('segments', 36), rd.get('rows', 1)
        lead = rd.get('row_lead', [0.0] * NR)
        spread = 0.12                                         # room for the earliest and latest pieces
        # A brush presses in slowly, runs fast through the middle and slows as it lifts.
        progress = smoother(t / draw_end) * (1 + soft + 2 * spread) - spread
        erase = smoother((t - fade_start) / (1 - fade_start)) * (1 + soft + 2 * spread) - spread if t >= fade_start else -10.0
        drift = m['sweep_deg'] * math.sin(2 * math.pi * t)
        breathe = 1 + m.get('sweep_breathe', 0.006) * math.sin(2 * math.pi * (t + 0.25))
        whole = 'ringwhole' in rest_by and rd.get('fade') == 'opacity'
        handed_over = whole and t >= draw_end
        if whole:
            fade_o = 1 - smoother((t - fade_start) / (1 - fade_start)) if t >= fade_start else 1.0
            dxw, dyw, daw = turn_about('ringwhole', m['circle_centre'], drift)
            steps.append({'slot': 'ringwhole', 'dx': round(dxw, 3), 'dy': round(dyw, 3), 'da': round(daw, 3), 'sx': round(breathe, 4), 'sy': round(breathe, 4),
                          'o': round(fade_o if handed_over else 0.0, 3)})
        for layer in arcs:
            bits = layer.split('_')
            j = int(bits[1]); b = int(bits[2]) if len(bits) > 2 else 0
            u_mid = (j + 0.5) / NA
            # Each piece arrives at its own moment: a per-row lead that drifts along the stroke, plus a fixed jitter.
            off = lead[b] + 0.03 * math.sin(2 * math.pi * (1.3 * u_mid + 0.37 * b)) + rd.get('jitter', 0.04) * (jitter(j, b, 1) - 0.5)
            off_e = lead[b] * 0.5 + rd.get('jitter', 0.04) * 1.5 * (jitter(j, b, 2) - 0.5)
            o_in = smoother((progress - (u_mid + off)) / soft + 0.5)
            o_out = 1 - smoother((erase - (u_mid + off_e)) / (soft * 1.6) + 0.5)
            o = o_in * o_out
            if whole:
                o = 0.0 if handed_over else o_in
            dx, dy, da = turn_about(layer, m['circle_centre'], drift)
            steps.append({'slot': layer, 'dx': round(dx, 3), 'dy': round(dy, 3), 'da': round(da, 3), 'sx': round(breathe, 4), 'sy': round(breathe, 4), 'o': round(o, 3)})
    for i, layer in enumerate(l for l in rest_by if l.startswith('sweep') and not (rd and l.startswith('sweep_'))):
        phase = i * 0.25
        drift = m['sweep_deg'] * math.sin(2 * math.pi * (t + phase))
        dx, dy, da = turn_about(layer, m['circle_centre'], drift)
        breathe = 1 + m.get('sweep_breathe', 0.006) * math.sin(2 * math.pi * (t + phase + 0.25))
        steps.append({'slot': layer, 'dx': round(dx, 3), 'dy': round(dy, 3), 'da': round(da, 3), 'sx': round(breathe, 4), 'sy': round(breathe, 4)})
    frames.append({'ms': MS, 'slots': steps})

sprite_id = cfg['id']
slots = [{'id': l['layer'], 'name': l['layer'].replace('_', ' ').capitalize()} for l in rest]
rig = {'id': f'{sprite_id}-idle', 'owner': sprite_id, 'revision': 1, 'name': 'Idle', 'loop': True, 'slots': slots, 'frames': frames}
doc = {'format': 'spritesmith.sprite@1', 'id': sprite_id, 'name': cfg['name'], 'canvas': [CANVAS, CANVAS], 'origin': [CANVAS / 2, CANVAS / 2],
       'assets': assets, 'rest': rest, 'animations': [{'id': 'idle', 'name': 'Idle', 'rig': {'id': rig['id'], 'revision': 1}}]}
(out / 'sprite.json').write_text(json.dumps(doc, separators=(',', ':')))
(out / 'rig.json').write_text(json.dumps(rig, separators=(',', ':')))


# ---- Render, the way the sprite@1 renderer does: each frame from the rest pose, each layer about its centre --------
def render(step_map, scale):
    canvas = Image.new('RGBA', (CANVAS * scale, CANVAS * scale), tuple(int(c) for c in bg) + (255,))
    for l in rest:
        d = step_map.get(l['layer'], {})
        q = next(p for p in parts if p['layer'] == l['layer'])
        src = q['hi'] if scale > 1 else q['lo']
        w = l['w'] * d.get('sx', 1) * scale
        h = l['h'] * d.get('sy', 1) * scale
        im = src.resize((max(1, round(w)), max(1, round(h))), Image.LANCZOS)
        if 'o' in d:
            a = np.asarray(im).copy(); a[..., 3] = (a[..., 3] * d['o']).astype(np.uint8); im = Image.fromarray(a, 'RGBA')
        im = im.rotate(-d.get('da', 0), resample=Image.BICUBIC, expand=True)
        cx = (l['x'] + d.get('dx', 0)) * scale
        cy = (l['y'] + d.get('dy', 0)) * scale
        canvas.alpha_composite(im, (round(cx - im.width / 2), round(cy - im.height / 2)))
    return canvas.convert('RGB')


rest_img = render({}, K)
ref = px * alpha[..., None] + bg * (1 - alpha[..., None]) if TRANSPARENT else px
diff = np.abs(np.asarray(rest_img).astype(np.float32) - ref).mean()
review = []
for f, fr in enumerate(frames):
    im = render({s['slot']: s for s in fr['slots']}, 2)
    im.save(out / 'frames' / f'{f:02d}.png', optimize=True)
    review.append(im)
review[0].save(out / 'idle.gif', save_all=True, append_images=review[1:], duration=MS, loop=0, optimize=True)
# A strip of the extreme frames for a quick look: rest, deepest dip, ripple extremes.
pick = [0, N // 4, N // 2, 3 * N // 4]
strip = Image.new('RGB', (len(pick) * 512, 512))
for i, f in enumerate(pick):
    strip.paste(review[f], (i * 512, 0))
strip.save(out / 'review-strip.png')
(out / 'geometry.json').write_text(json.dumps(geom))
print(json.dumps({'id': sprite_id, 'geometry': geom, 'parts': [l['layer'] for l in rest], 'rest_vs_original_mean_abs_diff': round(float(diff), 2),
                  'uncovered_paint_fraction': round(uncovered, 4), 'sprite_bytes': (out / 'sprite.json').stat().st_size,
                  'asset_sizes': {a['id']: [a['width'], a['height']] for a in assets}}))
