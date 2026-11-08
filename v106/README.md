# v106 WONDERWALL — The Flash × Oasis "Wonderwall" (voidfx, 9:16)

A one-off Flash edit made in the Dexter studio's number range, on the v11 BOP engine (Flash base), on `dev/pipeline-v2`.

## Concept
**"Maybe you're gonna be the one that saves me."**
- In the S3 finale, Barry walks into the Speed Force to pay for Flashpoint, and Iris watches him go. In the S4 premiere, she is the one who brings him back ("Run, Barry, run").
- **The opening:** the edit opens inside the Speed Force, with Barry in the blue mist looking back over his shoulder.
- **"You're gonna be the one":** a lightning rod strikes and splits the frame onto Iris in tears. On "gonna", one of her tears gathers on her jaw, holding Barry's goodbye inside it, and falls toward the lens; we fall through it onto him (rev 2).
- **"Saves me":** he tears out in gold.
- **"And after all":** THE WONDERWALL rises behind him. It is a wall of glowing tiles, each one a moment of the edit, with gold light in the mortar.
- **"You're my":** the wall cracks with lightning.
- **"WONDERWALL":** the frame itself becomes the wall and bursts toward the camera, and he strides out through it.
- **The loop:** he turns and walks back into the Speed Force, and the mist clears on frame 0 ("I said maybe").

## Song
- **Source:** `src/wonderwall.mp3`, Oasis.
- **Tempo:** 87.02 BPM, fitted to the drum stem. The automatic map locked to 4/3 of it, 116 BPM, on the swung strum.
- **Window:** bars 57–65 (157.50 → 179.56 s, 22.06 s), the second chorus.
- **The loop:** bar 65 is where chorus 3 begins the same way in the song, so it is musically exact. The edit has no tape stop.
- **Lyrics:** Whisper large-v3 on the Demucs vocal stem, with every word checked against the stem's envelope. The small model had put "I said maybe" 3.4 s early.

| Time | Words |
|---|---|
| 1.07 s | "I said maybe" |
| 4.44 s | "you're gonna be" |
| 6.42 s | "the one" |
| 6.98 s | "that saves me" |
| 11.04 s | "and after all" |
| 14.42 s | "you're" |
| 16.40 s | "my" |
| 16.64 s | "wonderwall", held to about 20.8 s |

## Look
**WONDER:** golden-hour amber light against Speed Force cobalt, milky lifted blacks, and red-orange halation on the highlights. It is a fast table grade, `tone_lut`, with the colour on contiguous planes.

## Custom pieces (`v106/work/fx106.py`)
| Piece | What it does | Sound |
|---|---|---|
| Speed Force mist (`mist=`) | Drifting cobalt and violet wisps behind his matte, cold sparks, and a flicker every other beat | Airy bed |
| `mist_swirl` | A luminous mist volume rolls over the frame (the picture refracts and softens under it, never fully opaque) and clears onto the next shot, with lightning inside | Airy swell, crackle, reversed shimmer |
| `lightning_rod` | A leader flickers down, then the bolt strikes beside the next face (never on it), and the next shot burns open outward from the bolt with an ember rim | Leader crackle, thunder, ground impact |
| `tear_lens` (rev 2) | Fills the one dead span (the Iris hold, 4.8–6.5 s). A lit water drop (dark Fresnel edge, warm/cold rim, a streetlight highlight and its caustic, a soft shadow) gathers on her jaw; inside it, Barry's goodbye (S3 farewell, the reverse shot), minified as through a real drop. It lets go and falls toward the lens, growing until the frame is inside it; the lens relaxes flat and a ripple runs out, kept off his face | A soft plip as it lets go, a reversed swell, a low muffled bloom and a sub as we fall through |
| `clash106` | v11's clash, with the collision moved below the face and the sparks masked off it | Two zaps, impact, thunder |
| THE WONDERWALL (`wall=`) | A running-bond wall of bevelled tiles cut from the edit's own source frames (warm sepia memories) with gold mortar light, in perspective from below. It rises tile by tile from the bottom on "and after all", the mortar breathes on the beat, lightning crawls along the mortar on "you're my", and the light wraps his edge | Stone grind, a tick per row, rising crackle |
| `wonderwall` (focal) | The frame becomes the wall (running-bond tiles, lit bevels, glowing mortar, trembling), then bursts toward the camera on "WON-". The tiles fly out from the centre, with the ones over his face going first and fastest, and he strides out through gold light and a shockwave | Rumble build, crack, impact, sub drop, thunder, stone and glass shatter, whoosh |
| WONDERWALL title | Bevelled gold letters with a cobalt glow, each struck out of light on its syllable over the sung word; they phase out (vibrating ghosts) before the next cut | A zap per letter, panned across |
| `loop_mist` | He walks back into the Speed Force; the mist rolls over the lens and clears on frame 0's own image | Airy swell, reversed shimmer, reversed swell |

From the engine: the motion pass (velocity ramps with flow on restored frames, plus the beat camera, which rests on Iris and through the burst); `strobe_echo`, `phase`, `speedforce_in`, `bolt_trace`, `whirlwind`, `emblem_flash`, `dolly`, `lichtenberg`, `whip`, `strobe`, `perimeter`, `lightstreak` and `light_leak`; and the aura, remnants, charge, dust and rays.

## Rev 2 (owner notes)
- **"Remove like half of the sound effects, mostly the tedious annoying ones like the emblem shine and the few near the end."** Cut 14 of the 28 sound moments: the emblem shine; everything after the burst (the light-leak chime, the mist swirl into the last shot, the title's letter zaps, the loop swells, the Speed Force air beds); the strobe-echo stutter, the bolt-trace crackle and the eyes-close-up strobe; the camera-punch swishes; the wall's row ticks, its crack bed, the aura hit and the remnant whooshes. Every shimmer ("shine") and the Speed Force whine are gone. Kept: the lightning rod, the clash, the light streaks, phase, the Speed Force rush, the whirlwind, the dolly, the Lichtenberg, the whip, the perimeter, the stone grind, the charge hum and the burst; added the tear.
- **"One more polish smooth over the animations."** Five held shots ran at the source's 24p cadence (judder spikes every 2–3 frames): eyes, saves, emblem, through and smile now use flow in-betweens like the rest. The mist transitions popped at their ends (the corners were still covered at zero): the coverage is now exactly clear at 0 and full at 1, and the shots dissolve under the mist instead of switching. The tiles' tremble is a smooth shiver (each tile on its own 9–15 Hz sine) instead of a new random offset every frame. The mist's lightning stays at the frame edges, off faces. The Speed Force mist used to drift in whole quarter-res steps (a small jump every ~3 frames); it now drifts sub-pixel, on a canvas big enough that it never wraps. The last shot used to start inside a pink lightning flicker in the source (134.37–134.47 s), which jumped twice under the mist; it now starts at 134.50, steady blue like frame 0.
- **"Make sure the loop is seamless."** Rev 1 switched the picture under the mist to a frozen frame 0 in a single frame (a jump of 26 grey levels at 21.4 s) and froze the mist behind him. Now the picture dissolves into frame 0's under the thickest mist, frame 0's finish fades in with it, and the Speed Force mist behind him keeps drifting on into frame 0 (rendered at the loop's virtual frames). The mist's cold flicker moved to the half bar, so frame 0 is clean. Sound: the loop is the music alone (bar 65 into chorus 3).
- **"Identify one space where there isn't anything happening and add a custom unique graphic into a cool transition."** Measured frame-to-frame activity on the encode: the Iris hold (e14–e19, 4.8–6.5 s) was the stillest span in the edit (1.2–1.4 grey levels a frame, against 5–18 elsewhere). It is now Iris → TEAR LENS → Barry's goodbye on "gonna", landing on the sung word.

Rev 2 measured on the encode: QC 11/11, loop seam 0.14, −13.0 LUFS / −3.3 dBTP after AAC. Frame-to-frame jumps that weren't cuts or designed flashes: rev 1 had them at 2.3 s, 18.4 s, 20.27 s, 20.35 s, 21.4 s and across the wrap; rev 2 has none. Sharpness within 1–4 % of rev 1 on every shot.

## Rev 3 (owner note)
- **"Can you slow down the tear drop transition so it's more visible?"** The tear now runs 1.0 s instead of 0.6 s (it gathers on her jaw for 0.4 s with Barry visible inside, hangs and swells for 0.15 s, then falls toward the lens for 0.45 s), and the fall-through settles over 0.43 s instead of 0.3 s. To make room, the cut onto Barry moved one half-beat later, onto the sung "BE", and the clash into "saves me" moved one half-beat later too, onto the sung "SAVES" (it was 0.43 s early). QC 11/11, seam 0.14, −13.0 LUFS / −2.9 dBTP after AAC.

## Measured
See `work/qc.log`, `work/mixcheck.json` and `work/sharpness.json` after the render.
