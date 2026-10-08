"""Avior Studio enso explorations: a brush sweep, a silhouette ibis, its reflection. Each animation is a variation."""
import math
from spritesmith import P_ell, P_limb
from spritesmith.text import word

KEY = 'avior_enso'
NAME = 'Avior Studio — enso variations'
SIZE = (128, 128)
SIZES = {'wordmark': (160, 160), 'lockup': (224, 96)}
ANIMS = {k: 1 for k in ['enso', 'gap_top', 'closed', 'dry', 'double', 'knockout', 'mirror', 'waterline', 'breakout',
                        'flight', 'profile', 'cradle', 'spiral', 'sumi', 'moonrise', 'wordmark', 'lockup']}
PALETTE = {'ink': '#253729', 'stroke': '#253729', 'water': '#253729', 'disc': '#253729', 'paper': '#f4f3eb'}
VARIANTS = {
    'black': {'ink': '#141414', 'stroke': '#141414', 'water': '#141414', 'disc': '#141414'},
    'cream': {'ink': '#f4f3eb', 'stroke': '#f4f3eb', 'water': '#f4f3eb', 'disc': '#f4f3eb', 'paper': '#253729'},
    'teal': {'ink': '#1e4d50', 'stroke': '#1e4d50', 'water': '#1e4d50', 'disc': '#1e4d50'},
    'gold_ring': {'ink': '#253729', 'stroke': '#d99a45', 'water': '#79bbb2', 'disc': '#253729'},
    'teal_ring': {'ink': '#253729', 'stroke': '#1e4d50', 'water': '#79bbb2', 'disc': '#253729'},
    'ember': {'ink': '#3a1f1a', 'stroke': '#c4552e', 'water': '#e2a15a', 'disc': '#3a1f1a'},
    'night': {'ink': '#e9eef2', 'stroke': '#dfe6ee', 'water': '#8fa6bd', 'disc': '#e9eef2', 'paper': '#121c2a'},
    # single inks
    'plum': {'ink': '#4a2a4f', 'stroke': '#4a2a4f', 'water': '#4a2a4f', 'disc': '#4a2a4f'},
    'indigo': {'ink': '#2b3a67', 'stroke': '#2b3a67', 'water': '#2b3a67', 'disc': '#2b3a67'},
    'rust': {'ink': '#9a4a2a', 'stroke': '#9a4a2a', 'water': '#9a4a2a', 'disc': '#9a4a2a'},
    'olive': {'ink': '#5b6b2a', 'stroke': '#5b6b2a', 'water': '#5b6b2a', 'disc': '#5b6b2a'},
    'slate': {'ink': '#3d4a52', 'stroke': '#3d4a52', 'water': '#3d4a52', 'disc': '#3d4a52'},
    'cocoa': {'ink': '#4a3326', 'stroke': '#4a3326', 'water': '#4a3326', 'disc': '#4a3326'},
    # two-tone: forest bird, coloured sweep
    'coral_sweep': {'stroke': '#e8735a', 'water': '#f2b5a4'},
    'violet_sweep': {'stroke': '#7b5ea7', 'water': '#c3b3e0'},
    'sky_sweep': {'stroke': '#4f9fd6', 'water': '#a9d3ef'},
    'moss_sweep': {'stroke': '#6f9a4a', 'water': '#b9d19a'},
    'mustard_sweep': {'stroke': '#d6a820', 'water': '#f0d98a'},
    'rose_sweep': {'stroke': '#c45c8a', 'water': '#ebb3cb'},
    # three-tone
    'lagoon': {'ink': '#1e4d50', 'stroke': '#d99a45', 'water': '#79bbb2', 'disc': '#1e4d50'},
    'sunset': {'ink': '#3a1f1a', 'stroke': '#f08a5a', 'water': '#7a86c2', 'disc': '#3a1f1a'},
    'tidal': {'ink': '#253729', 'stroke': '#79bbb2', 'water': '#d99a45', 'disc': '#253729'},
    # light on dark
    'gold_on_navy': {'ink': '#e1b16e', 'stroke': '#e1b16e', 'water': '#8fa6bd', 'disc': '#e1b16e', 'paper': '#121c2a'},
    'mint_on_forest': {'ink': '#d6efe0', 'stroke': '#79bbb2', 'water': '#79bbb2', 'disc': '#d6efe0', 'paper': '#253729'},
    'coral_on_plum': {'ink': '#f4f3eb', 'stroke': '#f08a5a', 'water': '#c3b3e0', 'disc': '#f4f3eb', 'paper': '#2b2246'},
    'cream_on_ember': {'ink': '#fff6e8', 'stroke': '#f5c060', 'water': '#e2a15a', 'disc': '#fff6e8', 'paper': '#4a2520'},
    'white': {'ink': '#ffffff', 'stroke': '#ffffff', 'water': '#ffffff', 'disc': '#ffffff', 'paper': '#000000'},
    'teal_on_black': {'ink': '#79bbb2', 'stroke': '#79bbb2', 'water': '#79bbb2', 'disc': '#79bbb2', 'paper': '#141414'},
}

BIRD = ('M34 64 C39 54 45 43 58 42 C65 41 70 45 73 42 C76 39 70 31 73 24 C76 17 84 18 87 23 C89 27 85 31 82 31 '
        'C80 39 85 46 76 52 C71 56 68 66 55 68 C46 71 39 69 31 73 Z')
BEAK = 'M84 25 C98 35 104 47 102 60 C100 48 92 37 82 31 Z'
LEG_A = 'M55 58 L54 88 L52 92 L57 92 L58 88 L59 58 Z'
LEG_B = 'M66 58 L66 86 L69 92 L74 92 L71 85 L71 58 Z'


def bird(s, col='@ink', dx=0, dy=0, k=1.0):
    with s.g(dx=dx, dy=dy, sx=k, sy=k, about=(64, 92)):
        for d in (LEG_A, LEG_B, BIRD, BEAK):
            s.flat(d, col)


def reflection(s, boundary, top=92, op=.3, col='@ink', dx=0, dy=0, k=1.0, squash=.4):
    cid = s._id()
    s.defs.append(f'<clipPath id="wb{cid}">{boundary}</clipPath>')
    s.defs.append(f'<clipPath id="rf{cid}"><path d="M0 {top}H{s.w}V{s.h}H0Z"/></clipPath>')
    s.raw(f'<g clip-path="url(#wb{cid})"><g clip-path="url(#rf{cid})" opacity="{op}">'
          f'<g transform="translate(0 {top * (1 + squash):.1f}) scale(1 -{squash})">')
    bird(s, col, dx, dy, k)
    s.raw('</g></g></g>')


def brush(cx, cy, r, start, end, w0, w1, steps=64, wob=0.0, drift=0.0):
    """Closed path of a brush-stroke arc tapering from w0 to w1. `wob` ripples the edges; `drift` pulls the
    radius inward over the stroke (a spiral)."""
    outer, inner = [], []
    for n in range(steps + 1):
        t = n / steps
        a = math.radians(start + (end - start) * t)
        w = w0 + (w1 - w0) * t + wob * math.sin(t * 29) * (1 - t)
        rr = r - drift * t
        outer.append((cx + (rr + w / 2) * math.cos(a), cy + (rr + w / 2) * math.sin(a)))
        inner.append((cx + (rr - w / 2) * math.cos(a), cy + (rr - w / 2) * math.sin(a)))
    pts = outer + inner[::-1]
    return 'M' + ' L'.join(f'{x:.2f} {y:.2f}' for x, y in pts) + 'Z'


def ripples(s, col='@water', dy=0, ws=(1.4, 1.1, .9), op=.5):
    with s.g(dy=dy):
        for (d, w) in zip(['M40 96 Q62 99 84 95', 'M47 103 Q62 101 80 103', 'M52 110 Q62 112 74 110'], ws):
            s.curve(d, col, w, sw=0, op=op)


def flying(s, col='@ink'):
    body = 'M36 74 C44 66 58 62 76 62 C84 62 92 66 98 72 C92 78 80 84 64 84 C52 84 42 80 36 74 Z'
    upper = 'M68 64 C56 54 42 36 30 14 C50 22 70 38 82 56 C80 62 74 66 68 66 Z'
    lower = 'M58 78 C52 92 50 104 52 116 C60 108 72 96 78 82 C76 78 70 76 64 76 Z'
    for d in (body, upper, lower, P_limb([(94, 68), (104, 60), (110, 50)], 9, 6), P_ell(110, 48, 7, 6),
              'M114 50 C122 58 124 70 118 82 C118 70 114 62 108 56 Z'):
        s.flat(d, col)
    s.curve('M38 74 C30 72 24 76 20 82 M38 74 C28 74 22 70 18 68', col, 1.6, sw=0)


def draw(s, anim, i):
    if anim == 'enso':
        s.flat(brush(64, 64, 52, 200, 505, 10, .8), '@stroke')
        reflection(s, '<circle cx="64" cy="64" r="49"/>')
        bird(s); ripples(s)

    elif anim == 'gap_top':
        # The sweep starts low on the left and ends thin at the top right, so the beak points into the opening.
        s.flat(brush(64, 64, 52, 160, 440, 11, .6), '@stroke')
        reflection(s, '<circle cx="64" cy="64" r="49"/>')
        bird(s); ripples(s)

    elif anim == 'closed':
        s.flat(brush(64, 64, 52, 0, 360, 7.5, 7.5, wob=.5), '@stroke')
        reflection(s, '<circle cx="64" cy="64" r="49"/>')
        bird(s); ripples(s)

    elif anim == 'dry':
        # Dry-brush: the sweep splits into streaks as the ink runs out.
        s.flat(brush(64, 64, 52, 200, 400, 10, 5, wob=.6), '@stroke')
        for r, w0, w1, end, op in [(55, 2.2, .3, 505, 1), (51.5, 2.6, .4, 498, 1), (48.5, 1.6, .2, 490, .8), (53.5, 1.2, .2, 512, .7)]:
            s.flat(brush(64, 64, r, 395, end, w0, w1), '@stroke')
        reflection(s, '<circle cx="64" cy="64" r="47"/>')
        bird(s); ripples(s)

    elif anim == 'double':
        s.flat(brush(64, 64, 55, 205, 500, 4, .6), '@stroke')
        s.flat(brush(64, 64, 48, 190, 470, 7, .6), '@stroke')
        reflection(s, '<circle cx="64" cy="64" r="45"/>', op=.28, k=.92)
        bird(s, k=.92); ripples(s, dy=-1, ws=(1.2, 1, .8))

    elif anim == 'knockout':
        s.dot(64, 64, 58, '@disc')
        reflection(s, '<circle cx="64" cy="64" r="58"/>', col='@paper', op=.22)
        bird(s, '@paper'); ripples(s, col='@paper', op=.6)
        s.flat(brush(64, 64, 52, 200, 505, 3, .4), '@paper')

    elif anim == 'mirror':
        s.flat(brush(64, 64, 54, 200, 505, 9, .8), '@stroke')
        reflection(s, '<circle cx="64" cy="64" r="51"/>', top=92, op=.38, squash=.62)
        bird(s)
        s.curve('M30 92 H98', '@water', .9, sw=0, op=.5)

    elif anim == 'waterline':
        s.flat(brush(64, 60, 52, 200, 505, 10, .8), '@stroke')
        s.flat('M14 90.5 Q64 85.5 116 90.5 Q64 94.5 14 90.5 Z', '@water')
        reflection(s, '<circle cx="64" cy="60" r="49"/>', top=90, op=.26)
        bird(s, dy=-2)

    elif anim == 'breakout':
        s.flat(brush(64, 66, 50, 200, 505, 10, .8), '@stroke')
        reflection(s, '<circle cx="64" cy="66" r="47"/>', top=100, op=.28, dx=-6, dy=8, k=1.22)
        bird(s, dx=-6, dy=8, k=1.22); ripples(s, dy=8)

    elif anim == 'flight':
        s.flat(brush(64, 66, 54, 150, 440, 9, .8), '@stroke')
        with s.g(dx=-2, dy=0, sx=.9, sy=.9, about=(64, 64)):
            flying(s)

    elif anim == 'profile':
        s.flat(brush(64, 64, 54, 200, 505, 10, .8), '@stroke')
        cid = s._id()
        s.defs.append(f'<clipPath id="pr{cid}"><circle cx="64" cy="64" r="49"/></clipPath>')
        s.raw(f'<g clip-path="url(#pr{cid})">')
        for d in (P_limb([(36, 130), (30, 104), (40, 76), (62, 54)], 17, 12), P_ell(68, 50, 12.5, 10)):
            s.flat(d, '@ink')
        s.raw('</g>')
        s.flat('M78 46 C94 54 104 70 108 98 C100 76 90 62 76 56 Z', '@ink')
        s.dot(71, 46, 2.2, '@paper')
        for d, w in [('M64 100 Q80 104 98 100', 1.3), ('M70 109 Q82 107 94 109', 1)]:
            s.curve(d, '@water', w, sw=0, op=.6)

    elif anim == 'cradle':
        # Only the lower sweep, like a nest or a bowl of water the bird stands in.
        s.flat(brush(64, 58, 54, 150, 400, 1, 11, wob=.3), '@stroke')
        reflection(s, '<circle cx="64" cy="58" r="51"/>', top=92, op=.28)
        bird(s); ripples(s, dy=-2)

    elif anim == 'spiral':
        s.flat(brush(64, 64, 56, 180, 560, 9, .6, drift=10), '@stroke')
        reflection(s, '<circle cx="64" cy="64" r="48"/>', op=.28, k=.9, dy=-2)
        bird(s, k=.9, dy=-2); ripples(s, dy=-3, ws=(1.2, 1, .8))

    elif anim == 'sumi':
        # Sumi-e: the sweep is one wet stroke, the bird and water are drawn with the same brush.
        s.flat(brush(64, 64, 52, 200, 505, 12, 1.4, wob=.8), '@stroke')
        s.flat(brush(64, 64, 49, 440, 500, 1.2, .2), '@stroke')
        bird(s)
        for (x0, y, x1, w) in [(36, 96, 96, 3.6), (46, 104, 88, 2.6), (56, 111, 80, 1.8)]:
            pts = [(x0 + (x1 - x0) * t, y + .8 * math.sin(t * math.pi)) for t in (n / 12 for n in range(13))]
            s.flat(P_limb(pts, w, .2), '@water')

    elif anim == 'moonrise':
        s.flat(brush(64, 64, 52, 200, 505, 10, .8), '@stroke')
        s.dot(32, 36, 13, '@stroke')
        s.dot(38, 31, 11.5, '@paper')
        reflection(s, '<circle cx="64" cy="64" r="49"/>')
        bird(s); ripples(s)

    elif anim == 'wordmark':
        with s.g(dx=16, dy=-12):
            s.flat(brush(64, 64, 52, 200, 505, 10, .8), '@stroke')
            reflection(s, '<circle cx="64" cy="64" r="49"/>')
            bird(s); ripples(s)
        for p in word('AVIOR', 80, 138, 19, track=3):
            s.flat(p, '@ink')

    elif anim == 'lockup':
        with s.g(dx=-16, dy=-20, sx=.66, sy=.66, about=(64, 64)):
            s.flat(brush(64, 64, 52, 200, 505, 10, .8), '@stroke')
            reflection(s, '<circle cx="64" cy="64" r="49"/>')
            bird(s); ripples(s)
        for p in word('AVIOR', 96, 52, 26, track=1, align='left'):
            s.flat(p, '@ink')
        for p in word('STUDIO', 97, 72, 12, track=5, align='left'):
            s.flat(p, '@ink', op=.7)
