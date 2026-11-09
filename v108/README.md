# v108 DOOMSDAY: Dexter × MF DOOM "Doomsday" (voidfx, 9:16)

A Dexter edit from the Dexter studio, scaffolded from the v107 ALL CAPS standard (the v12 engine + the v107 toolkit) on
`dev/pipeline-v2`. It is the first edit made with the efficiency update's loop (`song:`, `plan`, the sign-off pages,
`rev`, the fresh-eyes critique).

## The brief
The owner sent the song and two concept boards: *"I would like for you to create a edit using the doomsday song and the
attached concept transitions/ideas. I do not want you to use any text for either of the concepts I have attached (this
is not a new preference or something I want you to institute often, this is just what I want for this edit) … Try to
make this the best dexter edit you have created."* Asked whether the rest of the edit should carry lyric captions, the
owner chose **no text anywhere**.

- **SPECIMEN** (board 01): a microscope slide crosses his face and magnifies his eye; the next clip appears inside the
  glass before it fills the screen. 0.3–0.5 s, a glass tick at entry, a bass impact on the reveal, on the main drop.
- **SURFACE** (board 02): clear plastic stretches over the footage, its folds bending the picture; it peels diagonally
  away to a darker Dexter. 0.5–0.8 s, plastic tension and a sharp snap, where the edit turns from calm to threatening.

## Concept
**UNDER THE SURFACE / BORN IN BLOOD.** DOOM's hook, *"On Doomsday, ever since the womb, till I'm back where my brother
went, that's what my tomb say"*, is Dexter's history taken literally: he was born in blood in a shipping container, and
the S1 finale takes him back to his brother Brian's table, wrapped in plastic.

- **"Watch your own back, came in and go out alone":** the mask. Warm Miami: the sunset smile, the palms, the sunlit stare.
- **"Stay in the zone": SURFACE.** Kill-room plastic is pulled over the calm close-up, stretches (its folds bend his
  face), and peels away diagonally, slowly and then with a snap, onto the darker Dexter underneath. The grade changes
  with the peel.
- **"Turn H2O to cognac":** the drums and bass drop out; the M99 close-up; he holds a blood slide up to the light.
- **"On DOOMSDAY": SPECIMEN** (the signature, on the drop). A glass slide with a bead of blood sweeps in, settles over
  his eye and magnifies it; the green-lit stare appears inside the glass; the slide comes to the lens and fills it as the
  beat slams back.
- **"Ever since the womb":** blood pours down the lens onto the shipping container he was born in.
- **"Till I'm back where my brother went":** frost creeps over the lens (the Ice Truck Killer) and thaws onto him
  strapped to Brian's table.
- **"That's what my tomb say":** a roll onto him lying face up.
- **"Right above my government, Dumile name":** a crime-scene photo onto Miami Metro and the badge; the grin by the squad car.
- **"Either unmarked or engraved":** into the woods with the axe (the Trinity hike: an unmarked grave). **"Hey, who's to
  say?":** he turns and smirks at the lens.
- **"I wrote this one…":** a clean downbeat cut to the red desk, with the beat camera's punch; the light table. **"If you don't believe me":** the
  night drive; the wiper wipes it onto the boat with the trash bags, **"go get bagged and checked in"**.
- **The loop: THE LAST DROP.** He looks up; one drop of blood falls in the dark beside his head and comes toward the
  lens. Frame 0's smile is inside it; it fills the frame on the last frame and the edit starts again on the mask.
  The slide's drop is the hero object: twice, SPECIMEN and the loop.

## Song
- `src/doomsday.mp3` (MF DOOM, 4:58), 95.39 BPM; the drum-stem fit agrees with the map.
- Window h208 → h280 (9 bars, 65.643 → 88.286 s, 22.64 s); loop wrap 0.956 on the music stem.
- Lyrics: Whisper large-v3 on the Demucs vocal stem (`work/song.json`). Cuts sit on the sung words (the table in the EDL).
- The drop: drums and bass muted e18–e22 (the vocal and the sample thin out under a low-pass), back on "DOOMSDAY".

## Look
Two grades split by the peel. **surface108** (shots 1–3): warm, bleached pastel Miami, lifted blacks. **under108** (from
the peel): cold steel and teal, deep blacks; only blood red survives (skin is kept out of it). A fine grain, a soft
vignette, a little near-neutral halation.

## Sound
13 placed effects in 11 moments, layered only at the set pieces: the plastic (a pull, the creak, the snap), the drop (one
reverse swell, the glass tick, the bass impact), the pour, the frost forming, the roll, the wiper, the last drop. Small
transitions are silent; nothing on beat moments; no chimes or drones. Effects +10 dB against DOOM's loud master, the music
ducked 3 dB under the two biggest hits.

## Measured (the delivered file)
- **QC:** 11/11 on the encode. **Loudness:** −13.2 LUFS, true peak −3.3 dBTP after AAC.
- **Loop seam:** blurred difference 0.13 (gate ≤ 1); audio seam step 0.027; picture wrap step 0.73 vs local median 1.51.
- **Flashes:** 1, no white-outs. **Text:** none.
- **Faces vs effects:** 9 frames in 4 runs, all designed: the sun sweep (114), rain on the lens (864, 896), the loop drop as it
  fills the frame (1332–1342).
- **Motion audit:** no dead spans, no judder; 1 unexplained pop at 1213, the wiper blade's own sweep (designed).
- **plan_check:** 0 FAIL; 1 WARN (13 effects, the lean target is 10–12).
- **Effort:** 3 full renders before delivery (over the target of 2: the third applied the fresh-eyes critique), about 14 min
  of rendering, QC about 3 min a pass.

## Files
`work/edl108.py` (every decision), `work/fx108.py` (the v108 section at the end: the looks, SURFACE, SPECIMEN, the frost,
the last drop, the drop of blood), `work/audio108.py` (the v108 section: `music108`, `main108`). Media stays out of git.

## Caught before delivery (the new loop)
- **plan_check:** the three new transitions before they existed; a sandbox-sound warning; then 0 FAIL throughout.
- **QC, rev 1:** frame 0's close-up was wider than the 9:16 window (face-centring FAIL) → the sunset smile; an unexplained
  pop where the zipper ended → the wiper.
- **The sign-off pages:** the plastic first read as rain (rebuilt as folds); the frost read as a web (now rime only); the
  library heat haze carried the Flash studio's zigzag fire; `blood_lens` was a flat red tint; `m99`'s lids read as black
  bars; the headlights parked two orbs on his eyes; the zipper filled the frame with black; skin read as blood in the cold
  grade; the loop drop crossed his face.
- **The fresh-eyes critique** (one agent, before delivery): HIGH: the eye dive's black field with an outlined hexagon (your
  black-box family) → a clean downbeat cut; the frost's lines over his face → rime. MEDIUM: the two boat shots looked
  alike → the woods; the whip's gold streak crossed his mouth → removed; SPECIMEN showed hair, not a face, inside the glass
  → the incoming face is framed in it; the loop drop read as a marble → it falls down the dark beside him. One claim was
  not a defect: the "coil" at the left edge in SURFACE is the backlit trunk behind him in the source.

## Revision 1 (the owner's notes, 2026-11-09)
*"I generally like the edit. … merge that slide graphic slash animation and merge it with one of the actual slides from
that scene … I generally like when on the beat the clip like kind of jumps up and down with the beat, but in this edit I
would like for you to remove that just for this edit … add a lot more transition and unique graphics with custom
animated transitions … a lot of smooth transitions and creative ones so the edit flows all together."*

- **SPECIMEN with the real slide.** The upper slide in his hands (its own blood smear and frosted label, cut from the
  frame) lifts toward the lens, swings up so its clear end lies over his eye and magnifies it, the green stare appears in
  the glass, and the slide fills the lens on "DOOMSDAY". Where it was, the picture is filled from its surroundings, and his
  face goes soft behind the slide (depth of field). The CG slide and its bead are gone.
- **No beat bounce** anywhere in this edit (no zoom punch, kick or hit-frame blur). Recorded as a v108 exception, not a
  new rule.
- **Seven new custom transitions**, each its own idea and smooth: *haze* (Miami heat shimmer), *diffusion* (cognac-red dye
  spreading through water on "turn H2O to cognac"), *double vision* (the M99 takes hold), *luminol* (the light drops and
  blue forensic glow blooms around him, never on his face), *face match* (his face slides and scales onto the next face
  and they dissolve), *developer* (a print develops under the red safelight into the red desk), *sink* (the water rises
  over the lens and drains off the last shot). Three new shots (a Miami street, the car, a blood-slide close-up): 22 shots,
  21 transitions + the loop (was 19 / 18). Generic connectors are down to 6.
- **After the fresh-eyes critique (rev 1b):** SPECIMEN's slide now pivots up in his fingers (like tilting a slide to the
  light) so its clear end reaches his eye: most of where it was stays covered, and the rest sits in the soft background
  (it had left a grey band over his mouth). The face match registers on the eye line; the heat haze warps harder and
  switches at its peak; the darkroom ripples; the sink has bubbles; the dye wash is smooth; luminol glows soft and only
  below the collar; the 3 s shot is a calm day shot from another scene (it looked like the container scene); the palms
  shot starts after the passer-by; the wiper is slower (its one-frame jump is gone); skin no longer turns red in three
  shots. QC: SHIP, 11 pops all cuts, no dead spans, no judder.

## Revision 2 (the owner's notes)
*"I'd like for you to remove the water droplet filter at 14 seconds … I also do not like the first transition that's kind
of like the squiggle, swirl, weird animation. I like to replace it with a creative, unique transition."*
- **14 s:** the rain-on-the-lens transition into the woods is gone; a smooth push instead. `rainfocus` is now rejected in
  `studio/transitions.json`.
- **The heat haze at 1.9 s** is replaced by **FRONDS**: sunlit palm fronds (backlit, out of focus, three depths with
  parallax and motion blur) sweep across the lens as we pass under the palms he stands beneath; the cut is behind the
  nearest frond, with a soft leaf rustle. `haze108` is rejected in the registry.
- Note for the render-speed work: registering a new transition in `TR2` makes change tracking re-render every frame
  (`render` reads `TR2`), so a one-transition swap still costs a full render.
