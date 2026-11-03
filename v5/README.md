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
