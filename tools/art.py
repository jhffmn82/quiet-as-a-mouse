"""Every picture in The Loud Narrator, from PixelLab: the thief, the guards, the props, and the narrator's talking face.

    python tools/art.py            make whatever is missing (resumable; art/raw/state.json keeps the ids)
    python tools/art.py --plan     what would be made, and nothing else

Characters are made once with 8 rotations, then animated from PixelLab's templates facing five ways (south round to
north through east); the game mirrors the east side for the west. Raw downloads land in art/raw/; tools/pack.py turns
them into the game's sheets.
"""
import base64, concurrent.futures, json, os, sys, threading, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pl

ROOT = pl.ROOT
RAW = os.path.join(ROOT, 'art', 'raw')
STATE = os.path.join(RAW, 'state.json')
STYLE = 'stylized chunky chibi pixel art, huge head, tiny body, thick black outline, bold flat saturated colors'
DIRS = ['south', 'south-east', 'east', 'north-east', 'north']

CHARS = {
    'mouse': ('tiny chibi thief girl in an oversized plum purple hooded cloak with two round mouse ears on the hood, '
              'face hidden in the hood shadow except two big glowing yellow eyes, striped red and cream socks, '
              'a big lumpy burlap loot sack slung on her back, ' + STYLE,
              ['crouched-walking', 'walking-6-frames', 'running-6-frames', 'breathing-idle']),
    'gord': ('huge round chibi dungeon guard shaped like a barrel, enormous belly in rusty chainmail, tiny head in a '
             'dented iron bucket helmet with a narrow eye slit, short stubby legs, red tabard, holding a glowing brass '
             'lantern, ' + STYLE,
             ['walking-6-frames', 'breathing-idle']),
    'stilts': ('extremely tall skinny chibi dungeon guard with noodle-thin arms and legs, a tall pointy iron helmet, '
               'an enormous droopy black mustache, red tabard, holding a long spear upright, hunched and nervous, ' + STYLE,
               ['walking-6-frames', 'breathing-idle']),
}

# the guards, redrawn in Mouse's own style: create-character-pro with her character as the style reference
CHARS_PRO = {
    'gord2': ('big round chubby dungeon guard with a huge dopey friendly face, rosy cheeks, a bushy ginger beard, a small dented '
              'iron kettle helmet, a chainmail shirt stretched over a big round belly, a red tabard, a ring of keys on his belt, '
              'holding a glowing brass lantern', ['walking-6-frames', 'breathing-idle']),
    'stilts2': ('very tall skinny nervous dungeon guard with a long neck, huge worried eyes, a droopy black mustache, a tall pointy '
                'iron helmet, a red tabard over chainmail, knobbly knees, holding a long spear upright', ['walking-6-frames', 'breathing-idle']),
}
PRO_STYLE = 'the same chibi style as the reference: huge head, small body, soft shading, thick dark outline, bold flat colors'

PROPS = {   # name: (description, width, height)
    'idol': ('a small golden idol statue of a chubby little figure pressing one finger to its lips, shushing, '
             'standing on a short carved stone pedestal, glowing softly', 48, 64),
    'bucket': ('a plain dented grey metal bucket, completely ordinary and boring', 32, 32),
    'cabinet': ('a beige office filing cabinet with three drawers, completely ordinary and boring', 32, 48),
    'rocks': ('a small neat pile of identical round grey rocks, completely ordinary and boring', 32, 32),
    'stool': ('a plain wooden three-legged stool', 32, 32),
    'plant': ('a dead brown houseplant in a clay pot with one sad drooping leaf', 32, 40),
    'crate': ('a sturdy wooden crate with iron corners', 32, 32),
    'barrel': ('an old wooden barrel with iron bands', 32, 40),
    'shelf': ('a tall wooden bookshelf crammed with identical beige books', 48, 64),
    'rack': ('a wooden weapon rack holding three spears and a shield', 48, 48),
    'table': ('a rough wooden table with playing cards and a half-eaten sandwich on it', 48, 40),
    'sconce': ('a wall-mounted iron torch sconce with a bright orange flame', 32, 48),
    'door': ('a big arched wooden dungeon door with iron bands, slightly open with warm daylight shining through', 48, 64),
    'plaque': ('a small dull bronze plaque with tiny unreadable engraved text', 32, 32),
}

NARRATOR = ('bust portrait of a pompous theatrical old storyteller with a gigantic curled white mustache that leaves his '
            'mouth clearly visible, a gold monocle, bushy white eyebrows, a burgundy velvet smoking jacket and a cravat, '
            'facing the viewer, ' + STYLE)
MOODS = ['neutral', 'sad', 'happy', 'surprised']   # bored, chatty, thrilled, unhinged

lock = threading.Lock()
slots = threading.Semaphore(9)   # PixelLab runs 10 background jobs at once on this tier; more is a 429
grab = threading.Lock()


def load():
    return json.load(open(STATE)) if os.path.exists(STATE) else {}


def save(state):
    with lock:
        os.makedirs(RAW, exist_ok=True)
        json.dump(state, open(STATE, 'w'), indent=1)


def get(url):
    import urllib.request
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (loud-narrator)'})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def put(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'wb').write(data)


def b64png(path):
    return {'type': 'base64', 'base64': base64.b64encode(open(path, 'rb').read()).decode(), 'format': 'png'}


def run_jobs(ids):
    """Waits for background jobs, holding one slot each until it ends."""
    used = 0
    for jid in ids:
        j = pl.wait(jid)
        used += ((j.get('usage') or {}).get('generations') or 0)
    return used


def character(state, name):
    desc, anims = {**CHARS, **CHARS_PRO}[name]
    st = state.setdefault('chars', {}).setdefault(name, {})
    out = os.path.join(RAW, name)
    if 'id' not in st and name in CHARS_PRO:
        slots.acquire()
        try:
            r = pl.call('POST', '/create-character-pro', {
                'description': desc, 'image_size': {'width': 64, 'height': 64}, 'method': 'create_with_style',
                'view': 'low top-down', 'style_character_id': state['chars']['mouse']['id'], 'style_description': PRO_STYLE,
                'no_background': True})
            st['id'], st['job'] = r['character_id'], r.get('background_job_id')
            save(state)
            if st['job']:
                st['create_gens'] = run_jobs([st['job']])
        finally:
            slots.release()
        save(state)
    if 'id' not in st:
        slots.acquire()
        try:
            r = pl.call('POST', '/create-character-v3', {
                'description': desc, 'name': 'loud-narrator ' + name, 'image_size': {'width': 64, 'height': 64},
                'view': 'low top-down', 'outline': 'single color black outline', 'detail': 'medium detail',
                'no_background': True})
            st['id'], st['job'] = r['character_id'], r.get('background_job_id')
            save(state)
            if st['job']:
                st['create_gens'] = run_jobs([st['job']])
        finally:
            slots.release()
        save(state)
    cid = st['id']
    for _ in range(60):
        c = pl.call('GET', '/characters/%s' % cid)
        if c.get('status') == 'completed':
            break
        time.sleep(10)
    for d, url in (c.get('rotation_urls') or {}).items():
        p = os.path.join(out, 'rot', d + '.png')
        if url and not os.path.exists(p):
            put(p, get(url))
    print(name, 'rotations saved', flush=True)
    for tmpl in anims:
        a = st.setdefault('anims', {}).setdefault(tmpl, {})
        if 'group' not in a:
            with grab:   # one thread gathers several slots at a time, or two could each hold half and wait forever
                for _ in range(5):
                    slots.acquire()
            try:
                r = pl.call('POST', '/characters/animations', {
                    'character_id': cid, 'template_animation_id': tmpl, 'mode': 'template', 'directions': DIRS,
                    'animation_name': tmpl})
                a['group'], a['jobs'] = r.get('animation_group_id'), r.get('background_job_ids', [])
                save(state)
                a['gens'] = run_jobs(a['jobs'])
            finally:
                for _ in range(5):
                    slots.release()
            save(state)
        frames = {}
        for _ in range(30):
            c = pl.call('GET', '/characters/%s' % cid)
            for an in c.get('animations', []):
                if an.get('animation_group_id') == a['group']:
                    for dd in an.get('directions', []):
                        frames[dd.get('direction')] = dd.get('frames', [])
            if all(frames.get(d) for d in DIRS):
                break
            time.sleep(10)
        for d in DIRS:
            for i, url in enumerate(frames.get(d) or []):
                p = os.path.join(out, tmpl, d, '%02d.png' % i)
                if not os.path.exists(p):
                    put(p, get(url))
        print(name, tmpl, {d: len(frames.get(d) or []) for d in DIRS}, 'gens', a.get('gens'), flush=True)


def images(node, found):
    if isinstance(node, dict):
        if isinstance(node.get('base64'), str) and len(node['base64']) > 100:
            found.append(base64.b64decode(node['base64'].split(',', 1)[-1]))
            return
        for v in node.values():
            images(v, found)
    elif isinstance(node, list):
        for v in node:
            images(v, found)
    elif isinstance(node, str) and node.startswith('http') and '.png' in node:
        found.append(get(node))


def pixen(state, key, body, path, endpoint='/create-image-pixen'):
    if os.path.exists(path):
        return
    st = state.setdefault('images', {}).setdefault(key, {})
    slots.acquire()
    try:
        if 'job' not in st:
            r = pl.call('POST', endpoint, body)
            st['job'] = r.get('background_job_id')
            st['inline'] = None if st['job'] else r
            save(state)
        result = st['inline']
        if st['job']:
            j = pl.wait(st['job'])
            st['gens'] = (j.get('usage') or {}).get('generations')
            result = j.get('last_response') or j
    finally:
        slots.release()
    found = []
    images(result, found)
    if not found:
        raise SystemExit('%s: no image came back: %s' % (key, json.dumps(result)[:400]))
    put(path, found[0])
    save(state)
    print('image', key, 'gens', st.get('gens'), flush=True)


def prop(state, name):
    desc, w, h = PROPS[name]
    pixen(state, 'prop_' + name, {'description': desc + ', ' + STYLE + ', game prop sprite',
                                  'image_size': {'width': w, 'height': h}, 'no_background': True,
                                  'outline': 'single color black outline', 'detail': 'medium detail',
                                  'view': 'low top-down'}, os.path.join(RAW, 'props', name + '.png'))


def narrator(state):
    face = os.path.join(RAW, 'narrator', 'face.png')
    pixen(state, 'narrator', {'description': NARRATOR, 'image_size': {'width': 96, 'height': 96}, 'no_background': True,
                              'outline': 'single color black outline', 'detail': 'medium detail'}, face)
    pixen(state, 'narrator_asleep', {'image': b64png(face), 'no_background': True,
                                     'description': 'the same pompous old storyteller fast asleep: eyes shut, head drooping '
                                                    'to one side, mouth hanging open, same colors and pixels otherwise'},
          os.path.join(RAW, 'narrator', 'asleep.png'), endpoint='/edit-image-pixen')
    st = state.setdefault('visemes', {})
    for mood in MOODS:
        d = os.path.join(RAW, 'narrator', mood)
        if os.path.exists(os.path.join(d, 'visemes.json')):
            continue
        slots.acquire()
        try:
            if mood not in st:
                r = pl.call('POST', '/vocal-animation', {'portrait': b64png(face), 'mood': mood, 'viseme_count': 7,
                                                         'no_background': True, 'seed': 7})
                st[mood] = r.get('background_job_id') or r.get('job_id')
                save(state)
            while True:
                j = pl.call('GET', '/vocal-animation/%s' % st[mood])
                if j.get('status') == 'completed':
                    break
                if j.get('status') == 'failed':
                    raise SystemExit('visemes %s failed: %s' % (mood, json.dumps(j)[:400]))
                time.sleep(12)
        finally:
            slots.release()
        vis = j.get('visemes') or {}
        os.makedirs(d, exist_ok=True)
        order = []
        for vid, v in vis.items():
            found = []
            images(v, found)
            if found:
                put(os.path.join(d, vid + '.png'), found[0])
                order.append(vid)
        json.dump({'usage': j.get('usage'), 'order': order, 'viseme_order': j.get('viseme_order'),
                   'meta': {k: v for k, v in vis.items() if not isinstance(v, (dict, list))} if isinstance(vis, dict) else None},
                  open(os.path.join(d, 'visemes.json'), 'w'), indent=1)
        print('visemes', mood, order, j.get('usage'), flush=True)


def main():
    if '--plan' in sys.argv:
        print('characters:', {n: a for n, (_, a) in CHARS.items()})
        print('props:', list(PROPS))
        print('narrator moods:', MOODS)
        return
    state = load()
    pl.balance()
    with concurrent.futures.ThreadPoolExecutor(12) as pool:
        only = [a for a in sys.argv[1:] if not a.startswith('-')]
        if only:
            futs = [pool.submit(character, state, n) for n in only]
        else:
            futs = [pool.submit(character, state, n) for n in CHARS]
            futs += [pool.submit(narrator, state)]
            futs += [pool.submit(prop, state, n) for n in PROPS]
        for f in futs:
            try:
                f.result()
            except BaseException as e:
                print('FAILED:', repr(e), flush=True)
    pl.balance()


if __name__ == '__main__':
    main()
