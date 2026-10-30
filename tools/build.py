"""Builds the game for the web: one page with the pictures inside, plus the voice and the 3D props beside it.

    python tools/build.py       writes out/web/index.html (the page body, for the claude.ai artifact),
                                out/web/play.html (the same as a whole document), out/web/voice.mp3, out/web/props3d.json

The page fetches voice.mp3 and props3d.json by relative URL, so open it from a web server (or the artifact), not file://.
The floor and wall art is forge-godot's dungeon terrain, copied into game/art/terrain.
"""
import base64, json, os, shutil

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
GAME = os.path.join(ROOT, 'game')
OUT = os.path.join(ROOT, 'out', 'web')
TERRAIN = os.path.join(GAME, 'art', 'terrain', 'environment-terrain-dungeon-%s.webp')   # copied from forge-godot's assets/terrain


def data_url(path, mime):
    return 'data:%s;base64,%s' % (mime, base64.b64encode(open(path, 'rb').read()).decode())


def main():
    art = json.load(open(os.path.join(GAME, 'art.json')))
    for c in art['chars'].values():
        c['src'] = data_url(os.path.join(GAME, 'art', c.pop('file')), 'image/png')
    for k in ('props', 'narrator'):
        art[k]['src'] = data_url(os.path.join(GAME, 'art', art[k].pop('file')), 'image/png')
    art['terrain'] = {k: data_url(TERRAIN % k, 'image/webp') for k in ('floor', 'top', 'face')}
    voice = json.load(open(os.path.join(GAME, 'voice.json')))
    src = open(os.path.join(GAME, os.environ.get('SRC', 'src.html')), encoding='utf-8').read()
    page = src.replace('/*ART*/{}', json.dumps(art, separators=(',', ':'))).replace('/*VOICE*/{}', json.dumps(voice, separators=(',', ':')))
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(page)
    doc = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
           '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"></head><body>' + page + '</body></html>')
    open(os.path.join(OUT, 'play.html'), 'w', encoding='utf-8').write(doc)
    shutil.copy(os.path.join(GAME, 'voice.bin'), os.path.join(OUT, 'voice.mp3'))   # the clips end to end are one valid mp3 stream
    pack = {f[:-4]: base64.b64encode(open(os.path.join(GAME, 'props3d', f), 'rb').read()).decode()
            for f in sorted(os.listdir(os.path.join(GAME, 'props3d'))) if f.endswith('.glb')}
    json.dump(pack, open(os.path.join(OUT, 'props3d.json'), 'w'))   # artifacts do not serve .glb, so they travel as base64 JSON
    size = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(OUT) for f in fs)
    print('out/web/index.html', len(page) // 1024, 'KB; everything', size // 1024, 'KB')


if __name__ == '__main__':
    main()
