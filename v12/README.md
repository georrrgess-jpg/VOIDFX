# BLOOM — The Flash × fakemink "Night Blooming Jasmine" (voidfx v12, 9:16)

A 23.35 s, 1080×1920, 60 fps TikTok edit on the v11 engine with pipeline v2 (render server, frame cache, partial re-renders, face and mix checks). It loops in picture and sound.

## Rev 2 (owner: "remove the night text at the beginning and get rid of like half the sound effects")
- **NIGHT removed:** the opening is the storm sky and its bolt alone; BLOOM on the drop is now the only title.
- **Sound effects 87 → 37:** what's left is the set-piece hits (the strike, THE BLOOM's impact/sub/thunder, FULL BLOOM, the loop dive and landing) and one sound per transition.
  - Removed: the beat-moment sounds (pollen, bokeh stars, bud, petal echoes, aura), the BLOOM letter chimes, the NIGHT crackle, the cloud flickers, the heart-monitor beeps before the cut, the charge hum, and the secondary layers (whines, glass, shimmers, extra crackles and zaps).
- **Effects vs music (`mixcheck`):** one transition (the dolly into the eye, now only a reversed swell) sits more than 12 dB under the music, which follows from the request.
- **Loudness** is unchanged: −13.0 LUFS / −3.5 dBTP after AAC.
- **Render:** a verified partial re-render (96 frames, 32 checked bit-exact outside the range) plus the re-encode, 164 s.

## Concept: LIGHTNING BLOOM
"Night blooming" is the night Barry was struck by lightning. Lightning leaves Lichtenberg figures on what it hits, often called "lightning flowers". So the hero asset is a five-petal **lightning jasmine**:
- petal edges of live, crackling lightning;
- Lichtenberg veins that grow as it opens;
- a pale-yellow heart with stamens.

It runs bud → bloom → full bloom → closing through the edit and carries the loop.

- **Look, NOCTURNE:**
  - indigo nights, with daylight shots pushed into the night;
  - the suit kept crimson;
  - orange and red light turned to cream;
  - lightning in jasmine white over a cream glow;
  - a deep vignette and fine grain.

  Every library transition is restyled through the palette: the gold, red and ember constants all point at the v12 colours.
- **Titles (two, designed; no captions):**
  - **NIGHT** is grown out of lightning seeds over the storm.
  - **BLOOM** blooms in letter by letter on the drop; its two O's are rings with a lightning jasmine inside.

  The lyrics are fast, mumbled rap that Whisper can't transcribe reliably, so no sung words are captioned.

## Song
`src/night_blooming_jasmine.mp3`, bars 8–18 = song 18.71–42.05 s (102.79 BPM, half-beat 0.29185 s).

| Edit | Song | What happens |
|---|---|---|
| 0–9.34 s | bars 8–11 | instrumental groove (kicks, hats): the night |
| **9.34 s** | bar 12 | **the vocal enters, the hats fall away: THE BLOOM** |
| **18.68 s** | bar 16 | **the claps enter: FULL BLOOM** |
| 21.3–22.55 s | — | the vocal stem fades on a half-beat echo under the loop dive; the instrumental runs on and wraps into bar 8 on the bar grid; the mix closes a little under a low-pass for the last 0.45 s |

## Shots and transitions (16 cuts + the loop)

| Edit | Shot (pack, s) | In |
|---|---|---|
| 0.00 | Storm sky, its bolt pulled out and lit (fs5 105.12) — **NIGHT** | the loop landing |
| 1.75 | Barry struck by lightning in the lab (fbh 10.32, red light tamed to cream) | **STRIKE LINK**: the sky's bolt continues through the cut, branches crack out, the shot opens along them |
| 3.50 | He wakes in S.T.A.R. Labs (fs1 4.45, flow slow motion) | **ECG BOLT**: a heart-monitor trace crosses the frame, its beats turn to lightning, the frame tears open along it |
| 4.38 | First sparks gather at his hand (fbk 133.2) | bolt trace (restyled) |
| 5.84 | The suit in blue cortex light (fs2t 28.9) | **BUD IRIS**: a lightning bud turns and opens like an iris |
| 7.88 | His eye fills with lightning (fs1 291.9) | dolly focus pull (restyled) |
| **9.34** | Speed-trail run down a night street (fbk 60.7) — **BLOOM** | **THE BLOOM**: a bud forms in his pupil and bursts into a lightning jasmine that fills the frame; the run is inside the petals; afterimage petals and a ring keep opening |
| 10.51 | Masked close-up (fbk 124.75), **pollen** on the beats | petal whip |
| 11.67 | S5 suit under street lights (fs5 72.0), **bokeh stars** | Lichtenberg crawl (restyled) |
| 12.84 | S5 crouch in lightning streaks (fs5 108.6) | strobe echo (restyled) |
| 14.01 | Hood down, night bokeh (fbk 23.95), **petal echoes** | slices |
| 15.18 | Lightning on his chest (fs5 180.0), **a bud pulses on his emblem** | clash (restyled) |
| 16.34 | S3 masked at night (fs3 59.1), **aura rings** | haze (restyled) |
| 17.51 | Lightning run at the camera (fbk 20.0) | whip |
| **18.68** | **FULL BLOOM** (fbk 136.02) | a bolt strikes from the sky into the flower's heart behind his head; a lightning jasmine unfolds behind him (matte, light wrap), its petals glow as surfaces and breathe on the claps |
| 20.43 | S3 masked under street lights (fs3 106.8) | **PETAL PASS**: the flower lets go and its petals sweep past the camera |
| 21.60 | S5 masked, walking toward camera (fbh 109.7) | **POLLEN BURST**: the frame blows away as pollen of light (kept off faces) |
| 22.37–23.35 | **The loop** | a bud closes on his emblem; anticipation pull-back, then an accelerating dive into the bud. Its opening shows frame 0 (the storm), which fills the frame at scale 1.0 on the last frame |

Motion pass:
- velocity ramps with optical-flow slow motion on every montage shot;
- the beat camera, which rests under FULL BLOOM and the loop.

Every shot runs on restored sources (`tools/sr_prep.py`).

## Sources
New high-bitrate packs from the owner's 2026-11-08 Drive list:
- `flash_blitzkrieg`, `flash_s5`, `flash_s3`, `flash_s2_topaz` and `flash_s1`;
- `flash_b_hq`: the same frames as `flash_b` at 1.9× the bitrate.

All of them are 720p.

## Results (measured on the encoded files)

| Check | Result |
|---|---|
| Format | 1080×1920, 60 fps, 1,401 frames (23.35 s), clean decode, audio and video the same length |
| Loudness after AAC | −13.0 LUFS / −3.5 dBTP |
| Loop seam | passes the ≤ 1 gate (blurred picture diff); audio: no click at the seam (sample step 0.031 vs local median 0.026, the landing impact) |
| Flashes | no white-out runs, at most 1 a second, none over mean luma 110 (a flash governor caps flare frames at mean luma 0.40 before the finish) |
| Effects vs music (`mixcheck`) | 0 of 20 transitions and set pieces more than 12 dB under the music (music −8.9 dBFS RMS: a loud master) |
| Effects over faces (`faceqc`) | 2 runs listed, both checked on stills: FULL BLOOM (the flower's light is behind him; the face box is wider than his head) and the loop bud (a little bloom on the eye highlights, 6 %) |
| Sharpness (`sharpness.py 12`) | no shot flagged (lowest: dash 0.80×, charge 0.82× the edit's median) |
| Text over faces | none |
| Face centring | **one QC flag, a verified false positive**: on s3night frames 1022–1026 YuNet loses the full face (710 px wide, centred on frames 1018 and 1028) and finds a 250 px partial box at the left edge. The frames show the face centred |
| Render | full render 289 s (4.8 min) with the master in the background; one partial re-render (435 frames, 27 frames verified bit-exact outside the range, 217 s); a second partial was refused by its verification (the flash governor also touched frame 595) and fell back to a full render, as designed |

## Files
- `v12/work/edl12.py`: every decision.
- `v12/work/render12.py`: the v12 section sits above `# >>> pipeline v2: speed`.
- `v12/work/audio12.py`: `music12` and the v12 `main`.
- `v12/work/qc12.py`.
