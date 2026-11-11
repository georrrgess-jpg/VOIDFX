# v111 MONSTER: Dexter × Kanye West "Monster" (voidfx, 9:16)

A Dexter edit from the Dexter studio, scaffolded from the v110 SLEEPWALKER standard (`--base v110`) on `dev/pipeline-v2`.

## The brief
*"I would like for you to create an edit using the attached song. I want this edit to be high quality and I want it to be
the best edit you have created. I would like this edit to include really cool and unique transitions, graphics and
animations. I would like this edit to be the best dexter edit you have created. I want this edit to be completed with
efficiency and quality."*

## Concept
**I SHOOT THE LIGHTS OUT.** He is the thing that lives in the dark, and the edit is a flow of light:
- **LIGHTS OUT** (frame 0): the marina at night, slowed. On *"I shoot the lights out"* the city's lights behind him go out
  one by one, in a wave from the edges in toward him. Each one stutters, flares and dies, and the night thickens with
  every light. On *"out"* the light on him drops to a cold rim.
- **HIDE**: the light comes back first (his face lit from below, out of the dark); we pan past a door's edge to him behind it with his reflection;
  behind the chain-link fence; we push through the fence to the night by the truck.
- **DAYBREAK** (*"till it's bright out"*): the sun comes up where it is in the next shot (at the edge of the frame); the
  morning is inside its light; the day burns white and comes down onto the lake.
- **NIGHTFALL** (*"just another lonely night"*): the night comes down the frame from the sky over the lake, the garden
  lamp behind him coming on; we tilt up to the night sky.
- **THE MOON**: a full moon rises in the real night sky behind him (seen only in the sky, never on him); it swells and
  burns, and becomes the lamp over the kill table (*"Are you willing to sacrifice your life?"*): the lamp, the table,
  the gloves, a light from under the frame into the scalpel over the light table, the glare matched into the last shot.
- **THE PASSENGER** (the build and the drop): crouched in the light from below, the shadows grow around him (the
  midtones sink into the dark a little more on every beat of the riser) while the light in his hands pulses. On
  *"…I'm a monster"* the dark around him opens into the day from the edges of the frame (a soft red-lit front closing in
  behind him), and he goes last, in one quick switch on the drop: the blood-soaked suit walking out.
- The drop: the suit, the close-up, *"blood sucker"* on the slides (a glass slide pushed across), the luminol glow into
  the blood room, the grin (a clean cut on the downbeat), the red face, **THE SIREN** (*"now look who's in trouble"*: a light bar's red
  sweeps the frame, then its blue, and the crime scene is behind the blue), the woods, the fronds, **CANOPY** (pools of
  sunlight through the leaves, the bamboo inside them).
- **THE SHOT** (the loop): *"all you hear is rumbles"*: he raises the pistol at us and fires; the flash at the real
  muzzle (tracked) lights him and the woods, and frame 0 opens inside it: a burst of light grows from the muzzle with the
  marina inside it and fills the frame exactly on the last frame (the seam lands on frame 0); the shot's echo carries
  over the loop, where the lights are still on, for now.

## Song
`src/monster.mp3` (6:19). **93.7 BPM**: the drum stem, the snare band and the full mix agree on a 0.640 s beat; the first
map's 125 BPM was a 3:4 alias of the kick pattern (dotted eighths), and its auto window (4:36) had no words.
The edit uses `src/monster_pad.wav` (the song with 1.0 s of silence in front) so it can start 0.17 s before Bon Iver's
"I". Window h2 → h90 (0.93 → 29.10 s of the padded file, **28.18 s**): the whole intro, the drop at e65 (20.8 s, the
bass and *"…I'm a monster"*), and the first three lines of the verse, ending on *"rumbles"* just before *"Say"*.

## Look
**NIGHTSHADE:** teal-navy shadows, warm practicals, the day golden; harder and redder after the drop. No text.

## Transitions (25 + the loop)
New: emerge111, doorslide111, fence111, daybreak111, brightout111, nightfall111, lookup111, moon111, underlight111,
lightmatch111, passenger111 (the signature), slide111, siren111, shot111 (the loop). Liked library pieces: tear110,
light_sweep108, plasticroll110, luminol108, flicker109, fronds108, bokeh110. Connectors: dolly ×3, whip; one clean
downbeat cut. The beat camera runs from the drop at half punch (the owner's calmer drop).

## Sound
About ten placed effects: three lamps blowing and the light on him dying; the daybreak swell; crickets under the night;
a whoosh up to the sky; the kill lamp's buzz; a breath drawn in to the drop, the impact and sub drop on it; a far siren
whoop on "trouble"; the gunshot, whose echo carries over the loop into frame 0.

## Caught before rendering
- The first song map said 125 BPM and picked an instrumental window at 4:36; re-fit on the drum stem (93.7 BPM) and moved
  to the intro and the drop.
- Frame 0 was first a tight close-up with no lights in it to shoot out, then a garden walk that leaves the frame; the
  marina (a skyline of lights behind him) replaced both.
- The moon shot was first a day-for-night close-up with no sky in the 9:16 crop; replaced by a real night sky behind him,
  framed by hand (the face tracker lost him in three night shots).
- THE PASSENGER was first his shadow on the wall (the matte covered the dark wall, so it never read), then a red-edged
  dark double of his head (it read as a red ring around his face, against the face rule), then the shadow lunging over
  the lens (it went black, against the black-occluder rule). It is now dark-first: the monster comes out of the shadows.
- The light-first reveal went near-black for a few frames; the bright-out showed a double exposure at the switch; the
  lights-out left blocky dark squares where the lights were; the garden read as day; the underlight's front crossed his
  face; the slide shot cropped the slide out. All fixed.

## Before delivery: QC and the fresh-eyes critique
- QC round 1 failed the loop seam (a hard cut from the woods to the marina) and measured a dead span at 0.3–2.2 s;
  the render also stalled once when a worker ran out of memory while the restoration ran, and the disk filled once
  (old edits' regenerable caches were cleared).
- The critique predicted, and the studio fixed before sending: the loop reading as a flash and a fade (frame 0 now opens
  inside the muzzle flash); the face-match at 4.5 s mirroring his face at the borders (now a pan past the door's edge);
  the drop blotching his face and floating his glowing hands over the suit (now the day opens from the edges behind him
  and he goes last); double exposures (the double-vision transition and the second bright-out replaced, crossfades
  shortened); the opening's lights too small to read at phone size (the room now steps down on "shoot", "the",
  "lights", "out", with bigger pops and a push-in); the tape smeared by interpolation (held frames).
- Round 4: a light blows on each beat of the held "shoot" before the wave on "the lights out" (the motion audit still
  reads 0.3–2.2 s as quiet: it is the slowed opening, the lights popping behind him and the push-in).
- **Measured (final):** ship checkpoint 11/11; loudness -13.1 LUFS, true peak -2.9 dBTP after AAC; loop seam blurred
  difference 0.27 (gate ≤ 1), audio seam step 0.0015; no white-outs; the flagged pops are the designed ones (the last
  light's stutter on "out", the gunshot).
- Left as judgement calls: the edit is 28.2 s (the whole Bon Iver intro and the drop; the owner's usual is 20–26 s);
  the garden shot's own camera judders slightly (1.3 s, at night, under the nightfall transition).

## Revision 1 (the owner's notes)
*"I generally like this edit but I would like for you to change a couple things. Firstly, I dislike the graphic/animation
that appeared around the 23 second mark the forensics one. I would like for you to also implement a new more creative
loop. I want more custom graphics and animations to be implemented."*
- **The luminol is gone:** BLEED: the blood spot on his slide soaks out through the frame like blood through paper,
  its wet front darker (kept off his face), and the blood room is inside it.
- **The new loop, THE TRACER:** on "rumbles" he fires at us; we whip after the bullet's tracer as it climbs the right
  of the frame through the night, and the whip lands on the marina at frame 0, the tracer going into one of the
  skyline's lights. That light flares from the hit and is the first to blow on "shoot": the end fires the shot that
  starts the edit. A bullet whiz under the whip, a glass tick on the hit.
- **New animations:** sparks and glass fly up and fall from every light that blows in the opening; god rays turn
  slowly from the sunrise through the haze; dust drifts in the kill lamp's light (only in the lit air, never on his
  face); after the siren's sweep the light bar's red and blue keep washing over the crime scene on the half-beats.
- **Measured:** ship checkpoint 12/12; -13.1 LUFS, -2.6 dBTP after AAC; loop seam blurred difference 0.16 (gate ≤ 1).
