# Quiet as a Mouse

One 3D stealth level with 2D pixel-art characters. Mouse, a tiny hooded thief, has to steal the Idol of Silence from the
Vaults of Hush. The start screen plays it straight. The joke is buried until Percival, her narrator, clears his throat,
and the guard in the next room hears him through the bars.

Play it: https://claude.ai/artifact/JoaabeSZuRKP7Fz2NFTNgw (private until shared).

## The way in, one rule to a room

1. **The cellar.** No guards. Pull the lever. Percival says it out loud, and the ring on the floor shows how far his
   voice carries.
2. **The pantry.** Nod walks up and down. Stand at the lever and the ring shows first, red if Nod is inside it. Wait
   until he walks out of it, then pull.
3. **The stairs.** Stilts blocks them, facing the wrong way. Examine the pots across the room, then get out of the way:
   Percival describes them, Stilts goes to look, and you slip up the stairs behind him.

Each room has one goal, its rule on screen, and a word from Percival in your ear as you reach it. The ear asides are
not out loud, so no guard hears them.

## The job

1. Pick Gord's pocket for the archive key. Sneak up behind him and hold E, then keep sneaking away. Once Percival
   tells him, Gord pats his belt, then turns round to look where the hand was: be out of his sight by then.
2. Unlock the archive door while Gord is outside the ring.
3. Pull the lever in the archive. It raises the vault gate and the grate of a dark crawlspace into the vault.
4. Pick the vault guard Bertram's pocket for the case key.
5. Take the Idol of Silence.
6. Climb the rope out.

Get caught and you try again from the last step, once its line is over and nobody is chasing her.

## How Percival works

There are three rules, and nothing is hidden:

- **He says out loud whatever you do.** This covers pulling, picking, unlocking, taking and examining. He draws a
  visible breath first: 2.6 s after a deed, 2 s after examining something.
- **His ring is always the same size.** It reaches 5 steps around Mouse, and walls cut it short (past a wall it
  carries 1/1.6 as far). Stand at anything he would talk about and the ring shows before you act: teal if no guard is
  inside, red if one is. The prompt says who would hear. How close the guards are changes only how excited he sounds.
- **Every guard inside the ring hears him, and goes to look at whatever he talked about:** the lever, the door, the
  pots, the pedestal. A guard whose pocket was picked pats his belt (eyes down, about 1.6 s), then turns round, at a man's pace, to where the hand was.

Two more things happen with him:

- **Sights.** A few things he can't walk past without reading out, every word. Walking into a sight's gold ring sets
  him off, and his ring follows Mouse while he reads:
  - the visitors' book, just inside the archive door
  - the Roll of the Caught, by the hall to the entrance, which only catches his eye on the way out with the idol
- **The idol.** Once she has it, Q clamps it over his mouth for 8 s ("Mmmph!"), and his ring shrinks to almost
  nothing. This works twice. The guards hurry once it's gone.

The end screen rates the run: Ghost, Whisper, Page-turner or Bestseller.

Footsteps: walking within 2 steps of a guard, or running within 5, makes him turn. Sneaking (Shift) is silent.

## Look

- **One pixel grid.** The world renders at about a third of the screen's resolution and scales up sharp, so the 3D
  props and the pixel sprites share one grid.
- **Light.** The three nearest torches cast soft shadows. One post pass adds bloom, a filmic tone map, the grade
  (cool shadows, warm torchlight), a vignette and grain.
- **Walls.** The walls between the camera and a room are knee-high cutaways.
- **Props.** They are forge-godot's Tripo models, outlined like the sprites.

## Files

| Path | What |
|---|---|
| `game/src.html` | the whole game (three.js 0.169 from jsdelivr) |
| `tools/lines.py` | every spoken line, by trigger and loudness tier |
| `tools/audio.py` | voices them with ElevenLabs eleven_v3 (Percival George, Gord/Bertram/Nod Callum, Stilts/Stretch Will), and makes the sound effects. Percival's mouth is read off each clip as it decodes, so it keeps time with his voice |
| `tools/art.py` | PixelLab sprites: Mouse, and the guards drawn with Mouse as the style reference; Percival's face and mouth shapes |
| `tools/props3d.py` | copies forge-godot's 3D props with their textures shrunk to 512 px |
| `tools/pack.py` | packs `art/raw` into the sheets in `game/art` |
| `tools/build.py` | writes `out/web/`: `index.html` (artifact body), `play.html`, `voice.mp3`, `props3d.json` |
| `PLAN.md` | the polish plan from the adversarial audits |

Rebuild: `python tools/audio.py`, `python tools/pack.py`, `python tools/build.py`. `out/web/play.html` fetches its voice
and props by relative URL, so serve the folder rather than opening the file.
