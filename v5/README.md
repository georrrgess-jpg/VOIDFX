# FASTEST — The Flash × bôa "Duvet" (voidfx v5, 9:16)

This is a 25.77 s, 1080×1920, 60 fps TikTok edit built to the standard in `/CLAUDE.md` (benchmark: v4). It uses both Flash scene packs and the song "Duvet".

## Concept

Barry Allen, the fastest man alive, is losing everything, and the lyric carries it: *"I am falling, I am fading, I am drowning, tell me to breathe, I am hurting, I have lost it all, I am losing, tell me to breathe."* The edit moves from quiet, unmasked Barry to the full Speed Force. The look is warm amber and gold lightning over deep teal shadows, so it is visually distinct from the Dexter edits.

## Song window

Duvet is fitted to a half-beat grid (93 BPM, 529 onsets). The edit uses half-beats 208–288: exactly **10 bars**, from *"and you don't even think a thing"* to the last *"breathe"*. Because the window is a whole number of bars, the loop jumps from bar 36 back to bar 26 in tempo. The packs' audio has no usable dialogue, so the edit is music-driven.

## Timeline

| Time | Lyric | Picture | Transition in |
|---|---|---|---|
| 0.00 | *and you don't even think a thing* | masked close-up (THE FASTEST MAN ALIVE light-sweep title) | **lightning strike tears the frame open** from black |
| 1.29 | | Barry unmasked, dark | warm light flare |
| 2.58 | | pulling the cowl | **molecular phase** (vibrating copies) |
| 3.87 | | street run (0.29× flow slow-mo) | → **speed-force tunnel** |
| 5.15 | *I am falling* | falling through the air | out of the tunnel |
| 6.44 | FALLING (letters drop with gravity) | Barry with lightning | **lightning split** (frame tears along a bolt) |
| 7.73 | | Barry in the lab | dissolve |
| 9.02 | FADING (letters dissolve to sparks) | close-up | → phase out |
| 10.31 | *I am drowning* — DROWNING (ripple) | sparks / glowing blue chest (crawling arcs) | phase in, whip |
| 12.88 | *tell me to breathe* — BREATHE (slow inhale glow) | glowing Speed Force eyes, 2.6 s hero hold | flash |
| 15.46 | *I am hurting* — HURTING (RGB tear) | Barry unmasked | **voidfx logo: lightning traces the letters, fly through the "o"** (the only logo appearance) |
| 16.75–20.62 | *I have lost it all* — LOST / IT / ALL | lightning room, side run, street runs, lightning run | flash, whip, zoom-through + streaks, 3D roll |
| 20.62–24.48 | *I am losing* — LOSING (speed-streak) | scream, beam, lab storm, dark hand, white suit | flash, RGB cut, **time-vortex twirl**, lightning split |
| 24.48–25.77 | *tell me to breathe* — BREATHE | final masked close-up | → **fly into his eye, streaks collapse to black** → loop to the lightning strike |

## Built-in review (per the standard)

Review ran in passes on rendered stills while building. Each pass found and fixed problems:

1. **Opening shot:** the extreme close-up was cropping through the eyes. Fixed by reframing.
2. **"Equations" shot:** it could not be framed in 9:16 without cutting the face, so it was replaced with the lab shot.
3. **Speed-force tunnel:** too dense and busy. Toned down.
4. **voidfx logo:** the "o" ring left a white block over the next shot. It now fades as the camera passes through.
5. **Text that never appeared:** three words never showed because their end times fell before the sung word: **LOST IT ALL's "ALL"**, **FALLING** and **HURTING**. All are fixed, and `edl5.py` now asserts that every lyric window is non-empty.

Checkpoint run 1 passed all 7 automated criteria but **failed visual sign-off**, so the edit was not shipped:
- **HURTING over a face:** HURTING ran into the next shot and sat over the running Flash's face (also flagged by the text-over-face pass). It now ends on its own shot.
- **Empty stretch:** the 2.6 s glowing-eyes hold had about 1.3 s with nothing happening before BREATHE. A soft "TELL ME TO" lead-in line now eases in word by word on the sung words, before both BREATHEs.

The edit was re-rendered and the checkpoint run again.

The final **ship / no-ship checkpoint** is `work/qc5.py`. It runs on the encoded MP4 and checks format and frame count, a clean decode, loudness and true peak, frozen runs, face centering on every shot, text over faces, audio clicks at every cut and the loop seam. It prints PASS/FAIL per criterion and a verdict. After that comes a visual sign-off on contact sheets of every transition. If anything fails, the edit is fixed and re-rendered before delivery.

### Checkpoint run 2 (final): **SHIP**

| Criterion | Result |
|---|---|
| Format | PASS: 1080×1920, 60 fps, 1,546 frames, 25.767 s |
| Decode | PASS: clean |
| Loudness | PASS: −13.1 LUFS, true peak −3.0 dBTP |
| Frozen runs | PASS: none |
| Face centering | PASS: all shots (1 frame flagged, the distant running figure in the slow-mo street shot) |
| Audio clicks | PASS: 0 at 22 cuts |
| Loop seam | PASS: both ends dark; the loop re-enters on the opening lightning crack |
| Visual sign-off | PASS: every transition and text moment checked on frames from the encoded file. The one text-over-face flag ("TELL ME TO" in the white-suit shot) sits below his chin; the detector's box just extends lower than the face. |


## Revision 2 (user feedback)

- **Removed:** the THE FASTEST MAN ALIVE title card.
- **Removed:** the speed-force "starburst" tunnel (the burst you didn't like), both mid-edit and at the end.
- **New opening, emblem draw-on:** on black, the Flash emblem draws itself in electric gold. Its ring and lightning bolt are traced by bright sparks, with small arcs crackling around it. The bolt fills and flashes, then the camera **flies through the lightning bolt** into the first shot. Sound: an electric hum, crackles, then a crack and a whoosh through the bolt.
- **New transition, light-speed slit:** the street run collapses into a single glowing horizontal line, and the next shot bursts open from it. Used for the drop into "I am falling".
- **New transition, speed afterimages:** the incoming shot arrives as four converging red and gold time-remnants that snap together. Used twice.
- **New transition, shockwave:** a refracting ring of energy expands out from Barry's face, bending the image and revealing the next shot. Used on the scream.
- **New ending, collapse:** the last shot and its BREATHE collapse into the glowing line, then a spark, then black. That loops straight into the emblem drawing itself.

### Revision 2 checkpoint: **SHIP**

- **Automated criteria:** all 7 PASS. −13.1 LUFS / −3.0 dBTP, 0 clicks at 22 cuts, no frozen runs, faces centred.
- **Loop seam:** last and first frames are both black (luma 0.5 vs 0.6).
- **Visual sign-off:** all new effects were verified on frames pulled from the encoded MP4: the emblem draw-on, the fly through the bolt, the light-speed slit, the afterimages, the shockwave, and the line-to-spark-to-black ending.


## Revision 3 (user feedback)

- **Removed:** the slow-motion street run straight at the camera, and the shot of Barry suspended in the air after it.
- **Replacements:** a masked Barry smiling (on *"think a thing"*), then the emblem crackling with blue lightning (ring-wipe in), then masked Barry with green arcs (bolt-wipe in).
- **Lyrics as full phrases, not single words.** Every line is a two-tier lockup timed word by word to the vocal:
  - a small tracked lead line (*I AM*, *TELL ME TO*, *I HAVE*);
  - a large detailed keyword: gradient fill, gold edge, inner shading, glow, and a light sweep once it lands;
  - a soft dark backing keeps every line readable over bright lightning.
  - The intro also gets text now: *YOU DON'T EVEN / THINK A THING*.
- **Each keyword's animation acts out its meaning:**
  - FALLING drops in with gravity, then falls away;
  - FADING dissolves into rising sparks;
  - DROWNING sinks through a ripple while bubbles rise;
  - BREATHE inhales slowly while a heartbeat (ECG) line draws across the screen;
  - HURTING lands, then cracks apart along a lightning fracture;
  - LOST / IT / ALL stack up, then scatter away;
  - LOSING arrives letter by letter, then is pulled away one letter at a time.
- **New transitions:**
  - **ring wipe:** an expanding gold energy ring reveals the next shot;
  - **bolt wipe:** a lightning bolt sweeps across the frame, with the next shot behind it;
  - **prism:** RGB copies converge;
  - **speed smear:** row-sliced horizontal motion smear.
  - These replace every remaining plain flash or RGB cut. Each has its own sound.
- **New ambient graphics:**
  - drifting gold embers through the whole edit, denser in the second half;
  - lightning bolts flickering down both edges of the frame on every downbeat of the chorus;
  - gold light streaks across the running shots.
- **Lyric sound design:** a crack on HURTING, bubbles on DROWNING, shimmer on FADING, and whooshes on LOST IT ALL and LOSING.

### Revision 3 checkpoint: **SHIP**

- **Automated criteria:** all 7 PASS.
  - −13.1 LUFS / −3.0 dBTP.
  - 0 clicks at 23 cuts.
  - No frozen runs.
  - **0 face-centering flags and 0 text-over-face frames** (the first fully clean run).
  - Loop seam: first and last frames both black (luma 0.6 / 0.6).
- **Visual sign-off:** every lyric lockup, meaning-driven text animation and new transition was verified on frames pulled from the encoded MP4.


## Revision 4 (user feedback)

- **Lyric fix:** the opening line is *you don't even **feel** a thing*. The speech model had heard "think". It now reads YOU DON'T EVEN / FEEL A THING.
- **New FALLING animation, in three acts:**
  1. **Plunge.** The word drops in from just above, stretched, with a vertical gold light trail.
  2. **Slam.** It lands with squash-and-settle, an elliptical gold shockwave under it and a burst of gravity-driven sparks, then a light sweep.
  3. **Tumble.** The letters break loose one by one and fall away, spinning, with ember trails.
  - Sound: a plunge whoosh, a slam impact, spark shimmer and a tumble whoosh.
- **Polish:**
  - an anamorphic gold flare streaks off the brightest highlights;
  - subtle lens chromatic aberration toward the frame edges;
  - landing spark bursts on FEEL A THING, HURTING and LOSING.
- **More sound design:**
  - a soft tick as each lead word appears;
  - an impact on each keyword landing;
  - an inhale under each BREATHE;
  - risers plus sub drops into the three big sections (drowning, hurting, losing);
  - a low electric crackle bed under the whole chorus.

### Revision 4 checkpoint: **SHIP**

- **Automated criteria:** all 7 PASS.
  - −13.0 LUFS / −2.9 dBTP.
  - 0 clicks at 23 cuts.
  - No frozen runs.
  - 0 face-centering flags and 0 text-over-face frames.
  - Loop seam matched (luma 0.6 / 0.6).
- **Visual sign-off:** FEEL A THING and the three acts of FALLING (plunge, slam with shockwave and sparks, tumble) were verified on frames from the encoded MP4.

## Files

- `out/fastest_flash_voidfx_9x16.mp4`: upload version.
- `out/fastest_flash_voidfx_9x16_master.mov`: master.
- `work/edl5.py`: every decision.
- `work/render5.py`: picture. It uses the v4 engine plus a Flash toolkit: procedural lightning, lightning open and split, speed-force tunnel, molecular phase, twirl, crawling arcs, eye-out, and the logo with a lightning trace.
- `work/audio5.py`: sound. It builds the song loop and adds lightning cracks, zaps, whooshes and shimmer.
- `work/qc5.py`: the review and ship checkpoint.

### Re-render

```bash
python3 v5/work/render5.py prep
python3 v5/work/audio5.py
python3 v5/work/render5.py video v5/out
python3 v5/work/qc5.py v5/out/fastest_flash_voidfx_9x16.mp4
```

## Limitations

- **I can't watch or listen.** Everything was verified by frames and measurement. Watch once with sound before posting.
- **Sources are 720p.** Pack B is 24p content inside a 60 fps file, and its duplicate frames are dropped and flow-interpolated.
