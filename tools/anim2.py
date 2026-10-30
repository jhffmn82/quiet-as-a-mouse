"""Re-animates a character with PixelLab's skeleton-v3 mode, which poses the same drawing frame to frame instead of
redrawing it (steadier, clearer legs): python tools/anim2.py <char> <template> <name> [<template> <name> ...] [--dirs north-east,...]

Frames land in art/raw/<char>/<name>/<direction>/NN.png, beside the template-mode ones; tools/pack.py picks the
animation names it is told to use. Receipts go in art/raw/state.json under the character, so a rerun never pays twice.
"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pl
from art import RAW, STATE, DIRS, get, put, load, save


def animate(state, char, template, name, dirs=DIRS):
    st = state['chars'][char]; cid = st['id']
    a = st.setdefault('anims', {}).setdefault(name, {})
    if 'group' not in a:
        r = pl.call('POST', '/characters/animations', {'character_id': cid, 'template_animation_id': template, 'mode': 'skeleton-v3',
                                                       'directions': dirs, 'animation_name': name})
        a['group'], a['jobs'] = r.get('animation_group_id'), r.get('background_job_ids', [])
        save(state)
    used = 0
    for j in a['jobs']:
        used += ((pl.wait(j).get('usage') or {}).get('generations') or 0)
    a['gens'] = used; save(state)
    frames = {}
    for _ in range(40):
        c = pl.call('GET', '/characters/%s' % cid)
        for an in c.get('animations', []):
            if an.get('animation_group_id') == a['group']:
                for dd in an.get('directions', []):
                    frames[dd.get('direction')] = dd.get('frames', [])
        if all(frames.get(d) for d in dirs):
            break
        time.sleep(10)
    for d in dirs:
        for i, url in enumerate(frames.get(d) or []):
            p = os.path.join(RAW, char, name, d, '%02d.png' % i)
            if not os.path.exists(p):
                put(p, get(url))
    print(char, name, {d: len(frames.get(d) or []) for d in dirs}, 'gens', used, flush=True)


if __name__ == '__main__':
    char, rest = sys.argv[1], sys.argv[2:]
    dirs = DIRS   # redraw only some directions, e.g. one that came back garbled
    if '--dirs' in rest:
        i = rest.index('--dirs'); dirs = rest[i + 1].split(','); rest = rest[:i] + rest[i + 2:]
    state = load(); pl.balance()
    for template, name in zip(rest[::2], rest[1::2]):
        animate(state, char, template, name, dirs)
    pl.balance()
