# EVENT HORIZON — The Flash × Brent Faiyaz "Wish You Well" (voidfx v13, 9:16)

A 20.87 s, 1080×1920, 60 fps TikTok edit on the v12 engine with pipeline v2. It loops in picture and sound.

## Concept: SINGULARITY
In the S1 finale a singularity tears open over Central City and pulls everything toward it; Barry runs into it to close it. Here the song is the singularity's voice, a love that pulls everything in:
- *"Pick me up"*: its pull lifts the debris;
- *"God, look out for me"*: he looks up at it;
- *"Darling,"*: time dilates and stops at its event horizon;
- *"I don't wish you well"*: he breaks out;
- *"When you ain't with me, I want you crying"*: Iris, left in his wind.

The hero asset is a **procedural black hole**:
- a shadow and a photon ring;
- real gravitational lensing of the footage (the point-mass lens equation, applied to every pixel);
- an accretion disk of lightning on Keplerian orbits, with Doppler colour (the approaching side cool white, the receding side amber-red);
- the far side of the disk lensed into an arc over the top of the shadow.

It runs through the whole edit: frame 0, his pupil, the event horizon, his chest emblem, and the loop.

- **Look, REDSHIFT:**
  - a desaturated silver-steel world;
  - only the suit's crimson, skin, lightning and the hole's light keep their colour;
  - at the horizon, the picture redshifts (dimmer, sliding to red) as time slows.

  Library transitions are restyled through the palette.
- **No text.** The lyrics are clean, but the picture carries the song (v12 rule: a title must earn its place).

## Song
`src/wish_you_well_full.mp3`, song half-beats 92 → 188 (20.05 → 40.92 s), 96 half-beats = six 16-half-beat phrases (3.48 s each).
- **Grid:** fitted on the Demucs drum stem: half-beat 0.217398 s (137.99 BPM half-beats; the feel is 69 BPM), offset 0.0539 s. The automatic map agreed within 10 ms.
- **There are no real drums in this section:** an ambient phrase with an 808 hit at e = 8 (mod 16) and a rest at e = 12–14.
- **The loop is musically exact:** bar 23 mirrors bar 11 (music spectral correlation 0.9996 across the wrap).
- **Lyrics** (Whisper large-v3 on the vocal stem; the full-mix pass heard "girl" where the stem says "God"):

| Edit | Song | What happens |
|---|---|---|
| 0.59 s | 20.64 | "Pick me up, don't know if it's what I need / But it's what I want, God, look out for me" |
| 10.79 s (e49.6) | 30.84 | **"Darling,"** then the vocal is silent for 3 s |
| 13.04–13.48 s (e60–62) | 33.1 | the song's deepest rest: **the freeze** |
| 13.91 s (e64) | 33.97 | the music returns: **the breakout** |
| 14.6–16.0 s | 34.6–36.0 | "I don't wish you well" |
| 16.3–19.0 s | 36.3–39.0 | "When you ain't with me, I want you crying" |

## Shots and transitions (15 cuts + the loop)

| Edit | Shot (pack, s) | In |
|---|---|---|
| 0.00 | The S1 vortex over the city, **the singularity at its core** (fs1 290.22) | the loop |
| 1.74 | Barry looks up as the debris rises: "Pick me up" (fs1 277.47) | **LENS DROP**: the singularity moves in; inside its Einstein ring the lensed light shows the next shot; one continuous hole |
| 3.04 | Masked, serious (fs1 228.10) | **FRAME DRAG**: a spinning mass twists the frame round it (Lense–Thirring) |
| 4.13 | Masked, bloody, in profile (fs1 286.95) | **REDSHIFT**: the light stretches toward the hole and loses energy |
| 5.22 | "God, look out for me": he looks up (fs1 268.30) | **PHOTON RING**: the picture curls into orbit round a small hole and unwinds |
| 6.52 | His eye (fs1 291.50) | dolly (restyled) |
| 7.39 | The take-off on the airfield (fs1 195.00, velocity ramp) | **EYE HORIZON**: his pupil becomes the singularity, wraps the iris into an Einstein ring and swallows the frame; we come out of its throat |
| 8.70 | The run (fbh 80.90) | **ACCRETION WHIP**: through the plane of the disk |
| 9.57 | Iris watching (fs1 285.55) | strobe echo (restyled) |
| 10.44 | **"Darling,"**: masked close-up (fs1 221.72); time dilates to a stop, the background bends toward a mass just out of frame, the picture redshifts | whip |
| 12.17 | **THE EVENT HORIZON** (focal set piece): on the airfield, the singularity eclipses behind his head (behind his matte, on a clean plate). The disk slows and freezes in the song's rest, then collapses | **EVENT HORIZON**: the close-up streams and twists into the corner and opens onto the airfield |
| 13.91 | The breakout: the charge-up (fbh 52.92) | **GRAV WAVE**: rings of quadrupole strain race out with the next shot behind the wavefront |
| 15.65 | Lightning round him (fbh 83.85, on flow) | **SPAGHETTIFY**: the tidal pull stretches the frame into streams spiralling into a point |
| 16.96 | He looks at her and leaves (fs1 236.30) | **EMBLEM HORIZON**: on the real tracked chest emblem (Hough), a singularity is born in it and swallows the frame |
| 17.83 | Iris in his wind: "I want you crying" (fs1 237.80) | **SLIPSTREAM**: the air he leaves drags the frame sideways along a thin trail of his light |
| 19.13–20.87 | **The loop**: he looks up at the singularity (fs1 279.55), the camera falls into it, and frame 0's vortex comes through. The inside is rendered at frame 0's virtual frames, so the hole keeps turning across the wrap | **LENS DROP** into the hole he is looking at |

## Sound
- **The song plays straight** (the window wraps exactly). The one designed move: it sinks under a low-pass with the picture's redshift from "Darling," and snaps open on the breakout.
- **About 16 effects:**
  - one per designed transition; small moves (dolly, strobe echo) are silent;
  - layered sound only at the event horizon (gravity rising, the drop into the frozen moment, the collapse), the breakout (impact, sub, thunder) and the loop fall;
  - a low hum of the singularity under the whole loop.

## Results (measured on the encoded files)

| Check | Result |
|---|---|
| Format | 1080×1920, 60 fps, 1,252 frames (20.87 s), clean decode; container durations: audio 20.867 s, video 20.867 s |
| Loudness after AAC | −13.3 LUFS / −3.2 dBTP |
| Loop seam | blurred picture diff 0.14 (gate ≤ 1); motion audit: wrap step 0.71 against a local median of 1.53 (no spike); audio: no click (the waveform is continuous through the seam) |
| Flashes | 2 events, at most 1 a second, none over mean luma 110, no white-out runs |
| Effects vs music (`mixcheck`) | music −18.9 dBFS RMS (a quiet master). 3 of 19 moments are "buried", all silent by design: frame 0, the dolly and the strobe echo |
| Motion audit (`motionqc`) | no dead spans; no hold-cadence judder. 15 pops: 7 cuts, 3 beat hits, 2 flashes, 2 cadence, and 1 (f893) that is the breakout's lightning igniting along the suit in the source, checked on frames |
| Effects over faces (`faceqc`) | 3 runs, all designed, checked on stills: horizon 758–808 (3 %: the singularity's rim light behind his helmet); last 1184–1198 (11 %: the loop fall's zoom moving the picture against the face track) |
| Sharpness (`sharpness.py 13`) | 2 shots flagged: emblem (0.71× the median: a dark, glowing source shot, now on flow) and last (0.72×: the loop fall's designed zoom and radial blur) |
| Text over faces | none (no text) |
| Render | 4 full renders this round (~5.4 min each to the upload file; the master follows in the background). One partial re-render was refused by its own verification (2 horizon frames differed outside the changed ranges) and fell back to a full render, as designed |

## Caught by review (before delivery)
- **Faces:** the photon ring's, the loop's and the lens drops' holes landed on faces. They are now off-face, behind his matte, or shown only while the frame is fully curled.
- **The horizon** was first planned on a frame-filling close-up, where the hole could only hide behind him or sit on his face. It moved to the S1 airfield wide, where it eclipses behind his head.
- **Seams:** the photon ring's polar wrap seam (now a mirrored wrap), and a hard Doppler colour seam through the hole (now a smooth gradient).
- **Two holes at once** at the first lens drop: the transition's hole now *is* the sky's hole, and the loop's hole is frame 0's.
- **Throats:** mirrored copies at the edges of the throats (the inner picture is now kept at scale ≥ 1).
- **A ghost of him** dragged round his own matte edge by the lensing: the background is lensed as a clean plate, with him inpainted out (v105 rule 5).
- **Judder (`motionqc`):** 30p hold judder on the fast shots. The engine refused flow above a 14-grey-level frame difference; there is now a per-shot limit (`flowmax`), with the in-betweens checked at full resolution.
- **Flow warps:** across the breakout's lightning ignition, and across a source cut 0.03 s before its range. The fix is a blend fallback (`flowfall`), and the range now starts after the cut.
- **Length check:** QC decoded the AAC padding (+19 ms). It now reads the container durations, which players use.
- **Off-palette transition:** the orange "phase" flash was replaced by SLIPSTREAM.


## Files
- `v13/work/edl13.py`: every decision.
- `v13/work/sec13.py`: the v13 section, spliced into `render13.py` above `# >>> pipeline v2: speed`.
- `v13/work/audio13.py`: `music13` and the v13 `main`.
- `v13/work/qc13.py`.
