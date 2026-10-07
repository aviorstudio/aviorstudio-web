"""Avior's ibis and its reflection, authored with Spritesmith's vector primitives."""
KEY = 'avior_ibis'
NAME = 'Avior Studio — ibis standing above its reflection'
SIZE = (128, 128)
ANIMS = {'badge': 1, 'pond': 1, 'seal': 1}


def bird(s, seal=False):
    feather = '#fff4d7' if not seal else '#f7ead0'
    leg = '#dfac72'
    s.curve('M58 66 L57 87 L55 91 M68 65 L68 85 L71 91', leg, 1.8)
    s.shape('M34 64 C39 54 45 43 58 42 C65 41 70 45 73 42 C76 39 70 31 73 24 C76 17 84 18 87 23 C89 27 85 31 82 31 C80 39 85 46 76 52 C71 56 68 66 55 68 C46 71 39 69 31 73 Z', feather, sw=2.4)
    s.shape('M84 25 C98 35 104 47 102 60 C100 48 92 37 82 31 Z', '#d9a06b', sw=1.7)
    s.shape('M38 62 C47 50 59 49 68 51 C64 60 51 66 38 67 Z', '#e1c79b', sw=1.4)
    s.curve('M43 61 Q53 56 61 55', feather, 1.2, sw=0)
    s.dot(82, 24, 1.5, '#242b31')
    s.dot(82.4, 23.6, .45, '#fff4d7')


def draw(s, anim, i):
    if anim == 'badge':
        s.shape('M64 6 C94 6 118 29 118 60 C118 94 94 116 64 123 C34 116 10 94 10 60 C10 29 34 6 64 6 Z', '#1e4d50', sw=3)
        s.e(62, 42, 29, 28, '#e7b665', sw=0, shade=False)
        s.shape('M15 78 Q43 70 65 77 Q91 68 114 77 L109 95 Q91 111 64 119 Q37 111 19 95 Z', '#5caaa3', sw=0)
        s.poly([(22,75),(28,54),(31,75)], '#347b70', sw=0)
    elif anim == 'pond':
        s.e(62, 92, 49, 25, '#79bbb2', sw=0)
        s.arc(63, 61, 52, 191, 448, '#e1b16e', 3)
        s.curve('M20 88 Q17 74 20 62 M22 84 Q28 74 27 67', '#347b70', 2, sw=0)
    else:
        s.e(64, 64, 57, 57, '#203c42', sw=2.5)
        s.arc(64, 64, 49, 192, 444, '#d4a968', 2)
    boundary = ('<ellipse cx="62" cy="92" rx="49" ry="25"/>' if anim == 'pond'
                else '<circle cx="64" cy="64" r="56"/>' if anim == 'seal'
                else '<path d="M64 6 C94 6 118 29 118 60 C118 94 94 116 64 123 C34 116 10 94 10 60 C10 29 34 6 64 6 Z"/>')
    s.defs.append(f'<clipPath id="water-boundary">{boundary}</clipPath>')
    s.defs.append('<clipPath id="reflection"><path d="M18 92H111V123H18Z"/></clipPath>')
    s.raw('<g clip-path="url(#water-boundary)"><g clip-path="url(#reflection)" opacity="0.34"><g transform="translate(0 128.8) scale(1 -.4)">')
    bird(s, anim == 'seal')
    s.raw('</g></g></g>')
    bird(s, anim == 'seal')
    water = '#d6efe0' if anim != 'seal' else '#82b4ab'
    for d in ['M39 91 Q61 94 83 90', 'M46 99 Q60 97 78 99', 'M42 107 Q58 110 74 107', 'M52 115 H66']:
        s.curve(d, water, 1.3, sw=0)
