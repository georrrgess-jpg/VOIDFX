# WISH YOU WELL — Dexter × Brent Faiyaz "Wish You Well" (voidfx v8, 9:16)

This is a 21.73 s, 1080×1920, 60 fps TikTok edit built on the v7 engine to the standard in `/CLAUDE.md`. It loops.

## Song: the section used and why

The song came as a **36 s phone screen recording** of the YouTube upload (`src/wish_you_well_screenrec.mov`). Its audio was extracted to `src/wish_you_well_rec.wav`. I mapped it with `tools/song_map.py` (138 BPM, half-beat 0.21731 s) and timed the vocal from a Demucs vocal stem with Whisper.

| Song time | What happens | Edit |
|---|---|---|
| 13.96 | quiet section: the hi-hats drop out, *"ooh, ooh, yeah"* | **start** (lead-in) |
| 19.17 | the beat comes back (+16 dB) | the first big hit (headlights) |
| 20.26–25.32 | *"Pick me up, don't know if it's what I need / But it's what I want, God, look out for me"* | lyric typography |
| 27.86 | the drums thin out | the break: the S1 pilot line *"Tonight's the night."* sits in the gap |
| 30.04 | *"Darling,"* (held) | freeze-frame composition |
| 31.34 | near-silent bar | the blood drop falls |
| **33.08** | **the drop** (+46 dB in the high band, the biggest change in the recording) | **hero transition: blood blooms in water** |
| 34.16–35.12 | *"I don't wish you well"* | one cut per syllable |
| 35.69 | the beat after "well" | dead stop, then the loop |

**Window:** half-beats 64 → 164 (13.96 → 35.69 s, 21.73 s). The recording ends at 35.94 s, so the edit is built to *arrive* at the drop rather than play out after it. The quiet lead-in and the near-silent bar make the hook feel earned.

## Concept: "Tonight's the night."

Dexter's night drive to the kill, scored like a toxic love song: the R&B hook becomes his love letter to the man on the table. The look is new: **sodium nocturne**.
- **Colour:** deep indigo shadows, lifted rather than crushed; warm sodium-vapour highlights; skin kept natural.
- **Atmosphere:** rain on the glass, passing streetlight sweeps, warm halation.
- **Type:** elegant serif italic with blood-red accents.

## Timeline

| Time | Picture | Transition in / effect (each has its own sound) |
|---|---|---|
| 0.00 | **Rear-view mirror** in a dark car: rain on the windshield, night-city bokeh, a streetlight comes up on his eyes | **push into the mirror** |
| 1.30 | South Beach at night | **streetlight sweep**: the cut hides in a passing light band (car pass-by) |
| 3.48 | Walking through the night garden. **Speed ramp**: 0.5× flow slow-mo on true-60 fps footage, then 2.4× into the beat | **windshield wiper** clears the rain off the next shot (thunk, squeak) |
| 5.22 | **Beat returns.** Under a streetlight: **PICK / ME / UP** stacked behind him (MODNet cutout, tracked to his head, off-centre framing) | **headlights** rush the lens and flare (pass-by, riser, hit) |
| 7.17 | Gloving up at night. DON'T KNOW IF IT'S / WHAT I *NEED* | **whip pan** |
| 7.82 | Behind the chain-link | **face-match** |
| 8.69 | The kill-room rapture, head back. BUT IT'S WHAT I + a huge serif ***WANT*** behind his head | **sodium light leak** |
| 10.21 | He looks up. *GOD,* / LOOK OUT FOR ME | **vertical whip**, following his gaze |
| 11.73 | Kill room, the lamp | **voidfx logo, original**, fly-through (the only logo appearance) |
| 12.60 | Plastic sheeting | **kill-room plastic wraps the lens** |
| 13.26 | Face shield over blood spatter | **impact frame** (1 frame of negative cut-out, then punch-in) |
| 13.91 | The pilot drive silhouette. ***"Tonight's the night."*** (his line, written on with a pen nib) | **rain-glass focus pull** |
| 15.65 | The orange room; **freeze** on ***"Darling,"***. The world drains to indigo while he stays lit with a warm rim light; the word is written in blood-red script | **shadow pass**; shutter click |
| 17.38 | **A single drop of blood falls** through the dark in slow motion, **refracting Dexter's face upside-down inside it** | heartbeat, slow fall |
| **19.12** | **The drop hits the water**: crown splash, rings, blood blooming in water that clears onto the kill-room close-up | **blood in water** (sub boom, bloop, splash) |
| 20.20–21.16 | **I / DON'T / WISH / YOU / *WELL***: one cut per syllable (knife, blood slide, dark walk, red smirk, the stare). The line builds word by word across the cuts | **syllable slams** (a hit per word) |
| 21.30–21.73 | Pull back into the rear-view mirror, the light leaves it | **loop**: the edit reopens on the same mirror |

## Sound

- **Song:** played straight on its beat grid, with a **dead stop** on the beat after "well". The stop's reverb tail wraps into the opening under the rain.
- **Dialogue:** *"Tonight's the night."* comes from a Demucs vocal stem of the S1 pilot, levelled, with the music dipped 4 dB under it.
- **Beds:** rain and car-interior ambience in the car sections, and low room tone under everything, across the wrap.
- **Effects:** every transition has its own sound, plus the pen scratch on the write-ons, the shutter click on the freeze, the slow fall and heartbeat for the drop, and one hit per hook syllable. All of it sits under the song.

## Frame rate

The export is 60 fps for the camera moves, type and graphics. **24p source footage plays at its native cadence (frame hold), with no synthesized frames.** Optical-flow slow motion is used only on genuinely 60 fps footage: the night-garden ramp, the rapture and the face shield.

## Files

- `out/wish_you_well_dexter_voidfx_9x16.mp4`: upload version.
- `out/wish_you_well_dexter_voidfx_9x16_master.mov`: master.
- `work/edl8.py`: every decision (shots, ramps, text timings, the song window).
- `work/render8.py`: the v7 engine plus the v8 toolkit:
  - nocturne grade;
  - rain glass, streetlight sweeps;
  - car interior and mirror;
  - transitions: headlights, wiper, whips, light leak, wrap, impact, rain focus, slam;
  - blood drop and blood bloom;
  - freeze composition;
  - type: behind-subject, lyric, script, hook.
- `work/audio8.py`: sound.
- `work/qc8.py`: the review and ship checkpoint.

### Re-render

```bash
bash tools/build.sh 8 prep audio auto
bash tools/build.sh 8 video qc
```

The stems need to exist first:

```bash
python3 -m demucs -n htdemucs --two-stems=vocals -o v8/audio/sep src/wish_you_well_rec.wav
python3 -m demucs -n htdemucs --two-stems=vocals -o v8/audio/sep v8/audio/p8_open.wav
```

`p8_open.wav` is pack8 from 0 to 6 s at 44.1 kHz.
