# Polish plan and what came of it (2026-10-29)

Two rounds of adversarial review, each with independent reviewers working from screenshots and code: a stealth designer,
an indie art director and, in round one, a gameplay programmer. Then a bot played every segment of the heist in real
time from its real checkpoint.

## Look

- One pixel grid: the world renders at about a third of the screen's resolution and scales up sharp, so the 3D props
  and the pixel sprites share one grid. The camera snaps to whole pixels.
- Post pass: bloom, a filmic tone map, the grade (cool shadows, warm torchlight), a vignette, grain, and red edges in a
  chase.
- Lighting:
  - The three nearest torches cast soft shadows from props, walls and the sprites.
  - Contact shading where floor meets wall, and lit lips on the wall tops, which are lit from within so they read as
    stone.
  - Gord and Bertram carry real lantern light, which also counts toward being seen.
- The walls between the camera and a room are knee-high cutaways, and the camera stays over the map and looks ahead.
- Props:
  - outlined like the sprites (thin on the torch stands)
  - squared with forge-godot's own yaw table
  - one long table instead of two squashed ones
- Effects: live flames, small halos, embers that fade, and a few warm motes in the daylight shaft.
- Vision cones are an ordered stipple on the pixel grid: calm teal, then amber, then crimson.
- Voice rings: constant-width bands, cut by walls exactly as his voice is. The coming ring is dashed.
- See-through outlines show behind walls, tall props and guards, never as a smear.
- Type: Cormorant SC for the interface, IM Fell English for speech, IM Fell English SC for shouting. Pixel-framed and
  bevelled buttons, prompts, bubbles (kept on screen and stacked), and pixel icons.
- The HUD is one inked plate: portrait, state, cause, four volume pips, who would hear, and breath and boredom bars. The
  job is one line, and the HUD hides behind any card. The end card shows Percival's face and his review.

## Play

- Room lines are whispered, and only at a quiet moment.
- Deeds cut off his chatter and always get the full breath. Tiers: under 2.5 he shouts, under 5 he's thrilled (and that
  guard hears), under 8 he chats. Reach is 1.5, 4.5, 9 or 13 steps.
- Guards who hear go to what he described, once per line; the lever's line sends them to the gate it opened. A
  chaser counts a line as heard, so a shout cannot re-steer him later.
- A sleeping guard does not excite him, but can hear him close by.
- Boredom is measured by where she is, and paused while a guard is within 6 steps. Standing still is seen no more than
  sneaking.
- The reveal: Nod hears the intro, shuffles over, gives up and dozes off: "...Did he hear me? Oh dear." He sleeps in the
  far corner of the entrance hall, clear of the route.
- Percival notices: he derails, gets suspicious, and stops falling for it after three times. Quiet deeds are strained
  whispers. The lines that read as machine-written were rewritten.
- Routes:
  - Pillars in the guardroom.
  - A crawlspace from the archive into the vault, opened by the lever and too low for guards to enter.
  - Statues in the vault.
  - Bertram turns in the middle of the vault.
  - Junk sits away from deed spots.
- The idol: two Shh charges, which become available once its line has been said. Guards hurry once it is gone.
- The review rates the winning try: Ghost, Whisper, Page-turner or Bestseller.
- Checkpoints save once a deed's line is over and nobody is chasing her. They keep the Shh charges and subject changes.
  There is no restart from the pause screen during a chase.
- Sound: ElevenLabs effects for footsteps (walking and running only), keys, the lock, the lever and gate, the idol, the
  alarm, the cell door and the win. Bertram and Nod have voices of their own.

## Code

- Fixed:
  - a spot with no last position, which froze the game
  - a chaser running on the spot
  - the audio clock holding up the game (every line has a wall-clock deadline, and audio resumes on input)
  - R on the win card
  - old lines playing into a new try
  - the intro could be skipped, and its timer leaked
  - the time stat never reset
  - the restart line's volume, and it no longer wakes Nod
  - queued breaths were halved, and a later trigger could jump the queue
  - pulses after the end
  - landscape phones, touchscreen laptops, and the iPhone silent switch
  - load errors went unreported
  - per-frame DOM writes, an invisible full-screen pass, eager decoding of every clip, serial loading, and leaks
    on retry

## Rebuilt on three rules (Justin, 2026-10-29)

After playing the dozing build, he said:
- "I still have no idea what's going on or what I'm supposed to do."
- "Early challenges need to be very simple and have clear mechanics."
- "Nothing I do as a player seems to matter at all."

He was right. Most of what set Percival off was outside the player's hands:
- the nearest guard's distance set how far his voice carried
- a timer put him to sleep
- a guard walking up set him off
- walking past a sight made him read

He chose a rebuild on three rules, with nothing hidden:
1. He says out loud whatever you do, after a visible breath.
2. His ring is always 5 steps, cut by walls. It shows before you act, teal or red, and the prompt names who would hear.
3. Guards who hear go to look at whatever he talked about. A guard who was pickpocketed pats his belt, then turns
   round to where the hand was (see the next section).

Gone:
- dozing and the Doze bar
- volume set by guard distance (the tiers now only change how excited he sounds)
- the volume pips
- "someone's coming"
- running lines
- changing the subject with junk, which is replaced by luring with it

New:
- **The way in.** Three small rooms, south of the entrance, each with one goal and one rule shown under the goal:
  - the cellar, with no guards
  - the pantry, where Nod walks past the lever
  - the stairs, which Stilts blocks facing the wrong way (examine the pots, then slip past)

  The guardroom is now Gord alone. Its first step is the pickpocket lesson, then the door, using the pantry's rule
  again.
- **Asides.** Percival talks to the player as she reaches each lesson: whispered, teal, and not out loud, so no guard
  hears them. The intro reveal now has Nod hear him through the cellar gate and come to the bars.
- **Sights.** The visitors' book stays. The Roll is only read on the way out, where the idol's Shh is the answer.

## Verified by bot (real time, no teleports, 2 runs each, after the rebuild)

A segment counts as done only once Percival's line about it is over, so a guard hearing it would show.

| Segment | Result |
|---|---|
| Cellar: pull the lever | 2/2, never heard, never seen |
| Pantry: wait at the door until Nod walks away, pull, go through the gate | 2/2, never heard, never seen |
| Stairs: examine the pots, hide in the far corner, up the stairs while Stilts looks | 2/2, Stilts hears on purpose, never seen |
| A: Gord's pocket, out of the ring before he speaks; the door while Gord is far | 2/2, never heard, never seen |
| B: the visitors' book, then the archive lever | 2/2, never heard, never seen |
| C: Bertram's pocket, then behind the statue, which cuts the ring short | 2/2, never heard, never seen |
| D: the idol, then behind the other statue | 2/2, never heard, never seen |
| E: the escape; the idol over his mouth for the Roll; the rope | 2/2, never heard, never seen |

What the runs changed along the way:
- Nod's walk gave too short a window, so he now dawdles 3.5 s at the far end.
- Stilts stood inside the one-tile stairway, where its walls cut the ring short and he could never hear the pots. He
  now stands at the foot of the stairs, still blocking them.
- A torch in the stairs room sat on the obvious path, so it moved beside Stilts.

## After the rebuild: Justin's notes, 2026-10-30

| He saw | Cause | Fix |
|---|---|---|
| She is sideways with two heads while sneaking | PixelLab's skeleton sneak came back garbled facing north-east (also used, mirrored, for north-west), and its "south" row faces south-west | That one direction redrawn (`tools/anim2.py mouse crouched-walking sk-sneak-ne --dirs north-east`, 3 generations; the garbled frames kept in `art/raw/mouse/sk-sneak-garbled`); the sneak takes its south and southern diagonals from the right rows |
| A picked guard turns straight round to face her, so sneaking away is impossible | He snapped round the instant Percival spoke, 2.6 s after the pick, and swept nearly the whole half behind him; sneaking covers under 4 steps in that time | He pats his belt first (1.6 s, eyes down, no cone), then turns at a man's pace (3.2 rad/s) and sweeps narrower (±0.7 rad) |
| Percival's mouth doesn't match his speaking | The mouth came from PixelLab's text-only plan stretched evenly over each clip | The mouth is read off each clip as it decodes: loudness every 50 ms opens it, a hiss shows teeth, silence shuts it |
| Holding Shift to sneak isn't fun | | Shift (or the Sneak button) turns sneaking on and off; a SNEAKING badge shows while it is on |

Verified by bot after these changes (real time):

| Run | Result |
|---|---|
| Pick Gord, then stand still (the control) | caught, as it should be |
| Pick Gord, then sneak straight back the way he came | 2/2: he hears, pats, looks, never sees her |
| Pick Gord, then sneak back down the hall | 2/2: the walls cut the ring, he never hears |
| Pick Gord, then one step aside into the dark | 2/2: he hears and searches, never sees her |
| A and C as before | 1/1 each, never heard, never seen |
| His mouth against the playing buffer (the intro, 306 samples) | shut in 101 of 104 silent samples, open in 115 of 119 loud ones |
