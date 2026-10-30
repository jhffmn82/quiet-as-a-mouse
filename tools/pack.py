"""Packs art/raw into the game's sheets: one per character, one for the props, one for the narrator's face.

    python tools/pack.py        writes game/art/*.png and game/art.json

Characters: a row per animation and direction (south, south-east, east, north-east, north), a 64px frame per column;
foot is how many pixels sit below the lowest drawn one, so the card can stand on its feet.
The narrator: a row per mood, a column per mouth shape in /lip-sync's order, and the sleeping face on a row of its own.
"""
import json, os, sys
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from art import CHARS, CHARS_PRO, DIRS, PROPS, MOODS, RAW, ROOT

OUT = os.path.join(ROOT, 'game', 'art')
SKELETON = {'mouse': {'walking-6-frames': 'sk-walk', 'crouched-walking': 'sk-sneak', 'running-6-frames': 'sk-run'}}
LIP_ORDER = ['rest', 'closed', 'small_open', 'medium_open', 'wide_open', 'round', 'teeth']


def frames(name, anim, d):
    if anim == 'rot':   # a still pose, for a character whose animations have not come back yet
        p = os.path.join(RAW, name, 'rot', d + '.png')
        return [Image.open(p).convert('RGBA')] if os.path.exists(p) else []
    folder = os.path.join(RAW, name, anim, d)
    if not os.path.isdir(folder):
        return []
    return [Image.open(os.path.join(folder, f)).convert('RGBA') for f in sorted(os.listdir(folder)) if f.endswith('.png')]


def chars():
    meta = {}
    for name, (_, anims) in {**CHARS, **CHARS_PRO}.items():
        # the skeleton-mode re-animations (tools/anim2.py), where they exist, stand in for the template ones
        anims = [SKELETON.get(name, {}).get(x, x) if all(frames(name, SKELETON.get(name, {}).get(x, x), d) for d in DIRS) else x for x in anims]
        have = [a for a in anims if all(frames(name, a, d) for d in DIRS)] or ['rot']
        if not all(frames(name, have[0], d) for d in DIRS):
            print(name, 'has no finished animations yet'); continue
        if name in CHARS_PRO and have == ['rot']:
            print(name, 'still animating; the game uses the old sheet'); continue
        grid = {a: [frames(name, a, d) for d in DIRS] for a in have}
        fw = max(f.width for a in have for row in grid[a] for f in row)
        fh = max(f.height for a in have for row in grid[a] for f in row)
        cols = max(len(row) for a in have for row in grid[a])
        sheet = Image.new('RGBA', (fw * cols, fh * len(have) * len(DIRS)))
        bottom = 0
        for ai, a in enumerate(have):
            for di, row in enumerate(grid[a]):
                for fi, f in enumerate(row):
                    x, y = fi * fw + (fw - f.width) // 2, (ai * len(DIRS) + di) * fh + (fh - f.height)
                    sheet.alpha_composite(f, (x, y))
                    bb = f.getbbox()
                    if bb:
                        bottom = max(bottom, bb[3] + (fh - f.height))
        sheet.save(os.path.join(OUT, name + '.png'))
        # each animation and direction stands on its own lowest pixel (template animations sit higher in the canvas)
        feet = {a: [fh - max((f.getbbox() or (0, 0, 0, fh))[3] + (fh - f.height) for f in grid[a][di]) for di in range(len(DIRS))] for a in have}
        # skeleton mode draws her about a tenth bigger than template mode did, so each skeleton animation is shown shrunk
        # until she stands as tall as in the template version of the same move
        tall = lambda fs: sorted(f.getbbox()[3] - f.getbbox()[1] for f in fs)[len(fs) // 2]
        scale = {sk: round(sorted(tall(frames(name, t, d)) / tall(grid[sk][di]) for di, d in enumerate(DIRS))[len(DIRS) // 2], 3)
                 for t, sk in SKELETON.get(name, {}).items() if sk in have and all(frames(name, t, d) for d in DIRS)}
        meta[name] = {'file': name + '.png', 'fw': fw, 'fh': fh, 'W': sheet.width, 'H': sheet.height, 'foot': fh - bottom, 'feet': feet,
                      'scale': scale, 'anims': {a: {'row': i * len(DIRS), 'n': len(grid[a][0])} for i, a in enumerate(have)}}
        print(name, have, sheet.size, 'foot', fh - bottom, 'scale', scale)
    return meta


def props():
    ims = {n: Image.open(os.path.join(RAW, 'props', n + '.png')).convert('RGBA') for n in PROPS
           if os.path.exists(os.path.join(RAW, 'props', n + '.png'))}
    W = sum(i.width + 2 for i in ims.values()); H = max(i.height for i in ims.values())
    sheet, x, rects = Image.new('RGBA', (W, H)), 0, {}
    for n, im in ims.items():
        sheet.alpha_composite(im, (x, 0))
        bb = im.getbbox()
        rects[n] = {'x': x, 'y': 0, 'w': im.width, 'h': im.height, 'foot': im.height - bb[3] if bb else 0}
        x += im.width + 2
    sheet.save(os.path.join(OUT, 'props.png'))
    print('props', list(rects), sheet.size, 'missing', [n for n in PROPS if n not in rects])
    return {'file': 'props.png', 'W': W, 'H': H, 'rects': rects}


def narrator():
    cell = 96
    rows = {}
    sheet = Image.new('RGBA', (cell * len(LIP_ORDER), cell * (len(MOODS) + 1)))
    have = [m for m in MOODS if os.path.exists(os.path.join(RAW, 'narrator', m, 'visemes.json'))]
    for r, mood in enumerate(MOODS):
        src = mood if mood in have else (have[0] if have else None)
        for c, v in enumerate(LIP_ORDER):
            p = os.path.join(RAW, 'narrator', src, v + '.png') if src else os.path.join(RAW, 'narrator', 'face.png')
            if not os.path.exists(p):
                p = os.path.join(RAW, 'narrator', 'face.png')
            sheet.alpha_composite(Image.open(p).convert('RGBA').resize((cell, cell), Image.NEAREST), (c * cell, r * cell))
        rows[mood] = r
    sheet.alpha_composite(Image.open(os.path.join(RAW, 'narrator', 'asleep.png')).convert('RGBA').resize((cell, cell), Image.NEAREST),
                          (0, len(MOODS) * cell))
    sheet.save(os.path.join(OUT, 'narrator.png'))
    print('narrator moods', have, 'of', MOODS)
    return {'file': 'narrator.png', 'cell': cell, 'rows': rows, 'rest': LIP_ORDER.index('rest'),
            'asleep': {'x': 0, 'y': len(MOODS) * cell}}


def main():
    os.makedirs(OUT, exist_ok=True)
    meta = {'chars': chars(), 'props': props(), 'narrator': narrator()}
    json.dump(meta, open(os.path.join(ROOT, 'game', 'art.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
