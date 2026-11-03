# WARMPOP — Dexter × George Clanton "Warmpop" (voidfx v6, 9:16)

This is a 26.67 s, 1080×1920, 60 fps TikTok edit built to the standard in `/CLAUDE.md` (benchmark: v4). It uses all six Dexter sources: the new S5 pack, packs 1, 3, 4 and 5, and the Doakes pack's engine and methods.

## Concept: a VHS Miami daydream

Dexter's Season 5 voice-over carries the cold open: *"I've disappeared so many people. My turn now to disappear myself."* On *"disappear myself"* he literally dissolves into pixel dust that blows off the frame. The song's filtered build gets more and more restless:
- a kaleidoscope;
- a tape rewind;
- a camera flash on his blood-speckled face;
- a VHS tear.

Then the picture shrinks into a CRT television floating over a neon grid and sunset, and the camera dives through the screen into the drop, where the song's full mix comes back.

What follows is a sunlit, pastel Miami montage of Dexter grinning, running and killing. It ends on the red-shirt close-up, with *"It… was me."* lip-synced and lit up in neon.

The tape then rewinds, drops into static, and the static loops straight back into the tape loading at the start.

The look is a new pastel "vapor" grade, separate from every earlier edit's: lifted pink shadows, cyan-blue highlights and VHS chroma bleed. On top of that sit:
- scanlines and head-switch noise;
- a VCR on-screen display: PLAY ▶ at the start and ◀◀ REW at the end (the SP counter was removed at the user's request);
- bloom, an anamorphic streak and grain.

## Song window

The song's half-beat grid is fitted at 90 BPM. The edit plays half-beats **416–496**: exactly **10 bars**, 2:18.9 → 2:45.5.
- **First 4 bars:** the song's own filtered build (the highs are muffled), which sits under the voice-over.
- **2:29.5, the good part:** the full mix comes back in at half-beat 448, the edit's drop at 10.667 s, which lands exactly as the camera passes through the CRT.

## Timeline (revision 2)

| Time | Picture | Transition in (each has its own sound) |
|---|---|---|
| 0.00 | boat, pastel Miami skyline. VO: *"I've disappeared so many people."* | **tape load**: static, VCR clunk, the picture rolls in while the song winds up to speed |
| 2.67 | blue night profile. VO: *"My turn now to disappear myself."* → **he dissolves into pixel dust** | **into his eye**: the camera dives into his pupil, the pupil swallows the frame, a hexagonal camera aperture opens (heartbeat, shutter blades) |
| 6.67 | red shirt at the crime scene | **reassemble**: the scene builds itself from flying pixel blocks (the dissolve played backwards) |
| 8.00 | interrogation | **polaroid**: flash, the frame freezes into a print and is tossed away (shutter, print eject) |
| 8.67 | blood-speckled face | **face-match morph**: his face slides and scales onto his face in the next shot |
| 9.33 | walking out of the dark | **VHS tear** |
| 9.77 → 10.67 | frame shrinks into a CRT on the neon grid, camera dives through the screen with **hyperspace light streaks** | **CRT fly-through** (hum, riser, drop impact, degauss) |
| 10.67 | boat: Dexter stands in the **vapor world** (sunset + neon grid), then reality **tunes in** behind him scanline by scanline. Chrome **MIAMI** title | out of the screen |
| 12.00 | grin by the pink wall, palm shadows | **3D cube** turning over the vapor sunset world |
| 13.33 | running through the grass (VHS colour echo) | **through the sun**: a striped retro sun rises and the camera flies through its stripes |
| 14.00 | laughing, palm shadows, bokeh motes | **film strip whip**: the frame shrinks into a strip of film on a glowing light table, whips up to the next frame, zooms back in (projector rattle) |
| 14.67 | crime-scene crowd | **sticker peel**: the frame peels off from the corner like a glossy pastel sticker |
| 16.00 | grinning mid-kill, then a **VHS ‖ PAUSE** freeze with tape jitter on the grin | blood drop splat |
| 17.33 | ice cream in the club (VHS colour echo) | **knife slash**: a blade cuts the frame and the halves fly apart with blood flecks (swish, steel ring) |
| 18.67 | night garden | **voidfx logo as a neon sign**, fly through the "o" (the only logo appearance) |
| 20.00 | cap and sunglasses | **film burn**: pastel burn holes eat through the frame |
| 20.67 | hood | **through the sunglasses**: the next shot appears reflected in his lenses, the camera dives into one |
| 21.33 | finger gun | **shadow pass**: darkness swallows the frame, the next shot emerges brightest-first |
| 22.67 | red-shirt close-up, *"It… was me."* → neon **IT** · **WAS** · **ME.**, which throws coloured light onto his face | **finger-gun bang → CRT power-off**: muzzle flash on his fingertip, the picture collapses to a line and a dot, then powers back on |
| 26.00 | the shot rewinds at 8× (◀◀ REW), the song scrubs backwards | → static → loops into the tape load |

## Text

Every word eases in (fade + rise + blur-to-sharp) and sits in the 1270–1620 px band, clear of faces and of TikTok's UI. Each text moment has its own animation:
- **Voice-over captions:** two-line retro lockups with pink/cyan offset echoes. *disappeared* and *disappear myself* are in chrome, and the whole second caption breaks apart into flying pixels as he vanishes.
- **MIAMI:** chrome type sweeps in from the left with a light sweep across it.
- **IT / WAS / ME.:** neon tubes that ease in and flicker on, each word on its spoken word.
- **No labels, name tags, constant watermark or outro card.**

## Sound

- **Dialogue:** isolated from the pack's score with Demucs (htdemucs), high-passed, levelled to a speech-RMS target, equal-power fades at every join, and a small plate reverb. The music ducks about 6.5 dB under it (about 8 dB under "It was me").
- **Song:** varispeed tape spin-up at the start; at the end the song brakes and scrubs **backwards** with the picture's rewind, then static.
- **Bed:** tape hiss runs through everything, including the wrap, and the static runs across the loop seam. The mix is built circularly and mastered on a wrapped copy.
- **Sound design:** synthesised per transition: VCR clunk and motor, tape-scrub squeal, camera-flash pop, bit-crushed crumble for the pixel dissolve, CRT hum and degauss, card-flip ticks, neon buzz, blood drip and splash, water bloop, digital melt sweep, word ticks, MIAMI shimmer, and neon flicker on each end word.
- **Master:** −13 LUFS, true peak ≤ −2.5 dBTP, measured after AAC encoding.

## Built-in review

Review ran in passes on rendered stills while building. Each pass found and fixed problems:

1. **Captions:** *"I've disappeared so many people"* ran off both sides of the frame, and *"disappear"* overlapped *"My turn now to"*. Both are now two-line lockups.
2. **Pixel dissolve:** the first version sprayed blocks over the whole background. It was rebuilt as forward-moving particles taken only from Dexter's matte, with a cyan glow only along the dissolve front.
3. **CRT:** the TV screen showed the centre of the frame, which cut off his head. The screen now shows the face band, and the opening is a bezel closing in.
4. **Police-tape shot:** it showed the back of a cop's head in murky pink, so it was replaced. A lit interrogation profile was tried next, but it was **wider than the 9:16 window**, so it was rejected for the blood-speckled close-up.
5. **Montage replacements:** a "shades" shot that opened on someone's hair and an unreadable macro of lips were both replaced, with the sunlit run and the container kill.
6. **Club shot:** it ended on a blurred pan, so the source was trimmed and the frame blending switched to optical flow.
7. **Tiles:** the first version had flat black gaps. They are now glossy card flips.
8. **Neon sign:** it popped on and showed WAS 1.6 s before it was said. It now eases in word by word, timed from the vocal stem, which also showed the line is *"It… was me"* with no "Harry".
9. **Logo:** first placed over his face; moved below it.
10. **OSD:** moved below TikTok's top tabs.

The **ship / no-ship checkpoint** is `work/qc6.py`, run on the encoded MP4. It checks:
- format and frame count, and a clean decode;
- loudness and true peak after AAC;
- frozen runs and face centering on every shot;
- text over faces;
- clicks at every cut and at the loop seam;
- the picture and sound of the loop seam, and that audio and video are the same length.

After that comes a visual sign-off on contact sheets of every transition, the drop, the dissolve and the ending, pulled from the encoded file.

### Checkpoint run 1: automated 9/9 PASS, **visual sign-off FAIL** (not shipped)

Automated results:
- −13.0 LUFS / −2.9 dBTP after AAC.
- 1,600 frames, clean decode, no frozen runs.
- 0 face-centering flags and 0 text-over-face frames.
- 0 clicks at 17 cuts and at the loop seam.
- The loop seam matched static to static, and audio and video are exactly the same length.

Frames from the encoded file still showed three defects:
- **Kaleidoscope (both uses):** a hard wedge-shaped seam on the left. The angle morph from the normal frame to the folded one can't be continuous, so it is now a spin-dissolve into the full mirror fold.
- **Ripple:** its first frames pinched Dexter's face. The distortion is now about a third as strong, with a gentle tremble before the cut.
- **"It… was me.":** a dark blocky blotch beside his face. Police lights flip the source frame from red to dark, and optical-flow interpolation fails on that. The interpolator now falls back to a blend whenever consecutive source frames change brightness sharply.

The edit was re-rendered and the checkpoint run again.

### Checkpoint run 2 (final): **SHIP**

| Criterion | Result |
|---|---|
| Format | PASS: 1080×1920, 60 fps, 1,600 frames, 26.667 s |
| Decode | PASS: clean |
| Loudness | PASS: −13.0 LUFS, true peak −2.9 dBTP (after AAC) |
| Frozen runs | PASS: none |
| Face centering | PASS: 0 flags across all 18 shots |
| Text over faces | PASS: 0 frames |
| Audio clicks | PASS: 0 at 17 cuts and at the loop seam |
| Loop seam | PASS: static → static (blurred diff 4.3), −37.6 / −36.6 dBFS either side |
| A/V length | PASS: identical (0.0 ms) |
| Visual sign-off | PASS: every transition, the dissolve, the CRT drop, MIAMI, the neon logo, the neon words, the rewind and the static seam were checked on frames from the encoded MP4. All three run-1 defects are fixed. |

## Files

- `out/warmpop_dexter_voidfx_9x16.mp4`: upload version (H.264 + AAC, fast-start).
- `out/warmpop_dexter_voidfx_9x16_master.mov`: master (CRF 11 + PCM).
- `work/edl6.py`: every decision.
- `work/render6.py`: picture. It is the v4/v5 engine plus the v6 toolkit:
  - VHS look and OSD;
  - tape load and rewind end;
  - VHS roll and tear;
  - pixel dissolve with clean plate;
  - kaleidoscope;
  - CRT world fly-through;
  - card tiles and neon trace;
  - blood ink and ripple;
  - pixel-sort melt;
  - neon logo;
  - retro captions, MIAMI and the neon sign.
- `work/audio6.py`: sound.
- `work/qc6.py`: the review and ship checkpoint.

### Re-render

```bash
python3 v6/work/render6.py prep
python3 -m demucs -n htdemucs --two-stems=vocals -o v6/audio/sep v6/audio/pack6_clip.wav
python3 v6/work/audio6.py
python3 v6/work/render6.py video v6/out
python3 v6/work/qc6.py v6/out/warmpop_dexter_voidfx_9x16.mp4
```

`pack6_clip.wav` is the first 26 s of `src/pack6_s5.mp4` at 44.1 kHz. The song is `src/warmpop.mp3` resampled to `v6/audio/song48.wav`.

## Limitations

- **I can't watch or listen.** Everything was verified by frames and measurement. Watch once with sound before posting.
- **Sources are 720p,** and some are 24p or 30p. Duplicate frames are dropped and optical-flow interpolated to 60 fps.
- **Length:** 26.67 s, which is ten whole bars. That is slightly over the 26 s guideline, kept so the music window ends on a bar.

## Revision 2 (user feedback)

- **Removed:** the Japanese subtitle lines under the captions, and the katakana above MIAMI.
- **Replaced every transition that wasn't doing much** (three tape rewinds, two flashes, two kaleidoscopes, the VHS roll, the ripple and the second neon trace). There are **10 new designed transitions**, each "going through something" and each with its own sound:
  - into his eye: pupil, then a hexagonal aperture;
  - reassemble from pixel blocks;
  - polaroid toss;
  - face-match morph;
  - 3D cube over the vapor world;
  - through the striped retro sun;
  - knife slash, with the halves flying apart;
  - film burn;
  - through the sunglasses;
  - shadow pass.
- **New graphics and animation:**
  - after the drop, Dexter stands in the vapor world, then reality tunes in behind him scanline by scanline (person matte);
  - hyperspace light streaks during the CRT dive;
  - swaying palm-frond shadows on the sunny shots;
  - VHS colour-echo trails on the run and club shots.
- **New sound design:** heartbeat and shutter blades, the dissolve played backwards, flash with shutter and print eject, cube landing, a sun chord swell with blind rattles, knife swish with a steel ring, fire crackle, a glass chime, a reverse shadow swell, and signal-lock chirps.

Review while building:
- The first stills showed every lead-in half missing; the routing had gone into an overridden function, and it was fixed.
- The eye dive panned to the eye too late; it was retimed.
- MIAMI overlapped the cube; it now ends first.
- The palm shadows read as solid spikes; they were redrawn as separated, drooping leaflets and softened.
- The sunglasses reflections were drawn too tall. These are thin wraparound shades, so the shot now carries its own lens shape.
- The slash halves now fly apart and tilt.
- The shadow pass lost its violet wash.

### Revision 2 checkpoint: **SHIP**

- **Automated criteria:** all PASS.
  - −13.1 LUFS / −2.9 dBTP after AAC.
  - 1,600 frames, clean decode, no frozen runs.
  - 0 face-centering flags.
  - 0 clicks at 17 cuts and at the loop seam.
  - Loop seam matched static to static, and audio and video are the same length.
- **Flags that are by design:**
  - *Text over face (1 frame, 150):* during the eye dive his face fills the screen.
  - *Near-black frames (1278–1279):* the bottom of the shadow pass.
- **Visual sign-off:** every new transition, the vapor tune-in and the hyperspace streaks were checked on frames from the encoded MP4.


## Revision 3 (final polish)

- **New transitions**, replacing the last older-style effects:
  - **film strip whip** (instead of the card tiles): the strip shows real neighbouring frames of the edit, with sprocket holes and edge-code dashes;
  - **sticker peel** (instead of the second neon trace): a flat-fold page peel with a glossy pink-to-cyan back, a roll highlight and a cast shadow;
  - **finger-gun bang → CRT power-off / power-on** (instead of the pixel melt): it ties the finger gun to the confession.
- **New graphics and animation:**
  - a **VHS ‖ PAUSE** freeze-frame on the kill grin, with tape jitter, a noise bar and the OSD; the shot resumes from where it paused;
  - **pastel bokeh motes** drifting through the sunny montage shots;
  - **palm-tree silhouettes** in the vapor world, around the CRT and behind Dexter during the tune-in;
  - **neon light spill**: IT / WAS / ME. throw cyan and pink light onto his face and shirt.
- **New sounds:**
  - projector rattle;
  - sticker crackle and paper flap;
  - a stylised gunshot, a CRT power-off whine and thunk, and a power-on sweep;
  - a VCR pause clunk in and out, with hum while it's held.
- **Review while building:**
  - The film strip's motion blur was about 30× the strip's real per-frame speed, so it smeared into streaks; it now matches the movement.
  - `putText` can't draw on float frames, so the edge codes are drawn as dashes.
  - The fingertip position for the muzzle flash was measured from the shot.

### Revision 3 checkpoint: **SHIP**

- **Automated criteria:** all PASS.
  - −13.0 LUFS / −2.8 dBTP after AAC.
  - 1,600 frames, clean decode, no frozen runs (the VHS pause jitters, so it isn't a freeze).
  - 0 clicks at 17 cuts and at the loop seam.
  - Loop seam matched static to static, and audio and video are the same length.
- **Flags that are by design:**
  - *Near-black frames 1356–1362:* the CRT power-off.
  - *Text over face, frame 150:* the eye dive.
  - *One face flag of 27 in pink_wall:* he turns his head; this is within tolerance.
- **Visual sign-off:** checked on frames from the encoded MP4: the film strip, sticker peel, pause, bang, power-off/on, neon spill and vapor-world palms.

## Benchmark status

The user approved v6 as a reference edit alongside v4. The engine was then made reusable for new edits:
- **Paths and output names come from the EDL.** `VER`, `SLUG` and `SONG`, plus the knobs `DROP_TITLE`, `MONTAGE`, `VANISH_T0` and `VO_STEM`.
- **New review modes:** `auto` (sheets around every cut), `clip A B` (a small MP4 with sound) and `preview`.
- **Music-only edits build without changes.** No VO is needed, and the song is decoded automatically.
- **Verified unchanged after the refactor:** the audio rebuild matches the shipped mix bit for bit, and fresh renders match the shipped MP4 to within encoding noise (about 3/255).
- **Whole pipeline smoke-tested:** scaffold, prep, auto, audio and clip were run on a throwaway edit with a different EDL.

See `docs/TOOLKIT.md` and `tools/`.
