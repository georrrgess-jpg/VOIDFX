# v106 WONDERWALL — The Flash × Oasis "Wonderwall" (voidfx, 9:16)

A one-off Flash edit made in the Dexter studio's number range, on the v11 BOP engine (Flash base), on `dev/pipeline-v2`.

## Concept
**"Maybe you're gonna be the one that saves me."**
- In the S3 finale, Barry walks into the Speed Force to pay for Flashpoint, and Iris watches him go. In the S4 premiere, she is the one who brings him back ("Run, Barry, run").
- **The opening:** the edit opens inside the Speed Force, with Barry in the blue mist looking back over his shoulder.
- **"You're gonna be the one":** a lightning rod strikes and splits the frame onto Iris in tears.
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
| `clash106` | v11's clash, with the collision moved below the face and the sparks masked off it | Two zaps, impact, thunder |
| THE WONDERWALL (`wall=`) | A running-bond wall of bevelled tiles cut from the edit's own source frames (warm sepia memories) with gold mortar light, in perspective from below. It rises tile by tile from the bottom on "and after all", the mortar breathes on the beat, lightning crawls along the mortar on "you're my", and the light wraps his edge | Stone grind, a tick per row, rising crackle |
| `wonderwall` (focal) | The frame becomes the wall (running-bond tiles, lit bevels, glowing mortar, trembling), then bursts toward the camera on "WON-". The tiles fly out from the centre, with the ones over his face going first and fastest, and he strides out through gold light and a shockwave | Rumble build, crack, impact, sub drop, thunder, stone and glass shatter, whoosh |
| WONDERWALL title | Bevelled gold letters with a cobalt glow, each struck out of light on its syllable over the sung word; they phase out (vibrating ghosts) before the next cut | A zap per letter, panned across |
| `loop_mist` | He walks back into the Speed Force; the mist rolls over the lens and clears on frame 0's own image | Airy swell, reversed shimmer, reversed swell |

From the engine: the motion pass (velocity ramps with flow on restored frames, plus the beat camera, which rests on Iris and through the burst); `strobe_echo`, `phase`, `speedforce_in`, `bolt_trace`, `whirlwind`, `emblem_flash`, `dolly`, `lichtenberg`, `whip`, `strobe`, `perimeter`, `lightstreak` and `light_leak`; and the aura, remnants, charge, dust and rays.

## Measured
See `work/qc.log`, `work/mixcheck.json` and `work/sharpness.json` after the render.
