"""Copies forge-godot's 3D props into the game, with their textures shrunk for the web.

    python tools/props3d.py      writes game/props3d/<name>.glb

Each forge prop is one Tripo mesh with one baked colour texture (a ~1 MB JPEG); at 512 px it is ~60 KB and looks
the same from the game's camera.
"""
import io, json, os, struct
from PIL import Image

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
SRC = os.path.join(ROOT, '..', 'forge-godot', 'assets', 'props3d')
OUT = os.path.join(ROOT, 'game', 'props3d')
NAMES = ['crate', 'crate-supply', 'barrel', 'sacks', 'bookshelf', 'weapon-rack', 'long-table', 'chair', 'desk',
         'lever-up', 'lever-down', 'torch-stand', 'wall-plaque', 'urn-group', 'pedestal', 'pillar', 'statue']


def shrink(name, size=512):
    b = open(os.path.join(SRC, name + '.glb'), 'rb').read()
    n = struct.unpack('<I', b[12:16])[0]
    j = json.loads(b[20:20 + n])
    bin_at = 20 + n
    bn = struct.unpack('<I', b[bin_at:bin_at + 4])[0]
    blob = b[bin_at + 8:bin_at + 8 + bn]
    views = [bytes(blob[v.get('byteOffset', 0):v.get('byteOffset', 0) + v['byteLength']]) for v in j['bufferViews']]
    for img in j.get('images', []):
        im = Image.open(io.BytesIO(views[img['bufferView']])).convert('RGB')
        im.thumbnail((size, size), Image.LANCZOS)
        out = io.BytesIO(); im.save(out, 'JPEG', quality=84)
        views[img['bufferView']] = out.getvalue(); img['mimeType'] = 'image/jpeg'
    new = bytearray()
    for v, data in zip(j['bufferViews'], views):
        while len(new) % 4: new.append(0)
        v['byteOffset'] = len(new); v['byteLength'] = len(data); v['buffer'] = 0
        new += data
    while len(new) % 4: new.append(0)
    j['buffers'] = [{'byteLength': len(new)}]
    js = json.dumps(j, separators=(',', ':')).encode()
    js += b' ' * ((4 - len(js) % 4) % 4)
    glb = struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(new)) + struct.pack('<II', len(js), 0x4E4F534A) + js \
        + struct.pack('<II', len(new), 0x004E4942) + bytes(new)
    open(os.path.join(OUT, name + '.glb'), 'wb').write(glb)
    return len(b), len(glb)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    total = 0
    for nm in NAMES:
        a, z = shrink(nm)
        total += z
        print('%-14s %5d KB -> %4d KB' % (nm, a // 1024, z // 1024))
    print('total', total // 1024, 'KB')
