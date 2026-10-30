"""Every voice in The Loud Narrator, from ElevenLabs (eleven_v3), packed for the game.

    python tools/audio.py            voice whatever is missing, then write game/voice.bin and game/voice.json
    python tools/audio.py --list     the lines, their tiers and the character count, and nothing else

The lines live in tools/lines.py. The key is Shoulda Listened's (.secrets/elevenlabs-api-key.txt there) unless this
project has its own, or ELEVENLABS_API_KEY. Each take is cached in art/audio/cache under a hash of its request, so a run
only pays for what changed. The narrator's mouth is worked out in the game from each decoded clip, so it keeps time.
voice.bin is every clip's mp3 end to end; voice.json gives each clip's byte range, length, loudness gain, text and tier.
Needs numpy and lameenc.
"""
import concurrent.futures, hashlib, json, os, re, sys, time, urllib.error, urllib.request
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lines import LINES

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / 'art' / 'audio' / 'cache'
OUT = ROOT / 'game'
API = 'https://api.elevenlabs.io/v1'
RATE = 22050
VOICES = {'George': 'JBFqnCBsd6RMkjVDRZzb', 'Callum': 'N2lVS1w4EtoT3dr4eOWO', 'Will': 'bIHbv24MWmeRgasZH58o', 'Brian': 'nPczCjzI2devNBz1zQrb', 'Charlie': 'IKne3meq5aSn9XLyUdCD'}
STABILITY = {0: .5, 1: .5, 2: .3, 3: 0.0}
# the world's own sounds: name: (takes, prompt, seconds). They come back as stereo PCM at 44.1 kHz whatever is asked.
SFX = {
    'fx_step': (3, 'a single soft footstep of a small leather boot on a stone dungeon floor, close and quiet', .5),
    'fx_run': (2, 'a single quick hurried footstep slapping on a stone floor', .5),
    'fx_keys': (1, 'a small ring of iron keys jingling briefly as it is lifted off a belt', .9),
    'fx_lock': (1, 'an old iron lock turning with a heavy key, two clicks, then a wooden door creaking open', 1.8),
    'fx_lever': (1, 'a heavy iron lever pulled down with a clunk, then distant chains rattling and a portcullis grinding upward', 2.6),
    'fx_idol': (1, 'a soft magical golden shimmer with a gentle choir hum as a sacred treasure is lifted', 1.6),
    'fx_alert': (1, 'a short sharp tense orchestral sting, strings and a low drum hit, an intruder is spotted', 1.1),
    'fx_caught': (1, 'a heavy iron dungeon cell door slamming shut with a deep clang and echo', 1.4),
    'fx_win': (1, 'a gentle triumphant flourish of harp and warm strings, a quiet heist completed', 2.6),
    'fx_rattle': (1, 'an old iron door handle rattling against a locked latch', .8),
    'fx_rope': (1, 'a thick rope creaking and swaying as someone climbs it quickly', 1.4),
}   # v3 wants 0 (creative) to really shout; whispers stay steady
VOICE_DB = -15.0   # the median speech loudness; each clip gets the gain that puts it here before the tier's own volume


def key():
    k = os.environ.get('ELEVENLABS_API_KEY')
    for p in (ROOT / '.secrets' / 'elevenlabs-api-key.txt', ROOT.parent / 'shoulda-listened' / '.secrets' / 'elevenlabs-api-key.txt'):
        if not k and p.exists():
            k = p.read_text().strip()
    if not k:
        sys.exit('No ElevenLabs key')
    return k


def spoken(text):
    return re.sub(r'\s+', ' ', re.sub(r'\[[^\]]*\]', '', text)).strip()


def tts(voice, tier, text):
    body = {'text': text, 'model_id': 'eleven_v3', 'voice_settings': {'stability': STABILITY[tier], 'similarity_boost': .8}}
    path = f'/text-to-speech/{VOICES[voice]}'
    h = hashlib.sha1(json.dumps([path, body], sort_keys=True).encode()).hexdigest()[:16]
    f = CACHE / f'{h}.pcm'
    if f.exists():
        return f.read_bytes()
    req = urllib.request.Request(f'{API}{path}?output_format=pcm_{RATE}', data=json.dumps(body).encode(),
                                 headers={'xi-api-key': key(), 'Content-Type': 'application/json', 'User-Agent': 'loud-narrator'})
    for attempt in range(5):
        try:
            data = urllib.request.urlopen(req, timeout=300).read()
            break
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors='replace')[:400]
            if e.code in (429, 500, 502, 503) and attempt < 4:
                time.sleep(8 * (attempt + 1))
                continue
            raise SystemExit(f'ElevenLabs {e.code} on "{text[:40]}": {msg}')
    CACHE.mkdir(parents=True, exist_ok=True)
    f.write_bytes(data)
    with open(CACHE.parent / 'calls.jsonl', 'a', encoding='utf-8') as log:
        log.write(json.dumps({'t': time.strftime('%Y-%m-%d %H:%M:%S'), 'voice': voice, 'text': text, 'bytes': len(data)}) + '\n')
    return data


def speech_db(x):
    import numpy as np
    n = int(RATE * .05)
    rms = np.sqrt((x[:len(x) // n * n].reshape(-1, n) ** 2).mean(axis=1))
    act = rms[rms > rms.max() * .1]
    return float(20 * np.log10(np.sqrt((act ** 2).mean()) or 1e-9))


def encode(pcm):
    import numpy as np, lameenc
    x = np.frombuffer(pcm, '<i2').astype(np.float64) / 32768
    loud = np.flatnonzero(np.abs(x) > .01)
    if len(loud):
        x = x[max(0, loud[0] - int(RATE * .01)):loud[-1] + int(RATE * .08)]
    x = x / (np.max(np.abs(x)) or 1) * .9
    fade = int(RATE * .004)
    if len(x) > 2 * fade:
        x[:fade] *= np.linspace(0, 1, fade)
        x[-fade:] *= np.linspace(1, 0, fade)
    e = lameenc.Encoder()
    e.set_bit_rate(48); e.set_in_sample_rate(RATE); e.set_channels(1); e.set_quality(2)
    data = bytes(e.encode((np.clip(x, -1, 1) * 32767).astype('<i2').tobytes()) + e.flush())
    return data, len(x) / RATE, speech_db(x)


def sfx(prompt, secs, seed):
    body = {'text': prompt, 'duration_seconds': secs, 'prompt_influence': .55, 'model_id': 'eleven_text_to_sound_v2', 'seed': seed}
    h = hashlib.sha1(json.dumps(['/sound-generation', body], sort_keys=True).encode()).hexdigest()[:16]
    f = CACHE / f'sfx-{h}.pcm'
    if f.exists():
        return f.read_bytes()
    req = urllib.request.Request(f'{API}/sound-generation?output_format=pcm_44100', data=json.dumps(body).encode(),
                                 headers={'xi-api-key': key(), 'Content-Type': 'application/json', 'User-Agent': 'loud-narrator'})
    for attempt in range(5):
        try:
            data = urllib.request.urlopen(req, timeout=300).read(); break
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors='replace')[:300]
            if e.code in (429, 500, 502, 503) and attempt < 4:
                time.sleep(8 * (attempt + 1)); continue
            raise SystemExit(f'ElevenLabs {e.code} on sfx "{prompt[:40]}": {msg}')
    CACHE.mkdir(parents=True, exist_ok=True); f.write_bytes(data)
    return data


def encode_sfx(pcm):
    import numpy as np, lameenc
    x = np.frombuffer(pcm, '<i2').astype(np.float64) / 32768
    x = x[:len(x) // 2 * 2].reshape(-1, 2).mean(axis=1)   # interleaved stereo to mono
    loud = np.flatnonzero(np.abs(x) > .01)
    if len(loud):
        x = x[max(0, loud[0] - 200):loud[-1] + 2000]
    x = x / (np.max(np.abs(x)) or 1) * .85
    fade = min(len(x) // 4, 400)
    if fade:
        x[-fade:] *= np.linspace(1, 0, fade)
    e = lameenc.Encoder(); e.set_bit_rate(64); e.set_in_sample_rate(44100); e.set_channels(1); e.set_quality(2)
    return bytes(e.encode((np.clip(x, -1, 1) * 32767).astype('<i2').tobytes()) + e.flush()), len(x) / 44100


def clips():
    out = []
    for group, (voice, tier, texts) in LINES.items():
        for i, text in enumerate(texts):
            out.append((f'{group}_{i + 1}', group, voice, tier, text))
    return out


def main():
    todo = clips()
    if '--list' in sys.argv:
        for name, group, voice, tier, text in todo:
            print(f'{tier} {voice:6} {name:14} {text[:80]}')
        print(len(todo), 'clips,', sum(len(t) for *_, t in todo), 'characters')
        return

    def run(job):
        name, group, voice, tier, text = job
        data, secs, db = encode(tts(voice, tier, text))
        return name, group, voice, tier, text, data, secs, db

    blob, manifest = bytearray(), {}
    for name, (takes, prompt, secs) in SFX.items():
        for i in range(takes):
            data, dur = encode_sfx(sfx(prompt, secs, 2000 + i))
            manifest[f'{name}_{i + 1}'] = {'o': len(blob), 'n': len(data), 'secs': round(dur, 2), 'tier': 0, 'voice': 'fx', 'gain': 1, 'text': ''}
            blob += data
    print(sum(t for t, _, _ in SFX.values()), 'sound effects')
    with concurrent.futures.ThreadPoolExecutor(4) as pool:
        for name, group, voice, tier, text, data, secs, db in pool.map(run, todo):
            m = {'o': len(blob), 'n': len(data), 'secs': round(secs, 2), 'tier': tier, 'voice': voice,
                 'gain': round(min(2, max(.5, 10 ** ((VOICE_DB - db) / 20))), 3), 'text': spoken(text)}
            manifest[name] = m
            blob += data
            print(f'{tier} {name:14} {secs:5.1f} s {db:6.1f} dB', flush=True)
    (OUT / 'voice.bin').write_bytes(bytes(blob))
    (OUT / 'voice.json').write_text(json.dumps(manifest, separators=(',', ':')))
    print(len(todo), 'clips,', len(blob) // 1024, 'KB,', round(sum(m['secs'] for k, m in manifest.items() if k[0] != '_')), 's of talk')


if __name__ == '__main__':
    main()
