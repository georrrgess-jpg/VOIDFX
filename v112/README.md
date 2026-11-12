# v112 FORGIVENESS: Dexter × Tame Impala "Posthumous Forgiveness" (voidfx, 9:16)

A Dexter edit from the Dexter studio, scaffolded from the v111 MONSTER standard (`--base v111`) on `dev/pipeline-v2`.

## The brief
*"I would like for you to create a visually appealing and expert level dexter edit using the attached song. I would like
this edit to incorporate amazing and unique transitions, graphics and animations. I want you to create a really unique and
creative transition and I would like for you to try to incorporate cool camera motions to achieve this loop. Ensure the
loop is seamless and the animations and graphics are smooth. I want this to be the best dexter edit you have created and
it should reflect that. and I would like this edit to be completed in an efficient manner."*

## Concept
**WANNA TELL YOU 'BOUT THE TIME.** The song is a son talking to his dead father; Dexter's dead father is Harry, who gave
him the Code. The edit is what Dexter would tell him.
- **Golden hour and memory** through the long held *"Wanna tell you 'bout the time…"* (the break, no bass): the port at
  sunset (frame 0), his face against the low sun at the parade (a SUN LEAK burns across the film, the next shot behind its front), the funeral (the picture splits into its
  colours through a PRISM), him in the car by day, looking up at the evening, the night drive, the kill room.
- **VERTIGO** (the signature, the build into the drop): at the cemetery by the lake, the camera does a dolly zoom: he stays
  the same size while the cemetery behind him compresses toward him, softening and warming, as the song builds. On the
  drop the vertigo **snaps** forward and the world rushes past into the next shot.
- **The drop** is the life he'd tell Harry about: the palm-lined street at speed, the sunglasses going on (**THE GLINT**:
  the sun catches the brightest point beside him and throws an anamorphic streak), the grin, the mask, *"all the times
  that I had"* on his blood slides, the kill room, the crime scene's light bar, the fronds, the tear, the fire.
- **THE ORBIT** (the loop, a camera move): the last shot and frame 0 sit side by side round him like one panorama; the
  camera swings across from one to the other, the frame turning in perspective and rolling with the swing, the motion
  blur following its speed, and the low sun between the two places passes through the lens: the swing through the
  sunset lands on him at the port at sunset (frame 0). The swing is still settling over frame 0's first half-second, so
  the loop never stops moving.
- **Living animation:** anamorphic flares drift from the sun in the golden shots (only on a real light, never across his
  face); dust floats in the low light; red halation round every highlight.

## Song
`src/posthumous.mp3` (6:06). The song changes tempo; the second half's groove is **83 BPM** (half-beat 0.3615 s; the full
mix and the snare agree; the drum fit locked to another relative and the map to part one's 77 BPM, so the grid was fitted
on the groove by hand). Window **h820–h888 (296.75–321.33 s, 24.58 s)**: *"Wanna tell you 'bout the time"* held over the
break, the drop at e38 (13.7 s, the bass returns), *"I was in Abbey Road / All the times that I had"*, ending before
*"Thought of you"*.

## Look
**GOLDEN HOUR:** warm 70s film: amber highlights, lifted teal shadows, red halation, grain, a soft chromatic edge; the
night shots cooler. No text.

## Transitions (20 + the loop)
New: leak112 (SUN LEAK), prism112, vertigo112 (the signature, with the VERTIGO dolly zoom on the grave), glint112,
orbit112 (THE ORBIT loop). From the v110–v111 toolkits: emerge, lookup, nightfall, daybreak, slide, lightmatch, siren.
Liked library pieces: plasticroll110, bokeh110, light_sweep108, fronds108, tear110, flicker109. Connectors: whip ×2,
dolly.

## Sound
Seven lean moments: the sun leak's swell; a low rising hum through the vertigo; a breath drawn in to the drop and a sub
drop on the snap; the glint's whoosh; a far siren whoop at the crime scene; THE ORBIT's rush, carried across the loop.

## Caught before rendering (stills)
- The song's tempo changes; the auto window was instrumental. Re-fitted on the groove and moved to the lyric.
- A tight profile close-up cropped to his cheek; an extreme close-up cropped to his nose and mouth; a slide-at-the-window
  shot that can't keep both his face and the slide in 9:16: all replaced. Two pairs of shots from the same source take
  (the kill room, the palm street) replaced.
- The flare's streak crossed his face (now guarded) and drew on a bright shirt (now only on the sun).
- The first orbit squeezed him into a sliver at the swap; rebuilt as a perspective swing with parallax and a roll, the
  swap inside the peak motion blur.
- The glint swapped two faces in a crossfade (now inside the burst); the brush's jagged edge crossed his face (now a light
  sweep).

## Before delivery: QC rounds
- **Round 1** (QC 10/11): the sunlit profile close-up was wider than the 9:16 frame (face cut off) and a dead span
  (1.8–2.9 s); THE ORBIT read as a cut-out of him in front of a sliding plate and swapped two Dexters in a crossfade;
  the prism and the sun leak each showed both shots at once; two library transitions (bokeh, nightfall) stopped on a
  non-zero effect (pops). Fixed: the sunset parade close-up; THE ORBIT rebuilt as one camera swing on the whole picture
  through the sun (no cut-out, no crossfade); the leak's front carries the next shot; the prism swaps inside its peak
  blur; the tapers; VERTIGO lengthened to 1.0 s and its first frames no longer blend the unzoomed grave.
- **Round 2–3:** the grin (an extreme close-up cut at the eyebrows) became the lab smirk into the lens; the prism's swap
  moved under a soft warm peak (a 52-level pop at 3.3 s); the flare no longer lands on the white shirt in the last shot.
- **Round 4:** the warm close-up (cut off) became the kitchen smirk in the blinds' light, into which the light sweep is
  motivated.
- **Round 5, the fresh-eyes critique** (predicted HIGH: the nightfall's black patches on his face, three look-alike
  close-ups in a row, the cemetery hold dragging): the nightfall keeps its lamps off his face and never goes black; the
  dusk, night and lab shots replaced (the sunlit suburb by the car, the shipping container lit from above, the lab's
  projector light) so the first half moves between places and scales; VERTIGO pushed to 2.45× so the cemetery visibly
  compresses at phone size, its streak removed; the whip edge-replicates (it mirrored two half-faces); the daybreak
  into the last shot (a double exposure of two close-ups) became a bright-out; the orbit's join feathered; the sunlit
  shirt rolled off. QC now leaves the loop's own window out of face-centring (the swing moves the face by design).
- **Measured (final):** QC 11/11 on the encode; -13.0 LUFS, true peak -3.5 dBTP after AAC; loop seam blurred
  difference 0.23 (gate ≤ 1), audio seam step 0.0066, wrap step 1.29 vs local median 2.27; no white-outs, 1 flash
  event; no dead spans, no judder; the two remaining pops are designed (the bokeh's swap at 10.9 s, the bright-out's
  climb at 23.4 s).
- **Left as judgement calls:** the sunglasses shot is an extreme close-up (the glasses going on are the moment); 21
  transitions + the loop in 24.6 s (the first half is the song's long held break, a calmer section).
