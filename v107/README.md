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

## Measured
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
