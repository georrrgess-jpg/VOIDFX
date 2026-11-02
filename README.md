# THE MASK SLIPS — Dexter × Blood Theme (voidfx)

A 22-second vertical (1080×1920, 60 fps) Dexter Morgan character edit built entirely in code
(FFmpeg + Python/OpenCV) from the supplied 135-scene pack and the *Blood Theme* instrumental.
Every decision lives in one file, `work/edl.py`; the renderer reads nothing else.

## Concept

**The public face slips, the ritual takes over, then the mask goes back on.**

- The edit opens on Dexter grinning and pointing a finger-gun at the viewer: charm with a gun in it.
- The smile cracks on the build's big sub hit.
- On the drop he lowers a face shield over a blood-spattered suit.
- What follows is the private ritual: the blood slide, the hunt, gloves, the kill room, the act, release, and the smile.
- He puts a finger to his lips on the last hit, and the music obeys a beat later. The song's own hard stop is the "shh".
- In the silence he walks back into public life: *"Check in. Establish an alibi."* The word "alibi" lands on the same office grin.
- The final shot is the first half of the opening finger-gun, so the loop continues straight into the hook.

## Timeline (edit seconds; 1 pulse = 0.3334 s, 6 pulses per 2-second bar)

| Time | Shot (pack #) | Purpose |
|---|---|---|
| 0.00–1.33 | finger-gun at the lens (#36) | **Hook**: readable face on frame 0; slow push-in |
| 1.33–2.67 | boat laugh (#40) | public face |
| 2.67–4.00 | ice cream, eyes go cold (#39) | first crack, cut on the build's biggest sub hit |
| 4.00–6.00 | black gloves on, eyes up to the lens (#22) | preparation in daylight |
| 6.00–8.00 | walks out of darkness (#130) | build: accelerating push-in, a 4-frame "breath" on the song's sub gap |
| **8.00** | **drop**: face shield over blood spatter (#32) | white hit (~0.05 s), held slice "crack", RGB split, small shake |
| 8.67–10.00 | blood slide raised to his eye (#75) | **signature**: freezes on pulse 28 as evidence, with a shutter flash, colour drained except the blood, an `EVIDENCE 01` bracket and a glass tink |
| 10.00–12.00 | container walk (#10) → chain-link stare (#119) → gloving at night (#67) | the hunt (`voidfx` mark, 10.05–11.31) |
| 12.00–15.00 | photo wall (#59) → victim's-eye slide (#88, punch-in) → knife (#110) → bandana mask (#60) → hand on face (#46) | the room and the act; two half-unit cuts for escalation |
| 15.00–18.00 | gloved hands (#47) → rapture (#93) → the private smile (#96) | release; the slip completes |
| 18.00–18.68 | "shh" (#62) | finger reaches his lips on the last hit; **the music stops at 18.68** |
| 18.68–21.00 | walking, checking his watch (#21) | silence, then *"Check in."* |
| 21.00–22.00 | the office grin again (#36, first half) | *"…establish an alibi."* Flows into frame 0 on loop |

## Music edit

The beat grid was fitted to the song: 180 pulses per minute, a 6/8 feel with 2.000 s bars,
residual 6.6 ms RMS. Grid timing was corrected for onset-detector bias against sub-bass attacks.

| Edit time | Song time | Section |
|---|---|---|
| 0.00–8.00 | 62.36–70.36 | bars 31–34: the sustained build, ending with a riser and a sub gap |
| 8.00–18.00 | 70.36–80.36 | bars 35–39: the drop and percussion phrase (B B C A A) |
| from 18.00 | from 112.37 | bar 56: the final two hits, the song's own hard stop at 113.05, then the quiet outro bed (faded by 22.0 s) |

The splice falls 6 ms before both downbeats, so the bar-56 kick plays untouched. Bars 51–55 repeat the
harmony of bars 35–39, so jumping from bar 39 to bar 56 is how the song itself ends that phrase.
The total length is 66 pulses, so the restart hit lands on the grid when the edit loops.

## Sound

- **Music:** the Blood Theme instrumental (supplied file), edited as above.
- **Dialogue:** *"Check in. Establish an alibi."* comes from the scene pack's audio, the only clean line in it.
  - Three local speech models agreed on the wording; word onsets were measured from the waveform.
  - Processing: high-pass, light presence lift, 3:1 compression, levelled.
  - Placement: "Check" lands on pulse 59, two silent pulses after the stop.
- **Foley:** one synthesized glass tink on the evidence freeze. No other effects were added, because the song already carries its own risers and impacts.
- **Mix:** −12.5 LUFS integrated, true peak −3.0 dBTP, both measured on the encoded AAC.
  - The edit starts on a sub hit, which made AAC's first frame overshoot. The encoder gets 1024 samples of the song's own lead-in, hidden by an MP4 edit list; the audio is verified sample-aligned to picture.
  - The outro bed is ducked 3 dB under the voice.

## Picture

- **9:16 framing:** each shot is reframed separately, with keyframed crop centres checked on first, middle and last frames. Text stays out of TikTok's bottom 300 px and right 160 px.
- **Colour:**
  - Per shot: partial grey-world white balance, plus a gamma that brings the face (metered on skin) to a target level.
  - Shared look: soft S-curve with lifted (not crushed) blacks.
  - Three look families: warm public daylight, cooler private rooms, coldest night.
  - Blood-like reds get richer and deeper.
- **Finish:** chroma-only block clean-up, Lanczos upscale, light unsharp mask, light soft luma grain (1%, to mask compression blocks), subtle vignette.
- **Type:** Inter Display for subtitles (the accent word is set Bold, with a deep-red hairline under "alibi"), JetBrains Mono for the evidence label, and a small lowercase `voidfx` mark.

## Files

- `out_final/the_mask_slips_tiktok.mp4`: **upload version**, 37.5 MB (H.264 High, CRF 19 capped at 20 Mbps (≈13.4 Mbps actual), yuv420p BT.709, AAC-LC 256k 48 kHz, fast-start).
- `out_final/the_mask_slips_master.mov`: **master**, 134 MB (H.264 CRF 12 + 24-bit PCM). Both come from one render pass, so there is no second lossy generation.
- `out_final_alt_open/…`: the same edit with an alternative cold open (his eyes over a fresh blood slide, #126). It is darker and more forensic from frame 0, but its loop is a hard cut (seam difference 75.9) instead of the main version's seamless finger-gun continuation.
- `work/`: the reproducible project.
  - `edl.py`: every decision.
  - `render.py`: picture.
  - `build_audio.py`: sound.
  - `qc.py`: checks on the encoded file.
  - `analyze.py` / `audio_analyze.py`: media analysis.
  - `cropcheck.py` / `framecheck.py` / `strips.py`: visual inspection sheets.

## Caption options

1. `check in. establish an alibi.`
2. `the smile was always the mask.`
3. `nicest guy at miami metro.`

Hashtags: `#dexter #dextermorgan #dexteredit #dextermorganedit #michaelchall #bloodtheme #characteredit #tvedit`

Media (`src/`, `audio/`, `out*/`, `frames/`) is git-ignored. The footage is copyrighted and large, and everything can be regenerated.

### Re-render

```bash
python3 work/render.py prep                 # colour correction + blood-drop tracking
python3 work/build_audio.py                 # audio/mix.wav
python3 work/render.py video out_final      # upload mp4 + master
python3 work/qc.py out_final/the_mask_slips_tiktok.mp4 final
EDIT_VARIANT=alt_open python3 work/render.py prep && EDIT_VARIANT=alt_open python3 work/render.py video out_final_alt_open
```

Turn the `voidfx` mark off with `SIGNATURE["enabled"] = False` in `work/edl.py`.

## QC (measured on the encoded upload file)

| Check | Result |
|---|---|
| Format | 1080×1920, 60/1 CFR, 1,320 frames, 22.000 s, yuv420p, BT.709 tags, fast-start |
| Decode | full decode, no errors |
| Cuts | all 20 re-detected on their exact intended frames (pulse grid; rounding ≤ ½ frame) |
| Black | no black segments; one near-black frame (477) is the intended pre-drop "breath" |
| Frozen runs | none (the evidence freeze keeps grain and push-in alive) |
| Loop seam | last→first frame difference 1.95, against a median consecutive difference of 2.12 |
| Audio | −12.5 LUFS, −3.0 dBTP after AAC; 0-sample offset vs the mix at 0, 8, 18 and 19.5 s |

Revisions made during review:
- **Bracket glitch:** the evidence bracket was drawn early with negative opacity; it now appears only on the freeze.
- **Drop flash:** shortened, so the "crack" slices show as it clears (face readable again after ~0.03 s).
- **Pre-drop dip:** made softer so it reads as a dip rather than black.
- **Smile shot:** given per-shot contrast instead of a milky lift.
- **Upload size:** 95 MB → 37.5 MB, from lighter, softer grain and a bitrate cap.
- **True peak:** fixed AAC start overshoot (+1.1 → −3.0 dBTP).

## Limitations

- **I can't watch or listen.** Everything was verified by frame inspection and measurement, not by watching at normal speed or listening. Watch it once at normal speed with sound before posting, especially the dialogue line and the drop.
- **The scene pack is 1200×720 at about 1 Mbps,** upscaled 2.67× for 9:16, so close-ups look soft and some dark shots show compression blocks. The smile (#96) is the weakest.
- **The 60 fps is the pack's own.** The pack is already motion-interpolated to 60 fps (every frame differs in motion), and 60 fps is kept for that reason, not to add frames.
- **Slow-motion is mild.** The ending walk (0.83×), the final grin (0.73×), the finger-gun (0.89×) and the drop shot (0.87×) use frame blending. Nothing is slower.
- **The dialogue audio is low quality.** The pack's audio is 13 kbps AAC, so the line sounds slightly lo-fi.
- **The music is the user-supplied file.** Rights clearance for posting is up to the uploader.
