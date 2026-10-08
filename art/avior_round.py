"""The Avior Studio mark and the steps that led to it.

The mark is `mark`: a white ibis and its reflection in still water, cradled by one brush sweep that starts
thin and ends round, the bird's outline lightly smoothed. The other animations are the exploration around
it (the untouched round-two cradle, heavier smoothing, and one-dial steps), kept so the choice can be
revisited. White silhouette on black; the site puts it on a black tile."""
import math
import re
from spritesmith import P_ell, P_limb, capsule

KEY = 'avior_round'
NAME = 'Avior Studio — rounded cradle'
SIZE = (128, 128)
STEPS = {
    'mark':        dict(w0=2.0, w1=7.0, eye=1.7, centre=True),     # the chosen mark: Smooth, the skinnier sweep, a dot eye
    'smooth':      dict(),
    'k2':          dict(k=2),
    'k4':          dict(k=4),
    'fat':         dict(fat=.6),
    'legs':        dict(legw=5.2),
    'thin_start':  dict(w0=3.6),
    'heavy':       dict(w1=12.5),
    'light':       dict(w1=9.5),
    'eased':       dict(ease=True),
    'bigger':      dict(scale=1.07),
    'smaller':     dict(scale=.94),
    'no_mirror':   dict(refl=0),
    'mirror':      dict(refl=.42),
    'ripples':     dict(ripw=(2.0, 1.6, 1.2)),
    'no_ripples':  dict(ripw=None),
    'gap_left':    dict(start=142, end=392),
    'gap_right':   dict(start=158, end=408),
    'low':         dict(cy=61),
    'thin1':       dict(w0=2.2, w1=8.5),
    'thin2':       dict(w0=2.0, w1=7.0),
    'thin3':       dict(w0=1.8, w1=5.5),
    'thin4':       dict(w0=1.6, w1=4.0),
    'even':        dict(w0=4.0, w1=4.0),
}
ANIMS = {k: 1 for k in ['base', 'caps', 'smoother', 'smoothest', 'plump', 'built'] + list(STEPS)}
PALETTE = {'ink': '#ffffff', 'paper': '#000000'}
VARIANTS = {'cream': {'ink': '#f4f3eb'}, 'bone': {'ink': '#e6dcc4'}}

BIRD = ('M34 64 C39 54 45 43 58 42 C65 41 70 45 73 42 C76 39 70 31 73 24 C76 17 84 18 87 23 C89 27 85 31 82 31 '
        'C80 39 85 46 76 52 C71 56 68 66 55 68 C46 71 39 69 31 73 Z')
BEAK = 'M84 25 C98 35 104 47 102 60 C100 48 92 37 82 31 Z'
LEG_A = 'M55 58 L54 88 L52 92 L57 92 L58 88 L59 58 Z'
LEG_B = 'M66 58 L66 86 L69 92 L74 92 L71 85 L71 58 Z'


def sample(path, step=1.0):
    toks = re.findall(r'[MCLZ]|-?[\d.]+', path)
    pts, cur, n = [], None, 0
    while n < len(toks):
        c = toks[n]; n += 1
        if c == 'M':
            cur = (float(toks[n]), float(toks[n + 1])); n += 2; pts.append(cur)
        elif c == 'L':
            p = (float(toks[n]), float(toks[n + 1])); n += 2
            k = max(1, int(math.dist(cur, p) / step))
            pts += [(cur[0] + (p[0] - cur[0]) * t / k, cur[1] + (p[1] - cur[1]) * t / k) for t in range(1, k + 1)]
            cur = p
        elif c == 'C':
            c1, c2, p = [(float(toks[n + j]), float(toks[n + j + 1])) for j in (0, 2, 4)]; n += 6
            k = max(2, int((math.dist(cur, c1) + math.dist(c1, c2) + math.dist(c2, p)) / step))
            for j in range(1, k + 1):
                t = j / k; u = 1 - t
                pts.append((u ** 3 * cur[0] + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t ** 3 * p[0],
                            u ** 3 * cur[1] + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t ** 3 * p[1]))
            cur = p
    return pts


def smooth(pts, k, passes=2):
    """Average each point with its k neighbours either side, closed, a few passes: rounds every corner."""
    n = len(pts)
    for _ in range(passes):
        pts = [(sum(pts[(i + j) % n][0] for j in range(-k, k + 1)) / (2 * k + 1),
                sum(pts[(i + j) % n][1] for j in range(-k, k + 1)) / (2 * k + 1)) for i in range(n)]
    return pts


def inflate(pts, d):
    """Push each point outward along its normal by d (positive = fatter)."""
    n = len(pts); out = []
    for i, p in enumerate(pts):
        a, b = pts[i - 1], pts[(i + 1) % n]
        tx, ty = b[0] - a[0], b[1] - a[1]
        l = math.hypot(tx, ty) or 1
        out.append((p[0] + ty / l * d, p[1] - tx / l * d))
    return out


def poly(pts):
    return 'M' + ' L'.join(f'{x:.2f} {y:.2f}' for x, y in pts) + 'Z'


def brush(cx, cy, r, start, end, w0, w1, steps=96, ease=False):
    outer, inner = [], []
    for n in range(steps + 1):
        t = n / steps
        if ease:
            t_w = t * t * (3 - 2 * t)
        else:
            t_w = t
        a = math.radians(start + (end - start) * t)
        w = w0 + (w1 - w0) * t_w
        outer.append((cx + (r + w / 2) * math.cos(a), cy + (r + w / 2) * math.sin(a)))
        inner.append((cx + (r - w / 2) * math.cos(a), cy + (r - w / 2) * math.sin(a)))
    return poly(outer + inner[::-1])


def sweep(s, w0=1.0, w1=11.0, caps=False, ease=False, start=150, end=400, cy=58):
    cx, r = 64, 54
    s.flat(brush(cx, cy, r, start, end, w0, w1, ease=ease), '@ink')
    if caps:
        for a, w in ((start, w0), (end, w1)):
            s.dot(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)), w / 2, '@ink')


def bird_smooth(s, k=0, fat=0.0, legs='capsule', legw=4.2):
    """The silhouette, smoothed by window k (0 = as drawn), inflated by `fat`, with rounded leg ends."""
    body = sample(BIRD)
    if k:
        body = smooth(body, k)
    if fat:
        body = inflate(body, fat)
    beak = sample(BEAK)
    if k:
        beak = smooth(beak, max(1, k // 3), passes=1)
    s.flat(poly(body), '@ink')
    s.flat(poly(beak), '@ink')
    if k:
        s.dot(84, 28.5, 3.2 + k * .12, '@ink')   # keep the beak rooted in the head as the head rounds off
    if legs == 'capsule':
        s.flat(capsule((55.5, 60), (53.5, 91), legw + fat), '@ink')
        s.flat(capsule((68, 60), (71, 91), legw + fat), '@ink')
    else:
        s.flat(LEG_A, '@ink'); s.flat(LEG_B, '@ink')


def bird_built(s):
    """The ibis rebuilt from round parts only: ellipses and tapered limbs merged into one silhouette."""
    body = P_ell(54, 60, 22, 13, rot=-14)
    neck = P_limb([(70, 60), (74, 44), (77, 30)], 14, 10)
    head = P_ell(80, 26, 9, 8)
    beak = P_limb([(86, 28), (96, 38), (102, 50), (103, 60)], 5.5, 1.2)
    tail = P_limb([(50, 62), (40, 67), (32, 73)], 10, 3)
    for d in (body, neck, head, beak, tail):
        s.flat(d, '@ink')
    s.flat(capsule((55.5, 62), (53.5, 91), 4.4), '@ink')
    s.flat(capsule((68, 62), (71, 91), 4.4), '@ink')


def reflection(s, draw, top=92, op=.3, cy=58):
    cid = s._id()
    s.defs.append(f'<clipPath id="wb{cid}"><circle cx="64" cy="{cy}" r="51"/></clipPath>')
    s.defs.append(f'<clipPath id="rf{cid}"><path d="M0 {top}H128V128H0Z"/></clipPath>')
    s.raw(f'<g clip-path="url(#wb{cid})"><g clip-path="url(#rf{cid})" opacity="{op}">'
          f'<g transform="translate(0 {top * 1.4:.1f}) scale(1 -.4)">')
    draw()
    s.raw('</g></g></g>')


def ripples(s, dy=-2, op=.5, ws=(1.4, 1.1, .9)):
    for d, w in zip(['M40 96 Q62 99 84 95', 'M47 103 Q62 101 80 103', 'M52 110 Q62 112 74 110'], ws):
        s.raw(f'<path d="{d}" transform="translate(0 {dy})" fill="none" stroke="{s_ink()}" stroke-width="{w}" '
              f'stroke-linecap="round" opacity="{op}"/>')


def s_ink():
    from spritesmith import pal
    return pal('ink')


def cradle(s, k=3, fat=0.0, legw=4.2, w0=2.5, w1=11.0, ease=False, scale=1.0, refl=.3, ripw=(1.4, 1.1, .9), start=150, end=400, cy=58, eye=0.0, centre=False):
    if centre:
        # The drawing's ink (sweep, bird and reflection) is centred on (64.9, 55.6) at full size; move it onto
        # the canvas centre and scale it to leave an even margin, so tiles and icons sit true.
        s.raw('<g transform="translate(64 64) scale(0.9) translate(-64.9 -55.6)">')
    sweep(s, w0=w0, w1=w1, caps=True, ease=ease, start=start, end=end, cy=cy)
    def b():
        with s.g(sx=scale, sy=scale, about=(62, 92)):
            bird_smooth(s, k, fat=fat, legw=legw)
    if refl:
        reflection(s, b, op=refl, cy=cy)
    b()
    if eye:
        with s.g(sx=scale, sy=scale, about=(62, 92)):
            s.dot(82.2, 25.2, eye, '@paper')   # the eye, in the ground colour
    if ripw:
        ripples(s, ws=ripw)
    if centre:
        s.raw('</g>')


def draw(s, anim, i):
    if anim in STEPS:
        cradle(s, **STEPS[anim])
    elif anim == 'base':
        sweep(s); reflection(s, lambda: bird_smooth(s, 0, legs='flat')); bird_smooth(s, 0, legs='flat'); ripples(s)
    elif anim == 'caps':
        sweep(s, w0=2.5, caps=True); reflection(s, lambda: bird_smooth(s, 0)); bird_smooth(s, 0); ripples(s)
    elif anim == 'smoother':
        sweep(s, w0=2.5, caps=True); reflection(s, lambda: bird_smooth(s, 6)); bird_smooth(s, 6); ripples(s)
    elif anim == 'smoothest':
        sweep(s, w0=3, caps=True); reflection(s, lambda: bird_smooth(s, 10)); bird_smooth(s, 10); ripples(s)
    elif anim == 'plump':
        sweep(s, w0=3, caps=True); reflection(s, lambda: bird_smooth(s, 6, fat=1.2)); bird_smooth(s, 6, fat=1.2); ripples(s)
    elif anim == 'built':
        sweep(s, w0=3, caps=True); reflection(s, lambda: bird_built(s)); bird_built(s); ripples(s)
