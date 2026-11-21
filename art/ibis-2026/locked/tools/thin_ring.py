"""Make the painted ring thinner by squeezing it toward the middle of its own stroke.

Usage: python -I thin_ring.py PAINTING.png OUT.png FACTOR

At every angle around the ring, the stroke's middle (the alpha-weighted mean radius there) stays put and the paint
on either side is pulled in toward it by FACTOR (0.7 keeps 70% of the width). The bristle texture, the taper along
the stroke and the open gap are kept; only the width changes. Everything that is not the ring is left untouched.
The ring is the connected paint that sits far out from the centre, the same rule the cut pipeline uses.
"""
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

src, out, factor = sys.argv[1], sys.argv[2], float(sys.argv[3])
img = np.asarray(Image.open(src).convert('RGBA')).astype(np.float64)
H, W = img.shape[:2]
alpha = img[..., 3] / 255
yy, xx = np.mgrid[0:H, 0:W]

# Ring mask: components whose mean radius is far out, plus faint dust nearest to them.
solid = ndimage.binary_dilation(alpha > 0.12, iterations=3)
lab, _ = ndimage.label(solid)
keep = np.zeros_like(solid)
for i, sl in enumerate(ndimage.find_objects(lab), start=1):
    pts = np.argwhere(lab[sl] == i) + (sl[0].start, sl[1].start)
    if np.hypot(pts[:, 1] - W / 2, pts[:, 0] - H / 2).mean() > 290 * W / 1024:
        keep |= lab == i
seed = np.where(keep, 1, np.where(solid, 2, 0)).astype(np.int8)
_, (iy, ix) = ndimage.distance_transform_edt(seed == 0, return_indices=True)
ring_m = (seed[iy, ix] == 1) & (alpha > 0)

# Circle through the stroke.
w = alpha * ring_m
ys, xs = np.nonzero(w > 0.3)
A = np.c_[xs, ys, np.ones_like(xs)]
cx2, cy2, c = np.linalg.lstsq(A, xs ** 2 + ys ** 2, rcond=None)[0]
cx, cy = cx2 / 2, cy2 / 2

# Middle of the stroke at each angle: alpha-weighted mean radius, smoothed round the circle. Angles with no paint
# take the nearest painted angle's value, so the tapered ends squeeze toward a sensible line.
NB = 1440
r = np.hypot(xx - cx, yy - cy)
th = np.arctan2(yy - cy, xx - cx)
b = ((th + np.pi) / (2 * np.pi) * NB).astype(int) % NB
sw = np.bincount(b.ravel(), w.ravel(), NB)
sr = np.bincount(b.ravel(), (w * r).ravel(), NB)
has = sw > 1.0
mid = np.where(has, sr / np.maximum(sw, 1e-9), np.nan)
idx = np.where(has, np.arange(NB), -1)
# nearest painted bin, circularly
valid = np.nonzero(has)[0]
d = np.abs(np.arange(NB)[:, None] - valid[None, :]); d = np.minimum(d, NB - d)
mid = mid[valid[d.argmin(axis=1)]]
k = 15
pad = np.r_[mid[-k:], mid, mid[:k]]
mid = np.convolve(pad, np.ones(2 * k + 1) / (2 * k + 1), mode='same')[k:-k]

# Pull every output pixel's sample from further out along its radius: r_src = mid + (r - mid) / factor.
th_c = th
m_at = np.interp((th_c + np.pi) / (2 * np.pi) * NB, np.arange(NB + 1), np.r_[mid, mid[0]])
r_src = m_at + (r - m_at) / factor
sx = cx + r_src * np.cos(th_c)
sy = cy + r_src * np.sin(th_c)
far = np.abs(r - m_at) > 0.12 * np.nanmean(mid)        # only the band around the stroke is resampled
sx[far] = -10; sy[far] = -10

ring = img * ring_m[..., None]
pm = ring.copy(); pm[..., :3] *= pm[..., 3:4] / 255          # premultiply so edges don't darken
thin = np.stack([ndimage.map_coordinates(pm[..., ch], [sy, sx], order=1, mode='constant') for ch in range(4)], -1)
a = thin[..., 3:4]
thin[..., :3] = np.where(a > 0, thin[..., :3] / np.maximum(a, 1e-9) * 255, 0)

rest = img * (~ring_m)[..., None]
base = Image.fromarray(np.clip(thin, 0, 255).astype(np.uint8), 'RGBA')
base.alpha_composite(Image.fromarray(rest.astype(np.uint8), 'RGBA'))
base.save(out, optimize=True)


def width(mask_alpha):
    """Mean stroke width in px: painted area along the ring divided by its length."""
    return mask_alpha.sum() / (has.sum() / NB * 2 * np.pi * np.nanmean(mid))


print(f'centre ({cx:.1f}, {cy:.1f})  mean radius {np.nanmean(mid):.1f}  width {width(w):.1f} -> {width(thin[..., 3] / 255):.1f} px')
