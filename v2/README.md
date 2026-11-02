# THE DARK PASSENGER — Dexter × MATRIX FUNK (slowed) — voidfx v2

A 25.7-second, 1920×1080, 60 fps Dexter character edit built in code (FFmpeg + Python/OpenCV)
from all three supplied scene packs. It uses MATRIX FUNK (slowed), the voidfx logo, and the
supplied TikTok reference for structure, look and sound.

## What the reference does (measured) and how v2 answers it

| Reference | Measured | v2 |
|---|---|---|
| Song | MATRIX FUNK slowed again by 1.126× with the pitch drop (102.8 BPM vs the file's 115.8) | Same 1.12644× vinyl-style slow-down → 102.83 BPM |
| Intro | bass removed (sub ~60 dB down), highs rolled off; two phrases with a ~1-beat echo-out gap | High-pass 180 Hz + low-pass 3.2 kHz; one-beat echo-out gap after phrase 1 |
| Drop | full bass returns on a phrase downbeat at 8.6 s | Full range returns on the song's own re-entry after its break, at 9.34 s |
| Picture, intro | black-and-white hallway walk, then face close-up and a red DEXTER title | B&W letterboxed tunnel walk, name card, flicker blackout, gloves, eyes-to-lens close-up, red DEXTER title with growing blood drips |
| Picture, drop | comic/ink look, one cut per beat, red accents, newsprint textures, glitch and white-slab transitions | Comic-ink filter (ink lines + halftone + paper); blood is the only colour; one cut per beat |
| Ending | tool graphics, strobing silhouette, hard stop | Comic page with four panels; finger-gun at the lens with a strobe; BANG; music stops; voidfx logo animation |
| Branding | creator watermark persistent bottom-right | voidfx logo watermark bottom-right throughout, plus an animated logo outro |

## Structure (1 beat = 0.5835 s)

| Time | What happens |
|---|---|
| 0.00–0.13 | **Flash-forward hook**: three glitched ink frames from later in the edit (blood slide, hood, finger-gun) |
| 0.13–4.09 | B&W letterboxed tunnel walk; typed name card "DEXTER MORGAN / BLOOD SPATTER ANALYST — MIAMI METRO P.D." |
| 4.09–4.67 | The tunnel light flickers out on the musical gap (electrical buzz, echo tail) |
| 4.67–7.00 | The light snaps on: gloving up in a single white spotlight (pack 2) |
| 7.00–8.75 | Hands together, eyes lift to the lens (pack 3, optical-flow slow motion); **DEXTER** slams in, blood drips grow |
| 8.75–9.34 | Picture drains to black, only the red title remains; a riser builds |
| **9.34** | **DROP**: white hit, the title shatters, the letterbox snaps open, shake + RGB split; the world turns to ink as he pulls up the hood (pack 3) |
| 9.34–18.67 | One cut per beat, 16 shots from all three packs: jungle charge, chain-link stare, whip pan into the garage run, stick charge (invert hit), face shield and drill flare, the blood slide (red), kill-room knife; a white slab wipe into **"TONIGHT'S / THE / NIGHT"** typed over him leaning over a victim; knife, glitch into the bandana mask, blue kill room, hand on face, face shield, "shh", peeking |
| 18.67–21.01 | **Comic page**: four panels slam in on the beats (hands, night drive, crouched in plastic, release), "THE DARK PASSENGER" caption box, then the camera rushes into the last panel |
| 21.01–23.34 | Glitch cut to the office grin; slow finger-gun at the lens; strobe accelerates |
| **23.34** | **BANG**: muzzle flash, shake, the music stops dead (only its reverb tail) |
| 23.4–25.68 | voidfx logo: slices slide in with motion blur, glint sweep, slow push, glitch out |

## Techniques used

- **Velocity ramps** with real motion blur: several source frames are averaged across the shutter during fast parts.
- **Optical-flow slow motion** (DIS flow, bidirectional warping) on the 24 fps close-up.
- **Duplicate-frame removal:** pack 2 is 24p inside a 60 fps file, so its repeated pulldown frames are dropped before retiming.
- **Comic-ink look:**
  - CLAHE tone mapping.
  - Extended-DoG ink lines.
  - Three tones: ink, a 45° halftone, and paper.
  - Edge-preserving flattening on busy foliage.
  - Procedural newsprint texture ("BAY HARBOR BUTCHER") printed into the highlights.
  - Blood-red kept by colour ratio, so blood stays red and skin doesn't.
- **Camera and impact effects:** per-cut zoom bounce and rotation snap, impact shakes, RGB split, invert hits, a whip pan with directional blur, a glitch slice/block transition, a white slab wipe, a letterbox snap-open and a strobe.
- **Type:** typed name card with a cursor; DEXTER with procedurally grown blood drips (a separate drip per letter edge) that run over the letterbox; kinetic words with stroke, slam-scale, motion blur and tilt.
- **Comic page:** panels composited on a page with borders, slam-ins, a caption box and a camera rush.
- **Logo:** the user's voidfx logo, as a sliced fly-in with motion blur, a glint sweep and a glitch-out.

## Sound

- **Music:** the slowed song as above.
- **Effects (synthesized, sparse):**
  - typing ticks on the name card
  - light-flicker buzz synced to the picture flicker
  - title slam
  - a riser into the drop, then the drop impact
  - a whoosh on the whip pan
  - glitch bursts
  - panel slams
  - the BANG (impact plus reverb)
  - a logo whoosh and shimmer
- **Levels:** intro about 6 dB under the drop, as in the reference. Mastered to −13.0 LUFS with true peak −2.5 dBTP, measured on the encoded MP4. An AAC pre-roll keeps the encoder from overshooting on the opening hit.

## Files

- `out_final/the_dark_passenger_voidfx.mp4`: **upload version**, 77 MB. H.264 High at ~24 Mbps, because the halftone texture needs bitrate. AAC 256k, fast-start.
- `out_final/the_dark_passenger_voidfx_master.mov`: **master** (H.264 CRF 11 + 24-bit PCM).
- `work/edl2.py`: every decision.
- `work/render2.py`: picture.
- `work/audio2.py`: sound.
- `work/qc2.py`: checks.
- `work/analyze.py`, `work/strips.py`: analysis tools.

### Re-render

```bash
python3 v2/work/audio2.py
python3 v2/work/render2.py video v2/out_final
python3 v2/work/qc2.py v2/out_final/the_dark_passenger_voidfx.mp4 final
```

## QC (measured on the encoded upload file)

| Check | Result |
|---|---|
| Format | 1920×1080, 60/1 CFR, 1,541 frames, 25.683 s, start 0.000 |
| Decode | full decode, no errors |
| Cuts | 20 of 22 cuts re-detected on their exact frames; the other two are hidden on purpose (black-to-light-on, whip pan) |
| Black frames | only the planned ones: flash-forward gaps, the flicker-out, the strobe, post-bang |
| Frozen runs | none |
| Beat sync | bass hits land within −14 to +23 ms of the grid (≤ 1.4 frames) |

Fixes made during review:
- **Noisy shots:** the drop shot, the foliage shots and the stone wall were noisy in ink, so they got edge-preserving flattening and brighter paper.
- **"shh" shot:** unreadable in ink, so it uses photographic B&W.
- **Skin turning red:** the "blood" detection was catching skin, so it was rebuilt from measured colour ratios (blood r/g ≥ 2.0, skin ≤ 1.71).
- **Finger-gun shirt:** red patches on the shirt were removed, keeping only the wall art red.
- **Title shatter:** shortened, so the drop shot reads.
- **Opening:** a flash-forward hook was added.


## Revision 2 (this version)

- **More clips, faster cuts:**
  - A second intro walk: the hallway with the axe (pack 3).
  - A glove-snap insert at the crime-scene pool (pack 2).
  - New montage shots: crime tape (pack 2), axe stare (pack 3) and gloved walk (pack 3).
  - Two half-beat bursts (crime tape → knife; axe stare → hand on face → face shield → gloved walk) escalate the cut rate before the comic page.
  - 27 cuts in 25.7 s, up from 21.
- **New transitions:**
  - Radial zoom-throughs at 10.5 s, 12.25 s and 17.5 s.
  - A spin transition at 15.75 s.
  - All are built from 7-sample motion-blurred camera moves that accelerate into the cut and decelerate out of it.
  - They join the whip pan, glitch cuts and white slab wipe.
- **New graphics:**
  - Animated comic speed lines on the three charge shots. They are drawn as contrast-inverted streaks, so they read on both black and white.
  - Procedural blood-splatter bursts (body, streaks and droplets; scale-in, then fade) on the drop and on "NIGHT".
  - The intro camera "breathes" on every beat.
- **Sound:**
  - The bang now ends in a 0.42 s tape-stop instead of a dead cut.
  - A whoosh is timed to each zoom and spin transition, and a panned splat hit to each splatter.
  - Glitch bursts are softer and low-passed, and the flicker buzz is quieter.
  - The effects bus is soft-saturated, and the music ducks 2.5 dB under the drop and bang impacts.
  - The encoded audio was scanned for clicks: every edit point is clean. The two transients the scan flagged are drum hits in the song itself.
- **QC:**
  - Picture: 1,541 frames, 60 fps, no decode errors, no frozen runs.
  - Loudness: −13.0 LUFS with true peak −2.6 dBTP.
  - Cuts: 24 of 27 re-detected on their exact frames; the other three are deliberately hidden (light-on, whip pan, zoom-through).


## Revision 3 (final)

- **Blood transition into the drop (8.7–9.6 s):**
  - DEXTER is now liquid blood, with gloss, bevel, shadow and a red glow; its drips grow and droplets break off.
  - At 8.9 s the drips surge and become a full-screen pour: about 30 streams widen until the frame is solid, flowing blood.
  - On the drop the curtain falls away under gravity, its jagged edge revealing the comic-ink hood shot.
  - Splatters land just after the reveal.
  - Sound: a bubbling pour and rumble build under the riser, then a downward splash on the reveal.
- **TONIGHT'S THE NIGHT:**
  - The words now stack instead of replacing each other.
  - Each word has a sticker outline, an ink stroke, a 3D extrusion and a halftone drop shadow. A comic starburst slams in behind each one.
  - Earlier words get knocked when a new one lands.
  - NIGHT is liquid red and drips.
  - All three blast out toward the camera before the next cut.
  - Each word has its own thud (NIGHT heaviest), plus an exit whoosh.
- **New transitions:**
  - A comic-strip slice slam (alternating panel strips, 13.4 s).
  - An ink bleed, where the next shot spreads in through the darkest ink first (18.1 s).
  - Both have their own whooshes.
- **Polish:**
  - The comic page has a halftone background and panel drop shadows.
  - The voidfx logo outro gets two blood drips with droplet "plinks".
  - The drop's white flash is reduced, so the blood reveal carries the moment.
- **9:16 vertical version** (`out_final_9x16/`):
  - Every shot is reframed separately for vertical and checked at start and end.
  - The comic page becomes four stacked panels.
  - Title, words, name card, splatters and watermark are laid out for vertical, with the watermark above TikTok's caption area.
- **QC (both versions):**
  - Picture: 1,541 frames, 60 fps, 25.683 s, full decode with no errors, no frozen runs.
  - Loudness: −13.0 LUFS with true peak −2.3 dBTP.


## Revision 4 (audio polish, logo)

- **Logo:** the blood drips and their "plink" sounds are removed from the voidfx logo outro.
- **Intro audio:**
  - **Brighter:** it was heavily filtered (high-pass 180 Hz + low-pass 3.2 kHz, which sounded muffled). It is now only lightly trimmed (high-pass 95 Hz + low-pass 7.5 kHz).
  - **Smooth open-up:** over the last 2.3 s before the drop it opens to full range with an equal-power blend, so the drop no longer jumps from a muffled to a full sound.
  - **No click at the start:** the filters run on 1 s of lead-in before the edit starts, so they are settled at frame 0.
  - **Softer gap:** the one-beat gap is a soft −12 dB dip with 60 ms fades and an echo tail, instead of a hard cut to silence.
  - **Fewer small sounds:** the typing ticks are removed, the light-flicker buzz is 6 dB quieter and low-passed, and the opening glitch burst is 4 dB quieter.
  - **Level:** the intro now sits about 3–4 dB under the drop (previously ~6 dB).
  - **Clicks:** a click scan finds only two sharp drum hits that are in the song itself.

## Limitations

- **I can't watch or listen.** Everything was checked frame by frame and by measurement. Watch once at normal speed with sound before posting.
- **The "4K" packs are 1280×720** (upscaled 1.5× to 1080p), so close-ups are soft. The ink look hides most of this.
- **Pack 3 is 24 fps**, so its normal-speed shots keep 24p cadence. The eyes-up close-up is optical-flow interpolated.
- **No vocals.** The reference's audio and the supplied MP3 match closely spectrally, and I found no vocal layer to replicate. None were added.
- **Vertical framing:** the 9:16 version crops each 16:9 shot, so some wide moments (the comic page, crowd shots) are tighter than in the horizontal cut.
