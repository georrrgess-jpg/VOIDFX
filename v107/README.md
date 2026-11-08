# v107 ALL CAPS: Dexter × Madvillain "All Caps" (voidfx, 9:16)

A Dexter edit from the Dexter studio, built on the v12 engine on `dev/pipeline-v2`.

## Why the v12 engine
The agreed Dexter base, v105, has no restored-source sampler. That sampler (`sr_prep` bands, flow on restored frames) is the fix for the owner's one gripe about DRACULA: *"the quality of some of the clips."*

The v12 engine has it. It also has the speed ramps and the beat camera, and it carries every v4–v9 Dexter transition (plastic rip, redact, zipper, slidebox, m99 …). This is a choice the owner can overrule.

## Concept
**ALL CAPS.** *"Just remember ALL CAPS when you spell the man name."* The press only knows him as the BAY HARBOR BUTCHER; the song spells his name.

- **The verse is his work:**
  - **"And he won't stop till he got the masses":** his stare, then the kill table.
  - **"And show 'em what they know not":** "shh".
  - **"Through flows of hot molasses":** the blood lab, then the hazmat suit soaked in blood.
  - **"Do it like the robot to headspin":** the plastic, then the upside-down face.
  - **"Took a few minutes to convince the average bugaboo":** Doakes.
  - **"It's ugly like look at you, it's a damn shame":** Doakes in the cage, then a victim.
- **The press:** the newspaper spins in on "took a few minutes to convince". The headline is BAY HARBOR / BUTCHER, and the photo under it is him, captioned as the blood-spatter analyst.
- **"ALL CAPS when you spell the man name":** a strip of newsprint slaps across the frame. The six sung words stamp **D-E-X-T-E-R** onto it in letterpress type, one letter per word.
- **The beat break:** the strip flies up into the sky and becomes the real banner the plane tows over Miami, **WE ♥ DEXTER** (the S1 finale fantasy). Then the parade: he has got the masses.
- **The loop:** the confetti thickens over the lens on the bass drop-out bar and clears on frame 0, "and he won't stop till he got the masses".

## Song
- **Source:** `src/all_caps.mp3`, Madvillain, 2:14.
- **Tempo:** 87.50 BPM, fitted over 8 bars on the Demucs drum stem.
  - The automatic map read 175.6 BPM, and the drum autocorrelation read 117.4 (the dotted pattern).
  - The kick falls on every beat from 22.5166 s.
- **Window:** half-beats 176 → 240 (8 bars, 60.92 → 82.86 s, 21.94 s): the end of verse 1 and the beat break.
- **The loop:** the bass drops out in the last bar and returns on bar 1, so the wrap lands like a drop.
- **Lyrics:** Whisper large-v3 on the vocal stem. Onsets were snapped to the stem where they are strong (`work/onsets.json`). "Bugaboo" is the published word (Whisper heard "boogaloo" twice).

## Look
**TABLOID:**
- newsprint cream highlights, ink blacks and slate blues;
- one spot red (blood, the heart on the banner, the BUTCHER headline, caption emphasis);
- a misregistered red plate, paper grain, and a fine screen in the shadows.

Red-lit skin is kept out of the spot red per shot (`redthr`).

## Custom pieces (`work/fx107.py`)
| Piece | What it does | Sound |
|---|---|---|
| `press_flash` | A press camera fires. The next shot is printed as a halftone newspaper photo, which resolves into the footage as its dots shrink | Flashbulb pop, shutter |
| `molasses` (physical) | A viscous sheet of blood pours down the lens. Its leading edge has fingers and a rounded bead, and broad undulations slide down it. It refracts the shot under it, absorbs light by thickness, and has a glossy highlight. It drains from the top with a meniscus and reveals the next shot | A gloopy pour, a glug, a drip |
| `headspin` | Two full turns about the centre, motion-blurred, landing on the upside-down shot | Circling wind, a whoom, a sub |
| `flip` | The upside-down shot rolls over into the grin | A short whoosh |
| `frontpage` (hero asset) | The front page spins in (MIAMI GAZETTE, BAY HARBOR / BUTCHER, INVESTIGATION STILL ONGOING, columns, his halftone photo and caption), lands and settles. We dive into his photo, and its dots resolve into the next shot | Paper flutter, a slap, a whoosh |
| `stamp` (focal) | A torn strip of newsprint slaps on with "CAPS". D-E-X-T-E-R is stamped one letter per sung word: the type comes down, the ink spreads and settles, the paper is debossed, and the strip shakes. On the cut it flies into the sky and morphs onto the banner's own DEXTER | A paper slap, six letterpress hits, a whoosh and wind |
| banner shot | The source frame is enlarged only 1.2×, tracked on the banner, with the sky extended above and below, so WE ♥ DEXTER fits whole in 9:16 | (from the stamp) |
| `confetti_pop`, `confetti_loop` | Procedural paper confetti in the press palette: lit, fluttering, with depth of field. It bursts in the sky over the banner, then carries on behind him in the parade (his matte keeps it off him). In the loop it thickens over the lens on the bass drop-out bar and clears on frame 0 | A pop and a flutter; nothing in the loop bar |

From the engine: plastic rip, redact, impact, slam, whip, zipper, dolly; the beat camera; flow on restored frames; the robot step-motion (`robo()` in the EDL).

## Rev 2 (owner notes)
- **"The transition that occurs at 3 seconds in, I don't really like that. I like to replace it with a custom graphic into a really cool transition."** The press flash at 2.74 s is replaced by **SPECIAL REPORT** (`broadcast`):
  1. The kill-table shot letterboxes into a TV image.
  2. The TV pulls back into a dark room. It is a lit CRT set with a bevel, an LED and the screen's glow on the wall, and the picture carries a LIVE bug and a chyron: SPECIAL REPORT, BAY HARBOR BUTCHER STILL AT LARGE, POLICE URGE RESIDENTS TO STAY ALERT · FBI JOINS INVESTIGATION.
  3. The channel flips through rolling static onto him ("shh").
  4. We push back in, and the screen opens to the full frame.

  It runs 1.2 s on "till he got the masses / and show 'em". Sound: a CRT hum, a channel click with static, a push-in whoosh.
- **"The head spin transition ... the final shot doesn't have a centered shot of Dexter."** The spin now lands on a centred shot: his face from directly overhead on the pillow (S2, eyes opening). The turn decelerates about his face, so it reads as the camera spinning above his head. The roll into the grin became a whip.
- **"I also don't like that you reuse the same clip around the 17-second mark ... and the 19-second mark."** The second smiling parade close-up is gone. From 19.2 s it is one wide shot of him walking through the cheering crowd.
- **"Smooth out the ending part."** The beat camera rests through the whole break (from 18.5 s). The ending has fewer cuts: the crowd (a dolly), then the walk (a soft smear) carries the loop.
- **"The loop is pretty low effort ... make the loop more creative with a unique graphic/animation and then do the transition."** The loop is now **THE MASSES SPELL HIS NAME** (`name_loop`):
  1. The crowd's confetti swirls in from both sides at chest height (never across his face) and assembles into a 1000 px DEXTER of about 1,050 lit, fluttering paper pieces, while the parade steps back (dimmed, softened).
  2. The name holds through the bass drop-out bar.
  3. On the bar line it bursts toward the lens and down, while frame 0 dissolves in under it.
  4. The last frame is frame 0's picture.

  Sound: one paper flutter as it gathers, one whoosh on the burst.

## Rev 3 (owner notes)
- **"I don't like the transition at 3 seconds with the black bars."** The TV is gone. The kill-table shot now carries a two-part set piece, full frame throughout:
  1. **SPATTER ANALYSIS** (`spatter_fx`, the new graphic). Ten blood stains spatter across the lens, elongated along their flight lines, with satellites and mist. A taut red string runs back from each stain, with impact-angle readouts. On the e6 beat they lock at a ringed crosshair, and a paper tag types POINT OF ORIGIN. The point is where his face is about to appear.
  2. **RORSCHACH** (`rorschach`, 21 + 30 frames). From the point of origin a blood-ink blot blooms, mirrored about the fold like an inkblot card. Inside it his face appears mirrored (both of him), then the blot floods the frame. The mirrored half of the card swings open on the fold, and the real "shh" is underneath.

  Sound: a wet spatter burst, a short swell as the blot blooms, a plop on the cut, a paper swish as the card opens. These replace the four TV sounds.
- **"How slow it writes Dexter's name in black ... make it line up so it's not too fast and not too slow."** D-E-X-T-E-R is now stamped on an even 16th-note grid (e44 → e46.5, one letter every 10 frames, the hi-hat rhythm), not one letter per sung word (uneven gaps of 0.19–0.33 s). The platen comes down in the 3 frames before each hit, so each letter lands on its beat, with the stamp sound on the same frame. The name is complete on "the", so "man name" plays over the whole word.

## Rev 4 (owner notes)
- **"Get rid of the point of origin graphic/transition."** The spatter analysis and the Rorschach that grew out of it are both removed (the code stays in `fx107.py`, unused). The kill table now plays clean and cuts to "shh" on the downbeat, and the beat camera punches the cut.
  - Review lesson: the POINT OF ORIGIN, with strings converging on a target ring where his face appears, broke a recorded owner dislike: *no "gimmick on the face" effects (e.g. lines converging on his face with a target ring)*. Check the CLAUDE.md dislikes before designing a graphic.
- **"Remove and replace the black box transition from the 3 and a half second mark."** The redaction boxes ("shh" → the lab) are replaced by a **PAGE TURN** (`page_turn107`, 14 + 12 frames). The frame is a page of the paper:
  - it lifts at the bottom-right corner and rolls over a cylinder;
  - its back is newsprint (three columns of body type, crossheads, rules) with the picture faintly showing through;
  - it lies over itself as it turns, shades along the roll, casts a shadow on the lab shot underneath, and clears off the top-left corner.

  This is a true roll, where v104's page turn was a flat fold. Sound: one paper flip.

Caught by review before delivery:
- **Edge fringe on the beat hits:** every beat hit's colour split wrapped the frame's edge columns (`np.roll`), leaving a 2–3 px cyan line on the left edge and a magenta line on the right edge for a frame or two. It has been there since rev 1. `rgb_split` now repeats the edge pixels instead.

## Measured (rev 4)
- **QC:** 11/11 on the encode.
- **Loudness:** −13.0 LUFS, true peak −3.5 dBTP after AAC.
- **Loop seam:** the audio seam step is 0.0005; the picture lands on frame 0.
- **Glitch audit:** every jump is a cut, a beat hit or a designed transition. The page turn (frames 218–241) moves smoothly, with no single-frame pop; the cut at 165 is the downbeat.
- **Dead spans:** none of 0.5 s or more.
- **Effort:** 2 full renders for rev 4 (the second for the edge fix), about 280 s each.

## Measured (rev 3)
- **QC:** 11/11 on the encode.
- **Loudness:** −13.0 LUFS, true peak −3.4 dBTP after AAC.
- **Loop seam:** the audio seam step is 0.0005; the picture lands on frame 0.
- **The set piece (frames 96–200):** no frame-to-frame pop. The largest step is the e6 beat hit at the lock.
- **Dead spans:** none of 0.5 s or more.
- **Stamp:** the letters land on frames 905, 915, 926, 936, 946 and 957, one every 10 frames.
- **Effort:** 1 full render for rev 3, 282 s.

Caught by review on stills before the render:
- The spatter drops, strings and tag were too small to read at phone size; they are now 1.4–1.7× larger.
- The blot's wings ran off the frame and read as a band; it was reshaped into a card that fits the frame.
- The unfolding card went edge-on as a dark line through his nose; it now fades out before it turns edge-on.

## Measured (rev 2)
- **QC:** 11/11 on the encode.
- **Loudness:** −13.0 LUFS, true peak −3.5 dBTP after AAC.
- **Loop seam:** the audio seam step is 0.0005; the picture lands on frame 0.
- **Dead spans:** none of 0.5 s or more.
- **Glitch audit:** every frame-to-frame jump is a cut, a beat hit or a designed transition.
- **Effort:** 2 full renders for rev 2, about 275 s each.

Caught by review before delivery:
- **The TV exit:** the screen vignette and glass reflection switched off in one frame as the screen opened (top-of-frame luma 50 → 80). They now fade in with the letterbox and out as it opens.
- **The grin centring flag:** the grin is an extreme close-up whose face is wider than the frame, so the detector boxes it past the edge. Its only flags were inside the whip and the front-page fly-in. Centring QC now lists flags inside designed transitions without counting them, using the same windows faceqc leaves out.

## Measured (rev 1)
- **QC:** 11/11 on the encode.
- **Loudness:** −13.0 LUFS, true peak −3.5 dBTP after AAC.
- **Loop seam:** blurred difference 0.16 (the gate is ≤ 1); the audio seam step is 0.0005.
- **Flashes:** none over a mean luma of 110, and no white-outs.
- **Text over faces:** 2 single frames, on cuts.
- **Faces vs effects:** 11 flags in 2 runs (Doakes and the cage, ≤ 4.4 % of the face box).
- **Glitch audit:** every frame-to-frame jump is a cut, a beat hit or a designed transition.
- **Dead spans:** none of 1 s or more.
- **Sharpness:** five shots flagged soft: hazmat, robot, cage, crowd, final. They are 720p, restored, with zoom ≤ 1.06.
- **Effort:** 4 full renders before delivery, about 275 s each.

Caught by review before delivery:
- **The loop click:** the AAC tail pads about 2 ms of silence, and frame 0 starts on a loud kick, so the wrap clicked. Fixed with a 2 ms fade on each side.
- **Tight close-ups:** five shots put the face in the caption band or past the frame edge; they were swapped for wider moments.
- **Judder:** where flow is refused, the engine held frames, giving 24p judder; it now blends them.
- **The confetti burst:** it covered his face; it now goes behind his matte, and starts in the sky.
- **The banner sky:** the padding reflected the banner above and below.
- **Red skin:** red-lit skin read as blood, fixed with a per-shot red threshold.
